"""Exit after bars strategy exit method.

Description:
    Automatically closes open trades after a configurable number of bars
    have completed while the position is active, matching StrategyQuant's
    SQ.ExitMethods.ExitAfterBars snippet.

Purpose:
    FEAT-EXIT-METHODS: StrategyQuant donor-faithful exit methods.

Key Capabilities:
    - FR-exit-methods-bars: Time-based bar count exit trigger.

Python API Usage:
    from app.extend.exit_methods.exit_after_bars import ExitAfterBars
    exit_method = ExitAfterBars(exit_after_bars=10)
    should_close = exit_method.should_exit(bars_in_trade=10)

CLI Usage:
    python -m app.cli exit-method bars --bars 10
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.exit_methods.base import ExitMethod, ExitType
from app.workspace.trading.exits import ExitAfterBars as TradingExitAfterBars

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ExitAfterBars(ExitMethod):
    """Automatically closes a trade after a configured number of bars in trade."""

    exit_after_bars: int = 0
    name: str = "Exit After Bars"
    category: str = "ExitMethods"
    sort_order: int = 500
    for_engine: str = "*"
    exit_type: ExitType = ExitType.EXIT_AFTER_BARS

    def __post_init__(self) -> None:
        """Validate bar count is non-negative."""
        if self.exit_after_bars < 0:
            raise ValueError("exit_after_bars must be non-negative")

    def should_exit(self, bars_in_trade: int) -> bool:
        """Determine whether order has reached or exceeded bar threshold.

        Args:
            bars_in_trade: Number of bars the trade has been open.

        Returns:
            True if position should close, False otherwise.
        """
        if self.exit_after_bars <= 0:
            return False

        exceeded = bars_in_trade >= self.exit_after_bars
        if exceeded:
            logger.debug(
                "FR-exit-methods-bars: bars=%d >= threshold=%d, triggering exit",
                bars_in_trade,
                self.exit_after_bars,
            )
        return exceeded

    @override
    def evaluate(self, *args: Any, **kwargs: Any) -> bool:
        """Evaluate bar lifetime against position state."""
        bars = int(args[0]) if args else int(kwargs.get("bars_in_trade", 0))
        return self.should_exit(bars)

    @override
    def compute_value(
        self,
        direction: int,
        price: float,
        tick_size: float = 0.0001,
        **kwargs: Any,
    ) -> float:
        """Compute price level (not applicable for bar-count exit)."""
        raise NotImplementedError("ExitAfterBars does not produce a price level")

    def to_policy(self) -> TradingExitAfterBars:
        """Convert to trading execution policy."""
        return TradingExitAfterBars(bars=self.exit_after_bars)
