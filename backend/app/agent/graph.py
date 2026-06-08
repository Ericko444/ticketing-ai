import logging
from pathlib import Path
from typing import Literal

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from app.agent.nodes import classify_ticket, evaluate_routing
from app.agent.state import AgentState
from app.config import settings
from app.db.models import Ticket
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

_DB_PATH = str(Path(__file__).parent.parent.parent / "ticketing.db")


def _needs_supervisor(state: AgentState) -> Literal["notify_supervisor", "send_notifications"]:
    low_confidence = state["routing_confidence"] < settings.confidence_threshold
    bad_verdict = state["evaluator_verdict"] in ("uncertain", "incorrect")
    if low_confidence or bad_verdict:
        return "notify_supervisor"
    return "send_notifications"


def _notify_supervisor_node(state: AgentState) -> AgentState:
    from langgraph.types import interrupt

    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter_by(id=state["ticket_id"]).first()
        if ticket:
            ticket.status = "pending_supervisor"
            ticket.assigned_team = state["assigned_team"]
            ticket.routing_confidence = state["routing_confidence"]
            ticket.evaluator_verdict = state["evaluator_verdict"]
            db.commit()
    finally:
        db.close()

    supervisor_input = interrupt(
        {
            "message": "Routing needs review",
            "ticket_id": state["ticket_id"],
            "proposed_team": state["assigned_team"],
            "confidence": state["routing_confidence"],
            "verdict": state["evaluator_verdict"],
        }
    )
    action = supervisor_input.get("action", "approved")
    override_team = supervisor_input.get("team", state["assigned_team"])

    final_team = override_team if action == "overridden" else state["assigned_team"]
    return {**state, "supervisor_action": action, "final_team": final_team}


def _send_notifications_node(state: AgentState) -> AgentState:
    final_team = state.get("final_team") or state["assigned_team"]

    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter_by(id=state["ticket_id"]).first()
        if ticket:
            ticket.final_team = final_team
            ticket.assigned_team = state["assigned_team"]
            ticket.routing_confidence = state["routing_confidence"]
            ticket.evaluator_verdict = state["evaluator_verdict"]
            ticket.supervisor_action = state.get("supervisor_action", "")
            ticket.status = "routed"
            db.commit()
    finally:
        db.close()

    logger.info("Ticket %s routed to %s", state["ticket_id"], final_team)
    return {**state, "final_team": final_team}


def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)
    graph.add_node("classify_ticket", classify_ticket)
    graph.add_node("evaluate_routing", evaluate_routing)
    graph.add_node("notify_supervisor", _notify_supervisor_node)
    graph.add_node("send_notifications", _send_notifications_node)

    graph.set_entry_point("classify_ticket")
    graph.add_edge("classify_ticket", "evaluate_routing")
    graph.add_conditional_edges("evaluate_routing", _needs_supervisor)
    graph.add_edge("notify_supervisor", "send_notifications")
    graph.add_edge("send_notifications", END)

    if checkpointer is None:
        checkpointer = SqliteSaver.from_conn_string(_DB_PATH)

    return graph.compile(checkpointer=checkpointer)


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
