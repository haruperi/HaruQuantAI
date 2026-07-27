"""Public async economic-calendar service for FEAT-DATA-11.

Section 5 of the design declares the public service surface for retrieving
normalized economic events: ``get_economic_events`` and
``get_symbol_economic_events``, plus ``is_news_restricted`` from section 6.
These functions delegate to an injected `EconomicCalendarProvider` (and
optionally to a persistent `EconomicEventStore`); callers wire the provider,
the functions stay pure and async.

The functions are async because provider access is intrinsically awaitable
even when synchronously testable transports are used.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.services.data.contracts import DataError
from app.services.data.economic_calendar.calendar_state import (
    DEFAULT_MINIMUM_IMPACT,
)
from app.services.data.economic_calendar.profiling import get_symbol_event_profile
from app.services.data.economic_calendar.restriction import (
    is_news_restricted_events,
)
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
    from app.services.data.economic_calendar.providers import EconomicCalendarProvider
    from app.services.data.economic_calendar.store import EconomicEventStore


def _require_aware(name: str, value: datetime) -> datetime:
    """Validate one window bound is timezone-aware UTC."""
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise DataError("VALIDATION_FAILED", safe_details={"field": name})
    return value


def _matches_scope(
    event: EconomicEvent,
    currencies: Sequence[str] | None,
    countries: Sequence[str] | None,
) -> bool:
    """Return whether a normalized event matches any supplied scope filter."""
    if currencies is None and countries is None:
        return True
    return bool(
        (
            currencies is not None
            and event.currency is not None
            and event.currency in currencies
        )
        or (
            countries is not None
            and event.country is not None
            and event.country in countries
        )
    )


async def get_economic_events(
    start: datetime,
    end: datetime,
    *,
    provider: EconomicCalendarProvider,
    currencies: Sequence[str] | None = None,
    countries: Sequence[str] | None = None,
    minimum_impact: EventImpact | None = None,
) -> list[EconomicEvent]:
    """Retrieve normalized economic events for a UTC window.

    Args:
        start: Inclusive timezone-aware UTC window start.
        end: Exclusive timezone-aware UTC window end.
        provider: Injected economic-calendar provider.
        currencies: Optional currency filter.
        countries: Optional country filter.
        minimum_impact: Optional minimum-impact filter.

    Returns:
        Normalized economic events matching the supplied filters.

    Raises:
        DataError: If the window is invalid or the provider fails.
    """
    _require_aware("start", start)
    _require_aware("end", end)
    if start >= end:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
    logger.info(
        "Retrieving economic events for window [%s, %s)",
        start.isoformat(),
        end.isoformat(),
    )
    events = await provider.get_events(
        start,
        end,
        currencies=currencies,
        countries=countries,
        minimum_impact=minimum_impact,
    )
    return [
        event
        for event in events
        if start <= event.scheduled_at < end
        and _matches_scope(event, currencies, countries)
        and (minimum_impact is None or event.impact >= minimum_impact)
    ]


async def get_symbol_economic_events(
    symbol: str,
    start: datetime,
    end: datetime,
    *,
    provider: EconomicCalendarProvider,
    minimum_impact: EventImpact | None = None,
) -> list[EconomicEvent]:
    """Retrieve economic events relevant to one tradable symbol.

    Args:
        symbol: Canonical tradable symbol (must have a registered profile).
        start: Inclusive timezone-aware UTC window start.
        end: Exclusive timezone-aware UTC window end.
        provider: Injected economic-calendar provider.
        minimum_impact: Optional minimum-impact filter.

    Returns:
        Normalized economic events relevant to the symbol.

    Raises:
        DataError: If the symbol/profile is unknown or the window is invalid.
    """
    profile = get_symbol_event_profile(symbol)
    _require_aware("start", start)
    _require_aware("end", end)
    if start >= end:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
    logger.info(
        "Retrieving symbol economic events for %s over [%s, %s)",
        symbol,
        start.isoformat(),
        end.isoformat(),
    )
    return await get_economic_events(
        start,
        end,
        provider=provider,
        currencies=tuple(sorted(profile.currencies)),
        countries=tuple(sorted(profile.countries)),
        minimum_impact=minimum_impact,
    )


async def is_news_restricted(
    symbol: str,
    at: datetime,
    *,
    provider: EconomicCalendarProvider,
    minutes_before: int = 10,
    minutes_after: int = 10,
    minimum_impact: EventImpact = DEFAULT_MINIMUM_IMPACT,
) -> bool:
    """Return True when ``at`` falls inside a relevant news-window for ``symbol``.

    Mirrors section 6 of the design. The system-trading path normally realizes
    news-block through the Risk calendar gate; this public function is provided
    for callers (advisory checks, tooling, simulators) that need a direct check
    against the same normalized event source.

    Args:
        symbol: Canonical tradable symbol (must have a registered profile).
        at: Timezone-aware UTC instant.
        provider: Injected economic-calendar provider.
        minutes_before: Blackout minutes before each release.
        minutes_after: Blackout minutes after each release.
        minimum_impact: Minimum impact to consider. Defaults to HIGH.

    Returns:
        True when ``at`` falls inside any blocking window for the symbol.

    Raises:
        ValueError: If ``at`` is timezone-naive.
        DataError: If the symbol is unknown or retrieval fails.
    """
    if at.tzinfo is None or at.utcoffset() != timedelta(0):
        raise ValueError("at must be timezone-aware UTC")
    if minutes_before < 0 or minutes_after < 0:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "minutes"})
    window_start = at - timedelta(minutes=max(minutes_before, minutes_after))
    window_end = at + timedelta(
        minutes=max(minutes_before, minutes_after),
        microseconds=1,
    )
    events = await get_symbol_economic_events(
        symbol,
        window_start,
        window_end,
        provider=provider,
        minimum_impact=minimum_impact,
    )
    return is_news_restricted_events(
        events,
        at,
        minutes_before=minutes_before,
        minutes_after=minutes_after,
        minimum_impact=minimum_impact,
    )


def get_persisted_events(
    start: datetime,
    end: datetime,
    *,
    store: EconomicEventStore,
    currencies: Sequence[str] | None = None,
    countries: Sequence[str] | None = None,
    minimum_impact: EventImpact | None = None,
    provider: str | None = None,
    request_id: str | None = None,
) -> list[EconomicEvent]:
    """Synchronous read-only accessor over one stored economic-event set.

    Convenience wrapper around `EconomicEventStore.query` for callers that do
    not need provider refresh (e.g. advisory dashboards, research). The async
    service functions above remain the canonical retrieval surface.

    Args:
        start: Inclusive timezone-aware UTC window start.
        end: Exclusive timezone-aware UTC window end.
        store: Injected economic-event store.
        currencies: Optional currency filter.
        countries: Optional country filter.
        minimum_impact: Optional minimum-impact filter.
        provider: Optional provider filter.
        request_id: Optional trace correlation id.

    Returns:
        Chronologically ordered events matching the supplied filters.

    Raises:
        DataError: If the window is invalid or the read fails.
    """
    _require_aware("start", start)
    _require_aware("end", end)
    return store.query(
        start,
        end,
        currencies=currencies,
        countries=countries,
        minimum_impact=minimum_impact,
        provider=provider,
        request_id=request_id,
    )


__all__ = [
    "get_economic_events",
    "get_persisted_events",
    "get_symbol_economic_events",
    "is_news_restricted",
]
