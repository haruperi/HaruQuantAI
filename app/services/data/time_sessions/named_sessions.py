"""Analytical named-session classification kept separate from tradability."""

from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.time_sessions.contracts import (
    ActiveMarketSessions,
    ActiveMarketSessionsRequest,
    NamedSessionDefinition,
)
from app.utils import logger

FOREX_NAMED_SESSIONS = (
    NamedSessionDefinition(
        name="Sydney",
        timezone="Australia/Sydney",
        opens_at=time(8),
        closes_at=time(17),
    ),
    NamedSessionDefinition(
        name="Tokyo",
        timezone="Asia/Tokyo",
        opens_at=time(9),
        closes_at=time(18),
    ),
    NamedSessionDefinition(
        name="London",
        timezone="Europe/London",
        opens_at=time(8),
        closes_at=time(17),
    ),
    NamedSessionDefinition(
        name="New York",
        timezone="America/New_York",
        opens_at=time(8),
        closes_at=time(17),
    ),
)


def _get_active_market_sessions_raw(
    request: ActiveMarketSessionsRequest,
    *,
    definitions: tuple[NamedSessionDefinition, ...] = FOREX_NAMED_SESSIONS,
) -> ActiveMarketSessions:
    """Return analytical labels active at an aware UTC instant.

    These labels describe regional liquidity only and do not authorize orders.

    Args:
        request: Symbol, UTC evaluation instant, and trace identity.
        definitions: Explicit regional definitions to classify.

    Returns:
        Active labels in configured order.

    Raises:
        DataError: If a configured timezone is unavailable.
    """
    logger.info("Classifying analytical market sessions for %s", request.symbol)
    active: list[str] = []
    for definition in definitions:
        try:
            local_time = request.at.astimezone(ZoneInfo(definition.timezone)).time()
        except ZoneInfoNotFoundError as error:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "definitions.timezone"},
                request_id=request.request_id,
            ) from error
        if _contains(
            local_time,
            opens_at=definition.opens_at,
            closes_at=definition.closes_at,
        ):
            active.append(definition.name)
    return ActiveMarketSessions(
        symbol=request.symbol,
        checked_at=request.at,
        sessions=tuple(active),
        request_id=request.request_id,
    )


def get_active_market_sessions(
    request: ActiveMarketSessionsRequest,
    *,
    definitions: tuple[NamedSessionDefinition, ...] = FOREX_NAMED_SESSIONS,
) -> StandardResponse[ActiveMarketSessions]:
    """Return analytical labels active at an aware UTC instant.

    These labels describe regional liquidity only and do not authorize orders.

    Args:
        request: Symbol, UTC evaluation instant, and trace identity.
        definitions: Explicit regional definitions to classify.

    Returns:
        Standard response carrying active labels in configured order.

    Raises:
        (in-band) ``INVALID_INPUT`` if a configured timezone is unavailable.
    """
    return run_data_operation(
        operation="data.time_sessions.get_active_market_sessions",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _get_active_market_sessions_raw(request, definitions=definitions),
    )


def _contains(value: time, *, opens_at: time, closes_at: time) -> bool:
    """Return whether a wall time lies in a possibly cross-midnight interval.

    Args:
        value: Local wall time to classify.
        opens_at: Inclusive opening time.
        closes_at: Exclusive closing time.

    Returns:
        Whether the interval contains ``value``.
    """
    if opens_at < closes_at:
        return opens_at <= value < closes_at
    return value >= opens_at or value < closes_at


__all__ = ["FOREX_NAMED_SESSIONS", "get_active_market_sessions"]
