"""Fixed value in pips formula for RangeLevel.

Matches SQ.Formulas.RangeLevel.FixedValue.

Description:
    Computes an entry trigger level offset by fixed pips from base price or
    decision quotes.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-level-fixed: Calculate fixed pip entry trigger level.
Python API Usage:
    from app.extend.formulas.range_level.fixed_value import FixedValue
    formula = FixedValue(value=20.0)
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


class FixedValue(FormulaBlock):
    """RangeLevel formula calculating entry price offset by fixed pips."""

    def __init__(self, value: float = 50.0) -> None:
        """Initialize FixedValue with pips amount and order 200."""
        super().__init__(
            name="Fixed value (in pips)",
            group="RangeLevel",
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
        """Calculate entry trigger level offset by fixed pips.

        Args:
            strategy: Execution context with quote/pip conversion helpers.
            symbol: Target market symbol.
            price: Current reference price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Computed entry trigger level price.
        """
        logger.debug(
            "RangeLevel.FixedValue.evaluate_formula symbol=%s value=%s price=%s dir=%d",
            symbol,
            self.value,
            price,
            direction,
        )
        if strategy is not None and hasattr(strategy, "convert_pips_to_real_price"):
            val_price = float(strategy.convert_pips_to_real_price(symbol, self.value))
        elif strategy is not None and hasattr(strategy, "convertPipsToRealPrice"):
            val_price = float(strategy.convertPipsToRealPrice(symbol, self.value))
        else:
            val_price = self.value * _DEFAULT_PIP_SIZE

        base = price
        if strategy is not None:
            if direction == 1 and hasattr(strategy, "decisionBid"):
                base = float(strategy.decisionBid(symbol, 0))
            elif direction == -1 and hasattr(strategy, "decisionAsk"):
                base = float(strategy.decisionAsk(symbol, 0))

        if direction == 1:
            return base - val_price
        return base + val_price
