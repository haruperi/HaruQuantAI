"""Crypto fixed percent balance money management snippet.

Description:
    Computes cryptocurrency order quantity risking a fixed percentage of
    settled account balance per trade.
Purpose:
    FEAT-MONEY-MANAGEMENT: Crypto balance percentage position sizing.
Key Capabilities:
    - FR-MM-CRYPTO-FIXED-BALANCE-PCT: Account balance percent risk for crypto.
Python API Usage:
    from app.extend.money_management.crypto_fixed_balance_pct import (
        CryptoFixedBalancePct,
    )
    sizer = CryptoFixedBalancePct(risk_in_pct=2.0, decimals=4)
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


class CryptoFixedBalancePct(BasePositionSizer):
    """Crypto risk fixed percentage of account balance (CryptoFixedBalancePct.java)."""

    name: str = "CryptoFixedBalancePct"
    display: str = "Crypto fixed % balance: #Risk#%"
    help_text: str = "<b>Crypto fixed percentage of balance</b>"
    description: str = "Crypto #Risk#% of balance"
    sort_order: int = 200
    for_engine: str = "*,-SP,-SA"
    supported_engines: tuple[str, ...] = ("Crypto",)

    def __init__(
        self,
        *,
        risk_in_pct: float = 2.0,
        decimals: int = 4,
        lots_if_no_mm: float = 0.01,
        max_lots: float = 1000.0,
        Risk: float | None = None,  # noqa: N803
        Decimals: int | None = None,  # noqa: N803
        LotsIfNoMM: float | None = None,  # noqa: N803
        MaxLots: float | None = None,  # noqa: N803
    ) -> None:
        super().__init__()
        self.risk_in_pct: float = Risk if Risk is not None else risk_in_pct
        self.decimals: int = Decimals if Decimals is not None else decimals
        self.lots_if_no_mm: float = (
            LotsIfNoMM if LotsIfNoMM is not None else lots_if_no_mm
        )
        self.max_lots: float = MaxLots if MaxLots is not None else max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute crypto order quantity risking risk_in_pct% of balance."""
        if (
            account_equity <= 0.0
            or stop_loss_pips <= 0.0
            or pip_value <= 0.0
            or self.risk_in_pct <= 0.0
        ):
            result = round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            risk_pct = min(self.risk_in_pct * self.weight, 100.0)
            dollar_risk = account_equity * (risk_pct / 100.0)
            raw = dollar_risk / (stop_loss_pips * pip_value)
            result = clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-MM-CRYPTO-FIXED-BALANCE-PCT: CryptoFixedBalancePct=%f", result)
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
        _ = (symbol, order_type, sl, tick_size, point_value)
        if self.risk_in_pct < 0:
            msg = (
                "Money management wasn't properly initialized. "
                "Call init() method before computing trade size!"
            )
            raise ValueError(msg)

        if price <= 0.0:
            return min(self.lots_if_no_mm, self.max_lots)

        balance = 10000.0
        if strategy is not None and hasattr(strategy, "get_account_balance"):
            balance = float(strategy.get_account_balance())
        elif strategy is not None and hasattr(strategy, "getAccountBalance"):
            balance = float(strategy.getAccountBalance())

        risk_pct = min(self.risk_in_pct * self.weight, 100.0)
        money_to_risk = round(balance * (risk_pct / 100.0), 2)
        trade_size = round_lots(money_to_risk / price, size_step, self.decimals)
        if trade_size <= 0.0:
            trade_size = self.lots_if_no_mm
        if self.max_lots > 0.0 and trade_size > self.max_lots:
            trade_size = self.max_lots
        logger.debug(
            "FR-MM-CRYPTO-FIXED-BALANCE-PCT: compute_trade_size=%f", trade_size
        )
        return trade_size


__all__ = ["CryptoFixedBalancePct"]
