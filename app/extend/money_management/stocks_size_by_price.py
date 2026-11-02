"""Stocks size by price money management snippet.

Description:
    Computes stock share trade size by dividing available account balance
    or initial capital by current instrument share price.
Purpose:
    FEAT-MONEY-MANAGEMENT: Equity/capital allocation by share price.
Key Capabilities:
    - FR-MM-STOCKS-SIZE-BY-PRICE: Share quantity calculation by stock price.
Python API Usage:
    from app.extend.money_management.stocks_size_by_price import (
        StocksSizeByPrice,
    )
    sizer = StocksSizeByPrice(capital_pct=50.0, decimals=0)
    lots = sizer.compute_size(10000.0, 20.0, 50.0)
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


class StocksSizeByPrice(BasePositionSizer):
    """Allocate capital by instrument share price (StocksSizeByPrice.java)."""

    name: str = "StocksSizeByPrice"
    display: str = "Stocks size by price"
    help_text: str = (
        "<b>Size computed as Balance / StockSize.</b> "
        "Position sizing method specifically for stocks."
    )
    description: str = "Stocks size by price, max #MaxSize# lots"
    sort_order: int = 500
    for_engine: str = "*,-SP,-SA"
    supported_engines: tuple[str, ...] = ("Stocks", "Default")

    def __init__(
        self,
        *,
        use_account_balance: bool = True,
        capital_pct: float = 100.0,
        decimals: int = 0,
        lots_if_no_mm: float = 1.0,
        max_lots: float = 10000.0,
        UseAccountBalance: bool | None = None,  # noqa: N803
        MaxSize: float | None = None,  # noqa: N803
        Decimals: int | None = None,  # noqa: N803
        LotsIfNoMM: float | None = None,  # noqa: N803
        MaxLots: float | None = None,  # noqa: N803
    ) -> None:
        super().__init__()
        self.use_account_balance: bool = (
            UseAccountBalance if UseAccountBalance is not None else use_account_balance
        )
        self.capital_pct: float = capital_pct
        self.decimals: int = Decimals if Decimals is not None else decimals
        self.lots_if_no_mm: float = (
            LotsIfNoMM if LotsIfNoMM is not None else lots_if_no_mm
        )
        effective_max = MaxSize if MaxSize is not None else max_lots
        self.max_lots: float = MaxLots if MaxLots is not None else effective_max

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute shares from capital allocation and price (passed via pip_value)."""
        _ = stop_loss_pips
        price = pip_value
        if account_equity <= 0.0 or price <= 0.0 or self.capital_pct <= 0.0:
            result = round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            allocated = account_equity * (self.capital_pct / 100.0) * self.weight
            raw = allocated / price
            result = clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-MM-STOCKS-SIZE-BY-PRICE: StocksSizeByPrice=%f", result)
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
        if self.max_lots < 0:
            msg = (
                "Money management wasn't properly initialized. "
                "Call init() method before computing trade size!"
            )
            raise ValueError(msg)

        if price <= 0.0:
            return min(self.lots_if_no_mm, self.max_lots)

        capital = self.initial_capital
        if self.use_account_balance:
            if strategy is not None and hasattr(strategy, "get_account_balance"):
                capital = float(strategy.get_account_balance())
            elif strategy is not None and hasattr(strategy, "getAccountBalance"):
                capital = float(strategy.getAccountBalance())
        elif strategy is not None and hasattr(strategy, "get_initial_balance"):
            capital = float(strategy.get_initial_balance())
        elif strategy is not None and hasattr(strategy, "getInitialBalance"):
            capital = float(strategy.getInitialBalance())

        trade_size = (capital / price) * self.weight
        trade_size = round_lots(trade_size, size_step, self.decimals)
        if trade_size <= 0.0:
            trade_size = 1.0
        if self.max_lots > 0.0 and trade_size > self.max_lots:
            trade_size = self.max_lots
        logger.debug("FR-MM-STOCKS-SIZE-BY-PRICE: compute_trade_size=%f", trade_size)
        return trade_size


__all__ = ["StocksSizeByPrice"]
