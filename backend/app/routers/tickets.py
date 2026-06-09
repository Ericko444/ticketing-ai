from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.models import Ticket
from app.db.session import get_db

router = APIRouter(prefix="/tickets", tags=["tickets"])


class TicketOut(BaseModel):
    id: str
    email_id: str
    subject: str
    body: str
    sender: str
    assigned_team: str
    routing_confidence: float
    evaluator_verdict: str
    supervisor_action: str
    final_team: str
    status: str
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TicketOut])
def list_tickets(skip: int = 0, limit: int = 20, db=Depends(get_db)):
    return (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db=Depends(get_db)):
    ticket = db.query(Ticket).filter_by(id=ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
