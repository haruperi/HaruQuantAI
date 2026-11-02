"""Price level formula for SLPT matching SQ.Formulas.SLPT.PriceLevel.

Description:
    Evaluates an arbitrary nested block directly as an absolute Stop Loss
    or Profit Target price level.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-slpt-price-level: Absolute price level SL/PT evaluation.
Python API Usage:
    from app.extend.formulas.slpt.price_level import PriceLevel
    formula = PriceLevel(value=1.1500)
    level = formula.evaluate_formula(None, "EURUSD", 1.1000, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import FormulaBlock

logger = get_logger(__name__)


class PriceLevel(FormulaBlock):
    """SLPT formula evaluating nested block as an absolute price level."""

    def __init__(self, value: Any = 0.0) -> None:
        """Initialize PriceLevel with nested block/scalar value and order 700."""
        super().__init__(
            name="Price level",
            group="SLPT",
            order=700,
            price_level=True,
        )
        self.value: Any = value

    @override
    def evaluate_formula(
        self,
        strategy: Any,
        symbol: str,
        price: float,
        direction: int,
    ) -> float:
        """Return evaluated nested block directly as absolute price level.

        Args:
            strategy: Strategy execution context.
            symbol: Financial instrument symbol.
            price: Current reference price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Calculated numeric price.
        """
        logger.debug(
            "SLPT.PriceLevel.evaluate_formula symbol=%s price=%s direction=%s",
            symbol,
            price,
            direction,
        )
        if hasattr(self.value, "evaluate_block"):
            return float(self.value.evaluate_block())
        if hasattr(self.value, "evaluate_formula"):
            return float(
                self.value.evaluate_formula(strategy, symbol, price, direction)
            )
        if callable(self.value):
            return float(self.value())
        return float(self.value)
