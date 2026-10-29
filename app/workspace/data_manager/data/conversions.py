"""Convert provider market records to standard bar and tick DataFrames."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from app.core.host.logging import get_logger
from app.include.contracts import MarketBar, MarketTick

logger = get_logger(__name__)
BAR_COLUMNS: list[str] = ["Open", "High", "Low", "Close", "Volume", "Spread"]
TICK_COLUMNS: list[str] = ["Bid", "Ask"]
__all__ = ["BAR_COLUMNS", "TICK_COLUMNS", "bars_to_dataframe", "ticks_to_dataframe"]


def _parse_bar_record(
    record: MarketBar | dict[str, Any] | Any,
) -> tuple[datetime | int | float | str, float, float, float, float, int, int]:
    """Extract individual bar fields from record or dictionary."""
    if isinstance(record, MarketBar):
        return (
            record.time,
            float(record.open),
            float(record.high),
            float(record.low),
            float(record.close),
            record.tick_volume,
            record.spread,
        )
    if isinstance(record, dict):
        raw_t = record.get("time")
        if raw_t is None:
            raw_t = record.get("DateTime", 0)
        time_val: datetime | int | float | str = (
            raw_t if isinstance(raw_t, (datetime, int, float, str)) else 0
        )
        raw_o = record.get("open")
        open_val = float(raw_o if raw_o is not None else record.get("Open", 0.0))
        raw_h = record.get("high")
        high_val = float(raw_h if raw_h is not None else record.get("High", 0.0))
        raw_l = record.get("low")
        low_val = float(raw_l if raw_l is not None else record.get("Low", 0.0))
        raw_c = record.get("close")
        close_val = float(raw_c if raw_c is not None else record.get("Close", 0.0))
        raw_v = record.get("tick_volume", record.get("volume"))
        vol_val = int(raw_v if raw_v is not None else record.get("Volume", 0))
        raw_s = record.get("spread")
        spread_val = int(raw_s if raw_s is not None else record.get("Spread", 0))
        return (time_val, open_val, high_val, low_val, close_val, vol_val, spread_val)

    raw_duck_t = getattr(record, "time", 0)
    duck_time: datetime | int | float | str = (
        raw_duck_t if isinstance(raw_duck_t, (datetime, int, float, str)) else 0
    )
    return (
        duck_time,
        float(getattr(record, "open", 0.0)),
        float(getattr(record, "high", 0.0)),
        float(getattr(record, "low", 0.0)),
        float(getattr(record, "close", 0.0)),
        int(getattr(record, "tick_volume", getattr(record, "volume", 0))),
        int(getattr(record, "spread", 0)),
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
    """Convert an iterable of MarketBar records or dicts to a pandas DataFrame."""
    timestamps: list[datetime | int | float | str] = []
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    volumes: list[int] = []
    spreads: list[int] = []

    for record in bars:
        t, o, h, low, c, v, s = _parse_bar_record(record)
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
    """Convert an iterable of MarketTick, Tick, or dicts to a pandas DataFrame."""
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
