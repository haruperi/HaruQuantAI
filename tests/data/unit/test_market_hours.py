"""Tests for deterministic venue-authoritative market-hours evaluation."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.data.contracts import DataError
from app.services.data.time_sessions.contracts import (
    MarketHours,
    MarketSchedule,
    SessionWindow,
)
from app.services.data.time_sessions.market_hours import (
    apply_venue_halt,
    evaluate_market_hours,
)
from app.utils import generate_id


def test_evaluate_market_hours_selects_current_and_next_sessions() -> None:
    checked_at = datetime(2026, 7, 20, 12, tzinfo=UTC)
    current = SessionWindow(
        label="current",
        opens_at=checked_at - timedelta(hours=1),
        closes_at=checked_at + timedelta(hours=1),
    )
    upcoming = SessionWindow(
        label="next",
        opens_at=checked_at + timedelta(hours=2),
        closes_at=checked_at + timedelta(hours=3),
    )
    schedule = MarketSchedule(
        source_id="broker",
        symbol="EURUSD",
        timezone="UTC",
        hours=(current, upcoming),
        sessions=(current, upcoming),
        observed_at=checked_at,
        request_id=generate_id("req"),
    )

    result = evaluate_market_hours(schedule, checked_at=checked_at)

    assert result.is_open is True
    assert result.current_session == current
    assert result.next_session == upcoming


def test_evaluate_market_hours_fails_closed_when_no_session_covers_time() -> None:
    checked_at = datetime(2026, 7, 20, 12, tzinfo=UTC)
    upcoming = SessionWindow(
        label="next",
        opens_at=checked_at + timedelta(hours=2),
        closes_at=checked_at + timedelta(hours=3),
    )
    schedule = MarketSchedule(
        source_id="broker",
        symbol="EURUSD",
        timezone="UTC",
        hours=(upcoming,),
        sessions=(upcoming,),
        observed_at=checked_at,
        request_id=generate_id("req"),
    )

    result = evaluate_market_hours(schedule, checked_at=checked_at)

    assert result.is_open is False
    assert result.current_session is None
    assert result.next_session == upcoming


def _open_hours() -> MarketHours:
    checked_at = datetime(2026, 7, 20, 12, tzinfo=UTC)
    current = SessionWindow(
        label="current",
        opens_at=checked_at - timedelta(hours=1),
        closes_at=checked_at + timedelta(hours=1),
    )
    schedule = MarketSchedule(
        source_id="broker",
        symbol="EURUSD",
        timezone="UTC",
        hours=(current,),
        sessions=(current,),
        observed_at=checked_at,
        request_id=generate_id("req"),
    )
    return evaluate_market_hours(schedule, checked_at=checked_at)


def test_apply_venue_halt_overrides_tradability_with_genuine_evidence() -> None:
    """A halted venue is never reported open, even mid-session (feature)."""
    hours = _open_hours()
    assert hours.is_open is True

    reopen_at = hours.checked_at + timedelta(minutes=30)
    halted = apply_venue_halt(
        hours, halted=True, reason="circuit breaker", reopen_at=reopen_at
    )

    assert halted.is_open is False
    assert halted.current_session is None
    assert halted.halted is True
    assert halted.halt_reason == "circuit breaker"
    assert halted.reopen_at == reopen_at


def test_apply_venue_halt_clears_halt_evidence_when_not_halted() -> None:
    """Clearing a halt drops its reason/reopen evidence without fabricating
    a restored `is_open`; the caller must re-evaluate tradability with
    `evaluate_market_hours` to resume, never infer it from the stale halt."""
    hours = _open_hours()
    halted = apply_venue_halt(hours, halted=True, reason="news pending")

    resumed = apply_venue_halt(halted, halted=False)

    assert resumed.halted is False
    assert resumed.halt_reason is None
    assert resumed.reopen_at is None
    assert resumed.is_open is False
    assert resumed.current_session is None


def test_market_hours_rejects_halted_and_open_together() -> None:
    """The contract itself fails closed on an inconsistent halted/open state."""
    hours = _open_hours()
    with pytest.raises(DataError):
        type(hours).model_validate({**dict(hours), "halted": True, "is_open": True})


def test_market_hours_rejects_halt_evidence_without_halted_flag() -> None:
    """A halt reason or reopen time requires `halted=True`."""
    hours = _open_hours()
    with pytest.raises(DataError):
        type(hours).model_validate({**dict(hours), "halt_reason": "unexpected"})
