"""ATR-based range value formula matching SQ.Formulas.Range.ATRBasedValue.

Description:
    Computes range distance as a multiple of Average True Range (ATR).
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-atr: Calculate ATR multiple range distance.
Python API Usage:
    from app.extend.formulas.range.atr_based_value import ATRBasedValue
    formula = ATRBasedValue(value=1.5, atr_period=14)
    val = formula.evaluate_formula(strategy, "EURUSD", 1.10, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import FormulaBlock

logger = get_logger(__name__)

_DEFAULT_ATR: float = 0.0010


class ATRBasedValue(FormulaBlock):
    """Range formula calculating distance as Value * ATR(AtrPeriod)."""

    def __init__(self, value: float = 1.0, atr_period: int = 20) -> None:
        """Initialize with ATR multiple multiplier and lookback period."""
        super().__init__(
            name="ATR-based value",
            group="Range",
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
        """Calculate ATR-based price distance.

        Args:
            strategy: Execution context with market data / ATR lookup.
            symbol: Target market symbol.
            price: Current reference price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Computed ATR multiple distance rounded to 5 decimal places.
        """
        logger.debug(
            "Range.ATRBasedValue.evaluate_formula symbol=%s mult=%s period=%d",
            symbol,
            self.value,
            self.atr_period,
        )
        if self.value == 0.0:
            return 0.0

        atr = _DEFAULT_ATR
        if strategy is not None:
            if hasattr(strategy, "get_atr_value"):
                atr = float(strategy.get_atr_value(symbol, self.atr_period))
            elif hasattr(strategy, "getATRValue"):
                atr = float(strategy.getATRValue(symbol, self.atr_period, 1))

        res = self.value * atr
        return round(res, 5)
