import asyncio
import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.models import Ticket
from app.db.session import SessionLocal

router = APIRouter(prefix="/debug", tags=["debug"])


class InjectRequest(BaseModel):
    subject: str = "Test: printer not working"
    body: str = "The office printer on the 3rd floor stopped responding after the Windows update."
    sender: str = "tester@example.com"


@router.post("/inject")
async def inject_email(req: InjectRequest):
    from app.agent.graph import get_graph
    from app.agent.state import AgentState

    email_id = str(uuid.uuid4())
    ticket_id = str(uuid.uuid4())

    db = SessionLocal()
    try:
        ticket = Ticket(
            id=ticket_id,
            email_id=email_id,
            subject=req.subject,
            body=req.body,
            sender=req.sender,
            status="pending",
        )
        db.add(ticket)
        db.commit()
    finally:
        db.close()

    state: AgentState = {
        "email_id": email_id,
        "subject": req.subject,
        "body": req.body,
        "sender": req.sender,
        "ticket_id": ticket_id,
        "assigned_team": "",
        "routing_confidence": 0.0,
        "evaluator_verdict": "",
        "supervisor_action": "",
        "final_team": "",
    }
    config = {"configurable": {"thread_id": ticket_id}}
    graph = get_graph()
    await asyncio.get_event_loop().run_in_executor(None, graph.invoke, state, config)

    return {"ticket_id": ticket_id, "email_id": email_id}
