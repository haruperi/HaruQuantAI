"""Fixed amount money management snippet.

Description:
    Calculates position size risking a fixed monetary amount per trade based
    on the order stop loss distance and point value.
Purpose:
    FEAT-MONEY-MANAGEMENT: Fixed monetary risk position sizing.
Key Capabilities:
    - FR-MM-FIXED-AMOUNT: Risk fixed currency value per order with stop scaling.
Python API Usage:
    from app.extend.money_management.fixed_amount import FixedAmount
    sizer = FixedAmount(risked_money=200.0, decimals=2, lots_if_no_mm=0.1, max_lots=5.0)
    lots = sizer.compute_size(10000.0, 20.0, 10.0)
CLI Usage:
    uv run pytest tests/extend/test_money_management_catalog.py --no-cov
"""

from __future__ import annotations

import logging
from typing import Any, override

from app.extend.money_management.base import (
    BasePositionSizer,
    clamp_lots,
    round_down,
    round_lots,
)

logger = logging.getLogger(__name__)


class FixedAmount(BasePositionSizer):
    """Risk fixed currency amount per trade (FixedAmount.java)."""

    name: str = "FixedAmount"
    display: str = "Fixed amount: #RiskedMoney# $"
    help_text: str = (
        "<b>Strategy will risk given amount of money for every trade</b><br/>"
        "This is basic money management without compounding."
    )
    description: str = "Fixed amount, #RiskedMoney# $"
    sort_order: int = 400
    for_engine: str = "*,-SP,-SA"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(
        self,
        *,
        risked_money: float = 100.0,
        decimals: int = 2,
        lots_if_no_mm: float = 0.1,
        max_lots: float = 5.0,
        RiskedMoney: float | None = None,  # noqa: N803
        Decimals: int | None = None,  # noqa: N803
        LotsIfNoMM: float | None = None,  # noqa: N803
        MaxLots: float | None = None,  # noqa: N803
    ) -> None:
        super().__init__()
        self.risked_money: float = (
            RiskedMoney if RiskedMoney is not None else risked_money
        )
        self.decimals: int = Decimals if Decimals is not None else decimals
        self.lots_if_no_mm: float = (
            LotsIfNoMM if LotsIfNoMM is not None else lots_if_no_mm
        )
        self.max_lots: float = MaxLots if MaxLots is not None else max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute lots risking a fixed currency amount over the stop distance."""
        _ = account_equity
        if stop_loss_pips <= 0.0 or pip_value <= 0.0 or self.risked_money <= 0.0:
            result = round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            raw = (self.risked_money * self.weight) / (stop_loss_pips * pip_value)
            result = clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-MM-FIXED-AMOUNT: FixedAmount=%f", result)
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
        _ = (strategy, symbol, order_type)
        if self.risked_money < 0:
            msg = (
                "Money management wasn't properly initialized. "
                "Call init() method before computing trade size!"
            )
            raise ValueError(msg)
        if sl <= 0.0 or tick_size <= 0.0 or point_value <= 0.0:
            return min(self.lots_if_no_mm, self.max_lots)

        order_sl = abs(price - sl) / tick_size if price > 0.0 else 0.0
        sl_in_money = order_sl * tick_size * point_value
        if sl_in_money <= 0.0:
            return min(self.lots_if_no_mm, self.max_lots)

        ratio = (self.risked_money * self.weight) / sl_in_money
        trade_size = round_lots(ratio, size_step, self.decimals)
        if trade_size <= 0.0:
            trade_size = self.lots_if_no_mm
        if self.max_lots > 0.0 and trade_size > self.max_lots:
            trade_size = self.max_lots
        logger.debug("FR-MM-FIXED-AMOUNT: compute_trade_size=%f", trade_size)
        return trade_size


__all__ = ["FixedAmount"]
