"""
Config loader for Stratum.

Reads stratum.config.json from the project root and merges operator-defined
overrides into the agent registry at startup.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from stratum.core.models import AgentLimits


_DEFAULT_CONFIG_PATH = "stratum.config.json"


def load_config(path: str | None = None) -> dict[str, Any]:
    """Read and parse stratum.config.json. Returns {} if file missing."""
    config_path = Path(path or os.getenv("STRATUM_CONFIG_PATH", _DEFAULT_CONFIG_PATH))
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return json.load(f)


def apply_config_to_registry(config: dict[str, Any] | None = None) -> None:
    """Merge config overrides into agent specs in the registry.

    For each agent listed in config["agents"], override the limits and/or
    permissions on the matching registered agent's spec.
    """
    if config is None:
        config = load_config()

    agents_config = config.get("agents", {})
    if not agents_config:
        return

    from stratum.core.agent import AGENT_REGISTRY

    for agent_instance in AGENT_REGISTRY.values():
        if agent_instance.spec is None:
            continue

        agent_overrides = agents_config.get(agent_instance.name, {})
        if not agent_overrides:
            continue

        # Override limits
        limits_overrides = agent_overrides.get("limits", {})
        if limits_overrides:
            spec_limits = agent_instance.spec.limits
            for limit_key, limit_value in limits_overrides.items():
                if hasattr(spec_limits, limit_key):
                    setattr(spec_limits, limit_key, limit_value)

        # Override permissions
        permissions_override = agent_overrides.get("permissions")
        if permissions_override is not None:
            agent_instance.spec.permissions = set(permissions_override)

        # Override fallback
        fallback_override = agent_overrides.get("fallback_agent_id")
        if fallback_override is not None:
            agent_instance.spec.fallback_agent_id = fallback_override
