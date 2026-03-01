from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from stratum.core.agent import get_agent_by_name, list_agents, list_agent_specs
from stratum.core.execution_engine import ExecutionEngine
from stratum.core.replay_engine import ReplayEngine
from stratum.core.workflow import WorkflowGraph
from stratum.api.auth import verify_api_key

router = APIRouter()

workflow: Optional[WorkflowGraph] = None
run_store = None  # RunStore instance (set at startup)


def set_workflow(wf: WorkflowGraph):
    global workflow
    workflow = wf


def get_run_store():
    global run_store
    if run_store is None:
        from stratum.storage.sqlite_run_store import SQLiteRunStore
        db_path = os.getenv("STRATUM_DB_PATH", "stratum.db")
        run_store = SQLiteRunStore(db_path=db_path)
    return run_store


class RunRequest(BaseModel):
    input_data: dict[str, Any] = {}
    api_key: Optional[str] = None
    provider: str = "openai"
    model: Optional[str] = None


class ReplayRequest(BaseModel):
    api_key: Optional[str] = None
    provider: str = "openai"
    model: Optional[str] = None


class RunResponse(BaseModel):
    run_id: str
    status: str


# ─── GET /workflow ──────────────────────────────────────────────────────────────
@router.get("/workflow")
def get_workflow():
    if not workflow:
        raise HTTPException(status_code=404, detail="No workflow configured")

    agents = []
    for node_name in workflow.get_nodes():
        agent = get_agent_by_name(node_name)
        agents.append({
            "id": agent.id if agent else node_name,
            "name": node_name,
            "role": agent.role if agent else "",
        })

    edges = []
    for from_name, to_name in workflow.get_edges():
        edges.append({"from": from_name, "to": to_name})

    return {
        "name": workflow.name,
        "agents": agents,
        "edges": edges,
    }


# ─── GET /agents ────────────────────────────────────────────────────────────────
@router.get("/agents")
def get_agents():
    specs = list_agent_specs()
    if specs:
        return {
            "agents": [
                {
                    "agent_id": s.agent_id,
                    "name": s.name,
                    "role": s.role,
                    "description": s.description,
                    "permissions": sorted(s.permissions),
                    "limits": {
                        "max_input_tokens": s.limits.max_input_tokens,
                        "max_output_tokens": s.limits.max_output_tokens,
                        "max_calls_per_run": s.limits.max_calls_per_run,
                        "rate_limit_rps": s.limits.rate_limit_rps,
                        "max_total_tokens_per_run": s.limits.max_total_tokens_per_run,
                    },
                    "fallback_agent_id": s.fallback_agent_id,
                }
                for s in specs
            ]
        }
    # Fallback: return basic agent info if no specs available
    agents = list_agents()
    return {
        "agents": [
            {
                "agent_id": a.id,
                "name": a.name,
                "role": a.role,
                "description": "",
                "permissions": [],
                "limits": {},
                "fallback_agent_id": None,
            }
            for a in agents
        ]
    }


# ─── POST /run ──────────────────────────────────────────────────────────────────
@router.post("/run", response_model=RunResponse)
def create_run(request: RunRequest, _auth: bool = Depends(verify_api_key)):
    if not workflow:
        raise HTTPException(status_code=404, detail="No workflow configured")

    engine = ExecutionEngine(workflow, api_key=request.api_key, provider=request.provider, model=request.model)
    run = engine.execute(request.input_data)
    get_run_store().save_run(run)

    return RunResponse(run_id=run.run_id, status=run.status.value)


# ─── GET /runs ──────────────────────────────────────────────────────────────────
@router.get("/runs")
def list_runs():
    runs = get_run_store().list_runs()
    return {
        "runs": [
            {
                "run_id": r.run_id,
                "workflow_name": r.workflow_name,
                "status": r.status.value,
                "duration": r.duration,
                "total_tokens": r.total_tokens,
                "total_cost": r.total_cost,
                "step_count": len(r.steps),
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "error": r.error,
                # Governance summary
                "steps_skipped": sum(
                    1 for s in r.steps
                    if s.status.value.startswith("skipped")
                    or s.status.value in ("rate_limited", "permission_denied")
                ),
                "steps_with_fallback": sum(
                    1 for s in r.steps if s.fallback_used
                ),
                "steps_failed": sum(
                    1 for s in r.steps
                    if s.status.value in ("failed", "failed_retries_exceeded")
                ),
            }
            for r in runs
        ]
    }


# ─── GET /runs/{run_id} ────────────────────────────────────────────────────────
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
        "total_cost": run.total_cost,
        "start_time": run.start_time.isoformat() if run.start_time else None,
        "end_time": run.end_time.isoformat() if run.end_time else None,
        # NOTE: encrypted_api_key is deliberately excluded from responses
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
                "cost": s.cost,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                # Governance fields
                "retry_count": s.retry_count,
                "fallback_used": s.fallback_used,
                "fallback_agent_id": s.fallback_agent_id,
                "skip_reason": s.skip_reason,
                "attempts": [
                    {
                        "attempt_number": a.attempt_number,
                        "status": a.status,
                        "error": a.error,
                        "duration": a.duration,
                    }
                    for a in s.attempts
                ],
            }
            for s in run.steps
        ],
    }


# ─── POST /replay/{run_id} ─────────────────────────────────────────────────────
@router.post("/replay/{run_id}", response_model=RunResponse)
def replay_run(run_id: str, request: ReplayRequest = ReplayRequest(), _auth: bool = Depends(verify_api_key)):
    if not workflow:
        raise HTTPException(status_code=404, detail="No workflow configured")

    store = get_run_store()
    original_run = store.get_run(run_id)
    if not original_run:
        raise HTTPException(status_code=404, detail="Run not found")

    replay_engine = ReplayEngine(workflow, store, api_key=request.api_key, provider=request.provider, model=request.model)
    new_run_id = replay_engine.replay(run_id, api_key=request.api_key)
    new_run = store.get_run(new_run_id)

    if not new_run:
        raise HTTPException(status_code=500, detail="Failed to create replay run")

    return RunResponse(run_id=new_run.run_id, status=new_run.status.value)
