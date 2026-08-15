"""Heap queue for deterministic scheduler events."""

# ruff: noqa: DOC201

from __future__ import annotations

import heapq
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.simulator.scheduler.contracts import _ScheduledEvent


class _EventQueue:
    """Private stable heap with duplicate-identity rejection."""

    def __init__(self) -> None:
        """Initialize an empty queue."""
        self._heap: list[tuple[tuple[object, ...], _ScheduledEvent]] = []
        self._identities: set[str] = set()

    def push(self, event: _ScheduledEvent) -> None:
        """Insert one event.

        Raises:
            ValueError: If its identity already exists.
        """
        if event.event_id in self._identities:
            raise ValueError("duplicate scheduler event identity")
        self._identities.add(event.event_id)
        heapq.heappush(self._heap, (event.key, event))

    def pop(self) -> _ScheduledEvent:
        """Pop the next event.

        Raises:
            ValueError: If the queue is empty.
        """
        if not self._heap:
            raise ValueError("scheduler queue is empty")
        return heapq.heappop(self._heap)[1]

    def ordered(self) -> tuple[_ScheduledEvent, ...]:
        """Return an immutable ordered snapshot."""
        return tuple(item[1] for item in sorted(self._heap, key=lambda item: item[0]))

    def __bool__(self) -> bool:
        """Return whether pending heap entries exist."""
        return bool(self._heap)


__all__ = ["_EventQueue"]
