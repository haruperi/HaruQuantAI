"""Provide an injectable boundary for obtaining aware UTC instants."""

from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.utils.errors.exceptions import ValidationError


class Clock(Protocol):
    """Describe a clock capable of returning a current datetime."""

    def now(self) -> datetime:
        """Return the current aware UTC instant.

        Returns:
            The clock's current datetime. Consumers validate that it is aware
            and UTC before accepting it.
        """
        ...


class SystemClock:
    """Read aware UTC instants from the local system clock."""

    def now(self) -> datetime:
        """Return the current aware UTC system instant.

        Returns:
            The current datetime with the standard-library UTC timezone.
        """
        return datetime.now(UTC)


def utc_now(clock: Clock | None = None) -> datetime:
    """Return an aware UTC instant from an injected or system clock.

    Args:
        clock: Optional caller-controlled clock. A ``SystemClock`` is used when
            omitted.

    Returns:
        The validated aware UTC instant returned by the selected clock.

    Raises:
        ValidationError: The clock returns a naive or non-UTC datetime.
    """
    current = (clock or SystemClock()).now()
    if current.tzinfo is None or current.utcoffset() != timedelta(0):
        raise ValidationError("CLOCK_VALUE_INVALID")
    return current
