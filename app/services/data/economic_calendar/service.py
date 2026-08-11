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

import hashlib
import json
from collections.abc import Coroutine, Sequence
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
    run_data_operation_async,
    unwrap_data_response,
)
from app.services.data.economic_calendar.calendar_state import (
    DEFAULT_MINIMUM_IMPACT,
)
from app.services.data.economic_calendar.profiling import (
    _get_symbol_event_profile_raw,
)
from app.services.data.economic_calendar.restriction import (
    _is_news_restricted_events_raw,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
    from app.services.data.economic_calendar.providers import EconomicCalendarProvider
    from app.services.data.economic_calendar.store import EconomicEventStore


def _default_store() -> EconomicEventStore:
    """Construct the internal database-backed event store lazily.

    Returns:
        The result produced by the operation.
    """
    from app.services.data.economic_calendar.store import EconomicEventStore

    return EconomicEventStore()


def _require_aware(name: str, value: datetime) -> datetime:
    """Validate one window bound is timezone-aware UTC.

    Args:
        name: The ``name`` argument.
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise DataError("VALIDATION_FAILED", safe_details={"field": name})
    return value


def _matches_scope(
    event: EconomicEvent,
    currencies: Sequence[str] | None,
    countries: Sequence[str] | None,
) -> bool:
    """Return whether a normalized event matches any supplied scope filter.

    Args:
        event: The ``event`` argument.
        currencies: The ``currencies`` argument.
        countries: The ``countries`` argument.

    Returns:
        The result produced by the operation.
    """
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


async def _get_economic_events_raw(
    start: datetime,
    end: datetime,
    *,
    provider: EconomicCalendarProvider,
    store: EconomicEventStore | None = None,
    currencies: Sequence[str] | None = None,
    countries: Sequence[str] | None = None,
    minimum_impact: EventImpact | None = None,
    request_id: str | None = None,
) -> list[EconomicEvent]:
    """Retrieve normalized economic events for a UTC window.

    Args:
        start: The ``start`` argument.
        end: The ``end`` argument.
        provider: The ``provider`` argument.
        store: The ``store`` argument.
        currencies: The ``currencies`` argument.
        countries: The ``countries`` argument.
        minimum_impact: The ``minimum_impact`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the window is invalid or the provider fails.
    """
    _require_aware("start", start)
    _require_aware("end", end)
    if start >= end:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
    logger.info(
        "Querying economic-event database for window [%s, %s)",
        start.isoformat(),
        end.isoformat(),
    )
    active_request_id = request_id or generate_id("req")
    active_store = store or _default_store()
    for gap_start, gap_end in active_store.missing_intervals(
        start, end, request_id=active_request_id
    ):
        logger.info(
            "Acquiring missing economic-event interval [%s, %s)",
            gap_start.isoformat(),
            gap_end.isoformat(),
        )
        provider_result = await provider.get_events(
            gap_start,
            gap_end,
            currencies=currencies,
            countries=countries,
            minimum_impact=minimum_impact,
        )
        acquired = (
            provider_result
            if isinstance(provider_result, list)
            else cast(
                "list[EconomicEvent]",
                unwrap_data_response(
                    provider_result,
                    operation="data.economic_calendar.get_economic_events",
                    request_id=active_request_id,
                ),
            )
        )
        accepted = [
            event
            for event in acquired
            if gap_start <= event.scheduled_at < gap_end
            and _matches_scope(event, currencies, countries)
            and (minimum_impact is None or event.impact >= minimum_impact)
        ]
        unwrap_data_response(
            active_store.upsert(accepted, request_id=active_request_id),
            operation="data.economic_calendar.persist_gap",
            request_id=active_request_id,
        )
        revision = hashlib.sha256(
            json.dumps(sorted((event.provider, event.id) for event in accepted)).encode(
                "utf-8"
            )
        ).hexdigest()
        active_store.record_coverage(
            gap_start,
            gap_end,
            provider="economic-calendar-provider",
            source_revision=revision,
            request_id=active_request_id,
        )
    return unwrap_data_response(
        active_store.query(
            start,
            end,
            currencies=currencies,
            countries=countries,
            minimum_impact=minimum_impact,
            request_id=active_request_id,
        ),
        operation="data.economic_calendar.query_persisted",
        request_id=active_request_id,
    )


async def get_economic_events(
    start: datetime,
    end: datetime,
    *,
    provider: EconomicCalendarProvider,
    store: EconomicEventStore | None = None,
    currencies: Sequence[str] | None = None,
    countries: Sequence[str] | None = None,
    minimum_impact: EventImpact | None = None,
) -> StandardResponse[list[EconomicEvent]]:
    """Retrieve normalized economic events for a UTC window.

    Args:
        start: Inclusive timezone-aware UTC window start.
        end: Exclusive timezone-aware UTC window end.
        provider: Injected economic-calendar provider.
        store: Optional injected database store; defaults to the Data store.
        currencies: Optional currency filter.
        countries: Optional country filter.
        minimum_impact: Optional minimum-impact filter.

    Returns:
        Standard response carrying the normalized economic events matching
        the supplied filters.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when the window is invalid, plus
            ``DataError`` codes when the provider fails.
    """
    request_id = generate_id("req")
    return await run_data_operation_async(
        operation="data.economic_calendar.get_economic_events",
        request_id=request_id,
        start_time=data_start_time(),
        raw=lambda: _get_economic_events_raw(
            start,
            end,
            provider=provider,
            store=store,
            currencies=currencies,
            countries=countries,
            minimum_impact=minimum_impact,
            request_id=request_id,
        ),
    )


async def _get_symbol_economic_events_raw(
    symbol: str,
    start: datetime,
    end: datetime,
    *,
    provider: EconomicCalendarProvider,
    store: EconomicEventStore | None = None,
    minimum_impact: EventImpact | None = None,
    request_id: str | None = None,
) -> list[EconomicEvent]:
    """Retrieve economic events relevant to one tradable symbol.

    Args:
        symbol: The ``symbol`` argument.
        start: The ``start`` argument.
        end: The ``end`` argument.
        provider: The ``provider`` argument.
        store: The ``store`` argument.
        minimum_impact: The ``minimum_impact`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the symbol/profile is unknown or the window is invalid.
    """
    profile = _get_symbol_event_profile_raw(symbol)
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
    return await _get_economic_events_raw(
        start,
        end,
        provider=provider,
        store=store,
        currencies=tuple(sorted(profile.currencies)),
        countries=tuple(sorted(profile.countries)),
        minimum_impact=minimum_impact,
        request_id=request_id,
    )


async def get_symbol_economic_events(
    symbol: str,
    start: datetime,
    end: datetime,
    *,
    provider: EconomicCalendarProvider,
    store: EconomicEventStore | None = None,
    minimum_impact: EventImpact | None = None,
) -> StandardResponse[list[EconomicEvent]]:
    """Retrieve economic events relevant to one tradable symbol.

    Args:
        symbol: Canonical tradable symbol (must have a registered profile).
        start: Inclusive timezone-aware UTC window start.
        end: Exclusive timezone-aware UTC window end.
        provider: Injected economic-calendar provider.
        store: Optional injected database store; defaults to the Data store.
        minimum_impact: Optional minimum-impact filter.

    Returns:
        Standard response carrying the normalized economic events relevant
        to the symbol.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when the symbol/profile is unknown or
            the window is invalid.
    """
    request_id = generate_id("req")
    return await run_data_operation_async(
        operation="data.economic_calendar.get_symbol_economic_events",
        request_id=request_id,
        start_time=data_start_time(),
        raw=lambda: _get_symbol_economic_events_raw(
            symbol,
            start,
            end,
            provider=provider,
            store=store,
            minimum_impact=minimum_impact,
            request_id=request_id,
        ),
    )


async def _is_news_restricted_raw(
    symbol: str,
    at: datetime,
    *,
    provider: EconomicCalendarProvider,
    store: EconomicEventStore | None = None,
    minutes_before: int = 10,
    minutes_after: int = 10,
    minimum_impact: EventImpact = DEFAULT_MINIMUM_IMPACT,
    request_id: str | None = None,
) -> bool:
    """Return True when ``at`` falls inside a relevant news-window for ``symbol``.

    Args:
        symbol: The ``symbol`` argument.
        at: The ``at`` argument.
        provider: The ``provider`` argument.
        store: The ``store`` argument.
        minutes_before: The ``minutes_before`` argument.
        minutes_after: The ``minutes_after`` argument.
        minimum_impact: The ``minimum_impact`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

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
    events = await _get_symbol_economic_events_raw(
        symbol,
        window_start,
        window_end,
        provider=provider,
        store=store,
        minimum_impact=minimum_impact,
        request_id=request_id,
    )
    return _is_news_restricted_events_raw(
        events,
        at,
        minutes_before=minutes_before,
        minutes_after=minutes_after,
        minimum_impact=minimum_impact,
    )


async def is_news_restricted(
    symbol: str,
    at: datetime,
    *,
    provider: EconomicCalendarProvider,
    store: EconomicEventStore | None = None,
    minutes_before: int = 10,
    minutes_after: int = 10,
    minimum_impact: EventImpact = DEFAULT_MINIMUM_IMPACT,
) -> StandardResponse[bool]:
    """Return True when ``at`` falls inside a relevant news-window for ``symbol``.

    Mirrors section 6 of the design. The system-trading path normally realizes
    news-block through the Risk calendar gate; this public function is provided
    for callers (advisory checks, tooling, simulators) that need a direct check
    against the same normalized event source.

    Args:
        symbol: Canonical tradable symbol (must have a registered profile).
        at: Timezone-aware UTC instant.
        provider: Injected economic-calendar provider.
        store: Optional injected database store; defaults to the Data store.
        minutes_before: Blackout minutes before each release.
        minutes_after: Blackout minutes after each release.
        minimum_impact: Minimum impact to consider. Defaults to HIGH.

    Returns:
        Standard response carrying ``True`` when ``at`` falls inside any
        blocking window for the symbol.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when ``at`` is timezone-naive, the
            minutes are negative, or the symbol is unknown, plus ``DataError``
            codes when retrieval fails.
    """

    def _raw() -> Coroutine[Any, Any, bool]:
        """Implement raw behavior.

        Returns:
            The result produced by the operation.
        """

        async def _coro() -> bool:
            """Evaluate the asynchronous news-restriction request.

            Returns:
                Whether the supplied instant is news restricted.

            Raises:
                DataError: If the evaluation time is invalid.
            """
            try:
                return await _is_news_restricted_raw(
                    symbol,
                    at,
                    provider=provider,
                    store=store,
                    minutes_before=minutes_before,
                    minutes_after=minutes_after,
                    minimum_impact=minimum_impact,
                    request_id=request_id,
                )
            except ValueError as error:
                raise DataError(
                    "VALIDATION_FAILED", safe_details={"field": "at"}
                ) from error

        return _coro()

    request_id = generate_id("req")
    return await run_data_operation_async(
        operation="data.economic_calendar.is_news_restricted",
        request_id=request_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def _get_persisted_events_raw(
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

    Args:
        start: The ``start`` argument.
        end: The ``end`` argument.
        store: The ``store`` argument.
        currencies: The ``currencies`` argument.
        countries: The ``countries`` argument.
        minimum_impact: The ``minimum_impact`` argument.
        provider: The ``provider`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the window is invalid or the read fails.
    """
    _require_aware("start", start)
    _require_aware("end", end)
    return unwrap_data_response(
        store.query(
            start,
            end,
            currencies=currencies,
            countries=countries,
            minimum_impact=minimum_impact,
            provider=provider,
            request_id=request_id,
        ),
        operation="data.economic_calendar.get_persisted_events",
        request_id=request_id or generate_id("req"),
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
) -> StandardResponse[list[EconomicEvent]]:
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
        Standard response carrying the chronologically ordered events
        matching the supplied filters.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when the window is invalid, plus
            ``DataError`` codes when the read fails.
    """
    return run_data_operation(
        operation="data.economic_calendar.get_persisted_events",
        request_id=request_id,
        start_time=data_start_time(),
        raw=lambda: _get_persisted_events_raw(
            start,
            end,
            store=store,
            currencies=currencies,
            countries=countries,
            minimum_impact=minimum_impact,
            provider=provider,
            request_id=request_id,
        ),
    )


__all__ = [
    "get_economic_events",
    "get_persisted_events",
    "get_symbol_economic_events",
    "is_news_restricted",
]
