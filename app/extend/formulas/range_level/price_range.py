"""Range in pips formula for RangeLevel matching SQ.Formulas.RangeLevel.PriceRange.

Description:
    Computes an entry trigger level offset by nested block pips.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-level-price-range: Entry level offset by nested block pips.
Python API Usage:
    from app.extend.formulas.range_level.price_range import PriceRange
    formula = PriceRange(value=15.0)
    level = formula.evaluate_formula(None, "EURUSD", 1.1000, 1)
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
    """RangeLevel formula calculating entry price offset by nested block pips."""

    def __init__(self, value: Any = 0.0) -> None:
        """Initialize PriceRange with nested block/scalar value and order 500."""
        super().__init__(
            name="Range in pips",
            group="RangeLevel",
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
        """Calculate entry trigger price level offset by evaluated pips.

        Args:
            strategy: Execution context with pip conversion helper.
            symbol: Target market symbol.
            price: Current reference price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Computed price level.
        """
        logger.debug(
            "RangeLevel.PriceRange.evaluate_formula symbol=%s price=%s dir=%d",
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
            val_price = float(strategy.convert_pips_to_real_price(symbol, pips))
        elif strategy is not None and hasattr(strategy, "convertPipsToRealPrice"):
            val_price = float(strategy.convertPipsToRealPrice(symbol, pips))
        else:
            val_price = pips * _DEFAULT_PIP_SIZE

        if direction == 1:
            return price - val_price
        return price + val_price
