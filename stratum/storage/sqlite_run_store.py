"""
SQLite implementation of RunStore.

Uses the stdlib sqlite3 module — no additional dependencies required.
Stores runs, steps, and agent specs in 3 tables with JSON-serialized
complex fields (input_data, output_data, attempts, etc.).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Optional

from stratum.core.models import (
    AttemptRecord,
    ExecutionRun,
    ExecutionStep,
    RunStatus,
    StepStatus,
)
from stratum.storage.run_store import RunStore


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    workflow_name   TEXT NOT NULL,
    status          TEXT NOT NULL,
    input_data      TEXT,
    output_data     TEXT,
    error           TEXT,
    start_time      TEXT,
    end_time        TEXT,
    total_tokens    INTEGER DEFAULT 0,
    total_cost      REAL DEFAULT 0.0,
    encrypted_api_key TEXT
);

CREATE TABLE IF NOT EXISTS steps (
    step_id         TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    agent_name      TEXT NOT NULL,
    status          TEXT NOT NULL,
    input_data      TEXT,
    output_data     TEXT,
    error           TEXT,
    skip_reason     TEXT,
    start_time      TEXT,
    end_time        TEXT,
    token_usage     INTEGER DEFAULT 0,
    cost            REAL DEFAULT 0.0,
    retry_count     INTEGER DEFAULT 0,
    fallback_used   INTEGER DEFAULT 0,
    fallback_agent_id TEXT,
    attempts        TEXT,
    step_order      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS agent_specs (
    agent_id        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    role            TEXT,
    description     TEXT,
    permissions     TEXT,
    limits          TEXT,
    fallback_agent_id TEXT,
    registered_at   TEXT
);
"""


class SQLiteRunStore(RunStore):
    def __init__(self, db_path: str = "stratum.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    # ─── RunStore interface ──────────────────────────────────────────────────────

    def save_run(self, run: ExecutionRun) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO runs
                   (run_id, workflow_name, status, input_data, output_data,
                    error, start_time, end_time, total_tokens, total_cost, encrypted_api_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run.run_id,
                    run.workflow_name,
                    run.status.value,
                    _json_dumps(run.input_data),
                    _json_dumps(run.output_data),
                    run.error,
                    _dt_str(run.start_time),
                    _dt_str(run.end_time),
                    run.total_tokens,
                    run.total_cost,
                    run.encrypted_api_key,
                ),
            )

            # Delete existing steps for this run (for re-saves)
            conn.execute("DELETE FROM steps WHERE run_id = ?", (run.run_id,))

            for i, step in enumerate(run.steps):
                conn.execute(
                    """INSERT INTO steps
                       (step_id, run_id, agent_name, status, input_data, output_data,
                        error, skip_reason, start_time, end_time, token_usage, cost,
                        retry_count, fallback_used, fallback_agent_id, attempts, step_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        step.step_id,
                        run.run_id,
                        step.agent_name,
                        step.status.value,
                        _json_dumps(step.input_data),
                        _json_dumps(step.output_data),
                        step.error,
                        step.skip_reason,
                        _dt_str(step.start_time),
                        _dt_str(step.end_time),
                        step.token_usage,
                        step.cost,
                        step.retry_count,
                        1 if step.fallback_used else 0,
                        step.fallback_agent_id,
                        _json_dumps(_serialize_attempts(step.attempts)),
                        i,
                    ),
                )

    def get_run(self, run_id: str) -> Optional[ExecutionRun]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not row:
                return None

            steps_rows = conn.execute(
                "SELECT * FROM steps WHERE run_id = ? ORDER BY step_order",
                (run_id,),
            ).fetchall()

            return _deserialize_run(dict(row), [dict(r) for r in steps_rows])

    def list_runs(self) -> list[ExecutionRun]:
        with self._connect() as conn:
            run_rows = conn.execute(
                "SELECT * FROM runs ORDER BY start_time DESC"
            ).fetchall()

            runs = []
            for run_row in run_rows:
                steps_rows = conn.execute(
                    "SELECT * FROM steps WHERE run_id = ? ORDER BY step_order",
                    (run_row["run_id"],),
                ).fetchall()
                try:
                    runs.append(
                        _deserialize_run(dict(run_row), [dict(r) for r in steps_rows])
                    )
                except Exception:
                    continue

            return runs

    def delete_run(self, run_id: str) -> bool:
        with self._connect() as conn:
            # Steps cascade-delete due to FK
            cursor = conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            return cursor.rowcount > 0

    def clear(self) -> None:
        """Clear all stored data (useful for tests)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM steps")
            conn.execute("DELETE FROM runs")

    # ─── Agent Spec persistence ──────────────────────────────────────────────────

    def save_agent_spec(self, spec_data: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO agent_specs
                   (agent_id, name, role, description, permissions, limits,
                    fallback_agent_id, registered_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    spec_data.get("agent_id", ""),
                    spec_data.get("name", ""),
                    spec_data.get("role", ""),
                    spec_data.get("description", ""),
                    _json_dumps(list(spec_data.get("permissions", []))),
                    _json_dumps(spec_data.get("limits", {})),
                    spec_data.get("fallback_agent_id"),
                    datetime.now().isoformat(),
                ),
            )


# ─── Helpers ────────────────────────────────────────────────────────────────────

def _json_dumps(obj: Any) -> Optional[str]:
    if obj is None:
        return None
    return json.dumps(obj, default=str)


def _dt_str(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _dt_parse(s: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(s) if s else None


def _serialize_attempts(attempts: list[AttemptRecord]) -> list[dict]:
    return [
        {
            "attempt_number": a.attempt_number,
            "status": a.status,
            "error": a.error,
            "duration": a.duration,
            "start_time": _dt_str(a.start_time),
            "end_time": _dt_str(a.end_time),
        }
        for a in attempts
    ]


def _deserialize_attempts(raw: Optional[str]) -> list[AttemptRecord]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return [
            AttemptRecord(
                attempt_number=a.get("attempt_number", 0),
                status=a.get("status", ""),
                error=a.get("error"),
                duration=a.get("duration", 0.0),
                start_time=_dt_parse(a.get("start_time")),
                end_time=_dt_parse(a.get("end_time")),
            )
            for a in parsed
        ]
    except (json.JSONDecodeError, TypeError):
        return []


def _deserialize_run(
    run_data: dict[str, Any], steps_data: list[dict[str, Any]]
) -> ExecutionRun:
    steps = []
    for s in steps_data:
        steps.append(
            ExecutionStep(
                step_id=s["step_id"],
                agent_name=s["agent_name"],
                status=StepStatus(s["status"]),
                input_data=json.loads(s["input_data"]) if s.get("input_data") else {},
                output_data=json.loads(s["output_data"]) if s.get("output_data") else None,
                error=s.get("error"),
                start_time=_dt_parse(s.get("start_time")),
                end_time=_dt_parse(s.get("end_time")),
                token_usage=s.get("token_usage", 0),
                cost=s.get("cost", 0.0),
                retry_count=s.get("retry_count", 0),
                fallback_used=bool(s.get("fallback_used", 0)),
                fallback_agent_id=s.get("fallback_agent_id"),
                attempts=_deserialize_attempts(s.get("attempts")),
                skip_reason=s.get("skip_reason"),
            )
        )

    return ExecutionRun(
        run_id=run_data["run_id"],
        workflow_name=run_data["workflow_name"],
        status=RunStatus(run_data["status"]),
        steps=steps,
        input_data=json.loads(run_data["input_data"]) if run_data.get("input_data") else {},
        output_data=json.loads(run_data["output_data"]) if run_data.get("output_data") else None,
        error=run_data.get("error"),
        start_time=_dt_parse(run_data.get("start_time")),
        end_time=_dt_parse(run_data.get("end_time")),
        encrypted_api_key=run_data.get("encrypted_api_key"),
    )
