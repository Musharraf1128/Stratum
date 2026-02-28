from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Agent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    callable: Optional[Callable[..., Any]] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.name:
            raise ValueError("Agent name is required")

    def execute(self, *args, **kwargs) -> Any:
        if self.callable is None:
            raise ValueError(f"Agent '{self.name}' has no callable execution function")
        return self.callable(*args, **kwargs)


AGENT_REGISTRY: dict[str, Agent] = {}


def register_agent(agent: Agent) -> None:
    AGENT_REGISTRY[agent.id] = agent


def get_agent(agent_id: str) -> Optional[Agent]:
    return AGENT_REGISTRY.get(agent_id)


def get_agent_by_name(name: str) -> Optional[Agent]:
    for agent in AGENT_REGISTRY.values():
        if agent.name == name:
            return agent
    return None


def list_agents() -> list[Agent]:
    return list(AGENT_REGISTRY.values())


def clear_registry() -> None:
    AGENT_REGISTRY.clear()


def agent(
    name: str,
    role: str = "",
    metadata: Optional[dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Agent]:
    def decorator(func: Callable[..., Any]) -> Agent:
        agent_instance = Agent(
            name=name,
            role=role,
            metadata=metadata or {},
            callable=func,
        )
        register_agent(agent_instance)
        return agent_instance

    return decorator
