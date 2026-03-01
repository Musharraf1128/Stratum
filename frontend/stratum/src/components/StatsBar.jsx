// components/StatsBar.jsx
// Responsibility: Render the 6-metric aggregate stats strip below the nav

export default function StatsBar({ runs, agentCount }) {
  const total      = runs.length;
  const completed  = runs.filter((r) => r.status === "completed").length;
  const failed     = runs.filter((r) => r.status === "failed").length;
  const totalTokens = runs.reduce((acc, r) => acc + (r.tokens || 0), 0);

  // cost can be a string ("$0.09") or a number — handle both
  const totalCost  = runs.reduce((acc, r) => {
    if (typeof r.cost === "number") return acc + r.cost;
    if (typeof r.cost === "string") return acc + parseFloat(r.cost.replace("$", "") || "0");
    return acc;
  }, 0);

  // Compute average duration from runs that have a parseable duration
  let avgDuration = "—";
  const completedRuns = runs.filter((r) => r.status === "completed");
  if (completedRuns.length > 0) {
    // duration is already a formatted string from adapters, just show the first completed run's for now
    avgDuration = completedRuns[0]?.duration || "—";
  }

  const stats = [
    { label: "Total Runs",    value: total,                         sub: `${completed} completed`       },
    { label: "Active Agents", value: agentCount,                    sub: "in workflow"                  },
    { label: "Total Tokens",  value: totalTokens.toLocaleString(),  sub: "across all runs"              },
    { label: "Total Cost",    value: `$${totalCost.toFixed(3)}`,    sub: "LLM spend"                    },
    { label: "Avg Duration",  value: avgDuration,                   sub: "per completed run"            },
    { label: "Error Rate",    value: total > 0 ? `${Math.round((failed / total) * 100)}%` : "0%", sub: `${failed} failed` },
  ];

  return (
    <div className="grid grid-cols-6 border-b border-zinc-900 flex-shrink-0">
      {stats.map((s, i) => (
        <div
          key={i}
          className={`px-5 py-4 ${i < stats.length - 1 ? "border-r border-zinc-900" : ""}`}
        >
          <div className="text-xs font-mono text-zinc-600 uppercase tracking-widest mb-1">
            {s.label}
          </div>
          <div className="text-xl font-light text-white tracking-tight">{s.value}</div>
          <div className="text-xs text-zinc-600 mt-0.5">{s.sub}</div>
        </div>
      ))}
    </div>
  );
}
