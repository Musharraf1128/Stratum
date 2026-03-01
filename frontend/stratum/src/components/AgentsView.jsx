// components/AgentsView.jsx
// Responsibility: New Agents tab — table of all registered agents with
// their governance spec (permissions, limits, fallback).

import { useState, useEffect } from "react";
import { fetchAgents } from "../api/stratum";

export default function AgentsView() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchAgents()
      .then((data) => {
        setAgents(data.agents || []);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <span className="text-xs font-mono text-zinc-600">Loading agents…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <span className="text-xs font-mono text-red-400">{error}</span>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-white">Registered Agents</h2>
        <p className="text-xs text-zinc-600 font-mono mt-1">{agents.length} agents with governance specs</p>
      </div>

      <div className="border border-zinc-800 rounded-lg overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/40">
              <th className="px-4 py-3 text-xs font-mono text-zinc-500 uppercase tracking-wider">Agent</th>
              <th className="px-4 py-3 text-xs font-mono text-zinc-500 uppercase tracking-wider">Role</th>
              <th className="px-4 py-3 text-xs font-mono text-zinc-500 uppercase tracking-wider">Permissions</th>
              <th className="px-4 py-3 text-xs font-mono text-zinc-500 uppercase tracking-wider">Token Limit</th>
              <th className="px-4 py-3 text-xs font-mono text-zinc-500 uppercase tracking-wider">Call Limit</th>
              <th className="px-4 py-3 text-xs font-mono text-zinc-500 uppercase tracking-wider">Fallback</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => (
              <tr key={agent.agent_id || agent.name} className="border-b border-zinc-800/50 hover:bg-zinc-900/30 transition-colors">
                <td className="px-4 py-3">
                  <div className="text-sm text-white font-medium">{agent.name}</div>
                  {agent.description && (
                    <div className="text-xs text-zinc-600 mt-0.5 truncate max-w-[200px]">{agent.description}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-xs font-mono text-zinc-400">{agent.role || "—"}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {(agent.permissions || []).length > 0 ? (
                      agent.permissions.map((p) => (
                        <span key={p} className="text-xs font-mono border border-zinc-700 text-zinc-400 px-1.5 py-0.5 rounded">
                          {p}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-zinc-700">—</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-xs font-mono text-zinc-400">
                  {agent.limits?.max_input_tokens != null ? (
                    <span>{agent.limits.max_input_tokens.toLocaleString()} in / {agent.limits.max_output_tokens?.toLocaleString() || "—"} out</span>
                  ) : "—"}
                </td>
                <td className="px-4 py-3 text-xs font-mono text-zinc-400">
                  {agent.limits?.max_calls_per_run != null ? `${agent.limits.max_calls_per_run}/run` : "—"}
                </td>
                <td className="px-4 py-3 text-xs font-mono text-zinc-500">
                  {agent.fallback_agent_id || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
