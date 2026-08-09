"""Fail-closed temporal validation for indicator inputs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)
from app.utils import get_logger

logger = get_logger(__name__)

_TIMEFRAME_SECONDS = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}


def _require_utc(value: datetime, field: str) -> None:
    """Require one aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field: Field name used in safe diagnostics.

    Raises:
        IndicatorError: If the value is not aware UTC.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_TIMEZONE,
            "closed-input timestamps must be aware UTC",
            {"field": field},
        )


@guard_public_boundary
def assert_closed_input(
    *,
    source_start: datetime,
    source_end: datetime,
    available_at: datetime | None,
    decision_time: datetime,
    source_timeframe: str,
    requested_timeframe: str,
    max_age: timedelta,
    complete: bool,
) -> bool:
    """Assert that supplied evidence is closed, causal, fresh, and compatible.

    Args:
        source_start: Inclusive source interval start.
        source_end: Exclusive source interval end.
        available_at: Earliest safe consumption time, or null when unknown.
        decision_time: Point-in-time decision boundary.
        source_timeframe: Canonical source timeframe.
        requested_timeframe: Canonical consuming timeframe.
        max_age: Explicit maximum permitted evidence age.
        complete: Whether the producer declares the evidence complete.

    Returns:
        True when every closed-input invariant passes.

    Raises:
        IndicatorError: If evidence is incomplete, future, stale, or incompatible.
    """
    logger.info("Validating closed indicator input")
    for field, value in (
        ("source_start", source_start),
        ("source_end", source_end),
        ("decision_time", decision_time),
    ):
        _require_utc(value, field)
    if available_at is None:
        raise IndicatorError(
            IndicatorErrorCode.IND_INPUT_NOT_CLOSED,
            "input availability is unknown",
        )
    _require_utc(available_at, "available_at")
    if max_age <= timedelta(0):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "maximum input age must be positive",
        )
    source_seconds = _TIMEFRAME_SECONDS.get(source_timeframe)
    requested_seconds = _TIMEFRAME_SECONDS.get(requested_timeframe)
    if (
        source_seconds is None
        or requested_seconds is None
        or requested_seconds % source_seconds != 0
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INCOMPATIBLE_TIMEFRAME,
            "source and requested timeframes are incompatible",
        )
    expected_end = source_start + timedelta(seconds=source_seconds)
    if not complete or source_end != expected_end or available_at > decision_time:
        raise IndicatorError(
            IndicatorErrorCode.IND_INPUT_NOT_CLOSED,
            "input interval is incomplete or unavailable",
        )
    if source_end > decision_time:
        raise IndicatorError(
            IndicatorErrorCode.IND_LOOKAHEAD_RISK,
            "input interval ends after the decision time",
        )
    if decision_time - available_at > max_age:
        raise IndicatorError(
            IndicatorErrorCode.IND_STALE_INPUT,
            "input evidence exceeds its explicit maximum age",
        )
    return True


__all__ = ["assert_closed_input"]
