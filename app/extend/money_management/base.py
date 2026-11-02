"""Contract for custom position sizing and money management snippets.

Description:
    Defines the BasePositionSizer abstract contract for StrategyQuant-compatible
    money management and position sizing calculation snippets, along with common
    rounding, clamping, and evaluation routines.
Purpose:
    FEAT-MONEY-MANAGEMENT: Provide the canonical MoneyManagement base contract.
Key Capabilities:
    - FR-MM-SIZER-CONTRACT: Declare compute_size and compute_trade_size.
    - FR-MM-ROUNDING: Precision truncation and step-based rounding routines.
Python API Usage:
    from app.extend.money_management.base import (
        BasePositionSizer,
        clamp_lots,
        round_down,
    )
CLI Usage:
    uv run pytest tests/extend/test_money_management_catalog.py --no-cov
"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


def round_down(value: float, decimals: int) -> float:
    """Truncate/floor positive lot size to the requested decimal places.

    Args:
        value: Raw volume or lot size.
        decimals: Decimal places to preserve.

    Returns:
        Floored float value rounded down to decimals.
    """
    if not math.isfinite(value) or value <= 0.0:
        return 0.0
    factor = float(10 ** max(decimals, 0))
    return math.floor(value * factor + 1e-9) / factor


def round_lots(value: float, size_step: float = 0.0, decimals: int = 2) -> float:
    """Round lot size according to broker step size and decimal precision.

    Matches donor StrategyQuant round(tradeSize, sizeStep, decimals) logic.

    Args:
        value: Raw trade size.
        size_step: Minimum lot increment / step size.
        decimals: Decimal precision limit.

    Returns:
        Step-aligned and precision-rounded trade size.
    """
    if not math.isfinite(value) or value <= 0.0:
        return 0.0
    d = value
    if size_step > 0.0:
        d = math.floor(d / size_step) * size_step
    return round(d, max(decimals, 0))


def clamp_lots(
    computed: float,
    *,
    decimals: int,
    lots_if_no_mm: float,
    max_lots: float = 0.0,
    min_lots: float = 0.0,
) -> float:
    """Apply donor rounding, minimum fallback, and maximum lot cap.

    Args:
        computed: Raw computed lots.
        decimals: Decimal places to round down to.
        lots_if_no_mm: Fallback lots when computed size is below min_lots.
        max_lots: Upper limit cap for lots.
        min_lots: Minimum threshold to consider valid sizing.

    Returns:
        Bounded and rounded lot size.
    """
    rounded = round_down(computed, decimals)
    if rounded <= min_lots:
        rounded = round_down(max(lots_if_no_mm, 0.0), decimals)
    if max_lots > 0.0 and rounded > max_lots:
        rounded = round_down(max_lots, decimals)
    return rounded


class BasePositionSizer(ABC):
    """Contract for custom trade volume calculation and money management."""

    name: str = "BasePositionSizer"
    category: str = "MoneyManagement"
    display: str = ""
    help_text: str = ""
    description: str = ""
    sort_order: int = 100
    for_engine: str = "*,-SP,-SA"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(self) -> None:
        self.initial_capital: float = 10000.0
        self.weight: float = 1.0
        self.max_pos: float = 1.0

    def set_weight(self, weight: float) -> None:
        """Set portfolio/strategy weighting multiplier."""
        self.weight = weight

    def set_max_open_positions(self, max_pos: float) -> None:
        """Set maximum allowable concurrent positions."""
        self.max_pos = max_pos

    def set_initial_capital(self, capital: float) -> None:
        """Set account initial capital."""
        self.initial_capital = capital

    @abstractmethod
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Calculate lots from account equity and stop distance."""

    def compute_trade_size(  # noqa: PLR0917
        self,
        strategy: Any = None,
        symbol: str = "",
        order_type: int = 0,
        price: float = 0.0,
        sl: float = 0.0,
        tick_size: float = 0.0001,
        point_value: float = 10.0,
        size_step: float = 0.01,
    ) -> float:
        """Donor StrategyQuant computeTradeSize parity method.

        Default implementation bridges to compute_size using available price/sl info.
        """
        _ = (strategy, symbol, order_type, size_step)
        stop_dist = (
            abs(price - sl) / tick_size
            if (price > 0.0 and sl > 0.0 and tick_size > 0.0)
            else 0.0
        )
        equity = 10000.0
        if strategy is not None and hasattr(strategy, "get_account_equity"):
            equity = float(strategy.get_account_equity())
        elif strategy is not None and hasattr(strategy, "getAccountEquity"):
            equity = float(strategy.getAccountEquity())
        return self.compute_size(equity, stop_dist, point_value)


__all__ = [
    "BasePositionSizer",
    "clamp_lots",
    "round_down",
    "round_lots",
]
