"""Define own size formula for Size group matching SQ.Formulas.Size.DefineOwnSize.

Description:
    Computes fixed user-defined position sizing lots.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-size-define-own: Fixed explicit trade lot sizing.
Python API Usage:
    from app.extend.formulas.size.define_own_size import DefineOwnSize
    sizer = DefineOwnSize(value=0.5)
    lots = sizer.compute_size(None, "EURUSD", 0, 1.1000, 1.0950)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import MMFormulaBlock

logger = get_logger(__name__)

_MIN_LOT_SIZE: float = 0.01


class DefineOwnSize(MMFormulaBlock):
    """Size formula returning fixed explicit trade lot sizes."""

    def __init__(self, value: float = 0.1) -> None:
        """Initialize DefineOwnSize with lot value and order 100."""
        super().__init__(
            name="Define own size",
            group="Size",
            order=100,
        )
        self.value: float = max(_MIN_LOT_SIZE, value)

    @override
    def compute_size(
        self,
        strategy: Any,
        symbol: str,
        order_type: int,
        price: float,
        sl: float,
    ) -> float:
        """Return fixed configured lot size.

        Args:
            strategy: Execution context (uninspected).
            symbol: Target financial instrument.
            order_type: Order type indicator code.
            price: Execution entry price.
            sl: Stop Loss reference price.

        Returns:
            Configured lot volume.
        """
        logger.debug(
            "Size.DefineOwnSize.compute_size symbol=%s price=%s sl=%s -> %s",
            symbol,
            price,
            sl,
            self.value,
        )
        return self.value
