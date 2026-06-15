"""Generates a PNG of the LangGraph workflow and saves it to docs/graph_workflow.png."""
from typing import TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    email_id: str
    subject: str
    body: str
    sender: str
    ticket_id: str
    assigned_team: str
    routing_confidence: float
    evaluator_verdict: str
    supervisor_action: str
    final_team: str


def _dummy(state: AgentState) -> AgentState:
    return state


def _router(state: AgentState) -> str:
    low = state["routing_confidence"] < 0.8
    bad = state["evaluator_verdict"] in ("uncertain", "incorrect")
    return "notify_supervisor" if (low or bad) else "send_notifications"


graph = StateGraph(AgentState)
graph.add_node("classify_ticket", _dummy)
graph.add_node("evaluate_routing", _dummy)
graph.add_node("notify_supervisor", _dummy)
graph.add_node("send_notifications", _dummy)

graph.set_entry_point("classify_ticket")
graph.add_edge("classify_ticket", "evaluate_routing")
graph.add_conditional_edges(
    "evaluate_routing",
    _router,
    {
        "notify_supervisor": "notify_supervisor",
        "send_notifications": "send_notifications",
    },
)
graph.add_edge("notify_supervisor", "send_notifications")
graph.add_edge("send_notifications", END)

compiled = graph.compile()
png_bytes = compiled.get_graph().draw_mermaid_png()

output = "docs/graph_workflow.png"
with open(output, "wb") as f:
    f.write(png_bytes)

print(f"Saved: {output}  ({len(png_bytes):,} bytes)")
