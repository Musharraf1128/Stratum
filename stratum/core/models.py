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
    # Governance statuses
    SKIPPED_BUDGET_EXCEEDED = "skipped_budget_exceeded"
    SKIPPED_CALL_LIMIT = "skipped_call_limit"
    RATE_LIMITED = "rate_limited"
    PERMISSION_DENIED = "permission_denied"
    COMPLETED_WITH_FALLBACK = "completed_with_fallback"
    FAILED_RETRIES_EXCEEDED = "failed_retries_exceeded"


# ─── Governance: Agent Limits & Spec ────────────────────────────────────────────

@dataclass
class AgentLimits:
    """Resource limits enforced per agent per run."""
    max_input_tokens: int = 4000
    max_output_tokens: int = 1000
    max_calls_per_run: int = 10
    rate_limit_rps: float = 1.0  # calls per second
    max_total_tokens_per_run: int = 20000


# Type alias for agent permissions (a set of permission tag strings)
AgentPermissions = set[str]

# Standard permission tags
STANDARD_PERMISSIONS = {
    "call:llm",
    "read:kb",
    "read:code",
    "write:tickets",
    "call:external_api",
    "call:github",
    "read:pii",
}


@dataclass
class AgentSpec:
    """Full specification for a governed agent."""
    agent_id: str = ""
    name: str = ""
    role: str = ""
    description: str = ""
    permissions: set[str] = field(default_factory=set)
    limits: AgentLimits = field(default_factory=AgentLimits)
    fallback_agent_id: Optional[str] = None


# ─── Governance: Retry Tracking ─────────────────────────────────────────────────

@dataclass
class AttemptRecord:
    """Record of a single execution attempt within a retry loop."""
    attempt_number: int = 0
    status: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ─── Execution Models ───────────────────────────────────────────────────────────

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
    # Governance fields
    retry_count: int = 0
    fallback_used: bool = False
    fallback_agent_id: Optional[str] = None
    attempts: list[AttemptRecord] = field(default_factory=list)
    skip_reason: Optional[str] = None

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
