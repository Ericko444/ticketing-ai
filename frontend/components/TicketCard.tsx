import type { Ticket } from "@/lib/api";
import TeamBadge from "./TeamBadge";

const TEAM_BORDER: Record<string, string> = {
  IT: "border-l-blue-500",
  Support: "border-l-emerald-500",
  Helpdesk: "border-l-amber-500",
  HR: "border-l-violet-500",
};

const STATUS_PILL: Record<string, string> = {
  routed: "bg-emerald-50 text-emerald-700",
  pending_supervisor: "bg-amber-50 text-amber-700",
  pending: "bg-blue-50 text-blue-700",
};

const STATUS_LABEL: Record<string, string> = {
  routed: "Routed",
  pending_supervisor: "Pending review",
  pending: "Processing",
};

export default function TicketCard({ ticket }: { ticket: Ticket }) {
  const displayTeam = ticket.final_team || ticket.assigned_team;
  const borderColor = TEAM_BORDER[displayTeam] ?? "border-l-slate-300";
  const statusPill = STATUS_PILL[ticket.status] ?? "bg-slate-100 text-slate-600";
  const statusLabel = STATUS_LABEL[ticket.status] ?? ticket.status.replace(/_/g, " ");
  const confidence = Math.round(ticket.routing_confidence * 100);
  const barColor =
    confidence >= 80 ? "bg-emerald-400" : confidence >= 60 ? "bg-amber-400" : "bg-red-400";

  return (
    <div
      className={`bg-white rounded-lg border border-slate-200 border-l-4 ${borderColor} p-4 hover:shadow-md hover:-translate-y-px transition-all cursor-pointer`}
    >
      <div className="flex items-start justify-between gap-4 mb-2">
        <p className="font-medium text-slate-900 text-sm leading-snug line-clamp-1">
          {ticket.subject}
        </p>
        <span
          className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full capitalize ${statusPill}`}
        >
          {statusLabel}
        </span>
      </div>

      <div className="flex items-center gap-3 mb-3">
        <TeamBadge team={displayTeam} />
        <span className="text-xs text-slate-400 truncate">{ticket.sender}</span>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${barColor}`}
            style={{ width: `${confidence}%` }}
          />
        </div>
        <span className="text-xs text-slate-400 tabular-nums shrink-0">{confidence}% confidence</span>
        {ticket.created_at && (
          <span className="text-xs text-slate-400 shrink-0 hidden sm:inline">
            {new Date(ticket.created_at).toLocaleString()}
          </span>
        )}
      </div>
    </div>
  );
}
