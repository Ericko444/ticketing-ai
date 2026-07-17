# Implementation Plan: Department Authentication

## Overview

The dashboard is currently unauthenticated — anyone who can reach the Next.js app sees every team's tickets and can act as the supervisor. This is the top item on the roadmap (`README.md`) and is confirmed via [`docs/intent/department-auth.md`](intent/department-auth.md) (interviewed 2026-07-16). Email+password login gates the app; a new `users` table (email, password hash, team, role) replaces `config.yaml`'s member list as the source of team membership. Team members only see their own team's tickets — enforced server-side, not cosmetically. The supervisor logs in through the same system but is unscoped. Session is an HTTP-only cookie, chosen because `EventSource` can't send `Authorization` headers but does send cookies automatically — this avoids a token-in-query-string workaround for `/stream`. Accounts are provisioned once via a seed script — no admin UI, no self-registration, no password reset in v1. 12 tasks across 5 phases.

## Architecture Decisions

- **Password hashing** — `bcrypt` added to `backend/requirements.txt`; new `backend/app/auth/security.py` (`hash_password`/`verify_password`).
- **Stateless signed session cookie, no sessions table** — `itsdangerous.URLSafeTimedSerializer` signs `{user_id, exp}` into the cookie value. New `SESSION_SECRET` / `SESSION_COOKIE_SECURE` env vars, following the existing `EMAIL_BACKEND`-style env-driven config pattern in `backend/app/config.py`.
- **`users` table replaces `config.yaml` membership** — `id, email (unique), password_hash, role ("member"|"supervisor"), team (nullable, null for supervisor)`. `config.yaml`'s `teams:` becomes a flat name list (metadata only); all `members:` lists are deleted. `supervisor.email` stays in `config.yaml` (it's the notification-recipient address, independent of login credentials). `TeamConfig` / `Settings.members_for_team` are removed.
- **Frontend enforcement is client-side, not `proxy.ts`** — this app's frontend is 100% client components (`"use client"`) fetching a separate-origin FastAPI backend; there's no server-rendered data to protect. Next.js 16 also deprecated `middleware.ts` in favor of `proxy.ts` (confirmed in `frontend/node_modules/next/dist/docs/.../proxy.md` — `frontend/AGENTS.md`'s breaking-changes warning is real here). Relying on `proxy.ts` to read the backend's cookie would only work in dev, because browser cookie-matching ignores port (a cookie set by `localhost:8000` happens to also be sent to `localhost:3000`) — that breaks under any real deployment where frontend and backend aren't on the exact same hostname. Instead, a small `AuthContext` calls `GET /auth/me` on mount (`credentials: "include"`) and redirects unauthenticated users to `/login`. The real security boundary is server-side on FastAPI, per the intent doc's success criteria; the frontend check is UX only.
- **Cross-origin credentials** — every `frontend/lib/api.ts` call needs `credentials: "include"`; `EventSource` needs `{ withCredentials: true }` (default `false`, would silently drop the cookie cross-origin).
- **`/stream` is team-filtered, not just auth-gated** (confirmed with user) — `SSEBroadcaster` tracks each subscriber's team (`None` = supervisor/all) and only enqueues matching `ticket_routed` events.
- **Seed script uses one shared default password** for all provisioned accounts, documented in the README — consistent with the intent's "no reset flow, admin re-runs the seed script" recovery model, and keeps Playwright e2e credentials deterministic.

---

## Dependency Graph

```
users table + password hashing + trimmed config.yaml
        │
        ├── seed script (provisions users)
        │
        ▼
signed session cookie (itsdangerous)
        │
        ▼
/auth/login, /auth/logout, /auth/me + get_current_user dependency
        │
        ├── GET /tickets, GET /tickets/{id} — team-filtered
        ├── /supervisor/approve, /supervisor/override — role-gated
        ├── /stream (SSE) — auth + team-filtered
        │       │
        │       └── graph.py notification lookup switches config.yaml → users table
        │
        ▼
Frontend: login page + AuthContext (calls /auth/me)
        │
        ├── Gate dashboard / supervisor / ticket-detail pages, nav, logout, EventSource credentials
        │
        ▼
Playwright e2e login flow + updated specs
        │
        ▼
Docs (README roadmap, env vars, phase summary)
```

---

## Phase 1: Backend Foundation

### Task 1: `users` table, password hashing, trimmed `config.yaml`
**Description:** Add the `User` model, a password hashing utility, and trim `config.yaml`/`config.py` down to team metadata now that membership lives in the DB.

**Acceptance criteria:**
- [ ] `User` model (id, email unique, password_hash, role, team nullable) added to `backend/app/db/models.py`; creates via `create_tables()`
- [ ] `backend/app/auth/security.py` exposes `hash_password`/`verify_password` that round-trip correctly
- [ ] `config.yaml`'s `teams:` is a flat name list; all `members:` keys removed; `supervisor.email` unchanged
- [ ] `TeamConfig` and `Settings.members_for_team` removed from `backend/app/config.py`

**Verification:**
- [ ] `pytest backend/tests/test_config.py backend/tests/test_db.py -v`

**Dependencies:** None

**Files:**
- `backend/app/db/models.py`
- `backend/app/auth/security.py`
- `backend/app/config.py`
- `config.yaml`
- `backend/requirements.txt`
- `backend/tests/test_config.py`, `backend/tests/test_db.py`

---

### Task 2: Seed script
**Description:** One-time script that migrates the current `config.yaml` roster (captured before Task 1 trims it) into `users`, assigning the shared default password. Idempotent by email so it doubles as the recovery path.

**Acceptance criteria:**
- [ ] `python -m backend.scripts.seed_users` creates one row per roster member (role="member", team set) plus one supervisor row (role="supervisor", team=null)
- [ ] Re-running does not create duplicates or error

**Verification:**
- [ ] `pytest backend/tests/test_seed_users.py -v`
- [ ] Manual: run against a fresh `ticketing.db`, inspect via `sqlite3`

**Dependencies:** Task 1

**Files:**
- `backend/scripts/seed_users.py`
- `backend/tests/test_seed_users.py`

---

### Checkpoint: Backend Foundation
- [ ] `pytest backend/tests -v` green
- [ ] Seed script produces expected rows on a fresh DB

---

## Phase 2: Session + Login Endpoints

### Task 3: Signed session cookie
**Description:** Stateless cookie signing/verification using `itsdangerous`, with a new `SESSION_SECRET` env var.

**Acceptance criteria:**
- [ ] `create_session_cookie(user_id)` / `read_session_cookie(token)` round-trip
- [ ] Expired or tampered token returns `None`

**Verification:**
- [ ] `pytest backend/tests/test_auth_session.py -v`

**Dependencies:** Task 1

**Files:**
- `backend/app/auth/session.py`
- `backend/app/config.py`, `backend/.env.example`, `backend/requirements.txt`
- `backend/tests/test_auth_session.py`

---

### Task 4: `/auth` router + `get_current_user` dependency
**Description:** Login, logout, and "who am I" endpoints, plus the FastAPI dependency other routers will use for enforcement.

**Acceptance criteria:**
- [ ] `POST /auth/login` sets an HTTP-only cookie on valid credentials, 401 on invalid
- [ ] `GET /auth/me` returns `{email, role, team}` with a valid cookie, 401 without
- [ ] `POST /auth/logout` clears the cookie
- [ ] `get_current_user` (401 if missing/invalid) and `require_supervisor` (403 if not supervisor) dependencies exist in `backend/app/auth/dependencies.py`

**Verification:**
- [ ] `pytest backend/tests/test_routers/test_auth.py -v`

**Dependencies:** Task 1, Task 3

**Files:**
- `backend/app/routers/auth.py`
- `backend/app/auth/dependencies.py`
- `backend/app/main.py`
- `backend/tests/test_routers/test_auth.py`

---

### Checkpoint: Session + Login
- [ ] Full round-trip via `TestClient`: login → cookie → `/auth/me` → logout → `/auth/me` 401

---

## Phase 3: Server-Side Enforcement

### Task 5: Team-scope `GET /tickets`, `GET /tickets/{id}`
**Description:** The core success criterion from the intent doc — ticket endpoints filter/reject by the logged-in user's team.

**Acceptance criteria:**
- [ ] List endpoint returns only the current user's team's tickets (supervisor sees all)
- [ ] Detail endpoint 404s for a ticket outside the user's team (not 403 — avoids confirming existence)
- [ ] Unauthenticated requests to either endpoint → 401

**Verification:**
- [ ] `pytest backend/tests/test_routers/test_tickets.py -v`

**Dependencies:** Task 4

**Files:**
- `backend/app/routers/tickets.py`
- `backend/tests/test_routers/test_tickets.py`

---

### Task 6: Role-gate `/supervisor/approve`, `/supervisor/override`
**Description:** Restrict supervisor actions to `role == "supervisor"`.

**Acceptance criteria:**
- [ ] Authenticated non-supervisor → 403
- [ ] Unauthenticated → 401
- [ ] Supervisor behavior unchanged

**Verification:**
- [ ] `pytest backend/tests/test_routers/test_supervisor.py -v`

**Dependencies:** Task 4

**Files:**
- `backend/app/routers/supervisor.py`
- `backend/tests/test_routers/test_supervisor.py`

---

### Task 7: Team-scope `/stream` (SSE)
**Description:** Real-time updates respect the same team boundary as the REST endpoints (confirmed with user — not just auth-gated).

**Acceptance criteria:**
- [ ] `SSEBroadcaster` tracks each subscriber's team; `None` (supervisor) receives everything
- [ ] A subscriber only receives `ticket_routed` events where `final_team` matches their team
- [ ] Unauthenticated connection attempts are rejected

**Verification:**
- [ ] `pytest backend/tests/test_routers/test_stream.py backend/tests/test_notifications/test_sse.py -v`

**Dependencies:** Task 4

**Files:**
- `backend/app/notifications/sse.py`
- `backend/app/routers/stream.py`
- `backend/tests/test_routers/test_stream.py`, `backend/tests/test_notifications/test_sse.py`

---

### Task 8: Team notification emails read from `users` table
**Description:** `_send_notifications_node` (`backend/app/agent/graph.py`) currently calls `settings.members_for_team()`, removed in Task 1. Switch to querying `User` by team.

**Acceptance criteria:**
- [ ] Notification recipients for a routed ticket match the seeded `users` rows for that team

**Verification:**
- [ ] `pytest backend/tests/test_graph.py -v`

**Dependencies:** Task 1, Task 2

**Files:**
- `backend/app/agent/graph.py`
- `backend/tests/test_graph.py`

---

### Checkpoint: Server-Side Enforcement
- [ ] `pytest backend/tests/ -v --cov=app` green
- [ ] Manual `curl`: IT cookie can't read/act on a Support ticket (404/403); supervisor cookie can

---

## Phase 4: Frontend

### Task 9: Login page + auth client
**Description:** Login form and a shared auth client/context, following the existing `fetch`-based style in `frontend/lib/api.ts`.

**Acceptance criteria:**
- [ ] `frontend/lib/auth.ts`: `login`, `logout`, `getMe` — all with `credentials: "include"`
- [ ] Every existing call in `frontend/lib/api.ts` adds `credentials: "include"`
- [ ] `frontend/app/login/page.tsx`: valid login redirects to `/`; invalid login shows inline error and stays on `/login`
- [ ] `AuthContext`/`useAuth` exposes `{ user, loading }` via one `getMe()` call

**Verification:**
- [ ] `npm test -- login`

**Dependencies:** Task 4

**Files:**
- `frontend/lib/auth.ts`, `frontend/lib/api.ts`, `frontend/lib/AuthContext.tsx`
- `frontend/app/login/page.tsx`
- `frontend/__tests__/login/LoginPage.test.tsx`

---

### Task 10: Gate pages, nav, logout, SSE credentials
**Description:** Wire the auth context into the app shell: redirect unauthenticated visitors, show current user + logout, hide supervisor-only nav, fix cross-origin SSE.

**Acceptance criteria:**
- [ ] Unauthenticated visits to `/`, `/supervisor`, `/tickets/:id` redirect to `/login`
- [ ] Header shows current user's email/team and a logout button
- [ ] "Supervisor Queue" nav link hidden when `role !== "supervisor"`
- [ ] `useTicketStream.ts` uses `new EventSource(url, { withCredentials: true })`
- [ ] Existing Jest tests for dashboard/supervisor/ticket-detail updated to mock an authenticated context

**Verification:**
- [ ] `cd frontend && npm test`

**Dependencies:** Task 9

**Files:**
- `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `frontend/app/supervisor/page.tsx`, `frontend/components/TicketDetail.tsx`
- `frontend/lib/useTicketStream.ts`
- `frontend/__tests__/TicketCard.test.tsx`, `__tests__/supervisor/SupervisorPage.test.tsx`, `__tests__/tickets/TicketDetailPage.test.tsx`

---

### Checkpoint: Frontend
- [ ] `npm test` green
- [ ] Manual browser pass: logged out → redirected to `/login`; IT member sees only IT tickets, no Supervisor Queue link; supervisor sees everything

---

## Phase 5: E2E + Docs

### Task 11: Update Playwright suite for auth
**Description:** Existing specs assume unauthenticated access and will break once pages are gated; add a login helper and seed the e2e DB.

**Acceptance criteria:**
- [ ] `e2e/helpers/auth.ts` (`loginAs`) using seeded default credentials
- [ ] `e2e/globalSetup.ts` seeds users after clearing tables
- [ ] `dashboard.spec.ts`, `supervisor.spec.ts`, `ticket-detail.spec.ts` log in before navigating
- [ ] New `login.spec.ts`: valid/invalid login, logout, team-scoping (IT member doesn't see a Support ticket)

**Verification:**
- [ ] `cd e2e && npx playwright test`

**Dependencies:** Phase 4 complete

**Files:**
- `e2e/helpers/auth.ts`, `e2e/globalSetup.ts`
- `e2e/tests/dashboard.spec.ts`, `e2e/tests/supervisor.spec.ts`, `e2e/tests/ticket-detail.spec.ts`, `e2e/tests/login.spec.ts`

---

### Task 12: Docs
**Description:** Reflect the shipped feature in project docs.

**Acceptance criteria:**
- [ ] `README.md` roadmap moves "Department authentication" to Done
- [ ] `docs/spec.md` documents `SESSION_SECRET`/`SESSION_COOKIE_SECURE` and the seed script
- [ ] `backend/.env.example` includes the new session env vars
- [ ] `docs/summaries/phase-N.md` written once implementation lands (per repo convention)

**Dependencies:** All prior tasks

**Files:**
- `README.md`, `docs/spec.md`, `backend/.env.example`, `docs/summaries/phase-N.md`

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Cross-origin cookie only works in dev because port isn't part of cookie-domain matching | Medium — breaks under a real multi-domain deployment | Documented as a known v1 limitation; deployment topology is out of scope of the intent doc |
| Shared default seed password | Low (no external users, no self-registration) | Documented in README; matches intent's "no reset flow, admin re-runs seed script" model |
| Existing Jest/Playwright suites assume unauthenticated access | High if missed — breaks all existing UI tests | Tasks 10/11 explicitly update every spec/test file that hits a now-gated page |
| SSE per-subscriber team filtering adds state to `SSEBroadcaster` | Low — small, isolated change | Scoped to Task 7 only; `broadcast()` call sites in `graph.py` don't change |

## Open Questions

None outstanding — SSE team-filtering scope was confirmed with the user during planning (filter by team, not just auth-gate).
