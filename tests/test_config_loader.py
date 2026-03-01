"""
Tests for the config loader.
"""
import json
import os
import tempfile

import pytest

from stratum.core.agent import agent, clear_registry
from stratum.core.config_loader import load_config, apply_config_to_registry
from stratum.core.models import AgentLimits


@pytest.fixture(autouse=True)
def cleanup():
    clear_registry()
    yield
    clear_registry()


def test_config_overrides_limits():
    """Config file should override agent limits."""
    @agent(
        name="test_agent", role="test",
        limits=AgentLimits(max_input_tokens=4000),
    )
    def func(data: dict, **kwargs) -> str:
        return "ok"

    config = {
        "agents": {
            "test_agent": {
                "limits": {"max_input_tokens": 1000},
            }
        }
    }

    apply_config_to_registry(config)
    assert func.spec.limits.max_input_tokens == 1000


def test_missing_config_returns_empty():
    """load_config should return {} if file doesn't exist."""
    config = load_config("/nonexistent/path/to/config.json")
    assert config == {}


def test_partial_override_preserves_defaults():
    """Overriding one limit field should not reset others."""
    @agent(
        name="partial_agent", role="test",
        limits=AgentLimits(max_input_tokens=4000, max_output_tokens=2000, max_calls_per_run=10),
    )
    def func(data: dict, **kwargs) -> str:
        return "ok"

    config = {
        "agents": {
            "partial_agent": {
                "limits": {"max_calls_per_run": 3},  # Only override this
            }
        }
    }

    apply_config_to_registry(config)
    assert func.spec.limits.max_calls_per_run == 3
    assert func.spec.limits.max_input_tokens == 4000  # preserved
    assert func.spec.limits.max_output_tokens == 2000  # preserved


def test_config_overrides_permissions():
    """Config should be able to override agent permissions."""
    @agent(
        name="perm_agent", role="test",
        permissions={"call:llm", "read:kb"},
    )
    def func(data: dict, **kwargs) -> str:
        return "ok"

    config = {
        "agents": {
            "perm_agent": {
                "permissions": ["call:llm"],  # Restrict to just one
            }
        }
    }

    apply_config_to_registry(config)
    assert func.spec.permissions == {"call:llm"}


def test_load_config_from_file():
    """Config should be loadable from an actual JSON file."""
    config_data = {
        "agents": {
            "file_agent": {
                "limits": {"max_input_tokens": 500}
            }
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        f.flush()
        config = load_config(f.name)
    os.unlink(f.name)

    assert config["agents"]["file_agent"]["limits"]["max_input_tokens"] == 500
