"""Profit Target strategy exit method.

Description:
    Evaluates and calculates profit target limit exit prices for open and
    pending orders with pip distance clamping and direction orientation,
    matching StrategyQuant's SQ.ExitMethods.ProfitTarget snippet.

Purpose:
    FEAT-EXIT-METHODS: StrategyQuant donor-faithful exit methods.

Key Capabilities:
    - FR-exit-methods-target: Profit target price computation and clamping.

Python API Usage:
    from app.extend.exit_methods.profit_target import ProfitTarget
    pt = ProfitTarget(profit_target=0.0050)
    target_price = pt.compute_value(direction=1, price=1.1000)

CLI Usage:
    python -m app.cli exit-method pt --target 0.0050
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.exit_methods.base import ExitMethod, ExitType, correct_sl_pt
from app.workspace.trading.exits import ProfitTarget as TradingProfitTarget

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ProfitTarget(ExitMethod):
    """Calculates and checks profit target levels for trading positions."""

    profit_target: float = 0.0
    name: str = "Profit Target"
    category: str = "ExitMethods"
    sort_order: int = 200
    for_engine: str = "*"
    exit_type: ExitType = ExitType.PROFIT_TARGET

    def __post_init__(self) -> None:
        """Validate target parameter is non-negative."""
        if self.profit_target < 0:
            raise ValueError("profit_target must be non-negative")

    @override
    def compute_value(
        self,
        direction: int,
        price: float,
        tick_size: float = 0.0001,
        min_pt_pips: int = 0,
        max_pt_pips: int = 0,
        **_kwargs: Any,
    ) -> float:
        """Compute the profit target price level for an order.

        Args:
            direction: 1 for Long, -1 for Short.
            price: Anchor price (fill or decision price).
            tick_size: Instrument tick size for pip conversion.
            min_pt_pips: Minimum allowed target distance in pips.
            max_pt_pips: Maximum allowed target distance in pips.
            **kwargs: Additional optional parameters.

        Returns:
            Clamped target price.
        """
        raw_pt = (
            price + self.profit_target if direction > 0 else price - self.profit_target
        )

        result = correct_sl_pt(
            entry_price=price,
            exit_price=raw_pt,
            direction=direction,
            tick_size=tick_size,
            is_stop_loss=False,
            min_pt_pips=min_pt_pips,
            max_pt_pips=max_pt_pips,
        )
        logger.debug(
            "FR-exit-methods-target: computed PT=%.5f (dir=%d, anchor=%.5f)",
            result,
            direction,
            price,
        )
        return result

    def should_exit(
        self, current_price: float, direction: int, target_price: float
    ) -> bool:
        """Determine if current market price has reached the profit target.

        Args:
            current_price: Current market price.
            direction: 1 for Long, -1 for Short.
            target_price: Profit target price.

        Returns:
            True if profit target reached, False otherwise.
        """
        if direction > 0:
            return current_price >= target_price
        return current_price <= target_price

    @override
    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        """Evaluate profit target computation or trigger."""
        target_args_count = 2
        if len(args) == target_args_count and isinstance(args[0], int):
            return self.compute_value(args[0], float(args[1]), **kwargs)
        return self.should_exit(*args, **kwargs)

    def to_policy(self, price: float) -> TradingProfitTarget:
        """Convert to trading execution policy with explicit price."""
        return TradingProfitTarget(price=price)
