"""Concrete donor-faithful Trading commission and scaling models.

Description:
    Implements the 6 StrategyQuant Trading extension cohort classes:
    NoneCommission (Commissions/None.java), PercentageBasedCommission
    (Commissions/PercentageBased.java), PerTradeCommission
    (Commissions/PerTrade.java), SizeBasedCommission (Commissions/SizeBased.java),
    StockpickerCommission (Commissions/Stockpicker.java), and NoScaling
    (Scaling/NoScaling.java).
Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: Complete the 6-class Trading extension
    cohort under app/include/trading.
Key Capabilities:
    - FR-trading-commission-compute: Calculate round-turn trade commissions and
      scaling adjustments across fixed, percentage, per-lot, and stockpicker
      fee structures.
Python API Usage:
    from app.include.trading.commissions import PercentageBasedCommission
CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import override

logger = logging.getLogger(__name__)


class BaseCommissionModel(ABC):
    """Contract for round-turn or per-order trade commission calculation."""

    name: str = "BaseCommissionModel"
    category: str = "Trading.Commissions"

    @abstractmethod
    def compute_commission(
        self,
        *,
        size: float,
        open_price: float,
        close_price: float | None = None,
        point_value: float = 1.0,
    ) -> float:
        """Compute total trade commission in account currency."""


@dataclass(frozen=True, slots=True)
class NoneCommission(BaseCommissionModel):
    """Zero commission model (Trading/Commissions/None.java)."""

    name: str = "None"

    @override
    def compute_commission(
        self,
        *,
        size: float,
        open_price: float,
        close_price: float | None = None,
        point_value: float = 1.0,
    ) -> float:
        """Return 0.0 commission for any order."""
        _ = (size, open_price, close_price, point_value)
        logger.debug("FR-trading-commission-compute: None=0.0")
        return 0.0


@dataclass(frozen=True, slots=True)
class PerTradeCommission(BaseCommissionModel):
    """Flat fee per trade regardless of size (Trading/Commissions/PerTrade.java)."""

    commission: float = 5.0
    name: str = "PerTrade"

    @override
    def compute_commission(
        self,
        *,
        size: float,
        open_price: float,
        close_price: float | None = None,
        point_value: float = 1.0,
    ) -> float:
        """Return fixed commission per trade when size > 0."""
        _ = (open_price, close_price, point_value)
        fee = max(self.commission, 0.0) if size > 0.0 else 0.0
        logger.debug("FR-trading-commission-compute: PerTrade=%f", fee)
        return round(fee, 6)


@dataclass(frozen=True, slots=True)
class SizeBasedCommission(BaseCommissionModel):
    """Commission proportional to order lot/share size (SizeBased.java)."""

    commission_per_lot: float = 7.0
    name: str = "SizeBased"

    @override
    def compute_commission(
        self,
        *,
        size: float,
        open_price: float,
        close_price: float | None = None,
        point_value: float = 1.0,
    ) -> float:
        """Return size * commission_per_lot."""
        _ = (open_price, close_price, point_value)
        fee = max(size, 0.0) * max(self.commission_per_lot, 0.0)
        logger.debug("FR-trading-commission-compute: SizeBased=%f", fee)
        return round(fee, 6)


@dataclass(frozen=True, slots=True)
class PercentageBasedCommission(BaseCommissionModel):
    """Percentage of trade notional value (PercentageBased.java)."""

    commission_pct: float = 0.1
    name: str = "PercentageBased"

    @override
    def compute_commission(
        self,
        *,
        size: float,
        open_price: float,
        close_price: float | None = None,
        point_value: float = 1.0,
    ) -> float:
        """Return commission as percentage of entry (+ optional exit) notional."""
        if size <= 0.0 or self.commission_pct <= 0.0:
            return 0.0
        rate = self.commission_pct / 100.0
        entry_notional = size * max(open_price, 0.0) * max(point_value, 0.0)
        exit_notional = (
            size * max(close_price, 0.0) * max(point_value, 0.0)
            if close_price is not None
            else entry_notional
        )
        fee = (entry_notional + exit_notional) * (rate / 2.0)
        logger.debug("FR-trading-commission-compute: PercentageBased=%f", fee)
        return round(fee, 6)


@dataclass(frozen=True, slots=True)
class StockpickerCommission(BaseCommissionModel):
    """Tiered equity/stockpicker commission with min/max bounds (Stockpicker.java)."""

    min_commission: float = 1.0
    max_commission_pct: float = 1.0
    per_share_commission: float = 0.005
    percentage_commission: float = 0.0
    name: str = "Stockpicker"

    @override
    def compute_commission(
        self,
        *,
        size: float,
        open_price: float,
        close_price: float | None = None,
        point_value: float = 1.0,
    ) -> float:
        """Compute round-turn stockpicker commission with min and max-pct caps."""
        if size <= 0.0 or open_price <= 0.0:
            return 0.0
        exit_p = (
            close_price if close_price is not None and close_price > 0.0 else open_price
        )

        def _leg_fee(price: float) -> float:
            notional = size * price * max(point_value, 1.0)
            raw = size * max(self.per_share_commission, 0.0) + notional * (
                max(self.percentage_commission, 0.0) / 100.0
            )
            fee = max(raw, self.min_commission, 0.0)
            if self.max_commission_pct > 0.0:
                cap = notional * (self.max_commission_pct / 100.0)
                if cap > 0.0:
                    fee = min(fee, cap)
            return fee

        total = _leg_fee(open_price) + _leg_fee(exit_p)
        logger.debug("FR-trading-commission-compute: Stockpicker=%f", total)
        return round(total, 6)


@dataclass(frozen=True, slots=True)
class NoScaling:
    """Pass-through scaling strategy (Trading/Scaling/NoScaling.java)."""

    name: str = "NoScaling"
    category: str = "Trading.Scaling"

    def scale_size(self, requested_size: float) -> float:
        """Return requested position size without scaling adjustments."""
        result = max(requested_size, 0.0)
        logger.debug("FR-trading-commission-compute: NoScaling=%f", result)
        return result


__all__ = [
    "BaseCommissionModel",
    "NoScaling",
    "NoneCommission",
    "PerTradeCommission",
    "PercentageBasedCommission",
    "SizeBasedCommission",
    "StockpickerCommission",
]
