# Phase 2 Summary: Gmail Integration

**Date:** 2026-06-08
**Commits:** d464d22 (Task 4), a155aeb (Task 5)
**Tests:** 14 new, 21 total — all passing

## What Was Built

### Task 4 — Gmail OAuth2 client (`d464d22`)
- `GmailClient` class in `backend/app/gmail/client.py`
- `list_unread_messages()` — returns list of unread message IDs (up to 50)
- `get_message(id)` — fetches full message, returns `{email_id, subject, sender, body}`
- `mark_as_read(id)` — removes UNREAD label via Gmail modify API
- `_extract_body()` — handles direct base64 data, `text/plain` parts, and nested `multipart/*` payloads recursively
- OAuth2 token stored in `token.json`, auto-refreshed when expired; first-run triggers browser flow

### Task 5 — Email poller (`a155aeb`)
- `poll_once()` — single poll iteration: list unread → deduplicate → fetch → insert Ticket → mark read → call handler
- `start_poller()` — infinite asyncio loop calling `poll_once()` every `settings.polling_interval_seconds` (30s)
- Duplicate detection: checks `Ticket.email_id` in DB; logs warning + inserts `DuplicateEmailLog` if already seen
- Poller registered as `asyncio.create_task()` inside FastAPI `lifespan`; cancelled cleanly on shutdown
- `on_new_email` callback receives `{email_id, subject, sender, body, ticket_id}` — Phase 3 wires this to the agent graph

## Files Created / Modified

| File | Change |
|---|---|
| `backend/app/gmail/client.py` | New — GmailClient + _extract_body |
| `backend/app/gmail/poller.py` | New — poll_once + start_poller |
| `backend/app/main.py` | Modified — lifespan now starts/stops poller task |
| `backend/tests/test_gmail_client.py` | New — 9 tests |
| `backend/tests/test_poller.py` | New — 5 tests |

## Decisions Made During Implementation

- `_noop_handler` used as default `on_new_email` callback in `main.py` lifespan — Phase 3 will replace this with the real agent graph trigger
- `mark_as_read` failure is a warning, not a hard error — prevents email being lost if the Gmail modify call flickers
- `get_message` failure skips the email entirely this poll cycle — it will appear again on the next poll if still unread

## Phase 3 Preview

Next: `AgentState` TypedDict + prompts (Task 6) → classify node (Task 7) → evaluate node (Task 8) → graph assembly (Task 9).
