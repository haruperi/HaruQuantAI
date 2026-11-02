"""Allow all trades risk management snippet.

Description:
    Allows all trading orders unconditionally without restrictions, matching
    StrategyQuant's SQ.RiskManagement.AllowAllTrades snippet.

Purpose:
    FEAT-RISK-MANAGEMENT: StrategyQuant donor-faithful risk management methods.

Key Capabilities:
    - FR-risk-management-allow-all: Unconditional order approval policy.

Python API Usage:
    from app.extend.risk_management.allow_all_trades import AllowAllTrades

    rm = AllowAllTrades()
    allowed = rm.verify_order(order=None, trader=None)

CLI Usage:
    python -m app.cli risk-management allow-all
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.risk_management.base import RiskManagementMethod

logger = get_logger(__name__)


@dataclass(frozen=False)
class AllowAllTrades(RiskManagementMethod):
    """Permits every trade unconditionally matching StrategyQuant AllowAllTrades."""

    name: str = "Allow all trades"
    display: str = "Allow all trades"
    help: str = "Every trade will be allowed."
    category: str = "RiskManagement"
    sort_order: int = 100

    @override
    def verify_order(
        self, order: Any = None, trader: Any = None, **kwargs: Any
    ) -> bool:
        """Verify order and permit it unconditionally.

        Args:
            order: The proposed order.
            trader: Optional trader reference.
            **kwargs: Extra parameters.

        Returns:
            Always True.
        """
        logger.debug(
            "FR-risk-management-allow-all: order allowed (trader=%s, order=%s)",
            trader,
            order,
        )
        return True

    @override
    def verifyOrder(self, trader: Any = None, order: Any = None) -> None:
        """Process donor Java verifyOrder contract as unconditional permit.

        Args:
            trader: Trader reference.
            order: Order reference.
        """
        logger.debug(
            "FR-risk-management-allow-all: verifyOrder no-op trader=%s",
            trader,
        )
