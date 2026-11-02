"""Percent value formula for SLPT matching SQ.Formulas.SLPT.PctValue.

Description:
    Calculates Stop Loss or Profit Target level offset by a percentage of
    order entry price.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-slpt-percent: Percent offset Stop Loss or Profit Target level.
Python API Usage:
    from app.extend.formulas.slpt.pct_value import PctValue
    formula = PctValue(value=2.0)
    level = formula.evaluate_formula(None, "EURUSD", 100.0, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import FormulaBlock

logger = get_logger(__name__)

_PERCENT_SCALE: float = 100.0


class PctValue(FormulaBlock):
    """SLPT formula calculating level offset as a percentage of entry price."""

    def __init__(self, value: float = 5.0) -> None:
        """Initialize PctValue with percentage amount and order 300."""
        super().__init__(
            name="Percent value",
            group="SLPT",
            order=300,
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
        """Calculate SL/PT price level offset by percentage of price.

        Args:
            strategy: Execution context (uninspected).
            symbol: Target market symbol.
            price: Order open price.
            direction: Sign indicator (1 for add, -1 for subtract).

        Returns:
            Calculated target price level.
        """
        logger.debug(
            "SLPT.PctValue.evaluate_formula symbol=%s pct=%s price=%s dir=%d",
            symbol,
            self.value,
            price,
            direction,
        )
        pct_distance = (price / _PERCENT_SCALE) * self.value
        if direction > 0:
            return price + pct_distance
        return price - pct_distance
