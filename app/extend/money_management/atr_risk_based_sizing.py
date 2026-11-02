"""ATR risk-based position sizing money management snippet.

Description:
    Dynamically adjusts position size so that each trade risks a fixed percentage
    of account equity based on Average True Range (ATR) volatility.
Purpose:
    FEAT-MONEY-MANAGEMENT: Volatility-adjusted ATR risk position sizing.
Key Capabilities:
    - FR-MM-ATR-RISK-BASED-SIZING: ATR multiple stop distance risk sizing.
Python API Usage:
    from app.extend.money_management.atr_risk_based_sizing import ATRRiskBasedSizing
    sizer = ATRRiskBasedSizing(risk_in_pct=2.0, atr_period=14, atr_multiplier=2.0)
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


def _extract_atr(strategy: Any, symbol: str, period: int) -> float:
    """Safely extract ATR value from strategy or market data chart."""
    if strategy is None:
        return 0.0
    if hasattr(strategy, "get_atr_value"):
        return float(strategy.get_atr_value(symbol, period))
    if hasattr(strategy, "getATRValue"):
        try:
            chart_fn = getattr(strategy.MarketData, "Chart", lambda _s: None)
            chart = chart_fn(symbol)
            return float(strategy.getATRValue(chart, period, 1))
        except AttributeError, TypeError, ValueError:
            return 0.0
    return 0.0


class ATRRiskBasedSizing(BasePositionSizer):
    """ATR volatility risk-based position sizing (ATRRiskBasedSizing.java)."""

    name: str = "ATRRiskBasedSizing"
    display: str = (
        "ATR Risk-Based Sizing: Risk #Risk#% of equity, "
        "Stop = #ATRMult# x ATR(#ATRPeriod#)"
    )
    help_text: str = (
        "<b>ATR Risk-Based Position Sizing</b><br>"
        "Adjusts trade size so each trade risks a fixed % of equity "
        "based on ATR volatility."
    )
    description: str = "Risk-based position sizing using ATR."
    sort_order: int = 300
    for_engine: str = "*,-SP,-SA"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(
        self,
        *,
        risk_in_pct: float = 2.0,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        decimals: int = 2,
        lots_if_no_mm: float = 0.1,
        max_lots: float = 100.0,
        Risk: float | None = None,  # noqa: N803
        ATRPeriod: int | None = None,  # noqa: N803
        ATRMult: float | None = None,  # noqa: N803
        Decimals: int | None = None,  # noqa: N803
        LotsIfNoMM: float | None = None,  # noqa: N803
        MaxLots: float | None = None,  # noqa: N803
    ) -> None:
        super().__init__()
        self.risk_in_pct: float = Risk if Risk is not None else risk_in_pct
        self.atr_period: int = ATRPeriod if ATRPeriod is not None else atr_period
        self.atr_multiplier: float = ATRMult if ATRMult is not None else atr_multiplier
        self.decimals: int = Decimals if Decimals is not None else decimals
        self.lots_if_no_mm: float = (
            LotsIfNoMM if LotsIfNoMM is not None else lots_if_no_mm
        )
        self.max_lots: float = MaxLots if MaxLots is not None else max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute lots using ATR-scaled volatility distance (stop_loss_pips as ATR)."""
        effective_stop = stop_loss_pips * self.atr_multiplier
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
        logger.debug("FR-MM-ATR-RISK-BASED-SIZING: ATRRiskBasedSizing=%f", result)
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
        _ = (order_type, price, sl)
        if self.risk_in_pct < 0:
            msg = (
                "Money management wasn't properly initialized. "
                "Call init() method before computing trade size!"
            )
            raise ValueError(msg)

        atr_val = _extract_atr(strategy, symbol, self.atr_period)
        if atr_val <= 0.0 or tick_size <= 0.0 or point_value <= 0.0:
            return min(self.lots_if_no_mm, self.max_lots)

        stop_distance_ticks = (atr_val * self.atr_multiplier) / tick_size
        sl_in_money = stop_distance_ticks * tick_size * point_value
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
        logger.debug("FR-MM-ATR-RISK-BASED-SIZING: compute_trade_size=%f", trade_size)
        return trade_size


__all__ = ["ATRRiskBasedSizing"]
