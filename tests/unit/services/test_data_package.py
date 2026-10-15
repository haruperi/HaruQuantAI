"""Unit tests for the app.services.data package structure, exports, and layering.

Description:
    Verifies that app.services.data satisfies the modular package architecture:
    - Layer 0: primitives.py
    - Layer 1: series.py, history.py, simulation.py, generation.py, catalog.py
    - Layer 2: __init__.py unified public export surface
    - Zero circular imports between submodules
    - Complete removal of app.services.libs.data (no backward compatibility)
"""

from __future__ import annotations

import importlib

import app.services.data as data_pkg
import app.services.data.catalog as data_catalog
import app.services.data.generation as data_gen
import app.services.data.history as data_hist
import app.services.data.primitives as data_prim
import app.services.data.series as data_ser
import app.services.data.simulation as data_sim
import pytest


class TestDataPackageExports:
    """Verify package-level public exports and submodule parity."""

    def test_primitives_exports_identity(self) -> None:
        """Verify primitives symbols match between package and submodule."""
        assert data_pkg.Timeframe is data_prim.Timeframe
        assert data_pkg.TIMEFRAME_SECONDS is data_prim.TIMEFRAME_SECONDS
        assert data_pkg.MarketBar is data_prim.MarketBar
        assert data_pkg.MarketTick is data_prim.MarketTick
        assert data_pkg.BridgeError is data_prim.BridgeError
        assert data_pkg.MAX_RECORDS == data_prim.MAX_RECORDS
        assert data_pkg.MAX_POSITION == data_prim.MAX_POSITION
        assert data_pkg.READ_TIMEOUT == data_prim.READ_TIMEOUT

    def test_series_exports_identity(self) -> None:
        """Verify series symbols match between package and submodule."""
        assert data_pkg.DataSeries is data_ser.DataSeries
        assert data_pkg.DataSeriesTypes is data_ser.DataSeriesTypes
        assert data_pkg.MedianDataSeries is data_ser.MedianDataSeries
        assert data_pkg.TypicalDataSeries is data_ser.TypicalDataSeries
        assert data_pkg.WeightedDataSeries is data_ser.WeightedDataSeries

    def test_history_exports_identity(self) -> None:
        """Verify history symbols match between package and submodule."""
        assert data_pkg.DataBackend is data_hist.DataBackend
        assert data_pkg.DataBrokerBackend is data_hist.DataBrokerBackend
        assert data_pkg.validate_request is data_hist.validate_request
        assert data_pkg.validate_rows is data_hist.validate_rows
        assert data_pkg.get_historical_bars is data_hist.get_historical_bars
        assert data_pkg.get_ticks is data_hist.get_ticks
        assert data_pkg.BAR_COLUMNS is data_hist.BAR_COLUMNS
        assert data_pkg.TICK_COLUMNS is data_hist.TICK_COLUMNS
        assert data_pkg.bars_to_dataframe is data_hist.bars_to_dataframe
        assert data_pkg.ticks_to_dataframe is data_hist.ticks_to_dataframe
        assert data_pkg.bars_to_df is data_hist.bars_to_df
        assert data_pkg.ticks_to_df is data_hist.ticks_to_df

    def test_simulation_exports_identity(self) -> None:
        """Verify simulation symbols match between package and submodule."""
        assert data_pkg.TickEvent is data_sim.TickEvent
        assert data_pkg.SpreadsMap is data_sim.SpreadsMap
        assert data_pkg.ITickSimulator is data_sim.ITickSimulator
        assert data_pkg.DefaultTickSimulator is data_sim.DefaultTickSimulator
        assert data_pkg.TSTickSimulator is data_sim.TSTickSimulator

    def test_generation_exports_identity(self) -> None:
        """Verify generation symbols match between package and submodule."""
        assert data_pkg.TICK_MODEL_REAL == data_gen.TICK_MODEL_REAL
        assert data_pkg.TICK_MODEL_GENERATED == data_gen.TICK_MODEL_GENERATED
        assert data_pkg.TICK_MODEL_TRADING_BAR == data_gen.TICK_MODEL_TRADING_BAR
        assert data_pkg.TICK_MODEL_OHLC_M1 == data_gen.TICK_MODEL_OHLC_M1
        assert data_pkg.SPREAD_FIXED == data_gen.SPREAD_FIXED
        assert data_pkg.SPREAD_NATIVE == data_gen.SPREAD_NATIVE
        assert data_pkg.SPREAD_VARIABLE == data_gen.SPREAD_VARIABLE
        assert data_pkg.SUPPORTED_TICK_MODELS is data_gen.SUPPORTED_TICK_MODELS
        assert data_pkg.SUPPORTED_SPREAD_MODELS is data_gen.SUPPORTED_SPREAD_MODELS
        assert data_pkg.PHASE_OPEN_CODE == data_gen.PHASE_OPEN_CODE
        assert data_pkg.PHASE_HIGH_CODE == data_gen.PHASE_HIGH_CODE
        assert data_pkg.PHASE_LOW_CODE == data_gen.PHASE_LOW_CODE
        assert data_pkg.PHASE_CLOSE_CODE == data_gen.PHASE_CLOSE_CODE
        assert data_pkg.TicksGenerator is data_gen.TicksGenerator
        assert data_pkg.generate_ticks is data_gen.generate_ticks
        assert data_pkg.generate_ticks_to_parquet is data_gen.generate_ticks_to_parquet

    def test_catalog_exports_identity(self) -> None:
        """Verify catalog symbols match between package and submodule."""
        assert data_pkg.ChartDef is data_catalog.ChartDef
        assert data_pkg.DataInfo is data_catalog.DataInfo

    def test_all_exports_present_in_package(self) -> None:
        """Ensure every name in __all__ can be resolved from the package."""
        for name in data_pkg.__all__:
            assert hasattr(data_pkg, name), f"Missing export: {name}"


class TestLayeringAndAntiCircularRules:
    """Verify architectural layering rules and absence of circular imports."""

    def test_dataseries_subclassing_and_factories(self) -> None:
        """Rule 2: Ensure DataSeries and derived classes coordinate without cycles."""
        high = [10.0, 11.0, 12.0]
        low = [8.0, 9.0, 10.0]
        close = [9.5, 10.5, 11.5]

        median = data_ser.DataSeries.create_median(high, low)
        assert isinstance(median, data_ser.MedianDataSeries)
        assert isinstance(median, data_ser.DataSeries)

        typical = data_ser.DataSeries.create_typical(high, low, close)
        assert isinstance(typical, data_ser.TypicalDataSeries)
        assert isinstance(typical, data_ser.DataSeries)

        weighted = data_ser.DataSeries.create_weighted(high, low, close)
        assert isinstance(weighted, data_ser.WeightedDataSeries)
        assert isinstance(weighted, data_ser.DataSeries)

    def test_submodules_do_not_import_package_init(self) -> None:
        """Rule 1: Submodules must not import upward from app.services.data."""
        import inspect

        submodules = [
            data_prim,
            data_ser,
            data_hist,
            data_sim,
            data_gen,
            data_catalog,
        ]
        for submod in submodules:
            source = inspect.getsource(submod)
            assert "from app.services.data import" not in source, (
                f"{submod.__name__} violates Rule 1 by importing from package top"
            )
            assert "import app.services.data\n" not in source, (
                f"{submod.__name__} violates Rule 1 by importing app.services.data"
            )

    def test_no_backward_compatibility_shim(self) -> None:
        """Verify that app.services.libs.data is completely deleted."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.libs.data")
