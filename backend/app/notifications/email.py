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
    backend = settings.email_backend.lower()

    if backend == "log":
        _send_log(to_addresses, subject, body)
    elif backend == "mailtrap":
        _send_smtp(
            to_addresses, subject, body,
            host="sandbox.smtp.mailtrap.io",
            port=587,
            user=settings.mailtrap_user,
            password=settings.mailtrap_password,
            sender=settings.mailtrap_user,
        )
    elif backend == "gmail":
        _send_smtp(
            to_addresses, subject, body,
            host="smtp.gmail.com",
            port=465,
            user=settings.gmail_user,
            password=settings.gmail_app_password,
            sender=settings.gmail_user,
            use_ssl=True,
        )
    else:
        logger.warning("Unknown EMAIL_BACKEND '%s' — falling back to log", backend)
        _send_log(to_addresses, subject, body)


def _send_log(to_addresses: list, subject: str, body: str) -> None:
    logger.info(
        "--- EMAIL (log backend) ---\nTo: %s\nSubject: %s\n\n%s\n--------------------------",
        ", ".join(to_addresses),
        subject,
        body,
    )


def _send_smtp(
    to_addresses: list,
    subject: str,
    body: str,
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    sender: str,
    use_ssl: bool = False,
) -> None:
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        if use_ssl:
            ctx = smtplib.SMTP_SSL(host, port)
        else:
            ctx = smtplib.SMTP(host, port)
        with ctx as smtp:
            if not use_ssl:
                smtp.starttls()
            smtp.login(user, password)
            smtp.sendmail(sender, to_addresses, msg.as_string())
        logger.info("Email sent via %s to %s — %s", host, to_addresses, subject)
    except Exception as exc:
        logger.error("Failed to send email via %s: %s", host, exc)
