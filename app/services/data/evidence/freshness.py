"""Cross-domain evidence freshness validation."""

from datetime import datetime, timedelta


def is_fresh(available_at: datetime, now: datetime, maximum_age: timedelta) -> bool:
    """Return whether evidence is UTC-aware, non-future, and within the age bound."""
    if available_at.tzinfo is None or now.tzinfo is None:
        return False
    age = now - available_at
    return timedelta(0) <= age <= maximum_age


__all__ = ["is_fresh"]
