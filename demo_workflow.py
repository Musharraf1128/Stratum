"""
Demo Workflow - Stratum v0.2

This script defines the 5 demo agents and the fork/join workflow graph.
Agents make real LLM calls when an api_key is provided, otherwise they
use mock responses with realistic token counts — enabling governance
demos (budget enforcement, retry/fallback) without needing a real key.

Demo staging:
  - Default run:          All steps complete with mock token counts
  - Budget demo:          fetch_data(4200) + process_a(14300) = 18500 > 20k on process_b
  - Retry+Fallback demo:  STRATUM_DEMO_FAIL_AGENT=process_a forces that agent to fail
"""

import os
from stratum.core.agent import agent, list_agents
from stratum.core.execution_engine import ExecutionEngine
from stratum.core.models import AgentLimits
from stratum.core.replay_engine import ReplayEngine
from stratum.core.workflow import WorkflowGraph
from stratum.storage.file_run_store import FileRunStore


def _try_llm(api_key, prompt, system_prompt=None, provider="openai", model=None):
    """Call LLM if api_key is available, otherwise return None."""
    if not api_key:
        return None
    from stratum.core.llm_client import call_llm
    return call_llm(api_key, prompt, provider=provider, model=model, system_prompt=system_prompt)


def _should_fail(agent_name: str) -> bool:
    """Check if this agent should simulate failure (for demo staging)."""
    fail_agent = os.getenv("STRATUM_DEMO_FAIL_AGENT", "")
    return fail_agent.lower() == agent_name.lower()


# ─── simple_processor (fallback agent) ──────────────────────────────────────

@agent(
    name="simple_processor",
    role="fallback_processor",
    description="Lightweight fallback processor — no LLM, deterministic output",
    permissions=set(),
    limits=AgentLimits(max_input_tokens=2000, max_output_tokens=1000, max_calls_per_run=5),
    max_retries=0,
)
def simple_processor(data: dict, **kwargs) -> dict:
    """Deterministic fallback: runs without LLM, always succeeds."""
    results = data.get("fetch_data", {}).get("results", [])
    if isinstance(results, list):
        processed = [f"simple_{item}" for item in results]
    else:
        processed = [f"simple_processed: {str(results)[:100]}"]
    return {
        "processed": processed,
        "path": "A-fallback",
        "_llm_response": {"total_tokens": 50, "cost": 0.0},
    }


# ─── fetch_data ─────────────────────────────────────────────────────────────

@agent(
    name="fetch_data",
    role="data_fetcher",
    description="Fetches and normalizes input data from queries",
    permissions={"call:llm", "read:kb"},
    limits=AgentLimits(max_input_tokens=2000, max_output_tokens=1000, max_calls_per_run=3),
    max_retries=2,
    retry_backoff_seconds=1.0,
)
def fetch_data(data: dict, api_key: str = None, provider: str = "openai", model: str = None) -> dict:
    """Fetch and analyze input data."""
    if _should_fail("fetch_data"):
        raise ConnectionError("Simulated fetch_data failure for demo")

    query = data.get("query", "default query")

    llm_resp = _try_llm(
        api_key,
        f"You are a data fetching agent. Analyze this query and return a structured list of 3 key data points to research: {query}",
        system_prompt="You are a precise data extraction agent. Return concise, structured results.",
        provider=provider,
        model=model,
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

    # Mock response with realistic token count
    return {
        "results": ["market_trends_2024", "competitor_analysis", "user_sentiment_data"],
        "query": query,
        "source": "mock",
        "_llm_response": {"total_tokens": 4200, "cost": 0.000630},
    }


# ─── process_a ──────────────────────────────────────────────────────────────

@agent(
    name="process_a",
    role="processor",
    description="Processes data through analytical path A",
    permissions={"call:llm"},
    limits=AgentLimits(max_input_tokens=4000, max_output_tokens=2000, max_calls_per_run=10),
    fallback_agent_id="simple_processor",
    max_retries=2,
    retry_backoff_seconds=1.5,
)
def process_a(data: dict, api_key: str = None, provider: str = "openai", model: str = None) -> dict:
    """Process data through analytical path A."""
    if _should_fail("process_a"):
        raise ConnectionError("Simulated process_a failure — connection timeout")

    results = data.get("fetch_data", {}).get("results", [])

    llm_resp = _try_llm(
        api_key,
        f"You are an analytical processor. Take these data points and provide a concise analytical summary with key insights:\n\n{results}",
        system_prompt="You are a data analyst. Provide structured analytical insights.",
        provider=provider,
        model=model,
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

    # Mock response — high token count to trigger budget demo
    return {
        "processed": [
            "Trend analysis: market shifting toward AI-first solutions",
            "Competitor gap: 3 of 5 competitors lack governance features",
            "Sentiment: 78% positive on structured agent frameworks",
        ],
        "path": "A",
        "_llm_response": {"total_tokens": 14300, "cost": 0.002145},
    }


# ─── process_b ──────────────────────────────────────────────────────────────

@agent(
    name="process_b",
    role="processor",
    description="Processes data through synthesis path B",
    permissions={"call:llm"},
    limits=AgentLimits(max_input_tokens=4000, max_output_tokens=2000, max_calls_per_run=10),
    max_retries=1,
)
def process_b(data: dict, api_key: str = None, provider: str = "openai", model: str = None) -> dict:
    """Process data through synthesis path B."""
    if _should_fail("process_b"):
        raise ConnectionError("Simulated process_b failure for demo")

    results = data.get("fetch_data", {}).get("results", [])

    llm_resp = _try_llm(
        api_key,
        f"You are a synthesis processor. Take these data points and create a synthesized narrative combining all findings:\n\n{results}",
        system_prompt="You are a content synthesizer. Create cohesive narratives from data.",
        provider=provider,
        model=model,
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

    # Mock response
    return {
        "processed": [
            "Narrative: the convergence of AI governance and developer tooling",
            "Key finding: teams need visibility into agent behavior at runtime",
        ],
        "path": "B",
        "_llm_response": {"total_tokens": 8500, "cost": 0.001275},
    }


# ─── aggregate ──────────────────────────────────────────────────────────────

@agent(
    name="aggregate",
    role="aggregator",
    description="Aggregates results from multiple processing paths",
    permissions={"call:llm"},
    limits=AgentLimits(max_input_tokens=6000, max_output_tokens=1000, max_calls_per_run=5),
    max_retries=1,
)
def aggregate(data: dict, api_key: str = None, provider: str = "openai", model: str = None) -> dict:
    """Aggregate results from both processing paths."""
    path_a = data.get("process_a", {})
    path_b = data.get("process_b", {})

    # Gracefully handle skipped/missing paths
    processed_a = path_a.get("processed", []) if isinstance(path_a, dict) else []
    processed_b = path_b.get("processed", []) if isinstance(path_b, dict) else []

    llm_resp = _try_llm(
        api_key,
        f"You are an aggregation agent. Combine these two analyses into a unified summary:\n\nAnalysis A:\n{processed_a}\n\nSynthesis B:\n{processed_b}",
        system_prompt="You are a results aggregator. Produce a clear, unified summary.",
        provider=provider,
        model=model,
    )

    if llm_resp:
        return {
            "combined": llm_resp.output,
            "paths_used": sum(1 for p in [processed_a, processed_b] if p),
            "_llm_response": {
                "total_tokens": llm_resp.total_tokens,
                "cost": llm_resp.cost,
            },
        }

    # Mock response
    combined = []
    if isinstance(processed_a, list):
        combined.extend(processed_a)
    elif processed_a:
        combined.append(str(processed_a))
    if isinstance(processed_b, list):
        combined.extend(processed_b)
    elif processed_b:
        combined.append(str(processed_b))

    paths_used = sum(1 for p in [processed_a, processed_b] if p)
    note = "" if paths_used == 2 else " (partial — one path was skipped by governance)"

    return {
        "combined": combined,
        "paths_used": paths_used,
        "note": f"Aggregated from {paths_used} of 2 paths{note}",
        "_llm_response": {"total_tokens": 1000, "cost": 0.000150},
    }


# ─── format_output ──────────────────────────────────────────────────────────

@agent(
    name="format_output",
    role="formatter",
    description="Formats final output into polished executive summary",
    permissions={"call:llm"},
    limits=AgentLimits(max_input_tokens=2000, max_output_tokens=500, max_calls_per_run=3),
    max_retries=1,
)
def format_output(data: dict, api_key: str = None, provider: str = "openai", model: str = None) -> dict:
    """Format final output into a polished result."""
    agg = data.get("aggregate", {})
    combined = agg.get("combined", []) if isinstance(agg, dict) else []
    paths_used = agg.get("paths_used", 0) if isinstance(agg, dict) else 0

    llm_resp = _try_llm(
        api_key,
        f"You are a formatting agent. Take this aggregated content and format it as a clean, professional executive summary:\n\n{combined}",
        system_prompt="You are a professional document formatter. Create polished executive summaries.",
        provider=provider,
        model=model,
    )

    if llm_resp:
        return {
            "summary": llm_resp.output,
            "paths_used": paths_used,
            "_llm_response": {
                "total_tokens": llm_resp.total_tokens,
                "cost": llm_resp.cost,
            },
        }

    # Mock response
    if isinstance(combined, list):
        items = "\n".join(f"  • {c}" for c in combined)
    else:
        items = f"  {combined}"

    return {
        "summary": f"Executive Summary ({paths_used} sources):\n{items}",
        "paths_used": paths_used,
        "_llm_response": {"total_tokens": 2100, "cost": 0.000315},
    }


# ─── Workflow graph ─────────────────────────────────────────────────────────

def build_workflow() -> WorkflowGraph:
    """Build the demo workflow graph. Never change the structure."""
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
    print("STRATUM v0.2 - Demo Workflow")
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

    fail_agent = os.getenv("STRATUM_DEMO_FAIL_AGENT", "")
    if fail_agent:
        print(f"\n   ⚠ DEMO MODE: '{fail_agent}' will simulate failure")

    print("\n3. Running workflow execution (mock mode)...")
    engine = ExecutionEngine(workflow)
    run = engine.execute({"query": "Analyze AI governance market trends for 2024"})

    print(f"   Run ID: {run.run_id}")
    print(f"   Status: {run.status.value}")
    print(f"   Duration: {run.duration:.4f}s")
    print(f"   Steps: {len(run.steps)}")
    print(f"   Total tokens: {run.total_tokens}")
    print(f"   Total cost: ${run.total_cost:.6f}")

    print("\n   Step details:")
    for step in run.steps:
        badge = step.status.value
        extra = ""
        if step.retry_count > 0:
            extra += f" | retries={step.retry_count}"
        if step.fallback_used:
            extra += f" | fallback={step.fallback_agent_id}"
        if step.skip_reason:
            extra += f" | reason={step.skip_reason}"
        print(f"   {'✓' if 'completed' in badge else '⊘' if 'skipped' in badge else '✗'} {step.agent_name:20s} — {badge:30s} — {step.token_usage:,} tok{extra}")

    print("\n4. Saving run to storage...")
    store = FileRunStore()
    store.save_run(run)
    print(f"   Saved: runs/run_{run.run_id}.json")

    print("\n5. Replaying run...")
    replay_engine = ReplayEngine(workflow, store)
    new_run_id = replay_engine.replay(run.run_id)
    new_run = store.get_run(new_run_id)
    print(f"   New run ID: {new_run_id}")
    print(f"   Status: {new_run.status.value}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
