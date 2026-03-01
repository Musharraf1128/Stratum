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

/** GET /agents — returns { agents[] } with full AgentSpec */
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

/**
 * POST /run — creates and executes a new run
 * @param {object} inputData - Input data for the run
 * @param {string|null} llmApiKey - LLM provider API key (sent in body for agents)
 * @param {string} provider - LLM provider name
 * @param {string|null} serverAuthKey - Stratum server auth key (sent as Bearer token)
 */
export function createRun(inputData = {}, llmApiKey = null, provider = "openai", serverAuthKey = null) {
    const body = { input_data: inputData, provider };
    if (llmApiKey) body.api_key = llmApiKey;
    const headers = { "Content-Type": "application/json" };
    if (serverAuthKey) headers["Authorization"] = `Bearer ${serverAuthKey}`;
    return request("/run", {
        method: "POST",
        headers,
        body: JSON.stringify(body),
    });
}

/**
 * POST /replay/:id — replays an existing run
 * @param {string} runId - Run ID to replay
 * @param {string|null} llmApiKey - LLM provider API key
 * @param {string} provider - LLM provider name
 * @param {string|null} serverAuthKey - Stratum server auth key
 */
export function replayRun(runId, llmApiKey = null, provider = "openai", serverAuthKey = null) {
    const body = { provider };
    if (llmApiKey) body.api_key = llmApiKey;
    const headers = { "Content-Type": "application/json" };
    if (serverAuthKey) headers["Authorization"] = `Bearer ${serverAuthKey}`;
    return request(`/replay/${runId}`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
    });
}
