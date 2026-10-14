"""Shared asynchronous historical bars and tick reads.

Description:
    Validate date bounds and read-only requests over TradingBackend.call. Native
    and explicitly seeded model data share immutable records; no clock progression
    or price aggregation occurs here. Validate returned shapes before exposing data.

Purpose:
    FEAT-LIBS-DATA: Broker-neutral bounded historical data retrieval.

Key Capabilities:
    - FR-DATA-HISTORICAL-READS: Fetch chronological bars and millisecond ticks.
      Associated: `get_historical_bars()`, `get_ticks()`
      Logging: DEBUG every read attempt with operation only, no payloads or paths.
    - FR-DATA-HISTORY-VALIDATION: Reject invalid or excessive historical data.
      Associated: `validate_rows()`, `validate_request()`
      Logging: DEBUG validation attempts; errors have bounded diagnostic codes.

Python API Usage:
    ```python
    from app.services.libs.data import get_historical_bars, get_ticks

    bars = await get_historical_bars(backend, "EURUSD", Timeframe.PERIOD_M1)
    ticks = await get_ticks(backend, "EURUSD")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_trading_market_data.py --no-cov
    ```
"""

from __future__ import annotations

import math
from dataclasses import fields
from datetime import UTC, datetime
from typing import Any, Literal

from app.host.logging import get_logger
from app.services.brokers.contracts import (
    BridgeError,
    MarketBar,
    MarketTick,
    Timeframe,
    TradingBackend,
)

logger = get_logger(__name__)
MAX_RECORDS = 1000
MAX_POSITION = 2**31 - 1
READ_TIMEOUT = 60.0
TIMEFRAME_SECONDS = {
    frame: (
        int(frame.value[1:]) * 60
        if frame.value.startswith("M") and frame != Timeframe.PERIOD_MN1
        else int(frame.value[1:]) * 3600
        if frame.value.startswith("H")
        else 86400
        if frame == Timeframe.PERIOD_D1
        else 604800
        if frame == Timeframe.PERIOD_W1
        else 2419200
    )
    for frame in Timeframe
    if frame != Timeframe.PERIOD_CURRENT
}


def validate_request(
    symbol: str,
    start: int,
    end: int,
    limit: int,
    timeframe: Timeframe | None = None,
) -> None:
    """Enforce the same bounds at the shared and simulated read boundaries."""
    logger.debug("FR-DATA-HISTORY-VALIDATION: validating request")
    if not symbol or any(type(value) is not int for value in (start, end, limit)):
        raise BridgeError("invalid history request", code="BAD_REQUEST")
    if start < 0 or end < start or not 1 <= limit <= MAX_RECORDS:
        raise BridgeError("invalid history bounds or limit", code="BAD_REQUEST")
    if timeframe is None and start == 0:
        raise BridgeError("tick start must be after the epoch", code="BAD_REQUEST")
    if timeframe is not None:
        if not isinstance(timeframe, Timeframe) or timeframe not in TIMEFRAME_SECONDS:
            raise BridgeError(
                "explicit timeframe required", code="UNSUPPORTED_TIMEFRAME"
            )
        if math.ceil((end - start) / TIMEFRAME_SECONDS[timeframe]) + 1 > limit:
            raise BridgeError("narrow the bar date range", code="DATA_LIMIT_EXCEEDED")


def _bounds(start: datetime, end: datetime, scale: int) -> tuple[int, int]:
    if start.utcoffset() is None or end.utcoffset() is None or start > end:
        raise BridgeError("ordered aware dates required", code="BAD_REQUEST")
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    first, last = start.astimezone(UTC) - epoch, end.astimezone(UTC) - epoch
    first_us = (first.days * 86400 + first.seconds) * 1_000_000 + first.microseconds
    last_us = (last.days * 86400 + last.seconds) * 1_000_000 + last.microseconds
    unit = 1_000_000 // scale
    return (first_us + unit - 1) // unit, last_us // unit


def validate_rows(
    payload: Any,
    kind: Literal["bars", "ticks"],
    start: int,
    end: int,
    limit: int,
) -> list[MarketBar] | list[MarketTick]:
    """Validate immutable records and chronology, without losing integer precision."""
    logger.debug("FR-DATA-HISTORY-VALIDATION: validating rows")
    if not isinstance(payload, list) or len(payload) > limit:
        raise BridgeError("invalid history payload", code="INVALID_MARKET_DATA")
    record_type = MarketBar if kind == "bars" else MarketTick
    names = {field.name for field in fields(record_type)}
    integer_names = (
        {"time", "tick_volume", "spread", "real_volume"}
        if kind == "bars"
        else {"time_msc", "volume", "flags"}
    )
    previous: int | None = None
    result: list[Any] = []
    for row in payload:
        if not isinstance(row, dict) or set(row) != names:
            raise BridgeError("invalid history row", code="INVALID_MARKET_DATA")
        for name, value in row.items():
            valid = (
                type(value) is int and value >= 0
                if name in integer_names
                else type(value) in (int, float)
                and math.isfinite(value)
                and (name != "volume_real" or value >= 0)
            )
            if not valid:
                raise BridgeError("invalid history number", code="INVALID_MARKET_DATA")
        stamp = row["time" if kind == "bars" else "time_msc"]
        if not start <= stamp <= end or (
            previous is not None
            and (stamp <= previous if kind == "bars" else stamp < previous)
        ):
            raise BridgeError("invalid history chronology", code="INVALID_MARKET_DATA")
        if kind == "bars" and not (
            row["low"]
            <= min(row["open"], row["close"])
            <= max(row["open"], row["close"])
            <= row["high"]
        ):
            raise BridgeError("invalid OHLC values", code="INVALID_MARKET_DATA")
        previous = stamp
        result.append(record_type(**row))
    return result


def _route(
    date_from: datetime | None,
    date_to: datetime | None,
    start_pos: int | None,
    count: int | None,
    limit: int,
    *,
    scale: int,
) -> tuple[str, int, int, int]:
    if (
        type(limit) is not int
        or not 1 <= limit <= MAX_RECORDS
        or (count is not None and (type(count) is not int or not 1 <= count <= limit))
        or (
            start_pos is not None
            and (type(start_pos) is not int or not 0 <= start_pos <= MAX_POSITION)
        )
        or (date_to is not None and (date_from is None or count is not None))
        or (start_pos is not None and (date_from is not None or date_to is not None))
    ):
        raise BridgeError(
            "conflicting history selectors or invalid count", code="BAD_REQUEST"
        )
    if date_from is not None:
        if count is not None:
            lower, _ = _bounds(date_from, date_from, scale)
            return "date_count", lower, 2**63 - 1, count
        lower, upper = _bounds(date_from, date_to or datetime.now(UTC), scale)
        return "range", lower, upper, 0
    if start_pos is not None and count is None:
        if start_pos >= limit:
            raise BridgeError(
                "position range exceeds limit", code="DATA_LIMIT_EXCEEDED"
            )
        return "position", 0, 2**63 - 1, start_pos + 1
    return (
        "position" if scale == 1 else "latest",
        start_pos or 0,
        2**63 - 1,
        count or limit,
    )


async def get_historical_bars(
    backend: TradingBackend,
    symbol: str,
    timeframe: Timeframe,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    *,
    start_pos: int | None = None,
    count: int | None = None,
    limit: int = MAX_RECORDS,
) -> list[MarketBar]:
    """Read bars by date range, forward date/count or native index/count."""
    logger.debug("FR-DATA-HISTORICAL-READS: requesting bars")
    mode, start, end, number = _route(
        date_from, date_to, start_pos, count, limit, scale=1
    )
    validate_request(
        symbol,
        start if mode != "position" else 0,
        max(start, end) if mode == "range" else (start if mode == "date_count" else 0),
        limit,
        timeframe,
    )
    if mode == "range" and start > end:
        return []
    payload = await backend.call(
        object_id="market-data",
        class_name="MarketData",
        method_name="Bars",
        args=[symbol, timeframe.value, mode, start, end, number, limit],
        timeout=READ_TIMEOUT,
    )
    rows = validate_rows(
        payload, "bars", 0 if mode == "position" else start, end, number or limit
    )
    return [row for row in rows if isinstance(row, MarketBar)]


async def get_ticks(
    backend: TradingBackend,
    symbol: str,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    *,
    count: int | None = None,
    limit: int = MAX_RECORDS,
) -> list[MarketTick]:
    """Read ticks by date range, forward date/count or latest count."""
    logger.debug("FR-DATA-HISTORICAL-READS: requesting ticks")
    mode, start, end, number = _route(
        date_from, date_to, None, count, limit, scale=1000
    )
    validate_request(
        symbol,
        1 if mode == "latest" else start,
        max(start, end) if mode == "range" else (start if mode == "date_count" else 1),
        limit,
    )
    if mode == "range" and start > end:
        return []
    payload = await backend.call(
        object_id="market-data",
        class_name="MarketData",
        method_name="Ticks",
        args=[symbol, mode, start, end, number, limit],
        timeout=READ_TIMEOUT,
    )
    rows = validate_rows(payload, "ticks", start, end, number or limit)
    return [row for row in rows if isinstance(row, MarketTick)]
