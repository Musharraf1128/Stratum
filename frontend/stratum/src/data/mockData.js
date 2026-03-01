// ─── Workflow Definition ───────────────────────────────────────────────────────
export const DEMO_WORKFLOW = {
  id: "wf_research_001",
  name: "Research & Presentation Workflow",
  agents: [
    { id: "a1", name: "Topic Analyzer",      role: "Classifier", x: 120, y: 200, status: "completed" },
    { id: "a2", name: "Research Agent",       role: "Researcher", x: 340, y: 120, status: "completed" },
    { id: "a3", name: "Audience Agent",       role: "Researcher", x: 340, y: 290, status: "running"   },
    { id: "a4", name: "Storyline Architect",  role: "Planner",    x: 580, y: 200, status: "pending"   },
    { id: "a5", name: "Quality Validator",    role: "Validator",  x: 800, y: 200, status: "pending"   },
  ],
  edges: [
    { from: "a1", to: "a2" },
    { from: "a1", to: "a3" },
    { from: "a2", to: "a4" },
    { from: "a3", to: "a4" },
    { from: "a4", to: "a5" },
  ],
};

// ─── Execution Runs ────────────────────────────────────────────────────────────
export const RUNS = [
  {
    id: "run_001",
    workflow: "Research & Presentation",
    status: "completed",
    start: "2025-03-01 09:14:02",
    duration: "4m 32s",
    tokens: 18420,
    cost: "$0.092",
    steps: [
      {
        agentId: "a1", agentName: "Topic Analyzer", status: "completed",
        duration: "8.2s", tokens: 1240,
        input: "Research topic: Multi-agent AI orchestration trends in 2025",
        output: "Extracted key themes: orchestration, governance, cost-tracking. Classified as technical research.",
        error: null,
      },
      {
        agentId: "a2", agentName: "Research Agent", status: "completed",
        duration: "68.4s", tokens: 8760,
        input: "Research multi-agent AI orchestration trends in 2025",
        output: "Found 12 relevant papers. Key findings: LangGraph adoption up 340%, governance tooling gap identified, average enterprise running 8.3 agents...",
        error: null,
      },
      {
        agentId: "a3", agentName: "Audience Agent", status: "completed",
        duration: "52.1s", tokens: 4200,
        input: "Analyze target audience for multi-agent orchestration content",
        output: "Primary: CTOs and VPs Eng at Series B+. Secondary: AI platform engineers. Pain: visibility and cost control.",
        error: null,
      },
      {
        agentId: "a4", agentName: "Storyline Architect", status: "completed",
        duration: "44.7s", tokens: 3120,
        input: "Research findings + audience profile",
        output: "5-act narrative: Problem → Market shift → Current tools gap → Stratum solution → ROI proof",
        error: null,
      },
      {
        agentId: "a5", agentName: "Quality Validator", status: "completed",
        duration: "21.3s", tokens: 1100,
        input: "Full storyline for validation",
        output: "Score: 91/100. All sections coherent. Recommend adding cost comparison data.",
        error: null,
      },
    ],
  },
  {
    id: "run_002",
    workflow: "Research & Presentation",
    status: "running",
    start: "2025-03-01 10:02:17",
    duration: "1m 14s…",
    tokens: 9840,
    cost: "$0.049",
    steps: [
      {
        agentId: "a1", agentName: "Topic Analyzer", status: "completed",
        duration: "6.9s", tokens: 980,
        input: "Research topic: Enterprise LLM cost optimization strategies",
        output: "Classified as financial + technical. Key entities: LLM providers, cost per token, batching strategies.",
        error: null,
      },
      {
        agentId: "a2", agentName: "Research Agent", status: "running",
        duration: "…", tokens: 6200,
        input: "Research enterprise LLM cost optimization",
        output: "In progress…",
        error: null,
      },
      {
        agentId: "a3", agentName: "Audience Agent", status: "running",
        duration: "…", tokens: 2660,
        input: "Audience for LLM cost optimization content",
        output: "In progress…",
        error: null,
      },
      {
        agentId: "a4", agentName: "Storyline Architect", status: "pending",
        duration: "—", tokens: 0, input: "—", output: "—", error: null,
      },
      {
        agentId: "a5", agentName: "Quality Validator", status: "pending",
        duration: "—", tokens: 0, input: "—", output: "—", error: null,
      },
    ],
  },
  {
    id: "run_003",
    workflow: "Research & Presentation",
    status: "failed",
    start: "2025-03-01 08:30:44",
    duration: "1m 02s",
    tokens: 4100,
    cost: "$0.021",
    steps: [
      {
        agentId: "a1", agentName: "Topic Analyzer", status: "completed",
        duration: "7.1s", tokens: 1100,
        input: "Research topic: Blockchain supply chain applications",
        output: "Classified as blockchain + logistics. Entities extracted.",
        error: null,
      },
      {
        agentId: "a2", agentName: "Research Agent", status: "failed",
        duration: "54.8s", tokens: 3000,
        input: "Research blockchain supply chain", output: "",
        error: "RateLimitError: OpenAI API quota exceeded. Retry after 60s.",
      },
      {
        agentId: "a3", agentName: "Audience Agent", status: "skipped",
        duration: "—", tokens: 0, input: "—", output: "—",
        error: "Skipped due to upstream failure",
      },
      {
        agentId: "a4", agentName: "Storyline Architect", status: "skipped",
        duration: "—", tokens: 0, input: "—", output: "—", error: null,
      },
      {
        agentId: "a5", agentName: "Quality Validator", status: "skipped",
        duration: "—", tokens: 0, input: "—", output: "—", error: null,
      },
    ],
  },
];
