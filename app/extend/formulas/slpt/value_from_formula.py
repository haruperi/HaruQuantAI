"""Value from formula in pips for SLPT matching SQ.Formulas.SLPT.ValueFromFormula.

Description:
    Calculates Stop Loss or Profit Target level offset by nested block pips.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-slpt-value-from-formula: Nested block pips for SL/PT level.
Python API Usage:
    from app.extend.formulas.slpt.value_from_formula import ValueFromFormula
    formula = ValueFromFormula(value=25.0)
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


class ValueFromFormula(FormulaBlock):
    """SLPT formula calculating level offset by evaluated nested block pips."""

    def __init__(self, value: Any = 0.0) -> None:
        """Initialize ValueFromFormula with nested block/scalar value and order 600."""
        super().__init__(
            name="Value from formula (in pips)",
            group="SLPT",
            order=600,
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
        """Calculate SL/PT price level offset by evaluated pips.

        Args:
            strategy: Execution context with pip conversion helper.
            symbol: Target market symbol.
            price: Order open price.
            direction: Sign indicator (1 for add, -1 for subtract).

        Returns:
            Computed target price level.
        """
        logger.debug(
            "SLPT.ValueFromFormula.evaluate_formula symbol=%s price=%s dir=%d",
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

        if direction > 0:
            return price + val_price
        return price - val_price
