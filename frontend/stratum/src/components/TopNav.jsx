// components/TopNav.jsx
// Responsibility: Top navigation bar — logo, workflow selector, tab navigation, API key, actions

export default function TopNav({ workflowName, onNewRun, onOpenSettings, hasApiKey, activeView, onViewChange }) {
  return (
    <nav
      className="flex items-center justify-between px-6 border-b border-zinc-900 flex-shrink-0"
      style={{ height: 52 }}
    >
      {/* Left: Logo + Workflow + Tabs */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <rect x="1"  y="1"  width="9" height="9" rx="1.5" fill="#f97316" opacity="0.9" />
            <rect x="12" y="1"  width="9" height="9" rx="1.5" fill="none" stroke="#f97316" strokeWidth="1.5" opacity="0.6" />
            <rect x="1"  y="12" width="9" height="9" rx="1.5" fill="none" stroke="#f97316" strokeWidth="1.5" opacity="0.6" />
            <rect x="12" y="12" width="9" height="9" rx="1.5" fill="#f97316" opacity="0.4" />
          </svg>
          <span className="text-sm font-semibold tracking-tight text-white">Stratum</span>
          <span className="text-xs font-mono border border-zinc-800 text-zinc-600 px-1.5 py-0.5 rounded">
            v0
          </span>
        </div>

        <div className="flex items-center gap-2 pl-4 border-l border-zinc-800">
          <span className="text-xs text-zinc-600 font-mono">workflow</span>
          <span className="text-xs font-mono text-zinc-300 border border-zinc-800 px-2 py-1 rounded">
            {workflowName}
          </span>
        </div>

        {/* View tabs */}
        <div className="flex items-center gap-1 pl-4 border-l border-zinc-800">
          {[
            { key: "workflow", label: "Workflow" },
            { key: "agents", label: "Agents" },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => onViewChange?.(key)}
              className={`px-3 py-1.5 text-xs font-mono rounded transition-colors ${
                activeView === key
                  ? "bg-orange-950/40 text-orange-400 border border-orange-800"
                  : "text-zinc-500 hover:text-zinc-300 border border-transparent"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Right: Live indicator + API Key + New Run */}
      <div className="flex items-center gap-3">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-xs text-zinc-500 font-mono">live</span>

        {/* API Key button */}
        <div className="border-l border-zinc-800 pl-3">
          <button
            onClick={onOpenSettings}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono border rounded transition-all duration-200 ${
              hasApiKey
                ? "border-emerald-800 text-emerald-400 hover:bg-emerald-950/30"
                : "border-zinc-700 text-zinc-500 hover:border-zinc-500 hover:text-zinc-300"
            }`}
            title="Configure API key"
          >
            {hasApiKey ? (
              <>
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>API Key</span>
              </>
            ) : (
              <>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="opacity-80">
                  <path d="M6 2v8M2 6h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                <span>Add your API Key</span>
              </>
            )}
          </button>
        </div>

        <div className="border-l border-zinc-800 pl-3">
          <button
            onClick={onNewRun}
            className="px-3 py-1.5 text-xs font-mono border border-orange-800 text-orange-400 hover:bg-orange-950/40 rounded transition-colors"
          >
            + New Run
          </button>
        </div>
      </div>
    </nav>
  );
}
