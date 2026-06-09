import asyncio
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class SSEBroadcaster:
    def __init__(self):
        self._queues: list[asyncio.Queue] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def subscribe(self) -> AsyncGenerator[dict, None]:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.append(q)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            if q in self._queues:
                self._queues.remove(q)

    def broadcast(self, event: dict) -> None:
        """Sync-safe broadcast, callable from worker threads."""
        if not self._queues:
            return
        if self._loop is None or self._loop.is_closed():
            logger.warning("SSE broadcast skipped — no event loop configured")
            return
        asyncio.run_coroutine_threadsafe(self._put_all(event), self._loop)

    async def _put_all(self, event: dict) -> None:
        for q in list(self._queues):
            await q.put(event)


broadcaster = SSEBroadcaster()
