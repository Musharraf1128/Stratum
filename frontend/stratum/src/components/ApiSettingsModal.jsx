// components/ApiSettingsModal.jsx
// Responsibility: Modal for selecting LLM provider and managing API keys.

import { useState, useEffect } from "react";

// ─── Provider definitions with inline SVG icons ────────────────────────────────
const PROVIDERS = [
  {
    id: "openai",
    name: "OpenAI",
    placeholder: "sk-...",
    icon: (active) => (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <path
          d="M28.07 13.32a7.2 7.2 0 0 0-.62-5.92A7.29 7.29 0 0 0 19.6 3.8a7.23 7.23 0 0 0-5.49-2.47 7.3 7.3 0 0 0-6.96 5.07 7.22 7.22 0 0 0-4.82 3.5 7.3 7.3 0 0 0 .89 8.58 7.2 7.2 0 0 0 .62 5.92 7.29 7.29 0 0 0 7.85 3.6 7.23 7.23 0 0 0 5.49 2.47 7.3 7.3 0 0 0 6.96-5.07 7.22 7.22 0 0 0 4.82-3.5 7.3 7.3 0 0 0-.89-8.58Zm-10.9 16.08a5.46 5.46 0 0 1-3.51-1.27l.17-.1 5.83-3.37a.95.95 0 0 0 .48-.83v-8.22l2.46 1.42a.09.09 0 0 1 .05.07v6.81a5.48 5.48 0 0 1-5.48 5.49ZM5.39 24.3a5.44 5.44 0 0 1-.65-3.67l.17.1 5.83 3.37a.96.96 0 0 0 .95 0l7.12-4.11v2.84a.09.09 0 0 1-.04.08l-5.9 3.4A5.48 5.48 0 0 1 5.4 24.3Zm-1.82-12.7A5.45 5.45 0 0 1 6.43 8.7v6.93a.95.95 0 0 0 .48.83l7.12 4.1-2.47 1.43a.09.09 0 0 1-.08 0l-5.9-3.4a5.48 5.48 0 0 1-2.01-7.49Zm20.78 4.85-7.12-4.11 2.46-1.42a.09.09 0 0 1 .09 0l5.9 3.4a5.48 5.48 0 0 1-.84 9.88V17.5a.95.95 0 0 0-.49-.84Zm2.45-3.7-.17-.1-5.83-3.36a.96.96 0 0 0-.96 0l-7.12 4.1V10.6a.09.09 0 0 1 .04-.08l5.9-3.4a5.48 5.48 0 0 1 8.14 5.67ZM10.2 17.37l-2.47-1.42a.09.09 0 0 1-.05-.07v-6.81a5.48 5.48 0 0 1 8.99-4.22l-.17.1-5.83 3.37a.95.95 0 0 0-.48.83l.01 8.22Zm1.34-2.89 3.17-1.83 3.17 1.83v3.66l-3.17 1.83-3.17-1.83v-3.66Z"
          fill={active ? "#10b981" : "#6b7280"}
        />
      </svg>
    ),
  },
  {
    id: "claude",
    name: "Claude",
    placeholder: "sk-ant-...",
    icon: (active) => (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <path
          d="M22.67 12.42 17.6 25.08h-3.47l1.91-4.82-4.45-10.14h3.6l2.49 6.78 2.49-6.78h2.5Z"
          fill={active ? "#f59e0b" : "#6b7280"}
        />
        <path
          d="M13.78 12.42H11.1l-5.1 12.66h2.67l1.13-2.96h4.64l1.12 2.96h2.68l-5.1-12.66h-1.35Zm-3.31 7.4 1.63-4.27 1.62 4.27h-3.25Z"
          fill={active ? "#f59e0b" : "#6b7280"}
        />
        <rect x="1" y="1" width="30" height="30" rx="6" stroke={active ? "#f59e0b" : "#3f3f46"} strokeWidth="1.5" fill="none" />
      </svg>
    ),
  },
  {
    id: "gemini",
    name: "Gemini",
    placeholder: "AIza...",
    icon: (active) => (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <path
          d="M16 2C16 2 24 8 24 16s-8 14-8 14"
          stroke={active ? "#4285F4" : "#6b7280"}
          strokeWidth="2.5"
          strokeLinecap="round"
          fill="none"
        />
        <path
          d="M16 2C16 2 8 8 8 16s8 14 8 14"
          stroke={active ? "#EA4335" : "#6b7280"}
          strokeWidth="2.5"
          strokeLinecap="round"
          fill="none"
        />
        <circle cx="16" cy="16" r="3" fill={active ? "#4285F4" : "#6b7280"} />
      </svg>
    ),
  },
];


export default function ApiSettingsModal({ isOpen, onClose, apiKey, provider, serverAuthKey, onSave }) {
  const [selectedProvider, setSelectedProvider] = useState(provider || "openai");
  const [key, setKey] = useState(apiKey || "");
  const [authKey, setAuthKey] = useState(serverAuthKey || "");
  const [showKey, setShowKey] = useState(false);
  const [showAuthKey, setShowAuthKey] = useState(false);

  // Sync when modal opens with new props
  useEffect(() => {
    if (isOpen) {
      setSelectedProvider(provider || "openai");
      setKey(apiKey || "");
      setAuthKey(serverAuthKey || "");
    }
  }, [isOpen, provider, apiKey, serverAuthKey]);

  if (!isOpen) return null;

  const activeProvider = PROVIDERS.find((p) => p.id === selectedProvider) || PROVIDERS[0];

  const handleSave = () => {
    onSave(key.trim() || null, selectedProvider, authKey.trim() || null);
    onClose();
  };

  const handleClear = () => {
    setKey("");
    setAuthKey("");
    onSave(null, selectedProvider, null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg mx-4 bg-zinc-950 border border-zinc-800 rounded-lg shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="1" y="6" width="14" height="8" rx="2" stroke="#f97316" strokeWidth="1.2" fill="none" />
              <path d="M4 6V4a4 4 0 0 1 8 0v2" stroke="#f97316" strokeWidth="1.2" strokeLinecap="round" fill="none" />
              <circle cx="8" cy="10.5" r="1.5" fill="#f97316" />
            </svg>
            <span className="text-sm font-semibold text-white">API Configuration</span>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-600 hover:text-zinc-400 transition-colors text-lg leading-none"
          >
            ×
          </button>
        </div>

        {/* Provider selector */}
        <div className="px-5 pt-4 pb-2">
          <label className="block text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">
            Select Provider
          </label>
          <div className="grid grid-cols-3 gap-3">
            {PROVIDERS.map((p) => {
              const isActive = selectedProvider === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setSelectedProvider(p.id)}
                  className={`flex flex-col items-center gap-2 py-4 px-3 rounded-lg border transition-all duration-200 ${
                    isActive
                      ? "border-orange-600 bg-orange-950/20 shadow-[0_0_12px_rgba(249,115,22,0.15)]"
                      : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-600 hover:bg-zinc-900/60"
                  }`}
                >
                  {p.icon(isActive)}
                  <span
                    className={`text-xs font-mono tracking-wide ${
                      isActive ? "text-white" : "text-zinc-500"
                    }`}
                  >
                    {p.name}
                  </span>
                  {isActive && (
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-0.5" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Key input */}
        <div className="px-5 py-4 space-y-3">
          <label className="block text-xs font-mono text-zinc-500 uppercase tracking-widest">
            {activeProvider.name} API Key
          </label>
          <div className="relative">
            <input
              type={showKey ? "text" : "password"}
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder={activeProvider.placeholder}
              className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2.5 text-sm font-mono text-zinc-300 placeholder-zinc-700 focus:outline-none focus:border-orange-600 transition-colors"
              spellCheck={false}
              autoComplete="off"
            />
            <button
              onClick={() => setShowKey(!showKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-mono text-zinc-600 hover:text-zinc-400 transition-colors px-1.5 py-0.5"
            >
              {showKey ? "hide" : "show"}
            </button>
          </div>

          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${key.trim() ? "bg-emerald-400" : "bg-zinc-700"}`} />
            <span className="text-xs font-mono text-zinc-600">
              {key.trim()
                ? `Key configured — runs will use ${activeProvider.name}`
                : "No key — runs will use mock responses"
              }
            </span>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 rounded p-3">
            <div className="text-xs text-zinc-500 leading-relaxed">
            Your key is stored in memory for this session only. It is not
              persisted to localStorage. On page reload you will re-enter it.
            </div>
          </div>
        </div>

        {/* Server Auth Key input */}
        <div className="px-5 pb-4 space-y-3">
          <label className="block text-xs font-mono text-zinc-500 uppercase tracking-widest">
            Server Auth Key
            <span className="text-zinc-700 normal-case ml-2">(STRATUM_API_KEY)</span>
          </label>
          <div className="relative">
            <input
              type={showAuthKey ? "text" : "password"}
              value={authKey}
              onChange={(e) => setAuthKey(e.target.value)}
              placeholder="my-stratum-secret"
              className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2.5 text-sm font-mono text-zinc-300 placeholder-zinc-700 focus:outline-none focus:border-orange-600 transition-colors"
              spellCheck={false}
              autoComplete="off"
            />
            <button
              onClick={() => setShowAuthKey(!showAuthKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-mono text-zinc-600 hover:text-zinc-400 transition-colors px-1.5 py-0.5"
            >
              {showAuthKey ? "hide" : "show"}
            </button>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${authKey.trim() ? "bg-emerald-400" : "bg-zinc-700"}`} />
            <span className="text-xs font-mono text-zinc-600">
              {authKey.trim()
                ? "Server auth configured — sent as Bearer token on run/replay"
                : "No auth key — only works if server has no STRATUM_API_KEY set"
              }
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-zinc-800">
          <button
            onClick={handleClear}
            className="px-3 py-1.5 text-xs font-mono text-zinc-600 hover:text-red-400 transition-colors"
          >
            Clear Key
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-xs font-mono border border-zinc-700 text-zinc-500 hover:text-zinc-300 rounded transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-1.5 text-xs font-mono border border-orange-800 text-orange-400 hover:bg-orange-950/40 rounded transition-colors"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
