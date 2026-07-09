# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100, ANN401, TRY301, BLE001
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
from app.utils.logger import logger

type TradeRecord = dict[str, Any]


def cagr(
    initial_value: float,
    final_value: float,
    years: float,
) -> float:
    """Compute compound annual growth rate (ANL-NFR-050).

    Args:
        initial_value (float): Input parameter `initial_value`.
        final_value (float): Input parameter `final_value`.
        years (float): Input parameter `years`.

    Returns:
        Calculated float value.
    """
    logger.debug("cagr: executed.")
    if initial_value <= 0 or final_value <= 0 or years <= 0:
        return 0.0
    return (math.pow(final_value / initial_value, 1.0 / years) - 1.0) * 100.0


def cagr_metric(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """CAGR metric from trades (ANL-NFR-050).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("cagr_metric: executed.")
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
    trades_or_initial: Any,
    config_or_final: Any = None,
    months: Any = None,
) -> Any:
    """Compute compound monthly growth rate (ANL-NFR-051).

    Args:
        trades_or_initial: Sequence of trade record dictionaries or initial value.
        config_or_final: MetricConfig for V2, or final value for V1.
        months: Months duration for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("compound_monthly_growth_rate: executed.")
    if config_or_final is not None and isinstance(config_or_final, MetricConfig):
        trades = trades_or_initial
        config = config_or_final
        closed = get_closed_trades(trades)
        initial_balance = float(
            config.metadata.get("initial_balance", 10000.0) if config else 10000.0
        )
        net_p = sum(_get_trade_pnl(t) for t in closed)
        final_balance = initial_balance + net_p
        months_val = float(config.metadata.get("months", 12.0) if config else 12.0)
        if initial_balance <= 0 or final_balance <= 0 or months_val <= 0:
            return MetricResult(value=0.0)
        val = (
            math.pow(final_balance / initial_balance, 1.0 / months_val) - 1.0
        ) * 100.0
        return MetricResult(value=val)

    # V1 compatibility path
    initial_value = trades_or_initial
    final_value = config_or_final
    if initial_value is None or final_value is None or months is None:
        return 0.0
    if float(months) <= 0 or float(initial_value) <= 0 or float(final_value) <= 0:
        return 0.0
    return (
        math.pow(float(final_value) / float(initial_value), 1.0 / float(months)) - 1.0
    ) * 100.0


def buy_and_hold_cagr(
    trades_or_prices: Any,
    config_or_years: Any = None,
) -> Any:
    """Compute buy-and-hold CAGR from price data (ANL-NFR-052).

    Args:
        trades_or_prices: Sequence of trade records or price values sequence.
        config_or_years: MetricConfig for V2, or years for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("buy_and_hold_cagr: executed.")
    if config_or_years is not None and isinstance(config_or_years, MetricConfig):
        config = config_or_years
        price_values = config.metadata.get("price_values", [])
        years = float(config.metadata.get("years", 1.0) if config else 1.0)
        if len(price_values) < 2 or years <= 0:
            return MetricResult(value=0.0)
        val = cagr(price_values[0], price_values[-1], years)
        return MetricResult(value=val)

    # V1 compatibility path
    price_values = trades_or_prices
    years_val = config_or_years
    if not price_values or len(price_values) < 2 or years_val is None or years_val <= 0:
        return 0.0
    return cagr(price_values[0], price_values[-1], years_val)


def adjusted_gross_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Sum winning PnL excluding extreme outliers (ANL-NFR-053).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("adjusted_gross_profit: executed.")
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
    """Sum losing PnL excluding extreme outliers (ANL-NFR-054).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("adjusted_gross_loss: executed.")
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
    """Compute net profit after removing outliers from both tails (ANL-NFR-055).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("adjusted_net_profit: executed.")
    g_profit = adjusted_gross_profit(trades, config).value or 0.0
    g_loss = adjusted_gross_loss(trades, config).value or 0.0
    val = g_profit + g_loss
    return MetricResult(value=val)


def select_net_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Compute net profit after trimming 2 % from each tail (ANL-NFR-056).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("select_net_profit: executed.")
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
    """Compute gross profit after trimming the top 2 % of wins (ANL-NFR-057).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("select_gross_profit: executed.")
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
    """Compute gross loss after trimming the bottom 2 % of losses (ANL-NFR-058).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("select_gross_loss: executed.")
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
    """Find the maximum gain from valley to peak (ANL-NFR-059).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_runup: executed.")
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
    """Identify the timestamp of maximum runup peak (ANL-NFR-060).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated str value.
    """
    logger.debug("max_runup_date: executed.")
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
    trades_or_equity: Any,
    config: Any = None,
) -> Any:
    """Calculate total return as a percentage of initial capital (ANL-NFR-077).

    Args:
        trades_or_equity: Sequence of trade records or equity curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("total_return: executed.")
    if config is not None and isinstance(config, MetricConfig):
        closed = get_closed_trades(trades_or_equity)
        net_p = sum(_get_trade_pnl(t) for t in closed)
        initial_balance = float(
            config.metadata.get("initial_balance", 10000.0) if config else 10000.0
        )
        if initial_balance <= 0:
            return MetricResult(value=0.0)
        val = (net_p / initial_balance) * 100.0
        return MetricResult(value=val)

    # V1 compatibility path
    from app.services.analytics.metrics.equity import _parse_equity_curve

    parsed = _parse_equity_curve(trades_or_equity)
    if len(parsed) < 2:
        return 0.0
    return ((parsed[-1][1] - parsed[0][1]) / parsed[0][1]) * 100.0


def return_on_initial_capital(
    trades_or_equity: Any,
    config: Any = None,
) -> Any:
    """Calculate net profit as a percentage of initial capital (ANL-NFR-078).

    Args:
        trades_or_equity: Sequence of trade records or equity curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("return_on_initial_capital: executed.")
    if config is not None and isinstance(config, MetricConfig):
        return total_return(trades_or_equity, config)

    # V1 compatibility path
    return total_return(trades_or_equity, None)


def return_over_drawdown(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total return relative to maximum trade drawdown (ANL-NFR-162).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_over_drawdown: executed.")
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
    """Calculate adjusted net profit as a percentage of max trade drawdown (ANL-NFR-163).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("adjusted_net_profit_as_percent_of_max_trade_drawdown: executed.")
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
    """Calculate total realized profit or loss from closed trades (ANL-NFR-164).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("net_profit: executed.")
    closed = get_closed_trades(trades)
    val = sum(_get_trade_pnl(t) for t in closed)
    return MetricResult(value=val)


def gross_profit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Sum winning closed-trade profit (ANL-NFR-165).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("gross_profit: executed.")
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    val = sum(_get_trade_pnl(t) for t in classes["wins"])
    return MetricResult(value=val)


def gross_loss(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Sum losing closed-trade loss (ANL-NFR-166).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("gross_loss: executed.")
    closed = get_closed_trades(trades)
    classes = classify_trades(closed, config)
    val = sum(_get_trade_pnl(t) for t in classes["losses"])
    return MetricResult(value=val)
