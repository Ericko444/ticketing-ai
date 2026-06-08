# Implementation Plan: AI-Powered Email Ticketing System

## Overview

Full-stack LangGraph ticketing system: Gmail ingestion → AI routing → routing evaluator → supervisor human-in-the-loop (when needed) → team notifications via email + real-time dashboard. Backend: Python/FastAPI. Frontend: Next.js. 19 tasks across 7 phases.

## Architecture Decisions

- **LangGraph SqliteSaver** for checkpointing — enables `interrupt()` to persist graph state across HTTP requests (supervisor approve/override resumes the paused graph)
- **SSE over WebSockets** — simpler server-side implementation, unidirectional push is all we need
- **One graph run per email** — each incoming email is its own LangGraph thread (thread_id = email_id)
- **Config-first** — teams, members, supervisor email all in `config.yaml`; no DB tables for team config in v1

---

## Dependency Graph

```
config.yaml + DB models
        ↓
Gmail OAuth2 client
        ↓
Email poller (background)
        ↓
AgentState TypedDict + prompts
        ↓
classify_ticket node → evaluate_routing node
        ↓
Graph assembly (conditional edge: confidence < 0.8 → interrupt)
        ↓
supervisor endpoints (resume graph) + email notifications + SSE broadcaster
        ↓
FastAPI routers (tickets, supervisor, stream)
        ↓
Next.js frontend (dashboard, detail, supervisor queue)
```

---

## Phase 1: Foundation

### Task 1: Backend project scaffolding
**Description:** Create the backend directory structure, virtual environment config, dependencies list, and FastAPI app skeleton.

**Acceptance criteria:**
- [ ] `backend/` directory matches spec structure
- [ ] `requirements.txt` includes: `langgraph`, `langchain-anthropic`, `fastapi`, `uvicorn`, `google-api-python-client`, `google-auth-oauthlib`, `sqlalchemy`, `pyyaml`, `python-dotenv`, `httpx`, `pytest`, `pytest-cov`
- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] `.env.example` documents all required env vars

**Verification:**
- [ ] `cd backend && uvicorn app.main:app --reload --port 8000` returns HTTP 200 on `GET /health`

**Dependencies:** None

**Files:**
- `backend/app/main.py`
- `backend/requirements.txt`
- `backend/.env.example`

**Scope:** S

---

### Task 2: Config system
**Description:** Load `config.yaml` at startup — team definitions, member email lists, supervisor email, confidence threshold, polling interval.

**Acceptance criteria:**
- [ ] `config.yaml` at project root defines all four teams with member emails and supervisor email
- [ ] `app/config.py` loads and validates config on import; raises on missing required fields
- [ ] Config is accessible as a typed object throughout the app

**Verification:**
- [ ] `python -c "from app.config import settings; print(settings.teams)"` prints team config
- [ ] Missing required field raises `ValueError` with a clear message

**Dependencies:** Task 1

**Files:**
- `config.yaml`
- `backend/app/config.py`

**Scope:** S

---

### Task 3: Database models
**Description:** SQLite schema for tickets. Stores ticket data, routing decision, evaluator verdict, supervisor action, and status.

**Acceptance criteria:**
- [ ] `Ticket` model has fields: `id`, `email_id`, `subject`, `body`, `sender`, `assigned_team`, `routing_confidence`, `evaluator_verdict`, `supervisor_action`, `final_team`, `status` (`pending_supervisor` | `routed` | `duplicate`), `created_at`
- [ ] `create_all()` runs on app startup
- [ ] `DuplicateEmailLog` model records skipped duplicate email IDs

**Verification:**
- [ ] App startup creates `ticketing.db` with correct schema
- [ ] `pytest tests/test_db.py` passes

**Dependencies:** Task 1

**Files:**
- `backend/app/db/models.py`
- `backend/app/db/session.py`
- `backend/tests/test_db.py`

**Scope:** S

---

### Checkpoint: Phase 1
- [ ] `uvicorn app.main:app --reload` starts clean
- [ ] Config loads from `config.yaml`
- [ ] SQLite DB created on startup with correct schema
- [ ] `pytest tests/` passes

---

## Phase 2: Gmail Integration

### Task 4: Gmail OAuth2 client
**Description:** Authenticate with Gmail API using OAuth2. Handles initial auth flow, token storage, and automatic token refresh.

**Acceptance criteria:**
- [ ] `GmailClient` class with methods: `list_unread_messages()`, `get_message(id)`, `mark_as_read(id)`
- [ ] Tokens stored in `token.json` (gitignored); auto-refreshed when expired
- [ ] `credentials.json` path configurable via `.env`
- [ ] `get_message()` returns parsed dict with `email_id`, `subject`, `body`, `sender`

**Verification:**
- [ ] `python -c "from app.gmail.client import GmailClient; c = GmailClient(); print(c.list_unread_messages())"` runs without error (may return empty list if inbox is empty)
- [ ] `pytest tests/test_gmail_client.py` passes (uses mocked HTTP responses)

**Dependencies:** Task 2

**Files:**
- `backend/app/gmail/client.py`
- `backend/tests/test_gmail_client.py`

**Scope:** M

---

### Task 5: Email poller
**Description:** Background asyncio task that polls Gmail every 30s, deduplicates, and hands new emails to the agent graph.

**Acceptance criteria:**
- [ ] Poller runs as a FastAPI `lifespan` background task
- [ ] Calls `GmailClient.list_unread_messages()` every 30s
- [ ] Checks DB for duplicate `email_id`; logs warning and inserts `DuplicateEmailLog` if already seen
- [ ] For new emails: creates a DB ticket with `status=pending`, triggers graph run
- [ ] Marks email as read in Gmail after DB insert

**Verification:**
- [ ] `pytest tests/test_poller.py` passes (mocked Gmail client + mocked graph trigger)

**Dependencies:** Tasks 3, 4

**Files:**
- `backend/app/gmail/poller.py`
- `backend/app/main.py` (lifespan update)
- `backend/tests/test_poller.py`

**Scope:** M

---

### Checkpoint: Phase 2
- [ ] Poller starts with the app and runs in background
- [ ] Duplicate emails are flagged, not reprocessed
- [ ] `pytest tests/` passes

---

## Phase 3: LangGraph Agent Core

### Task 6: Agent state and prompts
**Description:** Define the `AgentState` TypedDict and all LLM prompt templates used by the agent.

**Acceptance criteria:**
- [ ] `AgentState` matches the spec exactly (all 9 fields)
- [ ] `CLASSIFY_PROMPT` instructs the LLM to return team name + confidence score as JSON
- [ ] `EVALUATE_PROMPT` instructs the LLM to return `correct` | `uncertain` | `incorrect` as JSON
- [ ] Prompts tested with representative email fixtures

**Verification:**
- [ ] `pytest tests/test_prompts.py` passes (validates prompt output format with fixture responses)

**Dependencies:** Task 1

**Files:**
- `backend/app/agent/state.py`
- `backend/app/agent/prompts.py`
- `backend/tests/test_prompts.py`

**Scope:** S

---

### Task 7: Classify ticket node
**Description:** LangGraph node that sends email subject + body to Claude and returns the assigned team and confidence score.

**Acceptance criteria:**
- [ ] `classify_ticket(state)` calls Claude with `CLASSIFY_PROMPT`
- [ ] Parses JSON response: `{"team": "IT", "confidence": 0.92}`
- [ ] Returns updated state with `assigned_team` and `routing_confidence`
- [ ] Handles malformed LLM output gracefully (defaults to confidence 0.0 on parse error)

**Verification:**
- [ ] `pytest tests/test_nodes.py::test_classify_ticket` passes with fixture LLM responses

**Dependencies:** Task 6

**Files:**
- `backend/app/agent/nodes.py`
- `backend/tests/test_nodes.py`

**Scope:** M

---

### Task 8: Evaluate routing node
**Description:** LangGraph node that runs a second LLM call to verify the classification is correct before notifications fire.

**Acceptance criteria:**
- [ ] `evaluate_routing(state)` calls Claude with `EVALUATE_PROMPT` (email + proposed team)
- [ ] Parses JSON response: `{"verdict": "correct"}` | `{"verdict": "uncertain"}` | `{"verdict": "incorrect"}`
- [ ] Returns updated state with `evaluator_verdict`
- [ ] `uncertain` or `incorrect` verdict triggers supervisor path regardless of `routing_confidence`

**Verification:**
- [ ] `pytest tests/test_nodes.py::test_evaluate_routing` passes

**Dependencies:** Task 7

**Files:**
- `backend/app/agent/nodes.py` (add node)
- `backend/app/agent/prompts.py` (add EVALUATE_PROMPT)
- `backend/tests/test_nodes.py` (add test)

**Scope:** M

---

### Task 9: Graph assembly
**Description:** Wire all nodes into a compiled LangGraph graph with correct edges and conditional branching.

**Acceptance criteria:**
- [ ] Graph: `ingest_email → classify_ticket → evaluate_routing → [conditional]`
- [ ] Conditional edge: if `routing_confidence < 0.8` OR `evaluator_verdict != "correct"` → `notify_supervisor`; else → `send_notifications`
- [ ] `SqliteSaver` checkpointer configured (enables interrupt/resume)
- [ ] Graph compiled and importable without errors
- [ ] Each email processed in its own thread (`thread_id=email_id`)

**Verification:**
- [ ] `pytest tests/test_graph.py` passes (full graph run with fixture email + mock LLM)
- [ ] Graph handles both paths (high-confidence and low-confidence) in tests

**Dependencies:** Tasks 7, 8

**Files:**
- `backend/app/agent/graph.py`
- `backend/tests/test_graph.py`

**Scope:** M

---

### Checkpoint: Phase 3
- [ ] Full agent graph runs end-to-end with fixture emails
- [ ] Both routing paths (direct notify vs. supervisor interrupt) work in tests
- [ ] `pytest tests/` passes

---

## Phase 4: Human-in-the-Loop

### Task 10: Supervisor interrupt node
**Description:** Node that fires when routing needs review. Uses LangGraph `interrupt()` to pause the graph and stores the pending ticket in the DB for the supervisor.

**Acceptance criteria:**
- [ ] `notify_supervisor` node updates ticket `status` to `pending_supervisor` in DB
- [ ] Calls `interrupt()` — graph pauses here, state persisted by SqliteSaver
- [ ] Supervisor receives an alert email with ticket subject, proposed team, and a link to the supervisor dashboard

**Verification:**
- [ ] `pytest tests/test_graph.py::test_supervisor_interrupt` — graph pauses at interrupt, DB status is `pending_supervisor`

**Dependencies:** Tasks 9, 12 (email notification — implement Task 12 first or stub it)

**Files:**
- `backend/app/agent/nodes.py` (add notify_supervisor)
- `backend/app/agent/graph.py` (add node to graph)
- `backend/tests/test_graph.py` (add test)

**Scope:** M

---

### Task 11: Supervisor API endpoints
**Description:** FastAPI endpoints for the supervisor to approve or override a pending routing decision, which resumes the paused LangGraph graph.

**Acceptance criteria:**
- [ ] `POST /supervisor/approve` — resumes graph with `supervisor_action="approved"`, uses current `assigned_team` as `final_team`
- [ ] `POST /supervisor/override` — accepts `{"team": "HR"}`, resumes graph with `supervisor_action="overridden"`, updates `final_team`
- [ ] Both endpoints update ticket DB record and trigger `send_notifications` node
- [ ] Returns 404 if ticket not found or not in `pending_supervisor` status

**Verification:**
- [ ] `pytest tests/test_routers/test_supervisor.py` passes (httpx TestClient)

**Dependencies:** Tasks 9, 10

**Files:**
- `backend/app/routers/supervisor.py`
- `backend/app/main.py` (register router)
- `backend/tests/test_routers/test_supervisor.py`

**Scope:** M

---

### Checkpoint: Phase 4
- [ ] Low-confidence email → graph pauses → supervisor endpoint resumes → notifications fire
- [ ] `pytest tests/` passes

---

## Phase 5: Notifications

### Task 12: Email notifications
**Description:** SMTP email sender for two cases: (1) team members notified of a new confirmed ticket, (2) supervisor alerted when routing needs review.

**Acceptance criteria:**
- [ ] `send_team_notification(ticket, team_members)` sends email to all members of the assigned team
- [ ] `send_supervisor_alert(ticket, supervisor_email)` sends alert with ticket details + dashboard link
- [ ] Email credentials from `.env` (`GMAIL_USER`, `GMAIL_APP_PASSWORD`)
- [ ] Both functions are no-ops (log only) when `EMAIL_NOTIFICATIONS=false` in `.env` (dev mode)

**Verification:**
- [ ] `pytest tests/test_notifications/test_email.py` passes (mocked SMTP)

**Dependencies:** Task 2

**Files:**
- `backend/app/notifications/email.py`
- `backend/tests/test_notifications/test_email.py`

**Scope:** S

---

### Task 13: SSE broadcaster
**Description:** Server-Sent Events broadcaster that pushes `ticket_routed` events to all connected dashboard clients when a ticket is confirmed routed.

**Acceptance criteria:**
- [ ] `SSEBroadcaster` class with `subscribe()` (returns async generator) and `broadcast(event)` methods
- [ ] `broadcast()` called by `send_notifications` node after routing is confirmed
- [ ] Event payload: `{"type": "ticket_routed", "ticket": {...}}`
- [ ] Handles client disconnects gracefully (no leaked generators)

**Verification:**
- [ ] `pytest tests/test_notifications/test_sse.py` passes

**Dependencies:** Task 1

**Files:**
- `backend/app/notifications/sse.py`
- `backend/tests/test_notifications/test_sse.py`

**Scope:** S

---

## Phase 6: API Layer

### Task 14: Tickets router
**Description:** Read-only FastAPI endpoints for fetching ticket data.

**Acceptance criteria:**
- [ ] `GET /tickets` returns list of all tickets (newest first), paginated (`?skip=0&limit=20`)
- [ ] `GET /tickets/{id}` returns full ticket detail
- [ ] Response schema includes all `Ticket` model fields
- [ ] Returns 404 for unknown ticket ID

**Verification:**
- [ ] `pytest tests/test_routers/test_tickets.py` passes

**Dependencies:** Task 3

**Files:**
- `backend/app/routers/tickets.py`
- `backend/app/main.py` (register router)
- `backend/tests/test_routers/test_tickets.py`

**Scope:** S

---

### Task 15: SSE stream endpoint
**Description:** FastAPI endpoint that streams SSE events to connected clients.

**Acceptance criteria:**
- [ ] `GET /stream` returns `text/event-stream` response
- [ ] Subscribes to `SSEBroadcaster` and forwards events to client
- [ ] Sends a `ping` comment every 15s to keep connection alive
- [ ] Client disconnect detected and subscription cleaned up

**Verification:**
- [ ] `pytest tests/test_routers/test_stream.py` passes
- [ ] Manual test: `curl -N http://localhost:8000/stream` receives ping events

**Dependencies:** Task 13

**Files:**
- `backend/app/routers/stream.py`
- `backend/app/main.py` (register router)
- `backend/tests/test_routers/test_stream.py`

**Scope:** S

---

### Checkpoint: Phase 6
- [ ] All API endpoints return correct responses
- [ ] SSE stream delivers events
- [ ] `pytest tests/` passes with ≥ 80% coverage

---

## Phase 7: Frontend

### Task 16: Next.js project setup
**Description:** Scaffold the Next.js frontend with Tailwind CSS, API client, and SSE hook.

**Acceptance criteria:**
- [ ] `create-next-app` with App Router + TypeScript + Tailwind CSS
- [ ] `lib/api.ts` exports typed fetch functions for `getTickets()`, `getTicket(id)`, `approveRouting(id)`, `overrideRouting(id, team)`
- [ ] `lib/useTicketStream.ts` — React hook that connects to `GET /stream` and returns new ticket events
- [ ] `NEXT_PUBLIC_API_URL` env var used for backend base URL
- [ ] `.env.local.example` documented

**Verification:**
- [ ] `npm run dev` starts without errors
- [ ] `npm run build` succeeds
- [ ] `npm run lint` passes

**Dependencies:** Tasks 14, 15

**Files:**
- `frontend/` (full scaffold)
- `frontend/lib/api.ts`
- `frontend/lib/useTicketStream.ts`

**Scope:** M

---

### Task 17: Dashboard page
**Description:** Main page showing all tickets in real time. New tickets appear instantly via SSE without page refresh.

**Acceptance criteria:**
- [ ] `app/page.tsx` fetches initial ticket list on load
- [ ] `useTicketStream` hook prepends new tickets to list as SSE events arrive (< 3s after routing confirmation)
- [ ] `TicketCard` shows: subject, sender, assigned team (with `TeamBadge`), status, timestamp
- [ ] `TeamBadge` renders team name with a distinct color per team (IT=blue, Support=green, Helpdesk=yellow, HR=purple)
- [ ] Tickets with `status=pending_supervisor` shown with a warning indicator

**Verification:**
- [ ] `npm test -- TicketCard` passes
- [ ] Manual: trigger a test ticket and confirm it appears on dashboard within 3s

**Dependencies:** Task 16

**Files:**
- `frontend/app/page.tsx`
- `frontend/components/TicketCard.tsx`
- `frontend/components/TeamBadge.tsx`

**Scope:** M

---

### Task 18: Ticket detail page
**Description:** Individual ticket view showing full email body, routing decision trail, and evaluator verdict.

**Acceptance criteria:**
- [ ] `app/tickets/[id]/page.tsx` fetches ticket by ID
- [ ] Shows: subject, sender email, full body, assigned team, confidence score, evaluator verdict, supervisor action (if any), final team, timestamps
- [ ] Back navigation to dashboard
- [ ] 404 page for unknown ticket ID

**Verification:**
- [ ] `npm test -- tickets/` passes

**Dependencies:** Task 16

**Files:**
- `frontend/app/tickets/[id]/page.tsx`

**Scope:** S

---

### Task 19: Supervisor review queue
**Description:** Page listing all tickets pending supervisor review, with approve/override controls.

**Acceptance criteria:**
- [ ] `app/supervisor/page.tsx` shows only tickets with `status=pending_supervisor`
- [ ] Each row shows ticket subject, proposed team, confidence score, evaluator verdict
- [ ] "Approve" button calls `POST /supervisor/approve` and removes ticket from queue
- [ ] "Override" opens a `SupervisorModal` with team selector (IT/Support/Helpdesk/HR) and confirm button
- [ ] Optimistic UI update — ticket disappears from queue immediately on action
- [ ] Loading and error states handled

**Verification:**
- [ ] `npm test -- supervisor` passes
- [ ] Manual: approve a pending ticket and confirm it moves to `routed` status on dashboard

**Dependencies:** Tasks 16, 17

**Files:**
- `frontend/app/supervisor/page.tsx`
- `frontend/components/SupervisorModal.tsx`

**Scope:** M

---

### Checkpoint: Phase 7 (Final)
- [ ] End-to-end flow works: email arrives → routed → team sees it on dashboard in < 3s
- [ ] Supervisor flow works: flagged ticket → supervisor approves/overrides → team notified
- [ ] `npm run build` succeeds
- [ ] `pytest tests/` ≥ 80% coverage
- [ ] `npm test` ≥ 70% coverage

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Gmail OAuth2 first-run requires browser flow | Blocks local dev | Document manual auth step; provide `scripts/auth.py` helper |
| LangGraph SqliteSaver + `interrupt()` state corruption | Graph resumes with wrong state | Test interrupt/resume path explicitly in Task 10 |
| SSE connection drops silently in Next.js | Dashboard stops updating | Implement reconnect with exponential backoff in `useTicketStream` |
| Claude returns malformed JSON for routing | Graph crashes | Graceful fallback in classify/evaluate nodes (Task 7/8) |
| Confidence threshold (0.8) too aggressive in early testing | Every ticket goes to supervisor | Make threshold configurable in `config.yaml` (already planned) |

---

## Task Order Summary

```
Phase 1: Tasks 1 → 2 → 3
Phase 2: Tasks 4 → 5
Phase 3: Tasks 6 → 7 → 8 → 9
Phase 4: Tasks 12 (stub) → 10 → 11
Phase 5: Tasks 12 (full) → 13
Phase 6: Tasks 14 → 15
Phase 7: Tasks 16 → 17 → 18 → 19
```

Total: 19 tasks across 7 phases.
