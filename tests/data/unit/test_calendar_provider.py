"""EconomicCalendarProvider Protocol and scrape-adapter tests (FR-DATA-124)."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.providers import (
    CalendarScrapeProvider,
)

_START = datetime(2026, 1, 1, tzinfo=UTC)
_END = datetime(2026, 1, 8, tzinfo=UTC)


class _FakeTransport:
    """Deterministic transport returning ``site -> rows``."""

    def __init__(self, rows: Mapping[str, list[Mapping[str, object]]]) -> None:
        self._rows = rows

    async def fetch_site(
        self, site: str, _start: datetime, _end: datetime
    ) -> list[Mapping[str, object]]:
        return self._rows.get(site, [])


def _row(**overrides: object) -> Mapping[str, object]:
    """Build one raw calendar row applying the supplied overrides."""
    base: dict[str, object] = {
        "timestamp": "2026-01-02T12:30:00Z",
        "title": "Non-Farm Employment Change",
        "country": "USD",
        "impact": "High",
        "actual": "216K",
        "forecast": "170K",
        "previous": "173K",
    }
    base.update(overrides)
    return base


def test_provider_protocol_is_satisfied() -> None:
    """The scrape adapter exposes the broker-neutral Protocol surface."""
    provider = CalendarScrapeProvider(_FakeTransport({}), sites=("forexfactory",))
    assert callable(getattr(provider, "get_events", None))


def component_get_events_normalizes_calendar_events() -> None:
    """The scrape adapter wraps scraped rows into normalized events."""
    transport = _FakeTransport({"forexfactory": [_row()]})
    provider = CalendarScrapeProvider(transport, sites=("forexfactory",))

    events = asyncio.run(provider.get_events(_START, _END, minimum_impact=None))

    assert len(events) == 1
    event = events[0]
    assert isinstance(event, EconomicEvent)
    assert event.provider == "scrape:forexfactory"
    assert event.name == "Non-Farm Employment Change"
    assert event.impact is EventImpact.HIGH
    # ForexFactory publishes the currency ("USD") in the per-row country slot.
    # The adapter splits it back out: country=None, currency="USD".
    assert event.country is None
    assert event.currency == "USD"
    assert event.source == "forexfactory"
    assert event.actual is not None
    # The scraper preserves both the normalized Decimal and provider text.
    assert event.actual == 216000
    assert event.actual_raw == "216K"
    assert event.forecast_raw == "170K"
    assert event.previous_raw == "173K"
    assert event.unit == "K"


def test_get_events_normalizes_provider_country_case() -> None:
    """Normalize provider labels before enforcing the uppercase contract."""
    transport = _FakeTransport({"forexfactory": [_row(country="All")]})
    provider = CalendarScrapeProvider(transport, sites=("forexfactory",))

    events = asyncio.run(provider.get_events(_START, _END))

    assert events[0].country == "ALL"


def test_get_events_filters_by_currency() -> None:
    """Currency filter excludes non-matching rows post-normalization."""
    transport = _FakeTransport(
        {
            "forexfactory": [
                _row(country="USD"),
                _row(country="EUR", title="ECB Press Conference"),
            ]
        }
    )
    provider = CalendarScrapeProvider(transport, sites=("forexfactory",))

    usd_only = asyncio.run(provider.get_events(_START, _END, currencies=("USD",)))
    assert len(usd_only) == 1
    assert usd_only[0].currency == "USD"
    assert usd_only[0].country is None


def test_get_events_filters_by_minimum_impact() -> None:
    """Low impact events are filtered out when minimum_impact is HIGH."""
    transport = _FakeTransport(
        {
            "forexfactory": [
                _row(impact="High"),
                _row(impact="Low", title="Non-Farm Revisions"),
            ]
        }
    )
    provider = CalendarScrapeProvider(transport, sites=("forexfactory",))

    high_only = asyncio.run(
        provider.get_events(_START, _END, minimum_impact=EventImpact.HIGH)
    )
    assert len(high_only) == 1
    assert high_only[0].impact is EventImpact.HIGH


def test_get_events_maps_holiday_to_non_blocking_low_level() -> None:
    """Legacy holiday rows remain visible without expanding the impact enum."""
    transport = _FakeTransport(
        {
            "forexfactory": [
                _row(impact="holiday", title="New Year Holiday", actual=None)
            ]
        }
    )
    provider = CalendarScrapeProvider(transport, sites=("forexfactory",))

    events = asyncio.run(provider.get_events(_START, _END))
    assert len(events) == 1
    assert events[0].impact is EventImpact.LOW


def test_get_events_combines_currency_and_country_filters_as_relevance_union() -> None:
    """A currency match remains relevant when the provider has no country."""
    transport = _FakeTransport({"forexfactory": [_row(country="USD")]})
    provider = CalendarScrapeProvider(transport, sites=("forexfactory",))

    events = asyncio.run(
        provider.get_events(
            _START,
            _END,
            currencies=("EUR", "USD"),
            countries=("EU", "US"),
        )
    )

    assert len(events) == 1
    assert events[0].currency == "USD"
    assert events[0].country is None


def test_provider_event_id_survives_intraday_schedule_change() -> None:
    """Fallback identity does not change when a release moves within a day."""
    first = _FakeTransport({"forexfactory": [_row(timestamp="2026-01-02T12:30:00Z")]})
    revised = _FakeTransport({"forexfactory": [_row(timestamp="2026-01-02T13:00:00Z")]})

    first_event = asyncio.run(
        CalendarScrapeProvider(first, sites=("forexfactory",)).get_events(_START, _END)
    )[0]
    revised_event = asyncio.run(
        CalendarScrapeProvider(revised, sites=("forexfactory",)).get_events(
            _START,
            _END,
        )
    )[0]

    assert first_event.id == revised_event.id
