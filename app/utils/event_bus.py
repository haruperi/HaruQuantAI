"""InMemoryEventBus and event building utilities for HaruQuantAI.

This module provides basic event routing and envelope packaging for utilities.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class EventPublishResult:
    """Represents the result of an event publication attempt.

    Attributes:
        status: The final status of the delivery: 'delivered', 'duplicate',
            or 'failed'.
        message: Human-readable status details.
    """

    status: Literal["delivered", "duplicate", "failed"]
    message: str


class InMemoryEventBus:
    """Simple in-memory event bus for application diagnostics and testing."""

    def __init__(self) -> None:
        """Initialize the event bus with an empty log."""
        self._published_events: list[dict[str, Any]] = []

    def publish(self, event: dict[str, Any]) -> EventPublishResult:
        """Publish an event to the in-memory bus.

        Args:
            event: The standard event envelope dictionary to publish.

        Returns:
            An EventPublishResult indicating the event was delivered.
        """
        self._published_events.append(event)
        return EventPublishResult(
            status="delivered",
            message="Event delivered to in-memory bus successfully.",
        )


def build_event_envelope(
    *,
    event_type: str,
    source: str,
    severity: str,
    request_id: str | None = None,
    payload: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Build a standard event envelope.

    Args:
        event_type: Stable dot-separated event classification.
        source: Identifier of the emitting service.
        severity: Severity classification: 'info', 'warning', or 'error'.
        request_id: Optional trace ID for diagnostics.
        payload: Event domain parameters.
        metadata: Optional extra event tags.
        idempotency_key: Optional signature to prevent duplicate delivery.

    Returns:
        Structured event envelope dictionary with a unique event ID.
    """
    event_id = f"event_{uuid.uuid4().hex[:16]}"
    return {
        "event_id": event_id,
        "event_type": event_type,
        "source": source,
        "severity": severity,
        "timestamp": time.time(),
        "request_id": request_id,
        "payload": dict(payload),
        "metadata": dict(metadata or {}),
        "idempotency_key": idempotency_key,
    }
