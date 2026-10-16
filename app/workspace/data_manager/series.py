"""Columnar numerical series container and derived price series calculations.

Description:
    Provides high-performance columnar time-series storage (DataSeries) with
    dual-mode indexing (shift-based historical indexing and chronological access),
    vectorized zero-copy exports to NumPy, Polars, and PyArrow, and dynamic derived
    price series (MedianDataSeries, TypicalDataSeries, WeightedDataSeries).

Purpose:
    FEAT-DATAMGR-SERIES: High-throughput market data series and derived series kernel.

Key Capabilities:
    - FR-DATAMGR-SERIES-COLUMNAR: High-performance columnar series kernel with
      dual-mode indexing.
      Associated: `DataSeries`, `DataSeries.get()`, `DataSeries.set()`.
      Logging: In-memory array operations with zero side effects.
    - FR-DATAMGR-SERIES-TYPES: Standard bar series data types enumeration
      matching SQX DataSeriesTypes.
      Associated: `DataSeriesTypes`, `DataSeriesTypes.from_name()`.
      Logging: Integer enumeration mapping with zero side effects.
    - FR-DATAMGR-SERIES-MEDIAN: Dynamic median price series computing
      (High + Low) / 2.0.
      Associated: `MedianDataSeries`, `MedianDataSeries.compute_value()`.
      Logging: Pure vectorized and on-the-fly series calculations with
        zero side effects.
    - FR-DATAMGR-SERIES-TYPICAL: Dynamic typical price series computing
      (High + Low + Close) / 3.0.
      Associated: `TypicalDataSeries`, `TypicalDataSeries.compute_value()`.
      Logging: Pure vectorized and on-the-fly series calculations with
        zero side effects.
    - FR-DATAMGR-SERIES-WEIGHTED: Dynamic weighted price series computing
      (High + Low + 2*Close) / 4.0.
      Associated: `WeightedDataSeries`, `WeightedDataSeries.compute_value()`.
      Logging: Pure vectorized and on-the-fly series calculations with
        zero side effects.

Python API Usage:
    ```python
    from app.workspace.data_manager.series import (
        DataSeries,
        DataSeriesTypes,
        MedianDataSeries,
        TypicalDataSeries,
        WeightedDataSeries,
    )

    series = DataSeries([10.0, 11.5, 12.0], name="Close")
    val = series.get(0)
    median = MedianDataSeries([10.0, 12.0], [8.0, 9.0])
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.series
    ```
"""

from __future__ import annotations

import array
import math
from collections.abc import Iterator, Sequence
from enum import IntEnum
from typing import Any, overload

import numpy as np
import polars as pl
import pyarrow as pa
from app.host.logging import get_logger

from ._common import MarketBar

__all__ = [
    "DataSeries",
    "DataSeriesTypes",
    "MedianDataSeries",
    "TypicalDataSeries",
    "WeightedDataSeries",
]

logger = get_logger(__name__)


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


def main() -> None:
    """Demonstrate DataSeries and derived series calculation."""
    series = DataSeries([100.0, 102.5, 101.0, 105.0], name="Close")
    print(f"DataSeries '{series.name}' size: {series.size()}, current: {series.get(0)}")
    median = DataSeries.create_median([102.0, 104.0, 106.0], [98.0, 100.0, 102.0])
    print(f"MedianDataSeries size: {median.size()}, latest: {median.get(0)}")


if __name__ == "__main__":
    main()
