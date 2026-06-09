import uuid
from unittest.mock import MagicMock, patch

import pytest
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.graph import build_graph
from app.agent.state import AgentState
from app.db.models import Base, Ticket


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


def _make_graph(mock_classify_response: str, mock_evaluate_response: str):
    mock_response = MagicMock()
    mock_llm = MagicMock()

    call_count = 0

    def side_effect(prompt):
        nonlocal call_count
        call_count += 1
        r = MagicMock()
        r.content = mock_classify_response if call_count == 1 else mock_evaluate_response
        return r

    mock_llm.invoke.side_effect = side_effect
    return mock_llm


def _base_input(ticket_id: str = None) -> AgentState:
    return {
        "email_id": "msg_001",
        "subject": "My laptop won't boot",
        "body": "I turned it on and nothing happened.",
        "sender": "user@example.com",
        "assigned_team": "",
        "routing_confidence": 0.0,
        "evaluator_verdict": "",
        "supervisor_action": "",
        "final_team": "",
        "ticket_id": ticket_id or str(uuid.uuid4()),
    }


# ── High-confidence path (direct to send_notifications) ───────────────────────

def test_high_confidence_routes_directly(in_memory_db):
    ticket_id = str(uuid.uuid4())
    session = in_memory_db()
    session.add(Ticket(
        id=ticket_id, email_id="msg_001", subject="Laptop", body="broken", sender="u@e.com"
    ))
    session.commit()
    session.close()

    mock_llm = _make_graph(
        '{"team": "IT", "confidence": 0.95}',
        '{"verdict": "correct"}',
    )

    config = {"configurable": {"thread_id": ticket_id}}
    with patch("app.agent.nodes._llm", mock_llm), \
         patch("app.agent.graph.SessionLocal", in_memory_db), \
         patch("app.agent.graph.send_team_notification"), \
         patch("app.agent.graph.send_supervisor_alert"):

        graph = build_graph(checkpointer=MemorySaver())
        result = graph.invoke(_base_input(ticket_id), config)

    assert result["assigned_team"] == "IT"
    assert result["routing_confidence"] == 0.95
    assert result["evaluator_verdict"] == "correct"
    assert result["final_team"] == "IT"

    session = in_memory_db()
    ticket = session.query(Ticket).filter_by(id=ticket_id).first()
    assert ticket.status == "routed"
    assert ticket.final_team == "IT"
    session.close()


# ── Low-confidence path (supervisor interrupt) ─────────────────────────────────

def test_low_confidence_triggers_supervisor_interrupt(in_memory_db):
    ticket_id = str(uuid.uuid4())
    session = in_memory_db()
    session.add(Ticket(
        id=ticket_id, email_id="msg_002", subject="Question", body="help", sender="u@e.com"
    ))
    session.commit()
    session.close()

    mock_llm = _make_graph(
        '{"team": "Support", "confidence": 0.55}',
        '{"verdict": "uncertain"}',
    )

    config = {"configurable": {"thread_id": ticket_id}}
    graph = build_graph(checkpointer=MemorySaver())

    with patch("app.agent.nodes._llm", mock_llm), \
         patch("app.agent.graph.SessionLocal", in_memory_db), \
         patch("app.agent.graph.send_supervisor_alert"):
        result = graph.invoke(_base_input(ticket_id), config)

    # Graph should be interrupted — result is the interrupt value, not final state
    assert result is not None
    # Check DB ticket is pending_supervisor
    session = in_memory_db()
    ticket = session.query(Ticket).filter_by(id=ticket_id).first()
    assert ticket.status == "pending_supervisor"
    session.close()


def test_supervisor_interrupt_sends_alert(in_memory_db):
    ticket_id = str(uuid.uuid4())
    session = in_memory_db()
    session.add(Ticket(
        id=ticket_id, email_id="msg_002b", subject="Payroll question", body="help", sender="u@e.com"
    ))
    session.commit()
    session.close()

    mock_llm = _make_graph(
        '{"team": "Support", "confidence": 0.40}',
        '{"verdict": "uncertain"}',
    )

    config = {"configurable": {"thread_id": ticket_id}}
    graph = build_graph(checkpointer=MemorySaver())

    with patch("app.agent.nodes._llm", mock_llm), \
         patch("app.agent.graph.SessionLocal", in_memory_db), \
         patch("app.agent.graph.send_supervisor_alert") as mock_alert:
        graph.invoke(_base_input(ticket_id), config)

    mock_alert.assert_called_once()
    # Verify the ticket was persisted as pending before the alert was sent
    session = in_memory_db()
    ticket = session.query(Ticket).filter_by(id=ticket_id).first()
    assert ticket.status == "pending_supervisor"
    session.close()


def test_supervisor_resume_approved(in_memory_db):
    from langgraph.types import Command

    ticket_id = str(uuid.uuid4())
    session = in_memory_db()
    session.add(Ticket(
        id=ticket_id, email_id="msg_003", subject="Question", body="help", sender="u@e.com"
    ))
    session.commit()
    session.close()

    mock_llm = _make_graph(
        '{"team": "Support", "confidence": 0.55}',
        '{"verdict": "uncertain"}',
    )

    config = {"configurable": {"thread_id": ticket_id}}
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)

    with patch("app.agent.nodes._llm", mock_llm), \
         patch("app.agent.graph.SessionLocal", in_memory_db), \
         patch("app.agent.graph.send_supervisor_alert"):
        graph.invoke(_base_input(ticket_id), config)

    with patch("app.agent.graph.SessionLocal", in_memory_db), \
         patch("app.agent.graph.send_supervisor_alert"), \
         patch("app.agent.graph.send_team_notification"):
        result = graph.invoke(
            Command(resume={"action": "approved", "team": "Support"}),
            config,
        )

    assert result["supervisor_action"] == "approved"
    assert result["final_team"] == "Support"

    session = in_memory_db()
    ticket = session.query(Ticket).filter_by(id=ticket_id).first()
    assert ticket.status == "routed"
    session.close()


def test_supervisor_resume_overridden(in_memory_db):
    from langgraph.types import Command

    ticket_id = str(uuid.uuid4())
    session = in_memory_db()
    session.add(Ticket(
        id=ticket_id, email_id="msg_004", subject="Payroll issue", body="wrong amount", sender="u@e.com"
    ))
    session.commit()
    session.close()

    mock_llm = _make_graph(
        '{"team": "Support", "confidence": 0.45}',
        '{"verdict": "incorrect"}',
    )

    config = {"configurable": {"thread_id": ticket_id}}
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)

    with patch("app.agent.nodes._llm", mock_llm), \
         patch("app.agent.graph.SessionLocal", in_memory_db), \
         patch("app.agent.graph.send_supervisor_alert"):
        graph.invoke(_base_input(ticket_id), config)

    with patch("app.agent.graph.SessionLocal", in_memory_db), \
         patch("app.agent.graph.send_supervisor_alert"), \
         patch("app.agent.graph.send_team_notification"):
        result = graph.invoke(
            Command(resume={"action": "overridden", "team": "HR"}),
            config,
        )

    assert result["supervisor_action"] == "overridden"
    assert result["final_team"] == "HR"

    session = in_memory_db()
    ticket = session.query(Ticket).filter_by(id=ticket_id).first()
    assert ticket.status == "routed"
    assert ticket.final_team == "HR"
    session.close()
