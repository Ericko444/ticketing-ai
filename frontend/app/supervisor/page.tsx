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
    <main className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Supervisor Queue</h1>
        <Link href="/" className="text-sm text-blue-600 hover:underline">
          ← Dashboard
        </Link>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : tickets.length === 0 ? (
        <p className="text-gray-500">No tickets pending review.</p>
      ) : (
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="pb-2 font-medium">Subject</th>
              <th className="pb-2 font-medium">Proposed team</th>
              <th className="pb-2 font-medium">Confidence</th>
              <th className="pb-2 font-medium">Verdict</th>
              <th className="pb-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.id} className="border-b">
                <td className="py-3 pr-4 max-w-xs truncate">{ticket.subject}</td>
                <td className="py-3 pr-4">
                  <TeamBadge team={ticket.assigned_team} />
                </td>
                <td className="py-3 pr-4">
                  {(ticket.routing_confidence * 100).toFixed(0)}%
                </td>
                <td className="py-3 pr-4 capitalize">{ticket.evaluator_verdict}</td>
                <td className="py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(ticket.id)}
                      className="px-3 py-1 text-xs rounded bg-green-600 text-white hover:bg-green-700"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => setOverrideTarget(ticket.id)}
                      className="px-3 py-1 text-xs rounded border hover:bg-gray-50"
                    >
                      Override
                    </button>
                  </div>
                  {errors[ticket.id] && (
                    <p className="text-xs text-red-500 mt-1">{errors[ticket.id]}</p>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
