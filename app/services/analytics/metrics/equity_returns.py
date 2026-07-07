# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100, ANN401, C901
"""Equity returns, resampling, and distribution calculations (ANL-NFR-181)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics._helpers import parse_utc_time
from app.services.analytics.contracts import MetricConfig, MetricResult

type TradeRecord = dict[str, Any]
type EquityPoint = dict[str, Any]
type ReturnPoint = Any
type SeriesPoint = dict[str, Any]


def _parse_equity_curve(equity_curve: Any) -> list[tuple[Any, float]]:
    """Convert an equity curve input to a sorted list of (datetime, equity) tuples."""
    if equity_curve is None:
        return []
    if hasattr(equity_curve, "to_dict"):
        records = equity_curve.to_dict("records")
    elif isinstance(equity_curve, list):
        records = equity_curve
    elif isinstance(equity_curve, tuple):
        records = list(equity_curve)
    else:
        return []

    result = []
    for r in records:
        if isinstance(r, dict):
            t_val = r.get("timestamp") or r.get("time") or r.get("date")
            eq_val = r.get("equity") or r.get("balance") or r.get("value")
            t_dt = parse_utc_time(t_val)
            if t_dt is not None and eq_val is not None:
                result.append((t_dt, float(eq_val)))
        elif isinstance(r, (tuple, list)) and len(r) >= 2:
            t_dt = parse_utc_time(r[0])
            if t_dt is not None and r[1] is not None:
                result.append((t_dt, float(r[1])))

    result.sort(key=lambda x: x[0])
    return result


def _group_returns(equity_curve: Any, bucket: str = "daily") -> list[float]:
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return []
    grouped: dict[str, float] = {}
    for dt, eq in parsed:
        if bucket == "daily":
            key = dt.strftime("%Y-%m-%d")
        elif bucket == "weekly":
            key = dt.strftime("%Y-%W")
        elif bucket == "monthly":
            key = dt.strftime("%Y-%m")
        else:
            key = dt.strftime("%Y")
        grouped[key] = eq
    sorted_vals = [eq for _, eq in sorted(grouped.items())]
    return returns_series(sorted_vals)


def returns_series(equity_values: Sequence[float]) -> list[float]:
    """Compute period-over-period simple returns."""
    if len(equity_values) < 2:
        return []
    series: list[float] = []
    for i in range(1, len(equity_values)):
        prev = equity_values[i - 1]
        if prev <= 0:
            series.append(0.0)
        else:
            series.append((equity_values[i] - prev) / prev)
    return series


def log_returns_series(equity_values: Sequence[float]) -> list[float]:
    """Compute period-over-period log returns."""
    if len(equity_values) < 2:
        return []
    series: list[float] = []
    for i in range(1, len(equity_values)):
        prev = equity_values[i - 1]
        curr = equity_values[i]
        if prev <= 0 or curr <= 0:
            series.append(0.0)
        else:
            series.append(math.log(curr / prev))
    return series


def geometric_mean_return(returns: Sequence[float]) -> float:
    """Compute the geometric mean of a return series."""
    if not returns:
        return 0.0
    product = 1.0
    for r in returns:
        product *= 1.0 + r
    if product <= 0:
        return 0.0
    return math.pow(product, 1.0 / len(returns)) - 1.0


def return_volatility(returns: Sequence[float]) -> float:
    """Compute sample standard deviation of a return series."""
    if len(returns) < 2:
        return 0.0
    avg = sum(returns) / len(returns)
    variance = sum((v - avg) ** 2 for v in returns) / (len(returns) - 1)
    return math.sqrt(variance)


def downside_return_volatility(
    returns: Sequence[float],
    target: float = 0.0,
) -> float:
    """Compute volatility of returns below a target."""
    downside = [v for v in returns if v < target]
    return return_volatility(downside)


def benchmark_returns(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Generate a return series from benchmark equity or price values (ANL-NFR-181)."""
    # Exposing as a metric wrapper
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=[])
    eq_vals = [eq for _, eq in parsed]
    val = returns_series(eq_vals)
    return MetricResult(value=val)


def total_return_usd(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total return in currency units from an equity curve (ANL-NFR-190)."""
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    val = parsed[-1][1] - parsed[0][1]
    return MetricResult(value=val)


def returns_series_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate percentage returns between equity points (ANL-NFR-191)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=[])
    eq_vals = [eq for _, eq in parsed]
    val = returns_series(eq_vals)
    return MetricResult(value=val)


def log_returns_series_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate logarithmic returns between equity points (ANL-NFR-192)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=[])
    eq_vals = [eq for _, eq in parsed]
    val = log_returns_series(eq_vals)
    return MetricResult(value=val)


def daily_returns(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate daily percentage returns from an equity curve (ANL-NFR-193)."""
    val = _group_returns(equity, "daily")
    return MetricResult(value=val)


def weekly_returns(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate weekly percentage returns from an equity curve (ANL-NFR-194)."""
    val = _group_returns(equity, "weekly")
    return MetricResult(value=val)


def monthly_returns(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate monthly percentage returns from an equity curve (ANL-NFR-195)."""
    val = _group_returns(equity, "monthly")
    return MetricResult(value=val)


def annual_returns(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate annual percentage returns from an equity curve (ANL-NFR-196)."""
    val = _group_returns(equity, "annual")
    return MetricResult(value=val)


def calculate_return_metrics(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate aggregate cumulative and average returns from an equity curve (ANL-NFR-197)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value={})
    eq_vals = [eq for _, eq in parsed]
    pct_returns = returns_series(eq_vals)
    # Total percentage return
    tot_ret = 0.0
    if len(parsed) >= 2 and parsed[0][1] > 0:
        tot_ret = ((parsed[-1][1] - parsed[0][1]) / parsed[0][1]) * 100.0
    avg_ret = sum(pct_returns) / len(pct_returns) if pct_returns else 0.0
    val = {
        "total_return_percent": tot_ret,
        "average_return_percent": avg_ret * 100.0,
        "total_return_usd": parsed[-1][1] - parsed[0][1],
    }
    return MetricResult(value=val)


def win_loss_streaks(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, list[int]]]:
    """Return winning and losing streak sequences (ANL-NFR-203)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value={"wins": [], "losses": []})
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    wins = []
    losses = []
    curr_win = 0
    curr_loss = 0
    for r in rets:
        if r > 0:
            curr_win += 1
            if curr_loss > 0:
                losses.append(curr_loss)
                curr_loss = 0
        elif r < 0:
            curr_loss += 1
            if curr_win > 0:
                wins.append(curr_win)
                curr_win = 0
        else:
            if curr_win > 0:
                wins.append(curr_win)
                curr_win = 0
            if curr_loss > 0:
                losses.append(curr_loss)
                curr_loss = 0
    if curr_win > 0:
        wins.append(curr_win)
    if curr_loss > 0:
        losses.append(curr_loss)
    return MetricResult(value={"wins": wins, "losses": losses})


def kelly_criterion(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate Kelly criterion percentage from R-multiples or returns (ANL-NFR-204)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    if not rets:
        return MetricResult(value=0.0)
    wins = [r for r in rets if r > 0]
    losses = [abs(r) for r in rets if r < 0]
    if not wins or not losses:
        return MetricResult(value=0.0)
    win_rate = len(wins) / len(rets)
    avg_win = sum(wins) / len(wins)
    avg_loss = sum(losses) / len(losses)
    payoff = avg_win / avg_loss if avg_loss > 0 else 0.0
    if payoff <= 0:
        return MetricResult(value=0.0)
    val = win_rate - (1.0 - win_rate) / payoff
    return MetricResult(value=val)


def avg_monthly_return(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate arithmetic average monthly return (ANL-NFR-205)."""
    m_returns = _group_returns(equity, "monthly")
    val = sum(m_returns) / len(m_returns) if m_returns else 0.0
    return MetricResult(value=val * 100.0)


def monthly_return_stddev(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate monthly return volatility (ANL-NFR-206)."""
    m_returns = _group_returns(equity, "monthly")
    val = return_volatility(m_returns)
    return MetricResult(value=val * 100.0)


def annualized_return(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate geometric annualized return (ANL-NFR-207)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    periods_per_year = int(config.annualization_periods if config else 252)
    if not rets:
        return MetricResult(value=0.0)
    product = 1.0
    for r in rets:
        product *= 1.0 + r
    if product <= 0:
        return MetricResult(value=0.0)
    val = (math.pow(product, periods_per_year / len(rets)) - 1.0) * 100.0
    return MetricResult(value=val)


def geometric_mean_return_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate geometric mean return (ANL-NFR-208)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    val = geometric_mean_return(rets)
    return MetricResult(value=val * 100.0)


def best_return(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate best single-period return (ANL-NFR-209)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    val = max(rets, default=0.0)
    return MetricResult(value=val * 100.0)


def worst_return(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate worst single-period return (ANL-NFR-210)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    val = min(rets, default=0.0)
    return MetricResult(value=val * 100.0)


def buy_and_hold_return(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total buy-and-hold return from price data (ANL-NFR-211)."""
    price_values = config.metadata.get("price_values", [])
    if len(price_values) < 2 or price_values[0] <= 0:
        return MetricResult(value=0.0)
    val = ((price_values[-1] - price_values[0]) / price_values[0]) * 100.0
    return MetricResult(value=val)


def return_volatility_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return standard deviation (ANL-NFR-212)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    val = return_volatility(rets)
    return MetricResult(value=val * 100.0)


def downside_return_volatility_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate volatility of returns below target (ANL-NFR-213)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    target = float(config.metadata.get("target_return", 0.0) if config else 0.0)
    val = downside_return_volatility(rets, target)
    return MetricResult(value=val * 100.0)


def return_skewness(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return-distribution skewness (ANL-NFR-214)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    if len(rets) < 3:
        return MetricResult(value=0.0)
    avg = sum(rets) / len(rets)
    std = return_volatility(rets)
    if std == 0:
        return MetricResult(value=0.0)
    val = sum(((v - avg) / std) ** 3 for v in rets) / len(rets)
    return MetricResult(value=val)


def return_kurtosis(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return-distribution excess kurtosis (ANL-NFR-215)."""
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    if len(rets) < 4:
        return MetricResult(value=0.0)
    avg = sum(rets) / len(rets)
    std = return_volatility(rets)
    if std == 0:
        return MetricResult(value=0.0)
    val = (sum(((v - avg) / std) ** 4 for v in rets) / len(rets)) - 3.0
    return MetricResult(value=val)


def return_on_account(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return on required account size (ANL-NFR-216)."""
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_prof = parsed[-1][1] - parsed[0][1]
    account_size = float(
        config.metadata.get("account_size", parsed[0][1]) if config else parsed[0][1]
    )
    if account_size <= 0:
        return MetricResult(value=0.0)
    val = (net_prof / account_size) * 100.0
    return MetricResult(value=val)
