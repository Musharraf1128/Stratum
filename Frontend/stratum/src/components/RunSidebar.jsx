// components/RunSidebar.jsx
// Responsibility: Resizable left sidebar — collapsed by default (icon strip),
// expands on click. When expanded, a drag handle on the right edge allows resizing.

import { useState, useCallback, useRef, useEffect } from "react";
import { statusDot, statusBadge, statusColor } from "../utils/statusHelpers";

// ─── Single run row (shown when sidebar is expanded) ─────────────────────────
function RunRow({ run, isSelected, onSelect, onReplay }) {
  return (
    <div
      onClick={() => onSelect(run)}
      className={`group flex items-start gap-3 px-4 py-3 cursor-pointer transition-all duration-150 border-l-2 ${
        isSelected
          ? "border-orange-500 bg-orange-950/20"
          : "border-transparent hover:border-zinc-700 hover:bg-zinc-900/40"
      }`}
    >
      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${statusDot(run.status)}`} />

      <div className="flex-1 min-w-0 overflow-hidden">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-mono text-zinc-500 truncate max-w-[120px]">{run.id}</span>
          <span className={`text-xs font-mono border px-1.5 rounded flex-shrink-0 ${statusBadge(run.status)}`}>
            {run.status}
          </span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-zinc-300 font-mono flex-shrink-0">{run.duration}</span>
          <span className="text-xs text-zinc-600 flex-shrink-0">{run.cost}</span>
        </div>
        <div className="text-xs text-zinc-500 mt-0.5 truncate">{run.start}</div>
      </div>

      <button
        onClick={(e) => { e.stopPropagation(); onReplay(run); }}
        title="Replay run"
        className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 text-xs font-mono border border-zinc-700 text-zinc-400 hover:border-orange-600 hover:text-orange-400 rounded"
      >
        ↺
      </button>
    </div>
  );
}

// ─── Collapsed: vertical icon strip ──────────────────────────────────────────
function CollapsedStrip({ runs, selectedRun, onExpand }) {
  return (
    <div
      className="flex flex-col items-center gap-1 py-3 cursor-pointer"
      onClick={onExpand}
      title="Click to expand runs"
    >
      {/* Rail label */}
      <span
        className="text-zinc-700 font-mono uppercase tracking-widest mb-2"
        style={{ fontSize: 9, writingMode: "vertical-rl", letterSpacing: "0.2em" }}
      >
        RUNS
      </span>

      {/* One dot per run */}
      {runs.map((run) => (
        <div
          key={run.id}
          title={`${run.id} · ${run.status}`}
          className={`w-2 h-2 rounded-full transition-transform hover:scale-125 ${
            selectedRun?.id === run.id
              ? "ring-1 ring-orange-500 " + statusDot(run.status)
              : statusDot(run.status)
          }`}
        />
      ))}

      {/* Expand hint */}
      <div className="mt-auto pt-4">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-zinc-700">
          <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
    </div>
  );
}

// ─── Resize handle ───────────────────────────────────────────────────────────
function ResizeHandle({ onMouseDown, side = "right" }) {
  return (
    <div
      onMouseDown={onMouseDown}
      className={`absolute top-0 ${side === "right" ? "right-0" : "left-0"} w-1 h-full cursor-col-resize z-10 group`}
    >
      <div className={`w-[3px] h-full bg-transparent group-hover:bg-orange-600/40 active:bg-orange-500/60 transition-colors`} />
    </div>
  );
}

// ─── Main RunSidebar ──────────────────────────────────────────────────────────
export default function RunSidebar({ runs, selectedRun, onSelect, onReplay }) {
  const [expanded, setExpanded] = useState(false);
  const [width, setWidth] = useState(280);
  const isResizing = useRef(false);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    isResizing.current = true;
    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (e) => {
      if (!isResizing.current) return;
      const delta = e.clientX - startX;
      const newWidth = Math.max(200, Math.min(500, startWidth + delta));
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
      className="flex-shrink-0 border-r border-zinc-900 flex flex-col overflow-hidden transition-all duration-200 ease-in-out relative"
      style={{ width: expanded ? width : 36, background: "#0a0a0a" }}
    >
      {expanded ? (
        /* ── Expanded panel ── */
        <>
          <div className="px-4 py-3 border-b border-zinc-900 flex items-center justify-between flex-shrink-0">
            <span className="text-xs font-mono text-zinc-600 uppercase tracking-widest">Runs</span>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-zinc-700">{runs.length}</span>
              <button
                onClick={() => setExpanded(false)}
                className="text-zinc-700 hover:text-zinc-400 transition-colors ml-1"
                title="Collapse"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M8 2L4 6l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-hidden">
            {runs.map((run) => (
              <RunRow
                key={run.id}
                run={run}
                isSelected={selectedRun?.id === run.id}
                onSelect={onSelect}
                onReplay={onReplay}
              />
            ))}
          </div>

          {/* Drag handle on right edge */}
          <ResizeHandle onMouseDown={handleMouseDown} side="right" />
        </>
      ) : (
        /* ── Collapsed rail ── */
        <CollapsedStrip
          runs={runs}
          selectedRun={selectedRun}
          onExpand={() => setExpanded(true)}
        />
      )}
    </div>
  );
}
