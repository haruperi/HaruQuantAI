"""Stockpicker fixed amount money management snippet.

Description:
    Allocates a fixed currency capital pool across allowed positions,
    supporting integer share sizing and optional fractional shares.
Purpose:
    FEAT-MONEY-MANAGEMENT: Stockpicker portfolio position sizing.
Key Capabilities:
    - FR-MM-PICKER-FIXED-AMOUNT: Stockpicker fixed capital allocation.
Python API Usage:
    from app.extend.money_management.picker_fixed_amount import (
        PickerFixedAmount,
    )
    sizer = PickerFixedAmount(amount=1000.0, decimals=0)
    lots = sizer.compute_size(10000.0, 20.0, 50.0)
CLI Usage:
    uv run pytest tests/extend/test_money_management_catalog.py --no-cov
"""

from __future__ import annotations

import logging
import math
from typing import Any, override

from app.extend.money_management.base import (
    BasePositionSizer,
    clamp_lots,
    round_down,
)

logger = logging.getLogger(__name__)


class PickerFixedAmount(BasePositionSizer):
    """Stockpicker fixed cash allocation per position (PickerFixedAmount.java)."""

    name: str = "PickerFixedAmount"
    display: str = "Fixed amount: #RiskedMoney# $"
    help_text: str = (
        "<b>Fixed - the method allocates fixed amount of capital and "
        "split into maximum positions allowed.</b>"
    )
    description: str = "Fixed amount, #RiskedMoney# $"
    sort_order: int = 400
    for_engine: str = "SP,SA"
    supported_engines: tuple[str, ...] = ("Stockpicker",)

    def __init__(
        self,
        *,
        amount: float = 1000.0,
        decimals: int = 0,
        lots_if_no_mm: float = 1.0,
        max_lots: float = 100000.0,
        allow_fractional_shares: bool = False,
        fractional_decimal_numbers: int = 4,
        fractional_step: float = 0.01,
        RiskedMoney: float | None = None,  # noqa: N803
        AllowFractionalShares: bool | None = None,  # noqa: N803
        FractionalDecimalNumbers: int | None = None,  # noqa: N803
        FractionalStep: float | None = None,  # noqa: N803
        Decimals: int | None = None,  # noqa: N803
        LotsIfNoMM: float | None = None,  # noqa: N803
        MaxLots: float | None = None,  # noqa: N803
    ) -> None:
        super().__init__()
        self.amount: float = RiskedMoney if RiskedMoney is not None else amount
        self.decimals: int = Decimals if Decimals is not None else decimals
        self.lots_if_no_mm: float = (
            LotsIfNoMM if LotsIfNoMM is not None else lots_if_no_mm
        )
        self.max_lots: float = MaxLots if MaxLots is not None else max_lots
        self.allow_fractional_shares: bool = (
            AllowFractionalShares
            if AllowFractionalShares is not None
            else allow_fractional_shares
        )
        self.fractional_decimal_numbers: int = (
            FractionalDecimalNumbers
            if FractionalDecimalNumbers is not None
            else fractional_decimal_numbers
        )
        self.fractional_step: float = (
            FractionalStep if FractionalStep is not None else fractional_step
        )

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute stockpicker share quantity for a fixed cash amount."""
        _ = (account_equity, stop_loss_pips)
        share_price = pip_value
        if self.amount <= 0.0 or share_price <= 0.0:
            result = round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            raw = (self.amount * self.weight) / share_price
            if self.max_pos > 0.0:
                raw /= self.max_pos
            result = clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-MM-PICKER-FIXED-AMOUNT: PickerFixedAmount=%f", result)
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
        _ = (strategy, symbol, order_type, sl, tick_size, point_value, size_step)
        if self.amount < 0.0:
            msg = (
                "Money management wasn't properly initialized. "
                "Call init() method before computing trade size!"
            )
            raise ValueError(msg)
        if price <= 0.0:
            msg = (
                f"PickerFixedAmount money management - invalid {symbol} price. "
                f"It must be > 0, got {price:.2f}."
            )
            raise ValueError(msg)

        trade_size = (self.amount * self.weight) / price
        if self.max_pos > 0.0:
            trade_size /= self.max_pos

        if self.allow_fractional_shares:
            if self.fractional_step > 0.0:
                trade_size = (
                    round(trade_size / self.fractional_step) * self.fractional_step
                )
            trade_size = round(trade_size, self.fractional_decimal_numbers)
        else:
            if trade_size < 1.0:
                msg = f"Calculated trade size {trade_size:.2f} < 1"
                raise ValueError(msg)
            trade_size = float(math.floor(trade_size))

        logger.debug("FR-MM-PICKER-FIXED-AMOUNT: compute_trade_size=%f", trade_size)
        return trade_size


__all__ = ["PickerFixedAmount"]
