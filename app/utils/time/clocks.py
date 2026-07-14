"""Injectable UTC clock boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.utils.errors.exceptions import ValidationError


class Clock(Protocol):
    """Protocol for an injected clock."""

    def now(self) -> datetime:
        """Return the current aware UTC instant."""
        ...


class SystemClock:
    """System implementation of the UTC clock boundary."""

    def now(self) -> datetime:
        """Return the current aware UTC instant."""
        return datetime.now(UTC)


def utc_now(clock: Clock | None = None) -> datetime:
    """Return an aware UTC instant from an injected or system clock.

    Args:
        clock: Optional injected clock.

    Returns:
        An aware UTC datetime.

    Raises:
        ValidationError: If the clock returns a naive or non-UTC datetime.
    """
    current = (clock or SystemClock()).now()
    offset = current.utcoffset()
    if current.tzinfo is None or offset is None:
        raise ValidationError("CLOCK_VALUE_INVALID")
    if offset.total_seconds() != 0:
        raise ValidationError("CLOCK_VALUE_INVALID")
    return current
