// ─── Status → Tailwind class maps ─────────────────────────────────────────────

export const statusColor = (s) =>
  ({
    completed: "text-emerald-400",
    running:   "text-orange-400",
    pending:   "text-zinc-500",
    failed:    "text-red-400",
    skipped:   "text-zinc-600",
  }[s] ?? "text-zinc-500");

export const statusDot = (s) =>
  ({
    completed: "bg-emerald-400",
    running:   "bg-orange-400 animate-pulse",
    pending:   "bg-zinc-600",
    failed:    "bg-red-500",
    skipped:   "bg-zinc-700",
  }[s] ?? "bg-zinc-600");

export const statusBadge = (s) =>
  ({
    completed: "border-emerald-800 text-emerald-400 bg-emerald-950/40",
    running:   "border-orange-700  text-orange-400  bg-orange-950/40",
    pending:   "border-zinc-700    text-zinc-500    bg-zinc-900/40",
    failed:    "border-red-800     text-red-400     bg-red-950/40",
    skipped:   "border-zinc-800    text-zinc-600    bg-zinc-900/20",
  }[s] ?? "border-zinc-700 text-zinc-500");
