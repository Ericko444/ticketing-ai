import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_team_notification(ticket, team_members: list) -> None:
    if not settings.email_notifications:
        logger.info("Email notifications disabled — skipping team notification for ticket %s", ticket.id)
        return

    subject = f"New ticket assigned: {ticket.subject}"
    body = (
        f"A support ticket has been routed to your team.\n\n"
        f"Ticket ID: {ticket.id}\n"
        f"Subject: {ticket.subject}\n"
        f"From: {ticket.sender}\n"
        f"Team: {ticket.final_team}\n\n"
        f"View ticket: {settings.frontend_url}/tickets/{ticket.id}\n"
    )
    _send_email(to_addresses=team_members, subject=subject, body=body)


def send_supervisor_alert(ticket, supervisor_email: str) -> None:
    if not settings.email_notifications:
        logger.info("Email notifications disabled — skipping supervisor alert for ticket %s", ticket.id)
        return

    subject = f"Routing review required: {ticket.subject}"
    body = (
        f"A ticket requires your review before routing.\n\n"
        f"Ticket ID: {ticket.id}\n"
        f"Subject: {ticket.subject}\n"
        f"From: {ticket.sender}\n"
        f"Proposed Team: {ticket.assigned_team}\n"
        f"Confidence: {ticket.routing_confidence:.0%}\n"
        f"Evaluator Verdict: {ticket.evaluator_verdict}\n\n"
        f"Review here: {settings.frontend_url}/supervisor\n"
    )
    _send_email(to_addresses=[supervisor_email], subject=subject, body=body)


def _send_email(to_addresses: list, subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg["From"] = settings.gmail_user
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(settings.gmail_user, settings.gmail_app_password)
        smtp.sendmail(settings.gmail_user, to_addresses, msg.as_string())

    logger.info("Email sent to %s — %s", to_addresses, subject)
