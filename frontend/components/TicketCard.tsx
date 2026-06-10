import type { Ticket } from "@/lib/api";
import TeamBadge from "./TeamBadge";

export default function TicketCard({ ticket }: { ticket: Ticket }) {
  const displayTeam = ticket.final_team || ticket.assigned_team;

  return (
    <div className="rounded border p-4 hover:bg-gray-50 transition-colors cursor-pointer">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <TeamBadge team={displayTeam} />
          {ticket.status === "pending_supervisor" && (
            <span className="text-xs text-orange-600 font-medium">
              ⚠ Pending review
            </span>
          )}
        </div>
        <span className="text-xs text-gray-400">
          {ticket.created_at
            ? new Date(ticket.created_at).toLocaleString()
            : ""}
        </span>
      </div>
      <p className="font-medium text-sm truncate">{ticket.subject}</p>
      <p className="text-xs text-gray-500 mt-0.5">{ticket.sender}</p>
    </div>
  );
}
