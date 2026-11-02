"""Multi-chart data recording and verification strategy.

Description:
    Tests multi-chart initialization, chart property verification (connections,
    symbols, timeframes), tick grouping, and data series equality across multiple
    charts. Conforms to StrategyQuant SQ.Strategies.MarketDataChartData1TestStrategy1.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful MarketDataChartData1TestStrategy1.

Key Capabilities:
    - FR-STRAT-CHARTDATA1: Multi-chart registration, FullData record logging.

Python API Usage:
    from app.extend.strategies.market_data_chart_data_1_test_strategy_1 import (
        MarketDataChartData1TestStrategy1,
    )
    strat = MarketDataChartData1TestStrategy1()
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import Log, Strategy

logger = get_logger(__name__)

MAX_TICKS_COUNT = 20
CHART_INDEX_THRESHOLD = 4


@dataclass
class FullData:
    """Historical bar snapshot holding time, price, and chart attributes."""

    time: int = 0
    open: float = 0.0
    symbol: str = ""
    connection: str = ""
    timeframe: str = ""


class MarketDataChartData1TestStrategy1(Strategy):
    """Verifies multi-chart datasets, chart indexing, and data series equivalence."""

    def __init__(self) -> None:
        super().__init__()
        self.data: list[FullData] = []
        self.count: int = -1

    @override
    def Initialize(self) -> None:
        """Register custom multi-chart configurations."""
        c0 = self.MarketData.Chart(0)
        c0.Connection = "XTestConn1"
        c0.Symbol = "XSymbol_1_1"

        c1 = self.MarketData.Chart(1)
        c1.Connection = "XTestConn1"
        c1.Symbol = "XSymbol_1_2"

        c2 = self.MarketData.addChart("XSymbol_1_3", "H1")
        c2.Connection = "XTestConn1"

        self.MarketData.addChart("History", "XSymbol_0_1", "H1")
        self.MarketData.addChart("History", "XSymbol_0_2", "H1")
        logger.info("FR-STRAT-CHARTDATA1: Initialize completed with charts")

    @override
    def OnBarUpdate(self) -> None:
        """Process simulated tick updates and evaluate chart parity."""
        self.count += 1
        Log.debug("Tick processed!")

        if self.count >= MAX_TICKS_COUNT:
            Log.info("Stopping strategy here!")
            self.StopStrategy()

        if self.count % 4 > 0:
            return

        chart_index = self.count // 4
        chart = self.MarketData.Chart(chart_index)

        fd = FullData(
            time=chart.Time(0),
            open=chart.Open_val(0),
            symbol=chart.Symbol,
            connection=chart.Connection,
            timeframe=chart.Timeframe,
        )
        self.data.append(fd)

        if chart_index < CHART_INDEX_THRESHOLD:
            return

        self._verify_price_parity()
        self._verify_chart_metadata()
        logger.info("FR-STRAT-CHARTDATA1: Multi-chart metadata successfully validated")

    def _verify_price_parity(self) -> None:
        """Assert open price equivalences across primary and secondary charts."""
        o1 = self.Open_price(0)
        o2 = self.Open.get(0)
        o3 = self.MarketData.Chart(0).Open_val(0)
        o4 = self.MarketData.Chart(0).Open.get(0)

        if o1 != o2 or o1 != o3 or o1 != o4:
            raise ValueError("Values from Open() are not same (1)!")

        chart3 = self.MarketData.Chart(3)
        o5 = self.Open_price(3, 0)
        o6 = chart3.Open_val(0)
        o7 = chart3.Open.get(0)

        if o5 != o6 or o5 != o7:
            raise ValueError("Values from Open() are not same (2)!")

    def _verify_chart_metadata(self) -> None:
        """Assert connection strings and symbol tags match expectations."""
        expected = [
            (0, "XTestConn1", "XSymbol_1_1", "Error 1", "Error 2"),
            (1, "XTestConn1", "XSymbol_1_2", "Error 3", "Error 4"),
            (2, "XTestConn1", "XSymbol_1_3", "Error 5", "Error 6"),
            (3, "History", "XSymbol_0_1", "Error 7", "Error 8"),
            (4, "History", "XSymbol_0_2", "Error 9", "Error 10"),
        ]
        for idx, exp_conn, exp_sym, err_conn, err_sym in expected:
            c = self.MarketData.Chart(idx)
            if c.Connection != exp_conn:
                raise ValueError(err_conn)
            if c.Symbol != exp_sym:
                raise ValueError(err_sym)
