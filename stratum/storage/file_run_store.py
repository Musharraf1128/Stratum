from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from stratum.core.models import ExecutionRun, ExecutionStep, RunStatus, StepStatus
from stratum.storage.run_store import RunStore


class FileRunStore(RunStore):
    def __init__(self, runs_dir: str = "runs"):
        self.runs_dir = Path(runs_dir)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def clear(self) -> None:
        for file_path in self.runs_dir.glob("run_*.json"):
            file_path.unlink()

    def _run_file_path(self, run_id: str) -> Path:
        return self.runs_dir / f"run_{run_id}.json"

    def save_run(self, run: ExecutionRun) -> None:
        file_path = self._run_file_path(run.run_id)
        with open(file_path, "w") as f:
            json.dump(self._serialize_run(run), f, indent=2, default=str)

    def get_run(self, run_id: str) -> Optional[ExecutionRun]:
        file_path = self._run_file_path(run_id)
        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            data = json.load(f)
        return self._deserialize_run(data)

    def list_runs(self) -> list[ExecutionRun]:
        runs = []
        for file_path in self.runs_dir.glob("run_*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                runs.append(self._deserialize_run(data))
            except Exception:
                continue

        runs.sort(key=lambda r: r.start_time or datetime.min, reverse=True)
        return runs

    def delete_run(self, run_id: str) -> bool:
        file_path = self._run_file_path(run_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def _serialize_run(self, run: ExecutionRun) -> dict[str, Any]:
        return {
            "run_id": run.run_id,
            "workflow_name": run.workflow_name,
            "status": run.status.value,
            "steps": [self._serialize_step(step) for step in run.steps],
            "input_data": run.input_data,
            "output_data": run.output_data,
            "error": run.error,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
        }

    def _serialize_step(self, step: ExecutionStep) -> dict[str, Any]:
        return {
            "step_id": step.step_id,
            "agent_name": step.agent_name,
            "status": step.status.value,
            "input_data": step.input_data,
            "output_data": step.output_data,
            "error": step.error,
            "start_time": step.start_time.isoformat() if step.start_time else None,
            "end_time": step.end_time.isoformat() if step.end_time else None,
            "token_usage": step.token_usage,
        }

    def _deserialize_run(self, data: dict[str, Any]) -> ExecutionRun:
        steps = [self._deserialize_step(s) for s in data.get("steps", [])]
        return ExecutionRun(
            run_id=data["run_id"],
            workflow_name=data["workflow_name"],
            status=RunStatus(data["status"]),
            steps=steps,
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data"),
            error=data.get("error"),
            start_time=datetime.fromisoformat(data["start_time"])
            if data.get("start_time")
            else None,
            end_time=datetime.fromisoformat(data["end_time"])
            if data.get("end_time")
            else None,
        )

    def _deserialize_step(self, data: dict[str, Any]) -> ExecutionStep:
        return ExecutionStep(
            step_id=data["step_id"],
            agent_name=data["agent_name"],
            status=StepStatus(data["status"]),
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data"),
            error=data.get("error"),
            start_time=datetime.fromisoformat(data["start_time"])
            if data.get("start_time")
            else None,
            end_time=datetime.fromisoformat(data["end_time"])
            if data.get("end_time")
            else None,
            token_usage=data.get("token_usage", 0),
        )
