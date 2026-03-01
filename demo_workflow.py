"""
Demo Workflow - Stratum v0.1.0

This script demonstrates the full Stratum functionality:
- Creating agents with @agent decorator
- Building a workflow graph with parallel branches
- Running execution
- Saving/retrieving runs
- Replaying runs

When an api_key is provided, agents make real LLM calls.
When no key is provided, agents use mock/hardcoded logic.
"""

from stratum.core.agent import agent, clear_registry, list_agents, get_agent_by_name
from stratum.core.execution_engine import ExecutionEngine
from stratum.core.replay_engine import ReplayEngine
from stratum.core.workflow import WorkflowGraph
from stratum.storage.file_run_store import FileRunStore


def _try_llm(api_key, prompt, system_prompt=None, provider="openai"):
    """Call LLM if api_key is available, otherwise return None."""
    if not api_key:
        return None
    from stratum.core.llm_client import call_llm
    return call_llm(api_key, prompt, provider=provider, system_prompt=system_prompt)


@agent(name="fetch_data", role="data_fetcher")
def fetch_data(data: dict, api_key: str = None, provider: str = "openai") -> dict:
    """Fetch and analyze input data."""
    query = data.get("query", "default query")

    llm_resp = _try_llm(
        api_key,
        f"You are a data fetching agent. Analyze this query and return a structured list of 3 key data points to research: {query}",
        system_prompt="You are a precise data extraction agent. Return concise, structured results.",
        provider=provider,
    )

    if llm_resp:
        return {
            "results": llm_resp.output,
            "query": query,
            "source": "llm",
            "_llm_response": {
                "total_tokens": llm_resp.total_tokens,
                "cost": llm_resp.cost,
            },
        }

    # Fallback: mock logic
    return {
        "results": ["item1", "item2", "item3"],
        "query": query,
        "source": "mock",
    }


@agent(name="process_a", role="processor")
def process_a(data: dict, api_key: str = None, provider: str = "openai") -> dict:
    """Process data through analytical path A."""
    results = data.get("fetch_data", {}).get("results", [])

    llm_resp = _try_llm(
        api_key,
        f"You are an analytical processor. Take these data points and provide a concise analytical summary with key insights:\n\n{results}",
        system_prompt="You are a data analyst. Provide structured analytical insights.",
        provider=provider,
    )

    if llm_resp:
        return {
            "processed": llm_resp.output,
            "path": "A",
            "_llm_response": {
                "total_tokens": llm_resp.total_tokens,
                "cost": llm_resp.cost,
            },
        }

    # Fallback
    if isinstance(results, list):
        processed = [f"processed_{item}_A" for item in results]
    else:
        processed = [f"processed_A: {results}"]
    return {"processed": processed, "path": "A"}


@agent(name="process_b", role="processor")
def process_b(data: dict, api_key: str = None, provider: str = "openai") -> dict:
    """Process data through synthesis path B."""
    results = data.get("fetch_data", {}).get("results", [])

    llm_resp = _try_llm(
        api_key,
        f"You are a synthesis processor. Take these data points and create a synthesized narrative combining all findings:\n\n{results}",
        system_prompt="You are a content synthesizer. Create cohesive narratives from data.",
        provider=provider,
    )

    if llm_resp:
        return {
            "processed": llm_resp.output,
            "path": "B",
            "_llm_response": {
                "total_tokens": llm_resp.total_tokens,
                "cost": llm_resp.cost,
            },
        }

    # Fallback
    if isinstance(results, list):
        processed = [f"processed_{item}_B" for item in results]
    else:
        processed = [f"processed_B: {results}"]
    return {"processed": processed, "path": "B"}


@agent(name="aggregate", role="aggregator")
def aggregate(data: dict, api_key: str = None, provider: str = "openai") -> dict:
    """Aggregate results from both processing paths."""
    path_a = data.get("process_a", {}).get("processed", [])
    path_b = data.get("process_b", {}).get("processed", [])

    llm_resp = _try_llm(
        api_key,
        f"You are an aggregation agent. Combine these two analyses into a unified summary:\n\nAnalysis A:\n{path_a}\n\nSynthesis B:\n{path_b}",
        system_prompt="You are a results aggregator. Produce a clear, unified summary.",
        provider=provider,
    )

    if llm_resp:
        return {
            "combined": llm_resp.output,
            "total": 2,
            "_llm_response": {
                "total_tokens": llm_resp.total_tokens,
                "cost": llm_resp.cost,
            },
        }

    # Fallback
    combined = []
    if isinstance(path_a, list):
        combined.extend(path_a)
    else:
        combined.append(str(path_a))
    if isinstance(path_b, list):
        combined.extend(path_b)
    else:
        combined.append(str(path_b))
    return {"combined": combined, "total": len(combined)}


@agent(name="format_output", role="formatter")
def format_output(data: dict, api_key: str = None, provider: str = "openai") -> str:
    """Format final output into a polished result."""
    combined = data.get("aggregate", {}).get("combined", [])
    total = data.get("aggregate", {}).get("total", 0)

    llm_resp = _try_llm(
        api_key,
        f"You are a formatting agent. Take this aggregated content and format it as a clean, professional executive summary:\n\n{combined}",
        system_prompt="You are a professional document formatter. Create polished executive summaries.",
        provider=provider,
    )

    if llm_resp:
        # Return the LLM response directly — the engine will extract metrics
        return llm_resp

    # Fallback
    if isinstance(combined, list):
        result = f"Final Output ({total} items): {', '.join(str(c) for c in combined)}"
    else:
        result = f"Final Output: {combined}"
    return result


def build_workflow() -> WorkflowGraph:
    """Build the demo workflow graph."""
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

    print("\n3. Running workflow execution (mock mode)...")
    engine = ExecutionEngine(workflow)
    run = engine.execute({"query": "SELECT * FROM users"})

    print(f"   Run ID: {run.run_id}")
    print(f"   Status: {run.status.value}")
    print(f"   Duration: {run.duration:.4f}s")
    print(f"   Steps: {len(run.steps)}")
    print(f"   Total tokens: {run.total_tokens}")
    print(f"   Total cost: ${run.total_cost:.6f}")

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
