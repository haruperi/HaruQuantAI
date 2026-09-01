"""Immutable contracts for deterministic scheduler events."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal

from app.kernel.serialization import canonical_json

EventStatus = Literal["pending", "cancelled", "completed", "failed"]
EVENT_PRIORITIES: tuple[str, ...] = (
    "command_arrival",
    "tick_arrival",
    "rollover",
    "mark_to_market",
    "protective_trigger",
    "match_evaluation",
    "stop_out",
    "response_delivery",
)


@dataclass(frozen=True, slots=True)
class _ScheduledEvent:
    """One serializable deterministic scheduler event."""

    event_id: str
    scheduled_at: datetime
    priority: str
    canonical_symbol: str
    source_sequence: int
    scheduler_sequence: int
    handler_id: str
    payload: Mapping[str, object] = field(default_factory=dict)
    status: EventStatus = "pending"

    def __post_init__(self) -> None:
        """Validate and freeze scheduler event material.

        Raises:
            ValueError: If event identity, time, priority, or payload is invalid.
        """
        if not self.event_id or not self.handler_id or not self.canonical_symbol:
            raise ValueError("scheduler event identity is required")
        if (
            self.scheduled_at.tzinfo is None
            or self.scheduled_at.utcoffset() != timedelta(0)
        ):
            raise ValueError("scheduler timestamps must be aware UTC")
        if self.priority not in EVENT_PRIORITIES:
            raise ValueError("unknown scheduler event priority")
        if self.source_sequence < 0 or self.scheduler_sequence < 0:
            raise ValueError("scheduler sequences must be non-negative")
        canonical_json(self.payload)
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    @property
    def key(self) -> tuple[datetime, int, str, int, int]:
        """Return the canonical total-order key."""
        return (
            self.scheduled_at,
            EVENT_PRIORITIES.index(self.priority),
            self.canonical_symbol,
            self.source_sequence,
            self.scheduler_sequence,
        )


__all__ = ["EVENT_PRIORITIES", "EventStatus", "_ScheduledEvent"]
