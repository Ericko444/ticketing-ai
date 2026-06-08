from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True)
    email_id = Column(String, unique=True, nullable=False, index=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    sender = Column(String, nullable=False)
    assigned_team = Column(String, nullable=False, default="")
    routing_confidence = Column(Float, nullable=False, default=0.0)
    evaluator_verdict = Column(String, nullable=False, default="")
    supervisor_action = Column(String, nullable=False, default="")
    final_team = Column(String, nullable=False, default="")
    # pending_supervisor | routed | duplicate
    status = Column(String, nullable=False, default="pending_supervisor")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class DuplicateEmailLog(Base):
    __tablename__ = "duplicate_email_log"

    id = Column(String, primary_key=True)
    email_id = Column(String, nullable=False, index=True)
    detected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
