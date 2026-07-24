"""Deterministic market-open evaluation from authoritative UTC sessions."""

from datetime import datetime

from app.services.data.time_sessions.contracts import MarketHours, MarketSchedule
from app.services.data.time_sessions.utc import require_utc


def evaluate_market_hours(
    schedule: MarketSchedule,
    *,
    checked_at: datetime,
) -> MarketHours:
    """Evaluate current and next sessions without inferring missing evidence.

    Args:
        schedule: Authoritative schedule containing ordered UTC windows.
        checked_at: UTC instant to evaluate.

    Returns:
        Market hours with deterministic current and next selections.

    Raises:
        DataError: If ``checked_at`` is not timezone-aware UTC.
    """
    checked_at = require_utc(checked_at)
    current = next(
        (
            session
            for session in schedule.hours
            if session.opens_at <= checked_at < session.closes_at
        ),
        None,
    )
    next_session = next(
        (session for session in schedule.hours if session.opens_at > checked_at),
        None,
    )
    return MarketHours(
        **schedule.model_dump(),
        is_open=current is not None,
        checked_at=checked_at,
        current_session=current,
        next_session=next_session,
    )


__all__ = ["evaluate_market_hours"]
