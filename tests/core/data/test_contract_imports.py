"""Test canonical core data contracts and enums, and verify legacy include removal."""

from __future__ import annotations

import importlib

import app.core.data.contracts as data_contracts
import app.core.enums as new_enums
import pytest
from app.core.data.charts import ChartDef
from app.core.trading.connection.contracts import TradeRequest


def test_canonical_type_identity() -> None:
    """Verify that canonical contracts and enums are present and legacy bridge is removed."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.contracts")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.enums")

    # Pure data contracts present in app.core.data.contracts
    assert data_contracts.MarketBar.__module__ == "app.core.data.contracts"
    assert data_contracts.MarketTick.__module__ == "app.core.data.contracts"
    assert ChartDef.__module__ == "app.core.data.charts"
    assert not hasattr(data_contracts, "ChartDef")
    assert data_contracts.DataInfo.__module__ == "app.core.data.contracts"
    assert data_contracts.SymbolInfo.__module__ == "app.core.data.contracts"
    assert data_contracts.TradingSession.__module__ == "app.core.data.contracts"
    assert data_contracts.BookInfo.__module__ == "app.core.data.contracts"
    assert data_contracts.DataframeSeries.__module__ == "app.core.data.contracts"

    # Trading connection contracts cleanly decoupled from app.core.data.contracts
    assert not hasattr(data_contracts, "TradeRequest")
    assert not hasattr(data_contracts, "OrderInfo")
    assert not hasattr(data_contracts, "AccountInfo")
    assert not hasattr(data_contracts, "PositionInfo")
    assert not hasattr(data_contracts, "DealInfo")
    assert not hasattr(data_contracts, "BridgeError")

    # TradeRequest cleanly imported from app.core.trading.connection.contracts
    assert TradeRequest.__module__ == "app.core.trading.connection.contracts"

    # Exact timeframe second values per WO-C06.01
    assert new_enums.Timeframe.PERIOD_M1.to_seconds() == 60
    assert new_enums.Timeframe.PERIOD_H1.to_seconds() == 3600
    assert new_enums.Timeframe.PERIOD_D1.to_seconds() == 86400
