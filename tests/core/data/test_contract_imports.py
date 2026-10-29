"""Test identity between legacy bridge paths and canonical core data contracts and enums."""

from __future__ import annotations

import app.core.data.contracts as new_contracts
import app.core.enums as new_enums
import app.include.contracts as old_contracts
import app.include.enums as old_enums


def test_canonical_type_identity() -> None:
    """Verify that importing old and new contracts/enums returns identical objects."""
    assert old_contracts.MarketBar is new_contracts.MarketBar
    assert old_contracts.MarketTick is new_contracts.MarketTick
    assert old_contracts.ChartDef is new_contracts.ChartDef
    assert old_contracts.DataInfo is new_contracts.DataInfo
    assert old_contracts.SymbolInfo is new_contracts.SymbolInfo
    assert old_contracts.TradeRequest is new_contracts.TradeRequest
    assert old_contracts.TradingSession is new_contracts.TradingSession
    assert old_enums.Timeframe is new_enums.Timeframe
    assert old_enums.OrderType is new_enums.OrderType

    # Exact timeframe second values per WO-C06.01
    assert new_enums.Timeframe.PERIOD_M1.to_seconds() == 60
    assert new_enums.Timeframe.PERIOD_H1.to_seconds() == 3600
    assert new_enums.Timeframe.PERIOD_D1.to_seconds() == 86400
