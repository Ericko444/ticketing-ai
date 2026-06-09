import asyncio

import pytest

from app.notifications.sse import SSEBroadcaster


# ── Delivery ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_broadcast_delivered_to_subscriber():
    b = SSEBroadcaster()
    b.set_loop(asyncio.get_running_loop())

    received = []

    async def collect_one():
        async for event in b.subscribe():
            received.append(event)
            break

    task = asyncio.create_task(collect_one())
    await asyncio.sleep(0)  # let subscriber register

    b.broadcast({"type": "ticket_routed", "ticket": {"id": "t1"}})
    await asyncio.sleep(0.05)

    await task
    assert len(received) == 1
    assert received[0]["type"] == "ticket_routed"
    assert received[0]["ticket"]["id"] == "t1"


@pytest.mark.asyncio
async def test_all_subscribers_receive_broadcast():
    b = SSEBroadcaster()
    b.set_loop(asyncio.get_running_loop())

    got_a: list[dict] = []
    got_b: list[dict] = []

    async def sub(store: list):
        async for e in b.subscribe():
            store.append(e)
            break

    t1 = asyncio.create_task(sub(got_a))
    t2 = asyncio.create_task(sub(got_b))
    await asyncio.sleep(0)

    b.broadcast({"type": "ticket_routed", "ticket": {"id": "t2"}})
    await asyncio.sleep(0.05)

    await t1
    await t2

    assert len(got_a) == 1
    assert len(got_b) == 1
    assert got_a[0]["ticket"]["id"] == "t2"


# ── No-op cases ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_broadcast_no_subscribers_is_no_op():
    b = SSEBroadcaster()
    b.set_loop(asyncio.get_running_loop())
    b.broadcast({"type": "ticket_routed", "ticket": {}})  # should not raise


def test_broadcast_without_loop_is_no_op(caplog):
    import logging
    b = SSEBroadcaster()
    # set_loop never called — should log a warning, not raise
    with caplog.at_level(logging.WARNING):
        b.broadcast({"type": "ticket_routed", "ticket": {}})
    # no subscribers so early-return path is hit; nothing to assert beyond no exception


# ── Client disconnect / cleanup ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_subscriber_removed_after_cancel():
    b = SSEBroadcaster()
    b.set_loop(asyncio.get_running_loop())

    async def infinite_sub():
        async for _ in b.subscribe():
            pass  # never breaks — runs until cancelled

    task = asyncio.create_task(infinite_sub())
    await asyncio.sleep(0)
    assert len(b._queues) == 1

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert len(b._queues) == 0


@pytest.mark.asyncio
async def test_multiple_subscribers_independent_cleanup():
    b = SSEBroadcaster()
    b.set_loop(asyncio.get_running_loop())

    async def infinite_sub():
        async for _ in b.subscribe():
            pass

    t1 = asyncio.create_task(infinite_sub())
    t2 = asyncio.create_task(infinite_sub())
    await asyncio.sleep(0)
    assert len(b._queues) == 2

    t1.cancel()
    try:
        await t1
    except asyncio.CancelledError:
        pass

    assert len(b._queues) == 1

    t2.cancel()
    try:
        await t2
    except asyncio.CancelledError:
        pass

    assert len(b._queues) == 0
