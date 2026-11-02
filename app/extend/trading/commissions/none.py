"""Zero commission trading model snippet.

Description:
    Implements None commission model conforming to StrategyQuant
    SQ.Trading.Commissions.None. Returns zero commission on order open and close.

Purpose:
    FEAT-TRADING-COMMISSIONS: Port None commission method from StrategyQuant.

Key Capabilities:
    - FR-COMMISSIONS-NONE: Return 0.0 commission unconditionally on trade open/close.

Python API Usage:
    from app.extend.trading.commissions.none import NoneCommission
    comm = NoneCommission()
    fee = comm.computeCommissionsOnOpen(order)

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py -k test_none_commission
"""

from __future__ import annotations

import logging
from typing import Any, override

from app.extend.trading.commissions.base import (
    CommissionsMethod,
    CommissionsMethodsList,
)

logger = logging.getLogger(__name__)


class NoneCommission(CommissionsMethod):
    """Zero commission method matching StrategyQuant Commissions/None.java."""

    name: str = "None"
    display: str = "No commissions"

    def __init__(self) -> None:
        super().__init__()
        logger.debug("FR-COMMISSIONS-NONE: initialized None commission method")

    @override
    def computeCommissionsOnOpen(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on open (always 0.0)."""
        _ = (order, tickSize, pointValue)
        logger.debug("FR-COMMISSIONS-NONE: computeCommissionsOnOpen=0.0")
        return 0.0

    @override
    def computeCommissionsOnClose(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on close (always 0.0)."""
        _ = (order, tickSize, pointValue)
        logger.debug("FR-COMMISSIONS-NONE: computeCommissionsOnClose=0.0")
        return 0.0


NoneMethod = NoneCommission

CommissionsMethodsList.register("None", NoneCommission)
CommissionsMethodsList.register("NoneCommission", NoneCommission)

__all__ = [
    "NoneCommission",
    "NoneMethod",
]
