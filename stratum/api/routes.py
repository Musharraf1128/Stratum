from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from stratum.core.execution_engine import ExecutionEngine
from stratum.core.replay_engine import ReplayEngine
from stratum.core.workflow import WorkflowGraph
from stratum.storage.file_run_store import FileRunStore

router = APIRouter()

workflow: Optional[WorkflowGraph] = None
run_store: Optional[FileRunStore] = None


def set_workflow(wf: WorkflowGraph):
    global workflow
    workflow = wf


def get_run_store() -> FileRunStore:
    global run_store
    if run_store is None:
        run_store = FileRunStore()
    return run_store


class RunRequest(BaseModel):
    input_data: dict[str, Any] = {}


class RunResponse(BaseModel):
    run_id: str
    status: str


class WorkflowResponse(BaseModel):
    name: str
    nodes: list[str]
    edges: list[tuple[str, str]]


class RunListResponse(BaseModel):
    runs: list[dict[str, Any]]


@router.get("/workflow", response_model=WorkflowResponse)
def get_workflow():
    if not workflow:
        raise HTTPException(status_code=404, detail="No workflow configured")
    return WorkflowResponse(
        name=workflow.name,
        nodes=workflow.get_nodes(),
        edges=workflow.get_edges(),
    )


@router.post("/run", response_model=RunResponse)
def create_run(request: RunRequest):
    if not workflow:
        raise HTTPException(status_code=404, detail="No workflow configured")

    engine = ExecutionEngine(workflow)
    run = engine.execute(request.input_data)
    get_run_store().save_run(run)

    return RunResponse(run_id=run.run_id, status=run.status.value)


@router.get("/runs", response_model=RunListResponse)
def list_runs():
    runs = get_run_store().list_runs()
    return RunListResponse(
        runs=[
            {
                "run_id": r.run_id,
                "workflow_name": r.workflow_name,
                "status": r.status.value,
                "duration": r.duration,
                "start_time": r.start_time.isoformat() if r.start_time else None,
            }
            for r in runs
        ]
    )


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    run = get_run_store().get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": run.run_id,
        "workflow_name": run.workflow_name,
        "status": run.status.value,
        "input_data": run.input_data,
        "output_data": run.output_data,
        "error": run.error,
        "duration": run.duration,
        "total_tokens": run.total_tokens,
        "start_time": run.start_time.isoformat() if run.start_time else None,
        "end_time": run.end_time.isoformat() if run.end_time else None,
        "steps": [
            {
                "step_id": s.step_id,
                "agent_name": s.agent_name,
                "status": s.status.value,
                "input_data": s.input_data,
                "output_data": s.output_data,
                "error": s.error,
                "duration": s.duration,
                "token_usage": s.token_usage,
            }
            for s in run.steps
        ],
    }


@router.post("/replay/{run_id}", response_model=RunResponse)
def replay_run(run_id: str):
    if not workflow:
        raise HTTPException(status_code=404, detail="No workflow configured")

    store = get_run_store()
    original_run = store.get_run(run_id)
    if not original_run:
        raise HTTPException(status_code=404, detail="Run not found")

    replay_engine = ReplayEngine(workflow, store)
    new_run_id = replay_engine.replay(run_id)
    new_run = store.get_run(new_run_id)

    if not new_run:
        raise HTTPException(status_code=500, detail="Failed to create replay run")

    return RunResponse(run_id=new_run.run_id, status=new_run.status.value)
