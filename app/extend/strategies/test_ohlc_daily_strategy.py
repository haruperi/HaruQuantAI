"""Daily OHLC and multi-timeframe price shift verification strategy.

Description:
    Records intraday OHLC, Ask, Bid, and daily OHLC values across multiple shift
    intervals (0, 10, 20 bars back) into a formatted CSV record stream once the
    simulated bar time surpasses a configured start threshold. Conforms to
    StrategyQuant SQ.Strategies.TestOHLCDailyStrategy.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful TestOHLCDailyStrategy strategy.

Key Capabilities:
    - FR-STRAT-TESTOHLC: Multi-timeframe daily shift alignment and tick-level export.

Python API Usage:
    from app.extend.strategies.test_ohlc_daily_strategy import TestOHLCDailyStrategy
    strat = TestOHLCDailyStrategy()
    strat.Initialize()
    strat.OnBarUpdate()
    strat.Deinitialize()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import IO, override

from app.core.host.logging import get_logger
from app.extend.strategies.base import Strategy, UpdateEventTypes

logger = get_logger(__name__)


class TestOHLCDailyStrategy(Strategy):
    """Outputs intraday and daily OHLC shifted values to CSV stream."""

    __test__ = False

    def __init__(self, start_time: int = 1211241600000) -> None:
        super().__init__()
        self._start_time: int = start_time
        self._writer: IO[str] | None = None
        self._records: list[str] = []

    def get_records(self) -> list[str]:
        """Return captured CSV records."""
        return list(self._records)

    @override
    def Initialize(self) -> None:
        """Set update event type to BarTick and configure start timestamp."""
        self.setUpdateEventType(UpdateEventTypes.BarTick)
        logger.info(
            "FR-STRAT-TESTOHLC: Initialize configured with start_time=%s",
            self._start_time,
        )

    @override
    def OnBarUpdate(self) -> None:
        """Record OHLC, Ask/Bid, and daily shifts once threshold reached."""
        if self.Time.get(0) < self._start_time:
            return

        ts_ms = self.TimeCurrent()
        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        time_str = dt.strftime("%Y.%m.%d %H:%M:%S")

        parts = [
            time_str,
            str(self.Open.get(0)),
            str(self.High.get(0)),
            str(self.Low.get(0)),
            str(self.Close.get(0)),
            str(self.Ask()),
            str(self.Bid()),
            str(self.OpenD.get(0)),
            str(self.HighD.get(0)),
            str(self.LowD.get(0)),
            str(self.CloseD.get(0)),
            str(self.OpenD.get(10)),
            str(self.HighD.get(10)),
            str(self.LowD.get(10)),
            str(self.CloseD.get(10)),
            str(self.OpenD.get(20)),
            str(self.HighD.get(20)),
            str(self.LowD.get(20)),
            str(self.CloseD.get(20)),
        ]
        record = ";".join(parts)
        self._records.append(record)
        if self._writer is not None:
            self._writer.write(record + "\n")

        logger.debug("FR-STRAT-TESTOHLC: recorded line %s", record)

    @override
    def Deinitialize(self) -> None:
        """Close output writer."""
        if self._writer is not None:
            self._writer.close()
            self._writer = None
        logger.info("FR-STRAT-TESTOHLC: Deinitialize completed")
