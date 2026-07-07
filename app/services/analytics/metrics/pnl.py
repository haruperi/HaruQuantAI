# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""PnL, CAGR, and select/adjusted profit calculations (ANL-NFR-050)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.curves import balance_curve
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    classify_trades,
    get_closed_trades,
)

type TradeRecord = dict[str, Any]


def cagr(
    initial_value: float,
    final_value: float,
    years: float,
) -> float:
    """Compute compound annual growth rate (ANL-NFR-050)."""
    if initial_value <= 0 or final_value <= 0 or years <= 0:
        return 0.0
    return (math.pow(final_value / initial_value, 1.0 / years) - 1.0) * 100.0


def cagr_metric(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """CAGR metric from trades (ANL-NFR-050)."""
    closed = get_closed_trades(trades)
    initial_balance = float(
        config.metadata.get("initial_balance", 10000.0) if config else 10000.0
    )
    net_p = sum(_get_trade_pnl(t) for t in closed)
    final_balance = initial_balance + net_p
    years = float(config.metadata.get("years", 1.0) if config else 1.0)
    val = cagr(initial_balance, final_balance, years)
    return MetricResult(value=val)


def compound_monthly_growth_rate(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Compute compound monthly growth rate (ANL-NFR-051)."""
    closed = get_closed_trades(trades)
    initial_balance = float(
        config.metadata.get("initial_balance", 10000.0) if config else 10000.0
    )
    net_p = sum(_get_trade_pnl(t) for t in closed)
    final_balance = initial_balance + net_p
    months = float(config.metadata.get("months", 12.0) if config else 12.0)
    if initial_balance <= 0 or final_balance <= 0 or months <= 0:
        return MetricResult(value=0.0)
    val = (math.pow(final_balance / initial_balance, 1.0 / months) - 1.0) * 100.0
    return MetricResult(value=val)


def buy_and_hold_cagr(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Compute buy-and-hold CAGR from price data (ANL-NFR-052)."""
    price_values = config.metadata.get("price_values", [])
    years = float(config.metadata.get("years", 1.0) if config else 1.0)
    if len(price_values) < 2 or years <= 0:
        return MetricResult(value=0.0)
    val = cagr(price_values[0], price_values[-1], years)
    return MetricResult(value=val)


def adjusted_gross_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Sum winning PnL excluding extreme outliers (ANL-NFR-053)."""
    outlier_std_factor = float(
        config.metadata.get("outlier_std_factor", 3.0) if config else 3.0
    )
    wins = [_get_trade_pnl(t) for t in classify_trades(trades, config)["wins"]]
    if not wins:
        return MetricResult(value=0.0)
    avg = sum(wins) / len(wins)
    std = (
        math.sqrt(sum((x - avg) ** 2 for x in wins) / len(wins))
        if len(wins) > 1
        else 0.0
    )
    limit = avg + outlier_std_factor * std
    val = sum(x for x in wins if x <= limit)
    return MetricResult(value=val)


def adjusted_gross_loss(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Sum losing PnL excluding extreme outliers (ANL-NFR-054)."""
    outlier_std_factor = float(
        config.metadata.get("outlier_std_factor", 3.0) if config else 3.0
    )
    losses = [_get_trade_pnl(t) for t in classify_trades(trades, config)["losses"]]
    if not losses:
        return MetricResult(value=0.0)
    avg = sum(losses) / len(losses)
    std = (
        math.sqrt(sum((x - avg) ** 2 for x in losses) / len(losses))
        if len(losses) > 1
        else 0.0
    )
    limit = avg - outlier_std_factor * std
    val = sum(x for x in losses if x >= limit)
    return MetricResult(value=val)


def adjusted_net_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Compute net profit after removing outliers from both tails (ANL-NFR-055)."""
    g_profit = adjusted_gross_profit(trades, config).value or 0.0
    g_loss = adjusted_gross_loss(trades, config).value or 0.0
    val = g_profit + g_loss
    return MetricResult(value=val)


def select_net_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Compute net profit after trimming 2 % from each tail (ANL-NFR-056)."""
    pnls = sorted(_get_trade_pnl(t) for t in get_closed_trades(trades))
    if not pnls:
        return MetricResult(value=0.0)
    trim = int(len(pnls) * 0.02)
    trimmed = pnls[trim : len(pnls) - trim] if trim > 0 else pnls
    val = sum(trimmed)
    return MetricResult(value=val)


def select_gross_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Compute gross profit after trimming the top 2 % of wins (ANL-NFR-057)."""
    wins = sorted(_get_trade_pnl(t) for t in classify_trades(trades, config)["wins"])
    if not wins:
        return MetricResult(value=0.0)
    trim = int(len(wins) * 0.02)
    val = sum(wins[: len(wins) - trim] if trim > 0 else wins)
    return MetricResult(value=val)


def select_gross_loss(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Compute gross loss after trimming the bottom 2 % of losses (ANL-NFR-058)."""
    losses = sorted(
        _get_trade_pnl(t) for t in classify_trades(trades, config)["losses"]
    )
    if not losses:
        return MetricResult(value=0.0)
    trim = int(len(losses) * 0.02)
    val = sum(losses[trim:] if trim > 0 else losses)
    return MetricResult(value=val)


def max_runup(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Find the maximum gain from valley to peak (ANL-NFR-059)."""
    initial_balance = float(
        config.metadata.get("initial_balance", 10000.0) if config else 10000.0
    )
    curve = balance_curve(trades, initial_balance)
    if not curve:
        return MetricResult(value=0.0)
    equities = [c["equity"] for c in curve]
    running_min = equities[0]
    max_run = 0.0
    for eq in equities:
        running_min = min(running_min, eq)
        max_run = max(max_run, eq - running_min)
    return MetricResult(value=max_run)


def max_runup_date(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[str]:
    """Identify the timestamp of maximum runup peak (ANL-NFR-060)."""
    _fallback = "1970-01-01T00:00:00+00:00"
    initial_balance = float(
        config.metadata.get("initial_balance", 10000.0) if config else 10000.0
    )
    curve = balance_curve(trades, initial_balance)
    if not curve:
        return MetricResult(value=_fallback)
    equities = [c["equity"] for c in curve]
    running_min = equities[0]
    max_run = 0.0
    peak_idx = 0
    for i, eq in enumerate(equities):
        running_min = min(running_min, eq)
        run = eq - running_min
        if run > max_run:
            max_run = run
            peak_idx = i
    val = str(curve[peak_idx]["timestamp"])
    return MetricResult(value=val)


def total_return(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total return as a percentage of initial capital (ANL-NFR-077)."""
    closed = get_closed_trades(trades)
    net_p = sum(_get_trade_pnl(t) for t in closed)
    initial_balance = float(
        config.metadata.get("initial_balance", 10000.0) if config else 10000.0
    )
    if initial_balance <= 0:
        return MetricResult(value=0.0)
    val = (net_p / initial_balance) * 100.0
    return MetricResult(value=val)


def return_on_initial_capital(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit as a percentage of initial capital (ANL-NFR-078)."""
    return total_return(trades, config)


def return_over_drawdown(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total return relative to maximum trade drawdown (ANL-NFR-162)."""
    closed = get_closed_trades(trades)
    net_p = sum(_get_trade_pnl(t) for t in closed)
    # Using trade-level drawdowns to get max drawdown
    pnls = [_get_trade_pnl(t) for t in closed]
    running_peak = 0.0
    running_pnl = 0.0
    max_dd = 0.0
    for p in pnls:
        running_pnl += p
        running_peak = max(running_peak, running_pnl)
        max_dd = max(max_dd, running_peak - running_pnl)
    if max_dd <= 0:
        return MetricResult(value=0.0)
    val = net_p / max_dd
    return MetricResult(value=val)


def adjusted_net_profit_as_percent_of_max_trade_drawdown(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate adjusted net profit as a percentage of max trade drawdown (ANL-NFR-163)."""
    adj_net = adjusted_net_profit(trades, config).value or 0.0
    closed = get_closed_trades(trades)
    pnls = [_get_trade_pnl(t) for t in closed]
    running_peak = 0.0
    running_pnl = 0.0
    max_dd = 0.0
    for p in pnls:
        running_pnl += p
        running_peak = max(running_peak, running_pnl)
        max_dd = max(max_dd, running_peak - running_pnl)
    if max_dd <= 0:
        return MetricResult(value=0.0)
    val = (adj_net / max_dd) * 100.0
    return MetricResult(value=val)


def net_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total realized profit or loss from closed trades (ANL-NFR-164)."""
    closed = get_closed_trades(trades)
    val = sum(_get_trade_pnl(t) for t in closed)
    return MetricResult(value=val)


def gross_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Sum winning closed-trade profit (ANL-NFR-165)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    val = sum(_get_trade_pnl(t) for t in classes["wins"])
    return MetricResult(value=val)


def gross_loss(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Sum losing closed-trade loss (ANL-NFR-166)."""
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    val = sum(_get_trade_pnl(t) for t in classes["losses"])
    return MetricResult(value=val)
