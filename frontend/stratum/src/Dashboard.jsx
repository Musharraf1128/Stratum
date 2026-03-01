// Dashboard.jsx
// Responsibility: Root orchestrator. Owns all shared state and wires every child
// component. Fetches data from the Stratum backend API on mount.

import { useState, useCallback, useEffect } from "react";

import TopNav           from "./components/TopNav";
import StatsBar         from "./components/StatsBar";
import RunSidebar       from "./components/RunSidebar";
import CenterPane       from "./components/CenterPane";
import StepDetailPanel  from "./components/StepDetailPanel";
import ReplayToast      from "./components/ReplayToast";
import ApiSettingsModal from "./components/ApiSettingsModal";
import AgentsView       from "./components/AgentsView";

import { fetchWorkflow, fetchRuns, fetchRun, createRun, replayRun, fetchAgents } from "./api/stratum";
import { adaptWorkflow, adaptRuns, adaptRunDetail } from "./data/adapters";

// ─── Storage helpers ───────────────────────────────────────────────────────────
// API key is deliberately NOT persisted to localStorage (security).
// On page reload the user re-enters it. Provider preference is non-sensitive.
const PROVIDER_KEY = "stratum_provider";

function loadProvider() {
  try { return localStorage.getItem(PROVIDER_KEY) || "openai"; } catch { return "openai"; }
}
function saveProvider(p) {
  try { localStorage.setItem(PROVIDER_KEY, p); } catch { /* ignore */ }
}


export default function Dashboard() {
  // ── API key + provider state ─────────────────────────────────────────────────
  const [apiKey, setApiKey]               = useState(null);
  const [provider, setProvider]           = useState(loadProvider);
  const [serverAuthKey, setServerAuthKey] = useState(null);
  const [settingsOpen, setSettingsOpen]   = useState(false);

  const handleSaveApiKey = useCallback((key, prov, authKey) => {
    setApiKey(key);
    setProvider(prov);
    setServerAuthKey(authKey);
    saveProvider(prov);  // Only provider is persisted (non-sensitive)
  }, []);

  // ── Data from API ───────────────────────────────────────────────────────────
  const [workflow, setWorkflow]     = useState(null);
  const [runs, setRuns]             = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);

  // ── Shared UI state ─────────────────────────────────────────────────────────
  const [selectedRun,   setSelectedRun]   = useState(null);
  const [selectedNode,  setSelectedNode]  = useState(null);
  const [detailStep,    setDetailStep]    = useState(null);
  const [replayToast,   setReplayToast]   = useState(null);
  const [activeView,    setActiveView]    = useState("workflow");
  const [agentSpecs,    setAgentSpecs]    = useState([]);

  // ── Load workflow + runs on mount ───────────────────────────────────────────
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [wfData, runsData, agentsData] = await Promise.all([
        fetchWorkflow(),
        fetchRuns(),
        fetchAgents().catch(() => ({ agents: [] })),
      ]);

      const adaptedWorkflow = adaptWorkflow(wfData);
      const adaptedRuns = adaptRuns(runsData.runs);

      setWorkflow(adaptedWorkflow);
      setRuns(adaptedRuns);
      setAgentSpecs(agentsData.agents || []);

      // Auto-select first run if we have runs
      if (adaptedRuns.length > 0) {
        const firstRunDetail = await fetchRun(adaptedRuns[0].id);
        const fullRun = adaptRunDetail(firstRunDetail);
        setSelectedRun(fullRun);
        setRuns((prev) =>
          prev.map((r) => (r.id === fullRun.id ? fullRun : r))
        );
      }
    } catch (err) {
      console.error("Failed to load data:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ── Handlers ────────────────────────────────────────────────────────────────
  const handleSelectRun = useCallback(async (run) => {
    try {
      const runDetail = await fetchRun(run.id);
      const fullRun = adaptRunDetail(runDetail);
      setSelectedRun(fullRun);
      setSelectedNode(null);
      setDetailStep(null);
      setRuns((prev) =>
        prev.map((r) => (r.id === fullRun.id ? fullRun : r))
      );
    } catch (err) {
      console.error("Failed to fetch run detail:", err);
    }
  }, []);

  const handleNodeClick = useCallback((agent) => {
    if (!selectedRun) return;

    // Toggle: clicking the same node again closes the detail panel
    if (selectedNode?.id === agent.id) {
      setDetailStep(null);
      setSelectedNode(null);
      return;
    }

    const step = selectedRun.steps.find((s) => s.agentId === agent.id);
    if (step) {
      setDetailStep(step);
      setSelectedNode(agent);
    }
  }, [selectedRun, selectedNode]);

  const handleStepClick = useCallback((step, agent) => {
    setDetailStep(step);
    setSelectedNode(agent ?? null);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setDetailStep(null);
    setSelectedNode(null);
  }, []);

  const handleReplay = useCallback(async (run) => {
    try {
      setReplayToast(`Replaying ${run.id.slice(0, 8)}…`);
      const result = await replayRun(run.id, apiKey, provider, serverAuthKey);
      setReplayToast(`Replay created: ${result.run_id.slice(0, 8)}`);

      // Refresh runs list
      const runsData = await fetchRuns();
      const adaptedRuns = adaptRuns(runsData.runs);
      setRuns(adaptedRuns);

      // Auto-select the new replay run
      const newRunDetail = await fetchRun(result.run_id);
      const fullRun = adaptRunDetail(newRunDetail);
      setSelectedRun(fullRun);
      setRuns((prev) =>
        prev.map((r) => (r.id === fullRun.id ? fullRun : r))
      );
    } catch (err) {
      setReplayToast(`Replay failed: ${err.message}`);
    } finally {
      setTimeout(() => setReplayToast(null), 3000);
    }
  }, [apiKey, provider]);

  const handleNewRun = useCallback(async () => {
    try {
      setReplayToast("Starting new run…");
      const result = await createRun({ query: "New run from dashboard" }, apiKey, provider, serverAuthKey);
      setReplayToast(`Run created: ${result.run_id.slice(0, 8)}`);

      // Refresh runs list
      const runsData = await fetchRuns();
      const adaptedRuns = adaptRuns(runsData.runs);
      setRuns(adaptedRuns);

      // Auto-select the new run
      const newRunDetail = await fetchRun(result.run_id);
      const fullRun = adaptRunDetail(newRunDetail);
      setSelectedRun(fullRun);
      setRuns((prev) =>
        prev.map((r) => (r.id === fullRun.id ? fullRun : r))
      );
    } catch (err) {
      setReplayToast(`Run failed: ${err.message}`);
    } finally {
      setTimeout(() => setReplayToast(null), 3000);
    }
  }, [apiKey, provider]);

  // ── Loading / Error states ──────────────────────────────────────────────────
  if (loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ background: "#080808", color: "#e5e5e5", fontFamily: "system-ui, -apple-system, sans-serif" }}
      >
        <div className="text-center">
          <div className="text-xl font-light text-zinc-400 mb-2">Connecting to Stratum…</div>
          <div className="text-sm font-mono text-zinc-600">Loading workflow and runs</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ background: "#080808", color: "#e5e5e5", fontFamily: "system-ui, -apple-system, sans-serif" }}
      >
        <div className="text-center max-w-md">
          <div className="text-xl font-light text-red-400 mb-2">Connection Error</div>
          <div className="text-sm font-mono text-zinc-500 mb-4">{error}</div>
          <button
            onClick={loadData}
            className="px-4 py-2 text-sm font-mono border border-zinc-700 text-zinc-400 hover:border-orange-600 hover:text-orange-400 rounded transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!workflow) return null;

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div
      className="min-h-screen flex flex-col overflow-hidden"
      style={{ background: "#080808", color: "#e5e5e5", fontFamily: "system-ui, -apple-system, sans-serif" }}
    >
      <ReplayToast message={replayToast} />

      <ApiSettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        apiKey={apiKey}
        provider={provider}
        serverAuthKey={serverAuthKey}
        onSave={handleSaveApiKey}
      />

      <TopNav
        workflowName={workflow.name}
        onNewRun={handleNewRun}
        onOpenSettings={() => setSettingsOpen(true)}
        hasApiKey={!!apiKey}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* Main content area — conditional on activeView */}
      {activeView === "agents" ? (
        <AgentsView />
      ) : (
        <>
          <StatsBar runs={runs} agentCount={workflow.agents.length} />

          {/* Main 3-column layout */}
          <div
            className="flex flex-1 overflow-hidden"
            style={{ height: "calc(100vh - 108px)" }}
          >
            {/* Collapsible run sidebar */}
            <RunSidebar
              runs={runs}
              selectedRun={selectedRun}
              onSelect={handleSelectRun}
              onReplay={handleReplay}
            />

            {/* Graph / Diff center pane */}
            <CenterPane
              workflow={workflow}
              runs={runs}
              selectedRun={selectedRun}
              selectedNode={selectedNode}
              selectedStepId={detailStep?.agentId}
              onNodeClick={handleNodeClick}
              onStepClick={handleStepClick}
              agentSpecs={agentSpecs}
            />

            {/* Collapsible step detail right panel */}
            <StepDetailPanel step={detailStep} onClose={handleCloseDetail} />
          </div>
        </>
      )}
    </div>
  );
}
