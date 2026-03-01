from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    status: StepStatus = StepStatus.PENDING
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    token_usage: int = 0
    cost: float = 0.0

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class ExecutionRun:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str = ""
    status: RunStatus = RunStatus.PENDING
    steps: list[ExecutionStep] = field(default_factory=list)
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    encrypted_api_key: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def total_tokens(self) -> int:
        return sum(step.token_usage for step in self.steps)

    @property
    def total_cost(self) -> float:
        return sum(step.cost for step in self.steps)
