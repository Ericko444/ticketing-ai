# Phase 4 Summary: Human-in-the-Loop

**Date:** 2026-06-09
**Commits:** d09f23c (Task 12), 3c7c756 (Task 10), 45fe6f7 (Task 11)
**Tests:** 16 new, 56 total — all passing

## What Was Built

### Task 12 — Email notifications (`d09f23c`)
- `send_team_notification(ticket, team_members)` — SMTP email to all members of the routed team
- `send_supervisor_alert(ticket, supervisor_email)` — alert email with ticket details + dashboard link
- Both are no-ops (INFO log only) when `EMAIL_NOTIFICATIONS=false` in `.env`
- `_send_email()` — shared SMTP_SSL sender using Gmail credentials from settings

### Task 10 — notify_supervisor node wired (`3c7c756`)
- `_notify_supervisor_node` in `graph.py` now calls `send_supervisor_alert()` after updating DB status to `pending_supervisor`, before calling `interrupt()`
- `_send_notifications_node` now calls `send_team_notification()` inside the DB transaction block after `db.commit()`
- Test patches updated: `send_supervisor_alert` must be patched on **both** initial invoke and resume — LangGraph re-executes the entire node on resume, so the code before `interrupt()` runs again

### Task 11 — Supervisor API endpoints (`45fe6f7`)
- `POST /supervisor/approve` — resumes paused graph with `Command(resume={"action": "approved"})`
- `POST /supervisor/override` — validates team, resumes with `Command(resume={"action": "overridden", "team": "<team>"})`
- Both endpoints: verify ticket exists + is `pending_supervisor` (404 otherwise), resume graph via `run_in_executor` (LangGraph is sync)
- Team validation against `VALID_TEAMS` returns 422 for unknown teams
- `get_graph` and `Command` imported at module level for clean patching in tests

## Files Created / Modified

| File | Change |
|---|---|
| `backend/app/notifications/email.py` | New — send_team_notification, send_supervisor_alert |
| `backend/tests/test_notifications/test_email.py` | New — 6 tests |
| `backend/app/agent/graph.py` | Modified — notification calls in both nodes |
| `backend/tests/test_graph.py` | Modified — patch notifications; added test_supervisor_interrupt_sends_alert |
| `backend/app/routers/supervisor.py` | New — approve + override endpoints |
| `backend/tests/test_routers/test_supervisor.py` | New — 10 tests |
| `backend/app/main.py` | Modified — register supervisor router |

## Decisions Made During Implementation

- `get_graph` imported at module level in `supervisor.py` (not lazy) so it can be patched as `app.routers.supervisor.get_graph` in tests
- `StaticPool` used in `db_session` test fixture to ensure a single in-memory SQLite connection is shared across all session creations from the same engine
- `send_supervisor_alert` patched on **both** invoke passes in resume tests — LangGraph replays the full node body on resume, not just code after `interrupt()`
- `send_team_notification` called inside the `try` block (before `db.close()`) to keep the ticket object attached to the session

## Phase 5 Preview

Next: Phase 5 completes the notification pipeline with the SSE broadcaster (`Task 13`). Task 12 is already fully implemented (no stub distinction needed). Phase 5 just adds the SSE broadcaster and the stream endpoint will come in Phase 6.
