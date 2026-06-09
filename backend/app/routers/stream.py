import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.notifications.sse import broadcaster

router = APIRouter(tags=["stream"])

PING_INTERVAL = 15


@router.get("/stream")
async def stream():
    return StreamingResponse(
        _event_stream(PING_INTERVAL),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _event_stream(ping_interval: float = PING_INTERVAL):
    q: asyncio.Queue = asyncio.Queue()
    broadcaster._queues.append(q)
    try:
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=ping_interval)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield ": ping\n\n"
    finally:
        if q in broadcaster._queues:
            broadcaster._queues.remove(q)
