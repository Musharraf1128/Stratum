"""
Tests for SQLiteRunStore — persistence of runs, steps, and governance fields.
"""
import os
import tempfile

import pytest

from stratum.core.models import (
    AttemptRecord,
    ExecutionRun,
    ExecutionStep,
    RunStatus,
    StepStatus,
)
from stratum.storage.sqlite_run_store import SQLiteRunStore
from datetime import datetime


@pytest.fixture
def store():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    s = SQLiteRunStore(db_path=db_path)
    yield s
    try:
        os.unlink(db_path)
    except Exception:
        pass


def _make_run(steps=None, status=RunStatus.COMPLETED):
    return ExecutionRun(
        workflow_name="test_workflow",
        status=status,
        input_data={"key": "value"},
        output_data={"result": "ok"},
        start_time=datetime.now(),
        end_time=datetime.now(),
        steps=steps or [],
    )


def test_save_and_get_run(store):
    run = _make_run()
    store.save_run(run)

    loaded = store.get_run(run.run_id)
    assert loaded is not None
    assert loaded.run_id == run.run_id
    assert loaded.workflow_name == "test_workflow"
    assert loaded.status == RunStatus.COMPLETED
    assert loaded.input_data["key"] == "value"


def test_save_and_get_with_steps(store):
    step = ExecutionStep(
        agent_name="test_agent",
        status=StepStatus.COMPLETED,
        input_data={"in": "data"},
        output_data="output",
        start_time=datetime.now(),
        end_time=datetime.now(),
        token_usage=100,
        cost=0.001,
    )
    run = _make_run(steps=[step])
    store.save_run(run)

    loaded = store.get_run(run.run_id)
    assert len(loaded.steps) == 1
    assert loaded.steps[0].agent_name == "test_agent"
    assert loaded.steps[0].token_usage == 100


def test_governance_fields_persisted(store):
    attempt1 = AttemptRecord(
        attempt_number=1,
        status="failed",
        error="connection timeout",
        duration=0.5,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )
    attempt2 = AttemptRecord(
        attempt_number=2,
        status="completed",
        duration=0.3,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )

    step = ExecutionStep(
        agent_name="governed_agent",
        status=StepStatus.COMPLETED,
        retry_count=1,
        fallback_used=False,
        fallback_agent_id=None,
        attempts=[attempt1, attempt2],
        skip_reason=None,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )
    run = _make_run(steps=[step])
    store.save_run(run)

    loaded = store.get_run(run.run_id)
    loaded_step = loaded.steps[0]
    assert loaded_step.retry_count == 1
    assert loaded_step.fallback_used is False
    assert len(loaded_step.attempts) == 2
    assert loaded_step.attempts[0].status == "failed"
    assert loaded_step.attempts[0].error == "connection timeout"
    assert loaded_step.attempts[1].status == "completed"


def test_list_runs(store):
    run1 = _make_run()
    run2 = _make_run(status=RunStatus.FAILED)
    store.save_run(run1)
    store.save_run(run2)

    runs = store.list_runs()
    assert len(runs) >= 2
    run_ids = [r.run_id for r in runs]
    assert run1.run_id in run_ids
    assert run2.run_id in run_ids


def test_delete_run(store):
    run = _make_run()
    store.save_run(run)
    assert store.get_run(run.run_id) is not None

    store.delete_run(run.run_id)
    assert store.get_run(run.run_id) is None


def test_skip_reason_persisted(store):
    step = ExecutionStep(
        agent_name="skip_agent",
        status=StepStatus.SKIPPED_BUDGET_EXCEEDED,
        skip_reason="Token budget exceeded (run total: 50,000 / 20,000)",
        start_time=datetime.now(),
        end_time=datetime.now(),
    )
    run = _make_run(steps=[step])
    store.save_run(run)

    loaded = store.get_run(run.run_id)
    loaded_step = loaded.steps[0]
    assert loaded_step.status == StepStatus.SKIPPED_BUDGET_EXCEEDED
    assert "budget" in loaded_step.skip_reason.lower()
