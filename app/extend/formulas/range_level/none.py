"""None formula definition for RangeLevel matching SQ.Formulas.RangeLevel.None.

Description:
    Sentinel for undefined RangeLevel entry level, returning Order.NOT_DEFINED.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-range-level-none: Sentinel for undefined range level boundaries.
Python API Usage:
    from app.extend.formulas.range_level.none import NoneRangeLevel
    formula = NoneRangeLevel()
    val = formula.evaluate_formula(None, "EURUSD", 1.10, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import ORDER_NOT_DEFINED, FormulaBlock

logger = get_logger(__name__)


class NoneRangeLevel(FormulaBlock):
    """Sentinel formula for undefined range level offsets."""

    def __init__(self) -> None:
        """Initialize NoneRangeLevel with none_value=True and order 100."""
        super().__init__(
            name="None",
            group="RangeLevel",
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
            "NoneRangeLevel.evaluate_formula symbol=%s price=%s direction=%s",
            symbol,
            price,
            direction,
        )
        return ORDER_NOT_DEFINED
