"""Simple Martingale money management snippet.

Description:
    Implements a Martingale step-multiplier position sizing scheme that
    multiplies trade size after losses and resets to starting size upon
    profit or when exceeding a maximum lot ceiling.
Purpose:
    FEAT-MONEY-MANAGEMENT: Martingale progression position sizing.
Key Capabilities:
    - FR-MM-SIMPLE-MARTINGALE-MM: Loss streak lot multiplication and profit reset.
Python API Usage:
    from app.extend.money_management.simple_martingale_mm import (
        SimpleMartingaleMM,
    )
    sizer = SimpleMartingaleMM(start_lots=0.1, multiplier=2.0)
    sizer.record_trade_outcome(-50.0)
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


class SimpleMartingaleMM(BasePositionSizer):
    """Martingale step-multiplier money management (SimpleMartingaleMM.java)."""

    name: str = "SimpleMartingaleMM"
    display: str = "Simple Martingale MM"
    help_text: str = (
        "<b>Simple Martingale MM</b><br/>"
        "Multiplies the last trade size by multiplier after loss. "
        "Resets size to a starting size after profit."
    )
    description: str = "Simple Martingale MM"
    sort_order: int = 900
    for_engine: str = "*,-SP,-SA"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures")

    def __init__(
        self,
        *,
        mm_StartLots: float = 0.1,  # noqa: N803
        mm_Multiplier: float = 2.0,  # noqa: N803
        mm_MaxLots: float = 10.0,  # noqa: N803
        mm_Decimals: int = 2,  # noqa: N803
        start_lots: float | None = None,
        multiplier: float | None = None,
        max_lots: float | None = None,
        decimals: int | None = None,
        separate_by_direction: bool = True,
        consecutive_losses: int = 0,
        LotsStart: float | None = None,  # noqa: N803
        LotsMultiplier: float | None = None,  # noqa: N803
        LotsReset: float | None = None,  # noqa: N803
        Decimals: int | None = None,  # noqa: N803
        SeparateByDirection: bool | None = None,  # noqa: N803
    ) -> None:
        super().__init__()
        effective_start = LotsStart if LotsStart is not None else mm_StartLots
        self.start_lots: float = (
            start_lots if start_lots is not None else effective_start
        )

        effective_mult = LotsMultiplier if LotsMultiplier is not None else mm_Multiplier
        self.multiplier: float = (
            multiplier if multiplier is not None else effective_mult
        )

        effective_reset = LotsReset if LotsReset is not None else mm_MaxLots
        self.max_lots: float = max_lots if max_lots is not None else effective_reset

        effective_dec = Decimals if Decimals is not None else mm_Decimals
        self.decimals: int = decimals if decimals is not None else effective_dec

        self.separate_by_direction: bool = (
            SeparateByDirection
            if SeparateByDirection is not None
            else separate_by_direction
        )
        self.consecutive_losses: int = max(consecutive_losses, 0)
        self.consecutive_losses_long: int = 0
        self.consecutive_losses_short: int = 0

    def record_trade_outcome(self, profit: float, direction: int = 0) -> None:
        """Update martingale loss streak from closed trade profit/loss.

        Args:
            profit: Closed trade dollar profit/loss.
            direction: 1 for long trade, -1 for short trade, 0 for generic.
        """
        if profit < 0.0:
            self.consecutive_losses += 1
            if direction > 0:
                self.consecutive_losses_long += 1
            elif direction < 0:
                self.consecutive_losses_short += 1
        else:
            self.consecutive_losses = 0
            if direction > 0:
                self.consecutive_losses_long = 0
            elif direction < 0:
                self.consecutive_losses_short = 0

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute martingale lot size, resetting to start_lots when exceeding max."""
        _ = (account_equity, stop_loss_pips, pip_value)
        if self.start_lots <= 0.0 or self.multiplier <= 0.0:
            return 0.0
        raw = self.start_lots * (self.multiplier**self.consecutive_losses)
        rounded = round_down(raw, self.decimals)
        if self.max_lots > 0.0 and rounded > self.max_lots:
            rounded = round_down(self.start_lots, self.decimals)
        logger.debug("FR-MM-SIMPLE-MARTINGALE-MM: SimpleMartingaleMM=%f", rounded)
        return rounded

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
        _ = (symbol, price, sl, tick_size, point_value)
        if self.start_lots < 0.0:
            msg = (
                "Money management wasn't properly initialized. "
                "Call init() method before computing trade size!"
            )
            raise ValueError(msg)

        streak = self.consecutive_losses
        if self.separate_by_direction and order_type != 0:
            streak = (
                self.consecutive_losses_long
                if order_type > 0
                else self.consecutive_losses_short
            )

        raw = self.start_lots * (self.multiplier**streak) * self.weight
        if self.max_lots > 0.0 and raw > self.max_lots:
            raw = self.start_lots

        trade_size = round_lots(raw, size_step, self.decimals)
        logger.debug("FR-MM-SIMPLE-MARTINGALE-MM: compute_trade_size=%f", trade_size)
        return trade_size


__all__ = ["SimpleMartingaleMM"]
