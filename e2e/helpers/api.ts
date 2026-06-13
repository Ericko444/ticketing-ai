const BACKEND = "http://localhost:8000";

export interface InjectParams {
  subject: string;
  body: string;
  sender: string;
  /** Pre-set team — skips the classify LLM node */
  assigned_team?: string;
  /** Pre-set confidence — skips the classify LLM node */
  routing_confidence?: number;
  /** Pre-set verdict — skips the evaluate LLM node */
  evaluator_verdict?: string;
}

export interface InjectResult {
  ticket_id: string;
  email_id: string;
}

export interface Ticket {
  id: string;
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

/** Injects a ticket through the LangGraph pipeline via the debug endpoint. */
export async function injectTicket(params: InjectParams): Promise<InjectResult> {
  const res = await fetch(`${BACKEND}/debug/inject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`inject failed ${res.status}: ${text}`);
  }
  return res.json();
}

/** Injects a ticket that will always be auto-routed (high confidence, correct verdict). */
export async function injectRoutedTicket(
  params: Omit<InjectParams, "routing_confidence" | "evaluator_verdict">
): Promise<InjectResult> {
  return injectTicket({
    ...params,
    routing_confidence: 0.97,
    evaluator_verdict: "correct",
  });
}

/** Injects a ticket that will always land in the supervisor queue (low confidence, uncertain verdict). */
export async function injectSupervisorTicket(
  params: Omit<InjectParams, "routing_confidence" | "evaluator_verdict">
): Promise<InjectResult> {
  return injectTicket({
    ...params,
    routing_confidence: 0.35,
    evaluator_verdict: "uncertain",
  });
}

export async function getTicket(id: string): Promise<Ticket> {
  const res = await fetch(`${BACKEND}/tickets/${id}`);
  if (!res.ok) throw new Error(`getTicket failed: ${res.status}`);
  return res.json();
}
