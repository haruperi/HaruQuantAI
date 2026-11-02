"""ATR-based value formula for RangeLevel matching SQ.Formulas.RangeLevel.ATRBasedValue.

Description:
    Computes an entry trigger level offset by an ATR multiple.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-level-atr: Calculate ATR multiple entry trigger level.
Python API Usage:
    from app.extend.formulas.range_level.atr_based_value import ATRBasedValue
    formula = ATRBasedValue(value=1.5, atr_period=20)
    level = formula.evaluate_formula(None, "EURUSD", 1.1000, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import ORDER_NOT_DEFINED, FormulaBlock

logger = get_logger(__name__)

_DEFAULT_ATR: float = 0.0010


class ATRBasedValue(FormulaBlock):
    """RangeLevel formula calculating price offset by ATR multiple."""

    def __init__(self, value: float = 1.0, atr_period: int = 20) -> None:
        """Initialize with ATR multiple multiplier and lookback period."""
        super().__init__(
            name="ATR-based value",
            group="RangeLevel",
            order=300,
        )
        self.value: float = value
        self.atr_period: int = atr_period

    @override
    def evaluate_formula(
        self,
        strategy: Any,
        symbol: str,
        price: float,
        direction: int,
    ) -> float:
        """Calculate entry trigger price offset by ATR multiple.

        Args:
            strategy: Execution context with market data / ATR lookup.
            symbol: Target market symbol.
            price: Current reference price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Calculated trigger price level rounded to 5 decimal places.
        """
        logger.debug(
            "RangeLevel.ATRBasedValue.evaluate_formula symbol=%s mult=%s "
            "period=%d dir=%d",
            symbol,
            self.value,
            self.atr_period,
            direction,
        )
        if self.value == 0.0:
            return ORDER_NOT_DEFINED

        atr = _DEFAULT_ATR
        if strategy is not None:
            if hasattr(strategy, "get_atr_value"):
                atr = float(strategy.get_atr_value(symbol, self.atr_period))
            elif hasattr(strategy, "getATRValue"):
                atr = float(strategy.getATRValue(symbol, self.atr_period, 1))

        val_price = self.value * round(atr, 6)
        if direction == 1:
            return round(price - val_price, 5)
        return round(price + val_price, 5)
