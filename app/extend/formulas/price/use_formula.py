"""Price formula evaluating an arbitrary nested formula block.

Description:
    Evaluates a nested block expression or scalar operand as an absolute
    price level, matching SQ.Formulas.Price.UseFormula.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-price-use-formula: Evaluate price expression from nested block.
Python API Usage:
    from app.extend.formulas.price.use_formula import UseFormula
    formula = UseFormula(value=1.1250)
    price = formula.evaluate_formula(None, "EURUSD", 1.1200, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import FormulaBlock

logger = get_logger(__name__)


class UseFormula(FormulaBlock):
    """Evaluates an arbitrary nested block or scalar as a price level."""

    def __init__(self, value: Any = 0.0) -> None:
        """Initialize UseFormula with value parameter and price_level=True."""
        super().__init__(
            name="Use formula",
            group="Price",
            order=400,
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
        """Evaluate nested block or scalar value.

        Args:
            strategy: Strategy execution context.
            symbol: Financial instrument symbol.
            price: Current reference price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Calculated numeric price.
        """
        logger.debug(
            "UseFormula.evaluate_formula symbol=%s price=%s direction=%s",
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

    @override
    def is_boolean_value(self) -> bool:
        """Return True if nested value represents a boolean."""
        if isinstance(self.value, bool):
            return True
        if hasattr(self.value, "is_boolean_value"):
            return bool(self.value.is_boolean_value())
        return False
