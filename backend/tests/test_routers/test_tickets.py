import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Ticket
from app.db.session import get_db
from app.routers.tickets import router


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(router)
    return TestClient(app)


def _add_ticket(db_session, **kwargs) -> str:
    tid = kwargs.pop("id", str(uuid.uuid4()))
    t = Ticket(
        id=tid,
        email_id=kwargs.get("email_id", f"email_{tid}"),
        subject=kwargs.get("subject", "Test subject"),
        body=kwargs.get("body", "Test body"),
        sender=kwargs.get("sender", "user@example.com"),
        assigned_team=kwargs.get("assigned_team", "IT"),
        routing_confidence=kwargs.get("routing_confidence", 0.95),
        evaluator_verdict=kwargs.get("evaluator_verdict", "correct"),
        supervisor_action=kwargs.get("supervisor_action", ""),
        final_team=kwargs.get("final_team", "IT"),
        status=kwargs.get("status", "routed"),
        created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
    )
    db = db_session()
    db.add(t)
    db.commit()
    db.close()
    return tid  # return the ID string, not the detached ORM object


# ── GET /tickets ──────────────────────────────────────────────────────────────

def test_list_tickets_empty(client):
    response = client.get("/tickets")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tickets_returns_all(client, db_session):
    _add_ticket(db_session)
    _add_ticket(db_session)
    response = client.get("/tickets")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_tickets_newest_first(client, db_session):
    t1 = _add_ticket(db_session, subject="Older", created_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
    t2 = _add_ticket(db_session, subject="Newer", created_at=datetime(2024, 6, 1, tzinfo=timezone.utc))
    response = client.get("/tickets")
    data = response.json()
    assert data[0]["subject"] == "Newer"
    assert data[1]["subject"] == "Older"


def test_list_tickets_pagination(client, db_session):
    for i in range(5):
        _add_ticket(db_session)
    response = client.get("/tickets?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_tickets_default_limit(client, db_session):
    for i in range(25):
        _add_ticket(db_session)
    response = client.get("/tickets")
    assert len(response.json()) == 20


def test_list_tickets_schema(client, db_session):
    _add_ticket(db_session, subject="Laptop issue", sender="emp@co.com", final_team="IT")
    data = client.get("/tickets").json()
    t = data[0]
    for field in ("id", "email_id", "subject", "body", "sender", "assigned_team",
                  "routing_confidence", "evaluator_verdict", "supervisor_action",
                  "final_team", "status", "created_at"):
        assert field in t


# ── GET /tickets/{id} ─────────────────────────────────────────────────────────

def test_get_ticket_returns_detail(client, db_session):
    ticket_id = _add_ticket(db_session, subject="HR payroll question", sender="hr@co.com")
    response = client.get(f"/tickets/{ticket_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == ticket_id
    assert data["subject"] == "HR payroll question"
    assert data["sender"] == "hr@co.com"


def test_get_ticket_not_found(client):
    response = client.get("/tickets/nonexistent-id")
    assert response.status_code == 404
