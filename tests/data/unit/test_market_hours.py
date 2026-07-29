"""Tests for deterministic venue-authoritative market-hours evaluation."""

from datetime import UTC, datetime, timedelta

from app.services.data.time_sessions.contracts import MarketSchedule, SessionWindow
from app.services.data.time_sessions.market_hours import evaluate_market_hours
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
