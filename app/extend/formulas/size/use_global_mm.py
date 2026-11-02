"""Use global Money Management formula matching SQ.Formulas.Size.UseGlobalMM.

Description:
    Delegates lot sizing calculation to the project or strategy configured
    global Money Management method, defaulting to 1.0 or -1.0 sentinel when
    unconfigured.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-size-use-global-mm: Global money management delegation.
Python API Usage:
    from app.extend.formulas.size.use_global_mm import UseGlobalMM
    sizer = UseGlobalMM()
    lots = sizer.compute_size(strategy, "EURUSD", 0, 1.1000, 1.0950)
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.formulas.base import MMFormulaBlock

logger = get_logger(__name__)


class UseGlobalMM(MMFormulaBlock):
    """Size formula delegating to strategy's global Money Management method."""

    def __init__(self) -> None:
        """Initialize UseGlobalMM with order 200."""
        super().__init__(
            name="Use global Money Management",
            group="Size",
            order=200,
        )

    @override
    def compute_size(
        self,
        strategy: Any,
        symbol: str,
        order_type: int,
        price: float,
        sl: float,
    ) -> float:
        """Compute trade size from strategy global money management.

        Args:
            strategy: Execution context with money management method.
            symbol: Target financial instrument.
            order_type: Order type indicator code.
            price: Execution entry price.
            sl: Stop Loss reference price.

        Returns:
            Calculated trade lot size, or 1.0 if no MM configured.
        """
        logger.debug(
            "Size.UseGlobalMM.compute_size symbol=%s price=%s sl=%s",
            symbol,
            price,
            sl,
        )
        if strategy is None:
            return 1.0

        mm_method = None
        if hasattr(strategy, "get_global_mm_method"):
            mm_method = strategy.get_global_mm_method()
        elif hasattr(strategy, "getGlobalMMMethod"):
            mm_method = strategy.getGlobalMMMethod()
        elif hasattr(strategy, "get_settings"):
            settings = strategy.get_settings()
            if isinstance(settings, dict):
                mm_method = settings.get("MoneyManagement")

        if mm_method is None:
            return 1.0

        if hasattr(mm_method, "compute_trade_size"):
            return float(
                mm_method.compute_trade_size(strategy, symbol, order_type, price, sl)
            )
        if hasattr(mm_method, "computeTradeSize"):
            return float(
                mm_method.computeTradeSize(
                    strategy, symbol, order_type, price, sl, 0.0001, 1.0, 0.01
                )
            )
        return 1.0
