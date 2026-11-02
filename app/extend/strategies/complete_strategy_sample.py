"""Complete Strategy Sample demonstration strategy.

Description:
    Demonstrates the full scope of StrategyQuant strategy runtime capabilities,
    including setting update event types, reading chart data metadata (symbol,
    connection, timeframe), accessing primary and secondary chart open series,
    and verifying data retrieval consistency across multiple interfaces.
    Conforms to StrategyQuant SQ.Strategies.CompleteStrategySample.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful CompleteStrategySample strategy.

Key Capabilities:
    - FR-STRAT-COMPLETE-SAMPLE: Multi-chart inspection, series equivalence, and
      event control.

Python API Usage:
    from app.extend.strategies.complete_strategy_sample import CompleteStrategySample
    strat = CompleteStrategySample()
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import Log, Strategy, UpdateEventTypes

logger = get_logger(__name__)


class CompleteStrategySample(Strategy):
    """Reference implementation demonstrating multi-chart data and trading methods."""

    @override
    def Initialize(self) -> None:
        """Configure update event triggering to BarOpen."""
        _ = self.getEventType()
        self.setUpdateEventType(UpdateEventTypes.BarOpen)
        logger.info("FR-STRAT-COMPLETE-SAMPLE: Initialize invoked")

    @override
    def OnBarUpdate(self) -> None:
        """Verify data access across primary and secondary charts."""
        Log.debug("Tick processed!")

        _ = self.UpdatedChart
        _ = self.MultipleChartsUpdated
        _ = self.UpdateEventType
        _ = self.Bars()

        chart0 = self.MarketData.Chart(0)
        _ = chart0.Time(0)
        _ = chart0.Symbol
        _ = chart0.Connection
        _ = chart0.Timeframe
        _ = chart0.EventType

        # Four ways of getting open price on main chart
        o1 = self.Open_price(0)
        o2 = self.Open.get(0)
        o3 = chart0.Open_val(0)
        o4 = chart0.Open.get(0)

        if o1 != o2 or o1 != o3 or o1 != o4:
            raise ValueError(
                f"Values from Open() are not same (1): {o1}, {o2}, {o3}, {o4}"
            )

        # Three ways of getting open price on 4th chart (index 3)
        chart3 = self.MarketData.Chart(3)
        o5 = self.Open_price(3, 0)
        o6 = chart3.Open_val(0)
        o7 = chart3.Open.get(0)

        if o5 != o6 or o5 != o7:
            raise ValueError(f"Values from Open() are not same (2): {o5}, {o6}, {o7}")

        # Access DataSeries objects
        _ = self.Open
        _ = chart0.Open
        _ = self.MarketData.Chart(1).Open

        logger.info("FR-STRAT-COMPLETE-SAMPLE: OnBarUpdate validated data streams")
