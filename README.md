# Stratum

**A graph-native execution control layer for multi-agent AI systems.**

Stratum gives developers building multi-agent workflows a structured way to define, execute, observe, and replay agent collaboration -- all from a single control plane.

---

## The Problem

As teams move from single-agent prototypes to multi-agent systems, they hit the same walls:

- **No structured orchestration** -- agents are wired together with ad-hoc glue code
- **No execution visibility** -- when something breaks in a 5-agent pipeline, good luck finding where
- **No cost tracking** -- LLM spend grows, but there's no per-agent or per-run breakdown
- **No replay or debugging** -- you can't re-run a workflow with the same input and compare what changed

Stratum solves this by treating multi-agent workflows as **directed graphs** with full execution tracing.

---

## What Stratum Does (v0)

| Capability | Description |
|---|---|
| **Graph-based workflows** | Define agent pipelines as DAGs with explicit dependencies and parallel branches |
| **Execution engine** | Run workflows sequentially or in parallel with automatic dependency resolution |
| **Full execution trace** | Every agent step logs input, output, duration, token usage, cost, and errors |
| **Replay** | Re-run any previous execution with the same input, get a new trace, compare results |
| **Multi-provider LLM support** | Built-in support for OpenAI, Claude, and Gemini with per-model cost tracking |
| **REST API** | FastAPI backend exposing all operations over HTTP |
| **Visual dashboard** | React frontend with workflow graph view, run history, step inspection, and diff view |

---

## Architecture

```
                    ┌───────────────────────────────────────┐
                    │           React Dashboard             │
                    │  Graph View · Run List · Step Detail  │
                    │           · Diff View                 │
                    └──────────────────┬────────────────────┘
                                       │ HTTP
                    ┌──────────────────▼────────────────────┐
                    │            FastAPI Server             │
                    │   /workflow · /run · /runs · /replay  │
                    └──────────────────┬────────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────┐
          │                            │                        │
  ┌───────▼────────────┐    ┌──────────▼────────────┐   ┌───────▼────────┐
  │  Agent Registry    │    │  Execution Engine     │   │    Run Store   │
  │  @agent decorator  │    │  Sequential/Parallel  │   │   JSON files   │
  └────────────────────┘    │  Dependency resolver  │   └────────────────┘
                            └──────────┬────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │         WorkflowGraph (DAG)         │
                    │       NetworkX · Topological Sort   │
                    │       Cycle detection · Validation  │
                    └─────────────────────────────────────┘
```

---

## Project Structure

```
stratum/
├── stratum/                  # Python SDK + backend
│   ├── core/
│   │   ├── agent.py          # @agent decorator, Agent class, registry
│   │   ├── workflow.py       # WorkflowGraph (NetworkX DAG)
│   │   ├── execution_engine.py  # Sequential + parallel execution
│   │   ├── replay_engine.py  # Re-run workflows from saved state
│   │   ├── models.py         # ExecutionRun, ExecutionStep, status enums
│   │   ├── llm_client.py     # Multi-provider LLM calls + cost tracking
│   │   └── crypto.py         # API key encryption at rest
│   ├── api/
│   │   ├── server.py         # FastAPI app factory
│   │   └── routes.py         # REST endpoints
│   └── storage/
│       ├── run_store.py      # Abstract storage interface
│       └── file_run_store.py # JSON file implementation
├── frontend/stratum/         # React dashboard (Vite)
│   └── src/
│       ├── Dashboard.jsx     # Root component
│       ├── components/       # WorkflowGraph, RunSidebar, StepDetailPanel, DiffView, etc.
│       └── api/stratum.js    # API client
├── tests/                    # pytest test suite
├── demo_workflow.py          # 5-agent demo with fork/join pattern
└── pyproject.toml            # Project dependencies
```

---

## Quickstart

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Node.js 18+ (for the frontend)

### Backend

```bash
# Clone the repo
git clone https://github.com/Musharraf1128/stratum.git
cd stratum

# Install dependencies
uv sync

# Run the demo workflow (no API key needed -- uses mock mode)
uv run python demo_workflow.py

# Start the API server
uv run uvicorn stratum.api.server:app --reload --port 8000
```

### Frontend

```bash
cd frontend/stratum
npm install
npm run dev
```

Open `http://localhost:5173` to access the dashboard.

### With real LLM calls

Set your API key through the dashboard's settings modal, or pass it in the API request:

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {"query": "Analyze market trends in AI infrastructure"},
    "api_key": "your-api-key",
    "provider": "openai"
  }'
```

Supported providers: `openai`, `claude`, `gemini`.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/workflow` | Returns workflow graph (agents + edges) |
| `GET` | `/agents` | Lists all registered agents |
| `POST` | `/run` | Executes the workflow with given input |
| `GET` | `/runs` | Lists all saved runs with summary stats |
| `GET` | `/runs/{run_id}` | Returns full run details including all steps |
| `POST` | `/replay/{run_id}` | Re-executes a run with the original input |

---

## Demo Workflow

The included demo (`demo_workflow.py`) defines a 5-agent pipeline with a fork/join pattern:

```
fetch_data ──┬──> process_a ──┬──> aggregate ──> format_output
             └──> process_b ──┘
```

`process_a` and `process_b` run in parallel, demonstrating Stratum's parallel execution support.

---

## Running Tests

```bash
uv run pytest tests/ -v
```

---

## The Bigger Picture

Stratum v0 is the foundation for a broader vision: **a control plane for AI agents in production**.

As enterprises move from 2-3 experimental agents to 50-100 agents across departments, the need for centralized orchestration, governance, and cost management becomes critical. The same problems developers face locally -- visibility, tracing, cost tracking -- become organizational problems at scale.

The roadmap beyond v0 includes:

- **Agent governance** -- policy enforcement, access controls, approval workflows
- **Cost budgets and alerts** -- per-agent, per-team, per-workflow spending limits
- **Audit trails** -- compliance-ready logs of what every agent did, why, and what data it touched
- **Framework-agnostic SDK** -- bring your own agents (LangChain, CrewAI, AutoGen, custom), Stratum handles the control layer
- **Multi-tenant deployment** -- teams share a single Stratum instance with isolated workspaces

The core thesis: **orchestration and governance will matter more than individual agent capability.** Stratum is the layer that makes multi-agent systems trustworthy, debuggable, and cost-effective.

---

## License

MIT

---

## Contributing

This project is in early development. If you're interested in contributing or have feedback, open an issue or reach out.
