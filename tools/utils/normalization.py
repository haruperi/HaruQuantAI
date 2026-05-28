"""Timestamp normalization helpers for HaruQuantAI data tools."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def to_utc(value: datetime) -> datetime:
    """Return a datetime converted to UTC."""
    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime instance.")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def format_timestamp_z(value: datetime | None) -> str | None:
    """Format a datetime as an ISO timestamp ending in Z."""
    if value is None:
        return None
    return to_utc(value).isoformat().replace("+00:00", "Z")


def evaluate_freshness(
    observed_at: datetime,
    *,
    max_age_seconds: int,
    clock: Any = None,
) -> dict[str, Any]:
    """Evaluate whether an observation is within a freshness threshold."""
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative.")
    now = clock.now(timezone.utc) if clock is not None else datetime.now(timezone.utc)
    age_seconds = max(0.0, (to_utc(now) - to_utc(observed_at)).total_seconds())
    return {
        "observed_at": format_timestamp_z(observed_at),
        "age_seconds": age_seconds,
        "max_age_seconds": max_age_seconds,
        "is_fresh": age_seconds <= max_age_seconds,
    }


__all__ = [
    "evaluate_freshness",
    "format_timestamp_z",
    "to_utc",
]
