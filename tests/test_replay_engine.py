import tempfile

import pytest
from stratum.core.agent import agent, clear_registry
from stratum.core.execution_engine import ExecutionEngine
from stratum.core.models import RunStatus
from stratum.core.replay_engine import ReplayEngine
from stratum.core.workflow import WorkflowGraph
from stratum.storage.file_run_store import FileRunStore


@pytest.fixture(autouse=True)
def setup():
    clear_registry()
    yield
    clear_registry()


@pytest.fixture
def temp_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield FileRunStore(runs_dir=tmpdir)


def test_replay_creates_new_run(temp_store):
    wf = WorkflowGraph("test")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "result"

    engine = ExecutionEngine(wf)
    original_run = engine.execute({"input": "test"})
    temp_store.save_run(original_run)

    replay_engine = ReplayEngine(wf, temp_store)
    new_run_id = replay_engine.replay(original_run.run_id)

    assert new_run_id != original_run.run_id

    new_run = temp_store.get_run(new_run_id)
    assert new_run is not None
    assert new_run.status == RunStatus.COMPLETED
    assert new_run.input_data == original_run.input_data


def test_replay_nonexistent_run(temp_store):
    wf = WorkflowGraph("test")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "result"

    replay_engine = ReplayEngine(wf, temp_store)

    with pytest.raises(ValueError, match="not found"):
        replay_engine.replay("nonexistent-id")


def test_replay_preserves_input(temp_store):
    wf = WorkflowGraph("test")
    wf.add_agent("a")

    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return f"got: {data.get('input', 'nothing')}"

    engine = ExecutionEngine(wf)
    original_run = engine.execute({"input": "hello world"})
    temp_store.save_run(original_run)

    replay_engine = ReplayEngine(wf, temp_store)
    new_run_id = replay_engine.replay(original_run.run_id)

    new_run = temp_store.get_run(new_run_id)
    assert new_run.input_data == {"input": "hello world"}
