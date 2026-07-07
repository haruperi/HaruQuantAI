# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100, ANN401
"""Drawdown statistics, underwater series, recovery duration, and ratios (ANL-NFR-115)."""

from __future__ import annotations

import collections
import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics._helpers import parse_utc_time
from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.efficiency import _sorted_median
from app.services.analytics.metrics.equity_returns import (
    _parse_equity_curve,
    return_volatility,
    returns_series,
)
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    get_closed_trades,
    get_ordered_closed_trades,
)

type TradeRecord = dict[str, Any]
type EquityPoint = Any
type ReturnPoint = Any


def drawdown_series(equity_values: Sequence[float]) -> list[float]:
    """Compute peak-to-trough fractional drawdown series."""
    if not equity_values:
        return []
    peak = equity_values[0]
    series: list[float] = []
    for eq in equity_values:
        peak = max(peak, eq)
        if peak <= 0:
            series.append(0.0)
        else:
            series.append((peak - eq) / peak)
    return series


def drawdown_duration_series(equity_curve: Any) -> list[float]:
    """Compute hours-since-peak drawdown duration at each equity point."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return []
    durations: list[float] = []
    peak = parsed[0][1]
    peak_time = parsed[0][0]
    for dt, eq in parsed:
        if eq >= peak:
            peak = eq
            peak_time = dt
            durations.append(0.0)
        else:
            durations.append((dt - peak_time).total_seconds() / 3600.0)
    return durations


def trade_pnl_distribution(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate a statistical summary of realized trade PnL (ANL-NFR-115)."""
    # Note: Expects trades sequence from config or input_value.
    # We will extract closed trades and compute mean/std/min/max/median.
    trades = config.metadata.get("trades", [])
    pnls = sorted(_get_trade_pnl(t) for t in get_closed_trades(trades))
    if not pnls:
        return MetricResult(value={})
    n = len(pnls)
    mean = sum(pnls) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in pnls) / max(n - 1, 1))
    val = {
        "mean": mean,
        "std": std,
        "min": pnls[0],
        "max": pnls[-1],
        "median": _sorted_median(pnls),
    }
    return MetricResult(value=val)


def trade_level_drawdowns(
    trades: Sequence[TradeRecord],
) -> list[float]:
    """Compute balance-drawdown series at each trade close (ANL-NFR-116)."""
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return []
    balance = 10000.0
    balances = [balance]
    for t in closed:
        balance += _get_trade_pnl(t)
        balances.append(balance)
    peak = balances[0]
    drawdowns = []
    for b in balances:
        peak = max(peak, b)
        drawdowns.append(peak - b)
    return drawdowns


def trade_level_drawdowns_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Expose trade_level_drawdowns as a metric (ANL-NFR-116)."""
    trades = config.metadata.get("trades", [])
    val = trade_level_drawdowns(trades)
    return MetricResult(value=val)


def max_close_to_close_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum trade-level peak-to-valley decline (ANL-NFR-117)."""
    trades = config.metadata.get("trades", [])
    val = max(trade_level_drawdowns(trades), default=0.0)
    return MetricResult(value=val)


def avg_trade_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate mean trade-level close-to-close drawdown depth (ANL-NFR-118)."""
    trades = config.metadata.get("trades", [])
    dds = trade_level_drawdowns(trades)
    val = sum(dds) / len(dds) if dds else 0.0
    return MetricResult(value=val)


def max_consecutive_drawdown_trades(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[int]:
    """Calculate maximum number of consecutive trades inside drawdown (ANL-NFR-119)."""
    trades = config.metadata.get("trades", [])
    dds = trade_level_drawdowns(trades)
    max_con = 0
    curr_con = 0
    for d in dds:
        if d > 0:
            curr_con += 1
            max_con = max(max_con, curr_con)
        else:
            curr_con = 0
    return MetricResult(value=max_con)


def max_close_to_close_drawdown_date(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[str]:
    """Identify the timestamp of deepest trade-level valley (ANL-NFR-120)."""
    _fallback = "1970-01-01T00:00:00+00:00"
    trades = config.metadata.get("trades", [])
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return MetricResult(value=_fallback)
    dds = trade_level_drawdowns(trades)
    if not dds:
        return MetricResult(value=_fallback)
    max_dd = max(dds)
    max_idx = dds.index(max_dd)
    if max_idx == 0:
        return MetricResult(value=_fallback)
    t = closed[max_idx - 1]
    ct_raw = t.get("close_time") or t.get("close_timestamp")
    dt = parse_utc_time(ct_raw)
    val = dt.isoformat() if dt else _fallback
    return MetricResult(value=val)


def relative_drawdown_series(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Generate relative underperformance between strategy and benchmark (ANL-NFR-182)."""
    parsed_strat = _parse_equity_curve(equity)
    benchmark_equity = config.metadata.get("benchmark_equity", [])
    parsed_bench = _parse_equity_curve(benchmark_equity)
    if not parsed_strat or not parsed_bench:
        return MetricResult(value=[])
    # Align length
    n = min(len(parsed_strat), len(parsed_bench))
    rel_dd = []
    strat_vals = [x[1] for x in parsed_strat[:n]]
    bench_vals = [x[1] for x in parsed_bench[:n]]
    # Normalized relative underperformance
    strat_dd = drawdown_series(strat_vals)
    bench_dd = drawdown_series(bench_vals)
    for i in range(n):
        rel_dd.append(max(0.0, strat_dd[i] - bench_dd[i]))
    return MetricResult(value=rel_dd)


def drawdown_series_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate drawdown values from an equity curve (ANL-NFR-183)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=[])
    eq_vals = [eq for _, eq in parsed]
    val = drawdown_series(eq_vals)
    return MetricResult(value=val)


def drawdown_duration_series_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate drawdown duration values from an equity curve (ANL-NFR-184)."""
    val = drawdown_duration_series(equity)
    return MetricResult(value=val)


def max_drawdown_duration_from_equity(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum drawdown duration from equity values (ANL-NFR-185)."""
    val = max(drawdown_duration_series(equity), default=0.0)
    return MetricResult(value=val)


def max_strategy_drawdown_date(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[str]:
    """Identify the timestamp of deepest strategy equity valley (ANL-NFR-186)."""
    _fallback = "1970-01-01T00:00:00+00:00"
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=_fallback)
    equities = [eq for _, eq in parsed]
    if not equities:
        return MetricResult(value=_fallback)
    peak = equities[0]
    max_dd = 0.0
    valley_idx = 0
    for i, eq in enumerate(equities):
        peak = max(peak, eq)
        if peak > 0:
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
                valley_idx = i
    val = parsed[valley_idx][0].isoformat()
    return MetricResult(value=val)


def avg_underwater_drawdown_percent(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average drawdown depth while equity is below peak (ANL-NFR-187)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    active_dds = [d for d in dds if d > 0]
    val = (sum(active_dds) / len(active_dds)) * 100.0 if active_dds else 0.0
    return MetricResult(value=val)


def calculate_drawdown_metrics(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, Any]]:
    """Calculate aggregate drawdown metrics from an equity curve (ANL-NFR-188)."""
    max_dd = max_strategy_drawdown_percent(equity, config).value or 0.0
    avg_dd = avg_drawdown(equity, config).value or 0.0
    max_dur = max_drawdown_duration(equity, config).value or 0.0
    underwater = avg_underwater_drawdown_percent(equity, config).value or 0.0
    val = {
        "max_drawdown_percent": max_dd,
        "avg_drawdown_percent": avg_dd,
        "max_drawdown_duration_hours": max_dur,
        "avg_underwater_drawdown_percent": underwater,
        "max_drawdown_date": max_strategy_drawdown_date(equity, config).value or "",
    }
    return MetricResult(value=val)


def max_relative_drawdown_percent(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum relative underperformance as a positive percentage (ANL-NFR-220)."""
    res = relative_drawdown_series(equity, config)
    val = max(res.value, default=0.0) * 100.0 if res.value else 0.0
    return MetricResult(value=val)


def max_strategy_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate deepest peak-to-valley decline in currency units (ANL-NFR-221)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    peak = parsed[0][1]
    max_dd = 0.0
    for _, eq in parsed:
        peak = max(peak, eq)
        max_dd = max(max_dd, peak - eq)
    return MetricResult(value=max_dd)


def max_strategy_drawdown_percent(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate deepest percentage decline relative to running peak (ANL-NFR-222)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    peak = parsed[0][1]
    max_dd = 0.0
    for _, eq in parsed:
        peak = max(peak, eq)
        if peak > 0:
            max_dd = max(max_dd, (peak - eq) / peak)
    val = max_dd * 100.0
    return MetricResult(value=val)


def max_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum drawdown from returns (ANL-NFR-223)."""
    return max_strategy_drawdown_percent(equity, config)


def avg_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average drawdown depth (ANL-NFR-224)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    active_dds = [d for d in dds if d > 0]
    val = (sum(active_dds) / len(active_dds)) * 100.0 if active_dds else 0.0
    return MetricResult(value=val)


def drawdown_distribution(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate detailed drawdown distribution statistics (ANL-NFR-225)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value={})
    equities = [eq for _, eq in parsed]
    dds = sorted(drawdown_series(equities))
    if not dds:
        return MetricResult(value={})
    n = len(dds)
    mean = sum(dds) / n
    val = {
        "mean": mean * 100.0,
        "std": return_volatility(dds) * 100.0,
        "max": dds[-1] * 100.0,
        "median": _sorted_median(dds) * 100.0,
    }
    return MetricResult(value=val)


def max_drawdown_duration_from_returns(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum drawdown duration from return values (ANL-NFR-226)."""
    return max_drawdown_duration(equity, config)


def max_drawdown_duration(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum drawdown duration (ANL-NFR-227)."""
    val = max(drawdown_duration_series(equity), default=0.0)
    return MetricResult(value=val)


def avg_drawdown_duration(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average duration of drawdown episodes (ANL-NFR-228)."""
    durs = drawdown_duration_series(equity)
    if not durs:
        return MetricResult(value=0.0)
    # Collect distinct underwater episode durations
    episodes = []
    curr_dur = 0.0
    for d in durs:
        if d > 0:
            curr_dur = d
        elif curr_dur > 0:
            episodes.append(curr_dur)
            curr_dur = 0.0
    if curr_dur > 0:
        episodes.append(curr_dur)
    val = sum(episodes) / len(episodes) if episodes else 0.0
    return MetricResult(value=val)


def time_to_recovery(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate recovery periods for unique drawdowns (ANL-NFR-229)."""
    durs = drawdown_duration_series(equity)
    episodes = []
    curr_dur = 0.0
    for d in durs:
        if d > 0:
            curr_dur = d
        elif curr_dur > 0:
            episodes.append(curr_dur)
            curr_dur = 0.0
    if curr_dur > 0:
        episodes.append(curr_dur)
    return MetricResult(value=episodes)


def recovery_factor(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit relative to maximum drawdown (ANL-NFR-230)."""
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    max_dd = max_strategy_drawdown(equity, config).value or 0.0
    val = net_p / max_dd if max_dd > 0 else 0.0
    return MetricResult(value=val)


def max_close_to_close_drawdown_percent(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate close-to-close drawdown as a percentage (ANL-NFR-231)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    val = max(dds, default=0.0) * 100.0
    return MetricResult(value=val)


def account_size_required(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Estimate capital required to withstand max close-to-close dips (ANL-NFR-232)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    # Estimate capital based on max strategy drawdown + 10% safety buffer
    max_dd = max_strategy_drawdown(equity, config).value or 0.0
    val = max_dd * 1.10
    return MetricResult(value=val)


def avg_yearly_max_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Average the maximum drawdown observed in each year (ANL-NFR-233)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    by_year: dict[int, list[tuple[Any, float]]] = collections.defaultdict(list)
    for dt, eq in parsed:
        by_year[dt.year].append((dt, eq))
    yearly_dds = [
        max_strategy_drawdown_percent(curve, config).value or 0.0
        for curve in by_year.values()
    ]
    val = sum(yearly_dds) / len(yearly_dds) if yearly_dds else 0.0
    return MetricResult(value=val)


def ulcer_index(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate squared-drawdown-based ulcer index (ANL-NFR-234)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return MetricResult(value=0.0)
    val = math.sqrt(sum(d**2 for d in dds) / len(dds)) * 100.0
    return MetricResult(value=val)


def pain_index(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate mean absolute percentage drawdown (ANL-NFR-235)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return MetricResult(value=0.0)
    val = (sum(dds) / len(dds)) * 100.0
    return MetricResult(value=val)


def pain_ratio(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return relative to pain index (ANL-NFR-236)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    periods_per_year = int(config.annualization_periods if config else 252)
    product = 1.0
    for r in rets:
        product *= 1.0 + r
    ann_ret = (
        (math.pow(product, periods_per_year / len(rets)) - 1.0) * 100.0
        if rets and product > 0
        else 0.0
    )
    pain_idx = pain_index(equity, config).value or 0.0
    if pain_idx <= 0:
        return MetricResult(value=0.0)
    val = ann_ret / pain_idx
    return MetricResult(value=val)


def calmar_ratio(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate annualized return relative to maximum drawdown (ANL-NFR-237)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    periods_per_year = int(config.annualization_periods if config else 252)
    product = 1.0
    for r in rets:
        product *= 1.0 + r
    ann_ret = (
        (math.pow(product, periods_per_year / len(rets)) - 1.0) * 100.0
        if rets and product > 0
        else 0.0
    )
    max_dd = max_strategy_drawdown_percent(equity, config).value or 0.0
    if max_dd <= 0:
        return MetricResult(value=0.0)
    val = ann_ret / max_dd
    return MetricResult(value=val)


def fouse_ratio(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate Fouse drawdown-index-style ratio (ANL-NFR-238)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    periods_per_year = int(config.annualization_periods if config else 252)
    product = 1.0
    for r in rets:
        product *= 1.0 + r
    ann_ret = (
        (math.pow(product, periods_per_year / len(rets)) - 1.0) * 100.0
        if rets and product > 0
        else 0.0
    )
    ulcer = ulcer_index(equity, config).value or 0.0
    if ulcer <= 0:
        return MetricResult(value=0.0)
    val = ann_ret / ulcer
    return MetricResult(value=val)


def sterling_ratio(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate CAGR relative to adjusted average yearly maximum drawdown (ANL-NFR-239)."""
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    initial_balance = parsed[0][1]
    net_p = parsed[-1][1] - parsed[0][1]
    final_balance = initial_balance + net_p
    years = float(config.metadata.get("years", 1.0) if config else 1.0)
    cagr_val = 0.0
    if initial_balance > 0 and final_balance > 0 and years > 0:
        cagr_val = (
            math.pow(final_balance / initial_balance, 1.0 / years) - 1.0
        ) * 100.0
    avg_yearly_max_dd = avg_yearly_max_drawdown(equity, config).value or 0.0
    denom = avg_yearly_max_dd + 10.0  # standard Sterling adjustment adds 10%
    if denom <= 0:
        return MetricResult(value=0.0)
    val = cagr_val / denom
    return MetricResult(value=val)


def rina_index(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate select net profit relative to average drawdown and time in market (ANL-NFR-240)."""
    # Exposing placeholder for RINA index calculation
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    avg_dd = avg_drawdown(equity, config).value or 0.0
    if avg_dd <= 0:
        return MetricResult(value=0.0)
    val = net_p / avg_dd
    return MetricResult(value=val)


def adjusted_net_profit_as_percent_of_max_strategy_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate adjusted net profit as a percentage of max strategy drawdown (ANL-NFR-241)."""
    # Under metrics rules we extract adj_net_profit
    trades = config.metadata.get("trades", [])
    from app.services.analytics.metrics.pnl import adjusted_net_profit

    adj_net = adjusted_net_profit(trades, config).value or 0.0
    max_dd = max_strategy_drawdown(equity, config).value or 0.0
    if max_dd <= 0:
        return MetricResult(value=0.0)
    val = (adj_net / max_dd) * 100.0
    return MetricResult(value=val)


def return_on_max_strategy_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total return relative to maximum strategy drawdown (ANL-NFR-242)."""
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    max_dd = max_strategy_drawdown(equity, config).value or 0.0
    if max_dd <= 0:
        return MetricResult(value=0.0)
    val = (net_p / max_dd) * 100.0
    return MetricResult(value=val)


def return_on_max_close_to_close_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit relative to maximum close-to-close drawdown (ANL-NFR-243)."""
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    trades = config.metadata.get("trades", [])
    max_close_dd = max(trade_level_drawdowns(trades), default=0.0)
    if max_close_dd <= 0:
        return MetricResult(value=0.0)
    val = net_p / max_close_dd
    return MetricResult(value=val)


def drawdown_probability(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probability of drawdown exceeding a threshold (ANL-NFR-244)."""
    threshold = float(
        config.metadata.get("drawdown_threshold", 0.10) if config else 0.10
    )
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return MetricResult(value=0.0)
    exceeded = sum(1 for d in dds if d >= threshold)
    val = exceeded / len(dds)
    return MetricResult(value=val)
