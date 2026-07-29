"""Unit tests for pure calendar-state restriction (FR-DATA-127)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.services.data.contracts import DataError
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.restriction import (
    CALENDAR_STATE_BLACKOUT_AFTER,
    CALENDAR_STATE_BLACKOUT_BEFORE,
    CALENDAR_STATE_EVENT,
    CALENDAR_STATE_OPEN,
    evaluate_calendar_state,
    is_news_restricted_events,
)

_AT = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def _event(
    *,
    delta: timedelta,
    impact: EventImpact = EventImpact.HIGH,
    currency: str = "USD",
    country: str = "US",
    name: str = "CPI",
) -> EconomicEvent:
    """Build one event at ``_AT + delta``."""
    return EconomicEvent(
        id=f"ff:{delta.total_seconds()}",
        provider="scrape:forexfactory",
        name=name,
        category=None,
        country=country,
        currency=currency,
        scheduled_at=_AT + delta,
        impact=impact,
        actual=None,
        forecast=None,
        previous=None,
        actual_raw=None,
        forecast_raw=None,
        previous_raw=None,
        unit=None,
        source="forexfactory",
        source_url=None,
        updated_at=None,
    )


from app.services.data.contracts.responses import unwrap_data_response


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.economic_calendar.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_empty_successful_event_result_is_open() -> None:
    """An authoritative empty event collection is benign, not missing."""
    assert _unwrap(evaluate_calendar_state([], _AT)) == CALENDAR_STATE_OPEN


def test_at_on_event_release_is_event_state() -> None:
    """The instant exactly at the schedule is the release-state."""
    events = [_event(delta=timedelta(0))]
    assert _unwrap(evaluate_calendar_state(events, _AT)) == CALENDAR_STATE_EVENT


def test_at_before_release_is_blackout_before() -> None:
    """Five minutes before a high-impact event with a 10-minute window blocks."""
    events = [_event(delta=timedelta(minutes=5))]
    assert (
        _unwrap(evaluate_calendar_state(events, _AT)) == CALENDAR_STATE_BLACKOUT_BEFORE
    )


def test_at_after_release_is_blackout_after() -> None:
    """Five minutes after a high-impact event with a 10-minute window blocks."""
    events = [_event(delta=timedelta(minutes=-5))]
    assert (
        _unwrap(evaluate_calendar_state(events, _AT)) == CALENDAR_STATE_BLACKOUT_AFTER
    )


def test_at_outside_any_window_is_open() -> None:
    """A far-away event leaves the instant open."""
    events = [_event(delta=timedelta(hours=3))]
    assert _unwrap(evaluate_calendar_state(events, _AT)) == CALENDAR_STATE_OPEN


def test_minutes_before_excludes_at_outside_window() -> None:
    """A configured zero-minute pre-window admits any time before the release."""
    events = [_event(delta=timedelta(minutes=5))]
    assert (
        _unwrap(evaluate_calendar_state(events, _AT, before_minutes=0))
        == CALENDAR_STATE_OPEN
    )


def test_minimum_impact_filters_low_events() -> None:
    """A LOW impact event is ignored when filter is HIGH."""
    events = [_event(delta=timedelta(minutes=5), impact=EventImpact.LOW)]
    assert (
        _unwrap(evaluate_calendar_state(events, _AT, minimum_impact=EventImpact.HIGH))
        == CALENDAR_STATE_OPEN
    )
    assert (
        _unwrap(evaluate_calendar_state(events, _AT, minimum_impact=EventImpact.LOW))
        == CALENDAR_STATE_BLACKOUT_BEFORE
    )


def test_event_release_wins_over_blackout_of_a_near_neighbour() -> None:
    """An exact-release takes precedence over an adjacent blackout event."""
    events = [
        _event(delta=timedelta(minutes=5), name="NearEvent"),
        _event(delta=timedelta(minutes=0), name="ThisEvent"),
    ]
    assert _unwrap(evaluate_calendar_state(events, _AT, before_minutes=10)) == (
        CALENDAR_STATE_EVENT
    )


def test_naive_at_raises() -> None:
    """Timezone-naive input fails deterministically."""
    events = [_event(delta=timedelta(minutes=5))]
    with pytest.raises(DataError):
        _unwrap(evaluate_calendar_state(events, _AT.replace(tzinfo=None)))


def test_negative_minutes_raise() -> None:
    """Negative blackout minutes fail closed."""
    events = [_event(delta=timedelta(minutes=5))]
    with pytest.raises(DataError):
        _unwrap(evaluate_calendar_state(events, _AT, before_minutes=-1))


def test_is_news_restricted_blocks_calendar_states() -> None:
    """``is_news_restricted_events`` returns True only for blocking states."""
    events = [_event(delta=timedelta(minutes=5))]
    assert _unwrap(is_news_restricted_events(events, _AT)) is True


def test_is_news_restricted_open_returns_false() -> None:
    """``open`` state is not a block."""
    events = [_event(delta=timedelta(hours=3))]
    assert _unwrap(is_news_restricted_events(events, _AT)) is False


def test_is_news_restricted_unknown_does_not_block() -> None:
    """The pure helper never blocks when events are absent by design."""
    assert _unwrap(is_news_restricted_events([], _AT)) is False
