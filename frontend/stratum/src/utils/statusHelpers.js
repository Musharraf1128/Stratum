// ─── Status → Tailwind class maps ─────────────────────────────────────────────

export const statusColor = (s) =>
({
  completed: "text-emerald-400",
  completed_with_fallback: "text-amber-400",
  running: "text-orange-400",
  pending: "text-zinc-500",
  failed: "text-red-400",
  failed_retries_exceeded: "text-red-400",
  skipped: "text-zinc-600",
  skipped_budget_exceeded: "text-orange-400",
  skipped_call_limit: "text-orange-400",
  rate_limited: "text-yellow-400",
  permission_denied: "text-red-400",
}[s] ?? "text-zinc-500");

export const statusDot = (s) =>
({
  completed: "bg-emerald-400",
  completed_with_fallback: "bg-amber-400",
  running: "bg-orange-400 animate-pulse",
  pending: "bg-zinc-600",
  failed: "bg-red-500",
  failed_retries_exceeded: "bg-red-500",
  skipped: "bg-zinc-700",
  skipped_budget_exceeded: "bg-orange-400",
  skipped_call_limit: "bg-orange-400",
  rate_limited: "bg-yellow-400",
  permission_denied: "bg-red-500",
}[s] ?? "bg-zinc-600");

export const statusBadge = (s) =>
({
  completed: "border-emerald-800 text-emerald-400 bg-emerald-950/40",
  completed_with_fallback: "border-amber-700  text-amber-400  bg-amber-950/40",
  running: "border-orange-700  text-orange-400  bg-orange-950/40",
  pending: "border-zinc-700    text-zinc-500    bg-zinc-900/40",
  failed: "border-red-800     text-red-400     bg-red-950/40",
  failed_retries_exceeded: "border-red-800     text-red-400     bg-red-950/40",
  skipped: "border-zinc-800    text-zinc-600    bg-zinc-900/20",
  skipped_budget_exceeded: "border-orange-800  text-orange-400  bg-orange-950/30",
  skipped_call_limit: "border-orange-800  text-orange-400  bg-orange-950/30",
  rate_limited: "border-yellow-800  text-yellow-400  bg-yellow-950/30",
  permission_denied: "border-red-800     text-red-400     bg-red-950/30",
}[s] ?? "border-zinc-700 text-zinc-500");

// Human-readable status labels
export const statusLabel = (s) =>
({
  completed: "Completed",
  completed_with_fallback: "Fallback",
  running: "Running",
  pending: "Pending",
  failed: "Failed",
  failed_retries_exceeded: "Retries Exceeded",
  skipped: "Skipped",
  skipped_budget_exceeded: "Budget Exceeded",
  skipped_call_limit: "Call Limit",
  rate_limited: "Rate Limited",
  permission_denied: "Permission Denied",
}[s] ?? s);
