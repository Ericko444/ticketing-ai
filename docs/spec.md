# Spec: AI-Powered Email Ticketing System

## Objective

Build a LangGraph-based system that ingests incoming support emails via Gmail API, classifies them, and routes each ticket to the correct team (IT, Support, Helpdesk, HR). A routing evaluator node checks correctness before notifications fire. If the evaluator flags a low-confidence or incorrect routing, the graph pauses and alerts a supervisor (human-in-the-loop) to approve or override. Once routing is confirmed, team members are notified via email and can view new tickets in a real-time in-app dashboard.

**Users:**
- **Consumers** — send support emails to a shared Gmail inbox
- **Team members** — IT, Support, Helpdesk, HR staff who receive and action tickets
- **Supervisor** — reviews flagged routing decisions before they are finalized

**Success criteria:**
- Emails are automatically routed to the correct team without manual intervention
- Routing evaluator catches mis-routes before the team is notified
- Supervisor receives an alert and can approve/override routing via the dashboard
- Team members see new tickets in real time (< 3s from routing confirmation to dashboard update)
- All notifications sent within 30s of a ticket being confirmed routed

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph (Python) |
| LLM | Claude claude-sonnet-4-6 (Anthropic) |
| Email ingestion | Gmail API (OAuth2) |
| Email notifications | Gmail SMTP (smtplib) |
| Backend API | FastAPI |
| Real-time push | Server-Sent Events (SSE) |
| Frontend | Next.js (App Router) |
| Persistence | SQLite + LangGraph SqliteSaver checkpointer |
| Environment | Python 3.11+, Node.js 18+ |

---

## Commands

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000            # Dev server

# Run agent (standalone)
python -m app.agent.graph

# Frontend
cd frontend
npm install
npm run dev       # Dev server on http://localhost:3000
npm run build     # Production build
npm run lint      # ESLint

# Tests
cd backend
pytest tests/ -v --cov=app

cd frontend
npm test
```

---

## Project Structure

```
ticketing-ai/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── config.py             # Settings (env vars, team config)
│   │   ├── agent/
│   │   │   ├── graph.py          # LangGraph graph definition
│   │   │   ├── nodes.py          # Individual node functions
│   │   │   ├── state.py          # AgentState TypedDict
│   │   │   └── prompts.py        # LLM prompt templates
│   │   ├── gmail/
│   │   │   ├── client.py         # Gmail API client (OAuth2)
│   │   │   └── poller.py         # Email polling loop
│   │   ├── notifications/
│   │   │   ├── email.py          # SMTP email sender
│   │   │   └── sse.py            # SSE event broadcaster
│   │   ├── db/
│   │   │   ├── models.py         # SQLite models (tickets, teams)
│   │   │   └── session.py        # DB session
│   │   └── routers/
│   │       ├── tickets.py        # GET /tickets, GET /tickets/{id}
│   │       ├── supervisor.py     # POST /supervisor/approve, /override
│   │       └── stream.py         # GET /stream (SSE endpoint)
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx              # Dashboard (ticket list)
│   │   ├── tickets/[id]/page.tsx # Ticket detail
│   │   └── supervisor/page.tsx   # Supervisor review queue
│   ├── components/
│   │   ├── TicketCard.tsx
│   │   ├── TeamBadge.tsx
│   │   └── SupervisorModal.tsx
│   ├── lib/
│   │   └── api.ts                # API client + SSE hook
│   ├── package.json
│   └── .env.local.example
└── docs/
    └── spec.md                   # This file
```

---

## Code Style

**Python — agent node example:**

```python
from app.agent.state import AgentState

def route_ticket(state: AgentState) -> AgentState:
    response = llm.invoke(ROUTING_PROMPT.format(subject=state["subject"], body=state["body"]))
    return {**state, "assigned_team": response.content.strip(), "routing_confidence": response.usage.confidence}
```

- Snake_case for Python identifiers
- TypedDict for all LangGraph state shapes
- No inline comments unless a constraint is non-obvious
- All prompts in `prompts.py`, never inline in node functions

**TypeScript — component example:**

```tsx
export function TicketCard({ ticket }: { ticket: Ticket }) {
  return (
    <div className="rounded border p-4">
      <TeamBadge team={ticket.assignedTeam} />
      <p className="text-sm text-gray-600">{ticket.subject}</p>
    </div>
  );
}
```

- PascalCase for components, camelCase for everything else
- Props typed inline for simple components, separate interface for complex
- Tailwind CSS for styling

---

## LangGraph Agent Flow

```
[Gmail Poller] → ingest_email
                      ↓
               classify_ticket          (LLM: assigns team + confidence score)
                      ↓
               evaluate_routing         (LLM: checks if classification is correct)
                      ↓
            ┌─── confidence < 0.8? ───┐
            │                         │
     notify_supervisor          send_notifications
     [interrupt() — wait]             ↓
            │                   [done]
     supervisor approves
     or overrides
            ↓
     send_notifications
            ↓
          [done]
```

**State shape:**
```python
class AgentState(TypedDict):
    email_id: str
    subject: str
    body: str
    sender: str
    assigned_team: str          # "IT" | "Support" | "Helpdesk" | "HR"
    routing_confidence: float   # 0.0 – 1.0
    evaluator_verdict: str      # "correct" | "uncertain" | "incorrect"
    supervisor_action: str      # "approved" | "overridden" | ""
    final_team: str
    ticket_id: str
```

---

## Testing Strategy

- **Framework:** pytest (backend), Jest + React Testing Library (frontend)
- **Unit tests:** Each LangGraph node function tested in isolation with mock LLM responses
- **Integration tests:** Full graph run against a fixture email corpus (no real Gmail API calls)
- **API tests:** FastAPI endpoints tested with httpx TestClient
- **Frontend tests:** Component rendering + SSE hook behavior
- **Coverage target:** ≥ 80% backend, ≥ 70% frontend
- **No mocking the LLM in integration tests** — use deterministic fixture responses via dependency injection

---

## Boundaries

**Always:**
- Validate all incoming email data before passing to the agent
- Run pytest before committing backend changes
- Keep all secrets in `.env` files, never hardcoded
- Log routing decisions and evaluator verdicts to the database

**Ask first:**
- Adding new team categories beyond IT/Support/Helpdesk/HR
- Changing the confidence threshold (currently 0.8)
- Switching LLM provider or model
- Adding a new Gmail scope to the OAuth consent screen

**Never:**
- Commit `.env` files or `credentials.json`
- Auto-reply to the consumer (out of scope)
- Modify ticket content after it's been stored
- Skip the evaluator node (even in dev mode)

---

## Decisions

1. **Team member registry** — Config file (`config.yaml`) for v1. Admin UI to manage members is a future enhancement.
2. **Email polling interval** — Every 30 seconds via a background polling loop. Gmail Push Notifications (Pub/Sub) is a future enhancement for true real-time ingestion.
3. **Supervisor identity** — One global supervisor email address defined in config. Per-team supervisors are a future enhancement.
4. **Ticket deduplication** — Flag duplicate email IDs: log a warning and skip processing, storing the duplicate attempt in the DB for visibility.
