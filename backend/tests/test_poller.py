import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, DuplicateEmailLog, Ticket
from app.gmail.poller import poll_once


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session


@pytest.fixture
def mock_gmail():
    gmail = MagicMock()
    gmail.list_unread_messages.return_value = ["msg_001"]
    gmail.get_message.return_value = {
        "email_id": "msg_001",
        "subject": "VPN not working",
        "sender": "user@example.com",
        "body": "I can't connect to the VPN.",
    }
    return gmail


async def test_new_email_creates_ticket(in_memory_db, mock_gmail):
    handler_calls = []

    async def handler(data):
        handler_calls.append(data)

    with patch("app.gmail.poller.SessionLocal", in_memory_db):
        await poll_once(mock_gmail, handler)

    session = in_memory_db()
    ticket = session.query(Ticket).filter_by(email_id="msg_001").first()
    assert ticket is not None
    assert ticket.subject == "VPN not working"
    assert ticket.status == "pending_supervisor"
    assert len(handler_calls) == 1
    assert handler_calls[0]["ticket_id"] == ticket.id
    session.close()


async def test_new_email_marked_as_read(in_memory_db, mock_gmail):
    with patch("app.gmail.poller.SessionLocal", in_memory_db):
        await poll_once(mock_gmail, AsyncMock())

    mock_gmail.mark_as_read.assert_called_once_with("msg_001")


async def test_duplicate_email_skipped(in_memory_db, mock_gmail):
    session = in_memory_db()
    session.add(Ticket(
        id=str(uuid.uuid4()),
        email_id="msg_001",
        subject="existing",
        body="body",
        sender="a@b.com",
    ))
    session.commit()
    session.close()

    handler = AsyncMock()
    with patch("app.gmail.poller.SessionLocal", in_memory_db):
        await poll_once(mock_gmail, handler)

    handler.assert_not_called()
    mock_gmail.get_message.assert_not_called()

    session = in_memory_db()
    dup_count = session.query(DuplicateEmailLog).filter_by(email_id="msg_001").count()
    assert dup_count == 1
    session.close()


async def test_empty_inbox_does_nothing(in_memory_db):
    gmail = MagicMock()
    gmail.list_unread_messages.return_value = []
    handler = AsyncMock()

    with patch("app.gmail.poller.SessionLocal", in_memory_db):
        await poll_once(gmail, handler)

    handler.assert_not_called()


async def test_failed_get_message_skips_email(in_memory_db, mock_gmail):
    mock_gmail.get_message.side_effect = Exception("API error")
    handler = AsyncMock()

    with patch("app.gmail.poller.SessionLocal", in_memory_db):
        await poll_once(mock_gmail, handler)

    handler.assert_not_called()
    session = in_memory_db()
    assert session.query(Ticket).count() == 0
    session.close()
