import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import create_tables


async def _noop_handler(email_data: dict) -> None:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    from app.gmail.client import GmailClient
    from app.gmail.poller import start_poller
    gmail = GmailClient()
    poller_task = asyncio.create_task(start_poller(gmail, _noop_handler))
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
