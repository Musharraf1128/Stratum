# Stratum

**Graph-native execution control layer for multi-agent systems.**

Stratum gives you a DAG execution engine, parallel workflow orchestration, governance enforcement (token budgets, call limits, rate limiting, retries, fallbacks), SQLite persistence, and a React dashboard — all in one SDK.

---

## Quick Start

```bash
# Clone and install
git clone <repo-url> && cd Stratum
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn networkx pydantic cryptography python-dotenv

# Set up environment (optional — dev mode works without these)
cp .env.example .env

# Run backend
uvicorn stratum.api.server:app --reload

# Run frontend (in another terminal)
cd frontend/stratum && npm install && npm run dev
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

Open **http://localhost:5173** to see the dashboard.

---

## Define Agents

```python
from stratum.core.agent import agent
from stratum.core.models import AgentLimits

@agent(
    name="analyzer",
    role="processor",
    description="Analyzes input data using LLM",
    permissions={"call:llm", "read:kb"},
    limits=AgentLimits(
        max_input_tokens=4000,
        max_output_tokens=2000,
        max_calls_per_run=10,
        rate_limit_rps=1.0,
    ),
    fallback_agent_id="simple_analyzer",
    max_retries=2,
    retry_backoff_seconds=1.5,
)
def analyzer(data: dict, api_key=None, provider="openai", model=None) -> dict:
    # Your agent logic here
    return {"result": "analyzed"}
```

### Permissions

| Tag                 | Description                      |
|---------------------|----------------------------------|
| `call:llm`          | Can call LLM APIs                |
| `read:kb`           | Can read knowledge base          |
| `read:code`         | Can read code repositories       |
| `write:tickets`     | Can create/update tickets        |
| `call:external_api` | Can call external APIs           |
| `call:github`       | Can call GitHub API              |
| `read:pii`          | Can access PII data              |

### Limits

| Field                      | Default | Description                       |
|----------------------------|---------|-----------------------------------|
| `max_input_tokens`         | 4000    | Max input tokens per call         |
| `max_output_tokens`        | 1000    | Max output tokens per call        |
| `max_calls_per_run`        | 10      | Max calls for this agent per run  |
| `rate_limit_rps`           | 1.0     | Max calls per second              |
| `max_total_tokens_per_run` | 20000   | Token budget per run (all agents) |

---

## Config Overrides (`stratum.config.json`)

Operator-level overrides for agent limits and permissions:

```json
{
  "agents": {
    "analyzer": {
      "limits": { "max_calls_per_run": 5 },
      "permissions": ["call:llm"]
    }
  },
  "workflows": {
    "demo_workflow": { "max_total_tokens": 20000 }
  }
}
```

---

## Step Statuses

| Status                    | Meaning                                 |
|---------------------------|-----------------------------------------|
| `completed`               | Ran successfully                        |
| `completed_with_fallback` | Primary failed, fallback succeeded      |
| `failed`                  | Failed without retries configured       |
| `failed_retries_exceeded` | Failed after all retries exhausted      |
| `skipped_budget_exceeded` | Token budget exceeded, skipped          |
| `skipped_call_limit`      | Call limit per run exceeded, skipped    |
| `rate_limited`            | Call rate too fast, skipped             |
| `permission_denied`       | Missing required permission             |

---

## Environment Variables

| Variable            | Description                                | Required |
|----------------------|--------------------------------------------|----------|
| `STRATUM_API_KEY`   | API key for authenticating mutating routes | No (dev mode) |
| `STRATUM_SECRET_KEY`| Fernet key for encrypting stored API keys  | No (auto-generated) |
| `STRATUM_DB_PATH`   | SQLite database file path                  | No (default: `stratum.db`) |
| `STRATUM_CORS_ORIGIN` | Allowed CORS origin                      | No (default: `http://localhost:5173`) |

---

## API Endpoints

| Method | Endpoint           | Auth | Description                    |
|--------|-------------------|------|--------------------------------|
| GET    | `/workflow`       | No   | Get workflow graph              |
| GET    | `/agents`         | No   | Get all agent specs             |
| GET    | `/runs`           | No   | List all runs with summaries    |
| GET    | `/runs/{id}`      | No   | Get run details with steps      |
| POST   | `/run`            | Yes* | Execute a new run               |
| POST   | `/replay/{id}`    | Yes* | Replay an existing run          |

*Auth required only when `STRATUM_API_KEY` env var is set.

---

## Tests

```bash
python -m pytest tests/ -v
```

**55 tests** covering: agents, execution engine, governance enforcement, SQLite storage, config loader, API endpoints, replay, and workflow graph.

---

## License

MIT

---

## Contributing

This project is in early development. If you're interested in contributing or have feedback, open an issue or reach out.
