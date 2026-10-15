"""Unit tests for DataSeries and derived price series in app.workspace.data_manager.series.

Description:
    Validates high-performance columnar time-series storage (DataSeries) with
    dual-mode indexing (shift-based offset indexing and chronological access),
    warmup constraints (indy_starting_bar), condition predicates (is_rising,
    crosses_above, etc.), columnar zero-copy exports to NumPy, Polars, and PyArrow,
    DataSeriesTypes enumeration, and dynamic derived price series (MedianDataSeries,
    TypicalDataSeries, WeightedDataSeries).

Purpose:
    FEAT-DATAMGR-SERIES: Test suite for Data Manager series kernel.

Python API Usage:
    ```bash
    uv run pytest tests/unit/workspace/data_manager/test_series.py --no-cov
    ```
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl
import pyarrow as pa
import pytest
from app.workspace.data_manager import (
    DataSeries,
    DataSeriesTypes,
    MarketBar,
    MedianDataSeries,
    TypicalDataSeries,
    WeightedDataSeries,
)
from app.workspace.data_manager import series as series_mod
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


class TestDataSeriesReExports:
    """Verify package and module re-export parity for series components."""

    def test_reexport_identities(self) -> None:
        """Verify symbols exported from app.workspace.data_manager match submodule."""
        assert DataSeries is DirectDataSeries
        assert DataSeriesTypes is DirectDataSeriesTypes
        assert MedianDataSeries is DirectMedianDataSeries
        assert TypicalDataSeries is DirectTypicalDataSeries
        assert WeightedDataSeries is DirectWeightedDataSeries


class TestDataSeriesCore:
    """Test suite for DataSeries initialization, indexing, and array mutations."""

    def test_empty_initialization(self) -> None:
        """Verify empty DataSeries construction and default attributes."""
        ds = DataSeries()
        assert len(ds) == 0
        assert ds.size() == 0
        assert ds.name == ""
        assert ds.chart_type == "Line"
        assert ds.indy_starting_bar == 0
        assert ds.shift == 0
        assert math.isnan(ds.get(0))
        assert math.isnan(ds.get_double(0))

    def test_sequence_and_numpy_initialization(self) -> None:
        """Verify construction from sequence and numpy array."""
        ds1 = DataSeries([1.5, 2.5, 3.5], name="Close")
        assert len(ds1) == 3
        assert ds1.get(0) == 3.5
        assert ds1.get(1) == 2.5
        assert ds1.get(2) == 1.5
        assert ds1.get_double(0) == 1.5

        arr = np.array([10.0, 20.0, 30.0], dtype=np.float64)
        ds2 = DataSeries(arr, chart_type="Histogram", color="#ff0000")
        assert len(ds2) == 3
        assert ds2.chart_type == "Histogram"
        assert ds2.color == "#ff0000"
        assert ds2.get(0) == 30.0

    def test_shift_and_chronological_indexing(self) -> None:
        """Verify shift-based historical access vs chronological index access."""
        ds = DataSeries([10.0, 20.0, 30.0, 40.0, 50.0])
        # shift 0 is newest (index 4)
        assert ds.get(0) == 50.0
        assert ds.get(1) == 40.0
        assert ds.get(4) == 10.0
        assert math.isnan(ds.get(5))
        assert math.isnan(ds.get(-1))

        # chronological index 0 is oldest
        assert ds.get_double(0) == 10.0
        assert ds.get_double(4) == 50.0
        assert math.isnan(ds.get_double(5))
        assert math.isnan(ds.get_double(-1))

    def test_global_shift_offset(self) -> None:
        """Verify global shift offset applies to shift-based lookups."""
        ds = DataSeries([10.0, 20.0, 30.0, 40.0], shift=1)
        assert ds.get(0) == 30.0  # effective shift = 0 + 1 = 1 (second to last)
        assert ds.get(1) == 20.0  # effective shift = 1 + 1 = 2
        assert ds.get(2) == 10.0  # effective shift = 2 + 1 = 3
        assert math.isnan(ds.get(3))  # out of bounds

    def test_warmup_guard_indy_starting_bar(self) -> None:
        """Verify indy_starting_bar warmup gating."""
        ds = DataSeries([1.0, 2.0, 3.0, 4.0, 5.0], indy_starting_bar=2)
        # Chronological index < 2 returns NaN
        # index 0 (shift 4) -> nan
        assert math.isnan(ds.get(4))
        # index 1 (shift 3) -> nan
        assert math.isnan(ds.get(3))
        # index 2 (shift 2) -> 3.0
        assert ds.get(2) == 3.0
        assert ds.get(0) == 5.0

    def test_mutations_set_add_and_set_double(self) -> None:
        """Verify value mutation via add, set, and set_double."""
        ds = DataSeries([10.0, 20.0])
        ds.add(30.0)
        assert len(ds) == 3
        assert ds.get(0) == 30.0

        ds.add_values(2, 99.0)
        assert len(ds) == 5
        assert ds.get(0) == 99.0
        assert ds.get(1) == 99.0

        # set current (shift=0)
        ds.set(42.0)
        assert ds.get(0) == 42.0

        # set specific shift
        ds.set(1, 88.0)
        assert ds.get(1) == 88.0

        # set_double by chronological index
        ds.set_double(0, 77.0)
        assert ds.get_double(0) == 77.0

        # out of bounds set does nothing
        ds.set(100, 1.0)
        ds.set_double(100, 1.0)

    def test_get_rounded(self) -> None:
        """Verify rounding float results."""
        ds = DataSeries([1.234567, 2.345678])
        assert ds.get_rounded(0, 3) == 2.346
        assert ds.get_rounded(1, 2) == 1.23
        assert math.isnan(ds.get_rounded(10))

    def test_magic_methods_iteration_and_subscription(self) -> None:
        """Verify __iter__ and __getitem__ protocol."""
        ds = DataSeries([1.0, 2.0, 3.0])
        assert list(ds) == [1.0, 2.0, 3.0]
        assert ds[0] == 3.0  # shift index
        assert ds[1] == 2.0
        slice_res = ds[:2]  # slice access returns numpy array
        assert isinstance(slice_res, np.ndarray)
        np.testing.assert_array_equal(slice_res, np.array([1.0, 2.0]))


class TestDataSeriesPredicates:
    """Test suite for condition predicates (is_rising, crosses_above, etc.)."""

    def test_is_rising_and_falling(self) -> None:
        """Verify rising and falling trend checks."""
        ds = DataSeries([10.0, 20.0, 15.0, 25.0])
        # [10, 20, 15, 25] -> shift 0 is 25, shift 1 is 15
        assert ds.is_rising(0, 1) is True
        assert ds.is_falling(0, 1) is False
        assert ds.is_rising(1, 1) is False  # 15 vs 20
        assert ds.is_falling(1, 1) is True

    def test_crosses_above_and_below_constant(self) -> None:
        """Verify cross detection against constant threshold."""
        ds = DataSeries([10.0, 15.0, 25.0])
        # shift 1 is 15, shift 0 is 25 -> crossed above 20
        assert ds.crosses_above(20.0, 0) is True
        assert ds.crosses_below(20.0, 0) is False

        ds_down = DataSeries([25.0, 20.0, 15.0])
        assert ds_down.crosses_below(18.0, 0) is True
        assert ds_down.crosses_above(18.0, 0) is False

    def test_crosses_above_and_below_series(self) -> None:
        """Verify cross detection against another DataSeries."""
        fast = DataSeries([10.0, 15.0, 25.0])
        slow = DataSeries([12.0, 18.0, 20.0])
        # At shift 1: fast=15 <= slow=18; At shift 0: fast=25 > slow=20
        assert fast.crosses_above(slow, 0) is True
        assert fast.crosses_below(slow, 0) is False

    def test_is_higher_and_lower(self) -> None:
        """Verify level comparisons against constants and series."""
        ds1 = DataSeries([10.0, 20.0])
        ds2 = DataSeries([15.0, 15.0])
        assert ds1.is_higher(15.0, 0) is True
        assert ds1.is_lower(15.0, 0) is False
        assert ds1.is_higher(ds2, 0) is True
        assert ds1.is_lower(ds2, 0) is False


class TestDataSeriesColumnarInterop:
    """Test suite for NumPy, Polars, and PyArrow columnar exports/imports."""

    def test_numpy_roundtrip(self) -> None:
        """Verify zero-copy export to NumPy and reconstruction."""
        arr = np.array([1.0, 2.0, 3.5, 4.0], dtype=np.float64)
        ds = DataSeries.from_numpy(arr, name="TestNP")
        np.testing.assert_array_equal(ds.to_numpy(), arr)

    def test_polars_roundtrip(self) -> None:
        """Verify export to Polars and reconstruction."""
        s = pl.Series("pl_series", [10.0, 20.0, 30.0])
        ds = DataSeries.from_polars(s)
        assert ds.name == "pl_series"
        pl_export = ds.to_polars()
        assert isinstance(pl_export, pl.Series)
        assert pl_export.to_list() == [10.0, 20.0, 30.0]

    def test_arrow_roundtrip(self) -> None:
        """Verify export to PyArrow and reconstruction."""
        arr = pa.array([100.0, 200.0, 300.0], type=pa.float64())
        ds = DataSeries.from_arrow(arr, name="ArrowSeries")
        assert ds.name == "ArrowSeries"
        pa_export = ds.to_arrow()
        assert isinstance(pa_export, pa.Array)
        assert pa_export.to_pylist() == [100.0, 200.0, 300.0]


class TestDataSeriesTypes:
    """Test suite for DataSeriesTypes enumeration."""

    def test_standard_values(self) -> None:
        """Verify standard SQX DataSeriesTypes integer values."""
        assert DataSeriesTypes.OPEN == 0
        assert DataSeriesTypes.HIGH == 1
        assert DataSeriesTypes.LOW == 2
        assert DataSeriesTypes.CLOSE == 3
        assert DataSeriesTypes.VOLUME == 4
        assert DataSeriesTypes.MEDIAN == 5
        assert DataSeriesTypes.TYPICAL == 6
        assert DataSeriesTypes.WEIGHTED == 7

    def test_pascal_case_aliases(self) -> None:
        """Verify SQX PascalCase aliases."""
        assert DataSeriesTypes.Open == 0
        assert DataSeriesTypes.High == 1
        assert DataSeriesTypes.Low == 2
        assert DataSeriesTypes.Close == 3
        assert DataSeriesTypes.Volume == 4
        assert DataSeriesTypes.Median == 5
        assert DataSeriesTypes.Typical == 6
        assert DataSeriesTypes.Weighted == 7

    def test_from_name(self) -> None:
        """Verify case-insensitive name resolution."""
        assert DataSeriesTypes.from_name("open") == DataSeriesTypes.OPEN
        assert DataSeriesTypes.from_name("HIGH") == DataSeriesTypes.HIGH
        assert DataSeriesTypes.from_name("Median") == DataSeriesTypes.MEDIAN
        with pytest.raises(ValueError, match="Unknown DataSeriesTypes name"):
            DataSeriesTypes.from_name("NON_EXISTENT")


class TestDerivedPriceSeries:
    """Test suite for MedianDataSeries, TypicalDataSeries, and WeightedDataSeries."""

    def test_median_data_series(self) -> None:
        """Verify MedianDataSeries calculation ((High + Low) / 2.0)."""
        highs = [10.0, 20.0, 30.0]
        lows = [8.0, 16.0, 24.0]
        med = MedianDataSeries(highs, lows)
        assert len(med) == 3
        # Chronological: (10+8)/2=9, (20+16)/2=18, (30+24)/2=27
        assert med.get(0) == 27.0
        assert med.get(1) == 18.0
        assert med.get(2) == 9.0
        assert med.compute_value(0) == 9.0
        assert med.High.get(0) == 30.0
        assert med.Low.get(0) == 24.0

    def test_typical_data_series(self) -> None:
        """Verify TypicalDataSeries calculation ((High + Low + Close) / 3.0)."""
        highs = [10.0, 20.0]
        lows = [8.0, 16.0]
        closes = [9.0, 18.0]
        typ = TypicalDataSeries(highs, lows, closes)
        assert len(typ) == 2
        # (10+8+9)/3 = 9.0, (20+16+18)/3 = 18.0
        assert typ.get(0) == 18.0
        assert typ.get(1) == 9.0
        assert typ.compute_value(0) == 9.0

    def test_weighted_data_series(self) -> None:
        """Verify WeightedDataSeries calculation ((High + Low + 2*Close) / 4.0)."""
        highs = [10.0, 20.0]
        lows = [8.0, 16.0]
        closes = [9.0, 18.0]
        wt = WeightedDataSeries(highs, lows, closes)
        assert len(wt) == 2
        # (10+8+18)/4 = 9.0, (20+16+36)/4 = 18.0
        assert wt.get(0) == 18.0
        assert wt.get(1) == 9.0
        assert wt.compute_value(0) == 9.0

    def test_derived_from_bars_and_add_bar(self) -> None:
        """Verify construction from MarketBar sequence and dynamic add_bar."""
        bars = [
            MarketBar(
                time=1000, open=10.0, high=12.0, low=8.0, close=10.0, tick_volume=100
            ),
            MarketBar(
                time=2000, open=11.0, high=14.0, low=10.0, close=12.0, tick_volume=150
            ),
        ]
        med = MedianDataSeries.from_bars(bars)
        typ = TypicalDataSeries.from_bars(bars)
        wt = WeightedDataSeries.from_bars(bars)

        assert med.get(0) == 12.0  # (14+10)/2
        assert typ.get(0) == 12.0  # (14+10+12)/3
        assert wt.get(0) == 12.0  # (14+10+24)/4

        new_bar = MarketBar(
            time=3000, open=12.0, high=16.0, low=12.0, close=14.0, tick_volume=200
        )
        med.add_bar(new_bar)
        typ.add_bar(new_bar)
        wt.add_bar(new_bar)

        assert len(med) == 3
        assert med.get(0) == 14.0  # (16+12)/2
        assert typ.get(0) == 14.0  # (16+12+14)/3
        assert wt.get(0) == 14.0  # (16+12+28)/4

    def test_factory_methods(self) -> None:
        """Verify DataSeries static factory creation."""
        high = [10.0, 12.0]
        low = [8.0, 10.0]
        close = [9.0, 11.0]

        med = DataSeries.create_median(high, low)
        typ = DataSeries.create_typical(high, low, close)
        wt = DataSeries.create_weighted(high, low, close)

        assert isinstance(med, MedianDataSeries)
        assert isinstance(typ, TypicalDataSeries)
        assert isinstance(wt, WeightedDataSeries)

    def test_empty_derived_series(self) -> None:
        """Verify derived series construction with empty arrays."""
        med = MedianDataSeries([], [])
        typ = TypicalDataSeries([], [], [])
        wt = WeightedDataSeries([], [], [])
        assert len(med) == 0
        assert len(typ) == 0
        assert len(wt) == 0


def test_main_cli_execution() -> None:
    """Verify series module main demonstration runs cleanly."""
    series_mod.main()
