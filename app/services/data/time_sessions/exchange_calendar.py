"""Exchange-calendar session retrieval using explicit venue identifiers."""

from datetime import UTC, datetime, timedelta

import exchange_calendars as xcals  # type: ignore[import-untyped]

from app.services.data._limits import get_limit
from app.services.data.contracts import DataError
from app.services.data.time_sessions.contracts import (
    ExchangeSessionRequest,
    TradingSession,
)
from app.utils import logger


def get_exchange_sessions(
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
        logger.error("Exchange calendar query failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "exchange_calendar"},
            request_id=request.request_id,
        ) from error
    return sessions


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
