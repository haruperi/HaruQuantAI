"""Verify market data DataFrame transformation utilities.

Description:
    Test suite for bars_to_dataframe, ticks_to_dataframe, and aliases, verifying
    index naming, UTC timezone preservation, column ordering, data types, and
    edge cases (empty inputs, dict representations, custom object duck typing).

Purpose:
    FEAT-SERVICES-DATA: Validate DataFrame conversions for market bars and ticks.

Key Capabilities:
    - FR-SERVICES-DATA-BARS-DATAFRAME: Validate historical bar conversion to DataFrame.
    - FR-SERVICES-DATA-TICKS-DATAFRAME: Validate historical tick conversion to DataFrame.

Python API Usage:
    ```python
    pytest tests/unit/services/test_data.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_data.py --cov=app/services/utils/data
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import pytest
from app.services.brokers.contracts import MarketBar, MarketTick, Tick
from app.services.utils.data import (
    bars_to_dataframe,
    bars_to_df,
    ticks_to_dataframe,
    ticks_to_df,
)


def test_bars_to_dataframe_from_market_bars() -> None:
    """Verify converting MarketBar objects to DataFrame with expected columns and index."""
    bars = [
        MarketBar(
            time=1700000000,
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1020,
            tick_volume=150,
            spread=15,
            real_volume=2000,
        ),
        MarketBar(
            time=1700000060,
            open=1.1020,
            high=1.1060,
            low=1.1010,
            close=1.1040,
            tick_volume=220,
            spread=12,
            real_volume=3000,
        ),
    ]

    df = bars_to_dataframe(bars)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume", "Spread"]
    assert df.index.name == "DateTime"
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[s]"

    # Verify first row values and second precision representation
    assert df.index[0] == pd.Timestamp("2023-11-14 22:13:20")
    assert str(df.index[0]) == "2023-11-14 22:13:20"
    assert df["Open"].iloc[0] == pytest.approx(1.1000)
    assert df["High"].iloc[0] == pytest.approx(1.1050)
    assert df["Low"].iloc[0] == pytest.approx(1.0950)
    assert df["Close"].iloc[0] == pytest.approx(1.1020)
    assert df["Volume"].iloc[0] == 150
    assert df["Spread"].iloc[0] == 15

    # Verify second row
    assert df["Volume"].iloc[1] == 220
    assert df["Spread"].iloc[1] == 12

    # Verify alias
    df_alias = bars_to_df(bars)
    pd.testing.assert_frame_equal(df, df_alias)


def test_bars_to_dataframe_from_dicts() -> None:
    """Verify converting dictionaries with various key conventions."""
    bar_dicts: list[dict[str, Any]] = [
        {
            "time": 1700000000,
            "open": 1.05,
            "high": 1.06,
            "low": 1.04,
            "close": 1.055,
            "tick_volume": 50,
            "spread": 8,
        },
        {
            "DateTime": 1700000060,
            "Open": 1.055,
            "High": 1.065,
            "Low": 1.050,
            "Close": 1.060,
            "Volume": 80,
            "Spread": 10,
        },
    ]

    df = bars_to_dataframe(bar_dicts)
    assert len(df) == 2
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[s]"
    assert df["Open"].iloc[0] == pytest.approx(1.05)
    assert df["Volume"].iloc[0] == 50
    assert df["Open"].iloc[1] == pytest.approx(1.055)
    assert df["Volume"].iloc[1] == 80


def test_bars_to_dataframe_from_custom_objects() -> None:
    """Verify converting arbitrary objects with bar attributes."""

    @dataclass
    class CustomBar:
        time: int
        open: float
        high: float
        low: float
        close: float
        volume: int
        spread: int

    bars = [CustomBar(1700000000, 1.20, 1.22, 1.19, 1.21, 300, 5)]
    df = bars_to_dataframe(bars)
    assert len(df) == 1
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[s]"
    assert df["Volume"].iloc[0] == 300
    assert df["Spread"].iloc[0] == 5


def test_bars_to_dataframe_empty() -> None:
    """Verify converting empty bar sequence produces empty DataFrame with schema."""
    df = bars_to_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume", "Spread"]
    assert df.index.name == "DateTime"
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[s]"


def test_ticks_to_dataframe_from_market_ticks() -> None:
    """Verify converting MarketTick objects with millisecond timestamps."""
    ticks = [
        MarketTick(
            time_msc=1700000000123,
            bid=1.1000,
            ask=1.1002,
            last=1.1001,
            volume=5,
            flags=6,
            volume_real=5.0,
        ),
        MarketTick(
            time_msc=1700000000456,
            bid=1.1001,
            ask=1.1003,
            last=1.1002,
            volume=10,
            flags=6,
            volume_real=10.0,
        ),
    ]

    df = ticks_to_dataframe(ticks)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["Bid", "Ask"]
    assert df.index.name == "DateTime"
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[ms]"

    # Millisecond precision preserved without timezone offset
    assert df.index[0] == pd.Timestamp("2023-11-14 22:13:20.123")
    assert df.index[1] == pd.Timestamp("2023-11-14 22:13:20.456")
    assert "2023-11-14 22:13:20.123" in df.to_string()
    assert df["Bid"].iloc[0] == pytest.approx(1.1000)
    assert df["Ask"].iloc[0] == pytest.approx(1.1002)

    # Verify alias
    df_alias = ticks_to_df(ticks)
    pd.testing.assert_frame_equal(df, df_alias)


def test_ticks_to_dataframe_from_tick_objects() -> None:
    """Verify converting Tick objects with datetime timestamps."""
    ticks = [
        Tick(
            symbol="EURUSD",
            time=datetime(2026, 10, 12, 14, 30, 0, 210000, tzinfo=UTC),
            bid=1.0950,
            ask=1.0952,
        ),
    ]

    df = ticks_to_dataframe(ticks)
    assert len(df) == 1
    assert list(df.columns) == ["Bid", "Ask"]
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[ms]"
    assert df["Bid"].iloc[0] == pytest.approx(1.0950)
    assert df["Ask"].iloc[0] == pytest.approx(1.0952)
    assert df.index[0] == pd.Timestamp("2026-10-12 14:30:00.210")
    assert "2026-10-12 14:30:00.210" in df.to_string()


def test_ticks_to_dataframe_from_dicts() -> None:
    """Verify converting dictionaries with time_msc and time keys."""
    tick_dicts: list[dict[str, Any]] = [
        {"time_msc": 1700000000100, "bid": 1.25, "ask": 1.26},
        {"time": 1700000001, "bid": 1.255, "ask": 1.265},
    ]

    df = ticks_to_dataframe(tick_dicts)
    assert len(df) == 2
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[ms]"
    assert df["Bid"].iloc[0] == pytest.approx(1.25)
    assert df["Ask"].iloc[0] == pytest.approx(1.26)
    assert df["Bid"].iloc[1] == pytest.approx(1.255)
    assert df["Ask"].iloc[1] == pytest.approx(1.265)


def test_ticks_to_dataframe_from_custom_objects() -> None:
    """Verify converting arbitrary duck-typed objects."""

    @dataclass
    class CustomTickWithMsc:
        time_msc: int
        bid: float
        ask: float

    @dataclass
    class CustomTickWithTime:
        time: int
        bid: float
        ask: float

    ticks = [
        CustomTickWithMsc(1700000000100, 1.30, 1.31),
        CustomTickWithTime(1700000002, 1.305, 1.315),
    ]
    df = ticks_to_dataframe(ticks)
    assert len(df) == 2
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[ms]"
    assert df["Bid"].iloc[0] == pytest.approx(1.30)
    assert df["Bid"].iloc[1] == pytest.approx(1.305)


def test_ticks_to_dataframe_empty() -> None:
    """Verify converting empty tick sequence produces empty DataFrame with schema."""
    df = ticks_to_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == ["Bid", "Ask"]
    assert df.index.name == "DateTime"
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is None
    assert str(df.index.dtype) == "datetime64[ms]"
