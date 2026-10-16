"""Unit tests verifying removal of app.services.data and unification into data_manager.

Description:
    Verifies that the legacy app.services.data package and all its submodules have
    been completely removed with zero backward compatibility shims, and that all
    canonical market data capabilities (history, simulation, generation, series,
    contracts) are properly consolidated and exported from app.workspace.data_manager.

Purpose:
    FEAT-DATAMGR-UNIFICATION: Zero-shim removal verification of legacy data package.

Key Capabilities:
    - FR-DATA-PACKAGE-REMOVAL: Verify all legacy app.services.data modules raise
      ModuleNotFoundError on import.
    - FR-DATAMGR-EXPORT-PARITY: Verify unified public export surface in
      app.workspace.data_manager matches underlying submodules.
    - FR-DATAMGR-LAYERING-RULES: Verify submodules do not import upward from __init__.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/test_data_package.py --no-cov
    ```
"""

from __future__ import annotations

import importlib
import inspect

import app.workspace.data_manager as dm_pkg
import app.workspace.data_manager.generation as dm_gen
import app.workspace.data_manager.history as dm_hist
import app.workspace.data_manager.simulation as dm_sim
import pytest


class TestLegacyDataPackageRemoved:
    """Verify complete removal of legacy app.services.data package and shims."""

    @pytest.mark.parametrize(
        "legacy_module",
        [
            "app.services.data",
            "app.services.data.primitives",
            "app.services.data.catalog",
            "app.services.data.series",
            "app.services.data.history",
            "app.services.data.simulation",
            "app.services.data.generation",
            "app.services.libs",
            "app.services.libs.data",
        ],
    )
    def test_legacy_module_removed(self, legacy_module: str) -> None:
        """Verify that legacy module raises ModuleNotFoundError on import."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(legacy_module)


class TestDataManagerExportParity:
    """Verify package-level public exports and submodule parity in data_manager."""

    def test_history_exports_identity(self) -> None:
        """Verify history symbols match between data_manager and history submodule."""
        assert dm_pkg.DataBackend is dm_hist.DataBackend
        assert dm_pkg.DataBrokerBackend is dm_hist.DataBrokerBackend
        assert dm_pkg.validate_request is dm_hist.validate_request
        assert dm_pkg.validate_rows is dm_hist.validate_rows
        assert dm_pkg.get_historical_bars is dm_hist.get_historical_bars
        assert dm_pkg.get_ticks is dm_hist.get_ticks
        assert dm_pkg.BAR_COLUMNS is dm_hist.BAR_COLUMNS
        assert dm_pkg.TICK_COLUMNS is dm_hist.TICK_COLUMNS
        assert dm_pkg.bars_to_dataframe is dm_hist.bars_to_dataframe
        assert dm_pkg.ticks_to_dataframe is dm_hist.ticks_to_dataframe
        assert dm_pkg.bars_to_df is dm_hist.bars_to_df
        assert dm_pkg.ticks_to_df is dm_hist.ticks_to_df

    def test_simulation_exports_identity(self) -> None:
        """Verify simulation symbols match between data_manager and simulation."""
        assert dm_pkg.TickEvent is dm_sim.TickEvent
        assert dm_pkg.SpreadsMap is dm_sim.SpreadsMap
        assert dm_pkg.ITickSimulator is dm_sim.ITickSimulator
        assert dm_pkg.DefaultTickSimulator is dm_sim.DefaultTickSimulator
        assert dm_pkg.TSTickSimulator is dm_sim.TSTickSimulator

    def test_generation_exports_identity(self) -> None:
        """Verify generation symbols match between data_manager and generation."""
        assert dm_pkg.TICK_MODEL_REAL == dm_gen.TICK_MODEL_REAL
        assert dm_pkg.TICK_MODEL_GENERATED == dm_gen.TICK_MODEL_GENERATED
        assert dm_pkg.TICK_MODEL_TRADING_BAR == dm_gen.TICK_MODEL_TRADING_BAR
        assert dm_pkg.TICK_MODEL_OHLC_M1 == dm_gen.TICK_MODEL_OHLC_M1
        assert dm_pkg.SPREAD_FIXED == dm_gen.SPREAD_FIXED
        assert dm_pkg.SPREAD_NATIVE == dm_gen.SPREAD_NATIVE
        assert dm_pkg.SPREAD_VARIABLE == dm_gen.SPREAD_VARIABLE
        assert dm_pkg.SUPPORTED_TICK_MODELS is dm_gen.SUPPORTED_TICK_MODELS
        assert dm_pkg.SUPPORTED_SPREAD_MODELS is dm_gen.SUPPORTED_SPREAD_MODELS
        assert dm_pkg.PHASE_OPEN_CODE == dm_gen.PHASE_OPEN_CODE
        assert dm_pkg.PHASE_HIGH_CODE == dm_gen.PHASE_HIGH_CODE
        assert dm_pkg.PHASE_LOW_CODE == dm_gen.PHASE_LOW_CODE
        assert dm_pkg.PHASE_CLOSE_CODE == dm_gen.PHASE_CLOSE_CODE
        assert dm_pkg.TicksGenerator is dm_gen.TicksGenerator
        assert dm_pkg.generate_ticks is dm_gen.generate_ticks
        assert dm_pkg.generate_ticks_to_parquet is dm_gen.generate_ticks_to_parquet

    def test_all_exports_present_in_package(self) -> None:
        """Ensure every name in __all__ can be resolved from data_manager."""
        for name in dm_pkg.__all__:
            assert hasattr(dm_pkg, name), f"Missing export: {name}"


class TestLayeringAndAntiCircularRules:
    """Verify architectural layering rules and absence of circular imports."""

    def test_submodules_do_not_import_package_init(self) -> None:
        """Rule: Submodules must not import upward from app.workspace.data_manager."""
        submodules = [
            dm_hist,
            dm_sim,
            dm_gen,
        ]
        for submod in submodules:
            source = inspect.getsource(submod)
            assert "from app.workspace.data_manager import" not in source, (
                f"{submod.__name__} violates layering by importing from package top"
            )
            assert "import app.workspace.data_manager\n" not in source, (
                f"{submod.__name__} violates layering by importing package top"
            )
