"""Bounded event replay, subscription lifecycle, and cross-thread delivery."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from app.core.host.events import CORE_EVENT_CHANNELS, EventBus, HostEvent
from pydantic import ValidationError


def test_event_defaults_and_frozen_envelope():
    event = HostEvent(cursor=1, channel="jobs")
    assert datetime.fromisoformat(event.timestamp).utcoffset().total_seconds() == 0
    assert event.event_type == "update"
    assert event.payload == {}
    with pytest.raises(ValidationError):
        event.cursor = 2
    with pytest.raises(ValidationError):
        HostEvent(cursor=1, channel="jobs", unknown=True)


def test_publish_filters_channels_updates_and_unsubscribes():
    bus = EventBus()
    subscriber, queue, replay, gap = bus.subscribe(["jobs"])
    payload = {"progress": 10}
    first = bus.publish("jobs", "progress", payload, "2026-10-25T00:00:00+00:00")
    payload["progress"] = 20
    assert queue.get_nowait().payload == {"progress": 10}
    assert first.timestamp == "2026-10-25T00:00:00+00:00"
    assert not replay and not gap
    bus.publish("custom")
    assert queue.empty()
    assert bus.update_subscription(subscriber, ["custom"])
    second = bus.publish("custom")
    assert queue.get_nowait() == second
    assert not bus.update_subscription("missing", [])
    bus.unsubscribe(subscriber)
    bus.unsubscribe(subscriber)
    bus.publish("custom")
    assert queue.empty()
    assert set(CORE_EVENT_CHANNELS) | {"custom"} == set(bus.channels)


def test_bounded_replay_gap_and_snapshot_limits():
    bus = EventBus(ring_capacity=3)
    events = [bus.publish("jobs" if i % 2 == 0 else "system") for i in range(5)]
    _, _, replay, gap = bus.subscribe(["jobs"], since_cursor=0)
    assert gap
    assert replay == [events[2], events[4]]
    snapshot = bus.get_snapshot(since_cursor=0, limit=2)
    assert snapshot.has_gap
    assert snapshot.events == events[-2:]
    assert snapshot.newest_cursor == 5
    assert bus.get_snapshot("jobs", since_cursor=2).events == [events[2], events[4]]
    assert bus.get_snapshot(since_cursor=5).events == []
    assert bus.get_snapshot(limit=0).events == [events[-1]]
    assert not bus.subscribe(since_cursor=2)[3]


def test_slow_subscriber_drops_new_events_and_retains_history(caplog):
    bus = EventBus(max_queue_size=1)
    _, queue, _, _ = bus.subscribe()
    first = bus.publish("jobs")
    second = bus.publish("jobs")
    assert queue.get_nowait() == first
    assert queue.empty()
    assert bus.get_snapshot().events == [first, second]
    assert "Dropped cursor=2" in caplog.text


def test_clear_removes_subscribers_and_history_but_preserves_cursor():
    bus = EventBus(ring_capacity=0, max_queue_size=0)
    subscriber, queue, _, _ = bus.subscribe()
    bus.publish("jobs")
    queue.get_nowait()
    bus.clear()
    assert bus.get_snapshot().events == []
    assert not bus.update_subscription(subscriber, ["jobs"])
    assert bus.publish("jobs").cursor == 2
    assert queue.empty()


def test_cross_thread_delivery_runs_on_subscriber_loop_and_bounds_pending():
    async def scenario():
        bus = EventBus(max_queue_size=2)
        subscriber, queue, _, _ = bus.subscribe(["jobs"])
        # Block this loop until the publisher finishes so pending callbacks count
        # against the queue bound, not just events already placed in the queue.
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(lambda: [bus.publish("jobs") for _ in range(5)])
            events = future.result(timeout=2)
        await asyncio.sleep(0)
        assert queue.qsize() == 2
        assert [queue.get_nowait(), queue.get_nowait()] == events[:2]
        bus.publish("jobs")
        bus.unsubscribe(subscriber)
        await asyncio.sleep(0)
        assert queue.empty()

    asyncio.run(scenario())


def test_concurrent_publishers_produce_unique_ordered_cursors():
    bus = EventBus(ring_capacity=100)
    with ThreadPoolExecutor(max_workers=4) as pool:
        events = list(pool.map(lambda _: bus.publish("jobs"), range(100)))
    assert sorted(event.cursor for event in events) == list(range(1, 101))
    assert [event.cursor for event in bus.get_snapshot().events] == list(range(1, 101))
