"""Robustness test strategy with async trading events.

Description:
    Tests order state transitions, asynchronous order submission with listener
    callbacks, dynamic modification of Stop Loss and Profit Target levels on open
    trades, and bar-duration exit rules. Conforms to StrategyQuant
    SQ.Strategies.RobustnessTestStrategy.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful RobustnessTestStrategy strategy.

Key Capabilities:
    - FR-STRAT-ROBUSTNESS: Asynchronous order execution and event listener handling.

Python API Usage:
    from app.extend.strategies.robustness_test_strategy import RobustnessTestStrategy
    strat = RobustnessTestStrategy()
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


class RobustnessTestStrategy(Strategy, ITradingEventListener):
    """Robustness testing strategy alternating buy and sell orders with async events."""

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
        logger.info("FR-STRAT-ROBUSTNESS: Initialize configured BarOpen")

    @override
    def OnBarUpdate(self) -> None:
        """Manage active trade lifecycle, SL/PT adjustment, and alternate directions."""
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
            "FR-STRAT-ROBUSTNESS: OnBarUpdate executed (trade_type=%s)",
            self._trade_type,
        )

    @override
    def OnEvent(self, event: ITradingEvent) -> None:
        """Handle global trading event notifications."""
        self.events_received.append(event)
        logger.debug("FR-STRAT-ROBUSTNESS: OnEvent received %s", event.event_type)

    @override
    def OnTradingEvent(self, event: ITradingEvent) -> None:
        """Handle order-specific asynchronous event notifications."""
        self.events_received.append(event)
        logger.debug(
            "FR-STRAT-ROBUSTNESS: OnTradingEvent received %s", event.event_type
        )
