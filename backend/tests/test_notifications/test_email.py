import logging
from unittest.mock import MagicMock, patch

import pytest

from app.notifications.email import send_supervisor_alert, send_team_notification


def _make_ticket(**kwargs):
    t = MagicMock()
    t.id = kwargs.get("id", "t001")
    t.subject = kwargs.get("subject", "Laptop won't boot")
    t.sender = kwargs.get("sender", "user@example.com")
    t.assigned_team = kwargs.get("assigned_team", "IT")
    t.final_team = kwargs.get("final_team", "IT")
    t.routing_confidence = kwargs.get("routing_confidence", 0.55)
    t.evaluator_verdict = kwargs.get("evaluator_verdict", "uncertain")
    return t


def _smtp_mock():
    ctx = MagicMock()
    smtp = MagicMock()
    smtp.__enter__ = MagicMock(return_value=ctx)
    smtp.__exit__ = MagicMock(return_value=False)
    return smtp, ctx


# ── send_team_notification ────────────────────────────────────────────────────

def test_team_notification_no_op_when_disabled(caplog):
    with caplog.at_level(logging.INFO), patch("app.notifications.email.settings") as s:
        s.email_notifications = False
        send_team_notification(_make_ticket(), ["member@team.com"])
    assert "disabled" in caplog.text


def test_team_notification_sends_email():
    smtp, ctx = _smtp_mock()
    with patch("app.notifications.email.settings") as s, \
         patch("app.notifications.email.smtplib.SMTP_SSL", return_value=smtp):
        s.email_notifications = True
        s.gmail_user = "bot@gmail.com"
        s.gmail_app_password = "secret"
        s.frontend_url = "http://localhost:3000"
        send_team_notification(_make_ticket(final_team="IT"), ["it@company.com"])

    ctx.sendmail.assert_called_once()
    _, recipients, message = ctx.sendmail.call_args[0]
    assert "it@company.com" in recipients
    assert "Laptop" in message


def test_team_notification_sends_to_all_members():
    smtp, ctx = _smtp_mock()
    members = ["a@co.com", "b@co.com", "c@co.com"]
    with patch("app.notifications.email.settings") as s, \
         patch("app.notifications.email.smtplib.SMTP_SSL", return_value=smtp):
        s.email_notifications = True
        s.gmail_user = "bot@gmail.com"
        s.gmail_app_password = "pass"
        s.frontend_url = "http://localhost:3000"
        send_team_notification(_make_ticket(), members)

    _, recipients, _ = ctx.sendmail.call_args[0]
    assert recipients == members


# ── send_supervisor_alert ─────────────────────────────────────────────────────

def test_supervisor_alert_no_op_when_disabled(caplog):
    with caplog.at_level(logging.INFO), patch("app.notifications.email.settings") as s:
        s.email_notifications = False
        send_supervisor_alert(_make_ticket(), "sup@example.com")
    assert "disabled" in caplog.text


def test_supervisor_alert_sends_email():
    smtp, ctx = _smtp_mock()
    with patch("app.notifications.email.settings") as s, \
         patch("app.notifications.email.smtplib.SMTP_SSL", return_value=smtp):
        s.email_notifications = True
        s.gmail_user = "bot@gmail.com"
        s.gmail_app_password = "secret"
        s.frontend_url = "http://localhost:3000"
        send_supervisor_alert(_make_ticket(routing_confidence=0.45), "sup@example.com")

    ctx.sendmail.assert_called_once()
    _, recipients, message = ctx.sendmail.call_args[0]
    assert "sup@example.com" in recipients
    assert "review" in message.lower()


def test_supervisor_alert_includes_confidence():
    smtp, ctx = _smtp_mock()
    with patch("app.notifications.email.settings") as s, \
         patch("app.notifications.email.smtplib.SMTP_SSL", return_value=smtp):
        s.email_notifications = True
        s.gmail_user = "bot@gmail.com"
        s.gmail_app_password = "pass"
        s.frontend_url = "http://localhost:3000"
        send_supervisor_alert(_make_ticket(routing_confidence=0.60), "sup@example.com")

    _, _, message = ctx.sendmail.call_args[0]
    assert "60%" in message
