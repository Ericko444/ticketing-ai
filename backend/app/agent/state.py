from typing import TypedDict


class AgentState(TypedDict):
    email_id: str
    subject: str
    body: str
    sender: str
    assigned_team: str        # "IT" | "Support" | "Helpdesk" | "HR"
    routing_confidence: float  # 0.0 – 1.0
    evaluator_verdict: str    # "correct" | "uncertain" | "incorrect"
    supervisor_action: str    # "approved" | "overridden" | ""
    final_team: str
    ticket_id: str
