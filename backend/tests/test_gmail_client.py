import base64
from unittest.mock import MagicMock, patch

import pytest

from app.gmail.client import GmailClient, _extract_body


def _make_client_with_mock_service(mock_service):
    client = GmailClient(credentials_path="fake.json", token_path="fake_token.json")
    client._service = mock_service
    return client


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


# ── _extract_body ──────────────────────────────────────────────────────────────

def test_extract_body_from_direct_data():
    payload = {"body": {"data": _b64("Hello world")}, "parts": []}
    assert _extract_body(payload) == "Hello world"


def test_extract_body_from_text_plain_part():
    payload = {
        "body": {"data": ""},
        "parts": [
            {"mimeType": "text/plain", "body": {"data": _b64("Plain text body")}},
            {"mimeType": "text/html", "body": {"data": _b64("<p>HTML</p>")}},
        ],
    }
    assert _extract_body(payload) == "Plain text body"


def test_extract_body_nested_parts():
    payload = {
        "body": {},
        "parts": [
            {
                "mimeType": "multipart/alternative",
                "body": {},
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": _b64("Nested plain")}},
                ],
            }
        ],
    }
    assert _extract_body(payload) == "Nested plain"


def test_extract_body_empty_returns_empty_string():
    assert _extract_body({"body": {}, "parts": []}) == ""


# ── GmailClient ────────────────────────────────────────────────────────────────

def test_list_unread_messages_returns_ids():
    mock_service = MagicMock()
    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg_001"}, {"id": "msg_002"}]
    }
    client = _make_client_with_mock_service(mock_service)
    result = client.list_unread_messages()
    assert result == ["msg_001", "msg_002"]


def test_list_unread_messages_empty_inbox():
    mock_service = MagicMock()
    mock_service.users().messages().list().execute.return_value = {}
    client = _make_client_with_mock_service(mock_service)
    assert client.list_unread_messages() == []


def test_get_message_parses_headers_and_body():
    mock_service = MagicMock()
    mock_service.users().messages().get().execute.return_value = {
        "id": "msg_001",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "My laptop won't boot"},
                {"name": "From", "value": "user@example.com"},
            ],
            "body": {"data": _b64("I turned it on and nothing happened.")},
            "parts": [],
        },
    }
    client = _make_client_with_mock_service(mock_service)
    result = client.get_message("msg_001")

    assert result["email_id"] == "msg_001"
    assert result["subject"] == "My laptop won't boot"
    assert result["sender"] == "user@example.com"
    assert result["body"] == "I turned it on and nothing happened."


def test_get_message_missing_subject_uses_default():
    mock_service = MagicMock()
    mock_service.users().messages().get().execute.return_value = {
        "id": "msg_002",
        "payload": {
            "headers": [{"name": "From", "value": "x@y.com"}],
            "body": {"data": _b64("body")},
            "parts": [],
        },
    }
    client = _make_client_with_mock_service(mock_service)
    result = client.get_message("msg_002")
    assert result["subject"] == "(no subject)"


def test_mark_as_read_calls_modify():
    mock_service = MagicMock()
    client = _make_client_with_mock_service(mock_service)
    client.mark_as_read("msg_001")
    mock_service.users().messages().modify.assert_called_once_with(
        userId="me",
        id="msg_001",
        body={"removeLabelIds": ["UNREAD"]},
    )
