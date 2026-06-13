const TEAM_STYLES: Record<string, { pill: string; dot: string }> = {
  IT: { pill: "bg-blue-50 text-blue-700 ring-1 ring-blue-200", dot: "bg-blue-500" },
  Support: { pill: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200", dot: "bg-emerald-500" },
  Helpdesk: { pill: "bg-amber-50 text-amber-700 ring-1 ring-amber-200", dot: "bg-amber-500" },
  HR: { pill: "bg-violet-50 text-violet-700 ring-1 ring-violet-200", dot: "bg-violet-500" },
};

export default function TeamBadge({ team }: { team: string }) {
  const style = TEAM_STYLES[team] ?? {
    pill: "bg-slate-100 text-slate-600 ring-1 ring-slate-200",
    dot: "bg-slate-400",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${style.pill}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${style.dot}`} />
      {team}
    </span>
  );
}
