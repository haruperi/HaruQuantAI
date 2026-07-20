"""In-memory Event Bus and pub/sub primitives for utilities.

This module is a support helper, not an official AI tool. It provides a
thread-safe bounded pub/sub bus suitable for tests and local workflows.
It does not connect to any external message broker.

Public exports:
    EventEnvelope, PublishResult, InMemoryEventBus,
    build_event_envelope, publish_event.

Side effects:
    None on import. All state lives inside caller-owned ``InMemoryEventBus``
    instances.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from threading import RLock
from typing import Literal, TypedDict

from app.services.utils.errors import ValidationError
from app.services.utils.identity import generate_event_id
from app.services.utils.logger import logger
from app.services.utils.normalization import format_utc_timestamp, utc_now
from app.services.utils.security import redact_mapping

EventSeverity = Literal["info", "warning", "error", "critical"]
DeliveryStatus = Literal["delivered", "failed", "dropped", "duplicate", "conflict"]
EventHandler = Callable[[dict[str, object]], None]


class EventEnvelope(TypedDict):
    """Standard utility event envelope."""

    event_id: str
    event_type: str
    event_version: str
    source: str
    severity: EventSeverity
    timestamp: str
    request_id: str | None
    correlation_id: str | None
    causation_id: str | None
    idempotency_key: str | None
    payload: dict[str, object]
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Event publish result."""

    status: DeliveryStatus
    message: str
    event_id: str | None
    delivered_count: int = 0
    failed_count: int = 0


@dataclass
class InMemoryEventBus:
    """Thread-safe bounded in-memory Event Bus for tests and local workflows.

    Note:
        The idempotency cache grows unbounded. For production workflows,
        supply an external bus with TTL-based eviction.
    """

    max_queue_size: int = 1000
    fail_fast_when_full: bool = True
    _handlers: dict[str, list[EventHandler]] = field(
        default_factory=dict, init=False, repr=False
    )
    _queue: deque[EventEnvelope] = field(default_factory=deque, init=False, repr=False)
    _idempotency: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register an event handler for an event type.

        Args:
            event_type: Non-empty event type to subscribe to.
            handler: Callable invoked with a copy of each published event.

        Raises:
            ValidationError: If ``event_type`` is empty.

        Side effects:
            Mutates this bus instance's handler registry.
        """
        if not event_type.strip():
            raise ValidationError("event_type must be non-empty.", code="INVALID_INPUT")
        with self._lock:
            self._handlers.setdefault(event_type, []).append(handler)
        logger.debug(
            "Implemented event subscription", extra={"event_name": "event_subscribed"}
        )

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unregister an event handler if it is currently registered.

        Args:
            event_type: Event type the handler was registered under.
            handler: The handler callable to remove.

        Side effects:
            Mutates this bus instance's handler registry. A no-op when the
            handler is not registered.
        """
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            self._handlers[event_type] = [item for item in handlers if item != handler]
        logger.debug(
            "Implemented event unsubscription",
            extra={"event_name": "event_unsubscribed"},
        )

    def publish(self, event: EventEnvelope) -> PublishResult:
        """Publish an event to registered handlers.

        Enforces idempotency and bounded-queue policy before dispatching to
        handlers. Handler exceptions are isolated and counted rather than
        raised.

        Args:
            event: Sanitized event envelope to publish.

        Returns:
            A ``PublishResult`` describing the delivery outcome
            (``delivered``, ``failed``, ``dropped``, ``duplicate``, or
            ``conflict``).

        Side effects:
            Mutates queue and idempotency state; invokes subscriber
            handlers.
        """
        with self._lock:
            key = event.get("idempotency_key")
            material = str(event.get("event_id"))
            if key is not None and key in self._idempotency:
                if self._idempotency[key] == material:
                    return PublishResult(
                        "duplicate", "duplicate event ignored", event["event_id"]
                    )
                return PublishResult(
                    "conflict", "idempotency conflict", event["event_id"]
                )
            if len(self._queue) >= self.max_queue_size:
                if self.fail_fast_when_full:
                    return PublishResult(
                        "dropped", "event queue is full", event["event_id"]
                    )
                self._queue.popleft()
            self._queue.append(event)
            if key is not None:
                self._idempotency[key] = material
            handlers = list(self._handlers.get(event["event_type"], []))
        delivered = 0
        failed = 0
        for handler in handlers:
            try:
                handler(dict(event))
                delivered += 1
            except Exception:  # noqa: BLE001
                failed += 1
        status: DeliveryStatus = "failed" if failed else "delivered"
        logger.debug(
            "Implemented event publish dispatch",
            extra={"event_name": "event_published", "status": status},
        )
        return PublishResult(
            status, "event published", event["event_id"], delivered, failed
        )

    def queue_depth(self) -> int:
        """Return the current queue depth.

        Returns:
            Number of events currently buffered in the bounded queue.
        """
        with self._lock:
            depth = len(self._queue)
        logger.info("Implemented retrieving event bus queue depth")
        return depth

    def idempotency_size(self) -> int:
        """Return the idempotency cache size.

        Returns:
            Number of remembered idempotency keys.
        """
        with self._lock:
            size = len(self._idempotency)
        logger.info("Implemented retrieving event bus idempotency size")
        return size


def build_event_envelope(
    *,
    event_type: str,
    source: str,
    payload: Mapping[str, object],
    severity: EventSeverity = "info",
    event_version: str = "1.0.0",
    request_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    idempotency_key: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> EventEnvelope:
    """Build a sanitized utility event envelope with a deterministic ID.

    Payload and metadata are redacted of secret material before the
    envelope is returned.

    Args:
        event_type: Non-empty event type identifier.
        source: Non-empty originating component name.
        payload: Event payload mapping; redacted before storage.
        severity: Event severity (info, warning, error, or critical).
        event_version: Stable event schema version.
        request_id: Optional trace request identifier.
        correlation_id: Optional cross-request correlation identifier.
        causation_id: Optional causing-event identifier.
        idempotency_key: Optional idempotency key for duplicate suppression.
        metadata: Optional metadata mapping; redacted before storage.

    Returns:
        A sanitized ``EventEnvelope``.

    Raises:
        ValidationError: If ``event_type``/``source`` is empty or
            ``severity`` is invalid.

    Side effects:
        None.
    """
    if not event_type.strip():
        raise ValidationError("event_type must be non-empty.", code="INVALID_INPUT")
    if not source.strip():
        raise ValidationError("source must be non-empty.", code="INVALID_INPUT")
    if severity not in {"info", "warning", "error", "critical"}:
        raise ValidationError("severity is invalid.", code="INVALID_INPUT")
    timestamp_str = format_utc_timestamp(utc_now())
    envelope: EventEnvelope = {
        "event_id": generate_event_id(),
        "event_type": event_type,
        "event_version": event_version,
        "source": source,
        "severity": severity,
        "timestamp": timestamp_str if timestamp_str is not None else "",
        "request_id": request_id,
        "correlation_id": correlation_id,
        "causation_id": causation_id,
        "idempotency_key": idempotency_key,
        "payload": redact_mapping(dict(payload)),
        "metadata": redact_mapping(dict(metadata or {})),
    }
    logger.debug(
        "Implemented event envelope construction",
        extra={"event_name": "event_envelope_built"},
    )
    return envelope


def publish_event(
    bus: InMemoryEventBus,
    event: EventEnvelope,
    *,
    timeout_seconds: float | None = None,
) -> PublishResult:
    """Publish an event through a caller-owned bus with an optional deadline.

    Args:
        bus: The caller-owned ``InMemoryEventBus`` to publish through.
        event: Sanitized event envelope to publish.
        timeout_seconds: Optional wall-clock deadline. When exceeded, a
            failed result is returned even if dispatch completed.

    Returns:
        The bus ``PublishResult``, or a ``"failed"`` result when the
        deadline is exceeded.

    Side effects:
        Delegates to ``bus.publish``; mutates bus state.
    """
    start = time.perf_counter()
    result = bus.publish(event)
    if timeout_seconds is not None and time.perf_counter() - start > timeout_seconds:
        logger.info(
            "Implemented event publish with timeout breach",
            extra={"event_name": "event_publish_timeout"},
        )
        return PublishResult("failed", "event publish timed out", event["event_id"])
    logger.info(
        "Implemented event publish via helper",
        extra={"event_name": "event_publish_helper"},
    )
    return result
