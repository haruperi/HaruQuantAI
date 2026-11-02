"""Flat per-trade commission model snippet.

Description:
    Implements flat per-trade commission model conforming to StrategyQuant
    SQ.Trading.Commissions.PerTrade. Applies fixed commission per trade side
    (on open and close, skipping pending orders).

Purpose:
    FEAT-TRADING-COMMISSIONS: Port PerTrade commission method from StrategyQuant.

Key Capabilities:
    - FR-COMMISSIONS-PER-TRADE: Apply fixed dollar amount commission per trade side.

Python API Usage:
    from app.extend.trading.commissions.per_trade import PerTradeCommission
    comm = PerTradeCommission(Commission=5.0)
    fee = comm.computeCommissionsOnOpen(order)

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py -k test_per_trade
"""

from __future__ import annotations

import logging
from typing import Any, override

from app.extend.trading.commissions.base import (
    CommissionsMethod,
    CommissionsMethodsList,
    get_order_size,
    is_pending_order,
)

logger = logging.getLogger(__name__)


class PerTrade(CommissionsMethod):
    """Flat fee per trade matching StrategyQuant Commissions/PerTrade.java."""

    name: str = "Per trade "
    display: str = "$ #Commission# per trade"

    def __init__(
        self,
        Commission: float = 0.0,  # noqa: N803
        commission: float | None = None,
    ) -> None:
        super().__init__()
        self.Commission: float = commission if commission is not None else Commission
        logger.debug(
            "FR-COMMISSIONS-PER-TRADE: initialized Commission=%f",
            self.Commission,
        )

    @property
    def commission(self) -> float:
        """Alias for Commission."""
        return self.Commission

    @override
    def computeCommissionsOnOpen(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on trade open (fixed dollar amount)."""
        _ = (tickSize, pointValue)
        size = get_order_size(order)
        fee = max(self.Commission, 0.0) if size > 0.0 else 0.0
        logger.debug("FR-COMMISSIONS-PER-TRADE: open fee=%f", fee)
        return fee

    @override
    def computeCommissionsOnClose(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on trade close (skips pending orders)."""
        _ = (tickSize, pointValue)
        if is_pending_order(order):
            logger.debug("FR-COMMISSIONS-PER-TRADE: pending order, close fee=0.0")
            return 0.0
        size = get_order_size(order)
        fee = max(self.Commission, 0.0) if size > 0.0 else 0.0
        logger.debug("FR-COMMISSIONS-PER-TRADE: close fee=%f", fee)
        return fee

    @override
    def compute_commission(
        self,
        *,
        size: float = 1.0,
        open_price: float = 1.0,
        close_price: float | None = None,
        point_value: float = 1.0,
    ) -> float:
        """Legacy flat fee per trade execution matching cohort test expectation."""
        _ = (open_price, close_price, point_value)
        fee = max(self.Commission, 0.0) if size > 0.0 else 0.0
        logger.debug("FR-COMMISSIONS-PER-TRADE: legacy compute_commission fee=%f", fee)
        return round(fee, 6)


PerTradeCommission = PerTrade

CommissionsMethodsList.register("PerTrade", PerTrade)
CommissionsMethodsList.register("Per trade ", PerTrade)
CommissionsMethodsList.register("PerTradeCommission", PerTrade)

__all__ = [
    "PerTrade",
    "PerTradeCommission",
]
