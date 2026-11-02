"""Market Data Test Strategy.

Description:
    Validates the addition of charts with varying timeframes, symbols, and
    connections, and tests multiple ways of querying Open prices from primary
    and secondary charts. Conforms to SQ.Strategies.MarketDataTestStrategy.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful MarketDataTestStrategy strategy.

Key Capabilities:
    - FR-STRAT-MARKETDATA-TEST: Dynamic chart registration and price accessor tests.

Python API Usage:
    from app.extend.strategies.market_data_test_strategy import MarketDataTestStrategy
    strat = MarketDataTestStrategy()
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import Log, Strategy

logger = get_logger(__name__)


class MarketDataTestStrategy(Strategy):
    """Verifies adding H4 charts and querying price series on charts."""

    @override
    def Initialize(self) -> None:
        """Register H4 charts with diverse parameter signatures."""
        self.MarketData.addChart("H4")
        self.MarketData.addChart("Symbol x1", "H4")
        self.MarketData.addChart("Connection 1", "Symbol x1", "H4")
        logger.info("FR-STRAT-MARKETDATA-TEST: Initialize registered charts")

    @override
    def OnBarUpdate(self) -> None:
        """Access open price series and verify data integrity."""
        # Four ways of getting open price of main chart
        _ = self.Open_price(0)
        _ = self.Open.get(0)
        _ = self.MarketData.Chart(0).Open_val(0)
        _ = self.MarketData.Chart(0).Open.get(0)

        # Three ways of getting open price of second chart
        _ = self.Open_price(1, 0)
        _ = self.MarketData.Chart(1).Open_val(0)
        _ = self.MarketData.Chart(1).Open.get(0)

        _ = self.MarketData.Chart(1).Symbol

        # Data series instances
        _ = self.Open
        _ = self.MarketData.Chart(0).Open
        _ = self.MarketData.Chart(1).Open

        Log.info("BAR UPDATE")
        logger.info("FR-STRAT-MARKETDATA-TEST: OnBarUpdate validated series access")
