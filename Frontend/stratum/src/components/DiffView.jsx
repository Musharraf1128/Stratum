// components/DiffView.jsx
// Responsibility: Select two runs and an agent, then show side-by-side
// output comparison with metadata.

import { useState } from "react";
import { statusColor } from "../utils/statusHelpers";

function DiffColumn({ run, step, label }) {
  return (
    <div className="flex flex-col overflow-y-auto">
      {/* Sticky header */}
      <div className="sticky top-0 px-4 py-2 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur flex-shrink-0">
        <span className="text-xs font-mono text-zinc-500">{label}</span>
        {run && (
          <span className={`ml-2 text-xs font-mono ${statusColor(run.status)}`}>
            {run.status}
          </span>
        )}
      </div>

      <div className="p-4 space-y-3 flex-1">
        {step ? (
          <>
            <div className="space-y-1">
              <div className="text-xs font-mono text-zinc-600 uppercase tracking-wider">Output</div>
              <div className="text-xs text-zinc-300 font-mono bg-zinc-900/50 border border-zinc-800 rounded p-3 whitespace-pre-wrap leading-relaxed min-h-16">
                {step.output || "—"}
              </div>
            </div>
            <div className="flex gap-3 text-xs font-mono">
              <span className="text-zinc-600">
                tokens: <span className="text-zinc-400">{step.tokens}</span>
              </span>
              <span className="text-zinc-600">
                dur: <span className="text-zinc-400">{step.duration}</span>
              </span>
            </div>
            {step.error && (
              <div className="text-xs text-red-400 font-mono bg-red-950/20 border border-red-900 rounded p-2">
                {step.error}
              </div>
            )}
          </>
        ) : (
          <div className="text-zinc-700 text-xs font-mono italic">
            No data for this agent in this run
          </div>
        )}
      </div>
    </div>
  );
}

export default function DiffView({ runs, workflow }) {
  const [runAId, setRunAId] = useState(runs[0]?.id ?? "");
  const [runBId, setRunBId] = useState(runs[1]?.id ?? "");
  const agents = workflow?.agents || [];
  const [agentFilter, setAgentFilter] = useState(agents[0]?.id ?? "");

  const runA  = runs.find((r) => r.id === runAId);
  const runB  = runs.find((r) => r.id === runBId);
  const stepA = runA?.steps.find((s) => s.agentId === agentFilter);
  const stepB = runB?.steps.find((s) => s.agentId === agentFilter);

  const selectClass = "bg-zinc-900 border border-zinc-700 text-zinc-300 text-xs font-mono px-2 py-1.5 rounded focus:outline-none focus:border-orange-600";

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800 flex-shrink-0 flex-wrap">
        <span className="text-xs text-zinc-600 font-mono uppercase tracking-widest">
          Compare Runs
        </span>

        <div className="flex items-center gap-2 ml-2">
          <select value={runAId} onChange={(e) => setRunAId(e.target.value)} className={selectClass}>
            {runs.map((r) => <option key={r.id} value={r.id}>{r.id}</option>)}
          </select>
          <span className="text-zinc-600 text-xs font-mono">vs</span>
          <select value={runBId} onChange={(e) => setRunBId(e.target.value)} className={selectClass}>
            {runs.map((r) => <option key={r.id} value={r.id}>{r.id}</option>)}
          </select>
        </div>

        {/* Agent filter pills */}
        <div className="flex gap-1 ml-auto flex-wrap">
          {agents.map((a) => (
            <button
              key={a.id}
              onClick={() => setAgentFilter(a.id)}
              className={`px-2 py-1 text-xs font-mono rounded border transition-colors ${
                agentFilter === a.id
                  ? "border-orange-600 text-orange-400 bg-orange-950/30"
                  : "border-zinc-800 text-zinc-600 hover:border-zinc-600"
              }`}
            >
              {a.name.split(" ")[0]}
            </button>
          ))}
        </div>
      </div>

      {/* Side-by-side columns */}
      <div className="flex-1 grid grid-cols-2 divide-x divide-zinc-800 overflow-hidden">
        <DiffColumn run={runA} step={stepA} label={runAId} />
        <DiffColumn run={runB} step={stepB} label={runBId} />
      </div>
    </div>
  );
}
