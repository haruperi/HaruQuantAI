"""Live Test Strategy 1 periodic hourly/half-hourly trade verification.

Description:
    Opens a trade on a strict time interval (Buy on full hour, minute 0; Sell on
    half hour, minute 30) and closes the position after 4 elapsed bars. Used to
    validate backtest execution bit-parity against live trading. Conforms to
    StrategyQuant SQ.Strategies.LiveTestStrategy1.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful LiveTestStrategy1 strategy.

Key Capabilities:
    - FR-STRAT-LIVETEST1: Periodic time-based entry and bar-count duration exit.

Python API Usage:
    from app.extend.strategies.live_test_strategy_1 import LiveTestStrategy1
    strat = LiveTestStrategy1()
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import (
    ILiveOrder,
    OrderCloseTypes,
    OrderTypes,
    Strategy,
    UpdateEventTypes,
)

logger = get_logger(__name__)

BARS_IN_TRADE_LIMIT = 4
MINUTE_HALF_HOUR = 30


class LiveTestStrategy1(Strategy):
    """Execution parity verification strategy opening trades every 30 minutes."""

    def __init__(self) -> None:
        super().__init__()
        self.order: ILiveOrder | None = None

    @override
    def Initialize(self) -> None:
        """Configure update event triggering to BarOpen."""
        self.setUpdateEventType(UpdateEventTypes.BarOpen)
        logger.info("FR-STRAT-LIVETEST1: Initialize invoked")

    @override
    def OnBarUpdate(self) -> None:
        """Manage active trade duration and trigger periodic entries."""
        if (
            self.order is not None
            and self.order.getBarsInTrade() >= BARS_IN_TRADE_LIMIT
        ):
            self.order.Close(OrderCloseTypes.Manual)
            self.order = None

        if self.order is None:
            trade_type: int = 0
            ts_ms = self.MarketData.Chart(0).Time(0)
            dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
            minute = dt.minute

            if minute == 0:
                trade_type = OrderTypes.Buy
            elif minute == MINUTE_HALF_HOUR:
                trade_type = OrderTypes.Sell

            if trade_type != 0:
                self.order = (
                    self.Trader.Open(trade_type, self.Symbol, 1.0)
                    .setMagicNumber(0)
                    .setComment("LiveTestStrategy1")
                    .Send()
                )

        logger.info(
            "FR-STRAT-LIVETEST1: OnBarUpdate processed (active_order=%s)",
            self.order is not None,
        )
