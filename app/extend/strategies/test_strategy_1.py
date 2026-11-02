"""Asynchronous order event dispatch testing strategy.

Description:
    Tests alternating Buy/Sell order dispatch with asynchronous listener
    callbacks (ITradingEventListener), dynamic SL/PT adjustment on active
    positions, and bar-duration exit limits. Conforms to StrategyQuant
    SQ.Strategies.TestStrategy1.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful TestStrategy1 strategy.

Key Capabilities:
    - FR-STRAT-TESTSTRATEGY1: Asynchronous order execution and listener handling.

Python API Usage:
    from app.extend.strategies.test_strategy_1 import TestStrategy1
    strat = TestStrategy1()
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import (
    ILiveOrder,
    ITradingEvent,
    ITradingEventListener,
    OrderCloseTypes,
    OrderTypes,
    Strategy,
    UpdateEventTypes,
)

logger = get_logger(__name__)


class TestStrategy1(Strategy, ITradingEventListener):
    """Execution test strategy toggling Buy/Sell orders via async dispatch."""

    __test__ = False

    def __init__(self) -> None:
        super().__init__()
        self._order: ILiveOrder | None = None
        self._trade_type: int = OrderTypes.Buy
        self.ExitAfterBars: int = 5
        self.events_received: list[ITradingEvent] = []

    @override
    def Initialize(self) -> None:
        """Configure update event triggering to BarOpen."""
        self.setUpdateEventType(UpdateEventTypes.BarOpen)
        logger.info("FR-STRAT-TESTSTRATEGY1: Initialize configured BarOpen")

    @override
    def OnBarUpdate(self) -> None:
        """Execute alternating Buy/Sell orders and manage duration exits."""
        if (
            self._order is not None
            and self._order.getBarsInTrade() > self.ExitAfterBars
        ):
            self._order.Close(OrderCloseTypes.Deleted)
            self._order = None

        if self._order is None:
            self._trade_type = (
                OrderTypes.Sell
                if self._trade_type == OrderTypes.Buy
                else OrderTypes.Buy
            )
            self._order = (
                self.Trader.Open(self._trade_type, self.Symbol)
                .setMagicNumber(0)
                .SendAsync(self)
            )
        else:
            self._order.setSL(1.234).setPT(1.234).Send()

        logger.info(
            "FR-STRAT-TESTSTRATEGY1: OnBarUpdate executed (trade_type=%s)",
            self._trade_type,
        )

    @override
    def OnEvent(self, event: ITradingEvent) -> None:
        """Handle global trading event notifications."""
        self.events_received.append(event)
        logger.debug("FR-STRAT-TESTSTRATEGY1: OnEvent received %s", event.event_type)

    @override
    def OnTradingEvent(self, event: ITradingEvent) -> None:
        """Handle order-specific asynchronous event notifications."""
        self.events_received.append(event)
        logger.debug(
            "FR-STRAT-TESTSTRATEGY1: OnTradingEvent received %s", event.event_type
        )
