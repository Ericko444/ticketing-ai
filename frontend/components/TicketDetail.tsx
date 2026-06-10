"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTicket, type Ticket } from "@/lib/api";
import TeamBadge from "./TeamBadge";

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
      <main className="max-w-3xl mx-auto p-6">
        <Link
          href="/"
          className="text-sm text-blue-600 hover:underline mb-4 block"
        >
          ← Back to dashboard
        </Link>
        <p className="text-gray-500">Ticket not found.</p>
      </main>
    );
  }

  if (!ticket) {
    return (
      <main className="max-w-3xl mx-auto p-6">
        <p className="text-gray-500">Loading…</p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto p-6">
      <Link
        href="/"
        className="text-sm text-blue-600 hover:underline mb-4 block"
      >
        ← Back to dashboard
      </Link>

      <h1 className="text-xl font-bold mb-4">{ticket.subject}</h1>

      <div className="space-y-3 text-sm mb-6">
        <div className="flex items-center gap-2">
          <span className="text-gray-500 w-36">From</span>
          <span>{ticket.sender}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500 w-36">Assigned team</span>
          <TeamBadge team={ticket.final_team || ticket.assigned_team} />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500 w-36">Confidence</span>
          <span>{(ticket.routing_confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500 w-36">Evaluator verdict</span>
          <span className="capitalize">{ticket.evaluator_verdict}</span>
        </div>
        {ticket.supervisor_action && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 w-36">Supervisor action</span>
            <span className="capitalize">{ticket.supervisor_action}</span>
          </div>
        )}
        {ticket.final_team && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 w-36">Final team</span>
            <TeamBadge team={ticket.final_team} />
          </div>
        )}
        <div className="flex items-center gap-2">
          <span className="text-gray-500 w-36">Status</span>
          <span className="capitalize">{ticket.status.replace("_", " ")}</span>
        </div>
        {ticket.created_at && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 w-36">Received</span>
            <span>{new Date(ticket.created_at).toLocaleString()}</span>
          </div>
        )}
      </div>

      <div className="border rounded p-4 bg-gray-50">
        <p className="text-xs text-gray-400 mb-2 uppercase tracking-wide">
          Email body
        </p>
        <p className="text-sm whitespace-pre-wrap">{ticket.body}</p>
      </div>
    </main>
  );
}
