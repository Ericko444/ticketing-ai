# Phase 5 Summary: Notifications

**Date:** 2026-06-09
**Commits:** 68e1b0e (Task 13)
**Tests:** 6 new, 62 total — all passing

## What Was Built

Task 12 (email notifications) was fully implemented in Phase 4. Phase 5 delivered Task 13 only.

### Task 13 — SSE broadcaster (`68e1b0e`)

- `SSEBroadcaster` class in `backend/app/notifications/sse.py`:
  - `set_loop(loop)` — called at app startup to store the main event loop reference
  - `subscribe()` — async generator; each caller gets its own `asyncio.Queue`; `try/finally` removes the queue on disconnect/cancel (no leaked generators)
  - `broadcast(event)` — sync-safe, callable from worker threads; uses `asyncio.run_coroutine_threadsafe(self._put_all(event), self._loop)` to schedule delivery on the main loop
  - `_put_all(event)` — internal coroutine that puts the event into every active queue
- `broadcaster` singleton exported from the module

**Wiring:**
- `_send_notifications_node` in `graph.py` calls `broadcaster.broadcast({...})` inside the DB block, after `db.commit()` and `send_team_notification()`. Payload: `{"type": "ticket_routed", "ticket": {...all Ticket fields...}}`
- `main.py` lifespan calls `broadcaster.set_loop(asyncio.get_running_loop())` at startup
- Graph tests now patch `app.agent.graph.broadcaster` wherever `_send_notifications_node` is reached (high-confidence path + supervisor resume path)

## Files Created / Modified

| File | Change |
|---|---|
| `backend/app/notifications/sse.py` | New — SSEBroadcaster + singleton |
| `backend/tests/test_notifications/test_sse.py` | New — 6 tests |
| `backend/app/agent/graph.py` | Modified — import broadcaster + call broadcast |
| `backend/app/main.py` | Modified — broadcaster.set_loop in lifespan |
| `backend/tests/test_graph.py` | Modified — patch broadcaster in affected tests |

## Decisions Made During Implementation

- `broadcast()` is synchronous because `_send_notifications_node` runs in a thread pool (via `run_in_executor`). `asyncio.run_coroutine_threadsafe` bridges the sync/async boundary.
- Event loop stored via `set_loop()` at startup rather than fetching at call time — fetching `asyncio.get_running_loop()` from a worker thread would raise `RuntimeError` since no loop is running in that thread.
- `try/finally` in `subscribe()` ensures the queue is removed even if the generator is cancelled mid-iteration (client disconnect).

## Phase 6 Preview

Next: Phase 6 adds the two remaining API routers — `GET /tickets` + `GET /tickets/{id}` (Task 14) and `GET /stream` SSE endpoint (Task 15).
