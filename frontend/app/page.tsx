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

  return (
    <main className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Ticket Dashboard</h1>
        <Link
          href="/supervisor"
          className="text-sm text-blue-600 hover:underline"
        >
          Supervisor Queue
        </Link>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading tickets…</p>
      ) : tickets.length === 0 ? (
        <p className="text-gray-500">No tickets yet.</p>
      ) : (
        <ul className="space-y-3">
          {tickets.map((ticket) => (
            <li key={ticket.id}>
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
