"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTickets, approveRouting, overrideRouting, type Ticket } from "@/lib/api";
import TeamBadge from "@/components/TeamBadge";
import SupervisorModal from "@/components/SupervisorModal";

export default function SupervisorPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [overrideTarget, setOverrideTarget] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    getTickets(0, 100)
      .then((all) => setTickets(all.filter((t) => t.status === "pending_supervisor")))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  function removeTicket(id: string) {
    setTickets((prev) => prev.filter((t) => t.id !== id));
  }

  async function handleApprove(ticketId: string) {
    removeTicket(ticketId);
    try {
      await approveRouting(ticketId);
    } catch {
      setErrors((e) => ({ ...e, [ticketId]: "Approve failed. Refresh to retry." }));
    }
  }

  async function handleOverride(team: string) {
    if (!overrideTarget) return;
    const id = overrideTarget;
    setOverrideTarget(null);
    removeTicket(id);
    try {
      await overrideRouting(id, team);
    } catch {
      setErrors((e) => ({ ...e, [id]: "Override failed. Refresh to retry." }));
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Supervisor Queue</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Tickets flagged for low-confidence routing
        </p>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="bg-white rounded-lg border border-slate-200 p-5 h-32 animate-pulse"
            />
          ))}
        </div>
      ) : tickets.length === 0 ? (
        <div className="text-center py-24">
          <p className="text-4xl mb-3">✓</p>
          <p className="font-medium text-slate-700">All clear</p>
          <p className="text-sm text-slate-400 mt-1">No tickets pending review</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tickets.map((ticket) => {
            const confidence = Math.round(ticket.routing_confidence * 100);
            const barColor =
              confidence >= 80
                ? "bg-emerald-400"
                : confidence >= 60
                ? "bg-amber-400"
                : "bg-red-400";

            return (
              <div
                key={ticket.id}
                data-testid="supervisor-card"
                data-ticket-id={ticket.id}
                className="bg-white border border-amber-200 rounded-xl p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <p className="font-semibold text-slate-900">{ticket.subject}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{ticket.sender}</p>
                  </div>
                  <span className="shrink-0 text-xs font-medium px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 ring-1 ring-amber-200">
                    Needs review
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-4 text-sm mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Proposed</span>
                    <TeamBadge team={ticket.assigned_team} />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Verdict</span>
                    <span className="text-xs font-medium text-slate-600 capitalize">
                      {ticket.evaluator_verdict}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 ml-auto">
                    <span className="text-xs text-slate-400">Confidence</span>
                    <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${barColor}`}
                        style={{ width: `${confidence}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-slate-600 tabular-nums">
                      {confidence}%
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
                  <button
                    onClick={() => handleApprove(ticket.id)}
                    className="px-4 py-1.5 text-sm rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 font-medium transition-colors"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => setOverrideTarget(ticket.id)}
                    className="px-4 py-1.5 text-sm rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium transition-colors"
                  >
                    Override team
                  </button>
                  <Link
                    href={`/tickets/${ticket.id}`}
                    className="ml-auto text-xs text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    View details →
                  </Link>
                </div>

                {errors[ticket.id] && (
                  <p className="text-xs text-red-500 mt-2">{errors[ticket.id]}</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {overrideTarget && (
        <SupervisorModal
          onConfirm={handleOverride}
          onCancel={() => setOverrideTarget(null)}
        />
      )}
    </main>
  );
}
