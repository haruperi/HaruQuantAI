"""Unit tests for research-only economic-calendar closure qualification."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.services.data.economic_calendar import closures
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact


def _event(*, name: str, event_type: str | None) -> EconomicEvent:
    """Build one normalized calendar event for closure classification."""
    return EconomicEvent(
        id="event-1",
        provider="scrape:forexfactory",
        name=name,
        category=None,
        country=None,
        currency="USD",
        scheduled_at=datetime(2025, 12, 25, 12, tzinfo=UTC),
        impact=EventImpact.LOW,
        event_type=event_type,
    )


def test_explicit_provider_holiday_type_is_preferred() -> None:
    """Provider definition evidence takes precedence over title inference."""
    assert closures._is_holiday(_event(name="Christmas Day", event_type="Holiday")) == (
        True,
        "provider_event_type",
    )


def test_legacy_title_requires_the_complete_holiday_word() -> None:
    """Legacy fallback is bounded to an exact word and avoids substrings."""
    assert closures._is_holiday(_event(name="Bank Holiday", event_type=None)) == (
        True,
        "legacy_title_word",
    )
    assert closures._is_holiday(_event(name="Preholiday Trading", event_type=None)) == (
        False,
        "legacy_title_word",
    )


def test_incomplete_calendar_coverage_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No closure support is returned when persisted coverage is incomplete."""

    class _Store:
        """Minimal incomplete-coverage store double."""

        def missing_intervals(
            self, *args: object, **kwargs: object
        ) -> tuple[object, ...]:
            del args, kwargs
            return (object(),)

        def query(self, *args: object, **kwargs: object) -> object:
            del args, kwargs
            raise AssertionError("query must not run without complete coverage")

    monkeypatch.setattr(closures, "EconomicEventStore", _Store)
    result = closures.resolve_calendar_closures(
        "EURUSD",
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, tzinfo=UTC),
        request_id="req-calendar",
    )

    assert result == ()


def test_complete_relevant_holiday_becomes_utc_day_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Complete relevant evidence yields bounded, provenance-bearing support."""
    event = _event(name="Christmas Day", event_type="holiday")

    class _Store:
        """Minimal complete-coverage store double."""

        def missing_intervals(self, *args: object, **kwargs: object) -> tuple[()]:
            del args, kwargs
            return ()

        def query(self, *args: object, **kwargs: object) -> object:
            del args, kwargs
            return SimpleNamespace(status="success", data=[event])

    monkeypatch.setattr(closures, "EconomicEventStore", _Store)
    monkeypatch.setattr(
        closures,
        "_get_symbol_event_profile_raw",
        lambda _symbol: SimpleNamespace(currencies=frozenset({"EUR", "USD"})),
    )
    result = closures.resolve_calendar_closures(
        "EURUSD",
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, tzinfo=UTC),
        request_id="req-calendar",
    )

    assert len(result) == 1
    assert result[0].opens_at == datetime(2025, 12, 25, tzinfo=UTC)
    assert result[0].closes_at == datetime(2025, 12, 26, tzinfo=UTC)
    assert result[0].classification_basis == "provider_event_type"
