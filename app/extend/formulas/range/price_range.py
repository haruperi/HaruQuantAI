"""Range in pips formula for Range group matching SQ.Formulas.Range.PriceRange.

Description:
    Evaluates a nested block expression returning pips and converts to real price.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-price-range: Convert nested block pips to price range.
Python API Usage:
    from app.extend.formulas.range.price_range import PriceRange
    formula = PriceRange(value=25.0)
    val = formula.evaluate_formula(strategy, "EURUSD", 1.10, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import FormulaBlock

logger = get_logger(__name__)

_DEFAULT_PIP_SIZE: float = 0.0001


class PriceRange(FormulaBlock):
    """Range formula evaluating nested block pips into real price."""

    def __init__(self, value: Any = 0.0) -> None:
        """Initialize PriceRange with nested block/scalar value and order 500."""
        super().__init__(
            name="Range in pips",
            group="Range",
            order=500,
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
        """Evaluate nested block and convert pips to real price.

        Args:
            strategy: Execution context with pip conversion helper.
            symbol: Target market symbol.
            price: Current reference price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Calculated range in price units.
        """
        logger.debug(
            "Range.PriceRange.evaluate_formula symbol=%s price=%s direction=%s",
            symbol,
            price,
            direction,
        )
        if hasattr(self.value, "evaluate_block"):
            pips = float(self.value.evaluate_block())
        elif hasattr(self.value, "evaluate_formula"):
            pips = float(
                self.value.evaluate_formula(strategy, symbol, price, direction)
            )
        elif callable(self.value):
            pips = float(self.value())
        else:
            pips = float(self.value)

        if strategy is not None and hasattr(strategy, "convert_pips_to_real_price"):
            return float(strategy.convert_pips_to_real_price(symbol, pips))
        if strategy is not None and hasattr(strategy, "convertPipsToRealPrice"):
            return float(strategy.convertPipsToRealPrice(symbol, pips))
        return pips * _DEFAULT_PIP_SIZE
