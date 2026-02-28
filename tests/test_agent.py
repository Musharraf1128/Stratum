import pytest
from stratum.core.agent import (
    Agent,
    agent,
    get_agent,
    get_agent_by_name,
    list_agents,
    clear_registry,
)


def test_agent_creation():
    clear_registry()
    test_agent = Agent(name="test_agent", role="tester")
    assert test_agent.name == "test_agent"
    assert test_agent.role == "tester"
    assert test_agent.id is not None


def test_agent_execute():
    clear_registry()

    def hello(name: str) -> str:
        return f"Hello, {name}!"

    test_agent = Agent(name="greeter", callable=hello)
    result = test_agent.execute("World")
    assert result == "Hello, World!"


def test_agent_decorator():
    clear_registry()

    @agent(name="decorated_agent", role="decorator_test")
    def my_func(x: int) -> int:
        return x * 2

    assert my_func.name == "decorated_agent"
    assert my_func.role == "decorator_test"
    assert my_func.execute(5) == 10


def test_agent_registry():
    clear_registry()

    @agent(name="agent1", role="role1")
    def func1():
        return "agent1"

    @agent(name="agent2", role="role2")
    def func2():
        return "agent2"

    agents = list_agents()
    assert len(agents) == 2

    retrieved = get_agent_by_name("agent1")
    assert retrieved is not None
    assert retrieved.role == "role1"


def test_agent_requires_name():
    clear_registry()
    with pytest.raises(ValueError):
        Agent(name="")
