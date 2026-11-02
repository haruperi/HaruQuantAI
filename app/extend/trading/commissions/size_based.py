"""Size-based commission model snippet.

Description:
    Implements size-based commission model conforming to StrategyQuant
    SQ.Trading.Commissions.SizeBased. Computes commission proportional to
    trade volume (lots/contracts) on order open.

Purpose:
    FEAT-TRADING-COMMISSIONS: Port SizeBased commission method from StrategyQuant.

Key Capabilities:
    - FR-COMMISSIONS-SIZE-BASED: Calculate commission per full lot/share.

Python API Usage:
    from app.extend.trading.commissions.size_based import SizeBasedCommission
    comm = SizeBasedCommission(Commission=7.0)
    fee = comm.computeCommissionsOnOpen(order)

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py -k test_size_based
"""

from __future__ import annotations

import logging
from typing import Any, override

from app.extend.trading.commissions.base import (
    CommissionsMethod,
    CommissionsMethodsList,
    get_order_size,
)

logger = logging.getLogger(__name__)


class SizeBased(CommissionsMethod):
    """Size-based commission method matching SQ Commissions/SizeBased.java."""

    name: str = "Size based"
    display: str = "$ #Commission# per full lot"

    def __init__(
        self,
        Commission: float = 0.0,  # noqa: N803
        commission_per_lot: float | None = None,
    ) -> None:
        super().__init__()
        self.Commission: float = (
            commission_per_lot if commission_per_lot is not None else Commission
        )
        logger.debug(
            "FR-COMMISSIONS-SIZE-BASED: initialized Commission=%f",
            self.Commission,
        )

    @property
    def commission_per_lot(self) -> float:
        """Alias for Commission."""
        return self.Commission

    @override
    def computeCommissionsOnOpen(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on open: Commission * order.getSize()."""
        _ = (tickSize, pointValue)
        fee = self.Commission * get_order_size(order)
        logger.debug("FR-COMMISSIONS-SIZE-BASED: open fee=%f", fee)
        return fee

    @override
    def computeCommissionsOnClose(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on close (always 0.0 for size-based)."""
        _ = (order, tickSize, pointValue)
        logger.debug("FR-COMMISSIONS-SIZE-BASED: close fee=0.0")
        return 0.0


SizeBasedCommission = SizeBased

CommissionsMethodsList.register("SizeBased", SizeBased)
CommissionsMethodsList.register("Size based", SizeBased)
CommissionsMethodsList.register("SizeBasedCommission", SizeBased)

__all__ = [
    "SizeBased",
    "SizeBasedCommission",
]
