"""Explicit simulated clock owned by the scheduler."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from datetime import datetime, timedelta


class _SimulatedClock:
    """Monotonic clock advanced only from scheduled events."""

    def __init__(self, current: datetime) -> None:
        """Initialize from an explicit aware UTC instant."""
        if current.tzinfo is None or current.utcoffset() != timedelta(0):
            raise ValueError("scheduler clock must be aware UTC")
        self._current = current

    @property
    def current(self) -> datetime:
        """Return the current simulated instant."""
        return self._current

    def advance_to(self, instant: datetime) -> datetime:
        """Advance monotonically to an event instant.

        Raises:
            ValueError: If the event precedes current simulated time.
        """
        if instant < self._current:
            raise ValueError("scheduler clock cannot move backwards")
        self._current = instant
        return instant


__all__ = ["_SimulatedClock"]
