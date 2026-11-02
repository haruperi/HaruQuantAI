"""CCI Reverse trading strategy.

Description:
    Implements a mean-reverting / trend-following strategy based on Commodity
    Channel Index (CCI) zero-line crossovers. Long entries occur when CCI(20) > 0,
    closing opposite short positions. Short entries occur when CCI(20) < 0,
    closing opposite long positions. Conforms to StrategyQuant SQ.Strategies.CCIReverse.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful CCIReverse strategy.

Key Capabilities:
    - FR-STRAT-CCIREVERSE: Zero-line CCI cross detection with reverse order closing.

Python API Usage:
    from app.extend.strategies.cci_reverse import CCIReverse
    strat = CCIReverse()
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import (
    OrderCloseTypes,
    OrderTypes,
    Strategy,
    UpdateEventTypes,
)

logger = get_logger(__name__)


class CCIReverse(Strategy):
    """CCI zero-line reversal strategy closing opposing positions on signal."""

    @override
    def Initialize(self) -> None:
        """Initialize event triggering preferences."""
        logger.info("FR-STRAT-CCIREVERSE: Initialize invoked")

    @override
    def OnBarUpdate(self) -> None:
        """Evaluate CCI and open / close reverse positions."""
        if self.UpdateEventType != UpdateEventTypes.BarOpen:
            return

        cci_value = self.Indicators.CCI(self.Open, 20).Value.get(0)

        if cci_value > 0:
            self._close_opposite_order(1234, OrderTypes.Sell)
            self.Trader.Buy(self.Symbol).setMagicNumber(1234).Send()

        if cci_value < 0:
            self._close_opposite_order(1234, OrderTypes.Buy)
            self.Trader.Sell(self.Symbol).setMagicNumber(1234).Send()
            self.Trader.getAccountBalance()

        logger.info("FR-STRAT-CCIREVERSE: OnBarUpdate processed with cci=%s", cci_value)

    def _close_opposite_order(self, magic_number: int, order_type: int) -> None:
        """Close open orders matching magic number and order type."""
        count = self.Trader.getOpenOrdersCount(True)
        for i in range(count):
            order = self.Trader.getOpenOrder(i, True)
            if (
                order.getMagicNumber() == magic_number
                and order.getOrderType() == order_type
            ):
                order.Close(OrderCloseTypes.Reversed)
