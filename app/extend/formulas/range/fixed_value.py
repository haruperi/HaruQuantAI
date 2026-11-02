"""Fixed value in pips formula for Range group matching SQ.Formulas.Range.FixedValue.

Description:
    Computes a pip distance converted into real price units.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-fixed-value: Convert fixed pips to absolute price range.
Python API Usage:
    from app.extend.formulas.range.fixed_value import FixedValue
    formula = FixedValue(value=50.0)
    range_val = formula.evaluate_formula(None, "EURUSD", 1.10, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import FormulaBlock

logger = get_logger(__name__)

_DEFAULT_PIP_SIZE: float = 0.0001


class FixedValue(FormulaBlock):
    """Range formula calculating distance from fixed pips."""

    def __init__(self, value: float = 50.0) -> None:
        """Initialize FixedValue with pips amount and order 200."""
        super().__init__(
            name="Fixed value (in pips)",
            group="Range",
            order=200,
        )
        self.value: float = value

    @override
    def evaluate_formula(
        self,
        strategy: Any,
        symbol: str,
        price: float,
        direction: int,
    ) -> float:
        """Calculate real price range for fixed pip count.

        Args:
            strategy: Execution context with pip conversion helper.
            symbol: Target market symbol.
            price: Current reference price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Computed price range distance.
        """
        logger.debug(
            "Range.FixedValue.evaluate_formula symbol=%s value=%s price=%s",
            symbol,
            self.value,
            price,
        )
        if self.value == 0.0:
            return 0.0

        if strategy is not None and hasattr(strategy, "convert_pips_to_real_price"):
            return float(strategy.convert_pips_to_real_price(symbol, self.value))
        if strategy is not None and hasattr(strategy, "convertPipsToRealPrice"):
            return float(strategy.convertPipsToRealPrice(symbol, self.value))
        return self.value * _DEFAULT_PIP_SIZE
