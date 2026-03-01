// components/CenterPane.jsx
// Responsibility: Tabbed container that hosts the Graph View (WorkflowGraph +
// ExecutionStepList) and the Diff View. Manages tab state locally.

import { useState } from "react";
import WorkflowGraph        from "./WorkflowGraph";
import ExecutionStepList    from "./ExecutionStepList";
import DiffView             from "./DiffView";
import { statusColor }      from "../utils/statusHelpers";

const TABS = [
  { key: "graph", label: "GRAPH VIEW"    },
  { key: "diff",  label: "DIFF / COMPARE" },
];

export default function CenterPane({
  workflow,
  runs,
  selectedRun,
  selectedNode,
  selectedStepId,
  onNodeClick,
  onStepClick,
  agentSpecs,
}) {
  const [activeTab, setActiveTab] = useState("graph");

  return (
    <div className="flex-1 flex flex-col overflow-hidden border-r border-zinc-900 min-w-0">
      {/* Tab bar */}
      <div className="flex border-b border-zinc-900 flex-shrink-0">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-5 py-3 text-xs font-mono tracking-wider border-b-2 transition-colors ${
              activeTab === key
                ? "border-orange-500 text-orange-400"
                : "border-transparent text-zinc-600 hover:text-zinc-400"
            }`}
          >
            {label}
          </button>
        ))}

        {/* Active run context badge */}
        {selectedRun && activeTab === "graph" && (
          <div className="ml-auto flex items-center px-4 gap-3">
            <span className="text-xs font-mono text-zinc-600">{selectedRun.id}</span>
            <span className={`text-xs font-mono ${statusColor(selectedRun.status)}`}>
              {selectedRun.status}
            </span>
            <span className="text-xs font-mono text-zinc-600">
              {selectedRun.tokens.toLocaleString()} tokens
            </span>
          </div>
        )}
      </div>

      {/* Tab panels */}
      {activeTab === "graph" ? (
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Graph takes all available vertical space */}
          <div className="flex-1 overflow-hidden">
            <WorkflowGraph
              workflow={workflow}
              selectedNode={selectedNode}
              onNodeClick={onNodeClick}
              activeRunSteps={selectedRun?.steps}
              agentSpecs={agentSpecs}
            />
          </div>

          {/* Step list docked at bottom */}
          <ExecutionStepList
            steps={selectedRun?.steps}
            selectedStepId={selectedStepId}
            onStepClick={onStepClick}
            workflow={workflow}
          />
        </div>
      ) : (
        <div className="flex-1 overflow-hidden">
          <DiffView runs={runs} workflow={workflow} />
        </div>
      )}
    </div>
  );
}
