"""Exchange-calendar session retrieval using explicit venue identifiers."""

from datetime import UTC, datetime, timedelta
from importlib import import_module

from app.composition.logging import get_logger
from app.services.data._limits import get_limit
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.time_sessions.contracts import (
    ExchangeSessionRequest,
    TradingSession,
)

logger = get_logger(__name__)


def _get_exchange_sessions_raw(
    request: ExchangeSessionRequest,
) -> tuple[TradingSession, ...]:
    """Return exchange-authoritative regular sessions in an inclusive date range.

    Args:
        request: Explicit symbol, calendar code, date range, and trace identity.

    Returns:
        Ordered venue sessions with UTC boundaries.

    Raises:
        DataError: If the range is too large or the calendar cannot be resolved.
    """
    days = (request.end - request.start).days + 1
    if days > get_limit("MARKET_SESSION_MAX_DAYS"):
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={"limit": "MARKET_SESSION_MAX_DAYS"},
            request_id=request.request_id,
        )
    logger.info(
        "Reading exchange sessions for %s from explicit calendar %s",
        request.symbol,
        request.calendar_code,
    )
    try:
        xcals = import_module("exchange_calendars")
        registered = xcals.get_calendar(request.calendar_code)
        calendar = type(registered)(
            start=request.start - timedelta(days=1),
            end=request.end + timedelta(days=1),
        )
        schedule = calendar.schedule
        selected = schedule[
            (schedule.index.date >= request.start)
            & (schedule.index.date <= request.end)
        ]
        sessions = tuple(
            TradingSession(
                symbol=request.symbol,
                opens_at=_as_utc(row["open"].to_pydatetime()),
                closes_at=_as_utc(row["close"].to_pydatetime()),
                source=f"exchange:{request.calendar_code}",
                label=str(label.date()),
            )
            for label, row in selected.iterrows()
        )
    except Exception as error:
        logger.exception("Exchange calendar query failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "exchange_calendar"},
            request_id=request.request_id,
        ) from error
    return sessions


def get_exchange_sessions(
    request: ExchangeSessionRequest,
) -> StandardResponse[tuple[TradingSession, ...]]:
    """Return exchange-authoritative regular sessions in an inclusive date range.

    Args:
        request: Explicit symbol, calendar code, date range, and trace identity.

    Returns:
        Standard response carrying ordered venue sessions with UTC boundaries.

    Raises:
        (in-band) ``LIMIT_EXCEEDED`` if the range is too large, or
        ``SOURCE_UNAVAILABLE`` if the calendar cannot be resolved.
    """
    return run_data_operation(
        operation="data.time_sessions.get_exchange_sessions",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _get_exchange_sessions_raw(request),
    )


def _as_utc(value: datetime) -> datetime:
    """Normalize one library timestamp to aware UTC.

    Args:
        value: Calendar timestamp.

    Returns:
        Aware UTC datetime.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = ["get_exchange_sessions"]
