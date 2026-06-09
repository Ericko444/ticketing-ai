import asyncio
import logging

from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from pydantic import BaseModel

from app.agent.graph import get_graph
from app.db.models import Ticket
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supervisor", tags=["supervisor"])

VALID_TEAMS = {"IT", "Support", "Helpdesk", "HR"}


class ApproveRequest(BaseModel):
    ticket_id: str


class OverrideRequest(BaseModel):
    ticket_id: str
    team: str


def _get_pending_ticket(ticket_id: str) -> Ticket:
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter_by(id=ticket_id).first()
    finally:
        db.close()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.status != "pending_supervisor":
        raise HTTPException(status_code=404, detail="Ticket is not pending supervisor review")
    return ticket


@router.post("/approve")
async def approve_routing(body: ApproveRequest):
    _get_pending_ticket(body.ticket_id)

    config = {"configurable": {"thread_id": body.ticket_id}}
    graph = get_graph()
    await asyncio.get_event_loop().run_in_executor(
        None,
        graph.invoke,
        Command(resume={"action": "approved"}),
        config,
    )
    logger.info("Supervisor approved routing for ticket %s", body.ticket_id)
    return {"status": "approved", "ticket_id": body.ticket_id}


@router.post("/override")
async def override_routing(body: OverrideRequest):
    if body.team not in VALID_TEAMS:
        raise HTTPException(status_code=422, detail=f"Invalid team '{body.team}'. Valid: {sorted(VALID_TEAMS)}")

    _get_pending_ticket(body.ticket_id)

    config = {"configurable": {"thread_id": body.ticket_id}}
    graph = get_graph()
    await asyncio.get_event_loop().run_in_executor(
        None,
        graph.invoke,
        Command(resume={"action": "overridden", "team": body.team}),
        config,
    )
    logger.info("Supervisor overrode routing for ticket %s → %s", body.ticket_id, body.team)
    return {"status": "overridden", "ticket_id": body.ticket_id, "team": body.team}
