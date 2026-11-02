"""Move Stop Loss to Break Even strategy exit method.

Description:
    Moves the protective stop-loss to the trade entry price plus an optional
    pip offset once the market advances past an activation profit threshold,
    matching StrategyQuant's SQ.ExitMethods.MoveSL2BE snippet.

Purpose:
    FEAT-EXIT-METHODS: StrategyQuant donor-faithful exit methods.

Key Capabilities:
    - FR-exit-methods-breakeven: Dynamic breakeven stop loss adjustment.

Python API Usage:
    from app.extend.exit_methods.move_sl_2_be import MoveSL2BE
    sl2be = MoveSL2BE(move_sl_to_be=0.0020, sl_to_be_add_pips=2.0)
    new_sl = sl2be.evaluate_new_sl(1.1000, 1.1030, 1)

CLI Usage:
    python -m app.cli exit-method sl2be --activation 0.0020
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.exit_methods.base import ExitMethod, ExitType
from app.workspace.trading.exits import MoveSL2BE as TradingMoveSL2BE

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MoveSL2BE(ExitMethod):
    """Adjusts stop loss to break-even after favorable price move."""

    move_sl_to_be: float = 0.0
    sl_to_be_add_pips: float = 0.0
    name: str = "Move SL to BE"
    category: str = "ExitMethods"
    sort_order: int = 300
    for_engine: str = "*,-SP,-SA"
    exit_type: ExitType = ExitType.MOVE_SL_2_BE

    def __post_init__(self) -> None:
        """Validate distance parameters."""
        if self.move_sl_to_be < 0:
            raise ValueError("move_sl_to_be activation must be non-negative")
        if self.sl_to_be_add_pips < 0:
            raise ValueError("sl_to_be_add_pips must be non-negative")

    def evaluate_new_sl(
        self,
        open_price: float,
        current_price: float,
        direction: int,
        current_sl: float | None = None,
        *,
        min_distance: float = 0.0,
        tick_size: float = 0.0001,
    ) -> float | None:
        """Evaluate if position should move stop loss to breakeven.

        Args:
            open_price: Fill price of the position.
            current_price: Current market bid (for long) or ask (for short).
            direction: 1 for Long, -1 for Short.
            current_sl: Current stop-loss price if any.
            min_distance: Minimum allowed distance from market in price units.
            tick_size: Instrument tick size for pip conversion.

        Returns:
            New adjusted stop loss price, or None if conditions not met.
        """
        if self.move_sl_to_be <= 0:
            return None

        offset_dist = self.sl_to_be_add_pips * tick_size

        if direction > 0:
            # Long position
            gain = current_price - open_price
            if gain >= self.move_sl_to_be:
                candidate_sl = open_price + offset_dist
                is_tighter = current_sl is None or current_sl < candidate_sl
                is_safe = abs(current_price - candidate_sl) >= min_distance
                if current_price >= candidate_sl and is_tighter and is_safe:
                    logger.debug(
                        "FR-exit-methods-breakeven: Long SL2BE moving to %.5f",
                        candidate_sl,
                    )
                    return candidate_sl
        else:
            # Short position
            gain = open_price - current_price
            if gain >= self.move_sl_to_be:
                candidate_sl = open_price - offset_dist
                is_tighter = current_sl is None or current_sl > candidate_sl
                is_safe = abs(candidate_sl - current_price) >= min_distance
                if current_price <= candidate_sl and is_tighter and is_safe:
                    logger.debug(
                        "FR-exit-methods-breakeven: Short SL2BE moving to %.5f",
                        candidate_sl,
                    )
                    return candidate_sl

        return None

    @override
    def evaluate(self, *args: Any, **kwargs: Any) -> float | None:
        """Evaluate breakeven condition against position state."""
        return self.evaluate_new_sl(*args, **kwargs)

    @override
    def compute_value(
        self,
        direction: int,
        price: float,
        tick_size: float = 0.0001,
        **kwargs: Any,
    ) -> float:
        """Compute static value (requires dynamic position evaluation)."""
        raise NotImplementedError("MoveSL2BE requires dynamic position evaluation")

    def to_policy(self) -> TradingMoveSL2BE:
        """Convert to trading execution policy."""
        return TradingMoveSL2BE(
            activation=self.move_sl_to_be, offset=self.sl_to_be_add_pips
        )
