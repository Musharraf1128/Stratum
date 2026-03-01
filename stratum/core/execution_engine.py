from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Optional

from stratum.core.models import ExecutionRun, ExecutionStep, RunStatus, StepStatus
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

    def execute(self, initial_input: Optional[dict[str, Any]] = None) -> ExecutionRun:
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
                if current_step and current_step.status == StepStatus.FAILED:
                    raise RuntimeError(
                        f"Agent '{agent_name}' failed: {current_step.error}"
                    )

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
                        and step.status == StepStatus.FAILED
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
                input_data[dep] = dep_step.output_data

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

    def _run_step(self, step: ExecutionStep) -> None:
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()

        try:
            from stratum.core.agent import get_agent_by_name

            agent = get_agent_by_name(step.agent_name)
            if not agent:
                raise ValueError(f"Agent '{step.agent_name}' not found in registry")

            # Pass api_key to the agent callable so it can use real LLM calls
            result = agent.execute(step.input_data, api_key=self.api_key, provider=self.provider, model=self.model)

            # If the result is an LLMResponse, extract metrics
            from stratum.core.llm_client import LLMResponse
            if isinstance(result, LLMResponse):
                step.output_data = result.output
                step.token_usage = result.total_tokens
                step.cost = result.cost
            elif isinstance(result, dict) and "_llm_response" in result:
                # Agent returned a dict with embedded LLM response metadata
                llm_meta = result.pop("_llm_response")
                step.output_data = result
                step.token_usage = llm_meta.get("total_tokens", 0)
                step.cost = llm_meta.get("cost", 0.0)
            else:
                step.output_data = result

            step.status = StepStatus.COMPLETED

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
