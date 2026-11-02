"""Stockpicker commission model snippet.

Description:
    Implements tiered equity/stockpicker commission model conforming to StrategyQuant
    SQ.Trading.Commissions.Stockpicker. Supports per-share, per-order,
    and percent-of-equity rates with customizable minimum and maximum bounds.

Purpose:
    FEAT-TRADING-COMMISSIONS: Port Stockpicker commission method from StrategyQuant.

Key Capabilities:
    - FR-COMMISSIONS-STOCKPICKER: Compute multi-tier stockpicker commission with caps.

Python API Usage:
    from app.extend.trading.commissions.stockpicker import StockpickerCommission
    comm = StockpickerCommission(Commission=0.0035, CommissionType="share")
    fee = comm.computeCommissionsOnOpen(order)

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py -k test_stockpicker
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


class Stockpicker(CommissionsMethod):
    """Stockpicker tiered commission method matching SQ Stockpicker.java."""

    name: str = "Stockpicker"
    display: str = "#Commission# / #CommissionType#"

    def __init__(  # noqa: PLR0917
        self,
        Commission: float = 0.0035,  # noqa: N803
        CommissionType: str = "share",  # noqa: N803
        MinPerOrder: float = 0.35,  # noqa: N803
        MinPerOrderType: str = "money",  # noqa: N803
        MaxPerOrder: float = 1.0,  # noqa: N803
        MaxPerOrderType: str = "equity",  # noqa: N803
        *,
        min_commission: float | None = None,
        max_commission_pct: float | None = None,
        per_share_commission: float | None = None,
        percentage_commission: float | None = None,
    ) -> None:
        super().__init__()
        self.Commission: float = (
            per_share_commission
            if per_share_commission is not None
            else (
                percentage_commission
                if percentage_commission is not None and percentage_commission > 0.0
                else Commission
            )
        )
        self.CommissionType: str = (
            "equity"
            if percentage_commission is not None and percentage_commission > 0.0
            else ("share" if per_share_commission is not None else CommissionType)
        )
        self.MinPerOrder: float = (
            min_commission if min_commission is not None else MinPerOrder
        )
        self.MinPerOrderType: str = (
            "money" if min_commission is not None else MinPerOrderType
        )
        self.MaxPerOrder: float = (
            max_commission_pct if max_commission_pct is not None else MaxPerOrder
        )
        self.MaxPerOrderType: str = (
            "equity" if max_commission_pct is not None else MaxPerOrderType
        )
        logger.debug(
            "FR-COMMISSIONS-STOCKPICKER: init Commission=%f type=%s min=%f max=%f",
            self.Commission,
            self.CommissionType,
            self.MinPerOrder,
            self.MaxPerOrder,
        )

    @property
    def min_commission(self) -> float:
        """Alias for MinPerOrder."""
        return self.MinPerOrder

    @property
    def max_commission_pct(self) -> float:
        """Alias for MaxPerOrder (when percent-based)."""
        return self.MaxPerOrder

    @property
    def per_share_commission(self) -> float:
        """Alias for Commission (when per-share)."""
        return self.Commission

    @property
    def percentage_commission(self) -> float:
        """Alias for Commission (when percent-based)."""
        return self.Commission if self.CommissionType == "equity" else 0.0

    def _calculate_base_fee(self, size: float, purchased_equity: float) -> float:
        """Calculate base commission without bounding."""
        if self.CommissionType == "share":
            return self.Commission * size
        if self.CommissionType == "order":
            return self.Commission
        if self.CommissionType == "equity":
            return (self.Commission / 100.0) * purchased_equity
        raise ValueError(f"Invalid commission type: {self.CommissionType}")

    def _calculate_limit(
        self,
        value: float,
        limit_type: str,
        purchased_equity: float,
        label: str,
    ) -> float:
        """Calculate dollar boundary for min or max limit."""
        if limit_type == "money":
            return value
        if limit_type == "equity":
            return (value / 100.0) * purchased_equity
        raise ValueError(f"Invalid {label} type: {limit_type}")

    @override
    def computeCommissionsOnOpen(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute stockpicker commission on open with min/max caps."""
        _ = (tickSize, pointValue)
        size = get_order_size(order)
        open_price = get_order_open_price(order)
        if size <= 0.0 or open_price <= 0.0:
            logger.debug(
                "FR-COMMISSIONS-STOCKPICKER: non-positive size or price, fee=0.0"
            )
            return 0.0

        purchased_equity = size * open_price
        commission = self._calculate_base_fee(size, purchased_equity)
        min_fee = self._calculate_limit(
            self.MinPerOrder, self.MinPerOrderType, purchased_equity, "min per order"
        )
        max_fee = self._calculate_limit(
            self.MaxPerOrder, self.MaxPerOrderType, purchased_equity, "max per order"
        )

        if min_fee > 0.0 and commission < min_fee:
            commission = min_fee
        if max_fee > 0.0 and commission > max_fee:
            commission = max_fee

        logger.debug(
            "FR-COMMISSIONS-STOCKPICKER: computed open commission=%f",
            commission,
        )
        return commission

    @override
    def computeCommissionsOnClose(
        self,
        order: Any,
        tickSize: float = 0.0001,
        pointValue: float = 1.0,
    ) -> float:
        """Compute commission on close (symmetrically evaluates open rule)."""
        return self.computeCommissionsOnOpen(
            order, tickSize=tickSize, pointValue=pointValue
        )


StockpickerCommission = Stockpicker

CommissionsMethodsList.register("Stockpicker", Stockpicker)
CommissionsMethodsList.register("StockpickerCommission", Stockpicker)

__all__ = [
    "Stockpicker",
    "StockpickerCommission",
]
