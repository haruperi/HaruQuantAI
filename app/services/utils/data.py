"""Market data structure to pandas DataFrame conversion utilities.

Description:
    Provides transformation functions that convert domain market data sequences
    (such as MarketBar, MarketTick, Tick, or compatible dictionary representations)
    into analysis-ready pandas DataFrames indexed by timezone-naive DateTime.
    Ensures consistent column naming, precision, and temporal indexing across quant
    strategies, indicators, and broker inspection workflows.

Purpose:
    FEAT-SERVICES-DATA: Expose standardized DataFrame conversion utilities.

Key Capabilities:
    - FR-SERVICES-DATA-BARS-DATAFRAME: Convert historical bars into a structured
      pandas DataFrame indexed by timezone-naive DateTime (second resolution).
      Associated: `bars_to_dataframe()`, `bars_to_df()`
      Logging: DEBUG converted bar count and resulting DataFrame shape.
    - FR-SERVICES-DATA-TICKS-DATAFRAME: Convert historical ticks into a structured
      pandas DataFrame indexed by timezone-naive DateTime (millisecond resolution).
      Associated: `ticks_to_dataframe()`, `ticks_to_df()`
      Logging: DEBUG converted tick count and resulting DataFrame shape.

Python API Usage:
    ```python
    from app.services.brokers.contracts import MarketBar, MarketTick
    from app.services.utils.data import bars_to_dataframe, ticks_to_dataframe

    bars = [MarketBar(1700000000, 1.1000, 1.1050, 1.0950, 1.1020, 100, 10, 0)]
    bars_df = bars_to_dataframe(bars)

    ticks = [MarketTick(1700000000000, 1.1000, 1.1002, 1.1001, 10, 6, 10.0)]
    ticks_df = ticks_to_dataframe(ticks)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_data.py --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import pandas as pd
from app.host.logging import get_logger
from app.services.brokers.contracts import MarketBar, MarketTick, Tick

logger = get_logger(__name__)

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
            int(bar.tick_volume),
            int(bar.spread),
        )
    if isinstance(bar, dict):
        return (
            bar.get("time", bar.get("DateTime", 0)),
            float(bar.get("open", bar.get("Open", 0.0))),
            float(bar.get("high", bar.get("High", 0.0))),
            float(bar.get("low", bar.get("Low", 0.0))),
            float(bar.get("close", bar.get("Close", 0.0))),
            int(bar.get("tick_volume", bar.get("volume", bar.get("Volume", 0)))),
            int(bar.get("spread", bar.get("Spread", 0))),
        )
    return (
        getattr(bar, "time", 0),
        float(getattr(bar, "open", 0.0)),
        float(getattr(bar, "high", 0.0)),
        float(getattr(bar, "low", 0.0)),
        float(getattr(bar, "close", 0.0)),
        int(getattr(bar, "tick_volume", getattr(bar, "volume", 0))),
        int(getattr(bar, "spread", 0)),
    )


def _parse_tick_record(
    tick: MarketTick | Tick | dict[str, Any] | Any,
) -> tuple[datetime | int | float | str, bool, float, float]:
    """Extract timestamp, is_ms flag, bid, and ask from record or dictionary."""
    if isinstance(tick, MarketTick):
        return tick.time_msc, True, float(tick.bid), float(tick.ask)
    if isinstance(tick, Tick):
        return tick.time, False, float(tick.bid), float(tick.ask)
    if isinstance(tick, dict):
        bid = float(tick.get("bid", 0.0))
        ask = float(tick.get("ask", 0.0))
        if "time_msc" in tick:
            return tick["time_msc"], True, bid, ask
        t = tick.get("time", tick.get("DateTime", 0))
        return t, False, bid, ask
    bid_val = float(getattr(tick, "bid", 0.0))
    ask_val = float(getattr(tick, "ask", 0.0))
    if hasattr(tick, "time_msc"):
        return tick.time_msc, True, bid_val, ask_val
    return getattr(tick, "time", 0), False, bid_val, ask_val


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
            "FR-SERVICES-DATA-BARS-DATAFRAME: converted 0 bars into empty DataFrame"
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
        "FR-SERVICES-DATA-BARS-DATAFRAME: converted %d bars -> shape %s",
        len(df),
        df.shape,
    )
    return df


def ticks_to_dataframe(
    ticks: Iterable[MarketTick | Tick | dict[str, Any]],
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
            "FR-SERVICES-DATA-TICKS-DATAFRAME: converted 0 ticks into empty DataFrame"
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
        "FR-SERVICES-DATA-TICKS-DATAFRAME: converted %d ticks -> shape %s",
        len(df),
        df.shape,
    )
    return df


bars_to_df = bars_to_dataframe
ticks_to_df = ticks_to_dataframe
