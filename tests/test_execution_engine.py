import pytest
from stratum.core.agent import agent, clear_registry
from stratum.core.execution_engine import ExecutionEngine
from stratum.core.models import RunStatus, StepStatus
from stratum.core.workflow import WorkflowGraph


@pytest.fixture(autouse=True)
def setup():
    clear_registry()
    yield
    clear_registry()


def test_execution_run_creation():
    wf = WorkflowGraph("test")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "done"

    engine = ExecutionEngine(wf)
    run = engine.execute({"input": "test"})

    assert run.workflow_name == "test"
    assert run.status == RunStatus.COMPLETED
    assert run.duration is not None


def test_execution_order():
    wf = WorkflowGraph("linear")
    wf.add_agent("a").add_agent("b").add_agent("c")
    wf.connect("a", "b").connect("b", "c")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "a_done"

    @agent(name="b", role="test")
    def func_b(data: dict, **kwargs) -> str:
        return f"b_got_{data.get('a', 'nothing')}"

    @agent(name="c", role="test")
    def func_c(data: dict, **kwargs) -> str:
        return f"c_got_{data.get('b', 'nothing')}"

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    assert run.status == RunStatus.COMPLETED
    assert run.steps[0].output_data == "a_done"
    assert run.steps[1].output_data == "b_got_a_done"
    assert run.steps[2].output_data == "c_got_b_got_a_done"


def test_parallel_execution():
    wf = WorkflowGraph("parallel")
    wf.add_agent("a").add_agent("b").add_agent("c")
    wf.connect("a", "b").connect("a", "c")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "a_done"

    @agent(name="b", role="test")
    def func_b(data: dict, **kwargs) -> str:
        return f"b_got_{data.get('a')}"

    @agent(name="c", role="test")
    def func_c(data: dict, **kwargs) -> str:
        return f"c_got_{data.get('a')}"

    engine = ExecutionEngine(wf)
    run = engine.execute_parallel({})

    assert run.status == RunStatus.COMPLETED
    assert run.steps[0].agent_name == "a"


def test_step_duration_recorded():
    wf = WorkflowGraph("test")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "done"

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    step = run.steps[0]
    assert step.duration is not None
    assert step.duration >= 0


def test_run_failure():
    wf = WorkflowGraph("failing")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        raise ValueError("Something went wrong")

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    assert run.status == RunStatus.FAILED
    assert "Something went wrong" in run.error


def test_total_tokens():
    wf = WorkflowGraph("test")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "done"

    engine = ExecutionEngine(wf)
    run = engine.execute({})

    assert run.total_tokens == 0
