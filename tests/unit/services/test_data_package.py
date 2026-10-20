"""Unit tests verifying removal of app.services.data and unification into include.data.

Description:
    Verifies that the legacy app.services.data package and all its submodules have
    been completely removed with zero backward compatibility shims, that canonical
    market data capabilities are exported from app.services.include, and that
    app.workspace.data_manager does not re-export app.services.include symbols.

Purpose:
    FEAT-DATAMGR-UNIFICATION: Zero-shim removal verification of legacy data package.

Key Capabilities:
    - FR-DATA-PACKAGE-REMOVAL: Verify legacy app.services.data modules raise error.
    - FR-DATAMGR-EXPORT-PARITY: Verify public export surface in app.services.include.
    - FR-DATAMGR-LAYERING-RULES: Verify submodules do not import upward from workspace.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/test_data_package.py --no-cov
    ```
"""

from __future__ import annotations

import importlib
import inspect

import app.services.include as include_pkg
import app.services.include.data as dm_hist
import app.workspace.data_manager as dm_pkg
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
            "app.workspace.data_manager.history",
        ],
    )
    def test_legacy_module_removed(self, legacy_module: str) -> None:
        """Verify that legacy module raises ModuleNotFoundError on import."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(legacy_module)


class TestDataManagerExportParity:
    """Verify package-level public exports in app.services.include and data_manager."""

    def test_history_exports_identity(self) -> None:
        """Verify history symbols match between app.services.include and include.data."""
        assert include_pkg.DataBackend is dm_hist.DataBackend
        assert include_pkg.validate_request is dm_hist.validate_request
        assert include_pkg.validate_rows is dm_hist.validate_rows
        assert include_pkg.get_historical_bars is dm_hist.get_historical_bars
        assert include_pkg.get_ticks is dm_hist.get_ticks
        assert include_pkg.BAR_COLUMNS is dm_hist.BAR_COLUMNS
        assert include_pkg.TICK_COLUMNS is dm_hist.TICK_COLUMNS
        assert include_pkg.bars_to_dataframe is dm_hist.bars_to_dataframe
        assert include_pkg.ticks_to_dataframe is dm_hist.ticks_to_dataframe
        assert include_pkg.bars_to_df is dm_hist.bars_to_df
        assert include_pkg.ticks_to_df is dm_hist.ticks_to_df

    def test_all_exports_present_in_package(self) -> None:
        """Ensure every name in __all__ can be resolved from data_manager and include."""
        for name in dm_pkg.__all__:
            assert hasattr(dm_pkg, name), f"Missing export in data_manager: {name}"
        for name in include_pkg.__all__:
            assert hasattr(include_pkg, name), f"Missing export in include: {name}"
        assert not hasattr(dm_pkg, "MarketBar")
        assert not hasattr(dm_pkg, "MarketTick")
        assert not hasattr(dm_pkg, "Timeframe")


class TestLayeringAndAntiCircularRules:
    """Verify architectural layering rules and absence of circular imports."""

    def test_submodules_do_not_import_package_init(self) -> None:
        """Rule: Submodules must not import upward from app.workspace.data_manager."""
        source = inspect.getsource(dm_hist)
        assert "from app.workspace.data_manager import" not in source, (
            f"{dm_hist.__name__} violates layering by importing from package top"
        )
        assert "import app.workspace.data_manager\n" not in source, (
            f"{dm_hist.__name__} violates layering by importing package top"
        )
