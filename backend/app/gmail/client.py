import base64
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailClient:
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        self._credentials_path = credentials_path or os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
        self._token_path = token_path or os.getenv("GMAIL_TOKEN_PATH", "token.json")
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service

        creds = None
        token_file = Path(self._token_path)

        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self._credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            token_file.write_text(creds.to_json())

        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def list_unread_messages(self) -> list[str]:
        service = self._get_service()
        result = service.users().messages().list(
            userId="me",
            q="is:unread",
            maxResults=50,
        ).execute()
        messages = result.get("messages", [])
        return [m["id"] for m in messages]

    def get_message(self, message_id: str) -> dict:
        service = self._get_service()
        msg = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()

        headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}
        body = _extract_body(msg["payload"])

        return {
            "email_id": message_id,
            "subject": headers.get("subject", "(no subject)"),
            "sender": headers.get("from", ""),
            "body": body,
        }

    def mark_as_read(self, message_id: str) -> None:
        service = self._get_service()
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()


def _extract_body(payload: dict) -> str:
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return ""
