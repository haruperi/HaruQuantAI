"""None formula definition for Range group matching SQ.Formulas.Range.None.

Description:
    Represents an undefined Range offset sentinel, returning Order.NOT_DEFINED.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-none: Sentinel for undefined range values.
Python API Usage:
    from app.extend.formulas.range.none import NoneRange
    formula = NoneRange()
    val = formula.evaluate_formula(None, "EURUSD", 1.10, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import ORDER_NOT_DEFINED, FormulaBlock

logger = get_logger(__name__)


class NoneRange(FormulaBlock):
    """Sentinel formula for undefined range values."""

    def __init__(self) -> None:
        """Initialize NoneRange with none_value=True and order 100."""
        super().__init__(
            name="None",
            group="Range",
            order=100,
            none_value=True,
        )

    @override
    def evaluate_formula(
        self,
        strategy: Any,
        symbol: str,
        price: float,
        direction: int,
    ) -> float:
        """Return ORDER_NOT_DEFINED sentinel."""
        logger.debug(
            "NoneRange.evaluate_formula symbol=%s price=%s direction=%s",
            symbol,
            price,
            direction,
        )
        return ORDER_NOT_DEFINED
