"""Test canonical core data contracts and enums, and verify legacy include removal."""

from __future__ import annotations

import importlib

import app.core.data.contracts as new_contracts
import app.core.enums as new_enums
import pytest


def test_canonical_type_identity() -> None:
    """Verify that canonical contracts and enums are present and legacy bridge is removed."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.contracts")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.enums")

    assert new_contracts.MarketBar is not None
    assert new_contracts.MarketTick is not None
    assert new_contracts.ChartDef is not None
    assert new_contracts.DataInfo is not None
    assert new_contracts.SymbolInfo is not None
    assert new_contracts.TradeRequest is not None
    assert new_contracts.TradingSession is not None

    # Exact timeframe second values per WO-C06.01
    assert new_enums.Timeframe.PERIOD_M1.to_seconds() == 60
    assert new_enums.Timeframe.PERIOD_H1.to_seconds() == 3600
    assert new_enums.Timeframe.PERIOD_D1.to_seconds() == 86400
