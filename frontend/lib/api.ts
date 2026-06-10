const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Ticket {
  id: string;
  email_id: string;
  subject: string;
  body: string;
  sender: string;
  assigned_team: string;
  routing_confidence: number;
  evaluator_verdict: string;
  supervisor_action: string;
  final_team: string;
  status: string;
  created_at: string | null;
}

export async function getTickets(skip = 0, limit = 20): Promise<Ticket[]> {
  const res = await fetch(`${API_URL}/tickets?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch tickets");
  return res.json();
}

export async function getTicket(id: string): Promise<Ticket> {
  const res = await fetch(`${API_URL}/tickets/${id}`);
  if (!res.ok) throw new Error("Ticket not found");
  return res.json();
}

export async function approveRouting(ticketId: string): Promise<void> {
  const res = await fetch(`${API_URL}/supervisor/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticket_id: ticketId }),
  });
  if (!res.ok) throw new Error("Failed to approve routing");
}

export async function overrideRouting(
  ticketId: string,
  team: string
): Promise<void> {
  const res = await fetch(`${API_URL}/supervisor/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticket_id: ticketId, team }),
  });
  if (!res.ok) throw new Error("Failed to override routing");
}
