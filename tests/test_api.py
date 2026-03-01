import os
import pytest
from fastapi.testclient import TestClient

from stratum.api.routes import set_workflow, get_run_store
from stratum.api.server import create_app
from stratum.core.agent import agent, clear_registry
from stratum.core.workflow import WorkflowGraph


@pytest.fixture(autouse=True)
def setup():
    clear_registry()
    store = get_run_store()
    store.clear()
    # Ensure no API key auth during tests
    os.environ.pop("STRATUM_API_KEY", None)
    yield
    clear_registry()
    store.clear()


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def workflow_with_agents():
    @agent(name="a", role="test")
    def func_a(data: dict, **kwargs) -> str:
        return "result_a"

    @agent(name="b", role="test")
    def func_b(data: dict, **kwargs) -> str:
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
    agent_names = [a["name"] for a in data["agents"]]
    assert "a" in agent_names
    assert "b" in agent_names


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

    # Governance summary fields present
    run = data["runs"][0]
    assert "steps_skipped" in run
    assert "steps_with_fallback" in run
    assert "steps_failed" in run


def test_get_run(client, workflow_with_agents):
    create_response = client.post("/run", json={"input_data": {}})
    run_id = create_response.json()["run_id"]

    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == run_id
    assert len(data["steps"]) >= 1

    # Governance fields in step response
    step = data["steps"][0]
    assert "retry_count" in step
    assert "fallback_used" in step
    assert "skip_reason" in step
    assert "attempts" in step


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


def test_agents_endpoint(client, workflow_with_agents):
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) >= 2
    agent_info = data["agents"][0]
    assert "name" in agent_info
    assert "permissions" in agent_info


def test_auth_required_when_env_var_set(client, workflow_with_agents):
    os.environ["STRATUM_API_KEY"] = "test_secret_key"
    try:
        # POST without auth should fail
        response = client.post("/run", json={"input_data": {}})
        assert response.status_code == 401

        # POST with correct auth should pass
        response = client.post(
            "/run",
            json={"input_data": {}},
            headers={"Authorization": "Bearer test_secret_key"},
        )
        assert response.status_code == 200

        # GET endpoints should still work without auth
        response = client.get("/runs")
        assert response.status_code == 200
    finally:
        os.environ.pop("STRATUM_API_KEY", None)
