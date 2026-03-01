// components/WorkflowGraph.jsx
// Responsibility: SVG-based workflow graph — render nodes, directed edges,
// live status coloring, hover tooltips, and emit onNodeClick events.

import { useRef, useState } from "react";

const CANVAS_W = 980;
const CANVAS_H = 340;

function getStepStatus(agentId, activeRunSteps) {
  if (!activeRunSteps) return null;
  return activeRunSteps.find((s) => s.agentId === agentId)?.status ?? null;
}

function nodeBorderColor(liveStatus, isSelected) {
  if (isSelected) return "#f97316";
  return (
    {
      completed: "#166534",
      completed_with_fallback: "#92400e",
      running: "#c2410c",
      failed: "#7f1d1d",
      failed_retries_exceeded: "#7f1d1d",
      skipped_budget_exceeded: "#92400e",
      skipped_call_limit: "#92400e",
      rate_limited: "#854d0e",
      permission_denied: "#7f1d1d",
    }[liveStatus] ?? "#1f1f1f"
  );
}

function nodeStatusBarColor(liveStatus) {
  return (
    {
      completed: "#16a34a",
      completed_with_fallback: "#f59e0b",
      running: "#f97316",
      failed: "#ef4444",
      failed_retries_exceeded: "#ef4444",
      skipped_budget_exceeded: "#f97316",
      skipped_call_limit: "#f97316",
      rate_limited: "#eab308",
      permission_denied: "#ef4444",
    }[liveStatus] ?? "#2a2a2a"
  );
}

function dotFill(liveStatus) {
  return (
    {
      completed: "#16a34a",
      completed_with_fallback: "#f59e0b",
      running: "#f97316",
      failed: "#ef4444",
      failed_retries_exceeded: "#ef4444",
      skipped_budget_exceeded: "#f97316",
      skipped_call_limit: "#f97316",
      rate_limited: "#eab308",
      permission_denied: "#ef4444",
    }[liveStatus] ?? "#2a2a2a"
  );
}

// ─── Tooltip for agent nodes ──────────────────────────────────────────────────
function AgentTooltip({ agent, position }) {
  if (!agent || !position) return null;

  return (
    <div
      className="absolute z-50 pointer-events-none"
      style={{ left: position.x, top: position.y - 10, transform: "translate(-50%, -100%)" }}
    >
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 shadow-xl min-w-[180px]">
        <div className="text-xs font-semibold text-white mb-1">{agent.name}</div>
        <div className="text-xs font-mono text-zinc-500">Role: {agent.role}</div>
        {agent.description && (
          <div className="text-xs text-zinc-600 mt-0.5">{agent.description}</div>
        )}
        {agent.permissions && agent.permissions.length > 0 && (
          <div className="text-xs font-mono text-zinc-500 mt-1">
            Perms: {agent.permissions.join(", ")}
          </div>
        )}
        {agent.limits && (
          <div className="text-xs font-mono text-zinc-500 mt-0.5">
            {agent.limits.max_input_tokens && `${agent.limits.max_input_tokens} in`}
            {agent.limits.max_output_tokens && ` / ${agent.limits.max_output_tokens} out`}
            {agent.limits.max_calls_per_run && ` · ${agent.limits.max_calls_per_run}/run`}
          </div>
        )}
      </div>
    </div>
  );
}

export default function WorkflowGraph({ workflow, selectedNode, onNodeClick, activeRunSteps, agentSpecs }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [hoveredAgent, setHoveredAgent] = useState(null);
  const [tooltipPos, setTooltipPos] = useState(null);

  // Find spec for an agent by name
  const getSpec = (agentName) => {
    if (!agentSpecs) return null;
    return agentSpecs.find((s) => s.name === agentName) || null;
  };

  const handleMouseEnter = (agent, e) => {
    const containerRect = containerRef.current?.getBoundingClientRect();
    if (containerRect) {
      setTooltipPos({
        x: e.clientX - containerRect.left,
        y: e.clientY - containerRect.top,
      });
    }
    const spec = getSpec(agent.name);
    setHoveredAgent(spec ? { ...agent, ...spec } : agent);
  };

  const handleMouseLeave = () => {
    setHoveredAgent(null);
    setTooltipPos(null);
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden"
      style={{ background: "#0a0a0a", border: "1px solid #1a1a1a" }}
    >
      {/* Agent tooltip */}
      <AgentTooltip agent={hoveredAgent} position={tooltipPos} />

      {/* Dot-grid background */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(#1a1a1a 1px, transparent 1px), linear-gradient(90deg, #1a1a1a 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${CANVAS_W} ${CANVAS_H}`}
        preserveAspectRatio="xMidYMid meet"
        className="relative z-10"
      >
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#3f3f3f" />
          </marker>
          <marker id="arrow-orange" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#f97316" />
          </marker>
          <filter id="glow-orange" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* ── Edges ── */}
        {workflow.edges.map((edge, i) => {
          const from = workflow.agents.find((a) => a.id === edge.from);
          const to   = workflow.agents.find((a) => a.id === edge.to);
          if (!from || !to) return null;
          const fromStatus = getStepStatus(from.id, activeRunSteps);
          const isActive   = fromStatus === "running" || fromStatus === "completed" || fromStatus === "completed_with_fallback";
          return (
            <line
              key={i}
              x1={from.x + 140} y1={from.y + 28}
              x2={to.x}         y2={to.y   + 28}
              stroke={isActive ? "#f97316" : "#2a2a2a"}
              strokeWidth={isActive ? 1.5 : 1}
              strokeDasharray={isActive ? "none" : "4 3"}
              markerEnd={isActive ? "url(#arrow-orange)" : "url(#arrow)"}
            />
          );
        })}

        {/* ── Nodes ── */}
        {workflow.agents.map((agent) => {
          const liveStatus  = getStepStatus(agent.id, activeRunSteps) ?? agent.status;
          const isSelected  = selectedNode?.id === agent.id;
          const isRunning   = liveStatus === "running";

          return (
            <g
              key={agent.id}
              transform={`translate(${agent.x}, ${agent.y})`}
              className="cursor-pointer"
              onClick={() => onNodeClick(agent)}
              onMouseEnter={(e) => handleMouseEnter(agent, e)}
              onMouseLeave={handleMouseLeave}
              filter={isRunning ? "url(#glow-orange)" : "none"}
            >
              {/* Card body */}
              <rect
                width={160} height={56} rx={4}
                fill={isSelected ? "#1a0f00" : "#111111"}
                stroke={nodeBorderColor(liveStatus, isSelected)}
                strokeWidth={isSelected ? 1.5 : 1}
              />
              {/* Left status strip */}
              <rect width={3} height={56} rx={1} fill={nodeStatusBarColor(liveStatus)} />

              {/* Role label */}
              <text x={14} y={18} fontSize={9} fill="#555" fontFamily="'Courier New', monospace" letterSpacing={1}>
                {agent.role.toUpperCase()}
              </text>

              {/* Agent name */}
              <text
                x={14} y={37}
                fontSize={12}
                fill={isSelected ? "#f97316" : "#e5e5e5"}
                fontFamily="system-ui, sans-serif"
                fontWeight={500}
              >
                {agent.name.length > 17 ? agent.name.slice(0, 17) + "…" : agent.name}
              </text>

              {/* Status dot */}
              <circle cx={147} cy={12} r={4} fill={dotFill(liveStatus)} />
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-3 right-4 flex gap-4">
        {[
          ["completed", "#16a34a"],
          ["fallback",  "#f59e0b"],
          ["running",   "#f97316"],
          ["pending",   "#2a2a2a"],
          ["failed",    "#ef4444"],
        ].map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: color }} />
            <span className="text-zinc-600 text-xs font-mono">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
