"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { getTickets, type Ticket } from "@/lib/api";
import { useTicketStream } from "@/lib/useTicketStream";
import TicketCard from "@/components/TicketCard";

export default function DashboardPage() {
  const [initialTickets, setInitialTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const streamTickets = useTicketStream();

  useEffect(() => {
    getTickets()
      .then(setInitialTickets)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const tickets = useMemo(() => {
    if (streamTickets.length === 0) return initialTickets;
    const ids = new Set(initialTickets.map((t) => t.id));
    const fresh = streamTickets.filter((t) => !ids.has(t.id));
    return [...fresh, ...initialTickets];
  }, [initialTickets, streamTickets]);

  const pendingCount = tickets.filter((t) => t.status === "pending_supervisor").length;

  return (
    <main className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">All incoming support tickets</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium text-emerald-600">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          Live
        </div>
      </div>

      {pendingCount > 0 && (
        <Link href="/supervisor">
          <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex items-center justify-between hover:bg-amber-100 transition-colors cursor-pointer">
            <span className="text-sm font-medium text-amber-800">
              ⚠ {pendingCount} ticket{pendingCount > 1 ? "s" : ""} pending supervisor review
            </span>
            <span className="text-xs text-amber-600 font-medium">Review →</span>
          </div>
        </Link>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white rounded-lg border border-slate-200 p-4 h-24 animate-pulse"
            />
          ))}
        </div>
      ) : tickets.length === 0 ? (
        <div className="text-center py-24">
          <p className="text-4xl mb-3">📭</p>
          <p className="font-medium text-slate-700">No tickets yet</p>
          <p className="text-sm text-slate-400 mt-1">
            Tickets will appear here as emails arrive
          </p>
        </div>
      ) : (
        <ul className="space-y-3">
          {tickets.map((ticket) => (
            <li key={ticket.id} data-testid={ticket.id}>
              <Link href={`/tickets/${ticket.id}`}>
                <TicketCard ticket={ticket} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
