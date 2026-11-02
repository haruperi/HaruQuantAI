"""Base class and contracts for risk management methods.

Description:
    Provides the core RiskManagementMethod abstract base class matching
    StrategyQuant's com.strategyquant.tradinglib.RiskManagementMethod contract,
    supporting pre-trade validation, order verification, and parameter grid metadata.

Purpose:
    FEAT-RISK-MANAGEMENT: StrategyQuant donor-faithful risk management methods.

Key Capabilities:
    - FR-risk-management-base: Base risk management contract and order verification.

Python API Usage:
    from app.extend.risk_management.base import RiskManagementMethod

    class CustomRiskMethod(RiskManagementMethod):
        def verify_order(self, order=None, trader=None, **kwargs) -> bool:
            return True

CLI Usage:
    python -m app.cli risk-management base
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=False)
class RiskManagementMethod(ABC):
    """Abstract base class for all StrategyQuant-compatible risk management methods."""

    name: str = "RiskManagementMethod"
    display: str = "Risk Management Method"
    help: str = ""
    category: str = "RiskManagement"
    equity: float = 0.0
    decimals: int = 2
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def set_name(self, name: str) -> None:
        """Set the display name of the method."""
        self.name = name

    def get_equity(self) -> float:
        """Return the current reference equity matching donor getEquity()."""
        return self.equity

    def get_decimals(self) -> int:
        """Return the price decimals matching donor getDecimals()."""
        return self.decimals

    @abstractmethod
    def verify_order(
        self, order: Any = None, trader: Any = None, **kwargs: Any
    ) -> bool:
        """Verify whether an order is allowed by this risk management method.

        Args:
            order: The proposed order or OrderRequest.
            trader: Optional trader, account, or context reference.
            **kwargs: Additional evaluation context.

        Returns:
            True if the order is approved/permitted, False otherwise.
        """

    def verifyOrder(self, trader: Any = None, order: Any = None) -> None:  # noqa: N802
        """Process donor Java verification contract against verify_order.

        Args:
            trader: Trader reference.
            order: Order reference.

        Raises:
            ValueError: If the order is rejected by verify_order.
        """
        allowed = self.verify_order(order=order, trader=trader)
        if not allowed:
            logger.warning(
                "FR-risk-management-base: order rejected by %s for trader=%s order=%s",
                self.name,
                trader,
                order,
            )
            raise ValueError(f"Order rejected by risk management method: {self.name}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize risk management method configuration to a dictionary."""
        return {
            "name": self.name,
            "display": self.display,
            "help": self.help,
            "category": self.category,
            "equity": self.equity,
            "decimals": self.decimals,
            "parameters": dict(self.parameters),
        }
