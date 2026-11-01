"""Full position close size sentinel formula definition.

Description:
    Implements the FullPosition formula evaluation helper used within strategy
    trade execution and Builder formulas. In the observed engine semantics,
    evaluating FullPosition returns numeric 0.0 as a close-size sentinel
    indicating that the entire open volume of the position should be closed.

Purpose:
    FEAT-FORMULAS-FULL-POSITION: Formula sentinel for closing the full position.

Key Capabilities:
    - FR-formulas-full-position: Returns float 0.0 regardless of symbol, price,
      direction, or strategy state.

Python API Usage:
    from app.extend.formulas.close_size.full_position import FullPosition
    evaluator = FullPosition()
    val = evaluator.evaluate_formula(None, "EURUSD", 1.1, 1)

CLI Usage:
    python -c "from app.extend.formulas.close_size.full_position import (
        FullPosition,
    ); print(FullPosition().evaluate_formula(None, 'EURUSD', 1.0, 1))"
"""

from __future__ import annotations

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class FullPosition:
    """Sentinel formula evaluator for closing full position volume."""

    def evaluate_formula(
        self, strategy: object, symbol: str, price: float, direction: int
    ) -> float:
        """Evaluate full position close size formula.

        Args:
            strategy: Strategy context object (uninspected).
            symbol: Financial instrument symbol (uninspected).
            price: Current reference price (uninspected).
            direction: Trade direction indicator (uninspected).

        Returns:
            Float 0.0 sentinel representing full position closure.
        """
        logger.debug(
            "Evaluating FullPosition: symbol=%s, price=%f, direction=%d, strategy=%s",
            symbol,
            price,
            direction,
            type(strategy).__name__,
        )
        return 0.0
