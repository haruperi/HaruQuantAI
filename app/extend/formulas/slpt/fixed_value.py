"""Fixed value in pips formula for SLPT matching SQ.Formulas.SLPT.FixedValue.

Description:
    Calculates Stop Loss or Profit Target level offset by fixed pips.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-slpt-fixed: Fixed pip Stop Loss or Profit Target level.
Python API Usage:
    from app.extend.formulas.slpt.fixed_value import FixedValue
    formula = FixedValue(value=30.0)
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
    """SLPT formula calculating level offset by fixed pips."""

    def __init__(self, value: float = 50.0) -> None:
        """Initialize FixedValue with pips distance and order 300."""
        super().__init__(
            name="Fixed value (in pips)",
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
        """Calculate SL/PT price level offset by fixed pips.

        Args:
            strategy: Execution context with pip conversion helper.
            symbol: Target market symbol.
            price: Order open price.
            direction: Sign indicator (1 for add, -1 for subtract).

        Returns:
            Computed protective or target price level.
        """
        logger.debug(
            "SLPT.FixedValue.evaluate_formula symbol=%s value=%s price=%s dir=%d",
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

        if direction > 0:
            return price + val_price
        return price - val_price
