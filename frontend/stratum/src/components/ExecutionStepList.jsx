// components/ExecutionStepList.jsx
// Responsibility: Tabular list of execution steps for the selected run.
// Emits onStepClick so the detail panel can open.

import { statusDot } from "../utils/statusHelpers";

export default function ExecutionStepList({ steps, selectedStepId, onStepClick, workflow }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="border-t border-zinc-900 flex-shrink-0" style={{ maxHeight: 220 }}>
      <div className="px-4 py-2 border-b border-zinc-900">
        <span className="text-xs font-mono text-zinc-600 uppercase tracking-widest">
          Execution Steps
        </span>
      </div>

      <div className="overflow-y-auto" style={{ maxHeight: 176 }}>
        {steps.map((step, i) => (
          <div
            key={step.agentId}
            onClick={() => onStepClick(step, workflow?.agents.find((a) => a.id === step.agentId))}
            className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors hover:bg-zinc-900/40 divide-y-0 border-b border-zinc-900/40 ${
              selectedStepId === step.agentId ? "bg-zinc-900/60" : ""
            }`}
          >
            <span className="text-xs text-zinc-700 font-mono w-4 flex-shrink-0">{i + 1}</span>
            <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${statusDot(step.status)}`} />
            <span className="text-sm text-zinc-300 flex-1">{step.agentName}</span>
            <span className="text-xs font-mono text-zinc-600 flex-shrink-0">{step.duration}</span>
            <span className="text-xs font-mono text-zinc-700 flex-shrink-0 w-20 text-right">
              {step.tokens > 0 ? step.tokens.toLocaleString() + " tok" : "—"}
            </span>
            {step.error && (
              <span className="text-xs text-red-500 flex-shrink-0" title={step.error}>⚠</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
