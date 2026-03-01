from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from stratum.core.models import AgentLimits, AgentSpec


@dataclass
class Agent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    callable: Optional[Callable[..., Any]] = field(default=None, repr=False)
    spec: Optional[AgentSpec] = field(default=None, repr=False)
    # Retry/fallback config (stored on Agent, read by engine)
    max_retries: int = 0
    retry_backoff_seconds: float = 1.0

    def __post_init__(self):
        if not self.name:
            raise ValueError("Agent name is required")

    def execute(self, *args, **kwargs) -> Any:
        if self.callable is None:
            raise ValueError(f"Agent '{self.name}' has no callable execution function")
        return self.callable(*args, **kwargs)


AGENT_REGISTRY: dict[str, Agent] = {}
AGENT_CALLABLE_REGISTRY: dict[str, Callable] = {}


def register_agent(agent_instance: Agent) -> None:
    AGENT_REGISTRY[agent_instance.id] = agent_instance
    if agent_instance.callable is not None:
        AGENT_CALLABLE_REGISTRY[agent_instance.id] = agent_instance.callable


def get_agent(agent_id: str) -> Optional[Agent]:
    return AGENT_REGISTRY.get(agent_id)


def get_agent_by_name(name: str) -> Optional[Agent]:
    for ag in AGENT_REGISTRY.values():
        if ag.name == name:
            return ag
    return None


def list_agents() -> list[Agent]:
    return list(AGENT_REGISTRY.values())


def get_agent_spec(agent_id: str) -> Optional[AgentSpec]:
    """Look up the AgentSpec for a given agent_id."""
    ag = AGENT_REGISTRY.get(agent_id)
    if ag and ag.spec:
        return ag.spec
    return None


def get_agent_spec_by_name(name: str) -> Optional[AgentSpec]:
    """Look up the AgentSpec for a given agent name."""
    ag = get_agent_by_name(name)
    if ag and ag.spec:
        return ag.spec
    return None


def list_agent_specs() -> list[AgentSpec]:
    """Return all AgentSpecs from the registry."""
    return [ag.spec for ag in AGENT_REGISTRY.values() if ag.spec is not None]


def clear_registry() -> None:
    AGENT_REGISTRY.clear()
    AGENT_CALLABLE_REGISTRY.clear()


def agent(
    name: str,
    role: str = "",
    metadata: Optional[dict[str, Any]] = None,
    # ── Governance fields (all optional for backward compat) ──
    description: str = "",
    permissions: Optional[set[str]] = None,
    limits: Optional[AgentLimits] = None,
    fallback_agent_id: Optional[str] = None,
    max_retries: int = 0,
    retry_backoff_seconds: float = 1.0,
) -> Callable[[Callable[..., Any]], Agent]:
    """Decorator to register an agent with optional governance spec."""
    def decorator(func: Callable[..., Any]) -> Agent:
        agent_id = str(uuid.uuid4())

        # Build the AgentSpec
        spec = AgentSpec(
            agent_id=agent_id,
            name=name,
            role=role,
            description=description,
            permissions=permissions or set(),
            limits=limits or AgentLimits(),
            fallback_agent_id=fallback_agent_id,
        )

        agent_instance = Agent(
            id=agent_id,
            name=name,
            role=role,
            metadata=metadata or {},
            callable=func,
            spec=spec,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )
        register_agent(agent_instance)
        return agent_instance

    return decorator
