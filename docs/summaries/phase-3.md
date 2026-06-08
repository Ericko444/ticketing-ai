# Phase 3 Summary: LangGraph Agent Core

**Date:** 2026-06-08
**Commits:** f9722ef (Task 6), bf3e27a (Tasks 7+8), d3ceb14 (Task 9), 92cb38c (graph wiring)
**Tests:** 19 new, 40 total — all passing

## What Was Built

### Task 6 — AgentState + prompts (`f9722ef`)
- `AgentState` TypedDict in `backend/app/agent/state.py` — all 9 fields matching the spec
- `CLASSIFY_PROMPT` — instructs Claude to return `{"team": "...", "confidence": 0.0-1.0}` JSON
- `EVALUATE_PROMPT` — instructs Claude to return `{"verdict": "correct|uncertain|incorrect"}` JSON

### Tasks 7 & 8 — classify_ticket + evaluate_routing nodes (`bf3e27a`)
- `classify_ticket(state)` — calls `claude-sonnet-4-6` with CLASSIFY_PROMPT, parses JSON response, zeroes confidence on unknown team or parse error
- `evaluate_routing(state)` — calls `claude-sonnet-4-6` with EVALUATE_PROMPT, defaults to `"uncertain"` on bad verdict or parse error
- `_parse_json()` — extracts JSON from LLM response even when surrounded by prose
- Both nodes are pure functions: take state → return updated state, no side effects

### Task 9 — Graph assembly (`d3ceb14`)
- `build_graph(checkpointer)` — compiles the full LangGraph with:
  - `classify_ticket → evaluate_routing → conditional edge`
  - Conditional: `confidence < 0.8 OR verdict != "correct"` → `notify_supervisor`, else → `send_notifications`
  - `_notify_supervisor_node` — updates DB to `pending_supervisor`, calls `interrupt()` to pause graph and wait for supervisor input
  - `_send_notifications_node` — updates DB to `routed` with `final_team`
- `SqliteSaver` checkpointer persists graph state to `ticketing.db` so `interrupt()`/resume works across HTTP requests
- `get_graph()` — singleton accessor used by the app

### Graph wiring (`92cb38c`)
- `main.py` lifespan now passes `_run_graph()` as the poller's `on_new_email` callback
- Each new email triggers `graph.invoke()` in a thread pool executor (LangGraph is synchronous)

## Files Created / Modified

| File | Change |
|---|---|
| `backend/app/agent/state.py` | New — AgentState TypedDict |
| `backend/app/agent/prompts.py` | New — CLASSIFY_PROMPT, EVALUATE_PROMPT |
| `backend/app/agent/nodes.py` | New — classify_ticket, evaluate_routing |
| `backend/app/agent/graph.py` | New — build_graph, get_graph, node functions |
| `backend/app/main.py` | Modified — poller wired to _run_graph |
| `backend/requirements.txt` | Modified — added langgraph-checkpoint-sqlite |
| `backend/tests/test_prompts.py` | New — 5 tests |
| `backend/tests/test_nodes.py` | New — 10 tests |
| `backend/tests/test_graph.py` | New — 4 tests |

## Decisions Made During Implementation

- `langgraph-checkpoint-sqlite` is a separate package in LangGraph v1+ — added to requirements
- `SessionLocal` imported at module level in `graph.py` (not inside functions) so tests can patch `app.agent.graph.SessionLocal`
- `interrupt()` used inside `_notify_supervisor_node` rather than `interrupt_before` on compile — single pause point, cleaner resume logic
- Graph runs synchronously; wrapped in `run_in_executor` in the async lifespan handler

## Phase 4 Preview

Next: supervisor interrupt already works in the graph — Phase 4 adds the FastAPI endpoints (`/supervisor/approve`, `/supervisor/override`) that resume the paused graph, plus email notifications.
