"""Unit tests for market data contracts and columnar DataSeries kernel in libs.data.

Description:
    Validates functionality, boundary conditions, numerical integrity,
    dual-indexing, warmup constraints, condition predicates, columnar
    conversions, and market data contracts (Timeframe, MarketBar, MarketTick,
    BridgeError) in app.workspace.data_manager.

Purpose:
    FEAT-LIBS-DATA: Test suite for consolidated market data library and series kernel.

Key Capabilities:
    - FR-DATA-MARKET-PRIMITIVES: Verify Timeframe enums, MarketBar, MarketTick, BridgeError.
    - FR-DATA-COLUMNAR-SERIES: Verify shift/chronological indexing, mutation, predicates.
    - FR-DATA-HISTORY-VALIDATION: Verify request validation and data validation.
    - FR-DATA-DATAFRAME-CONVERSIONS: Verify bars_to_dataframe and ticks_to_dataframe.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/test_data_series.py --no-cov
    ```
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow as pa
import pytest
from app.workspace.data_manager import (
    BAR_COLUMNS,
    TICK_COLUMNS,
    BridgeError,
    DataBackend,
    DataSeries,
    DataSeriesTypes,
    MarketBar,
    MarketTick,
    MedianDataSeries,
    Timeframe,
    TypicalDataSeries,
    WeightedDataSeries,
    bars_to_dataframe,
    bars_to_df,
    ticks_to_dataframe,
    ticks_to_df,
    validate_request,
    validate_rows,
)
from app.workspace.data_manager.history import (
    DataBackend as DirectDataBackend,
)
from app.workspace.data_manager.history import (
    bars_to_dataframe as direct_bars_to_dataframe,
)
from app.workspace.data_manager.history import (
    ticks_to_dataframe as direct_ticks_to_dataframe,
)
from app.workspace.data_manager.series import (
    DataSeries as DirectDataSeries,
)
from app.workspace.data_manager.series import (
    DataSeriesTypes as DirectDataSeriesTypes,
)
from app.workspace.data_manager.series import (
    MedianDataSeries as DirectMedianDataSeries,
)
from app.workspace.data_manager.series import (
    TypicalDataSeries as DirectTypicalDataSeries,
)
from app.workspace.data_manager.series import (
    WeightedDataSeries as DirectWeightedDataSeries,
)


def test_public_reexports() -> None:
    """Verify DataSeries and history symbols are exported from their respective packages."""
    assert DataBackend is DirectDataBackend
    assert DataSeries is DirectDataSeries
    assert DataSeriesTypes is DirectDataSeriesTypes
    assert MedianDataSeries is DirectMedianDataSeries
    assert TypicalDataSeries is DirectTypicalDataSeries
    assert WeightedDataSeries is DirectWeightedDataSeries


class TestTimeframe:
    """Test suite for Timeframe enumeration and conversion helpers."""

    def test_timeframe_constants_and_aliases(self) -> None:
        """Verify standard timeframe values and aliases."""
        assert Timeframe.PERIOD_M1.value == "M1"
        assert Timeframe.M1.value == "M1"
        assert Timeframe.PERIOD_H1.value == "H1"
        assert Timeframe.H1.value == "H1"
        assert Timeframe.PERIOD_D1.value == "D1"
        assert Timeframe.D1.value == "D1"
        assert Timeframe.PERIOD_W1.value == "W1"
        assert Timeframe.W1.value == "W1"
        assert Timeframe.PERIOD_MN1.value == "MN1"
        assert Timeframe.MN1.value == "MN1"

    def test_to_seconds_and_minutes(self) -> None:
        """Verify to_seconds and to_minutes methods."""
        assert Timeframe.PERIOD_M1.to_seconds() == 60
        assert Timeframe.PERIOD_M1.to_minutes() == 1
        assert Timeframe.PERIOD_H1.to_seconds() == 3600
        assert Timeframe.PERIOD_H1.to_minutes() == 60
        assert Timeframe.PERIOD_D1.to_seconds() == 86400
        assert Timeframe.PERIOD_D1.to_minutes() == 1440
        assert Timeframe.PERIOD_CURRENT.to_seconds() == 0

    def test_from_string_valid(self) -> None:
        """Verify parsing standard timeframe strings."""
        assert Timeframe.from_string("M1") == Timeframe.PERIOD_M1
        assert Timeframe.from_string("1m") == Timeframe.PERIOD_M1
        assert Timeframe.from_string("1min") == Timeframe.PERIOD_M1
        assert Timeframe.from_string("5M") == Timeframe.PERIOD_M5
        assert Timeframe.from_string("15min") == Timeframe.PERIOD_M15
        assert Timeframe.from_string("30m") == Timeframe.PERIOD_M30
        assert Timeframe.from_string("h1") == Timeframe.PERIOD_H1
        assert Timeframe.from_string("1H") == Timeframe.PERIOD_H1
        assert Timeframe.from_string("60m") == Timeframe.PERIOD_H1
        assert Timeframe.from_string("h4") == Timeframe.PERIOD_H4
        assert Timeframe.from_string("4h") == Timeframe.PERIOD_H4
        assert Timeframe.from_string("240m") == Timeframe.PERIOD_H4
        assert Timeframe.from_string("d1") == Timeframe.PERIOD_D1
        assert Timeframe.from_string("1d") == Timeframe.PERIOD_D1
        assert Timeframe.from_string("day") == Timeframe.PERIOD_D1
        assert Timeframe.from_string("w1") == Timeframe.PERIOD_W1
        assert Timeframe.from_string("1w") == Timeframe.PERIOD_W1
        assert Timeframe.from_string("week") == Timeframe.PERIOD_W1
        assert Timeframe.from_string("mn1") == Timeframe.PERIOD_MN1
        assert Timeframe.from_string("1mn") == Timeframe.PERIOD_MN1
        assert Timeframe.from_string("month") == Timeframe.PERIOD_MN1

    def test_from_string_invalid(self) -> None:
        """Verify parsing invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown timeframe identifier"):
            Timeframe.from_string("UNKNOWN")


class TestMarketRecords:
    """Test suite for MarketBar, MarketTick, and BridgeError."""

    def test_bridge_error_properties(self) -> None:
        """Verify BridgeError exception attributes."""
        err = BridgeError(
            "test error", code="ERR_CODE", command_id="cmd-1", uncertain=True
        )
        assert str(err) == "test error"
        assert err.code == "ERR_CODE"
        assert err.command_id == "cmd-1"
        assert err.uncertain is True

    def test_market_bar_properties_bullish(self) -> None:
        """Verify MarketBar bullish candle computations."""
        bar = MarketBar(
            time=1000,
            open=100.0,
            high=110.0,
            low=95.0,
            close=108.0,
            tick_volume=50,
            spread=2,
            real_volume=100,
        )
        assert bar.time == 1000
        assert bar.open == 100.0
        assert bar.high == 110.0
        assert bar.low == 95.0
        assert bar.close == 108.0
        assert bar.tick_volume == 50
        assert bar.spread == 2
        assert bar.real_volume == 100
        assert bar.volume == 100.0
        assert bar.is_bullish is True
        assert bar.is_bearish is False
        assert bar.is_doji is False
        assert bar.range == pytest.approx(15.0)
        assert bar.body == pytest.approx(8.0)

    def test_market_bar_properties_bearish_and_doji(self) -> None:
        """Verify MarketBar bearish and doji candles."""
        bearish = MarketBar(
            time=1000, open=105.0, high=110.0, low=95.0, close=98.0, tick_volume=20
        )
        assert bearish.is_bullish is False
        assert bearish.is_bearish is True
        assert bearish.is_doji is False
        assert bearish.body == pytest.approx(7.0)
        assert bearish.volume == 20.0

        doji = MarketBar(time=1000, open=100.0, high=105.0, low=95.0, close=100.0)
        assert doji.is_bullish is False
        assert doji.is_bearish is False
        assert doji.is_doji is True
        assert doji.body == pytest.approx(0.0)
        assert doji.volume == 0.0

    def test_market_tick_properties(self) -> None:
        """Verify MarketTick spread and midpoint computations."""
        tick = MarketTick(
            time_msc=1000000,
            bid=100.0,
            ask=100.5,
            last=100.25,
            volume=10,
            flags=6,
            volume_real=10.5,
        )
        assert tick.time_msc == 1000000
        assert tick.bid == 100.0
        assert tick.ask == 100.5
        assert tick.last == 100.25
        assert tick.volume == 10
        assert tick.flags == 6
        assert tick.volume_real == 10.5
        assert tick.spread == pytest.approx(0.5)
        assert tick.mid == pytest.approx(100.25)


class TestDataSeriesCore:
    """Test suite for DataSeries initialization, indexing, and mutations."""

    def test_initialization_empty(self) -> None:
        """Verify empty DataSeries construction and default attributes."""
        ds = DataSeries()
        assert len(ds) == 0
        assert ds.size() == 0
        assert ds.name == ""
        assert ds.chart_type == "Line"
        assert ds.indy_starting_bar == 0
        assert ds.shift == 0
        assert ds.computed_until_index == -1
        assert math.isnan(ds.get(0))

    def test_initialization_with_sequence_and_numpy(self) -> None:
        """Verify initialization with list and numpy array."""
        ds_list = DataSeries([1.5, 2.5, 3.5], name="Price")
        assert len(ds_list) == 3
        assert ds_list.name == "Price"
        assert ds_list.get(0) == 3.5
        assert ds_list.get(1) == 2.5
        assert ds_list.get(2) == 1.5

        arr = np.array([10.0, 20.0, 30.0], dtype=np.float32)
        ds_np = DataSeries(arr, chart_type="Histogram", color="#ff0000")
        assert len(ds_np) == 3
        assert ds_np.chart_type == "Histogram"
        assert ds_np.color == "#ff0000"
        assert ds_np.get(0) == 30.0

    def test_shift_indexing_and_out_of_bounds(self) -> None:
        """Verify shift-based indexing boundaries."""
        ds = DataSeries([10.0, 20.0, 30.0])
        assert ds.get(0) == 30.0
        assert ds.get(1) == 20.0
        assert ds.get(2) == 10.0
        assert math.isnan(ds.get(-1))
        assert math.isnan(ds.get(3))
        assert math.isnan(ds.get(100))

    def test_warmup_guard_indy_starting_bar(self) -> None:
        """Verify indy_starting_bar warmup gating."""
        # Chronological: [1.0, 2.0, 3.0, 4.0, 5.0]
        ds = DataSeries([1.0, 2.0, 3.0, 4.0, 5.0], indy_starting_bar=2)
        assert ds.get(0) == 5.0  # Chronological index 4 >= 2
        assert ds.get(1) == 4.0  # Chronological index 3 >= 2
        assert ds.get(2) == 3.0  # Chronological index 2 >= 2
        assert math.isnan(ds.get(3))  # Chronological index 1 < 2 -> NaN
        assert math.isnan(ds.get(4))  # Chronological index 0 < 2 -> NaN

    def test_global_shift_offset(self) -> None:
        """Verify global shift offset behavior."""
        ds = DataSeries([10.0, 20.0, 30.0, 40.0], shift=1)
        assert ds.get(0) == 30.0
        assert ds.get(1) == 20.0
        assert ds.get(2) == 10.0
        assert math.isnan(ds.get(3))

    def test_chronological_indexing(self) -> None:
        """Verify chronological get_double and set_double."""
        ds = DataSeries([100.0, 200.0, 300.0])
        assert ds.get_double(0) == 100.0
        assert ds.get_double(1) == 200.0
        assert ds.get_double(2) == 300.0
        assert math.isnan(ds.get_double(-1))
        assert math.isnan(ds.get_double(3))

        ds.set_double(1, 250.0)
        assert ds.get_double(1) == 250.0
        ds.set_double(-1, 999.0)
        ds.set_double(5, 999.0)
        assert len(ds) == 3

    def test_set_by_shift(self) -> None:
        """Verify setting values by current bar or explicit shift."""
        ds = DataSeries([10.0, 20.0, 30.0])
        ds.set(35.0)
        assert ds.get(0) == 35.0

        ds.set(1, 22.0)
        assert ds.get(1) == 22.0
        assert ds.get_double(1) == 22.0

        ds.set(5, 99.0)
        ds.set(-1, 99.0)
        assert len(ds) == 3

    def test_add_and_add_values(self) -> None:
        """Verify dynamic extension via add and add_values."""
        ds = DataSeries([10.0])
        ds.add(20.0)
        ds.add(30.0)
        assert len(ds) == 3
        assert ds.get(0) == 30.0
        assert ds.get(1) == 20.0
        assert ds.get(2) == 10.0

        ds.add_values(2, default_val=0.0)
        assert len(ds) == 5
        assert ds.get(0) == 0.0
        assert ds.get(1) == 0.0
        assert ds.get(2) == 30.0

        ds.add_values(0)
        ds.add_values(-1)
        assert len(ds) == 5

    def test_get_rounded(self) -> None:
        """Verify get_rounded decimal formatting."""
        ds = DataSeries([1.234567, 2.345678])
        assert ds.get_rounded(0, decimals=2) == 2.35
        assert ds.get_rounded(0, decimals=4) == 2.3457
        assert ds.get_rounded(1, decimals=3) == 1.235
        assert math.isnan(ds.get_rounded(10))

    def test_iteration_and_subscription(self) -> None:
        """Verify iterable and slice access."""
        vals = [10.0, 20.0, 30.0, 40.0]
        ds = DataSeries(vals)
        assert list(ds) == vals

        np.testing.assert_array_equal(ds[:2], np.array([10.0, 20.0]))
        assert ds[0] == 40.0
        assert ds[1] == 30.0


class TestDataSeriesPredicates:
    """Test suite for condition evaluation predicates."""

    def test_is_rising_and_falling(self) -> None:
        """Verify is_rising and is_falling logic."""
        ds = DataSeries([10.0, 12.0, 15.0, 14.0])
        assert ds.is_rising(shift=1, periods=1) is True
        assert ds.is_falling(shift=0, periods=1) is True
        assert ds.is_rising(shift=0, periods=1) is False
        assert ds.is_falling(shift=1, periods=1) is False
        assert ds.is_rising(shift=1, periods=2) is True
        assert ds.is_rising(shift=10) is False
        assert ds.is_falling(shift=10) is False

    def test_crosses_above_and_below_scalar(self) -> None:
        """Verify crossing predicates against scalar thresholds."""
        ds = DataSeries([10.0, 20.0, 25.0, 15.0])
        assert ds.crosses_above(15.0, shift=2) is True
        assert ds.crosses_below(15.0, shift=2) is False

        assert ds.crosses_below(20.0, shift=0) is True
        assert ds.crosses_above(20.0, shift=0) is False

        ds_flat = DataSeries([10.0, 10.0])
        assert ds_flat.crosses_above(10.0, shift=0) is False
        assert ds_flat.crosses_below(10.0, shift=0) is False

        assert ds.crosses_above(15.0, shift=10) is False
        assert ds.crosses_below(15.0, shift=10) is False

    def test_crosses_above_and_below_series(self) -> None:
        """Verify crossing predicates against another DataSeries."""
        fast = DataSeries([10.0, 25.0])
        slow = DataSeries([15.0, 20.0])
        assert fast.crosses_above(slow, shift=0) is True
        assert fast.crosses_below(slow, shift=0) is False

        assert slow.crosses_below(fast, shift=0) is True
        assert slow.crosses_above(fast, shift=0) is False

    def test_is_higher_and_lower(self) -> None:
        """Verify is_higher and is_lower predicates for scalar and series."""
        ds = DataSeries([10.0, 20.0])
        assert ds.is_higher(15.0, shift=0) is True
        assert ds.is_lower(25.0, shift=0) is True
        assert ds.is_higher(25.0, shift=0) is False
        assert ds.is_lower(15.0, shift=0) is False

        other = DataSeries([5.0, 25.0])
        assert ds.is_lower(other, shift=0) is True
        assert ds.is_higher(other, shift=1) is True

        assert ds.is_higher(10.0, shift=5) is False
        assert ds.is_lower(10.0, shift=5) is False


class TestDataSeriesInterop:
    """Test suite for NumPy, Polars, and PyArrow columnar interoperability."""

    def test_numpy_roundtrip(self) -> None:
        """Verify conversion to and from NumPy array."""
        arr = np.array([1.1, 2.2, 3.3, 4.4], dtype=np.float64)
        ds = DataSeries.from_numpy(arr, name="TestNP")
        assert ds.name == "TestNP"
        assert len(ds) == 4
        assert ds.get(0) == 4.4

        exported = ds.to_numpy()
        np.testing.assert_array_equal(exported, arr)

    def test_polars_roundtrip(self) -> None:
        """Verify conversion to and from Polars Series."""
        pl_series = pl.Series("PolarsData", [10.0, 20.0, 30.0], dtype=pl.Float64)
        ds = DataSeries.from_polars(pl_series)
        assert ds.name == "PolarsData"
        assert len(ds) == 3
        assert ds.get(0) == 30.0

        exported = ds.to_polars()
        assert exported.name == "PolarsData"
        assert exported.to_list() == [10.0, 20.0, 30.0]

    def test_arrow_roundtrip(self) -> None:
        """Verify conversion to and from PyArrow Array."""
        pa_arr = pa.array([100.0, 200.0, 300.0], type=pa.float64())
        ds = DataSeries.from_arrow(pa_arr, name="ArrowData")
        assert ds.name == "ArrowData"
        assert len(ds) == 3
        assert ds.get(0) == 300.0

        exported = ds.to_arrow()
        assert exported.to_pylist() == [100.0, 200.0, 300.0]


class TestValidationRoutines:
    """Test suite for data request and payload validation routines."""

    def test_validate_request_valid(self) -> None:
        """Verify valid history request passes."""
        validate_request("EURUSD", 100, 200, 100, Timeframe.PERIOD_M1)

    def test_validate_request_invalid(self) -> None:
        """Verify invalid bounds or symbols raise BridgeError."""
        with pytest.raises(BridgeError, match="invalid history request"):
            validate_request("", 100, 200, 100)

        with pytest.raises(BridgeError, match="invalid history bounds"):
            validate_request("EURUSD", -1, 100, 50)

        with pytest.raises(BridgeError, match="tick start must be after"):
            validate_request("EURUSD", 0, 100, 50, None)

    def test_validate_rows_bars(self) -> None:
        """Verify validating bar rows creates MarketBar records."""
        payload = [
            {
                "time": 100,
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "tick_volume": 10,
                "spread": 1,
                "real_volume": 20,
            }
        ]
        bars = validate_rows(payload, "bars", 50, 150, 10)
        assert len(bars) == 1
        assert isinstance(bars[0], MarketBar)
        assert bars[0].close == 1.15

    def test_validate_rows_invalid_ohlc(self) -> None:
        """Verify invalid OHLC relationship raises BridgeError."""
        payload = [
            {
                "time": 100,
                "open": 1.5,
                "high": 1.2,  # high lower than open
                "low": 1.0,
                "close": 1.15,
                "tick_volume": 10,
                "spread": 1,
                "real_volume": 20,
            }
        ]
        with pytest.raises(BridgeError, match="invalid OHLC values"):
            validate_rows(payload, "bars", 50, 150, 10)


class TestBarsToDataframe:
    """Test suite for bars_to_dataframe conversion and aliases."""

    def test_columns_and_aliases(self) -> None:
        """Verify BAR_COLUMNS constant and alias equality."""
        assert BAR_COLUMNS == ["Open", "High", "Low", "Close", "Volume", "Spread"]
        assert bars_to_df is bars_to_dataframe
        assert direct_bars_to_dataframe is bars_to_dataframe

    def test_empty_bars(self) -> None:
        """Verify empty sequence produces empty DataFrame with expected schema."""
        df = bars_to_dataframe([])
        assert len(df) == 0
        assert list(df.columns) == BAR_COLUMNS
        assert df.index.name == "DateTime"
        assert str(df.index.dtype) == "datetime64[s]"
        assert df["Open"].dtype == "float64"
        assert df["Volume"].dtype == "int64"

    def test_market_bar_sequence(self) -> None:
        """Verify converting MarketBar sequence."""
        bars = [
            MarketBar(1700000000, 1.10, 1.15, 1.05, 1.12, 100, 5, 200),
            MarketBar(1700000060, 1.12, 1.18, 1.11, 1.17, 150, 6, 300),
        ]
        df = bars_to_dataframe(bars)
        assert len(df) == 2
        assert list(df.columns) == BAR_COLUMNS
        assert df.index.name == "DateTime"
        assert str(df.index.dtype) == "datetime64[s]"
        assert df.index[0] == pd.Timestamp("2023-11-14 22:13:20")
        assert df.index[1] == pd.Timestamp("2023-11-14 22:14:20")
        assert df["Open"].iloc[0] == 1.10
        assert df["Close"].iloc[1] == 1.17
        assert df["Volume"].iloc[0] == 100
        assert df["Spread"].iloc[0] == 5

    def test_dict_bars_sequence(self) -> None:
        """Verify converting dictionary bar records with both naming conventions."""
        bars_lower = [
            {
                "time": 1700000000,
                "open": 1.10,
                "high": 1.15,
                "low": 1.05,
                "close": 1.12,
                "tick_volume": 80,
                "spread": 4,
            }
        ]
        df_lower = bars_to_dataframe(bars_lower)
        assert len(df_lower) == 1
        assert df_lower["Volume"].iloc[0] == 80
        assert df_lower["Spread"].iloc[0] == 4

        bars_upper = [
            {
                "DateTime": 1700000000,
                "Open": 2.10,
                "High": 2.15,
                "Low": 2.05,
                "Close": 2.12,
                "Volume": 90,
                "Spread": 3,
            }
        ]
        df_upper = bars_to_dataframe(bars_upper)
        assert len(df_upper) == 1
        assert df_upper["Open"].iloc[0] == 2.10
        assert df_upper["Volume"].iloc[0] == 90

    def test_duck_typed_bars_and_datetimes(self) -> None:
        """Verify duck-typed objects and datetime timestamps."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        class CustomBar:
            time = dt
            open = 100.0
            high = 105.0
            low = 95.0
            close = 102.0
            volume = 50
            spread = 2

        df = bars_to_dataframe([CustomBar()])  # type: ignore[list-item]
        assert len(df) == 1
        assert df.index[0] == pd.Timestamp("2024-01-01 12:00:00")
        assert df["Close"].iloc[0] == 102.0
        assert df["Volume"].iloc[0] == 50


class TestTicksToDataframe:
    """Test suite for ticks_to_dataframe conversion and aliases."""

    def test_columns_and_aliases(self) -> None:
        """Verify TICK_COLUMNS constant and alias equality."""
        assert TICK_COLUMNS == ["Bid", "Ask"]
        assert ticks_to_df is ticks_to_dataframe
        assert direct_ticks_to_dataframe is ticks_to_dataframe

    def test_empty_ticks(self) -> None:
        """Verify empty sequence produces empty DataFrame with expected schema."""
        df = ticks_to_dataframe([])
        assert len(df) == 0
        assert list(df.columns) == TICK_COLUMNS
        assert df.index.name == "DateTime"
        assert str(df.index.dtype) == "datetime64[ms]"
        assert df["Bid"].dtype == "float64"
        assert df["Ask"].dtype == "float64"

    def test_market_tick_sequence(self) -> None:
        """Verify converting MarketTick sequence with millisecond resolution."""
        ticks = [
            MarketTick(1700000000123, 1.1000, 1.1002, 1.1001, 10, 6, 10.0),
            MarketTick(1700000000456, 1.1001, 1.1003, 1.1002, 15, 6, 15.0),
        ]
        df = ticks_to_dataframe(ticks)
        assert len(df) == 2
        assert list(df.columns) == TICK_COLUMNS
        assert df.index.name == "DateTime"
        assert str(df.index.dtype) == "datetime64[ms]"
        assert df.index[0] == pd.Timestamp("2023-11-14 22:13:20.123000")
        assert df.index[1] == pd.Timestamp("2023-11-14 22:13:20.456000")
        assert df["Bid"].iloc[0] == 1.1000
        assert df["Ask"].iloc[1] == 1.1003

    def test_dict_ticks_sequence(self) -> None:
        """Verify converting dictionary ticks with ms and second timestamps."""
        ticks_ms = [{"time_msc": 1700000000500, "bid": 1.05, "ask": 1.06}]
        df_ms = ticks_to_dataframe(ticks_ms)
        assert len(df_ms) == 1
        assert df_ms.index[0] == pd.Timestamp("2023-11-14 22:13:20.500000")
        assert df_ms["Bid"].iloc[0] == 1.05

        ticks_sec = [{"time": 1700000000, "bid": 1.07, "ask": 1.08}]
        df_sec = ticks_to_dataframe(ticks_sec)
        assert len(df_sec) == 1
        assert df_sec.index[0] == pd.Timestamp("2023-11-14 22:13:20")
        assert df_sec["Ask"].iloc[0] == 1.08

    def test_duck_typed_ticks_and_datetimes(self) -> None:
        """Verify duck-typed tick objects and datetime timestamps."""
        dt = datetime(2024, 1, 1, 12, 0, 0, 500000, tzinfo=UTC)

        class CustomTick:
            time = dt
            bid = 1.2345
            ask = 1.2347

        df = ticks_to_dataframe([CustomTick()])
        assert len(df) == 1
        assert df.index[0] == pd.Timestamp("2024-01-01 12:00:00.500000")
        assert df["Bid"].iloc[0] == 1.2345
        assert df["Ask"].iloc[0] == 1.2347

        class CustomMsTick:
            time_msc = 1700000000999
            bid = 1.50
            ask = 1.51

        df_ms = ticks_to_dataframe([CustomMsTick()])
        assert len(df_ms) == 1
        assert df_ms.index[0] == pd.Timestamp("2023-11-14 22:13:20.999000")


class TestDataSeriesTypes:
    """Test suite for DataSeriesTypes enumeration."""

    def test_values_and_aliases(self) -> None:
        """Verify integer enum values and PascalCase aliases."""
        assert DataSeriesTypes.OPEN.value == 0
        assert DataSeriesTypes.Open.value == 0
        assert DataSeriesTypes.HIGH.value == 1
        assert DataSeriesTypes.High.value == 1
        assert DataSeriesTypes.LOW.value == 2
        assert DataSeriesTypes.Low.value == 2
        assert DataSeriesTypes.CLOSE.value == 3
        assert DataSeriesTypes.Close.value == 3
        assert DataSeriesTypes.VOLUME.value == 4
        assert DataSeriesTypes.Volume.value == 4
        assert DataSeriesTypes.MEDIAN.value == 5
        assert DataSeriesTypes.Median.value == 5
        assert DataSeriesTypes.TYPICAL.value == 6
        assert DataSeriesTypes.Typical.value == 6
        assert DataSeriesTypes.WEIGHTED.value == 7
        assert DataSeriesTypes.Weighted.value == 7

    def test_from_name_valid(self) -> None:
        """Verify from_name with case-insensitive strings."""
        assert DataSeriesTypes.from_name("open") == DataSeriesTypes.OPEN
        assert DataSeriesTypes.from_name("HIGH") == DataSeriesTypes.HIGH
        assert DataSeriesTypes.from_name("Low") == DataSeriesTypes.LOW
        assert DataSeriesTypes.from_name("close") == DataSeriesTypes.CLOSE
        assert DataSeriesTypes.from_name("volume") == DataSeriesTypes.VOLUME
        assert DataSeriesTypes.from_name("Median") == DataSeriesTypes.MEDIAN
        assert DataSeriesTypes.from_name("typical") == DataSeriesTypes.TYPICAL
        assert DataSeriesTypes.from_name("weighted") == DataSeriesTypes.WEIGHTED

    def test_from_name_invalid(self) -> None:
        """Verify from_name raises ValueError on unknown names."""
        with pytest.raises(ValueError, match="Unknown DataSeriesTypes name"):
            DataSeriesTypes.from_name("INVALID_SERIES")


class TestMedianDataSeries:
    """Test suite for MedianDataSeries ((High + Low) / 2.0)."""

    def test_init_from_sequences(self) -> None:
        """Verify initialization from numeric sequences."""
        highs = [10.0, 12.0, 15.0]
        lows = [8.0, 10.0, 11.0]
        med = MedianDataSeries(highs, lows)
        assert len(med) == 3
        assert med.get(0) == pytest.approx(13.0)  # (15 + 11) / 2
        assert med.get(1) == pytest.approx(11.0)  # (12 + 10) / 2
        assert med.get(2) == pytest.approx(9.0)  # (10 + 8) / 2

    def test_init_from_data_series(self) -> None:
        """Verify initialization from DataSeries objects and properties."""
        high_series = DataSeries([100.0, 110.0], name="High")
        low_series = DataSeries([90.0, 95.0], name="Low")
        open_series = DataSeries([92.0, 96.0], name="Open")
        close_series = DataSeries([98.0, 105.0], name="Close")
        vol_series = DataSeries([1000.0, 1500.0], name="Volume")
        med = MedianDataSeries(
            high_series,
            low_series,
            open=open_series,
            close=close_series,
            volume=vol_series,
            name="CustomMedian",
        )
        assert med.name == "CustomMedian"
        assert med.High is high_series
        assert med.Low is low_series
        assert med.Open is open_series
        assert med.Close is close_series
        assert med.Volume is vol_series
        assert med.compute_value(0) == pytest.approx(95.0)  # (100 + 90) / 2
        assert med.compute_value(1) == pytest.approx(102.5)  # (110 + 95) / 2

    def test_compute_value_bounds(self) -> None:
        """Verify compute_value with out-of-bounds index."""
        med = MedianDataSeries([10.0], [5.0])
        assert med.compute_value(0) == pytest.approx(7.5)
        assert math.isnan(med.compute_value(1))
        assert math.isnan(med.compute_value(-1))

    def test_from_bars(self) -> None:
        """Verify factory from_bars constructor."""
        bars = [
            MarketBar(
                time=1000,
                open=10.0,
                high=12.0,
                low=8.0,
                close=11.0,
                tick_volume=10,
            ),
            MarketBar(
                time=2000,
                open=11.0,
                high=14.0,
                low=10.0,
                close=13.0,
                tick_volume=20,
            ),
        ]
        med = MedianDataSeries.from_bars(bars)
        assert len(med) == 2
        assert med.get(0) == pytest.approx(12.0)  # (14 + 10) / 2
        assert med.get(1) == pytest.approx(10.0)  # (12 + 8) / 2
        assert med.Open is not None and med.Open.get(0) == 11.0
        assert med.Close is not None and med.Close.get(0) == 13.0
        assert med.Volume is not None and med.Volume.get(0) == 20.0

    def test_add_bar(self) -> None:
        """Verify dynamic mutation via add_bar."""
        bars = [
            MarketBar(time=1000, open=10.0, high=12.0, low=8.0, close=11.0),
        ]
        med = MedianDataSeries.from_bars(bars)
        assert len(med) == 1
        med.add_bar(MarketBar(time=2000, open=12.0, high=16.0, low=10.0, close=15.0))
        assert len(med) == 2
        assert med.get(0) == pytest.approx(13.0)  # (16 + 10) / 2
        assert med.High.get(0) == 16.0
        assert med.Low.get(0) == 10.0

    def test_empty_series(self) -> None:
        """Verify empty initialization."""
        med = MedianDataSeries([], [])
        assert len(med) == 0
        assert math.isnan(med.get(0))
        assert len(med.to_numpy()) == 0


class TestTypicalDataSeries:
    """Test suite for TypicalDataSeries ((High + Low + Close) / 3.0)."""

    def test_init_from_sequences(self) -> None:
        """Verify initialization and typical formula calculation."""
        highs = [12.0, 15.0]
        lows = [9.0, 12.0]
        closes = [10.5, 13.5]
        typ = TypicalDataSeries(highs, lows, closes)
        assert len(typ) == 2
        # (12 + 9 + 10.5) / 3 = 31.5 / 3 = 10.5
        assert typ.compute_value(0) == pytest.approx(10.5)
        # (15 + 12 + 13.5) / 3 = 40.5 / 3 = 13.5
        assert typ.compute_value(1) == pytest.approx(13.5)
        assert typ.get(0) == pytest.approx(13.5)

    def test_from_bars_and_add_bar(self) -> None:
        """Verify from_bars and dynamic add_bar."""
        bars = [
            MarketBar(time=1000, open=10.0, high=12.0, low=9.0, close=11.0),
        ]
        typ = TypicalDataSeries.from_bars(bars)
        assert len(typ) == 1
        assert typ.get(0) == pytest.approx((12.0 + 9.0 + 11.0) / 3.0)
        assert typ.Close.get(0) == 11.0

        typ.add_bar(MarketBar(time=2000, open=11.0, high=14.0, low=10.0, close=12.0))
        assert len(typ) == 2
        assert typ.get(0) == pytest.approx((14.0 + 10.0 + 12.0) / 3.0)

    def test_compute_value_nan_handling(self) -> None:
        """Verify NaN handling in compute_value."""
        typ = TypicalDataSeries([10.0], [8.0], [float("nan")])
        assert math.isnan(typ.compute_value(0))


class TestWeightedDataSeries:
    """Test suite for WeightedDataSeries ((High + Low + 2*Close) / 4.0)."""

    def test_init_from_sequences(self) -> None:
        """Verify initialization and weighted formula calculation."""
        highs = [12.0, 16.0]
        lows = [8.0, 10.0]
        closes = [10.0, 15.0]
        # Bar 0: (12 + 8 + 20) / 4 = 40 / 4 = 10.0
        # Bar 1: (16 + 10 + 30) / 4 = 56 / 4 = 14.0
        wt = WeightedDataSeries(highs, lows, closes)
        assert len(wt) == 2
        assert wt.compute_value(0) == pytest.approx(10.0)
        assert wt.compute_value(1) == pytest.approx(14.0)
        assert wt.get(0) == pytest.approx(14.0)
        assert wt.get(1) == pytest.approx(10.0)

    def test_from_bars_and_add_bar(self) -> None:
        """Verify from_bars and dynamic add_bar."""
        bars = [
            MarketBar(time=1000, open=10.0, high=12.0, low=8.0, close=10.0),
        ]
        wt = WeightedDataSeries.from_bars(bars)
        assert len(wt) == 1
        assert wt.get(0) == pytest.approx(10.0)

        wt.add_bar(MarketBar(time=2000, open=10.0, high=16.0, low=10.0, close=15.0))
        assert len(wt) == 2
        assert wt.get(0) == pytest.approx((16.0 + 10.0 + 30.0) / 4.0)

    def test_compute_value_nan_handling(self) -> None:
        """Verify NaN handling in compute_value."""
        wt = WeightedDataSeries([10.0], [float("nan")], [10.0])
        assert math.isnan(wt.compute_value(0))


class TestDataSeriesFactoryMethods:
    """Test suite for DataSeries factory methods (create_median, create_typical, create_weighted)."""

    def test_create_median(self) -> None:
        """Verify DataSeries.create_median helper."""
        med = DataSeries.create_median([10.0, 12.0], [8.0, 10.0])
        assert isinstance(med, MedianDataSeries)
        assert med.get(0) == pytest.approx(11.0)

    def test_create_typical(self) -> None:
        """Verify DataSeries.create_typical helper."""
        typ = DataSeries.create_typical([12.0], [8.0], [10.0])
        assert isinstance(typ, TypicalDataSeries)
        assert typ.get(0) == pytest.approx(10.0)

    def test_create_weighted(self) -> None:
        """Verify DataSeries.create_weighted helper."""
        wt = DataSeries.create_weighted([12.0], [8.0], [10.0])
        assert isinstance(wt, WeightedDataSeries)
        assert wt.get(0) == pytest.approx(10.0)
