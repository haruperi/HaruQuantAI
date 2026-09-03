"""Bounded SSE event buffer with monotonic replay cursors.

Purpose:
    Own the ordered in-memory event envelope buffer, monotonic sequence
    assignment, bounded retention, and cursor-based replay semantics for
    the SSE side of the serve-api-events transport.

Key capabilities:
    * Assign deterministic event IDs from a monotonic sequence.
    * Enforce bounded retention and per-batch replay limits.
    * Raise EventCursorExpiredError for expired or unknown cursors so
      consumers resync instead of assuming continuity.

Python API usage:
    buffer = EventStreamBuffer(ServeApiEventsConfig())
    envelope = buffer.publish("tick", "market", {"symbol": "EURUSD"})
    batch = buffer.replay(envelope.event_id, max_events=10)

CLI usage:
    uv run python -m app.services.interfaces.serve_api_events.transport
"""

from __future__ import annotations

import json
from collections import deque
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.contracts.interfaces.errors import EventCursorExpiredError, InterfaceError
from app.contracts.interfaces.models import (
    EventReplayBatch,
    InterfaceEventEnvelope,
)

if TYPE_CHECKING:
    from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig


def _utc_now() -> str:
    """Return the current instant as an ISO 8601 UTC timestamp.

    Returns:
        Timezone-aware UTC timestamp string.
    """
    return datetime.now(UTC).isoformat()


class EventStreamBuffer:
    """Ordered event buffer for one mounted transport generation.

    The buffer is process-local transport state: retention is bounded by
    configuration, sequence numbers are strictly monotonic per generation,
    and cursors are the deterministic event IDs assigned at publish time.
    """

    def __init__(self, config: ServeApiEventsConfig) -> None:
        """Initialize the buffer with bounded retention configuration.

        Args:
            config: Feature configuration carrying the stream bounds.
        """
        self._config = config
        self._sequence = 0
        self._events: deque[InterfaceEventEnvelope] = deque()
        self._cursor_index: dict[str, int] = {}
        self._closed = False

    def publish(
        self,
        event_type: str,
        topic: str,
        payload: dict[str, object],
    ) -> InterfaceEventEnvelope:
        """Publish one typed event into the bounded buffer.

        Args:
            event_type: Domain event classification name.
            topic: Channel or domain topic name.
            payload: JSON-serializable event data mapping.

        Returns:
            Envelope with the assigned sequence and deterministic cursor ID.

        Raises:
            ValueError: If a label is empty or the payload exceeds the
                configured byte bound.
            TypeError: If the payload is not a dictionary.
            InterfaceError: If the buffer is disposed.
        """
        self._ensure_open()
        if not isinstance(event_type, str) or not event_type:
            raise ValueError("event_type must be a non-empty string")
        if not isinstance(topic, str) or not topic:
            raise ValueError("topic must be a non-empty string")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        serialized = json.dumps(payload, default=str, separators=(",", ":"))
        size = len(serialized.encode("utf-8"))
        if size > self._config.event_payload_max_bytes:
            message = (
                f"event payload exceeds event_payload_max_bytes ({size} > "
                f"{self._config.event_payload_max_bytes})"
            )
            raise ValueError(message)
        self._sequence += 1
        envelope = InterfaceEventEnvelope(
            event_id=f"evt-{self._sequence:020d}",
            sequence_number=self._sequence,
            event_type=event_type,
            topic=topic,
            payload=dict(payload),
            timestamp=_utc_now(),
        )
        self._events.append(envelope)
        self._cursor_index[envelope.event_id] = envelope.sequence_number
        while len(self._events) > self._config.stream_retention_events:
            evicted = self._events.popleft()
            del self._cursor_index[evicted.event_id]
        return envelope

    def replay(
        self,
        last_event_id: str | None,
        max_events: int = 100,
    ) -> EventReplayBatch:
        """Replay retained events following a cursor.

        Args:
            last_event_id: Last received event ID, or None for the latest
                tail batch.
            max_events: Requested batch size; clamped to the configured
                replay batch limit.

        Returns:
            Batch of envelopes in sequence order with the next cursor.

        Raises:
            ValueError: If max_events is not a positive integer.
            EventCursorExpiredError: If the cursor is expired, unknown, or
                otherwise invalid, requiring a resync.
            InterfaceError: If the buffer is disposed.
        """
        self._ensure_open()
        if (
            not isinstance(max_events, int)
            or isinstance(max_events, bool)
            or max_events < 1
        ):
            raise ValueError("max_events must be a positive integer")
        limit = min(max_events, self._config.stream_replay_batch_limit)
        if last_event_id is None:
            tail = list(self._events)[-limit:]
            return EventReplayBatch(
                events=tuple(tail),
                next_cursor=tail[-1].event_id if tail else None,
                has_more=False,
                is_resync_required=False,
            )
        if not isinstance(last_event_id, str) or not last_event_id:
            raise ValueError("last_event_id must be a non-empty string")
        cursor_sequence = self._cursor_index.get(last_event_id)
        if cursor_sequence is None:
            raise EventCursorExpiredError(last_event_id)
        following = [
            envelope
            for envelope in self._events
            if envelope.sequence_number > cursor_sequence
        ]
        batch = following[:limit]
        return EventReplayBatch(
            events=tuple(batch),
            next_cursor=batch[-1].event_id if batch else last_event_id,
            has_more=len(following) > limit,
            is_resync_required=False,
        )

    def close(self) -> None:
        """Dispose the buffer and drop all retained events.

        Repeated calls are safe and perform no further work.
        """
        self._events.clear()
        self._cursor_index.clear()
        self._closed = True

    def _ensure_open(self) -> None:
        """Reject use after disposal.

        Raises:
            InterfaceError: If the buffer is disposed.
        """
        if self._closed:
            raise InterfaceError(
                "Event stream buffer is disposed",
                error_code="TRANSPORT_CLOSED",
            )
