"""Deterministic market-open evaluation from authoritative UTC sessions."""

from datetime import datetime

from app.services.data.time_sessions.contracts import (
    MarketHours,
    MarketSchedule,
    SessionWindow,
)
from app.services.data.time_sessions.utc import _require_utc_raw as require_utc


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
        **dict(schedule),
        is_open=current is not None,
        checked_at=checked_at,
        current_session=current,
        next_session=next_session,
    )


def apply_venue_halt(
    hours: MarketHours,
    *,
    halted: bool,
    reason: str | None = None,
    reopen_at: datetime | None = None,
    close_window: SessionWindow | None = None,
    roll_window: SessionWindow | None = None,
) -> MarketHours:
    """Overlay genuine caller-supplied venue-halt and window evidence.

    application Phase 0 reconciliation (`feature`): this function
    never infers a halt on its own. It composes evidence the caller already
    holds (for example a Data-owned `halt`/`venue_state` stream event) onto
    computed schedule tradability. A halted venue is never reported open.

    Args:
        hours: Previously evaluated market hours to overlay.
        halted: Whether the venue is currently halted, per caller evidence.
        reason: Halt reason; only meaningful when `halted` is `True`.
        reopen_at: Expected UTC resumption time; only meaningful when
            `halted` is `True`.
        close_window: Optional caller-supplied close/rollover window.
        roll_window: Optional caller-supplied roll window.

    Returns:
        Market hours with the halt and window evidence applied.

    Raises:
        ValueError: If the resulting contract is internally inconsistent.
    """
    fields = dict(hours)
    fields.update(
        {
            "is_open": False if halted else hours.is_open,
            "current_session": None if halted else hours.current_session,
            "halted": halted,
            "halt_reason": reason if halted else None,
            "reopen_at": reopen_at if halted else None,
            "close_window": close_window,
            "roll_window": roll_window,
        }
    )
    return MarketHours(**fields)


__all__ = ["apply_venue_halt", "evaluate_market_hours"]
