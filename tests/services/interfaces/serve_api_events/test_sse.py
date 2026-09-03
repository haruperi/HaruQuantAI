"""SSE event buffer behavior tests for serve-api-events."""

import pytest
from app.contracts.interfaces.errors import EventCursorExpiredError, InterfaceError
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig
from app.services.interfaces.serve_api_events.sse import EventStreamBuffer


def _buffer(config: ServeApiEventsConfig | None = None) -> EventStreamBuffer:
    """Build an event buffer with optional overrides."""
    return EventStreamBuffer(config or ServeApiEventsConfig())


def _publish(buffer: EventStreamBuffer, count: int) -> list[str]:
    """Publish count events and return their cursor IDs."""
    return [
        buffer.publish("tick", "market", {"index": index}).event_id
        for index in range(count)
    ]


def test_publish_assigns_monotonic_sequences_and_deterministic_ids() -> None:
    """Verify sequence ordering and cursor identity."""
    buffer = _buffer()
    first = buffer.publish("tick", "market", {"symbol": "EURUSD"})
    second = buffer.publish("tick", "market", {"symbol": "GBPUSD"})

    assert first.sequence_number == 1
    assert second.sequence_number == 2
    assert first.event_id == "evt-00000000000000000001"
    assert second.event_id == "evt-00000000000000000002"
    assert first.event_type == "tick"
    assert first.topic == "market"
    assert first.timestamp != ""


def test_publish_copies_payload() -> None:
    """Verify later payload mutation cannot rewrite published events."""
    buffer = _buffer()
    payload: dict[str, object] = {"symbol": "EURUSD"}
    envelope = buffer.publish("tick", "market", payload)
    payload["symbol"] = "MUTATED"
    assert envelope.payload["symbol"] == "EURUSD"


def test_replay_orders_events_and_reports_has_more() -> None:
    """Verify ordered replay batches with batch-limit clamping."""
    buffer = _buffer(ServeApiEventsConfig(stream_replay_batch_limit=2))
    cursors = _publish(buffer, 5)

    batch = buffer.replay(cursors[0], max_events=10)
    assert [event.sequence_number for event in batch.events] == [2, 3]
    assert batch.has_more is True
    assert batch.next_cursor == cursors[2]

    final = buffer.replay(cursors[3], max_events=10)
    assert [event.sequence_number for event in final.events] == [5]
    assert final.has_more is False


def test_replay_none_returns_latest_tail() -> None:
    """Verify cursorless replay returns the latest bounded batch."""
    buffer = _buffer(ServeApiEventsConfig(stream_replay_batch_limit=3))
    _publish(buffer, 5)

    batch = buffer.replay(None)
    assert [event.sequence_number for event in batch.events] == [3, 4, 5]
    assert batch.has_more is False
    assert batch.next_cursor == "evt-00000000000000000005"


def test_replay_empty_buffer_returns_empty_batch() -> None:
    """Verify replay against an empty buffer is well-defined."""
    batch = _buffer().replay(None)
    assert batch.events == ()
    assert batch.next_cursor is None


def test_expired_and_unknown_cursors_raise() -> None:
    """Verify expired, unknown, and invalid cursors require resync."""
    buffer = _buffer()
    _publish(buffer, 3)

    with pytest.raises(EventCursorExpiredError):
        buffer.replay("evt-00000000000000000099")
    with pytest.raises(EventCursorExpiredError):
        buffer.replay("not-a-cursor")


def test_retention_eviction_expires_oldest_cursors() -> None:
    """Verify bounded retention evicts the oldest events."""
    buffer = _buffer(ServeApiEventsConfig(stream_retention_events=3))
    cursors = _publish(buffer, 5)

    with pytest.raises(EventCursorExpiredError):
        buffer.replay(cursors[0])
    batch = buffer.replay(cursors[2])
    assert [event.sequence_number for event in batch.events] == [4, 5]


def test_publish_rejects_oversized_and_malformed_input() -> None:
    """Verify payload bounds and label validation."""
    buffer = _buffer(ServeApiEventsConfig(event_payload_max_bytes=16))
    with pytest.raises(ValueError, match="event_payload_max_bytes"):
        buffer.publish("tick", "market", {"detail": "0123456789abcdefgh"})
    with pytest.raises(ValueError, match="event_type"):
        buffer.publish("", "market", {})
    with pytest.raises(TypeError, match="payload"):
        buffer.publish("tick", "market", "not-a-dict")  # type: ignore[arg-type]


def test_replay_rejects_invalid_batch_size() -> None:
    """Verify non-positive batch sizes fail closed."""
    buffer = _buffer()
    with pytest.raises(ValueError, match="max_events"):
        buffer.replay(None, max_events=0)


def test_closed_buffer_rejects_use() -> None:
    """Verify disposal fails all subsequent operations closed."""
    buffer = _buffer()
    _publish(buffer, 1)
    buffer.close()
    buffer.close()
    with pytest.raises(InterfaceError, match="TRANSPORT_CLOSED"):
        buffer.publish("tick", "market", {})
    with pytest.raises(InterfaceError, match="TRANSPORT_CLOSED"):
        buffer.replay(None)
