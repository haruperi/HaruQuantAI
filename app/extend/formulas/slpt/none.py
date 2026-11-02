"""None formula definition for SLPT matching SQ.Formulas.SLPT.None.

Description:
    Sentinel for undefined Stop Loss or Profit Target level, returning
    Order.NOT_DEFINED.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-slpt-none: Sentinel for undefined protective levels.
Python API Usage:
    from app.extend.formulas.slpt.none import NoneSLPT
    formula = NoneSLPT()
    val = formula.evaluate_formula(None, "EURUSD", 1.10, 1)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import ORDER_NOT_DEFINED, FormulaBlock

logger = get_logger(__name__)


class NoneSLPT(FormulaBlock):
    """Sentinel formula for undefined SL/PT levels."""

    def __init__(self) -> None:
        """Initialize NoneSLPT with none_value=True and order 100."""
        super().__init__(
            name="None",
            group="SLPT",
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
            "NoneSLPT.evaluate_formula symbol=%s price=%s direction=%s",
            symbol,
            price,
            direction,
        )
        return ORDER_NOT_DEFINED
