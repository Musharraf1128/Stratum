// ─── Data adapters: API responses → frontend component shapes ─────────────────

/**
 * Auto-layout x/y positions for workflow agents.
 * Uses a simple topological layer-based layout.
 */
function layoutAgents(agents, edges) {
    const nameToAgent = {};
    agents.forEach((a) => (nameToAgent[a.name] = a));

    const inDegree = {};
    const children = {};
    agents.forEach((a) => {
        inDegree[a.name] = 0;
        children[a.name] = [];
    });
    edges.forEach((e) => {
        inDegree[e.to] = (inDegree[e.to] || 0) + 1;
        children[e.from] = children[e.from] || [];
        children[e.from].push(e.to);
    });

    // BFS layering (topological levels)
    const layers = [];
    let queue = agents.filter((a) => inDegree[a.name] === 0).map((a) => a.name);
    const visited = new Set();

    while (queue.length > 0) {
        layers.push([...queue]);
        queue.forEach((n) => visited.add(n));
        const next = [];
        queue.forEach((n) => {
            (children[n] || []).forEach((c) => {
                inDegree[c]--;
                if (inDegree[c] === 0 && !visited.has(c)) next.push(c);
            });
        });
        queue = next;
    }

    const LAYER_GAP_X = 220;
    const CANVAS_W = 980;
    const CANVAS_H = 340;
    const NODE_GAP_Y = 110;
    const START_X = 80;
    const positioned = {};

    layers.forEach((layer, li) => {
        const totalHeight = (layer.length - 1) * NODE_GAP_Y;
        const startY = Math.max(30, (CANVAS_H - totalHeight) / 2);
        layer.forEach((name, ni) => {
            positioned[name] = {
                x: START_X + li * LAYER_GAP_X,
                y: startY + ni * NODE_GAP_Y,
            };
        });
    });

    return positioned;
}

/**
 * Transform GET /workflow response → DEMO_WORKFLOW shape
 */
export function adaptWorkflow(apiWorkflow) {
    const positions = layoutAgents(apiWorkflow.agents, apiWorkflow.edges);

    const agents = apiWorkflow.agents.map((a) => ({
        id: a.name,
        name: a.name,
        role: a.role || "agent",
        x: positions[a.name]?.x ?? 100,
        y: positions[a.name]?.y ?? 200,
        status: "pending",
    }));

    return {
        name: apiWorkflow.name,
        agents,
        edges: apiWorkflow.edges,
    };
}


/**
 * Format seconds to human-readable duration string
 */
function formatDuration(seconds) {
    if (seconds == null) return "—";
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}m ${s.toString().padStart(2, "0")}s`;
}


/**
 * Format cost value to string
 */
function formatCost(cost) {
    if (!cost || cost === 0) return "$0.000";
    return `$${cost.toFixed(6)}`;
}


/**
 * Transform GET /runs/{id} step → frontend step shape
 */
function adaptStep(apiStep) {
    return {
        agentId: apiStep.agent_name,
        agentName: apiStep.agent_name,
        status: apiStep.status,
        duration: formatDuration(apiStep.duration),
        tokens: apiStep.token_usage || 0,
        cost: apiStep.cost || 0,
        input: typeof apiStep.input_data === "string"
            ? apiStep.input_data
            : JSON.stringify(apiStep.input_data, null, 2),
        output: typeof apiStep.output_data === "string"
            ? apiStep.output_data
            : JSON.stringify(apiStep.output_data, null, 2),
        error: apiStep.error || null,
        // Governance fields
        retryCount: apiStep.retry_count || 0,
        fallbackUsed: apiStep.fallback_used || false,
        fallbackAgentId: apiStep.fallback_agent_id || null,
        skipReason: apiStep.skip_reason || null,
        attempts: (apiStep.attempts || []).map((a) => ({
            number: a.attempt_number,
            status: a.status,
            error: a.error,
            duration: a.duration != null ? `${a.duration.toFixed(1)}s` : "—",
        })),
    };
}

/**
 * Transform GET /runs list response → RUNS shape
 */
export function adaptRuns(apiRunsList) {
    return apiRunsList.map((r) => ({
        id: r.run_id,
        workflow: r.workflow_name,
        status: r.status,
        start: r.start_time ? new Date(r.start_time).toLocaleString() : "—",
        duration: formatDuration(r.duration),
        tokens: r.total_tokens || 0,
        cost: formatCost(r.total_cost),
        steps: [],
        // Governance summary
        stepsSkipped: r.steps_skipped || 0,
        stepsWithFallback: r.steps_with_fallback || 0,
        stepsFailed: r.steps_failed || 0,
    }));
}

/**
 * Transform GET /runs/{id} response → full run with steps
 */
export function adaptRunDetail(apiRun) {
    return {
        id: apiRun.run_id,
        workflow: apiRun.workflow_name,
        status: apiRun.status,
        start: apiRun.start_time ? new Date(apiRun.start_time).toLocaleString() : "—",
        duration: formatDuration(apiRun.duration),
        tokens: apiRun.total_tokens || 0,
        cost: formatCost(apiRun.total_cost),
        error: apiRun.error || null,
        steps: (apiRun.steps || []).map(adaptStep),
    };
}
