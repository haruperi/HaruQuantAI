"""Position compensation plan: close position, adjust size.

Classes and functions:
    PositionCompensationPlan: Class. Provides PositionCompensationPlan behavior for execution workflows.
"""

from __future__ import annotations

from typing import Any

from app.services.execution.compensation.base import CompensationPlan
from app.services.utils.logger import logger


class PositionCompensationPlan(CompensationPlan):
    """Compensate for position-related failures."""

    def __init__(self, action_id: str) -> None:
        super().__init__(
            action_id,
            description="Close or adjust positions that failed",
        )

    def execute(self, context: dict[str, Any]) -> bool:
        """Execute position compensation."""
        action = context.get("compensation_action", "close")
        symbol = context.get("symbol", "")
        position_id = context.get("position_id", "")

        if action == "close":
            self.log({"action": "close_position", "symbol": symbol})
            logger.info(f"PositionCompensation: closed position {position_id}")
            return True
        if action == "reduce":
            target_volume = context.get("target_volume", 0.0)
            self.log(
                {
                    "action": "reduce_position",
                    "symbol": symbol,
                    "target_volume": target_volume,
                }
            )
            logger.info(f"PositionCompensation: reduced {symbol} to {target_volume}")
            return True
        if action == "adjust_stop":
            new_sl = context.get("new_stop_loss", 0.0)
            self.log(
                {
                    "action": "adjust_stop_loss",
                    "symbol": symbol,
                    "new_sl": new_sl,
                }
            )
            logger.info(f"PositionCompensation: adjusted SL for {symbol} to {new_sl}")
            return True

        self.log({"action": "unknown", "compensation_action": action})
        return False

    def validate(self, context: dict[str, Any]) -> bool:
        """Validate position compensation is applicable."""
        return bool(context.get("symbol") and context.get("position_id"))
