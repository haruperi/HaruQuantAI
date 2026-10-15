"""Shared asynchronous historical bars, tick reads, and columnar DataSeries kernel.

Description:
    Provides foundational market data structures, columnar DataSeries container,
    and historical market data readers for quantitative trading systems.
    Encapsulates broker-neutral market primitives (MarketBar, MarketTick, Timeframe),
    runtime bridge errors, the execution protocol (DataBackend), and high-throughput
    zero-copy conversion routines for NumPy, Polars, and PyArrow.

Purpose:
    FEAT-LIBS-DATA: Self-sufficient market data library, historical reader,
    and series kernel.

Key Capabilities:
    - FR-DATA-MARKET-PRIMITIVES: Standard timeframe enums, immutable bar and
      tick records.
      Associated: `Timeframe`, `MarketBar`, `MarketTick`, `BridgeError`.
      Logging: Pure numerical data structures with zero logging overhead.
    - FR-DATA-COLUMNAR-SERIES: High-performance columnar series kernel with
      dual-mode indexing.
      Associated: `DataSeries`, `DataSeries.get()`, `DataSeries.set()`.
      Logging: In-memory array operations with zero side effects.
    - FR-DATA-HISTORICAL-READS: Fetch chronological bars and millisecond ticks.
      Associated: `get_historical_bars()`, `get_ticks()`.
      Logging: DEBUG every read attempt with operation only, no payloads or paths.
    - FR-DATA-HISTORY-VALIDATION: Reject invalid or excessive historical data.
      Associated: `validate_rows()`, `validate_request()`.
      Logging: DEBUG validation attempts; errors carry bounded diagnostic codes.
    - FR-DATA-DATAFRAME-CONVERSIONS: Convert historical bars and ticks into structured
      pandas DataFrames.
      Associated: `bars_to_dataframe()`, `ticks_to_dataframe()`, `bars_to_df()`,
        `ticks_to_df()`.
    - FR-DATA-BROKER-BACKEND: Base market data provider adapter with Bars/Ticks
      dispatch.
      Associated: `DataBrokerBackend`, `DataBrokerBackend.fetch_bars()`,
        `DataBrokerBackend.fetch_ticks()`.
      Logging: DEBUG market data dispatch lifecycle through BaseBrokerBackend.
    - FR-DATA-DERIVED-SERIES: Derived price series and data series types enumeration.
      Associated: `DataSeriesTypes`, `MedianDataSeries`, `TypicalDataSeries`,
        `WeightedDataSeries`.
      Logging: Pure vectorized and on-the-fly series calculations with
        zero side effects.
    - FR-DATA-STREAMING-TICK-SIMULATOR: In-memory streaming intra-bar tick cursors.
      Associated: `TickEvent`, `SpreadsMap`, `ITickSimulator`,
        `DefaultTickSimulator`, `TSTickSimulator`.
      Logging: Pure in-memory streaming tick cursors with zero allocation overhead.
    - FR-DATA-BATCH-TICK-GENERATOR: Vectorized batch tick generation and Parquet
      streaming.
      Associated: `TicksGenerator`, `generate_ticks`, `generate_ticks_to_parquet`,
        `SUPPORTED_TICK_MODELS`, `SUPPORTED_SPREAD_MODELS`.
      Logging: DEBUG tick batch generation and Parquet streaming lifecycle.
    - FR-DATA-CHART-DEF-AND-CATALOG: Chart specifications and catalog metadata records.
      Associated: `ChartDef`, `DataInfo`.
      Logging: Pure in-memory metadata records with zero logging overhead.

Python API Usage:
    ```python
    from app.services.libs.data import (
        ChartDef,
        DataInfo,
        DataSeries,
        DataSeriesTypes,
        DefaultTickSimulator,
        MarketBar,
        MarketTick,
        MedianDataSeries,
        TickEvent,
        TicksGenerator,
        Timeframe,
        TypicalDataSeries,
        WeightedDataSeries,
        bars_to_dataframe,
        generate_ticks,
        generate_ticks_to_parquet,
        get_historical_bars,
        ticks_to_dataframe,
    )

    series = DataSeries([10.0, 11.5, 12.0], name="Close")
    current = series.get(0)
    median = MedianDataSeries([10.0, 12.0], [8.0, 9.0])
    bars = await get_historical_bars(backend, "EURUSD", Timeframe.PERIOD_M1)
    bars_df = bars_to_dataframe(bars)

    # In-memory streaming tick simulation
    sim = DefaultTickSimulator()
    sim.init(bars)
    event = TickEvent()
    while sim.get_next_tick(event):
        pass  # O(1) memory traversal

    # Chart specification and compatibility check
    chart_m1 = ChartDef("EURUSD", "M1")
    chart_h1 = ChartDef("EURUSD", "H1")
    assert chart_h1.can_be_computed_from(chart_m1)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_data_series.py --no-cov
    uv run pytest tests/unit/services/test_tick_simulation.py --no-cov
    uv run pytest tests/unit/services/test_chart_def_data_info.py --no-cov
    ```
"""

from __future__ import annotations

import array
import math
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict, dataclass, fields, replace
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any, Literal, Protocol, overload, override

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
from app.host.logging import get_logger
from app.services.brokers.base import BaseBrokerBackend, BridgeError
from app.services.libs.generators import RandomGenerator

logger = get_logger(__name__)

MAX_RECORDS = 1000
MAX_POSITION = 2**31 - 1
READ_TIMEOUT = 60.0

__all__ = [
    "BAR_COLUMNS",
    "MAX_POSITION",
    "MAX_RECORDS",
    "PHASE_CLOSE_CODE",
    "PHASE_HIGH_CODE",
    "PHASE_LOW_CODE",
    "PHASE_OPEN_CODE",
    "READ_TIMEOUT",
    "SPREAD_FIXED",
    "SPREAD_NATIVE",
    "SPREAD_VARIABLE",
    "SUPPORTED_SPREAD_MODELS",
    "SUPPORTED_TICK_MODELS",
    "TICK_COLUMNS",
    "TICK_MODEL_GENERATED",
    "TICK_MODEL_OHLC_M1",
    "TICK_MODEL_REAL",
    "TICK_MODEL_TRADING_BAR",
    "TIMEFRAME_SECONDS",
    "BridgeError",
    "ChartDef",
    "DataBackend",
    "DataBrokerBackend",
    "DataInfo",
    "DataSeries",
    "DataSeriesTypes",
    "DefaultTickSimulator",
    "ITickSimulator",
    "MarketBar",
    "MarketTick",
    "MedianDataSeries",
    "SpreadsMap",
    "TSTickSimulator",
    "TickEvent",
    "TicksGenerator",
    "Timeframe",
    "TypicalDataSeries",
    "WeightedDataSeries",
    "bars_to_dataframe",
    "bars_to_df",
    "generate_ticks",
    "generate_ticks_to_parquet",
    "get_historical_bars",
    "get_ticks",
    "ticks_to_dataframe",
    "ticks_to_df",
    "validate_request",
    "validate_rows",
]


class Timeframe(StrEnum):
    """Chart and series timeframe enumeration."""

    PERIOD_CURRENT = "CURRENT"
    PERIOD_M1 = "M1"
    PERIOD_M2 = "M2"
    PERIOD_M3 = "M3"
    PERIOD_M4 = "M4"
    PERIOD_M5 = "M5"
    PERIOD_M6 = "M6"
    PERIOD_M10 = "M10"
    PERIOD_M12 = "M12"
    PERIOD_M15 = "M15"
    PERIOD_M20 = "M20"
    PERIOD_M30 = "M30"
    PERIOD_H1 = "H1"
    PERIOD_H2 = "H2"
    PERIOD_H3 = "H3"
    PERIOD_H4 = "H4"
    PERIOD_H6 = "H6"
    PERIOD_H8 = "H8"
    PERIOD_H12 = "H12"
    PERIOD_D1 = "D1"
    PERIOD_W1 = "W1"
    PERIOD_MN1 = "MN1"

    # Shorthand aliases
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M10 = "M10"
    M12 = "M12"
    M15 = "M15"
    M20 = "M20"
    M30 = "M30"
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H6 = "H6"
    H8 = "H8"
    H12 = "H12"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    def to_seconds(self) -> int:
        """Convert timeframe duration to whole seconds."""
        val = self.value
        if val.startswith("M") and self != Timeframe.PERIOD_MN1:
            return int(val[1:]) * 60
        if val.startswith("H"):
            return int(val[1:]) * 3600
        fixed = {
            Timeframe.PERIOD_D1: 86400,
            Timeframe.PERIOD_W1: 604800,
            Timeframe.PERIOD_MN1: 2419200,
        }
        return fixed.get(self, 0)

    def to_minutes(self) -> int:
        """Convert timeframe duration to whole minutes."""
        return self.to_seconds() // 60

    @classmethod
    def from_string(cls, name: str) -> Timeframe:
        """Parse timeframe from common string representations.

        Args:
            name: String such as 'M1', '1m', 'H1', '1h', 'D1', '1d', etc.

        Returns:
            Matching Timeframe member.

        Raises:
            ValueError: If string format cannot be mapped to a standard timeframe.
        """
        cleaned = name.strip().upper()
        mapping: dict[str, Timeframe] = {
            "M1": cls.PERIOD_M1,
            "1M": cls.PERIOD_M1,
            "1MIN": cls.PERIOD_M1,
            "M2": cls.PERIOD_M2,
            "2M": cls.PERIOD_M2,
            "M3": cls.PERIOD_M3,
            "3M": cls.PERIOD_M3,
            "M4": cls.PERIOD_M4,
            "4M": cls.PERIOD_M4,
            "M5": cls.PERIOD_M5,
            "5M": cls.PERIOD_M5,
            "5MIN": cls.PERIOD_M5,
            "M6": cls.PERIOD_M6,
            "6M": cls.PERIOD_M6,
            "M10": cls.PERIOD_M10,
            "10M": cls.PERIOD_M10,
            "M12": cls.PERIOD_M12,
            "12M": cls.PERIOD_M12,
            "M15": cls.PERIOD_M15,
            "15M": cls.PERIOD_M15,
            "15MIN": cls.PERIOD_M15,
            "M20": cls.PERIOD_M20,
            "20M": cls.PERIOD_M20,
            "M30": cls.PERIOD_M30,
            "30M": cls.PERIOD_M30,
            "30MIN": cls.PERIOD_M30,
            "H1": cls.PERIOD_H1,
            "1H": cls.PERIOD_H1,
            "60M": cls.PERIOD_H1,
            "H2": cls.PERIOD_H2,
            "2H": cls.PERIOD_H2,
            "H3": cls.PERIOD_H3,
            "3H": cls.PERIOD_H3,
            "H4": cls.PERIOD_H4,
            "4H": cls.PERIOD_H4,
            "240M": cls.PERIOD_H4,
            "H6": cls.PERIOD_H6,
            "6H": cls.PERIOD_H6,
            "H8": cls.PERIOD_H8,
            "8H": cls.PERIOD_H8,
            "H12": cls.PERIOD_H12,
            "12H": cls.PERIOD_H12,
            "D1": cls.PERIOD_D1,
            "1D": cls.PERIOD_D1,
            "DAY": cls.PERIOD_D1,
            "W1": cls.PERIOD_W1,
            "1W": cls.PERIOD_W1,
            "WEEK": cls.PERIOD_W1,
            "MN1": cls.PERIOD_MN1,
            "1MN": cls.PERIOD_MN1,
            "MONTH": cls.PERIOD_MN1,
        }
        if cleaned in mapping:
            return mapping[cleaned]
        raise ValueError(f"Unknown timeframe identifier: {name!r}")


TIMEFRAME_SECONDS: dict[Timeframe, int] = {
    frame: frame.to_seconds()
    for frame in Timeframe
    if frame != Timeframe.PERIOD_CURRENT
}


@dataclass(frozen=True, slots=True)
class MarketBar:
    """Historical OHLC bar with its UTC opening time in epoch seconds."""

    time: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = 0
    spread: int = 0
    real_volume: int = 0

    @property
    def is_bullish(self) -> bool:
        """Check if candle closed higher than open."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Check if candle closed lower than open."""
        return self.close < self.open

    @property
    def is_doji(self) -> bool:
        """Check if candle closed at open."""
        return self.close == self.open

    @property
    def range(self) -> float:
        """Calculate total bar price range (High - Low)."""
        return self.high - self.low

    @property
    def body(self) -> float:
        """Calculate candle body size abs(Close - Open)."""
        return abs(self.close - self.open)

    @property
    def volume(self) -> float:
        """Calculate primary volume (real_volume if present, else tick_volume)."""
        return float(self.real_volume or self.tick_volume)


@dataclass(frozen=True, slots=True)
class MarketTick:
    """Historical tick retaining UTC epoch milliseconds and native flags."""

    time_msc: int
    bid: float
    ask: float
    last: float = 0.0
    volume: int = 0
    flags: int = 0
    volume_real: float = 0.0

    @property
    def spread(self) -> float:
        """Calculate instantaneous spread (Ask - Bid)."""
        return self.ask - self.bid

    @property
    def mid(self) -> float:
        """Calculate midpoint price."""
        return (self.ask + self.bid) / 2.0

    @property
    def time(self) -> int:
        """UTC epoch milliseconds alias for time_msc."""
        return self.time_msc


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


class DataSeries:
    """High-performance columnar numerical series container."""

    def __init__(
        self,
        values: Sequence[float] | np.ndarray[Any, Any] | None = None,
        *,
        name: str = "",
        chart_type: str = "Line",
        color: str = "",
        line_name: str = "",
        show_in_chart: bool = True,
        show_zero_values: bool = True,
        indy_starting_bar: int = 0,
        shift: int = 0,
    ) -> None:
        """Initialize DataSeries with optional values and metadata.

        Args:
            values: Initial sequence or numpy array of float values.
            name: Series name identifier.
            chart_type: Chart display type (e.g. 'Line', 'Bar', 'Histogram').
            color: Visual representation color.
            line_name: Secondary indicator line identifier.
            show_in_chart: Visibility flag in charts.
            show_zero_values: Whether zero values are charted.
            indy_starting_bar: Warmup bar count before indicator is computable.
            shift: Global access shift offset applied to all shift-based calls.
        """
        self.name = name
        self.chart_type = chart_type
        self.color = color
        self.line_name = line_name
        self.show_in_chart = show_in_chart
        self.show_zero_values = show_zero_values
        self.indy_starting_bar = indy_starting_bar
        self.shift = shift
        self.computed_until_index = -1

        if values is None:
            self._data = array.array("d")
        elif isinstance(values, np.ndarray):
            self._data = array.array("d", values.astype(np.float64).ravel())
        else:
            self._data = array.array("d", (float(v) for v in values))

    def __len__(self) -> int:
        """Return total count of values in series."""
        return len(self._data)

    def size(self) -> int:
        """Return total count of values in series."""
        return len(self._data)

    def get(self, shift: int = 0) -> float:
        """Retrieve value at specified bar shift.

        Args:
            shift: Historical offset (0 is newest/current bar, 1 is 1 bar ago).

        Returns:
            Floating-point value at effective shift, or NaN if out of bounds
            or prior to indy_starting_bar warmup period.
        """
        eff_shift = shift + self.shift
        n = len(self._data)
        if eff_shift < 0 or eff_shift >= n:
            return float("nan")

        chronological_idx = n - 1 - eff_shift
        if chronological_idx < self.indy_starting_bar:
            return float("nan")

        return self._data[chronological_idx]

    @overload
    def set(self, shift_or_value: float) -> None: ...

    @overload
    def set(self, shift_or_value: int, value: float) -> None: ...

    def set(
        self,
        shift_or_value: float,
        value: float | None = None,
    ) -> None:
        """Set series value at current bar (shift=0) or specified shift.

        Args:
            shift_or_value: Value when single arg, else historical shift.
            value: Float value when shift is provided as first argument.
        """
        n = len(self._data)
        if value is None:
            val = float(shift_or_value)
            eff_shift = self.shift
        else:
            val = float(value)
            eff_shift = int(shift_or_value) + self.shift

        if 0 <= eff_shift < n:
            self._data[n - 1 - eff_shift] = val

    def add(self, value: float) -> None:
        """Append a new value to the end of the series (advancing series length).

        Args:
            value: Value to append.
        """
        self._data.append(float(value))

    def add_values(self, count: int, default_val: float = float("nan")) -> None:
        """Append multiple values to the series.

        Args:
            count: Number of elements to append.
            default_val: Default value for appended elements.
        """
        if count > 0:
            self._data.extend([float(default_val)] * count)

    def get_double(self, real_index: int) -> float:
        """Retrieve value by zero-based chronological index (0 is oldest).

        Args:
            real_index: Physical chronological index.

        Returns:
            Value at index, or NaN if out of bounds.
        """
        if 0 <= real_index < len(self._data):
            return self._data[real_index]
        return float("nan")

    def set_double(self, real_index: int, value: float) -> None:
        """Set value by zero-based chronological index (0 is oldest).

        Args:
            real_index: Physical chronological index.
            value: Value to store.
        """
        if 0 <= real_index < len(self._data):
            self._data[real_index] = float(value)

    def get_rounded(self, shift: int = 0, decimals: int = 4) -> float:
        """Retrieve value at shift rounded to specified decimals.

        Args:
            shift: Historical offset.
            decimals: Number of decimal places.

        Returns:
            Rounded float value, or NaN.
        """
        val = self.get(shift)
        return round(val, decimals) if not math.isnan(val) else val

    # --- Condition Predicates ---

    def is_rising(self, shift: int = 0, periods: int = 1) -> bool:
        """Check if value at shift is strictly greater than (shift + periods).

        Args:
            shift: Target bar shift.
            periods: Number of bars backward to compare against.

        Returns:
            True if strictly rising, False otherwise.
        """
        v0 = self.get(shift)
        v1 = self.get(shift + periods)
        return not (math.isnan(v0) or math.isnan(v1)) and v0 > v1

    def is_falling(self, shift: int = 0, periods: int = 1) -> bool:
        """Check if value at shift is strictly lower than (shift + periods).

        Args:
            shift: Target bar shift.
            periods: Number of bars backward to compare against.

        Returns:
            True if strictly falling, False otherwise.
        """
        v0 = self.get(shift)
        v1 = self.get(shift + periods)
        return not (math.isnan(v0) or math.isnan(v1)) and v0 < v1

    def crosses_above(self, level: float | DataSeries, shift: int = 0) -> bool:
        """Check if series crossed above a level/series between shift+1 and shift.

        Args:
            level: Constant float threshold or another DataSeries.
            shift: Target bar shift.

        Returns:
            True if upward crossing occurred.
        """
        curr = self.get(shift)
        prev = self.get(shift + 1)
        curr_lvl = level.get(shift) if isinstance(level, DataSeries) else level
        prev_lvl = level.get(shift + 1) if isinstance(level, DataSeries) else level

        if (
            math.isnan(curr)
            or math.isnan(prev)
            or math.isnan(curr_lvl)
            or math.isnan(prev_lvl)
        ):
            return False
        return prev <= prev_lvl and curr > curr_lvl

    def crosses_below(self, level: float | DataSeries, shift: int = 0) -> bool:
        """Check if series crossed below a level/series between shift+1 and shift.

        Args:
            level: Constant float threshold or another DataSeries.
            shift: Target bar shift.

        Returns:
            True if downward crossing occurred.
        """
        curr = self.get(shift)
        prev = self.get(shift + 1)
        curr_lvl = level.get(shift) if isinstance(level, DataSeries) else level
        prev_lvl = level.get(shift + 1) if isinstance(level, DataSeries) else level

        if (
            math.isnan(curr)
            or math.isnan(prev)
            or math.isnan(curr_lvl)
            or math.isnan(prev_lvl)
        ):
            return False
        return prev >= prev_lvl and curr < curr_lvl

    def is_higher(self, level: float | DataSeries, shift: int = 0) -> bool:
        """Check if value at shift is strictly greater than level/series.

        Args:
            level: Constant threshold or another DataSeries.
            shift: Target bar shift.

        Returns:
            True if higher, False otherwise.
        """
        val = self.get(shift)
        lvl = level.get(shift) if isinstance(level, DataSeries) else level
        if math.isnan(val) or math.isnan(lvl):
            return False
        return val > lvl

    def is_lower(self, level: float | DataSeries, shift: int = 0) -> bool:
        """Check if value at shift is strictly lower than level/series.

        Args:
            level: Constant threshold or another DataSeries.
            shift: Target bar shift.

        Returns:
            True if lower, False otherwise.
        """
        val = self.get(shift)
        lvl = level.get(shift) if isinstance(level, DataSeries) else level
        if math.isnan(val) or math.isnan(lvl):
            return False
        return val < lvl

    # --- Columnar Interoperability ---

    def to_numpy(self) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Export series as a C-contiguous float64 NumPy array (chronological order).

        Returns:
            1D float64 NumPy array.
        """
        return np.frombuffer(self._data, dtype=np.float64)

    def to_polars(self) -> pl.Series:
        """Export series as a Polars Float64 Series.

        Returns:
            Polars Series with series name.
        """
        return pl.Series(self.name or "value", self.to_numpy())

    def to_arrow(self) -> pa.Array:
        """Export series as a PyArrow double Array.

        Returns:
            PyArrow double Array.
        """
        return pa.array(self.to_numpy())

    @classmethod
    def from_numpy(
        cls,
        arr: np.ndarray[Any, Any],
        name: str = "",
    ) -> DataSeries:
        """Create DataSeries from NumPy array.

        Args:
            arr: 1D NumPy numerical array.
            name: Optional series name.

        Returns:
            New DataSeries instance.
        """
        return cls(arr, name=name)

    @classmethod
    def from_polars(cls, series: pl.Series) -> DataSeries:
        """Create DataSeries from Polars Series.

        Args:
            series: Polars numerical Series.

        Returns:
            New DataSeries instance.
        """
        return cls(series.to_numpy(), name=series.name)

    @classmethod
    def from_arrow(cls, array_data: pa.Array, name: str = "") -> DataSeries:
        """Create DataSeries from PyArrow Array.

        Args:
            array_data: PyArrow double Array.
            name: Optional series name.

        Returns:
            New DataSeries instance.
        """
        return cls(array_data.to_numpy(), name=name)

    def __iter__(self) -> Iterator[float]:
        """Iterate through values in chronological order (oldest to newest)."""
        return iter(self._data)

    def __getitem__(
        self, item: int | slice
    ) -> float | np.ndarray[Any, np.dtype[np.float64]]:
        """Access values via slice or shift index."""
        if isinstance(item, slice):
            return self.to_numpy()[item]
        return self.get(item)

    @staticmethod
    def create_median(
        high: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        low: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        **kwargs: Any,
    ) -> MedianDataSeries:
        """Create a MedianDataSeries from High and Low price data."""
        return MedianDataSeries(high, low, **kwargs)

    @staticmethod
    def create_typical(
        high: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        low: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        close: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        **kwargs: Any,
    ) -> TypicalDataSeries:
        """Create a TypicalDataSeries from High, Low, and Close price data."""
        return TypicalDataSeries(high, low, close, **kwargs)

    @staticmethod
    def create_weighted(
        high: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        low: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        close: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        **kwargs: Any,
    ) -> WeightedDataSeries:
        """Create a WeightedDataSeries from High, Low, and Close price data."""
        return WeightedDataSeries(high, low, close, **kwargs)


class DataSeriesTypes(IntEnum):
    """Enumeration of standard bar series data types matching SQX DataSeriesTypes.

    Values correspond to standard OHLCV, derived price series, and volume types:
    - OPEN / Open (0)
    - HIGH / High (1)
    - LOW / Low (2)
    - CLOSE / Close (3)
    - VOLUME / Volume (4)
    - MEDIAN / Median (5) - (High + Low) / 2
    - TYPICAL / Typical (6) - (High + Low + Close) / 3
    - WEIGHTED / Weighted (7) - (High + Low + 2*Close) / 4
    """

    OPEN = 0
    HIGH = 1
    LOW = 2
    CLOSE = 3
    VOLUME = 4
    MEDIAN = 5
    TYPICAL = 6
    WEIGHTED = 7

    # SQX PascalCase aliases
    Open = 0
    High = 1
    Low = 2
    Close = 3
    Volume = 4
    Median = 5
    Typical = 6
    Weighted = 7

    @classmethod
    def from_name(cls, name: str) -> DataSeriesTypes:
        """Resolve series type from name string case-insensitively.

        Args:
            name: Series name (e.g. 'close', 'Open', 'TYPICAL', 'median').

        Returns:
            Corresponding DataSeriesTypes enum member.

        Raises:
            ValueError: If name is not a recognized series type.
        """
        key = name.strip().upper()
        for member in cls:
            if member.name == key:
                return member
        raise ValueError(f"Unknown DataSeriesTypes name: {name!r}")


class MedianDataSeries(DataSeries):
    """Dynamic median price series calculating (High + Low) / 2.0.

    Matches SQX `com.strategyquant.datalib.dataseries.MedianDataSeries`.
    Provides on-the-fly and vectorized computation of the median price
    for a sequence of bars or High and Low price series.
    """

    def __init__(
        self,
        high: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        low: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        *,
        open: DataSeries | Sequence[float] | np.ndarray[Any, Any] | None = None,  # noqa: A002
        close: DataSeries | Sequence[float] | np.ndarray[Any, Any] | None = None,
        volume: DataSeries | Sequence[float] | np.ndarray[Any, Any] | None = None,
        name: str = "Median",
        chart_type: str = "Line",
        color: str = "",
        line_name: str = "",
        show_in_chart: bool = True,
        show_zero_values: bool = True,
        indy_starting_bar: int = 0,
        shift: int = 0,
    ) -> None:
        """Initialize MedianDataSeries with High and Low data series.

        Args:
            high: High price series or sequence.
            low: Low price series or sequence.
            open: Optional Open price series or sequence.
            close: Optional Close price series or sequence.
            volume: Optional Volume series or sequence.
            name: Series name identifier.
            chart_type: Chart display type.
            color: Visual representation color.
            line_name: Secondary indicator line identifier.
            show_in_chart: Visibility flag in charts.
            show_zero_values: Whether zero values are charted.
            indy_starting_bar: Warmup bar count.
            shift: Global access shift offset.
        """
        self.high: DataSeries = (
            high if isinstance(high, DataSeries) else DataSeries(high, name="High")
        )
        self.low: DataSeries = (
            low if isinstance(low, DataSeries) else DataSeries(low, name="Low")
        )
        self.open: DataSeries | None = (
            open
            if (open is None or isinstance(open, DataSeries))
            else DataSeries(open, name="Open")
        )
        self.close: DataSeries | None = (
            close
            if (close is None or isinstance(close, DataSeries))
            else DataSeries(close, name="Close")
        )
        self.volume: DataSeries | None = (
            volume
            if (volume is None or isinstance(volume, DataSeries))
            else DataSeries(volume, name="Volume")
        )

        n = min(len(self.high), len(self.low))
        if n > 0:
            h_arr = self.high.to_numpy()[:n]
            l_arr = self.low.to_numpy()[:n]
            med_vals = (h_arr + l_arr) / 2.0
        else:
            med_vals = np.array([], dtype=np.float64)

        super().__init__(
            med_vals,
            name=name,
            chart_type=chart_type,
            color=color,
            line_name=line_name,
            show_in_chart=show_in_chart,
            show_zero_values=show_zero_values,
            indy_starting_bar=indy_starting_bar,
            shift=shift,
        )

    @property
    def High(self) -> DataSeries:  # noqa: N802
        """SQX compatibility alias for High series."""
        return self.high

    @property
    def Low(self) -> DataSeries:  # noqa: N802
        """SQX compatibility alias for Low series."""
        return self.low

    @property
    def Open(self) -> DataSeries | None:  # noqa: N802
        """SQX compatibility alias for Open series."""
        return self.open

    @property
    def Close(self) -> DataSeries | None:  # noqa: N802
        """SQX compatibility alias for Close series."""
        return self.close

    @property
    def Volume(self) -> DataSeries | None:  # noqa: N802
        """SQX compatibility alias for Volume series."""
        return self.volume

    def compute_value(self, real_index: int) -> float:
        """Compute median value (High + Low) / 2.0 at zero-based chronological index.

        Args:
            real_index: Zero-based chronological index (0 is oldest).

        Returns:
            Median float value, or NaN if out of bounds.
        """
        high_val = self.high.get_double(real_index)
        low_val = self.low.get_double(real_index)
        if math.isnan(high_val) or math.isnan(low_val):
            return float("nan")
        return (high_val + low_val) / 2.0

    def add_bar(self, bar: MarketBar) -> None:
        """Append a bar to the underlying series and compute its median value.

        Args:
            bar: MarketBar record to append.
        """
        self.high.add(bar.high)
        self.low.add(bar.low)
        if self.open is not None:
            self.open.add(bar.open)
        if self.close is not None:
            self.close.add(bar.close)
        if self.volume is not None:
            self.volume.add(bar.volume)
        self.add((bar.high + bar.low) / 2.0)

    @classmethod
    def from_bars(
        cls,
        bars: Sequence[MarketBar],
        *,
        name: str = "Median",
        **kwargs: Any,
    ) -> MedianDataSeries:
        """Construct MedianDataSeries directly from a sequence of MarketBar records.

        Args:
            bars: Sequence of MarketBar objects.
            name: Series name.
            **kwargs: Additional keyword arguments passed to constructor.

        Returns:
            New MedianDataSeries instance.
        """
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        opens = [b.open for b in bars]
        closes = [b.close for b in bars]
        volumes = [b.volume for b in bars]
        return cls(
            high=highs,
            low=lows,
            open=opens,
            close=closes,
            volume=volumes,
            name=name,
            **kwargs,
        )


class TypicalDataSeries(DataSeries):
    """Dynamic typical price series calculating (High + Low + Close) / 3.0.

    Matches SQX `com.strategyquant.datalib.dataseries.TypicalDataSeries`.
    Provides on-the-fly and vectorized computation of the typical price
    for a sequence of bars or High, Low, and Close price series.
    """

    def __init__(
        self,
        high: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        low: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        close: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        *,
        open: DataSeries | Sequence[float] | np.ndarray[Any, Any] | None = None,  # noqa: A002
        volume: DataSeries | Sequence[float] | np.ndarray[Any, Any] | None = None,
        name: str = "Typical",
        chart_type: str = "Line",
        color: str = "",
        line_name: str = "",
        show_in_chart: bool = True,
        show_zero_values: bool = True,
        indy_starting_bar: int = 0,
        shift: int = 0,
    ) -> None:
        """Initialize TypicalDataSeries with High, Low, and Close series.

        Args:
            high: High price series or sequence.
            low: Low price series or sequence.
            close: Close price series or sequence.
            open: Optional Open price series or sequence.
            volume: Optional Volume series or sequence.
            name: Series name identifier.
            chart_type: Chart display type.
            color: Visual representation color.
            line_name: Secondary indicator line identifier.
            show_in_chart: Visibility flag in charts.
            show_zero_values: Whether zero values are charted.
            indy_starting_bar: Warmup bar count.
            shift: Global access shift offset.
        """
        self.high: DataSeries = (
            high if isinstance(high, DataSeries) else DataSeries(high, name="High")
        )
        self.low: DataSeries = (
            low if isinstance(low, DataSeries) else DataSeries(low, name="Low")
        )
        self.close: DataSeries = (
            close if isinstance(close, DataSeries) else DataSeries(close, name="Close")
        )
        self.open: DataSeries | None = (
            open
            if (open is None or isinstance(open, DataSeries))
            else DataSeries(open, name="Open")
        )
        self.volume: DataSeries | None = (
            volume
            if (volume is None or isinstance(volume, DataSeries))
            else DataSeries(volume, name="Volume")
        )

        n = min(len(self.high), len(self.low), len(self.close))
        if n > 0:
            h_arr = self.high.to_numpy()[:n]
            l_arr = self.low.to_numpy()[:n]
            c_arr = self.close.to_numpy()[:n]
            typ_vals = (h_arr + l_arr + c_arr) / 3.0
        else:
            typ_vals = np.array([], dtype=np.float64)

        super().__init__(
            typ_vals,
            name=name,
            chart_type=chart_type,
            color=color,
            line_name=line_name,
            show_in_chart=show_in_chart,
            show_zero_values=show_zero_values,
            indy_starting_bar=indy_starting_bar,
            shift=shift,
        )

    @property
    def High(self) -> DataSeries:  # noqa: N802
        """SQX compatibility alias for High series."""
        return self.high

    @property
    def Low(self) -> DataSeries:  # noqa: N802
        """SQX compatibility alias for Low series."""
        return self.low

    @property
    def Close(self) -> DataSeries:  # noqa: N802
        """SQX compatibility alias for Close series."""
        return self.close

    @property
    def Open(self) -> DataSeries | None:  # noqa: N802
        """SQX compatibility alias for Open series."""
        return self.open

    @property
    def Volume(self) -> DataSeries | None:  # noqa: N802
        """SQX compatibility alias for Volume series."""
        return self.volume

    def compute_value(self, real_index: int) -> float:
        """Compute typical price (High + Low + Close) / 3.0 at chronological index.

        Args:
            real_index: Zero-based chronological index (0 is oldest).

        Returns:
            Typical price float value, or NaN if out of bounds.
        """
        high_val = self.high.get_double(real_index)
        low_val = self.low.get_double(real_index)
        close_val = self.close.get_double(real_index)
        if math.isnan(high_val) or math.isnan(low_val) or math.isnan(close_val):
            return float("nan")
        return (high_val + low_val + close_val) / 3.0

    def add_bar(self, bar: MarketBar) -> None:
        """Append a bar to the underlying series and compute its typical value.

        Args:
            bar: MarketBar record to append.
        """
        self.high.add(bar.high)
        self.low.add(bar.low)
        self.close.add(bar.close)
        if self.open is not None:
            self.open.add(bar.open)
        if self.volume is not None:
            self.volume.add(bar.volume)
        self.add((bar.high + bar.low + bar.close) / 3.0)

    @classmethod
    def from_bars(
        cls,
        bars: Sequence[MarketBar],
        *,
        name: str = "Typical",
        **kwargs: Any,
    ) -> TypicalDataSeries:
        """Construct TypicalDataSeries directly from a sequence of MarketBar records.

        Args:
            bars: Sequence of MarketBar objects.
            name: Series name.
            **kwargs: Additional keyword arguments passed to constructor.

        Returns:
            New TypicalDataSeries instance.
        """
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        closes = [b.close for b in bars]
        opens = [b.open for b in bars]
        volumes = [b.volume for b in bars]
        return cls(
            high=highs,
            low=lows,
            close=closes,
            open=opens,
            volume=volumes,
            name=name,
            **kwargs,
        )


class WeightedDataSeries(DataSeries):
    """Dynamic weighted price series calculating (High + Low + 2*Close) / 4.0.

    Matches SQX `com.strategyquant.datalib.dataseries.WeightedDataSeries`.
    Provides on-the-fly and vectorized computation of the weighted price
    for a sequence of bars or High, Low, and Close price series.
    """

    def __init__(
        self,
        high: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        low: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        close: DataSeries | Sequence[float] | np.ndarray[Any, Any],
        *,
        open: DataSeries | Sequence[float] | np.ndarray[Any, Any] | None = None,  # noqa: A002
        volume: DataSeries | Sequence[float] | np.ndarray[Any, Any] | None = None,
        name: str = "Weighted",
        chart_type: str = "Line",
        color: str = "",
        line_name: str = "",
        show_in_chart: bool = True,
        show_zero_values: bool = True,
        indy_starting_bar: int = 0,
        shift: int = 0,
    ) -> None:
        """Initialize WeightedDataSeries with High, Low, and Close series.

        Args:
            high: High price series or sequence.
            low: Low price series or sequence.
            close: Close price series or sequence.
            open: Optional Open price series or sequence.
            volume: Optional Volume series or sequence.
            name: Series name identifier.
            chart_type: Chart display type.
            color: Visual representation color.
            line_name: Secondary indicator line identifier.
            show_in_chart: Visibility flag in charts.
            show_zero_values: Whether zero values are charted.
            indy_starting_bar: Warmup bar count.
            shift: Global access shift offset.
        """
        self.high: DataSeries = (
            high if isinstance(high, DataSeries) else DataSeries(high, name="High")
        )
        self.low: DataSeries = (
            low if isinstance(low, DataSeries) else DataSeries(low, name="Low")
        )
        self.close: DataSeries = (
            close if isinstance(close, DataSeries) else DataSeries(close, name="Close")
        )
        self.open: DataSeries | None = (
            open
            if (open is None or isinstance(open, DataSeries))
            else DataSeries(open, name="Open")
        )
        self.volume: DataSeries | None = (
            volume
            if (volume is None or isinstance(volume, DataSeries))
            else DataSeries(volume, name="Volume")
        )

        n = min(len(self.high), len(self.low), len(self.close))
        if n > 0:
            h_arr = self.high.to_numpy()[:n]
            l_arr = self.low.to_numpy()[:n]
            c_arr = self.close.to_numpy()[:n]
            wt_vals = (h_arr + l_arr + 2.0 * c_arr) / 4.0
        else:
            wt_vals = np.array([], dtype=np.float64)

        super().__init__(
            wt_vals,
            name=name,
            chart_type=chart_type,
            color=color,
            line_name=line_name,
            show_in_chart=show_in_chart,
            show_zero_values=show_zero_values,
            indy_starting_bar=indy_starting_bar,
            shift=shift,
        )

    @property
    def High(self) -> DataSeries:  # noqa: N802
        """SQX compatibility alias for High series."""
        return self.high

    @property
    def Low(self) -> DataSeries:  # noqa: N802
        """SQX compatibility alias for Low series."""
        return self.low

    @property
    def Close(self) -> DataSeries:  # noqa: N802
        """SQX compatibility alias for Close series."""
        return self.close

    @property
    def Open(self) -> DataSeries | None:  # noqa: N802
        """SQX compatibility alias for Open series."""
        return self.open

    @property
    def Volume(self) -> DataSeries | None:  # noqa: N802
        """SQX compatibility alias for Volume series."""
        return self.volume

    def compute_value(self, real_index: int) -> float:
        """Compute weighted price (High + Low + 2*Close) / 4.0 at chronological index.

        Args:
            real_index: Zero-based chronological index (0 is oldest).

        Returns:
            Weighted price float value, or NaN if out of bounds.
        """
        high_val = self.high.get_double(real_index)
        low_val = self.low.get_double(real_index)
        close_val = self.close.get_double(real_index)
        if math.isnan(high_val) or math.isnan(low_val) or math.isnan(close_val):
            return float("nan")
        return (high_val + low_val + 2.0 * close_val) / 4.0

    def add_bar(self, bar: MarketBar) -> None:
        """Append a bar to the underlying series and compute its weighted value.

        Args:
            bar: MarketBar record to append.
        """
        self.high.add(bar.high)
        self.low.add(bar.low)
        self.close.add(bar.close)
        if self.open is not None:
            self.open.add(bar.open)
        if self.volume is not None:
            self.volume.add(bar.volume)
        self.add((bar.high + bar.low + 2.0 * bar.close) / 4.0)

    @classmethod
    def from_bars(
        cls,
        bars: Sequence[MarketBar],
        *,
        name: str = "Weighted",
        **kwargs: Any,
    ) -> WeightedDataSeries:
        """Construct WeightedDataSeries directly from a sequence of MarketBar records.

        Args:
            bars: Sequence of MarketBar objects.
            name: Series name.
            **kwargs: Additional keyword arguments passed to constructor.

        Returns:
            New WeightedDataSeries instance.
        """
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        closes = [b.close for b in bars]
        opens = [b.open for b in bars]
        volumes = [b.volume for b in bars]
        return cls(
            high=highs,
            low=lows,
            close=closes,
            open=opens,
            volume=volumes,
            name=name,
            **kwargs,
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


# ============================================================================
# Component 1: In-Memory Streaming Tick Cursor (SQX ITickSimulator / Default)
# ============================================================================


_TICKS_PER_BAR = 4
_CLOSE_TICK_INDEX = 3
_S_TO_MS_THRESHOLD = 100_000_000_000


@dataclass
class TickEvent:
    """Mutable market tick event buffer for zero-allocation simulation cursors.

    Matches com.strategyquant.datalib.TickEvent specification. Reused across
    billions of simulator ticks in Stage 4B backtesting without object allocation.
    """

    time: int = 0
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    symbol: str = ""
    symbol_hash: int = 0
    connection_hash: int = 0
    is_bar_open: bool = False
    is_bar_close: bool = False
    session_start_time: int = 0
    session_end_time: int = 0
    is_set: bool = False

    def set(
        self,
        time: int,
        bid: float,
        ask: float,
        *,
        volume: float = 1.0,
        symbol_hash: int = 0,
        connection_hash: int = 0,
        session_start_time: int = 0,
        session_end_time: int = 0,
        is_bar_open: bool = False,
        is_bar_close: bool = False,
    ) -> None:
        """Mutate all fields in-place on this event buffer."""
        self.time = time
        self.symbol_hash = symbol_hash
        self.connection_hash = connection_hash
        self.bid = bid
        self.ask = ask
        self.volume = volume
        self.session_start_time = session_start_time
        self.session_end_time = session_end_time
        self.is_bar_open = is_bar_open
        self.is_bar_close = is_bar_close
        self.is_set = True

    def copy_from(self, other: TickEvent) -> None:
        """Copy all field values from another TickEvent."""
        self.time = other.time
        self.bid = other.bid
        self.ask = other.ask
        self.volume = other.volume
        self.symbol = other.symbol
        self.symbol_hash = other.symbol_hash
        self.connection_hash = other.connection_hash
        self.is_bar_open = other.is_bar_open
        self.is_bar_close = other.is_bar_close
        self.session_start_time = other.session_start_time
        self.session_end_time = other.session_end_time
        self.is_set = other.is_set

    def reset(self) -> None:
        """Reset event buffer to uninitialized state."""
        self.time = 0
        self.bid = 0.0
        self.ask = 0.0
        self.volume = 0.0
        self.symbol = ""
        self.symbol_hash = 0
        self.connection_hash = 0
        self.is_bar_open = False
        self.is_bar_close = False
        self.session_start_time = 0
        self.session_end_time = 0
        self.is_set = False

    def to_market_tick(self) -> MarketTick:
        """Convert current state to an immutable MarketTick instance."""
        return MarketTick(
            time_msc=self.time,
            bid=self.bid,
            ask=self.ask,
            last=self.bid,
            volume=int(self.volume),
            volume_real=self.volume,
        )


class SpreadsMap:
    """Lookup container mapping instrument/connection keys to spread points.

    Matches com.strategyquant.datalib.ticksimulator.SpreadsMap specification.
    """

    def __init__(self, initial_spreads: dict[int | str, float] | None = None) -> None:
        """Initialize map with optional key-to-spread dictionary."""
        self._spreads: dict[int | str, float] = {}
        if initial_spreads:
            for k, v in initial_spreads.items():
                self._spreads[k] = max(0.0, float(v))

    def contains_key(self, key: int | str) -> bool:
        """Return True if the key has a configured spread."""
        return key in self._spreads

    def get_spread(self, key: int | str, default: float = 0.0) -> float:
        """Retrieve spread points for key, or fallback to default."""
        return self._spreads.get(key, default)

    def set_spread(self, key: int | str, spread: float) -> None:
        """Configure spread points for key."""
        self._spreads[key] = max(0.0, float(spread))


class ITickSimulator(Protocol):
    """Protocol defining the streaming tick simulator cursor contract.

    Matches com.strategyquant.datalib.ticksimulator.ITickSimulator.
    """

    def init(self, bars: Sequence[Any]) -> None:
        """Initialize simulator with historical bars."""
        ...

    def get_next_tick(self, target: TickEvent) -> bool:
        """Mutate target with next intra-bar tick, returning True until exhausted."""
        ...

    def set_symbols_spread(self, spreads: SpreadsMap | dict[int | str, float]) -> None:
        """Configure spread lookup table."""
        ...


class DefaultTickSimulator:
    """Clean-room intra-bar 4-tick simulator cursor for backtesting.

    Emulates com.strategyquant.datalib.ticksimulator.DefaultTickSimulator.
    Generates 4 ticks per bar in O(1) memory:
      - Bullish bar (close >= open): Open -> Low -> High -> Close
      - Bearish bar (close < open): Open -> High -> Low -> Close
    """

    def __init__(
        self,
        point_value: float = 0.00001,
        symbol: str = "",
        symbol_hash: int = 0,
        bar_duration_seconds: int = 60,
    ) -> None:
        """Initialize simulator cursor parameters."""
        self._point_value = max(1e-10, float(point_value))
        self._symbol = symbol
        self._symbol_hash = symbol_hash
        self._bar_duration_ms = max(1000, int(bar_duration_seconds * 1000))
        self._spreads_map = SpreadsMap()
        self._bars: list[Any] = []
        self._bar_index = 0
        self._tick_in_bar = 0

    def init(self, bars: Sequence[Any]) -> None:
        """Initialize simulator with a chronological sequence of bars."""
        self._bars = list(bars)
        self._bar_index = 0
        self._tick_in_bar = 0
        logger.debug(
            "FR-DATA-STREAMING-TICK-SIMULATOR: initialized cursor with %d bars",
            len(self._bars),
        )

    def set_symbols_spread(self, spreads: SpreadsMap | dict[int | str, float]) -> None:
        """Configure symbol spread lookup table."""
        if isinstance(spreads, SpreadsMap):
            self._spreads_map = spreads
        else:
            self._spreads_map = SpreadsMap(spreads)

    def get_next_tick(self, target: TickEvent) -> bool:
        """Advance cursor by one intra-bar tick, mutating target in place.

        Returns True while ticks are available, or False when all bars are exhausted.
        """
        while self._bar_index < len(self._bars):
            bar = self._bars[self._bar_index]
            open_val, high_val, low_val, close_val, vol_val, bar_time = (
                self._extract_bar_ohlcv(bar)
            )

            offsets = self._four_tick_offsets_ms(self._bar_duration_ms)
            bullish = close_val >= open_val

            if bullish:
                prices = (open_val, low_val, high_val, close_val)
            else:
                prices = (open_val, high_val, low_val, close_val)

            tick_idx = self._tick_in_bar
            price = prices[tick_idx]
            tick_time = bar_time + offsets[tick_idx]

            spread_pts = self._spreads_map.get_spread(
                self._symbol_hash or self._symbol,
                default=getattr(bar, "spread", 0.0) or 0.0,
            )
            spread_cash = spread_pts * self._point_value
            bid = price
            ask = price + spread_cash

            is_open = tick_idx == 0
            is_close = tick_idx == _CLOSE_TICK_INDEX

            target.set(
                time=tick_time,
                bid=bid,
                ask=ask,
                volume=max(1.0, vol_val / _TICKS_PER_BAR),
                symbol_hash=self._symbol_hash,
                is_bar_open=is_open,
                is_bar_close=is_close,
            )

            self._tick_in_bar += 1
            if self._tick_in_bar >= _TICKS_PER_BAR:
                self._bar_index += 1
                self._tick_in_bar = 0

            return True

        return False

    def stream_ticks(
        self,
        bars: Sequence[Any] | None = None,
    ) -> Iterator[MarketTick]:
        """Convenience generator yielding immutable MarketTick instances."""
        if bars is not None:
            self.init(bars)
        event = TickEvent()
        while self.get_next_tick(event):
            yield event.to_market_tick()

    @staticmethod
    def _extract_bar_ohlcv(
        bar: Any,
    ) -> tuple[float, float, float, float, float, int]:
        """Extract OHLCV and millisecond timestamp from bar object or dict."""
        if isinstance(bar, dict):
            o_raw = bar.get("open")
            o = float(o_raw if o_raw is not None else bar.get("Open", 0.0))
            h_raw = bar.get("high")
            h = float(h_raw if h_raw is not None else bar.get("High", 0.0))
            low_raw = bar.get("low")
            low_price = float(low_raw if low_raw is not None else bar.get("Low", 0.0))
            c_raw = bar.get("close")
            c = float(c_raw if c_raw is not None else bar.get("Close", 0.0))
            v_raw = bar.get("volume")
            v = float(v_raw if v_raw is not None else bar.get("Volume", 1.0))
            t_val = bar.get("time") or bar.get("Time", 0)
        else:
            o = float(getattr(bar, "open", 0.0))
            h = float(getattr(bar, "high", 0.0))
            low_price = float(getattr(bar, "low", 0.0))
            c = float(getattr(bar, "close", 0.0))
            v = float(getattr(bar, "volume", 1.0))
            t_val = getattr(bar, "time", 0)

        if isinstance(t_val, datetime):
            bar_ms = int(t_val.timestamp() * 1000)
        elif isinstance(t_val, (int, float)):
            bar_ms = int(t_val * 1000) if t_val < _S_TO_MS_THRESHOLD else int(t_val)
        else:
            bar_ms = 0

        return o, h, low_price, c, v, bar_ms

    @staticmethod
    def _four_tick_offsets_ms(bar_ms: int) -> tuple[int, int, int, int]:
        """Return 4 within-bar millisecond offsets."""
        close_offset = max(0, bar_ms - 1)
        first_inner = max(1, bar_ms // 3)
        second_inner = max(first_inner + 1, (2 * bar_ms) // 3)
        second_inner = min(second_inner, max(first_inner + 1, close_offset - 1))
        return (0, first_inner, second_inner, close_offset)


class TSTickSimulator(DefaultTickSimulator):
    """TradeStation-compatible intra-bar tick simulator cursor.

    Emulates com.strategyquant.datalib.ticksimulator.TSTickSimulator.
    Determines turn direction by evaluating proximity of Open to Low vs High:
      - If abs(open - low) < abs(open - high): price moves to Low first.
      - Flat or single-price bars emit reduced ticks.
    """

    @override
    def get_next_tick(self, target: TickEvent) -> bool:
        """Advance cursor using TradeStation intra-bar tick logic."""
        while self._bar_index < len(self._bars):
            bar = self._bars[self._bar_index]
            open_val, high_val, low_val, close_val, vol_val, bar_time = (
                self._extract_bar_ohlcv(bar)
            )

            # Determine TradeStation tick sequence
            prices: tuple[float, ...]
            if open_val == high_val == low_val == close_val:
                prices = (open_val,)
            elif open_val == high_val:
                prices = (open_val, low_val, close_val)
            elif open_val == low_val:
                prices = (open_val, high_val, close_val)
            else:
                dist_to_low = abs(open_val - low_val)
                dist_to_high = abs(open_val - high_val)
                if dist_to_low < dist_to_high:
                    prices = (open_val, low_val, high_val, close_val)
                else:
                    prices = (open_val, high_val, low_val, close_val)

            total_ticks = len(prices)
            offsets = np.linspace(0, self._bar_duration_ms - 1, total_ticks, dtype=int)

            tick_idx = self._tick_in_bar
            price = prices[tick_idx]
            tick_time = bar_time + int(offsets[tick_idx])

            spread_pts = self._spreads_map.get_spread(
                self._symbol_hash or self._symbol,
                default=getattr(bar, "spread", 0.0) or 0.0,
            )
            spread_cash = spread_pts * self._point_value
            bid = price
            ask = price + spread_cash

            is_open = tick_idx == 0
            is_close = tick_idx == total_ticks - 1

            target.set(
                time=tick_time,
                bid=bid,
                ask=ask,
                volume=max(1.0, vol_val / total_ticks),
                symbol_hash=self._symbol_hash,
                is_bar_open=is_open,
                is_bar_close=is_close,
            )

            self._tick_in_bar += 1
            if self._tick_in_bar >= total_ticks:
                self._bar_index += 1
                self._tick_in_bar = 0

            return True

        return False


# ============================================================================
# Component 2: Vectorized Batch Tick Generator & Parquet Streamer
# ============================================================================

TICK_MODEL_REAL = "real"
TICK_MODEL_GENERATED = "generated"
TICK_MODEL_TRADING_BAR = "trading_bar"
TICK_MODEL_OHLC_M1 = "ohlc_m1"

SUPPORTED_TICK_MODELS: frozenset[str] = frozenset(
    {
        TICK_MODEL_REAL,
        TICK_MODEL_GENERATED,
        TICK_MODEL_TRADING_BAR,
        TICK_MODEL_OHLC_M1,
    }
)

SPREAD_NATIVE = "native_spread"
SPREAD_FIXED = "fixed_spread"
SPREAD_VARIABLE = "variable_spread"

SUPPORTED_SPREAD_MODELS: frozenset[str] = frozenset(
    {
        SPREAD_NATIVE,
        SPREAD_FIXED,
        SPREAD_VARIABLE,
    }
)

PHASE_OPEN_CODE = np.uint8(1)
PHASE_HIGH_CODE = np.uint8(2)
PHASE_LOW_CODE = np.uint8(4)
PHASE_CLOSE_CODE = np.uint8(8)

_DATETIME_CANDIDATES: tuple[str, ...] = (
    "Datetime",
    "datetime",
    "time",
    "Time",
    "timestamp",
    "Timestamp",
)

_DEFAULT_BAR_SECONDS = 60


def _ensure_datetime_index(data: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame is indexed by a DatetimeIndex named Datetime."""
    if isinstance(data.index, pd.DatetimeIndex):
        if data.index.name != "Datetime":
            out = data.copy()
            out.index.name = "Datetime"
            return out
        return data

    for col in _DATETIME_CANDIDATES:
        if col in data.columns:
            out = data.copy()
            out.index = pd.DatetimeIndex(out[col], name="Datetime")
            return out.drop(columns=[col])

    raise ValueError(
        "DataFrame must have a DatetimeIndex or datetime column "
        "(Datetime, datetime, time, timestamp)."
    )


class TicksGenerator:
    """Vectorized generator producing standardized tick frames from bars or ticks.

    Completely decoupled from strategy signals, producing pure market data frames:
    ["bid", "ask", "last", "spread", "source_bar_time", "tick_index_in_bar",
     "is_bar_close"].
    """

    def __init__(
        self,
        model: str,
        trading_timeframe: str,
        *,
        m1_bars: pd.DataFrame | None = None,
        real_ticks: pd.DataFrame | None = None,
        point_value: float = 0.00001,
        spread_model: str = SPREAD_NATIVE,
        fixed_spread_points: float | None = None,
        min_spread_points: float | None = None,
        max_spread_points: float | None = None,
        random_seed: int | None = None,
    ) -> None:
        """Initialize generator and validate configuration."""
        self.model = str(model).lower()
        self.trading_timeframe = str(trading_timeframe).upper()
        self.m1_bars = m1_bars
        self.real_ticks = real_ticks
        self.point_value = float(point_value)
        self.spread_model = str(spread_model).lower()
        self.fixed_spread_points = fixed_spread_points
        self.min_spread_points = min_spread_points
        self.max_spread_points = max_spread_points
        self._random_seed = random_seed
        self._validate_config()
        logger.debug(
            "FR-DATA-BATCH-TICK-GENERATOR: initialized TicksGenerator model=%s",
            self.model,
        )

    def _validate_config(self) -> None:
        """Validate model, point value, and spread configuration."""
        if self.model not in SUPPORTED_TICK_MODELS:
            raise ValueError(
                f"Unsupported ticks model: {self.model}. "
                f"Supported models: {sorted(SUPPORTED_TICK_MODELS)}"
            )
        if self.point_value <= 0.0:
            raise ValueError("point_value must be > 0.")
        if self.spread_model not in SUPPORTED_SPREAD_MODELS:
            raise ValueError(
                f"Unsupported spread_model: {self.spread_model}. "
                f"Supported: {sorted(SUPPORTED_SPREAD_MODELS)}"
            )
        self._validate_spread_config()

    def _validate_spread_config(self) -> None:
        """Validate spread parameters for fixed and variable spread models."""
        if self.spread_model == SPREAD_FIXED:
            if self.fixed_spread_points is None:
                raise ValueError(
                    "fixed_spread_points is required for the fixed_spread model."
                )
            if float(self.fixed_spread_points) < 0.0:
                raise ValueError("fixed_spread_points must be >= 0.")
        elif self.spread_model == SPREAD_VARIABLE:
            if self.min_spread_points is None or self.max_spread_points is None:
                raise ValueError(
                    "min_spread_points and max_spread_points are required for "
                    "variable_spread model."
                )
            if (
                float(self.min_spread_points) < 0.0
                or float(self.max_spread_points) < 0.0
            ):
                raise ValueError(
                    "min_spread_points and max_spread_points must be >= 0."
                )
            if float(self.min_spread_points) > float(self.max_spread_points):
                raise ValueError("min_spread_points cannot exceed max_spread_points.")

    def generate(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Generate a standardized tick frame for the configured model."""
        logger.debug(
            "FR-DATA-BATCH-TICK-GENERATOR: generating ticks using model='%s' "
            "for timeframe='%s'.",
            self.model,
            self.trading_timeframe,
        )
        if self.model == TICK_MODEL_TRADING_BAR:
            return self._four_tick_frame(bars)
        if self.model == TICK_MODEL_OHLC_M1:
            return self._ohlc_m1_frame(bars)
        if self.model == TICK_MODEL_GENERATED:
            return self._generated_frame(bars)
        return self._real_frame(bars)

    @staticmethod
    def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
        """Return the actual column name matching any candidate case-insensitively."""
        lower = {str(col).lower(): str(col) for col in df.columns}
        for name in candidates:
            if name.lower() in lower:
                return lower[name.lower()]
        return None

    _find_col = find_col

    @classmethod
    def _require_col(cls, df: pd.DataFrame, candidates: list[str], context: str) -> str:
        """Return a required column name or raise ValueError."""
        col = cls.find_col(df, candidates)
        if col is None:
            raise ValueError(f"{context} requires one of columns: {candidates}")
        return col

    @staticmethod
    def _infer_bar_seconds(index: pd.DatetimeIndex) -> int:
        """Infer bar duration in seconds from median index spacing."""
        if len(index) > 1:
            deltas = index.to_series().diff().dropna()
            if not deltas.empty:
                return int(max(1, deltas.median().total_seconds()))
        return _DEFAULT_BAR_SECONDS

    def _configured_bar_seconds(self) -> int:
        """Return the configured trading-timeframe duration in seconds."""
        try:
            tf = Timeframe.from_string(self.trading_timeframe)
            return int(TIMEFRAME_SECONDS.get(tf, _DEFAULT_BAR_SECONDS))
        except ValueError:
            return _DEFAULT_BAR_SECONDS

    @staticmethod
    def _four_tick_offsets_ms(bar_seconds: int) -> npt.NDArray[np.int64]:
        """Return 4 within-bar millisecond offsets."""
        bar_ms = max(1, int(bar_seconds) * 1000)
        close_offset = max(0, bar_ms - 1)
        first_inner = max(1, bar_ms // 3)
        second_inner = max(first_inner + 1, (2 * bar_ms) // 3)
        second_inner = min(second_inner, max(first_inner + 1, close_offset - 1))
        return np.array([0, first_inner, second_inner, close_offset], dtype=np.int64)

    def _spread_points(
        self,
        native_per_tick: npt.NDArray[np.float64],
        total: int,
    ) -> npt.NDArray[np.float64]:
        """Return per-tick spread points for the configured model."""
        if self.spread_model == SPREAD_NATIVE:
            return np.asarray(np.maximum(native_per_tick, 0.0), dtype=np.float64)
        if self.spread_model == SPREAD_FIXED:
            fixed = max(0.0, float(self.fixed_spread_points or 0.0))
            return np.full(total, fixed, dtype=np.float64)
        low = float(self.min_spread_points or 0.0)
        high = float(self.max_spread_points or 0.0)
        rng = RandomGenerator(seed=self._random_seed)
        draws = np.array(
            [rng.next_double(low, high) for _ in range(total)], dtype=np.float64
        )
        return np.asarray(np.maximum(0.0, draws), dtype=np.float64)

    def _four_tick_frame(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Build a 4-tick-per-bar frame from OHLC bars."""
        if bars is None or bars.empty:
            return self._empty_frame()

        bars_indexed = _ensure_datetime_index(bars)
        if not bars_indexed.index.is_monotonic_increasing:
            bars_indexed = bars_indexed.sort_index()

        open_col = self._require_col(bars_indexed, ["Open"], "four-tick generation")
        high_col = self._require_col(bars_indexed, ["High"], "four-tick generation")
        low_col = self._require_col(bars_indexed, ["Low"], "four-tick generation")
        close_col = self._require_col(bars_indexed, ["Close"], "four-tick generation")
        spread_col = self.find_col(bars_indexed, ["Spread"])

        n_bars = len(bars_indexed.index)

        def col_or_zeros(name: str | None) -> npt.NDArray[np.float64]:
            if name is None:
                return np.zeros(n_bars, dtype=np.float64)
            values = pd.to_numeric(bars_indexed[name], errors="coerce").to_numpy(
                dtype=np.float64,
                copy=False,
            )
            return np.asarray(np.nan_to_num(values, nan=0.0), dtype=np.float64)

        open_arr = col_or_zeros(open_col)
        high_arr = col_or_zeros(high_col)
        low_arr = col_or_zeros(low_col)
        close_arr = col_or_zeros(close_col)
        native_spread_arr = col_or_zeros(spread_col)

        bar_seconds = (
            self._infer_bar_seconds(bars_indexed.index)
            if n_bars > 1
            else self._configured_bar_seconds()
        )
        offsets_ms = self._four_tick_offsets_ms(bar_seconds)

        bullish = close_arr >= open_arr
        total = n_bars * 4
        bid: npt.NDArray[np.float64] = np.empty(total, dtype=np.float64)
        bid[0::4] = open_arr
        bid[1::4] = np.where(bullish, low_arr, high_arr)
        bid[2::4] = np.where(bullish, high_arr, low_arr)
        bid[3::4] = close_arr

        phases: npt.NDArray[np.uint8] = np.empty(total, dtype=np.uint8)
        phases[0::4] = PHASE_OPEN_CODE
        phases[1::4] = np.where(bullish, PHASE_LOW_CODE, PHASE_HIGH_CODE)
        phases[2::4] = np.where(bullish, PHASE_HIGH_CODE, PHASE_LOW_CODE)
        phases[3::4] = PHASE_CLOSE_CODE

        spread_points = self._spread_points(np.repeat(native_spread_arr, 4), total)
        frame: dict[str, Any] = {
            "bid": bid,
            "ask": bid + (spread_points * self.point_value),
            "last": bid,
            "spread": np.rint(np.maximum(spread_points, 0.0)).astype(np.int64),
        }

        repeated_index = bars_indexed.index.repeat(4)
        tick_offsets = pd.to_timedelta(
            np.tile(offsets_ms.astype(np.int64), n_bars),
            unit="ms",
        )
        index = pd.DatetimeIndex(repeated_index + tick_offsets, name="Datetime")
        frame["tick_index_in_bar"] = np.tile(np.array([0, 1, 2, 3]), n_bars)
        frame["is_bar_close"] = phases

        result = pd.DataFrame(frame, index=index, copy=False)
        result["source_bar_time"] = repeated_index
        if not result.index.is_monotonic_increasing:
            return result.sort_index()
        return result

    def _ohlc_m1_frame(
        self,
        _trading_bars: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Build a four-tick frame from M1 bars."""
        if self.m1_bars is None or self.m1_bars.empty:
            raise ValueError("TICK_MODEL_OHLC_M1 requires non-empty m1_bars.")
        return self._four_tick_frame(self.m1_bars)

    def _generated_frame(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Interpolate each trading-timeframe bar into tick-volume ticks."""
        if bars is None or bars.empty:
            return self._empty_frame()

        frame = _ensure_datetime_index(bars)
        if not frame.index.is_monotonic_increasing:
            frame = frame.sort_index()
        open_col = self._require_col(frame, ["Open"], TICK_MODEL_GENERATED)
        high_col = self._require_col(frame, ["High"], TICK_MODEL_GENERATED)
        low_col = self._require_col(frame, ["Low"], TICK_MODEL_GENERATED)
        close_col = self._require_col(frame, ["Close"], TICK_MODEL_GENERATED)
        volume_col = self._require_col(
            frame,
            ["tick_volume", "Volume", "volume"],
            TICK_MODEL_GENERATED,
        )
        spread_col = self.find_col(frame, ["Spread"])

        def bar_floats(name: str) -> npt.NDArray[np.float64]:
            values = pd.to_numeric(frame[name], errors="coerce").to_numpy(
                dtype=np.float64,
                copy=False,
            )
            return np.asarray(np.nan_to_num(values, nan=0.0), dtype=np.float64)

        open_b = bar_floats(open_col)
        high_b = bar_floats(high_col)
        low_b = bar_floats(low_col)
        close_b = bar_floats(close_col)
        native_b = (
            bar_floats(spread_col)
            if spread_col is not None
            else np.zeros(len(open_b), dtype=np.float64)
        )
        vol_b = np.maximum(4, bar_floats(volume_col).astype(np.int64))
        total = int(vol_b.sum())
        if total == 0:
            return self._empty_frame()

        price, local_i, vol_rep = self._interpolate_generated(
            open_b,
            high_b,
            low_b,
            close_b,
            vol_b=vol_b,
            total=total,
        )
        spread_points = self._spread_points(np.repeat(native_b, vol_b), total)
        phases = self._generated_phase_codes(open_b, close_b, vol_b, local_i, vol_rep)

        n_bars = len(vol_b)
        bar_seconds = (
            self._infer_bar_seconds(frame.index)
            if n_bars > 1
            else self._configured_bar_seconds()
        )
        offset_ms = (max(1, bar_seconds * 1000) * local_i) // np.maximum(vol_rep, 1)
        repeated_index = frame.index.repeat(vol_b)
        index = pd.DatetimeIndex(
            repeated_index + pd.to_timedelta(offset_ms, unit="ms"),
            name="Datetime",
        )

        data: dict[str, Any] = {
            "bid": price,
            "ask": price + spread_points * self.point_value,
            "last": price,
            "spread": np.rint(np.maximum(spread_points, 0.0)).astype(np.int64),
            "tick_index_in_bar": local_i,
            "is_bar_close": phases,
        }

        result = pd.DataFrame(data, index=index, copy=False)
        result["source_bar_time"] = repeated_index
        if not result.index.is_monotonic_increasing:
            return result.sort_index()
        return result

    @staticmethod
    def _interpolate_generated(
        open_b: npt.NDArray[np.float64],
        high_b: npt.NDArray[np.float64],
        low_b: npt.NDArray[np.float64],
        close_b: npt.NDArray[np.float64],
        *,
        vol_b: npt.NDArray[np.int64],
        total: int,
    ) -> tuple[
        npt.NDArray[np.float64],
        npt.NDArray[np.int64],
        npt.NDArray[np.int64],
    ]:
        """Vectorize piecewise-linear OHLC interpolation across bars."""
        bar_start: npt.NDArray[np.int64] = np.repeat(
            np.cumsum(vol_b) - vol_b,
            vol_b,
        )
        local_i = np.arange(total) - bar_start
        vol_rep: npt.NDArray[np.int64] = np.repeat(vol_b, vol_b)

        steps = vol_b - 1
        base = steps // 3
        rem = steps % 3
        seg0 = base + (rem > 0)
        seg1 = base + (rem > 1)
        b1: npt.NDArray[np.int64] = np.repeat(seg0, vol_b)
        b2: npt.NDArray[np.int64] = np.repeat(seg0 + seg1, vol_b)
        seg0_rep: npt.NDArray[np.int64] = np.repeat(
            np.maximum(seg0, 1),
            vol_b,
        )
        seg1_rep: npt.NDArray[np.int64] = np.repeat(
            np.maximum(seg1, 1),
            vol_b,
        )
        seg2_rep: npt.NDArray[np.int64] = np.repeat(
            np.maximum(base, 1),
            vol_b,
        )

        bullish = close_b >= open_b
        w0: npt.NDArray[np.float64] = np.repeat(open_b, vol_b)
        w3: npt.NDArray[np.float64] = np.repeat(close_b, vol_b)
        w1: npt.NDArray[np.float64] = np.repeat(
            np.where(bullish, low_b, high_b),
            vol_b,
        )
        w2: npt.NDArray[np.float64] = np.repeat(
            np.where(bullish, high_b, low_b),
            vol_b,
        )

        in_seg0 = local_i <= b1
        in_seg1 = (local_i > b1) & (local_i <= b2)
        price: npt.NDArray[np.float64] = np.where(
            in_seg0,
            w0 + (w1 - w0) * (local_i / seg0_rep),
            np.where(
                in_seg1,
                w1 + (w2 - w1) * ((local_i - b1) / seg1_rep),
                w2 + (w3 - w2) * ((local_i - b2) / seg2_rep),
            ),
        )
        return price, local_i, vol_rep

    @staticmethod
    def _generated_phase_codes(
        open_b: npt.NDArray[np.float64],
        close_b: npt.NDArray[np.float64],
        vol_b: npt.NDArray[np.int64],
        local_i: npt.NDArray[np.int64],
        vol_rep: npt.NDArray[np.int64],
    ) -> npt.NDArray[np.uint8]:
        """Return generated tick phase bitmasks."""
        steps = vol_b - 1
        base = steps // 3
        rem = steps % 3
        seg0 = base + (rem > 0)
        seg1 = base + (rem > 1)
        first_turn: npt.NDArray[np.int64] = np.repeat(seg0, vol_b)
        second_turn: npt.NDArray[np.int64] = np.repeat(seg0 + seg1, vol_b)
        bullish: npt.NDArray[np.bool_] = np.repeat(close_b >= open_b, vol_b)
        high_i = np.where(bullish, second_turn, first_turn)
        low_i = np.where(bullish, first_turn, second_turn)

        bitmask = np.zeros(local_i.shape[0], dtype=np.uint8)
        bitmask[local_i == 0] |= PHASE_OPEN_CODE
        bitmask[local_i == high_i] |= PHASE_HIGH_CODE
        bitmask[local_i == low_i] |= PHASE_LOW_CODE
        bitmask[local_i == (vol_rep - 1)] |= PHASE_CLOSE_CODE
        return bitmask

    def _real_frame(
        self,
        _trading_bars: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Standardize real ticks."""
        if self.real_ticks is None or self.real_ticks.empty:
            raise ValueError("TICK_MODEL_REAL requires non-empty real_ticks.")

        ticks = _ensure_datetime_index(self.real_ticks.copy())
        bid_col = self._require_col(ticks, ["bid", "Bid"], TICK_MODEL_REAL)
        ask_col = self._require_col(ticks, ["ask", "Ask"], TICK_MODEL_REAL)
        last_col = self.find_col(ticks, ["last", "Last"])
        spread_col = self.find_col(ticks, ["spread", "Spread"])

        out = pd.DataFrame(index=ticks.index)
        out["bid"] = ticks[bid_col].astype(float)
        out["ask"] = ticks[ask_col].astype(float)
        out["last"] = (
            ticks[last_col].astype(float) if last_col is not None else out["bid"]
        )
        out["spread"] = (
            ticks[spread_col].astype(float)
            if spread_col is not None
            else (out["ask"] - out["bid"]) / self.point_value
        )
        out["source_bar_time"] = ticks.index
        out["tick_index_in_bar"] = np.arange(len(ticks))
        out["is_bar_close"] = np.full(len(ticks), PHASE_OPEN_CODE, dtype=np.uint8)
        out.index = pd.DatetimeIndex(out.index, name="Datetime")
        return out.sort_index()

    @staticmethod
    def _empty_frame() -> pd.DataFrame:
        """Return an empty tick frame with the standard column layout."""
        columns = [
            "bid",
            "ask",
            "last",
            "spread",
            "source_bar_time",
            "tick_index_in_bar",
            "is_bar_close",
        ]
        return pd.DataFrame(columns=columns)


def _to_dataframe(
    data: pd.DataFrame | list[dict[str, Any]] | None,
) -> pd.DataFrame | None:
    """Coerce list-of-records input into a DataFrame."""
    if data is None:
        return None
    if isinstance(data, pd.DataFrame):
        return data
    return pd.DataFrame(data)


def generate_ticks(
    *,
    model: str,
    trading_timeframe: str,
    bars: pd.DataFrame | list[dict[str, Any]] | None = None,
    m1_bars: pd.DataFrame | list[dict[str, Any]] | None = None,
    real_ticks: pd.DataFrame | list[dict[str, Any]] | None = None,
    point_value: float = 0.00001,
    spread_model: str = SPREAD_NATIVE,
    fixed_spread_points: float | None = None,
    min_spread_points: float | None = None,
    max_spread_points: float | None = None,
    random_seed: int | None = None,
) -> pd.DataFrame:
    """Generate standardized ticks as a columnar DataFrame with RangeIndex."""
    generator = TicksGenerator(
        model=model,
        trading_timeframe=trading_timeframe,
        m1_bars=_to_dataframe(m1_bars),
        real_ticks=_to_dataframe(real_ticks),
        point_value=point_value,
        spread_model=spread_model,
        fixed_spread_points=fixed_spread_points,
        min_spread_points=min_spread_points,
        max_spread_points=max_spread_points,
        random_seed=random_seed,
    )
    signal_bars = _to_dataframe(bars)
    if signal_bars is None:
        signal_bars = pd.DataFrame()
    raw = generator.generate(signal_bars)
    if raw.empty:
        return pd.DataFrame(columns=["timestamp", *raw.columns.tolist()])
    raw.insert(0, "timestamp", raw.index)
    raw.index = pd.RangeIndex(len(raw))
    return raw


def _output_aware_chunk_bounds(
    counts: npt.NDArray[np.int64],
    max_output_rows: int,
) -> list[tuple[int, int]]:
    """Return input row ranges targeting a maximum generated output size."""
    if len(counts) == 0:
        return []

    target = max(1, int(max_output_rows))
    bounds: list[tuple[int, int]] = []
    start = 0
    running = 0
    for idx, count in enumerate(counts):
        estimated = max(1, int(count))
        if idx > start and running + estimated > target:
            bounds.append((start, idx))
            start = idx
            running = 0
        running += estimated
    bounds.append((start, len(counts)))
    return bounds


def _chunk_bounds(n_rows: int, size: int) -> list[tuple[int, int]]:
    """Return row ranges covering n_rows in size chunks."""
    step = max(1, size)
    return [(idx, min(idx + step, n_rows)) for idx in range(0, n_rows, step)]


def generate_ticks_to_parquet(
    *,
    model: str,
    trading_timeframe: str,
    path: str | Path,
    bars: pd.DataFrame | list[dict[str, Any]] | None = None,
    m1_bars: pd.DataFrame | list[dict[str, Any]] | None = None,
    real_ticks: pd.DataFrame | list[dict[str, Any]] | None = None,
    point_value: float = 0.00001,
    spread_model: str = SPREAD_NATIVE,
    fixed_spread_points: float | None = None,
    min_spread_points: float | None = None,
    max_spread_points: float | None = None,
    random_seed: int | None = None,
    chunk_size: int = 100_000,
    max_output_rows_per_chunk: int = 2_000_000,
) -> dict[str, Any]:
    """Stream generated ticks to a Parquet file with bounded memory."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "FR-DATA-BATCH-TICK-GENERATOR: writing ticks to parquet model=%s path=%s",
        model,
        out_path,
    )

    bars_df = _to_dataframe(bars)
    m1_df = _to_dataframe(m1_bars)
    real_df = _to_dataframe(real_ticks)

    source = m1_df if model == TICK_MODEL_OHLC_M1 else bars_df
    if source is None or source.empty:
        empty_frame = generate_ticks(
            model=model,
            trading_timeframe=trading_timeframe,
            bars=bars_df,
            m1_bars=m1_df,
            real_ticks=real_df,
            point_value=point_value,
            spread_model=spread_model,
        )
        empty_frame.to_parquet(out_path, index=False)
        return {
            "path": str(out_path),
            "rows": 0,
            "columns": [str(c) for c in empty_frame.columns],
        }

    writer: pq.ParquetWriter | None = None
    rows = 0
    columns: list[str] = []

    # Calculate chunk boundaries
    if model == TICK_MODEL_GENERATED:
        vol_col = TicksGenerator.find_col(source, ["tick_volume", "Volume", "volume"])
        if vol_col is not None:
            counts = np.maximum(
                4,
                pd.to_numeric(source[vol_col], errors="coerce")
                .fillna(0)
                .to_numpy(dtype=np.int64),
            )
        else:
            counts = np.full(len(source), 4, dtype=np.int64)
        bounds = _output_aware_chunk_bounds(counts, max_output_rows_per_chunk)
    else:
        rows_per_chunk = max(1, int(max_output_rows_per_chunk) // 4)
        bounds = _chunk_bounds(len(source), min(chunk_size, rows_per_chunk))

    try:
        for start, stop in bounds:
            piece = source.iloc[start:stop]
            piece_bars = bars_df if model == TICK_MODEL_OHLC_M1 else piece
            piece_m1 = piece if model == TICK_MODEL_OHLC_M1 else m1_df

            chunk_frame = generate_ticks(
                model=model,
                trading_timeframe=trading_timeframe,
                bars=piece_bars,
                m1_bars=piece_m1,
                real_ticks=real_df,
                point_value=point_value,
                spread_model=spread_model,
                fixed_spread_points=fixed_spread_points,
                min_spread_points=min_spread_points,
                max_spread_points=max_spread_points,
                random_seed=random_seed,
            )
            if chunk_frame.empty:
                continue

            table = pa.Table.from_pandas(chunk_frame, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema)
                columns = [str(c) for c in chunk_frame.columns]
            writer.write_table(table)
            rows += len(chunk_frame)
    finally:
        if writer is not None:
            writer.close()

    return {"path": str(out_path), "rows": rows, "columns": columns}


# ---------------------------------------------------------------------------
# Stage 2A: ChartDef & DataInfo Market Data Abstractions
# ---------------------------------------------------------------------------


@dataclass
class ChartDef:
    """Market data request specification and resample compatibility abstraction.

    Corresponds to `com.strategyquant.datalib.ChartDef`. Defines chart properties,
    symbol identifiers, sessions, spread settings, and resample predicates.
    """

    symbol: str
    timeframe: str | Timeframe = "M1"
    instrument: str = "Forex"
    session: str = "Default"
    connection_name: str = ""
    connection_hash: int = 0
    symbol_hash: int = 0
    history_from: int = 0
    history_to: int = 0
    loaded_history_from: int = 0
    spread: float = 0.0
    real_spread: bool = False
    bar_time_type: int = 0
    min_distance: float = 0.0
    is_backtest_data_def: bool = False
    backload_type: int = 0
    backload_number: int = 0
    registered: bool = False

    def __post_init__(self) -> None:
        """Normalize timeframe string and initialize deterministic hashes."""
        if isinstance(self.timeframe, Timeframe):
            self.timeframe = self.timeframe.value
        if not self.connection_hash and self.connection_name:
            self.connection_hash = abs(hash(self.connection_name))
        if not self.symbol_hash and self.symbol:
            self.symbol_hash = abs(hash(self.symbol))

    @property
    def timeframe_str(self) -> str:
        """String representation of timeframe."""
        return str(self.timeframe)

    @property
    def timeframe_seconds(self) -> int:
        """Timeframe duration in seconds."""
        if isinstance(self.timeframe, Timeframe):
            return self.timeframe.to_seconds()
        tf_str = str(self.timeframe).strip().upper()
        if tf_str in ("TICK", "TICKS"):
            return 0
        try:
            return Timeframe.from_string(tf_str).to_seconds()
        except ValueError:
            pass
        if tf_str.startswith("S") and tf_str[1:].isdigit():
            return int(tf_str[1:])
        return 0

    def is_registered(self) -> bool:
        """Check if chart definition is registered."""
        return self.registered

    def set_registered(self, registered: bool = True) -> None:
        """Set registration flag."""
        self.registered = registered

    def get_symbol(self) -> str:
        """Get chart symbol."""
        return self.symbol

    def set_symbol(self, symbol: str) -> None:
        """Set chart symbol and recompute symbol hash."""
        self.symbol = symbol
        self.symbol_hash = abs(hash(symbol))

    def get_instrument(self) -> str:
        """Get instrument class."""
        return self.instrument

    def get_instrument_info(self) -> str:
        """Get instrument class info."""
        return self.instrument

    def get_symbol_info(self) -> str:
        """Get symbol instrument info."""
        return self.instrument

    def get_timeframe(self) -> str:
        """Get timeframe string."""
        return str(self.timeframe)

    def get_session(self) -> str:
        """Get chart session identifier."""
        return self.session

    def set_session(self, session: str) -> None:
        """Set chart session identifier."""
        self.session = session

    def get_connection_name(self) -> str:
        """Get connection provider name."""
        return self.connection_name

    def get_connection_hash(self) -> int:
        """Get connection hash."""
        return self.connection_hash

    def get_symbol_hash(self) -> int:
        """Get symbol hash."""
        return self.symbol_hash

    def get_history_from(self) -> int:
        """Get history start timestamp."""
        return self.history_from

    def set_history_from(self, history_from: int) -> None:
        """Set history start timestamp."""
        self.history_from = history_from

    def get_history_to(self) -> int:
        """Get history end timestamp."""
        return self.history_to

    def set_history_to(self, history_to: int) -> None:
        """Set history end timestamp."""
        self.history_to = history_to

    def get_loaded_history_from(self) -> int:
        """Get loaded history start timestamp."""
        return self.loaded_history_from

    def set_loaded_history_from(self, loaded_history_from: int) -> None:
        """Set loaded history start timestamp."""
        self.loaded_history_from = loaded_history_from

    def get_spread(self) -> float:
        """Get fixed spread points/price units."""
        return self.spread

    def set_spread(self, spread: float) -> None:
        """Set fixed spread."""
        self.spread = spread

    def modify_spread(self, spread: float) -> None:
        """Modify fixed spread."""
        self.spread = spread

    def set_real_spread(self, real_spread: bool) -> None:
        """Set whether real variable spread is active."""
        self.real_spread = real_spread

    def get_min_distance(self) -> float:
        """Get minimum distance in points."""
        return self.min_distance

    def set_min_distance(self, min_distance: float) -> None:
        """Set minimum distance in points."""
        self.min_distance = min_distance

    def get_bar_time_type(self) -> int:
        """Get bar timestamp anchor type (0=Open, 1=Close)."""
        return self.bar_time_type

    def get_effective_bar_time_type(self) -> int:
        """Get effective bar timestamp anchor type."""
        return self.bar_time_type

    def get_backload_type(self) -> int:
        """Get backload type."""
        return self.backload_type

    def get_backload_number(self) -> int:
        """Get backload count / number."""
        return self.backload_number

    def get_is_backtest_data_def(self) -> bool:
        """Check if this chart definition is designated for backtesting."""
        return self.is_backtest_data_def

    def is_symbol_recognized(self) -> bool:
        """Check if symbol is valid/recognized."""
        return bool(self.symbol and len(self.symbol.strip()) > 0)

    def is_smaller_than(self, other: ChartDef) -> bool:
        """Evaluate if this chart's timeframe is strictly smaller than other's."""
        return self.timeframe_seconds < other.timeframe_seconds

    def can_be_computed_from(self, other: ChartDef) -> bool:
        """Evaluate if this chart can be resampled/computed from another chart.

        Conditions:
        - Symbols match (case-insensitive).
        - Sessions match (or either is 'Default').
        - other's timeframe is smaller than or equal to this timeframe.
        - other's timeframe evenly divides this timeframe (or other is tick data).
        - other's historical range covers this chart's range (if specified).
        """
        if self.symbol.strip().upper() != other.symbol.strip().upper():
            return False

        if (
            self.session
            and other.session
            and self.session != "Default"
            and other.session not in ("Default", self.session)
        ):
            return False

        other_sec = other.timeframe_seconds
        self_sec = self.timeframe_seconds

        if other_sec > self_sec:
            return False

        if other_sec > 0 and self_sec % other_sec != 0:
            return False

        has_from_mismatch = (
            self.history_from > 0
            and other.history_from > 0
            and other.history_from > self.history_from
        )
        has_to_mismatch = (
            self.history_to > 0
            and other.history_to > 0
            and other.history_to < self.history_to
        )
        return not (has_from_mismatch or has_to_mismatch)

    def is_same_connection_symbol(self, other: ChartDef) -> bool:
        """Check if both charts share identical connection name and symbol."""
        return (
            self.symbol.strip().upper() == other.symbol.strip().upper()
            and self.connection_name.strip().upper()
            == other.connection_name.strip().upper()
        )

    def get_charts_hash(self) -> str:
        """Compute unique identifier hash string for chart."""
        return f"{self.connection_name}_{self.symbol}_{self.timeframe}_{self.session}"

    def clone(
        self,
        symbol: str | None = None,
        history_from: int | None = None,
        history_to: int | None = None,
    ) -> ChartDef:
        """Clone this ChartDef, optionally overriding symbol or date ranges."""
        overrides: dict[str, Any] = {}
        if symbol is not None:
            overrides["symbol"] = symbol
            overrides["symbol_hash"] = abs(hash(symbol))
        if history_from is not None:
            overrides["history_from"] = history_from
        if history_to is not None:
            overrides["history_to"] = history_to
        return replace(self, **overrides)

    def get_clone(
        self,
        symbol: str | None = None,
        history_from: int | None = None,
        history_to: int | None = None,
    ) -> ChartDef:
        """SQX donor alias for clone()."""
        return self.clone(
            symbol=symbol, history_from=history_from, history_to=history_to
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize ChartDef to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChartDef:
        """Construct ChartDef from a dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class DataInfo:
    """Market data catalog metadata record.

    Corresponds to `com.strategyquant.datalib.DataInfo`. Encapsulates dataset
    identity, symbol, timeframe, boundaries, row counts, and storage file metadata.
    """

    id: int = 0
    symbol: str = ""
    timeframe: str = "M1"
    instrument: str = "Forex"
    connection: str = ""
    timezone: str = "UTC"
    decimals: int = 4
    date_from: int = 0
    date_from_str: str = ""
    date_to: int = 0
    date_to_str: str = ""
    rows: int = 0
    total_days: int = 0
    filename: str = ""
    file_hash: int = 0
    bar_time_type: int = 0
    remove_weekends: bool = True
    show: bool = True
    source: int = 0
    source_data_id: int = 0
    basket_id: int = 0
    broker_id: int = 0
    original_symbol: str = ""
    seconds_records: int = 0
    u_symbol: str = ""
    u_symbol_name: str = ""

    def clone(self) -> DataInfo:
        """Clone this DataInfo record."""
        return replace(self)

    def to_chart_def(self) -> ChartDef:
        """Convert catalog metadata record into an operational ChartDef."""
        return ChartDef(
            symbol=self.symbol,
            timeframe=self.timeframe,
            instrument=self.instrument,
            connection_name=self.connection,
            history_from=self.date_from,
            history_to=self.date_to,
            bar_time_type=self.bar_time_type,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize DataInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataInfo:
        """Construct DataInfo from a dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
