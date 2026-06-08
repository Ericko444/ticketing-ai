import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, DuplicateEmailLog, Ticket


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_tables_created(db_session):
    engine = db_session.bind
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "tickets" in tables
    assert "duplicate_email_log" in tables


def test_ticket_insert_and_query(db_session):
    ticket = Ticket(
        id=str(uuid.uuid4()),
        email_id="gmail_msg_001",
        subject="My laptop won't boot",
        body="I turned it on and nothing happened.",
        sender="user@example.com",
        assigned_team="IT",
        routing_confidence=0.95,
        evaluator_verdict="correct",
        final_team="IT",
        status="routed",
    )
    db_session.add(ticket)
    db_session.commit()

    result = db_session.query(Ticket).filter_by(email_id="gmail_msg_001").first()
    assert result is not None
    assert result.assigned_team == "IT"
    assert result.status == "routed"


def test_ticket_defaults(db_session):
    ticket = Ticket(
        id=str(uuid.uuid4()),
        email_id="gmail_msg_002",
        subject="Question",
        body="Hello",
        sender="a@b.com",
    )
    db_session.add(ticket)
    db_session.commit()

    result = db_session.query(Ticket).filter_by(email_id="gmail_msg_002").first()
    assert result.assigned_team == ""
    assert result.routing_confidence == 0.0
    assert result.status == "pending_supervisor"
    assert isinstance(result.created_at, datetime)


def test_duplicate_email_log(db_session):
    log = DuplicateEmailLog(id=str(uuid.uuid4()), email_id="gmail_msg_001")
    db_session.add(log)
    db_session.commit()

    result = db_session.query(DuplicateEmailLog).filter_by(email_id="gmail_msg_001").first()
    assert result is not None
