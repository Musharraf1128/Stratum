"""
Tests for the governance enforcement engine:
  - Budget exceeded skip
  - Call limit skip
  - Rate limiting
  - Permission denied (placeholder)
  - Retry on transient failure
  - No retry on auth failure
  - Fallback after retry exhaustion
  - Attempt history recording
"""
import pytest

from stratum.core.agent import agent, clear_registry
from stratum.core.execution_engine import ExecutionEngine
from stratum.core.models import AgentLimits, ExecutionStep, RunStatus, StepStatus
from stratum.core.rate_limiter import RATE_LIMITER
from stratum.core.workflow import WorkflowGraph


@pytest.fixture(autouse=True)
def cleanup():
    clear_registry()
    RATE_LIMITER.reset()
    yield
    clear_registry()
    RATE_LIMITER.reset()


# ─── Budget exceeded ───────────────────────────────────────────────────────────

def test_budget_exceeded_skips_step():
    """When token total exceeds max, step should be skipped."""
    wf = WorkflowGraph("budget_test")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "result"

    engine = ExecutionEngine(wf)
    engine._max_total_tokens = 100
    engine._run_token_total = 200  # Already over budget

    step = ExecutionStep(agent_name="a", input_data={})
    engine._run_step(step)

    assert step.status == StepStatus.SKIPPED_BUDGET_EXCEEDED
    assert step.skip_reason is not None
    assert "budget" in step.skip_reason.lower()


# ─── Call limit ────────────────────────────────────────────────────────────────

def test_call_limit_skips_step():
    """When agent call count exceeds limit, step should be skipped."""
    wf = WorkflowGraph("call_limit_test")
    wf.add_agent("a")

    @agent(
        name="a", role="test",
        limits=AgentLimits(max_calls_per_run=1),
    )
    def func_a(data: dict, **kwargs) -> str:
        return "result"

    engine = ExecutionEngine(wf)
    # Simulate that agent has already been called once
    engine._run_call_counts[func_a.id] = 1

    step = ExecutionStep(agent_name="a", input_data={})
    engine._run_step(step)

    assert step.status == StepStatus.SKIPPED_CALL_LIMIT
    assert step.skip_reason is not None


# ─── Rate limiting ─────────────────────────────────────────────────────────────

def test_rate_limiting():
    """Agent should be rate-limited if called faster than allowed."""
    wf = WorkflowGraph("rate_test")
    wf.add_agent("a")

    @agent(
        name="a", role="test",
        limits=AgentLimits(rate_limit_rps=0.001),  # Very slow: 1 call per 1000 sec
    )
    def func_a(data: dict, **kwargs) -> str:
        return "result"

    # Pre-record a recent call → next call should be rate-limited
    RATE_LIMITER._last_call[func_a.id] = __import__("time").monotonic()

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    step = run.steps[0]
    assert step.status == StepStatus.RATE_LIMITED
    assert step.skip_reason is not None


# ─── Retry on transient failure ────────────────────────────────────────────────

def test_retry_on_transient_failure():
    """Agent with retries should retry on transient failures."""
    call_count = 0

    wf = WorkflowGraph("retry_test")
    wf.add_agent("a")

    @agent(name="a", role="test", max_retries=2, retry_backoff_seconds=0.01)
    def func_a(data: dict, **kwargs) -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("connection timeout")
        return "success"

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    step = run.steps[0]
    assert step.status == StepStatus.COMPLETED
    assert step.retry_count == 2
    assert len(step.attempts) == 3
    assert step.attempts[0].status == "failed"
    assert step.attempts[2].status == "completed"


# ─── No retry on auth failure ─────────────────────────────────────────────────

def test_no_retry_on_auth_failure():
    """Non-retryable errors (like 401 unauthorized) should stop immediately."""
    wf = WorkflowGraph("no_retry_test")
    wf.add_agent("a")

    @agent(name="a", role="test", max_retries=3, retry_backoff_seconds=0.01)
    def func_a(data: dict, **kwargs) -> str:
        raise ValueError("401 unauthorized")

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    step = run.steps[0]
    # Should fail without exhausting all retries
    assert step.status in (StepStatus.FAILED, StepStatus.FAILED_RETRIES_EXCEEDED)
    assert len(step.attempts) == 1  # Stopped after first attempt


# ─── Fallback agent ───────────────────────────────────────────────────────────

def test_fallback_agent_used():
    """When primary fails all retries, fallback agent should execute."""
    wf = WorkflowGraph("fallback_test")
    wf.add_agent("primary")

    @agent(name="fallback", role="fallback")
    def fallback_func(data: dict, **kwargs) -> str:
        return "fallback_result"

    @agent(
        name="primary", role="test",
        max_retries=1,
        retry_backoff_seconds=0.01,
        fallback_agent_id="fallback",
    )
    def func_primary(data: dict, **kwargs) -> str:
        raise ConnectionError("connection timeout")

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    step = run.steps[0]
    assert step.status == StepStatus.COMPLETED_WITH_FALLBACK
    assert step.fallback_used is True
    assert step.fallback_agent_id == "fallback"
    assert step.output_data == "fallback_result"


# ─── Attempt history ──────────────────────────────────────────────────────────

def test_attempt_history_recorded():
    """Each attempt should be recorded with proper metadata."""
    wf = WorkflowGraph("attempt_test")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "done"

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    step = run.steps[0]
    assert step.status == StepStatus.COMPLETED
    assert len(step.attempts) == 1
    attempt = step.attempts[0]
    assert attempt.attempt_number == 1
    assert attempt.status == "completed"
    assert attempt.duration >= 0
    assert attempt.start_time is not None
    assert attempt.end_time is not None


# ─── Normal execution still works ─────────────────────────────────────────────

def test_normal_execution_with_governance():
    """Standard execution should work normally with governance in place."""
    wf = WorkflowGraph("normal_gov")
    wf.add_agent("a").add_agent("b")
    wf.connect("a", "b")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "a_result"

    @agent(name="b", role="test")
    def func_b(data: dict, **kwargs) -> str:
        return f"b_got_{data.get('a', 'none')}"

    engine = ExecutionEngine(wf)
    run = engine.execute({"input": "test"})

    assert run.status == RunStatus.COMPLETED
    assert len(run.steps) == 2
    assert run.steps[0].status == StepStatus.COMPLETED
    assert run.steps[1].status == StepStatus.COMPLETED
    assert run.steps[0].output_data == "a_result"
