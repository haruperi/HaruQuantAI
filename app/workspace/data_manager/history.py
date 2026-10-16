"""Historical market data readers, boundary validators, and DataFrame converters.

Description:
    Provides asynchronous historical bar and tick fetching routines across
    broker and local data backends, request range validation, row boundaries,
    and structured conversion routines into pandas DataFrames.

Purpose:
    FEAT-DATAMGR-HISTORY: Historical market data retrieval, validation, and conversion.

Key Capabilities:
    - FR-DATAMGR-HISTORY-BAR-COLUMNS: Canonical bar column tuple specification.
      Associated: `BAR_COLUMNS`.
      Logging: Constant schema tuple with zero side effects.
    - FR-DATAMGR-HISTORY-TICK-COLUMNS: Canonical tick column tuple specification.
      Associated: `TICK_COLUMNS`.
      Logging: Constant schema tuple with zero side effects.
    - FR-DATAMGR-HISTORY-BACKEND-PROTOCOL: Execution protocol for market data readers.
      Associated: `DataBackend`.
      Logging: Protocol definition with zero side effects.
    - FR-DATAMGR-HISTORY-BROKER-BACKEND: Base market data provider adapter.
      Associated: `DataBrokerBackend`.
      Logging: DEBUG market data dispatch lifecycle through BaseBrokerBackend.
    - FR-DATAMGR-HISTORY-BARS-TO-DATAFRAME: Convert historical bars to pandas DataFrame.
      Associated: `bars_to_dataframe()`.
      Logging: In-memory vectorized DataFrame construction.
    - FR-DATAMGR-HISTORY-BARS-TO-DF: Shorthand alias for bars DataFrame conversion.
      Associated: `bars_to_df()`.
      Logging: In-memory vectorized DataFrame construction.
    - FR-DATAMGR-HISTORY-GET-HISTORICAL-BARS: Fetch historical bars from broker backend.
      Associated: `get_historical_bars()`.
      Logging: DEBUG historical bar query bounds.
    - FR-DATAMGR-HISTORY-GET-TICKS: Fetch historical ticks from broker backend.
      Associated: `get_ticks()`.
      Logging: DEBUG historical tick query bounds.
    - FR-DATAMGR-HISTORY-TICKS-TO-DATAFRAME: Convert historical ticks to DataFrame.
      Associated: `ticks_to_dataframe()`.
      Logging: In-memory vectorized DataFrame construction.
    - FR-DATAMGR-HISTORY-TICKS-TO-DF: Shorthand alias for ticks DataFrame conversion.
      Associated: `ticks_to_df()`.
      Logging: In-memory vectorized DataFrame construction.
    - FR-DATAMGR-HISTORY-VALIDATE-REQUEST: Validate historical data request parameters.
      Associated: `validate_request()`.
      Logging: DEBUG request parameters with error codes on validation failure.
    - FR-DATAMGR-HISTORY-VALIDATE-ROWS: Validate row counts and boundaries.
      Associated: `validate_rows()`.
      Logging: DEBUG row boundaries with error codes on validation failure.

Python API Usage:
    ```python
    from app.workspace.data_manager.history import (
        bars_to_dataframe,
        get_historical_bars,
        validate_request,
        validate_rows,
    )
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.history
    ```
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import fields
from datetime import UTC, datetime
from typing import Any, Literal, Protocol, override

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.services.brokers.base import BaseBrokerBackend, BridgeError
from app.services.include.contracts import (
    MAX_POSITION,
    MAX_RECORDS,
    READ_TIMEOUT,
    TIMEFRAME_SECONDS,
    MarketBar,
    MarketTick,
)
from app.services.include.enums import (
    Timeframe,
)

__all__ = [
    "BAR_COLUMNS",
    "TICK_COLUMNS",
    "DataBackend",
    "DataBrokerBackend",
    "bars_to_dataframe",
    "bars_to_df",
    "get_historical_bars",
    "get_ticks",
    "ticks_to_dataframe",
    "ticks_to_df",
    "validate_request",
    "validate_rows",
]

logger = get_logger(__name__)


class DataBackend(Protocol):
    """Execution protocol for market data readers."""

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline capability
    ) -> Any:
        """Execute a market data query over backend transport."""
        ...


class DataBrokerBackend(BaseBrokerBackend):
    """Base adapter for market data providers conforming to DataBackend."""

    @override
    def _dispatch(self, class_name: str, method_name: str, args: list[Any]) -> Any:
        """Route call to subclass methods, handling MarketData queries."""
        if class_name == "MarketData":
            if method_name == "Bars":
                return self._dispatch_bars(args)
            if method_name == "Ticks":
                return self._dispatch_ticks(args)
        return super()._dispatch(class_name, method_name, args)

    def _dispatch_bars(self, args: list[Any]) -> list[dict[str, Any]] | list[MarketBar]:
        """Unpack canonical args and invoke fetch_bars."""
        padded: list[Any] = list(args) + [None] * 7
        symbol = str(padded[0]) if padded[0] is not None else "EURUSD"
        timeframe = str(padded[1]) if padded[1] is not None else "H1"
        mode = str(padded[2]) if padded[2] is not None else "latest"
        start = int(padded[3]) if padded[3] is not None else 0
        end = int(padded[4]) if padded[4] is not None else 0
        count = int(padded[5]) if padded[5] is not None else 0
        limit = int(padded[6]) if padded[6] is not None else 1000
        return self.fetch_bars(
            symbol=symbol,
            timeframe=timeframe,
            mode=mode,
            start=start,
            end=end,
            count=count,
            limit=limit,
        )

    def _dispatch_ticks(
        self, args: list[Any]
    ) -> list[dict[str, Any]] | list[MarketTick]:
        """Unpack canonical args and invoke fetch_ticks."""
        padded: list[Any] = list(args) + [None] * 6
        symbol = str(padded[0]) if padded[0] is not None else "EURUSD"
        mode = str(padded[1]) if padded[1] is not None else "latest"
        start_ms = int(padded[2]) if padded[2] is not None else 0
        end_ms = int(padded[3]) if padded[3] is not None else 0
        count = int(padded[4]) if padded[4] is not None else 0
        limit = int(padded[5]) if padded[5] is not None else 1000
        return self.fetch_ticks(
            symbol=symbol,
            mode=mode,
            start_ms=start_ms,
            end_ms=end_ms,
            count=count,
            limit=limit,
        )

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        mode: str,
        start: int,
        end: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]] | list[MarketBar]:
        """Subclass hook to fetch historical candlestick bars."""
        del symbol, timeframe, mode, start, end, count, limit
        raise BridgeError(
            f"{self.name} does not support historical bars",
            code="UNSUPPORTED_OPERATION",
        )

    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str,
        start_ms: int,
        end_ms: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]] | list[MarketTick]:
        """Subclass hook to fetch historical or live ticks."""
        del symbol, mode, start_ms, end_ms, count, limit
        raise BridgeError(
            f"{self.name} does not support tick history",
            code="UNSUPPORTED_OPERATION",
        )


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
    backend: DataBackend,
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
    backend: DataBackend,
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


BAR_COLUMNS: list[str] = ["Open", "High", "Low", "Close", "Volume", "Spread"]
TICK_COLUMNS: list[str] = ["Bid", "Ask"]


def _parse_bar_record(
    bar: MarketBar | dict[str, Any] | Any,
) -> tuple[datetime | int | float | str, float, float, float, float, int, int]:
    """Extract individual bar fields from record or dictionary."""
    if isinstance(bar, MarketBar):
        return (
            bar.time,
            float(bar.open),
            float(bar.high),
            float(bar.low),
            float(bar.close),
            bar.tick_volume,
            bar.spread,
        )
    if isinstance(bar, dict):
        raw_t = bar.get("time")
        if raw_t is None:
            raw_t = bar.get("DateTime", 0)
        time_val: datetime | int | float | str = (
            raw_t if isinstance(raw_t, (datetime, int, float, str)) else 0
        )
        raw_o = bar.get("open")
        open_val = float(raw_o if raw_o is not None else bar.get("Open", 0.0))
        raw_h = bar.get("high")
        high_val = float(raw_h if raw_h is not None else bar.get("High", 0.0))
        raw_l = bar.get("low")
        low_val = float(raw_l if raw_l is not None else bar.get("Low", 0.0))
        raw_c = bar.get("close")
        close_val = float(raw_c if raw_c is not None else bar.get("Close", 0.0))
        raw_v = bar.get("tick_volume", bar.get("volume"))
        vol_val = int(raw_v if raw_v is not None else bar.get("Volume", 0))
        raw_s = bar.get("spread")
        spread_val = int(raw_s if raw_s is not None else bar.get("Spread", 0))
        return (time_val, open_val, high_val, low_val, close_val, vol_val, spread_val)

    raw_duck_t = getattr(bar, "time", 0)
    duck_time: datetime | int | float | str = (
        raw_duck_t if isinstance(raw_duck_t, (datetime, int, float, str)) else 0
    )
    return (
        duck_time,
        float(getattr(bar, "open", 0.0)),
        float(getattr(bar, "high", 0.0)),
        float(getattr(bar, "low", 0.0)),
        float(getattr(bar, "close", 0.0)),
        int(getattr(bar, "tick_volume", getattr(bar, "volume", 0))),
        int(getattr(bar, "spread", 0)),
    )


def _parse_tick_record(
    tick: MarketTick | Any,
) -> tuple[datetime | int | float | str, bool, float, float]:
    """Extract timestamp, is_ms flag, bid, and ask from record or dictionary."""
    if isinstance(tick, MarketTick):
        return tick.time_msc, True, float(tick.bid), float(tick.ask)
    if isinstance(tick, dict):
        bid = float(tick.get("bid", 0.0) or 0.0)
        ask = float(tick.get("ask", 0.0) or 0.0)
        if "time_msc" in tick:
            raw_msc = tick.get("time_msc", 0)
            msc_val: datetime | int | float | str = (
                raw_msc if isinstance(raw_msc, (datetime, int, float, str)) else 0
            )
            return msc_val, True, bid, ask
        raw_t = tick.get("time")
        if raw_t is None:
            raw_t = tick.get("DateTime", 0)
        t_val: datetime | int | float | str = (
            raw_t if isinstance(raw_t, (datetime, int, float, str)) else 0
        )
        return t_val, False, bid, ask
    bid_val = float(getattr(tick, "bid", 0.0))
    ask_val = float(getattr(tick, "ask", 0.0))
    if hasattr(tick, "time_msc"):
        raw_tick_msc = tick.time_msc
        tick_msc_val: datetime | int | float | str = (
            raw_tick_msc if isinstance(raw_tick_msc, (datetime, int, float, str)) else 0
        )
        return tick_msc_val, True, bid_val, ask_val
    raw_tick_t = getattr(tick, "time", 0)
    tick_time: datetime | int | float | str = (
        raw_tick_t if isinstance(raw_tick_t, (datetime, int, float, str)) else 0
    )
    return tick_time, False, bid_val, ask_val


def bars_to_dataframe(bars: Iterable[MarketBar | dict[str, Any]]) -> pd.DataFrame:
    """Convert an iterable of MarketBar records or dicts to a pandas DataFrame.

    The resulting DataFrame is indexed by a timezone-naive DatetimeIndex
    named 'DateTime' with second resolution ('datetime64[s]') and contains
    columns: Open, High, Low, Close, Volume, Spread. Volume is derived from
    tick_volume.

    Args:
        bars: Sequence of MarketBar objects or dictionaries containing bar fields.

    Returns:
        pd.DataFrame indexed by timezone-naive DateTime.
    """
    timestamps: list[datetime | int | float | str] = []
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    volumes: list[int] = []
    spreads: list[int] = []

    for bar in bars:
        t, o, h, low, c, v, s = _parse_bar_record(bar)
        timestamps.append(t)
        opens.append(o)
        highs.append(h)
        lows.append(low)
        closes.append(c)
        volumes.append(v)
        spreads.append(s)

    if not timestamps:
        idx = pd.DatetimeIndex([], name="DateTime", dtype="datetime64[s]")
        col_types = {
            "Open": "float64",
            "High": "float64",
            "Low": "float64",
            "Close": "float64",
            "Volume": "int64",
            "Spread": "int64",
        }
        df = pd.DataFrame(
            {col: pd.Series(dtype=col_types[col]) for col in BAR_COLUMNS},
            index=idx,
        )
        logger.debug(
            "FR-DATA-DATAFRAME-CONVERSIONS: converted 0 bars into empty DataFrame"
        )
        return df

    if all(isinstance(t, (int, float)) for t in timestamps):
        index = (
            pd.to_datetime(timestamps, unit="s", utc=True)
            .tz_localize(None)
            .as_unit("s")
        )
    else:
        index = pd.to_datetime(timestamps, utc=True).tz_localize(None).as_unit("s")

    index.name = "DateTime"
    df = pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes,
            "Spread": spreads,
        },
        index=index,
    )
    logger.debug(
        "FR-DATA-DATAFRAME-CONVERSIONS: converted %d bars -> shape %s",
        len(df),
        df.shape,
    )
    return df


def ticks_to_dataframe(
    ticks: Iterable[MarketTick | Any],
) -> pd.DataFrame:
    """Convert an iterable of MarketTick, Tick, or dicts to a pandas DataFrame.

    The resulting DataFrame is indexed by a timezone-naive DatetimeIndex
    named 'DateTime' with millisecond resolution ('datetime64[ms]') and contains
    columns: Bid, Ask.

    Args:
        ticks: Sequence of MarketTick, Tick, or dictionary tick representations.

    Returns:
        pd.DataFrame indexed by timezone-naive DateTime.
    """
    timestamps: list[datetime | int | float | str] = []
    use_ms: bool = False
    bids: list[float] = []
    asks: list[float] = []

    for tick in ticks:
        t, is_ms, b, a = _parse_tick_record(tick)
        timestamps.append(t)
        if is_ms:
            use_ms = True
        bids.append(b)
        asks.append(a)

    if not timestamps:
        idx = pd.DatetimeIndex([], name="DateTime", dtype="datetime64[ms]")
        df = pd.DataFrame(
            {col: pd.Series(dtype="float64") for col in TICK_COLUMNS},
            index=idx,
        )
        logger.debug(
            "FR-DATA-DATAFRAME-CONVERSIONS: converted 0 ticks into empty DataFrame"
        )
        return df

    if use_ms and all(isinstance(t, (int, float)) for t in timestamps):
        index = (
            pd.to_datetime(timestamps, unit="ms", utc=True)
            .tz_localize(None)
            .as_unit("ms")
        )
    elif all(isinstance(t, (int, float)) for t in timestamps):
        index = (
            pd.to_datetime(timestamps, unit="s", utc=True)
            .tz_localize(None)
            .as_unit("ms")
        )
    else:
        index = pd.to_datetime(timestamps, utc=True).tz_localize(None).as_unit("ms")

    index.name = "DateTime"
    df = pd.DataFrame(
        {
            "Bid": bids,
            "Ask": asks,
        },
        index=index,
    )
    logger.debug(
        "FR-DATA-DATAFRAME-CONVERSIONS: converted %d ticks -> shape %s",
        len(df),
        df.shape,
    )
    return df


bars_to_df = bars_to_dataframe
ticks_to_df = ticks_to_dataframe


def main() -> None:
    """Demonstrate historical data converters and row validation."""
    bar = MarketBar(time=1700000000, open=1.1, high=1.2, low=1.0, close=1.15)
    df = bars_to_dataframe([bar])
    print(f"Historical bars DataFrame shape: {df.shape}, columns: {list(df.columns)}")
    row = {
        "time": 1700000000,
        "open": 1.1,
        "high": 1.2,
        "low": 1.0,
        "close": 1.15,
        "tick_volume": 10,
        "spread": 0,
        "real_volume": 0,
    }
    validated = validate_rows([row], "bars", 1699999900, 1700000100, MAX_RECORDS)
    print(f"Validated rows: count={len(validated)}")


if __name__ == "__main__":
    main()
