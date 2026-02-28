"""
Demo Workflow - Stratum v0.1.0

This script demonstrates the full Stratum functionality:
- Creating agents with @agent decorator
- Building a workflow graph with parallel branches
- Running execution
- Saving/retrieving runs
- Replaying runs
"""

from stratum.core.agent import agent, clear_registry, list_agents, get_agent_by_name
from stratum.core.execution_engine import ExecutionEngine
from stratum.core.replay_engine import ReplayEngine
from stratum.core.workflow import WorkflowGraph
from stratum.storage.file_run_store import FileRunStore


@agent(name="fetch_data", role="data_fetcher")
def fetch_data(data: dict) -> dict:
    """Fetch data from source"""
    query = data.get("query", "default query")
    print(f"[fetch_data] Processing query: {query}")
    return {
        "results": ["item1", "item2", "item3"],
        "query": query,
        "source": "database",
    }


@agent(name="process_a", role="processor")
def process_a(data: dict) -> dict:
    """Process data through path A"""
    results = data.get("fetch_data", {}).get("results", [])
    print(f"[process_a] Processing {len(results)} items")
    processed = [f"processed_{item}_A" for item in results]
    return {"processed": processed, "path": "A"}


@agent(name="process_b", role="processor")
def process_b(data: dict) -> dict:
    """Process data through path B"""
    results = data.get("fetch_data", {}).get("results", [])
    print(f"[process_b] Processing {len(results)} items")
    processed = [f"processed_{item}_B" for item in results]
    return {"processed": processed, "path": "B"}


@agent(name="aggregate", role="aggregator")
def aggregate(data: dict) -> dict:
    """Aggregate results from both paths"""
    path_a = data.get("process_a", {}).get("processed", [])
    path_b = data.get("process_b", {}).get("processed", [])
    print(f"[aggregate] Combining {len(path_a)} + {len(path_b)} items")
    return {"combined": path_a + path_b, "total": len(path_a) + len(path_b)}


@agent(name="format_output", role="formatter")
def format_output(data: dict) -> str:
    """Format final output"""
    combined = data.get("aggregate", {}).get("combined", [])
    total = data.get("aggregate", {}).get("total", 0)
    result = f"Final Output ({total} items): {', '.join(combined)}"
    print(f"[format_output] {result}")
    return result


def build_workflow() -> WorkflowGraph:
    """Build the demo workflow graph"""
    wf = WorkflowGraph("demo_workflow")

    wf.add_agent("fetch_data")
    wf.add_agent("process_a")
    wf.add_agent("process_b")
    wf.add_agent("aggregate")
    wf.add_agent("format_output")

    wf.connect("fetch_data", "process_a")
    wf.connect("fetch_data", "process_b")
    wf.connect("process_a", "aggregate")
    wf.connect("process_b", "aggregate")
    wf.connect("aggregate", "format_output")

    return wf


def main():
    print("=" * 60)
    print("STRATUM v0.1.0 - Demo Workflow")
    print("=" * 60)

    print("\n1. Registered agents:")
    agents = list_agents()
    print(f"   Total: {len(agents)} agents")
    for a in agents:
        print(f"   - {a.name} ({a.role})")

    print("\n2. Building workflow graph...")
    workflow = build_workflow()
    print(f"   Workflow: {workflow.name}")
    print(f"   Nodes: {workflow.get_nodes()}")
    print(f"   Edges: {workflow.get_edges()}")
    print(f"   Execution order: {workflow.get_execution_order()}")

    print("\n3. Running workflow execution...")
    engine = ExecutionEngine(workflow)
    run = engine.execute({"query": "SELECT * FROM users"})

    print(f"   Run ID: {run.run_id}")
    print(f"   Status: {run.status.value}")
    print(f"   Duration: {run.duration:.4f}s")
    print(f"   Steps: {len(run.steps)}")

    print("\n4. Saving run to storage...")
    store = FileRunStore()
    store.save_run(run)
    print(f"   Saved: runs/run_{run.run_id}.json")

    print("\n5. Retrieving run from storage...")
    retrieved = store.get_run(run.run_id)
    print(f"   Retrieved: {retrieved.run_id}")
    print(f"   Status: {retrieved.status.value}")

    print("\n6. Listing all runs...")
    all_runs = store.list_runs()
    print(f"   Total: {len(all_runs)} runs")

    print("\n7. Replaying run...")
    replay_engine = ReplayEngine(workflow, store)
    new_run_id = replay_engine.replay(run.run_id)
    print(f"   New run ID: {new_run_id}")

    new_run = store.get_run(new_run_id)
    print(f"   Status: {new_run.status.value}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
