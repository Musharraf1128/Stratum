import os
import tempfile
from datetime import datetime

import pytest
from stratum.core.models import ExecutionRun, ExecutionStep, RunStatus, StepStatus
from stratum.storage.file_run_store import FileRunStore


@pytest.fixture
def temp_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield FileRunStore(runs_dir=tmpdir)


def test_save_and_get_run(temp_store):
    run = ExecutionRun(
        workflow_name="test_workflow",
        status=RunStatus.COMPLETED,
        input_data={"key": "value"},
    )
    run.steps.append(ExecutionStep(agent_name="agent1", status=StepStatus.COMPLETED))

    temp_store.save_run(run)
    retrieved = temp_store.get_run(run.run_id)

    assert retrieved is not None
    assert retrieved.workflow_name == "test_workflow"
    assert retrieved.status == RunStatus.COMPLETED
    assert len(retrieved.steps) == 1


def test_get_nonexistent_run(temp_store):
    result = temp_store.get_run("nonexistent-id")
    assert result is None


def test_list_runs(temp_store):
    run1 = ExecutionRun(workflow_name="wf1", status=RunStatus.COMPLETED)
    run2 = ExecutionRun(workflow_name="wf2", status=RunStatus.FAILED)

    temp_store.save_run(run1)
    temp_store.save_run(run2)

    runs = temp_store.list_runs()
    assert len(runs) == 2


def test_delete_run(temp_store):
    run = ExecutionRun(workflow_name="test", status=RunStatus.COMPLETED)
    temp_store.save_run(run)

    assert temp_store.delete_run(run.run_id) is True
    assert temp_store.get_run(run.run_id) is None

    assert temp_store.delete_run("nonexistent") is False
