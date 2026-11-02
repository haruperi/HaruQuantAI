"""Trailing Stop strategy exit method.

Description:
    Ratchets the protective stop loss forward as price moves favorably,
    activating once market price surpasses a configured threshold and
    never loosening previous stops, matching StrategyQuant's
    SQ.ExitMethods.TrailingStop snippet.

Purpose:
    FEAT-EXIT-METHODS: StrategyQuant donor-faithful exit methods.

Key Capabilities:
    - FR-exit-methods-trailing: Dynamic ratchet trailing stop adjustment.

Python API Usage:
    from app.extend.exit_methods.trailing_stop import TrailingStop
    ts = TrailingStop(trailing_stop=0.0020, trailing_activation=0.0030)
    new_sl = ts.evaluate_trailing_stop(1.1000, 1.1040, 1)

CLI Usage:
    python -m app.cli exit-method ts --trailing 0.0020 --activation 0.0030
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.exit_methods.base import ExitMethod, ExitType
from app.workspace.trading.exits import TrailingStop as TradingTrailingStop

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TrailingStop(ExitMethod):
    """Ratchets stop loss forward with favorable price progression."""

    trailing_stop: float = 0.0
    trailing_activation: float = 0.0
    name: str = "Trailing Stop"
    category: str = "ExitMethods"
    sort_order: int = 400
    for_engine: str = "*,-SP,-SA"
    exit_type: ExitType = ExitType.TRAILING_STOP

    def __post_init__(self) -> None:
        """Validate distance parameters."""
        if self.trailing_stop < 0:
            raise ValueError("trailing_stop must be non-negative")
        if self.trailing_activation < 0:
            raise ValueError("trailing_activation must be non-negative")

    def evaluate_trailing_stop(
        self,
        open_price: float,
        current_price: float,
        direction: int,
        current_sl: float | None = None,
        min_distance: float = 0.0,
    ) -> float | None:
        """Calculate updated trailing stop price if activation threshold is met.

        Args:
            open_price: Fill price of the position.
            current_price: Current market bid (for long) or ask (for short).
            direction: 1 for Long, -1 for Short.
            current_sl: Currently assigned stop-loss price if any.
            min_distance: Minimum allowed distance from market in price units.

        Returns:
            New tightened stop loss price, or None if conditions not met.
        """
        if self.trailing_stop <= 0:
            return None

        if direction > 0:
            # Long position
            gain = current_price - open_price
            if gain >= self.trailing_activation:
                candidate_sl = current_price - self.trailing_stop
                is_tighter = current_sl is None or candidate_sl > current_sl
                is_valid = (current_price - candidate_sl) >= min_distance
                if is_tighter and is_valid:
                    logger.debug(
                        "FR-exit-methods-trailing: Long TS ratcheted to %.5f",
                        candidate_sl,
                    )
                    return candidate_sl
        else:
            # Short position
            gain = open_price - current_price
            if gain >= self.trailing_activation:
                candidate_sl = current_price + self.trailing_stop
                is_tighter = current_sl is None or candidate_sl < current_sl
                is_valid = (candidate_sl - current_price) >= min_distance
                if is_tighter and is_valid:
                    logger.debug(
                        "FR-exit-methods-trailing: Short TS ratcheted to %.5f",
                        candidate_sl,
                    )
                    return candidate_sl

        return None

    @override
    def evaluate(self, *args: Any, **kwargs: Any) -> float | None:
        """Evaluate trailing stop condition against position state."""
        return self.evaluate_trailing_stop(*args, **kwargs)

    @override
    def compute_value(
        self,
        direction: int,
        price: float,
        tick_size: float = 0.0001,
        **kwargs: Any,
    ) -> float:
        """Compute static value (requires dynamic position evaluation)."""
        raise NotImplementedError("TrailingStop requires dynamic position evaluation")

    def to_policy(self) -> TradingTrailingStop:
        """Convert to trading execution policy."""
        if self.trailing_stop <= 0:
            raise ValueError(
                "trailing_stop must be positive to create execution policy"
            )
        return TradingTrailingStop(
            distance=self.trailing_stop, activation=self.trailing_activation
        )
