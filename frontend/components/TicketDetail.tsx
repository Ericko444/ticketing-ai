"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTicket, type Ticket } from "@/lib/api";
import TeamBadge from "./TeamBadge";

const STATUS_PILL: Record<string, string> = {
  routed: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  pending_supervisor: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  pending: "bg-blue-50 text-blue-700 ring-1 ring-blue-200",
};

export default function TicketDetail({ id }: { id: string }) {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    getTicket(id)
      .then(setTicket)
      .catch(() => setNotFound(true));
  }, [id]);

  if (notFound) {
    return (
      <main className="max-w-4xl mx-auto px-6 py-8">
        <Link href="/" className="text-sm text-indigo-600 hover:text-indigo-800 mb-6 block">
          ← Back to dashboard
        </Link>
        <p className="text-slate-500">Ticket not found.</p>
      </main>
    );
  }

  if (!ticket) {
    return (
      <main className="max-w-4xl mx-auto px-6 py-8 animate-pulse space-y-4">
        <div className="h-4 w-32 bg-slate-200 rounded" />
        <div className="h-8 w-2/3 bg-slate-200 rounded" />
        <div className="h-48 bg-slate-200 rounded-xl" />
      </main>
    );
  }

  const displayTeam = ticket.final_team || ticket.assigned_team;
  const confidence = Math.round(ticket.routing_confidence * 100);
  const barColor =
    confidence >= 80 ? "bg-emerald-400" : confidence >= 60 ? "bg-amber-400" : "bg-red-400";
  const statusPill =
    STATUS_PILL[ticket.status] ?? "bg-slate-100 text-slate-600 ring-1 ring-slate-200";
  const statusLabel = ticket.status.replace(/_/g, " ");

  return (
    <main className="max-w-4xl mx-auto px-6 py-8">
      <Link href="/" className="text-sm text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1 mb-6">
        ← Back to dashboard
      </Link>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold text-slate-900">{ticket.subject}</h1>
              <p className="text-sm text-slate-500 mt-1">{ticket.sender}</p>
            </div>
            <span
              className={`shrink-0 text-xs font-medium px-2.5 py-1 rounded-full capitalize ${statusPill}`}
            >
              {statusLabel}
            </span>
          </div>
        </div>

        {/* Metadata grid */}
        <div className="px-6 py-5 grid grid-cols-2 gap-x-8 gap-y-5 border-b border-slate-100">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1.5">Assigned team</p>
            <TeamBadge team={displayTeam} />
          </div>

          {ticket.final_team && ticket.final_team !== ticket.assigned_team && (
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1.5">Originally proposed</p>
              <TeamBadge team={ticket.assigned_team} />
            </div>
          )}

          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1.5">Routing confidence</p>
            <div className="flex items-center gap-3 mt-1">
              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${barColor} transition-all`}
                  style={{ width: `${confidence}%` }}
                />
              </div>
              <span className="text-sm font-semibold tabular-nums text-slate-700">{confidence}%</span>
            </div>
          </div>

          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1.5">Evaluator verdict</p>
            <p className="text-sm font-medium text-slate-700 capitalize">{ticket.evaluator_verdict}</p>
          </div>

          {ticket.supervisor_action && (
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1.5">Supervisor action</p>
              <p className="text-sm font-medium text-slate-700 capitalize">{ticket.supervisor_action}</p>
            </div>
          )}

          {ticket.created_at && (
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1.5">Received</p>
              <p className="text-sm text-slate-700">{new Date(ticket.created_at).toLocaleString()}</p>
            </div>
          )}
        </div>

        {/* Email body */}
        <div className="px-6 py-5">
          <p className="text-xs text-slate-400 uppercase tracking-wider mb-3">Email body</p>
          <div className="bg-slate-50 rounded-lg border border-slate-100 p-4">
            <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{ticket.body}</p>
          </div>
        </div>
      </div>
    </main>
  );
}
