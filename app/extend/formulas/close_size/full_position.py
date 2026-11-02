"""Full position close size sentinel formula definition.

Description:
    Implements the FullPosition formula evaluation helper used within strategy
    trade execution and Builder formulas. In the observed engine semantics,
    evaluating FullPosition returns numeric 0.0 as a close-size sentinel
    indicating that the entire open volume of the position should be closed.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-full-position: Returns float 0.0 regardless of symbol, price,
      direction, or strategy state.
Python API Usage:
    from app.extend.formulas.close_size.full_position import FullPosition
    evaluator = FullPosition()
    val = evaluator.evaluate_formula(None, "EURUSD", 1.1, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import FormulaBlock

logger = get_logger(__name__)


class FullPosition(FormulaBlock):
    """Sentinel formula evaluator for closing full position volume."""

    def __init__(self) -> None:
        """Initialize FullPosition with group CloseSize and order 100."""
        super().__init__(name="Full position", group="CloseSize", order=100)

    @override
    def evaluate_formula(
        self,
        strategy: Any,
        symbol: str,
        price: float,
        direction: int,
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
