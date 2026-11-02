"""Fixed size money management snippet.

Description:
    Implements fixed order size money management without compounding.
    Trades a configured fixed number of lots or units for every trade.
Purpose:
    FEAT-MONEY-MANAGEMENT: Fixed order size position sizing.
Key Capabilities:
    - FR-MM-FIXED-SIZE: Compute fixed volume with precision rounding and weighting.
Python API Usage:
    from app.extend.money_management.fixed_size import FixedSize
    sizer = FixedSize(size=0.25, decimals=2)
    lots = sizer.compute_size(10000.0, 20.0)
CLI Usage:
    uv run pytest tests/extend/test_money_management_catalog.py --no-cov
"""

from __future__ import annotations

import logging
from typing import Any, override

from app.extend.money_management.base import (
    BasePositionSizer,
    round_down,
    round_lots,
)

logger = logging.getLogger(__name__)


class FixedSize(BasePositionSizer):
    """Fixed order size money management block (FixedSize.java)."""

    name: str = "FixedSize"
    display: str = "Fixed size: #Size# lots"
    help_text: str = (
        "<b>No money management</b><br/>Strategy will trade with fixed number of lots."
    )
    description: str = "Fixed size, #Size# lots"
    sort_order: int = 100
    for_engine: str = "*,-SP,-SA"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(
        self,
        *,
        size: float = 0.1,
        decimals: int = 2,
        Size: float | None = None,  # noqa: N803
        Decimals: int | None = None,  # noqa: N803
    ) -> None:
        super().__init__()
        self.size: float = Size if Size is not None else size
        self.decimals: int = Decimals if Decimals is not None else decimals

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Return fixed position size rounded to configured decimals."""
        _ = (account_equity, stop_loss_pips, pip_value)
        result = round_down(max(self.size, 0.0), self.decimals)
        logger.debug("FR-MM-FIXED-SIZE: FixedSize=%f", result)
        return result

    @override
    def compute_trade_size(
        self,
        strategy: Any = None,
        symbol: str = "",
        order_type: int = 0,
        price: float = 0.0,
        sl: float = 0.0,
        tick_size: float = 0.0001,
        point_value: float = 10.0,
        size_step: float = 0.01,
    ) -> float:
        """Donor StrategyQuant computeTradeSize parity method."""
        _ = (strategy, symbol, order_type, price, sl, tick_size, point_value)
        raw = self.size * self.weight
        result = round_lots(raw, size_step, self.decimals)
        logger.debug("FR-MM-FIXED-SIZE: compute_trade_size=%f", result)
        return result


__all__ = ["FixedSize"]
