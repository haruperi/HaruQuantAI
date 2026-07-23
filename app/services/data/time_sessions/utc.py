"""Focused UTC validation for DATA time and session contracts."""

from datetime import datetime, timedelta


def require_utc(value: datetime) -> datetime:
    """Return an aware UTC timestamp or reject it.

    Args:
        value: Timestamp to validate.

    Returns:
        The unchanged aware UTC timestamp.

    Raises:
        ValueError: If the timestamp is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


__all__ = ["require_utc"]
