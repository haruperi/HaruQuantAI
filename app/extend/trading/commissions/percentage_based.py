"""Percentage based commission model snippet.

Description:
    Implements percentage based commission model conforming to StrategyQuant
    SQ.Trading.Commissions.PercentageBased. Computes commission as a percentage
    of purchased asset equity/notional on order open.

Purpose:
    FEAT-TRADING-COMMISSIONS: Port PercentageBased commission method from StrategyQuant.

Key Capabilities:
    - FR-COMMISSIONS-PERCENTAGE-BASED: Calculate commission as % of asset notional.

Python API Usage:
    from app.extend.trading.commissions.percentage_based import (
        PercentageBasedCommission,
    )
    comm = PercentageBasedCommission(CommissionPct=0.1)
    fee = comm.computeCommissionsOnOpen(order)

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py -k test_percentage_based
"""

from __future__ import annotations

import logging
from typing import Any, override

from app.extend.trading.commissions.base import (
    CommissionsMethod,
    CommissionsMethodsList,
    get_order_open_price,
    get_order_size,
)

logger = logging.getLogger(__name__)


class PercentageBased(CommissionsMethod):
    """Percentage based commission method matching SQ PercentageBased.java."""

    name: str = "Percentage based"
    display: str = "#CommissionPct# % of equity"

    def __init__(
        self,
        CommissionPct: float = 0.0,  # noqa: N803
        commission_pct: float | None = None,
    ) -> None:
        super().__init__()
        self.CommissionPct: float = (
            commission_pct if commission_pct is not None else CommissionPct
        )
        logger.debug(
            "FR-COMMISSIONS-PERCENTAGE-BASED: initialized CommissionPct=%f",
            self.CommissionPct,
        )

    @property
    def commission_pct(self) -> float:
        """Alias for CommissionPct."""
        return self.CommissionPct

    @override
    def computeCommissionsOnOpen(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on open as percentage of notional value."""
        _ = tickSize
        pct_commission = self.CommissionPct / 100.0
        purchased_equity = (
            get_order_size(order) * get_order_open_price(order) * pointValue
        )
        fee = pct_commission * purchased_equity
        logger.debug(
            "FR-COMMISSIONS-PERCENTAGE-BASED: open equity=%f fee=%f",
            purchased_equity,
            fee,
        )
        return fee

    @override
    def computeCommissionsOnClose(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on close (0.0 for percentage based)."""
        _ = (order, tickSize, pointValue)
        logger.debug("FR-COMMISSIONS-PERCENTAGE-BASED: close fee=0.0")
        return 0.0


PercentageBasedCommission = PercentageBased

CommissionsMethodsList.register("PercentageBased", PercentageBased)
CommissionsMethodsList.register("Percentage based", PercentageBased)
CommissionsMethodsList.register("PercentageBasedCommission", PercentageBased)

__all__ = [
    "PercentageBased",
    "PercentageBasedCommission",
]
