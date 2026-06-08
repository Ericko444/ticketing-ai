import asyncio
import logging
import uuid
from typing import Callable, Awaitable

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import DuplicateEmailLog, Ticket
from app.db.session import SessionLocal
from app.gmail.client import GmailClient

logger = logging.getLogger(__name__)


async def poll_once(
    gmail: GmailClient,
    on_new_email: Callable[[dict], Awaitable[None]],
) -> None:
    db: Session = SessionLocal()
    try:
        message_ids = gmail.list_unread_messages()
        for message_id in message_ids:
            existing = db.query(Ticket).filter_by(email_id=message_id).first()
            if existing:
                logger.warning("Duplicate email detected: %s — skipping", message_id)
                dup = DuplicateEmailLog(id=str(uuid.uuid4()), email_id=message_id)
                db.add(dup)
                db.commit()
                continue

            try:
                email_data = gmail.get_message(message_id)
            except Exception:
                logger.exception("Failed to fetch message %s", message_id)
                continue

            ticket = Ticket(
                id=str(uuid.uuid4()),
                email_id=email_data["email_id"],
                subject=email_data["subject"],
                body=email_data["body"],
                sender=email_data["sender"],
                status="pending_supervisor",
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)

            try:
                gmail.mark_as_read(message_id)
            except Exception:
                logger.warning("Could not mark message %s as read", message_id)

            await on_new_email({**email_data, "ticket_id": ticket.id})
    finally:
        db.close()


async def start_poller(
    gmail: GmailClient,
    on_new_email: Callable[[dict], Awaitable[None]],
) -> None:
    logger.info(
        "Email poller started (interval: %ss)", settings.polling_interval_seconds
    )
    while True:
        try:
            await poll_once(gmail, on_new_email)
        except Exception:
            logger.exception("Poller iteration failed")
        await asyncio.sleep(settings.polling_interval_seconds)
