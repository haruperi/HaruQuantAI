"""Multi-chart update synchronization verification strategy.

Description:
    Validates chart addition across timeframes and symbols, confirms OHLC series
    retrieval across primary and secondary charts, and asserts single-chart update
    events via UpdatedChart and MultipleChartsUpdated flags. Conforms to StrategyQuant
    SQ.Strategies.TestStrategy.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful TestStrategy strategy.

Key Capabilities:
    - FR-STRAT-TESTSTRATEGY: Multi-chart subscription and single-chart event check.

Python API Usage:
    from app.extend.strategies.test_strategy import TestStrategy
    strat = TestStrategy()
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import Strategy

logger = get_logger(__name__)


class TestStrategy(Strategy):
    """Verifies multi-chart synchronization and update event indexing."""

    __test__ = False

    @override
    def Initialize(self) -> None:
        """Register H4 multi-chart instances."""
        self.MarketData.addChart("H4")
        self.MarketData.addChart("Symbol x1", "H4")
        self.MarketData.addChart("Connection 1", "Symbol x1", "H4")
        logger.info("FR-STRAT-TESTSTRATEGY: Initialize configured multi-charts")

    @override
    def OnBarUpdate(self) -> None:
        """Verify open price series and single-chart update state."""
        # Four ways of getting main chart open price
        _ = self.Open_price(0)
        _ = self.Open.get(0)
        _ = self.MarketData.Chart(0).Open_val(0)
        _ = self.MarketData.Chart(0).Open.get(0)

        # Three ways of getting secondary chart open price
        _ = self.Open_price(1, 0)
        _ = self.MarketData.Chart(1).Open_val(0)
        _ = self.MarketData.Chart(1).Open.get(0)

        _ = self.MarketData.Chart(1).Symbol

        _ = self.Open
        _ = self.MarketData.Chart(0).Open
        _ = self.MarketData.Chart(1).Open

        _ = self.UpdatedChart
        _ = self.MarketData.Chart(2).isUpdated()

        if self.MultipleChartsUpdated:
            raise ValueError("MultipleChartsUpdated - this shouldn't happen here!")

        logger.info("FR-STRAT-TESTSTRATEGY: OnBarUpdate validated single chart update")
