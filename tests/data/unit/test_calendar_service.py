"""Unit tests for the public economic-calendar service (FR-DATA-126)."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

import pytest
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    build_data_response,
    data_start_time,
    unwrap_data_response,
)
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.service import (
    get_economic_events,
    get_symbol_economic_events,
    is_news_restricted,
)

_AT = datetime(2026, 7, 26, 12, tzinfo=UTC)


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.economic_calendar.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def _event(
    *,
    scheduled_at: datetime,
    currency: str = "USD",
    country: str | None = None,
    impact: EventImpact = EventImpact.HIGH,
) -> EconomicEvent:
    """Build one valid normalized event."""
    return EconomicEvent(
        id="provider-event-1",
        provider="demo",
        name="CPI",
        category=None,
        country=country,
        currency=currency,
        scheduled_at=scheduled_at,
        impact=impact,
        updated_at=scheduled_at,
    )


class _Provider:
    """Deterministic provider that records its requested window and filters."""

    def __init__(self, events: Sequence[EconomicEvent]) -> None:
        self._events = list(events)
        self.calls: list[tuple[datetime, datetime]] = []
        self.currencies: Sequence[str] | None = None
        self.countries: Sequence[str] | None = None
        self.minimum_impact: EventImpact | None = None

    async def get_events(
        self,
        start: datetime,
        end: datetime,
        *,
        currencies: Sequence[str] | None = None,
        countries: Sequence[str] | None = None,
        minimum_impact: EventImpact | None = None,
    ):
        self.calls.append((start, end))
        self.currencies = currencies
        self.countries = countries
        self.minimum_impact = minimum_impact
        return build_data_response(
            operation="data.economic_calendar.get_economic_events",
            request_id="req-00000000-0000-4000-8000-000000000000",
            start_time=data_start_time(),
            data=list(self._events),
        )


class _Store:
    """Fast database-port fake preserving query-before-acquire ordering."""

    def __init__(
        self, events: Sequence[EconomicEvent] = (), *, covered: bool = False
    ) -> None:
        self.events = list(events)
        self.covered = covered
        self.queries = 0

    def missing_intervals(self, start, end, *, request_id):
        del request_id
        return () if self.covered else ((start, end),)

    def upsert(self, events, *, request_id):
        self.events = list(events)
        return build_data_response(
            operation="data.economic_calendar.economic_event_store.upsert",
            request_id=request_id,
            start_time=data_start_time(),
            data=len(self.events),
        )

    def record_coverage(self, *_args, **_kwargs):
        self.covered = True

    def query(self, start, end, **kwargs):
        self.queries += 1
        currencies = kwargs.get("currencies")
        minimum = kwargs.get("minimum_impact")
        events = [
            event
            for event in self.events
            if start <= event.scheduled_at < end
            and (not currencies or event.currency in currencies)
            and (minimum is None or event.impact >= minimum)
        ]
        return build_data_response(
            operation="data.economic_calendar.economic_event_store.query",
            request_id=kwargs["request_id"],
            start_time=data_start_time(),
            data=events,
        )


def test_get_economic_events_defensively_filters_provider_rows() -> None:
    """Service applies currency and impact filters even if a provider ignores them."""
    provider = _Provider(
        (
            _event(scheduled_at=_AT),
            _event(
                scheduled_at=_AT + timedelta(days=2),
                currency="EUR",
                impact=EventImpact.LOW,
            ),
        )
    )

    events = _unwrap(
        asyncio.run(
            get_economic_events(
                _AT - timedelta(hours=1),
                _AT + timedelta(hours=1),
                provider=provider,
                store=_Store(),
                currencies=("USD",),
                minimum_impact=EventImpact.HIGH,
            )
        )
    )

    assert len(events) == 1
    assert events[0].currency == "USD"


def test_get_symbol_events_accepts_currency_match_without_country() -> None:
    """EURUSD accepts a USD row even when the scraper cannot infer a country."""
    provider = _Provider((_event(scheduled_at=_AT),))

    events = _unwrap(
        asyncio.run(
            get_symbol_economic_events(
                "EURUSD",
                _AT - timedelta(hours=1),
                _AT + timedelta(hours=1),
                provider=provider,
                store=_Store(),
            )
        )
    )

    assert len(events) == 1
    assert provider.currencies == ("EUR", "USD")
    assert provider.countries == ("EU", "US")


def test_news_restriction_includes_exact_before_boundary() -> None:
    """An event exactly minutes_before ahead is included and blocks."""
    provider = _Provider((_event(scheduled_at=_AT + timedelta(minutes=10)),))

    restricted = _unwrap(
        asyncio.run(
            is_news_restricted(
                "EURUSD",
                _AT,
                provider=provider,
                store=_Store(),
                minutes_before=10,
                minutes_after=5,
            )
        )
    )

    assert restricted is True
    assert provider.calls[0][1] > _AT + timedelta(minutes=10)


def test_service_rejects_non_utc_window() -> None:
    """Public retrieval fails closed for timezone-naive boundaries."""
    with pytest.raises(DataError):
        _unwrap(
            asyncio.run(
                get_economic_events(
                    _AT.replace(tzinfo=None),
                    _AT + timedelta(hours=1),
                    provider=_Provider(()),
                )
            )
        )


def test_complete_database_coverage_prevents_provider_call() -> None:
    """Complete stored coverage is returned without external acquisition."""
    event = _event(scheduled_at=_AT)
    provider = _Provider(())
    store = _Store((event,), covered=True)

    events = _unwrap(
        asyncio.run(
            get_economic_events(
                _AT - timedelta(hours=1),
                _AT + timedelta(hours=1),
                provider=provider,
                store=store,
            )
        )
    )

    assert events == [event]
    assert provider.calls == []
    assert store.queries == 1
