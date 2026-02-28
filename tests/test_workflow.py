import pytest
from stratum.core.workflow import WorkflowGraph


def test_workflow_creation():
    wf = WorkflowGraph(name="test_workflow")
    assert wf.name == "test_workflow"
    assert wf.get_nodes() == []


def test_add_agent():
    wf = WorkflowGraph()
    wf.add_agent("agent1").add_agent("agent2")
    assert wf.get_nodes() == ["agent1", "agent2"]


def test_connect_agents():
    wf = WorkflowGraph()
    wf.add_agent("a").add_agent("b").add_agent("c")
    wf.connect("a", "b").connect("b", "c")

    edges = wf.get_edges()
    assert ("a", "b") in edges
    assert ("b", "c") in edges


def test_cycle_detection():
    wf = WorkflowGraph()
    wf.add_agent("a").add_agent("b").add_agent("c")
    wf.connect("a", "b").connect("b", "c")

    with pytest.raises(ValueError, match="would create a cycle"):
        wf.connect("c", "a")


def test_topological_sort():
    wf = WorkflowGraph()
    wf.add_agent("start").add_agent("middle").add_agent("end")
    wf.connect("start", "middle").connect("middle", "end")

    order = wf.get_execution_order()
    assert order == ["start", "middle", "end"]


def test_get_dependencies():
    wf = WorkflowGraph()
    wf.add_agent("a").add_agent("b").add_agent("c")
    wf.connect("a", "c").connect("b", "c")

    deps = wf.get_dependencies("c")
    assert set(deps) == {"a", "b"}


def test_get_dependents():
    wf = WorkflowGraph()
    wf.add_agent("a").add_agent("b").add_agent("c")
    wf.connect("a", "b").connect("a", "c")

    dependents = wf.get_dependents("a")
    assert set(dependents) == {"b", "c"}


def test_validate_dag():
    wf = WorkflowGraph()
    wf.add_agent("a").add_agent("b").add_agent("c")
    wf.connect("a", "b").connect("b", "c")

    assert wf.validate() is True


def test_validate_cycle():
    wf = WorkflowGraph()
    wf.add_agent("a").add_agent("b").add_agent("c")
    wf.connect("a", "b").connect("b", "c")

    with pytest.raises(ValueError, match="would create a cycle"):
        wf.connect("c", "a")
