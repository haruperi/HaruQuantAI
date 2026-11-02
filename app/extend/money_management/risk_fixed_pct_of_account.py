"""Risk fixed percent of account equity money management snippet.

Description:
    Calculates position sizing risking a fixed percentage of total account
    equity per trade, adjusting order size upward as capital grows.
Purpose:
    FEAT-MONEY-MANAGEMENT: Equity percentage-based risk sizing.
Key Capabilities:
    - FR-MM-RISK-FIXED-PCT-OF-ACCOUNT: Compounding equity risk per order.
Python API Usage:
    from app.extend.money_management.risk_fixed_pct_of_account import (
        RiskFixedPctOfAccount,
    )
    sizer = RiskFixedPctOfAccount(risk_in_pct=2.0, decimals=2)
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


class RiskFixedPctOfAccount(BasePositionSizer):
    """Risk fixed percentage of account equity (RiskFixedPctOfAccount.java)."""

    name: str = "RiskFixedPctOfAccount"
    display: str = "Risk fixed % of account: #Risk#%"
    help_text: str = (
        "<b>Risk fixed percentage of account size</b><br/>"
        "Strategy will risk a given % of equity for every trade."
    )
    description: str = "Risk #Risk#% of account"
    sort_order: int = 300
    for_engine: str = "*,-SP,-SA"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(
        self,
        *,
        risk_in_pct: float = 5.0,
        decimals: int = 2,
        stop_loss_in_pips: int = 100,
        lots_if_no_mm: float = 1.0,
        max_lots: float = 100.0,
        Risk: float | None = None,  # noqa: N803
        Decimals: int | None = None,  # noqa: N803
        StopLossInPips: int | None = None,  # noqa: N803
        LotsIfNoMM: float | None = None,  # noqa: N803
        MaxLots: float | None = None,  # noqa: N803
    ) -> None:
        super().__init__()
        self.risk_in_pct: float = Risk if Risk is not None else risk_in_pct
        self.decimals: int = Decimals if Decimals is not None else decimals
        self.stop_loss_in_pips: int = (
            StopLossInPips if StopLossInPips is not None else stop_loss_in_pips
        )
        self.lots_if_no_mm: float = (
            LotsIfNoMM if LotsIfNoMM is not None else lots_if_no_mm
        )
        self.max_lots: float = MaxLots if MaxLots is not None else max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute lots risking risk_in_pct% of current account equity."""
        effective_stop = (
            stop_loss_pips if stop_loss_pips > 0.0 else float(self.stop_loss_in_pips)
        )
        if (
            account_equity <= 0.0
            or effective_stop <= 0.0
            or pip_value <= 0.0
            or self.risk_in_pct <= 0.0
        ):
            result = round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            risk_pct = min(self.risk_in_pct * self.weight, 100.0)
            dollar_risk = account_equity * (risk_pct / 100.0)
            raw = dollar_risk / (effective_stop * pip_value)
            result = clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug(
            "FR-MM-RISK-FIXED-PCT-OF-ACCOUNT: RiskFixedPctOfAccount=%f", result
        )
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
        _ = (symbol, order_type)
        if self.risk_in_pct < 0:
            msg = (
                "Money management wasn't properly initialized. "
                "Call init() method before computing trade size!"
            )
            raise ValueError(msg)

        order_sl = (
            abs(price - sl) / tick_size
            if (sl > 0.0 and price > 0.0 and tick_size > 0.0)
            else float(self.stop_loss_in_pips)
        )
        sl_in_money = order_sl * tick_size * point_value
        if sl_in_money <= 0.0:
            return min(self.lots_if_no_mm, self.max_lots)

        risk_pct = min(self.risk_in_pct * self.weight, 100.0)
        equity = 10000.0
        if strategy is not None and hasattr(strategy, "get_account_equity"):
            equity = float(strategy.get_account_equity())
        elif strategy is not None and hasattr(strategy, "getAccountEquity"):
            equity = float(strategy.getAccountEquity())

        max_risk = equity * (risk_pct / 100.0)
        trade_size = round_lots(max_risk / sl_in_money, size_step, self.decimals)
        if trade_size <= 0.0:
            trade_size = self.lots_if_no_mm
        if self.max_lots > 0.0 and trade_size > self.max_lots:
            trade_size = self.max_lots
        logger.debug(
            "FR-MM-RISK-FIXED-PCT-OF-ACCOUNT: compute_trade_size=%f", trade_size
        )
        return trade_size


__all__ = ["RiskFixedPctOfAccount"]
