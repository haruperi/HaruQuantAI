"""Current configured market hours and normalized session windows.

Moved from ``gateway/sessions.py`` by ``CAP-DATA-026``. The volume half of that module
went to ``retrieval/discovery.py`` in Phase 4; what remains here is temporal truth.

**Historical reconstruction is deliberately unsupported.** ``get_current_schedule``
returns the *currently configured* schedule and raises ``UNSUPPORTED_OPERATION`` for a
past date. Reconstructing what a venue's hours were on a given historical day requires
a calendar provider the system does not have, and guessing would produce evidence that
looks authoritative and is not.

``MarketCalendar`` is declared here as a Protocol. ``sources/composition`` implements it
structurally and imports it under ``TYPE_CHECKING`` only, so the two modules form no
runtime cycle.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol

from app.services.data.contracts import DataError
from app.services.data.contracts.validation import (
    reject_mixed_call_styles as _reject_mixed,
)
from app.services.data.contracts.validation import (
    require_direct_value as _required,
)
from app.services.data.contracts.validation import (
    resolve_request_id as _request_id,
)
from app.services.data.sources.composition import ensure_source, resolve_calendar
from app.services.data.sources.registry import get_source_descriptor
from app.services.data.time_sessions.contracts import MarketSchedule, ScheduleRequest
from app.utils import Clock, logger, utc_now


class MarketCalendar(Protocol):
    """Injected authoritative current-session calendar boundary."""

    def get_schedule(
        self,
        *,
        source_id: str,
        symbol: str,
        timezone: str,
        observed_at: datetime,
        request_id: str,
    ) -> MarketSchedule:
        """Return versioned provider/exchange schedule evidence."""
        ...


def get_current_schedule(
    request: ScheduleRequest,
    calendar: MarketCalendar,
    *,
    clock: Clock | None = None,
) -> MarketSchedule:
    """Return current configured hours and normalized UTC sessions.

    Advances cross-midnight windows correctly and rejects historical reconstruction.

    Args:
        request: Schedule details request.
        calendar: Caller-injected authoritative schedule provider.
        clock: Optional injected UTC clock.

    Returns:
        The MarketSchedule details.

    Raises:
        DataError: On missing, invalid, or unavailable schedule evidence.
    """
    logger.info(
        "Getting current schedule for %s on %s (Request: %s)",
        request.symbol,
        request.source_id,
        request.request_id,
    )

    desc = get_source_descriptor(request.source_id)
    if desc.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"source_id": request.source_id},
            request_id=request.request_id,
        )
    observed_at = utc_now(clock)
    try:
        schedule = calendar.get_schedule(
            source_id=request.source_id,
            symbol=request.symbol,
            timezone=request.timezone,
            observed_at=observed_at,
            request_id=request.request_id,
        )
    except DataError:
        raise
    except Exception as error:
        logger.error("Authoritative market-calendar query failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "market_calendar"},
            request_id=request.request_id,
        ) from error
    if (
        schedule.source_id != request.source_id
        or schedule.symbol != request.symbol
        or schedule.timezone != request.timezone
        or schedule.request_id != request.request_id
        or schedule.observed_at != observed_at
    ):
        raise DataError(
            "STALE_EVIDENCE",
            safe_details={"operation": "market_calendar"},
            request_id=request.request_id,
        )
    return schedule


def schedule_request(
    request: ScheduleRequest | None,
    *,
    view: Literal["hours", "sessions"],
    source_id: str | None,
    symbol: str | None,
    timezone: str | None,
    request_id: str | None,
) -> ScheduleRequest:
    """Return a typed schedule request from either supported call style.

    Raises:
        DataError: If call styles are mixed or validation fails.
    """
    trace_id = request.request_id if request is not None else _request_id(request_id)
    _reject_mixed(request, (source_id, symbol, timezone), trace_id)
    if request is not None:
        if request.view != view:
            operation = (
                "get_market_hours" if view == "hours" else "get_trading_sessions"
            )
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={
                    "message": (
                        f"{operation} requires {view} view, got '{request.view}'"
                    )
                },
                request_id=trace_id,
            )
        return request

    resolved_source_id = _required(source_id, "source_id", trace_id)
    resolved_symbol = _required(symbol, "symbol", trace_id)

    return ScheduleRequest(
        source_id=resolved_source_id,
        symbol=resolved_symbol,
        view=view,
        timezone=timezone if timezone is not None else "UTC",
        request_id=trace_id,
    )


# --- Public session operations ---


def get_market_hours(
    request: ScheduleRequest | None = None,
    calendar: MarketCalendar | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    timezone: str | None = None,
    request_id: str | None = None,
) -> MarketSchedule:
    """Retrieve market hours using a request or direct keywords.

    Returns:
        The current authoritative market schedule.
    """
    logger.info("Executing public DATA market-hours query")
    resolved = schedule_request(
        request,
        view="hours",
        source_id=source_id,
        symbol=symbol,
        timezone=timezone,
        request_id=request_id,
    )
    selected_calendar = calendar or resolve_calendar(
        resolved.source_id,
        resolved.request_id,
    )
    ensure_source(resolved.source_id, resolved.request_id)
    return get_current_schedule(resolved, selected_calendar)


def get_trading_sessions(
    request: ScheduleRequest | None = None,
    calendar: MarketCalendar | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    timezone: str | None = None,
    request_id: str | None = None,
) -> MarketSchedule:
    """Retrieve trading sessions using a request or direct keywords.

    Returns:
        The current authoritative trading-session schedule.
    """
    logger.info("Executing public DATA trading-session query")
    resolved = schedule_request(
        request,
        view="sessions",
        source_id=source_id,
        symbol=symbol,
        timezone=timezone,
        request_id=request_id,
    )
    selected_calendar = calendar or resolve_calendar(
        resolved.source_id,
        resolved.request_id,
    )
    ensure_source(resolved.source_id, resolved.request_id)
    return get_current_schedule(resolved, selected_calendar)


__all__ = [
    "MarketCalendar",
    "get_current_schedule",
    "get_market_hours",
    "get_trading_sessions",
    "schedule_request",
]
