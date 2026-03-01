// ─── API client for Stratum backend ───────────────────────────────────────────
const API_BASE = "http://localhost:8000";

async function request(path, options = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    if (!res.ok) {
        const detail = await res.text();
        throw new Error(`API ${res.status}: ${detail}`);
    }
    return res.json();
}

/** GET /workflow — returns { name, agents[], edges[] } */
export function fetchWorkflow() {
    return request("/workflow");
}

/** GET /agents — returns { agents[] } */
export function fetchAgents() {
    return request("/agents");
}

/** GET /runs — returns { runs[] } */
export function fetchRuns() {
    return request("/runs");
}

/** GET /runs/:id — returns full run with steps */
export function fetchRun(runId) {
    return request(`/runs/${runId}`);
}

/** POST /run — creates and executes a new run */
export function createRun(inputData = {}, apiKey = null, provider = "openai") {
    const body = { input_data: inputData, provider };
    if (apiKey) body.api_key = apiKey;
    return request("/run", {
        method: "POST",
        body: JSON.stringify(body),
    });
}

/** POST /replay/:id — replays an existing run */
export function replayRun(runId, apiKey = null, provider = "openai") {
    const body = { provider };
    if (apiKey) body.api_key = apiKey;
    return request(`/replay/${runId}`, {
        method: "POST",
        body: JSON.stringify(body),
    });
}
