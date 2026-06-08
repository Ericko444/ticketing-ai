import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import create_tables


async def _run_graph(email_data: dict) -> None:
    from app.agent.graph import get_graph
    from app.agent.state import AgentState
    graph = get_graph()
    state: AgentState = {
        "email_id": email_data["email_id"],
        "subject": email_data["subject"],
        "body": email_data["body"],
        "sender": email_data["sender"],
        "ticket_id": email_data["ticket_id"],
        "assigned_team": "",
        "routing_confidence": 0.0,
        "evaluator_verdict": "",
        "supervisor_action": "",
        "final_team": "",
    }
    config = {"configurable": {"thread_id": email_data["ticket_id"]}}
    await asyncio.get_event_loop().run_in_executor(None, graph.invoke, state, config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    from app.gmail.client import GmailClient
    from app.gmail.poller import start_poller
    gmail = GmailClient()
    poller_task = asyncio.create_task(start_poller(gmail, _run_graph))
    yield
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Ticketing AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
