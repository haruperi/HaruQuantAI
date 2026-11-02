"""Stop Loss strategy exit method.

Description:
    Evaluates and calculates protective stop loss exit prices for open and
    pending orders with pip distance clamping, tick grid snapping, and
    direction orientation, matching StrategyQuant's SQ.ExitMethods.StopLoss snippet.

Purpose:
    FEAT-EXIT-METHODS: StrategyQuant donor-faithful exit methods.

Key Capabilities:
    - FR-exit-methods-stop: Stop loss price computation, clamping, and tick snapping.

Python API Usage:
    from app.extend.exit_methods.stop_loss import StopLoss
    sl = StopLoss(stop_loss=0.0030)
    stop_price = sl.compute_value(direction=1, price=1.1000)

CLI Usage:
    python -m app.cli exit-method sl --stop 0.0030
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.exit_methods.base import ExitMethod, ExitType, correct_sl_pt
from app.workspace.trading.exits import StopLoss as TradingStopLoss

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class StopLoss(ExitMethod):
    """Calculates and checks protective stop loss levels for trading positions."""

    stop_loss: float = 0.0
    strategy_trails_this_stop: bool = False
    name: str = "Stop Loss"
    category: str = "ExitMethods"
    sort_order: int = 100
    for_engine: str = "*"
    exit_type: ExitType = ExitType.STOP_LOSS

    def __post_init__(self) -> None:
        """Validate stop loss parameter is non-negative."""
        if self.stop_loss < 0:
            raise ValueError("stop_loss must be non-negative")

    @override
    def compute_value(
        self,
        direction: int,
        price: float,
        tick_size: float = 0.0001,
        min_sl_pips: int = 0,
        max_sl_pips: int = 0,
        **_kwargs: Any,
    ) -> float:
        """Compute the protective stop loss price level for an order.

        Args:
            direction: 1 for Long, -1 for Short.
            price: Anchor price (fill or decision price).
            tick_size: Instrument tick size for pip conversion.
            min_sl_pips: Minimum allowed stop distance in pips.
            max_sl_pips: Maximum allowed stop distance in pips.
            **kwargs: Additional optional parameters.

        Returns:
            Clamped stop loss price.
        """
        raw_sl = price - self.stop_loss if direction > 0 else price + self.stop_loss

        result = correct_sl_pt(
            entry_price=price,
            exit_price=raw_sl,
            direction=direction,
            tick_size=tick_size,
            is_stop_loss=True,
            min_sl_pips=min_sl_pips,
            max_sl_pips=max_sl_pips,
        )
        logger.debug(
            "FR-exit-methods-stop: computed SL=%.5f (dir=%d, anchor=%.5f)",
            result,
            direction,
            price,
        )
        return result

    @staticmethod
    def fix_initial_stop_distance(
        distance: float,
        tick_step: float,
        is_long: bool,
        rounds_ties_up: bool = False,
    ) -> float:
        """Snap initial stop-loss distance to tick step grid with tie handling.

        Matches StrategyQuant fixInitialStopDistance logic.

        Args:
            distance: Raw stop distance.
            tick_step: Instrument tick step.
            is_long: True for long position, False for short.
            rounds_ties_up: True if engine rounds ties up in price.

        Returns:
            Tick-aligned distance.
        """
        if tick_step <= 0:
            return distance

        if not rounds_ties_up or not is_long:
            return round(round(distance / tick_step) * tick_step, 6)

        ticks = math.ceil((distance / tick_step) - 0.5)
        return round(ticks * tick_step, 6)

    def should_exit(
        self, current_price: float, direction: int, stop_price: float
    ) -> bool:
        """Determine if current market price has hit the stop loss.

        Args:
            current_price: Current market price.
            direction: 1 for Long, -1 for Short.
            stop_price: Stop loss price.

        Returns:
            True if stop loss breached, False otherwise.
        """
        if direction > 0:
            return current_price <= stop_price
        return current_price >= stop_price

    @override
    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        """Evaluate stop loss computation or trigger."""
        target_args_count = 2
        if len(args) == target_args_count and isinstance(args[0], int):
            return self.compute_value(args[0], float(args[1]), **kwargs)
        return self.should_exit(*args, **kwargs)

    def to_policy(self, price: float) -> TradingStopLoss:
        """Convert to trading execution policy with explicit price."""
        return TradingStopLoss(price=price)
