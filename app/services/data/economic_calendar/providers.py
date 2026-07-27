"""Economic-calendar provider Protocol and one concrete adapter for FEAT-DATA-11.

`EconomicCalendarProvider` is the broker-neutral retrieval boundary for
economic events. Concrete providers (e.g. ``CalendarScrapeProvider`` here,
an MT5 bridge in the future) translate it into normalized `EconomicEvent`
records without leaking provider-specific dictionaries across the boundary.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Protocol

from app.services.data.contracts import DataError
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.scraper import (
    CALENDAR_SITES,
    CalendarEvent,
    CalendarTransport,
    ScrapeOptions,
    ScrapeResult,
    scrape_economic_calendar,
)

#: Map of ISO-3166-1 alpha-2 country code to the single dominant currency.
#: Providers that already publish a currency are trusted verbatim; this table
#: only fills in the currency for scrapers that only carry a country code.
#: ForexFactory and the other broker-neutral scrapers actually publish a
#: *currency code* (USD, EUR, GBP, ...) in their per-row country slot, so we
#: also accept a 3-letter ISO-4217 currency directly in that field.
_COUNTRY_CURRENCY: dict[str, str] = {
    "US": "USD",
    "EU": "EUR",
    "DE": "EUR",
    "FR": "EUR",
    "GB": "GBP",
    "JP": "JPY",
    "CH": "CHF",
    "CA": "CAD",
    "AU": "AUD",
    "NZ": "NZD",
    "CN": "CNY",
}

#: Recognized ISO-4217 currency codes; when the scraped "country" slot is one
#: of these, the provider is actually publishing the currency directly.
_KNOWN_CURRENCIES: frozenset[str] = frozenset(_COUNTRY_CURRENCY.values()) | frozenset(
    {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "CNY"}
)

#: Map of scraped ``CalendarEvent.impact`` literal to normalized `EventImpact`.
_IMPACT_MAP: dict[str, EventImpact] = {
    "low": EventImpact.LOW,
    "medium": EventImpact.MEDIUM,
    "high": EventImpact.HIGH,
    "holiday": EventImpact.LOW,
}


class EconomicCalendarProvider(Protocol):
    """Broker-neutral economic-calendar retrieval boundary."""

    async def get_events(
        self,
        start: datetime,
        end: datetime,
        *,
        currencies: Sequence[str] | None = None,
        countries: Sequence[str] | None = None,
        minimum_impact: EventImpact | None = None,
    ) -> list[EconomicEvent]:
        """Return normalized economic events for a UTC window.

        Args:
            start: Inclusive timezone-aware UTC window start.
            end: Exclusive timezone-aware UTC window end.
            currencies: Optional filter; events whose currency is in the set.
            countries: Optional filter; events whose country is in the set.
            minimum_impact: Optional filter; events with at least this impact.

        Returns:
            Normalized economic events satisfying the supplied filters.

        Raises:
            DataError: If retrieval fails or the requested window is invalid.
        """
        ...


def _matches_scope(
    event: EconomicEvent,
    currencies: Sequence[str] | None,
    countries: Sequence[str] | None,
) -> bool:
    """Return whether an event matches any supplied relevance dimension."""
    if currencies is None and countries is None:
        return True
    currency_match = (
        currencies is not None
        and event.currency is not None
        and event.currency in currencies
    )
    country_match = (
        countries is not None
        and event.country is not None
        and event.country in countries
    )
    return currency_match or country_match


def _currency_for(country: str | None, currency: str | None) -> str | None:
    """Return the trusted currency, the slot's currency alias, or the dominant one."""
    if currency:
        return currency
    if country is None:
        return None
    if country in _KNOWN_CURRENCIES:
        # ForexFactory / MetalsMine / EnergyExch / CryptoCraft publish a
        # currency code ("USD", "EUR", ...) in the per-row country slot.
        return country
    return _COUNTRY_CURRENCY.get(country)


def _event_id(event: CalendarEvent) -> str:
    """Return the provider-stable event identifier."""
    return event.provider_event_id


def _unit(*values: str | None) -> str | None:
    """Infer a provider unit suffix without changing the raw representation."""
    for value in values:
        if value is None:
            continue
        normalized = value.rstrip()
        if normalized.endswith("%"):
            return "%"
        if normalized[-1:] in {"K", "k", "M", "m", "B", "b"}:
            return normalized[-1].upper()
    return None


def _normalize(site: str, event: CalendarEvent) -> EconomicEvent:
    """Map one scraped `CalendarEvent` to a normalized `EconomicEvent`."""
    raw_country = event.country or None
    # Some portals put the currency code (USD, EUR) in the country slot. We
    # detect that and split it back out: a real currency code populates
    # `currency` but leaves `country=None` (we don't invent an ISO country).
    currency: str | None
    if raw_country is not None and raw_country in _KNOWN_CURRENCIES:
        currency = raw_country
        country: str | None = None
    else:
        country = raw_country
        currency = _currency_for(country, None)
    impact = _IMPACT_MAP.get(event.impact, EventImpact.LOW)
    return EconomicEvent(
        id=_event_id(event),
        provider=f"scrape:{site}",
        name=event.title,
        category=None,
        country=country,
        currency=currency,
        scheduled_at=event.timestamp,
        impact=impact,
        actual=event.actual,
        forecast=event.forecast,
        previous=event.previous,
        revised_previous=None,
        # The legacy scraper already converts ``216K`` -> ``Decimal(216000)``,
        # so the original provider raw string is not recoverable here. Provider
        # implementations that retain the raw text (e.g. a future MQL5 bridge)
        # should populate ``actual_raw``/``forecast_raw``/``previous_raw``.
        actual_raw=event.actual_raw,
        forecast_raw=event.forecast_raw,
        previous_raw=event.previous_raw,
        unit=_unit(event.actual_raw, event.forecast_raw, event.previous_raw),
        source=site,
        source_url=None,
        updated_at=None,
    )


class CalendarScrapeProvider:
    """`EconomicCalendarProvider` backed by the existing multi-site scraper.

    The provider adapts the legacy `scrape_economic_calendar` pipeline
    (injected `CalendarTransport`) so callers can request normalized
    `EconomicEvent` values without touching the scrape/clean/dedup
    implementation. Network access is supplied by ``transport`` exactly as
    for the raw scraper — deterministically testable.
    """

    def __init__(
        self,
        transport: CalendarTransport,
        *,
        sites: Sequence[str] = CALENDAR_SITES,
        max_parallel_tasks: int = 4,
        request_id: str | None = None,
    ) -> None:
        """Initialize one scrape-backed calendar provider.

        Args:
            transport: Injected read-only calendar transport.
            sites: Sites to scrape. Defaults to all broker-neutral sites.
            max_parallel_tasks: Bounded scrape concurrency.
            request_id: Optional trace correlation id.
        """
        self._transport = transport
        self._sites = tuple(sites)
        self._max_parallel_tasks = max_parallel_tasks
        self._request_id = request_id

    async def _scrape(self, start: datetime, end: datetime) -> ScrapeResult:
        """Run the legacy synchronous scraper on a fresh event loop."""
        options = ScrapeOptions(
            start=start,
            end=end,
            sites=self._sites,
            max_parallel_tasks=self._max_parallel_tasks,
            request_id=self._request_id,
            transport=self._transport,
        )
        # `scrape_economic_calendar` uses `asyncio.run` internally; if this
        # provider is awaited from a running loop, that path raises. Run it in
        # a worker thread to keep the awaitable contract honest in either
        # context while reusing the legacy synchronous entry point verbatim.
        return await asyncio.to_thread(scrape_economic_calendar, options)

    async def get_events(
        self,
        start: datetime,
        end: datetime,
        *,
        currencies: Sequence[str] | None = None,
        countries: Sequence[str] | None = None,
        minimum_impact: EventImpact | None = None,
    ) -> list[EconomicEvent]:
        """Retrieve and normalize calendar events for the supplied window."""
        if (
            start.tzinfo is None
            or end.tzinfo is None
            or start.utcoffset() != timedelta(0)
            or end.utcoffset() != timedelta(0)
            or start >= end
        ):
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "window"},
            )
        result = await self._scrape(start, end)
        events: list[EconomicEvent] = []
        for scraped in result.events:
            normalized = _normalize(scraped.site, scraped)
            if not start <= normalized.scheduled_at < end:
                continue
            if not _matches_scope(normalized, currencies, countries):
                continue
            if minimum_impact is not None and normalized.impact < minimum_impact:
                continue
            events.append(normalized)
        return events


__all__ = [
    "CalendarScrapeProvider",
    "EconomicCalendarProvider",
]
