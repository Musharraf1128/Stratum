from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Optional

from stratum.core.models import (
    AttemptRecord,
    ExecutionRun,
    ExecutionStep,
    RunStatus,
    StepStatus,
)
from stratum.core.workflow import WorkflowGraph


class ExecutionEngine:
    def __init__(
        self,
        workflow: WorkflowGraph,
        max_workers: int = 4,
        api_key: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
    ):
        self.workflow = workflow
        self.max_workers = max_workers
        self.api_key = api_key
        self.provider = provider
        self.model = model

        # ── Per-run governance tracking (reset per execute() call) ──
        self._run_call_counts: dict[str, int] = {}      # agent_id -> call count this run
        self._run_last_call_time: dict[str, float] = {}  # agent_id -> last call timestamp
        self._run_token_total: int = 0                   # running token sum for this run
        self._max_total_tokens: int = 20000              # default; overridable via config

    def _reset_run_tracking(self) -> None:
        """Reset per-run governance counters."""
        self._run_call_counts.clear()
        self._run_last_call_time.clear()
        self._run_token_total = 0

        # Try to load max_total_tokens from config
        try:
            from stratum.core.config_loader import load_config
            config = load_config()
            wf_config = config.get("workflows", {}).get(self.workflow.name, {})
            self._max_total_tokens = wf_config.get("max_total_tokens", 20000)
        except Exception:
            self._max_total_tokens = 20000

    def execute(self, initial_input: Optional[dict[str, Any]] = None) -> ExecutionRun:
        self._reset_run_tracking()

        run = ExecutionRun(
            workflow_name=self.workflow.name,
            input_data=initial_input or {},
            start_time=datetime.now(),
        )

        # Encrypt and store the API key on the run (if provided)
        if self.api_key:
            from stratum.core.crypto import encrypt_key
            run.encrypted_api_key = encrypt_key(self.api_key)

        try:
            run.status = RunStatus.RUNNING
            execution_order = self.workflow.get_execution_order()

            for agent_name in execution_order:
                self._execute_node(agent_name, run, initial_input)

                current_step = next(
                    (s for s in run.steps if s.agent_name == agent_name), None
                )
                if current_step and current_step.status in (
                    StepStatus.FAILED,
                    StepStatus.FAILED_RETRIES_EXCEEDED,
                ):
                    raise RuntimeError(
                        f"Agent '{agent_name}' failed: {current_step.error}"
                    )
                # Non-fatal governance statuses: don't break the pipeline
                # SKIPPED*, RATE_LIMITED, PERMISSION_DENIED are logged but
                # don't halt the run

            run.status = RunStatus.COMPLETED
            run.output_data = self._collect_output(run)

        except Exception as e:
            run.status = RunStatus.FAILED
            run.error = str(e)

        finally:
            run.end_time = datetime.now()

        return run

    def execute_parallel(
        self, initial_input: Optional[dict[str, Any]] = None
    ) -> ExecutionRun:
        self._reset_run_tracking()

        run = ExecutionRun(
            workflow_name=self.workflow.name,
            input_data=initial_input or {},
            start_time=datetime.now(),
        )

        if self.api_key:
            from stratum.core.crypto import encrypt_key
            run.encrypted_api_key = encrypt_key(self.api_key)

        try:
            run.status = RunStatus.RUNNING
            execution_order = self.workflow.get_execution_order()
            completed: set[str] = set()

            while completed != set(execution_order):
                ready_nodes = [
                    agent
                    for agent in execution_order
                    if agent not in completed
                    and all(
                        dep in completed
                        for dep in self.workflow.get_dependencies(agent)
                    )
                ]

                if not ready_nodes:
                    raise RuntimeError("No ready nodes - possible deadlock")

                self._execute_parallel_nodes(ready_nodes, run, initial_input, completed)

                for step in run.steps:
                    if (
                        step.agent_name in ready_nodes
                        and step.status in (
                            StepStatus.FAILED,
                            StepStatus.FAILED_RETRIES_EXCEEDED,
                        )
                    ):
                        raise RuntimeError(
                            f"Agent '{step.agent_name}' failed: {step.error}"
                        )

                completed.update(ready_nodes)

            run.status = RunStatus.COMPLETED
            run.output_data = self._collect_output(run)

        except Exception as e:
            run.status = RunStatus.FAILED
            run.error = str(e)

        finally:
            run.end_time = datetime.now()

        return run

    def _execute_node(
        self,
        agent_name: str,
        run: ExecutionRun,
        initial_input: Optional[dict[str, Any]],
    ) -> None:
        step = ExecutionStep(agent_name=agent_name)

        dependencies = self.workflow.get_dependencies(agent_name)
        input_data = {}

        if initial_input:
            input_data.update(initial_input)

        for dep in dependencies:
            dep_step = next((s for s in run.steps if s.agent_name == dep), None)
            if dep_step:
                # If the dependency was skipped/rate-limited/etc, pass empty dict
                # so downstream agents don't crash on None.get()
                if dep_step.output_data is not None:
                    input_data[dep] = dep_step.output_data
                else:
                    input_data[dep] = {}

        step.input_data = input_data
        run.steps.append(step)

        self._run_step(step)

    def _execute_parallel_nodes(
        self,
        agent_names: list[str],
        run: ExecutionRun,
        initial_input: Optional[dict[str, Any]],
        completed: set[str],
    ) -> None:
        steps_to_run = []

        for agent_name in agent_names:
            step = ExecutionStep(agent_name=agent_name)

            dependencies = self.workflow.get_dependencies(agent_name)
            input_data = {}

            if initial_input:
                input_data.update(initial_input)

            for dep in dependencies:
                dep_step = next((s for s in run.steps if s.agent_name == dep), None)
                if dep_step:
                    input_data[dep] = dep_step.output_data

            step.input_data = input_data
            run.steps.append(step)
            steps_to_run.append(step)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._run_step, step): step for step in steps_to_run
            }

            for future in as_completed(futures):
                future.result()

    # ─── Core Governance Enforcement ────────────────────────────────────────────

    def _run_step(self, step: ExecutionStep) -> None:
        """Execute a single step with full governance enforcement.

        Enforcement flow:
        1. Look up AgentSpec from registry
        2. Rate limit check
        3. Call count check
        4. Token budget check
        5. Permission check (placeholder — always passes in v0)
        6. Retry loop with attempt tracking
        7. Fallback on exhausted retries
        8. Record attempt history
        """
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()

        try:
            from stratum.core.agent import get_agent_by_name

            agent = get_agent_by_name(step.agent_name)
            if not agent:
                raise ValueError(f"Agent '{step.agent_name}' not found in registry")

            spec = agent.spec  # May be None for backward-compat agents
            agent_id = agent.id

            # ── 1. Rate limit check ──
            if spec and spec.limits.rate_limit_rps > 0:
                from stratum.core.rate_limiter import RATE_LIMITER
                if not RATE_LIMITER.check_and_record(agent_id, spec.limits.rate_limit_rps):
                    step.status = StepStatus.RATE_LIMITED
                    step.skip_reason = (
                        f"Rate limited: {spec.limits.rate_limit_rps} calls/sec"
                    )
                    step.end_time = datetime.now()
                    return

            # ── 2. Call count check ──
            if spec and spec.limits.max_calls_per_run > 0:
                current_calls = self._run_call_counts.get(agent_id, 0)
                if current_calls >= spec.limits.max_calls_per_run:
                    step.status = StepStatus.SKIPPED_CALL_LIMIT
                    step.skip_reason = (
                        f"Call limit exceeded: {current_calls}/{spec.limits.max_calls_per_run}"
                    )
                    step.end_time = datetime.now()
                    return

            # ── 3. Token budget check ──
            # Estimate this step's cost using the agent's max_output_tokens limit.
            # If total + estimate would exceed budget, skip proactively.
            estimated_tokens = (
                spec.limits.max_output_tokens if spec else 1000
            )
            if (self._run_token_total + estimated_tokens) > self._max_total_tokens:
                step.status = StepStatus.SKIPPED_BUDGET_EXCEEDED
                step.skip_reason = (
                    f"Token budget exceeded (run total: {self._run_token_total:,} "
                    f"+ est. {estimated_tokens:,} > {self._max_total_tokens:,})"
                )
                step.end_time = datetime.now()
                return

            # ── 4. Permission check (placeholder—always passes in v0) ──
            # In a full implementation, required permissions would be checked
            # against spec.permissions here.

            # ── 5. Retry loop ──
            max_retries = agent.max_retries if spec else 0
            backoff = agent.retry_backoff_seconds if spec else 1.0
            max_attempts = max_retries + 1
            last_error: Optional[Exception] = None

            for attempt_num in range(1, max_attempts + 1):
                attempt_start = datetime.now()
                attempt_record = AttemptRecord(
                    attempt_number=attempt_num,
                    start_time=attempt_start,
                )

                try:
                    # Call the agent
                    result = agent.execute(
                        step.input_data,
                        api_key=self.api_key,
                        provider=self.provider,
                        model=self.model,
                    )

                    # Extract LLM metrics if present
                    from stratum.core.llm_client import LLMResponse
                    if isinstance(result, LLMResponse):
                        step.output_data = result.output
                        step.token_usage = result.total_tokens
                        step.cost = result.cost
                    elif isinstance(result, dict) and "_llm_response" in result:
                        llm_meta = result.pop("_llm_response")
                        step.output_data = result
                        step.token_usage = llm_meta.get("total_tokens", 0)
                        step.cost = llm_meta.get("cost", 0.0)
                    else:
                        step.output_data = result

                    # Record successful attempt
                    attempt_record.status = "completed"
                    attempt_record.end_time = datetime.now()
                    attempt_record.duration = (
                        attempt_record.end_time - attempt_start
                    ).total_seconds()
                    step.attempts.append(attempt_record)

                    # Update run-level tracking
                    self._run_call_counts[agent_id] = (
                        self._run_call_counts.get(agent_id, 0) + 1
                    )
                    self._run_token_total += step.token_usage

                    step.retry_count = attempt_num - 1
                    step.status = StepStatus.COMPLETED
                    step.end_time = datetime.now()
                    return

                except Exception as e:
                    last_error = e
                    attempt_record.status = "failed"
                    attempt_record.error = str(e)
                    attempt_record.end_time = datetime.now()
                    attempt_record.duration = (
                        attempt_record.end_time - attempt_start
                    ).total_seconds()
                    step.attempts.append(attempt_record)

                    # Check if retryable
                    if attempt_num < max_attempts:
                        from stratum.core.error_classifier import is_retryable
                        if not is_retryable(e):
                            break  # Non-retryable → stop immediately
                        # Wait before retry
                        time.sleep(backoff * attempt_num)

            # ── 6. All attempts failed → try fallback ──
            step.retry_count = len(step.attempts) - 1

            if spec and spec.fallback_agent_id:
                fallback_agent = get_agent_by_name(spec.fallback_agent_id)
                if fallback_agent:
                    try:
                        fallback_result = fallback_agent.execute(
                            step.input_data,
                            api_key=self.api_key,
                            provider=self.provider,
                            model=self.model,
                        )

                        from stratum.core.llm_client import LLMResponse
                        if isinstance(fallback_result, LLMResponse):
                            step.output_data = fallback_result.output
                            step.token_usage = fallback_result.total_tokens
                            step.cost = fallback_result.cost
                        elif isinstance(fallback_result, dict) and "_llm_response" in fallback_result:
                            llm_meta = fallback_result.pop("_llm_response")
                            step.output_data = fallback_result
                            step.token_usage = llm_meta.get("total_tokens", 0)
                            step.cost = llm_meta.get("cost", 0.0)
                        else:
                            step.output_data = fallback_result

                        step.fallback_used = True
                        step.fallback_agent_id = spec.fallback_agent_id
                        step.status = StepStatus.COMPLETED_WITH_FALLBACK

                        self._run_call_counts[agent_id] = (
                            self._run_call_counts.get(agent_id, 0) + 1
                        )
                        self._run_token_total += step.token_usage
                        step.end_time = datetime.now()
                        return

                    except Exception:
                        pass  # Fallback also failed — fall through to FAILED

            # ── 7. Final failure ──
            step.error = str(last_error) if last_error else "Unknown error"
            step.status = StepStatus.FAILED_RETRIES_EXCEEDED if max_retries > 0 else StepStatus.FAILED

        except Exception as e:
            step.error = str(e)
            step.status = StepStatus.FAILED

        finally:
            step.end_time = datetime.now()

    def _collect_output(self, run: ExecutionRun) -> dict[str, Any]:
        output = {}
        for step in run.steps:
            output[step.agent_name] = step.output_data
        return output
