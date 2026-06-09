import asyncio

import pytest

from app.notifications.sse import SSEBroadcaster
from app.routers.stream import _event_stream, router


# ── HTTP endpoint ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stream_endpoint_returns_event_stream_response():
    import app.routers.stream as stream_mod
    from fastapi.responses import StreamingResponse

    # Call the endpoint function directly — the async generator is created but
    # not iterated, so no queue is registered and the test completes instantly.
    response = await stream_mod.stream()

    assert isinstance(response, StreamingResponse)
    assert response.media_type == "text/event-stream"
    assert response.headers.get("cache-control") == "no-cache"


# ── Generator behaviour ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ping_sent_after_timeout():
    import app.routers.stream as stream_mod

    gen = stream_mod._event_stream(ping_interval=0.01)
    result = await gen.__anext__()
    await gen.aclose()

    assert result == ": ping\n\n"


@pytest.mark.asyncio
async def test_event_forwarded_to_stream():
    import app.routers.stream as stream_mod

    b = SSEBroadcaster()
    b.set_loop(asyncio.get_running_loop())

    original = stream_mod.broadcaster
    stream_mod.broadcaster = b
    try:
        gen = stream_mod._event_stream(ping_interval=5)
        task = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(0)  # let generator register its queue

        b.broadcast({"type": "ticket_routed", "ticket": {"id": "t42"}})
        await asyncio.sleep(0.05)

        result = await task
        await gen.aclose()
    finally:
        stream_mod.broadcaster = original

    assert result.startswith("data: ")
    assert "ticket_routed" in result
    assert "t42" in result


@pytest.mark.asyncio
async def test_queue_removed_after_close():
    import app.routers.stream as stream_mod

    b = SSEBroadcaster()
    b.set_loop(asyncio.get_running_loop())

    original = stream_mod.broadcaster
    stream_mod.broadcaster = b
    try:
        gen = stream_mod._event_stream(ping_interval=0.01)
        await gen.__anext__()  # receives a ping — queue is registered at this point
        assert len(b._queues) == 1

        await gen.aclose()
        assert len(b._queues) == 0
    finally:
        stream_mod.broadcaster = original


@pytest.mark.asyncio
async def test_multiple_clients_each_receive_event():
    import app.routers.stream as stream_mod

    b = SSEBroadcaster()
    b.set_loop(asyncio.get_running_loop())

    original = stream_mod.broadcaster
    stream_mod.broadcaster = b
    try:
        gen1 = stream_mod._event_stream(ping_interval=5)
        gen2 = stream_mod._event_stream(ping_interval=5)

        t1 = asyncio.create_task(gen1.__anext__())
        t2 = asyncio.create_task(gen2.__anext__())
        await asyncio.sleep(0)

        b.broadcast({"type": "ticket_routed", "ticket": {"id": "multi"}})
        await asyncio.sleep(0.05)

        r1 = await t1
        r2 = await t2
        await gen1.aclose()
        await gen2.aclose()
    finally:
        stream_mod.broadcaster = original

    assert "multi" in r1
    assert "multi" in r2
