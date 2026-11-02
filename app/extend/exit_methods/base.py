"""Base class, enumerations, and price correction utilities for exit methods.

Description:
    Provides the core ExitMethod abstract base class, ExitType enumeration,
    and the donor-faithful correct_sl_pt price clamping algorithm matching
    StrategyQuant's com.strategyquant.tradinglib.ExitMethod.

Purpose:
    FEAT-EXIT-METHODS: StrategyQuant donor-faithful exit methods.

Key Capabilities:
    - FR-exit-methods-base: Base exit method contract and SL/PT correction utilities.

Python API Usage:
    from app.extend.exit_methods.base import ExitMethod, correct_sl_pt
    clamped = correct_sl_pt(1.1, 1.09, 1, 0.0001, is_stop_loss=True)

CLI Usage:
    python -c "from app.extend.exit_methods.base import ExitMethod; print(ExitMethod)"
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class ExitType(IntEnum):
    """Exit method types matching StrategyQuant ExitTypes constants."""

    NONE = 0
    EXIT_AFTER_BARS = 1
    MOVE_SL_2_BE = 2
    PROFIT_TARGET = 3
    STOP_LOSS = 4
    TRAILING_STOP = 5


def correct_sl_pt(
    entry_price: float,
    exit_price: float,
    direction: int,
    tick_size: float,
    *,
    is_stop_loss: bool,
    min_sl_pips: int = 0,
    max_sl_pips: int = 0,
    min_pt_pips: int = 0,
    max_pt_pips: int = 0,
) -> float:
    """Clamp StopLoss or ProfitTarget exit price within configured pip bounds.

    Faithful to StrategyQuant ExitMethod.correctSLPT implementation.

    Args:
        entry_price: The fill or anchor price of the order.
        exit_price: The raw proposed exit price.
        direction: 1 for Long, -1 for Short.
        tick_size: Instrument tick size (point size).
        is_stop_loss: True if evaluating StopLoss, False for ProfitTarget.
        min_sl_pips: Minimum allowed distance for StopLoss in pips/ticks.
        max_sl_pips: Maximum allowed distance for StopLoss in pips/ticks.
        min_pt_pips: Minimum allowed distance for ProfitTarget in pips/ticks.
        max_pt_pips: Maximum allowed distance for ProfitTarget in pips/ticks.

    Returns:
        Clamped and bounded exit price.
    """
    is_favorable = (direction > 0 and not is_stop_loss) or (
        direction < 0 and is_stop_loss
    )
    n2 = 1 if is_favorable else -1
    result_price = exit_price

    if is_stop_loss:
        if min_sl_pips > 0:
            limit = entry_price + (n2 * min_sl_pips) * tick_size
            result_price = (
                max(limit, result_price) if n2 > 0 else min(limit, result_price)
            )
        if max_sl_pips > 0:
            limit = entry_price + (n2 * max_sl_pips) * tick_size
            result_price = (
                min(limit, result_price) if n2 > 0 else max(limit, result_price)
            )
    else:
        if min_pt_pips > 0:
            limit = entry_price + (n2 * min_pt_pips) * tick_size
            result_price = (
                max(limit, result_price) if n2 > 0 else min(limit, result_price)
            )
        if max_pt_pips > 0:
            limit = entry_price + (n2 * max_pt_pips) * tick_size
            result_price = (
                min(limit, result_price) if n2 > 0 else max(limit, result_price)
            )

    logger.debug(
        "FR-exit-methods-base: correct_sl_pt raw=%.5f clamped=%.5f (is_sl=%s)",
        exit_price,
        result_price,
        is_stop_loss,
    )
    return result_price


class ExitMethod(ABC):
    """Abstract base class for all StrategyQuant-compatible exit methods."""

    name: str = "ExitMethod"
    category: str = "ExitMethods"
    sort_order: int = 100
    for_engine: str = "*"
    exit_type: ExitType = ExitType.NONE

    @abstractmethod
    def compute_value(
        self,
        direction: int,
        price: float,
        tick_size: float = 0.0001,
        **kwargs: Any,
    ) -> float:
        """Compute the exit price level for an order.

        Args:
            direction: 1 for Long, -1 for Short.
            price: Anchor or reference price (e.g. fill price or decision price).
            tick_size: Instrument tick size for alignment.
            **kwargs: Additional evaluation parameters (e.g. pips constraints).

        Returns:
            Calculated exit price.
        """

    @abstractmethod
    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        """Evaluate exit condition against current position state."""
