"""Ask and Bid price logging strategy.

Description:
    Captures millisecond-level timestamps, current Ask price, and current Bid
    price on bar updates and records them into an output stream formatted as
    semicolon-separated records. Conforms to StrategyQuant
    SQ.Strategies.TestStrategyAskBid.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful TestStrategyAskBid strategy.

Key Capabilities:
    - FR-STRAT-ASKBID: Real-time spread and quote price recording.

Python API Usage:
    from app.extend.strategies.test_strategy_ask_bid import TestStrategyAskBid
    strat = TestStrategyAskBid()
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
from app.extend.strategies.base import Strategy

logger = get_logger(__name__)


class TestStrategyAskBid(Strategy):
    """Logs timestamped Ask and Bid prices on each bar update."""

    __test__ = False

    def __init__(self) -> None:
        super().__init__()
        self._writer: IO[str] | None = None
        self._records: list[str] = []

    def get_records(self) -> list[str]:
        """Return recorded Ask/Bid lines."""
        return list(self._records)

    @override
    def Initialize(self) -> None:
        """Initialize quote recording strategy."""
        logger.info("FR-STRAT-ASKBID: Initialize invoked")

    @override
    def OnBarUpdate(self) -> None:
        """Record formatted timestamp, Ask, and Bid prices."""
        ts_ms = self.Time.get(0)
        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        time_str = dt.strftime("%Y.%m.%d %H:%M:%S:000")

        line = f"{time_str};{self.Ask()};{self.Bid()}"
        self._records.append(line)
        if self._writer is not None:
            self._writer.write(line + "\n")

        logger.debug("FR-STRAT-ASKBID: recorded %s", line)

    @override
    def Deinitialize(self) -> None:
        """Flush and close output writer if open."""
        if self._writer is not None:
            self._writer.close()
            self._writer = None
        logger.info("FR-STRAT-ASKBID: Deinitialize completed")
