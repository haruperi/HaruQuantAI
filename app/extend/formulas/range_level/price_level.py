"""Price level formula for RangeLevel matching SQ.Formulas.RangeLevel.PriceLevel.

Description:
    Evaluates an arbitrary nested block directly as an absolute entry price level.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-level-price-level: Absolute price level entry evaluation.
Python API Usage:
    from app.extend.formulas.range_level.price_level import PriceLevel
    formula = PriceLevel(value=1.1250)
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
    """RangeLevel formula evaluating nested block as an absolute price level."""

    def __init__(self, value: Any = 0.0) -> None:
        """Initialize PriceLevel with nested block/scalar value and order 700."""
        super().__init__(
            name="Price level",
            group="RangeLevel",
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
            "RangeLevel.PriceLevel.evaluate_formula symbol=%s price=%s direction=%s",
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
