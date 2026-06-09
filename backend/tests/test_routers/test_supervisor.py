import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Ticket
from app.routers.supervisor import router


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
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _add_ticket(session_factory, status="pending_supervisor", team="Support") -> str:
    tid = str(uuid.uuid4())
    session = session_factory()
    session.add(Ticket(
        id=tid,
        email_id=f"email_{tid}",
        subject="Routing question",
        body="please help",
        sender="user@example.com",
        assigned_team=team,
        routing_confidence=0.55,
        evaluator_verdict="uncertain",
        status=status,
    ))
    session.commit()
    session.close()
    return tid


# ── POST /supervisor/approve ──────────────────────────────────────────────────

def test_approve_resumes_graph(client, db_session):
    ticket_id = _add_ticket(db_session)
    mock_graph = MagicMock()

    with patch("app.routers.supervisor.SessionLocal", db_session), \
         patch("app.routers.supervisor.get_graph", return_value=mock_graph):
        response = client.post("/supervisor/approve", json={"ticket_id": ticket_id})

    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == ticket_id
    assert data["status"] == "approved"
    mock_graph.invoke.assert_called_once()


def test_approve_passes_approved_command(client, db_session):
    from langgraph.types import Command

    ticket_id = _add_ticket(db_session)
    mock_graph = MagicMock()

    with patch("app.routers.supervisor.SessionLocal", db_session), \
         patch("app.routers.supervisor.get_graph", return_value=mock_graph):
        client.post("/supervisor/approve", json={"ticket_id": ticket_id})

    cmd = mock_graph.invoke.call_args[0][0]
    assert isinstance(cmd, Command)
    assert cmd.resume["action"] == "approved"


def test_approve_ticket_not_found(client, db_session):
    with patch("app.routers.supervisor.SessionLocal", db_session):
        response = client.post("/supervisor/approve", json={"ticket_id": "no-such-id"})
    assert response.status_code == 404


def test_approve_wrong_status_returns_404(client, db_session):
    ticket_id = _add_ticket(db_session, status="routed")
    with patch("app.routers.supervisor.SessionLocal", db_session):
        response = client.post("/supervisor/approve", json={"ticket_id": ticket_id})
    assert response.status_code == 404


# ── POST /supervisor/override ─────────────────────────────────────────────────

def test_override_resumes_graph_with_team(client, db_session):
    ticket_id = _add_ticket(db_session)
    mock_graph = MagicMock()

    with patch("app.routers.supervisor.SessionLocal", db_session), \
         patch("app.routers.supervisor.get_graph", return_value=mock_graph):
        response = client.post("/supervisor/override", json={"ticket_id": ticket_id, "team": "HR"})

    assert response.status_code == 200
    data = response.json()
    assert data["team"] == "HR"
    assert data["status"] == "overridden"
    mock_graph.invoke.assert_called_once()


def test_override_passes_overridden_command(client, db_session):
    from langgraph.types import Command

    ticket_id = _add_ticket(db_session)
    mock_graph = MagicMock()

    with patch("app.routers.supervisor.SessionLocal", db_session), \
         patch("app.routers.supervisor.get_graph", return_value=mock_graph):
        client.post("/supervisor/override", json={"ticket_id": ticket_id, "team": "IT"})

    cmd = mock_graph.invoke.call_args[0][0]
    assert isinstance(cmd, Command)
    assert cmd.resume["action"] == "overridden"
    assert cmd.resume["team"] == "IT"


def test_override_invalid_team_returns_422(client, db_session):
    with patch("app.routers.supervisor.SessionLocal", db_session):
        response = client.post("/supervisor/override", json={"ticket_id": "any", "team": "Finance"})
    assert response.status_code == 422


def test_override_ticket_not_found(client, db_session):
    with patch("app.routers.supervisor.SessionLocal", db_session):
        response = client.post("/supervisor/override", json={"ticket_id": "missing", "team": "HR"})
    assert response.status_code == 404


def test_override_missing_team_field_returns_422(client, db_session):
    with patch("app.routers.supervisor.SessionLocal", db_session):
        response = client.post("/supervisor/override", json={"ticket_id": "any"})
    assert response.status_code == 422
