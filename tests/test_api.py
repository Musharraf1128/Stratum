import pytest
from fastapi.testclient import TestClient

from stratum.api.routes import set_workflow, get_run_store
from stratum.api.server import app
from stratum.core.agent import agent, clear_registry
from stratum.core.workflow import WorkflowGraph


@pytest.fixture(autouse=True)
def setup():
    clear_registry()
    get_run_store().clear()
    yield
    clear_registry()
    get_run_store().clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def workflow_with_agents():
    @agent(name="a", role="test")
    def func_a(data: dict) -> str:
        return "result_a"

    @agent(name="b", role="test")
    def func_b(data: dict) -> str:
        return "result_b"

    wf = WorkflowGraph("demo")
    wf.add_agent("a").add_agent("b")
    set_workflow(wf)
    yield wf


def test_get_workflow(client, workflow_with_agents):
    response = client.get("/workflow")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "demo"
    assert "a" in data["nodes"]
    assert "b" in data["nodes"]


def test_create_run(client, workflow_with_agents):
    response = client.post("/run", json={"input_data": {"key": "value"}})
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "completed"


def test_list_runs(client, workflow_with_agents):
    client.post("/run", json={"input_data": {}})

    response = client.get("/runs")
    assert response.status_code == 200
    data = response.json()
    assert len(data["runs"]) >= 1


def test_get_run(client, workflow_with_agents):
    create_response = client.post("/run", json={"input_data": {}})
    run_id = create_response.json()["run_id"]

    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == run_id
    assert len(data["steps"]) >= 1


def test_get_nonexistent_run(client):
    response = client.get("/runs/nonexistent-id")
    assert response.status_code == 404


def test_replay_run(client, workflow_with_agents):
    create_response = client.post("/run", json={"input_data": {"test": "data"}})
    run_id = create_response.json()["run_id"]

    replay_response = client.post(f"/replay/{run_id}")
    assert replay_response.status_code == 200
    data = replay_response.json()
    assert data["run_id"] != run_id
    assert data["status"] == "completed"


def test_replay_nonexistent_run(client):
    response = client.post("/replay/nonexistent-id")
    assert response.status_code == 404
