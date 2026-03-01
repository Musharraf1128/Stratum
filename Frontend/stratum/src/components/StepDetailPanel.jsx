// components/StepDetailPanel.jsx
// Responsibility: Resizable right-side detail drawer. Collapsed by default
// to a narrow rail; expands on click. Drag handle on left edge for resizing.
// Shows input, output, tokens, cost, duration, status and error for a step.

import { useState, useCallback, useRef, useEffect } from "react";
import { statusColor, statusDot } from "../utils/statusHelpers";

function MetaCard({ label, children }) {
  return (
    <div className="border border-zinc-800 px-3 py-2 rounded overflow-hidden">
      <div className="text-xs text-zinc-600 font-mono uppercase tracking-wider mb-1">{label}</div>
      <div className="text-sm truncate">{children}</div>
    </div>
  );
}

function CodeBlock({ label, content, isError = false }) {
  return (
    <div className="min-w-0">
      <div
        className={`text-xs font-mono uppercase tracking-wider mb-2 ${
          isError ? "text-red-700" : "text-zinc-600"
        }`}
      >
        {label}
      </div>
      <div
        className={`rounded p-3 text-sm font-mono leading-relaxed overflow-x-auto break-words ${
          isError
            ? "border border-red-900 bg-red-950/30 text-red-400"
            : "border border-zinc-800 bg-zinc-950 text-zinc-300"
        }`}
        style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
      >
        {content || "—"}
      </div>
    </div>
  );
}

// ─── Resize handle ───────────────────────────────────────────────────────────
function ResizeHandle({ onMouseDown }) {
  return (
    <div
      onMouseDown={onMouseDown}
      className="absolute top-0 left-0 w-1 h-full cursor-col-resize z-10 group"
    >
      <div className="w-[3px] h-full bg-transparent group-hover:bg-orange-600/40 active:bg-orange-500/60 transition-colors" />
    </div>
  );
}

// ─── Collapsed: vertical icon strip (right side) ─────────────────────────────
function CollapsedStrip({ step, onExpand }) {
  return (
    <div
      className="flex flex-col items-center gap-2 py-3 cursor-pointer"
      onClick={onExpand}
      title="Click to expand details"
    >
      {/* Rail label */}
      <span
        className="text-zinc-700 font-mono uppercase tracking-widest mb-2"
        style={{ fontSize: 9, writingMode: "vertical-rl", letterSpacing: "0.2em" }}
      >
        DETAIL
      </span>

      {/* Status dot when a step is selected */}
      {step && (
        <div
          title={`${step.agentName} · ${step.status}`}
          className={`w-2 h-2 rounded-full ${statusDot(step.status)}`}
        />
      )}

      {/* Expand hint (chevron pointing left = toward center) */}
      <div className="mt-auto pt-4">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-zinc-700">
          <path d="M8 2L4 6l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
    </div>
  );
}

// ─── Expanded: full detail content ────────────────────────────────────────────
function ExpandedContent({ step, onCollapse }) {
  /* Empty state */
  if (!step) {
    return (
      <>
        <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between flex-shrink-0">
          <span className="text-xs font-mono text-zinc-600 uppercase tracking-widest">Detail</span>
          <button
            onClick={onCollapse}
            className="text-zinc-700 hover:text-zinc-400 transition-colors ml-1"
            title="Collapse"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        <div className="h-full flex flex-col items-center justify-center gap-3 p-8 text-center">
          <div className="w-12 h-12 border border-zinc-800 rounded-lg flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="8" stroke="#3f3f3f" strokeWidth="1.5" />
              <path d="M10 6v4l3 3" stroke="#3f3f3f" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <div className="text-xs text-zinc-700 font-mono uppercase tracking-wider">Select a node</div>
          <div className="text-xs text-zinc-700 leading-relaxed">
            Click any agent in the graph or step in the list to inspect its execution details,
            inputs, outputs, and token usage.
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 flex-shrink-0">
        <div className="min-w-0">
          <span className="text-xs font-mono text-zinc-500 uppercase tracking-widest">
            Agent Detail
          </span>
          <div className="text-sm text-white mt-0.5 truncate">{step.agentName}</div>
        </div>
        <button
          onClick={onCollapse}
          className="text-zinc-700 hover:text-zinc-400 transition-colors ml-2 flex-shrink-0"
          title="Collapse"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-hidden p-4 space-y-4">
        {/* Meta row */}
        <div className="grid grid-cols-2 gap-2">
          <MetaCard label="Status">
            <span className={`font-mono ${statusColor(step.status)}`}>{step.status}</span>
          </MetaCard>
          <MetaCard label="Duration">
            <span className="font-mono text-zinc-300">{step.duration}</span>
          </MetaCard>
          <MetaCard label="Tokens">
            <span className="font-mono text-zinc-300">{step.tokens.toLocaleString()}</span>
          </MetaCard>
          <MetaCard label="Cost">
            <span className="font-mono text-emerald-400">
              {step.cost > 0 ? `$${step.cost.toFixed(6)}` : "—"}
            </span>
          </MetaCard>
        </div>

        <CodeBlock label="Input"  content={step.input}  />
        <CodeBlock label="Output" content={step.output} />
        {step.error && <CodeBlock label="Error" content={step.error} isError />}
      </div>
    </>
  );
}

// ─── Main StepDetailPanel ─────────────────────────────────────────────────────
export default function StepDetailPanel({ step, onClose }) {
  const [expanded, setExpanded] = useState(false);
  const [width, setWidth] = useState(400);
  const isResizing = useRef(false);

  // Auto-expand when a step is selected, auto-collapse when cleared
  useEffect(() => {
    if (step) {
      setExpanded(true);
    } else {
      setExpanded(false);
    }
  }, [step]);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    isResizing.current = true;
    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (e) => {
      if (!isResizing.current) return;
      // Dragging left = increasing width (since panel is on the right)
      const delta = startX - e.clientX;
      const newWidth = Math.max(280, Math.min(600, startWidth + delta));
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  }, [width]);

  return (
    <div
      className="flex-shrink-0 border-l border-zinc-900 flex flex-col overflow-hidden transition-all duration-200 ease-in-out h-full relative"
      style={{ width: expanded ? width : 36, background: "#0d0d0d" }}
    >
      {expanded ? (
        <>
          <ExpandedContent step={step} onCollapse={() => setExpanded(false)} />
          {/* Drag handle on left edge */}
          <ResizeHandle onMouseDown={handleMouseDown} />
        </>
      ) : (
        <CollapsedStrip step={step} onExpand={() => setExpanded(true)} />
      )}
    </div>
  );
}
