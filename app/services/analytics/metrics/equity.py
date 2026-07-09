# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100, ANN401, C901, TRY301, BLE001, PLR0911
"""Equity returns, resampling, and distribution calculations (ANL-NFR-181)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.trade_outcomes import parse_utc_time
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger

type TradeRecord = dict[str, Any]
type EquityPoint = dict[str, Any]
type ReturnPoint = Any
type SeriesPoint = dict[str, Any]


def _parse_equity_curve(equity_curve: Any) -> list[tuple[Any, float]]:
    """Convert an equity curve input to a sorted list of (datetime, equity) tuples.

    Args:
        equity_curve (Any): Sequence of equity values or curve.

    Returns:
        Calculated list[tuple[Any, float]] value.
    """
    logger.debug("_parse_equity_curve: executed.")
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
    """Expose behavior for `_group_returns`.

    Args:
        equity_curve (Any): Sequence of equity values or curve.
        bucket (str): Input parameter `bucket`.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("_group_returns: executed.")
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
    """Compute period-over-period simple returns.

    Args:
        equity_values (Sequence[float]): Sequence of numeric values.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("returns_series: executed.")
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
    """Compute period-over-period log returns.

    Args:
        equity_values (Sequence[float]): Sequence of numeric values.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("log_returns_series: executed.")
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
    """Compute the geometric mean of a return series.

    Args:
        returns (Sequence[float]): Sequence of return floats.

    Returns:
        Calculated float value.
    """
    logger.debug("geometric_mean_return: executed.")
    if not returns:
        return 0.0
    product = 1.0
    for r in returns:
        product *= 1.0 + r
    if product <= 0:
        return 0.0
    return math.pow(product, 1.0 / len(returns)) - 1.0


def return_volatility(returns: Sequence[float]) -> float:
    """Compute sample standard deviation of a return series.

    Args:
        returns (Sequence[float]): Sequence of return floats.

    Returns:
        Calculated float value.
    """
    logger.debug("return_volatility: executed.")
    if len(returns) < 2:
        return 0.0
    avg = sum(returns) / len(returns)
    variance = sum((v - avg) ** 2 for v in returns) / (len(returns) - 1)
    return math.sqrt(variance)


def downside_return_volatility(
    returns: Sequence[float],
    target: float = 0.0,
) -> float:
    """Compute volatility of returns below a target.

    Args:
        returns (Sequence[float]): Sequence of return floats.
        target (float): Minimum acceptable return (MAR).

    Returns:
        Calculated float value.
    """
    logger.debug("downside_return_volatility: executed.")
    downside = [v for v in returns if v < target]
    return return_volatility(downside)


def benchmark_returns(
    price_values: Any,
    config: Any = None,
) -> Any:
    """Calculate returns of a benchmark series (ANL-NFR-192).

    Args:
        price_values: Sequence of price values.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated list[float] in V1 mode.
    """
    logger.debug("benchmark_returns: executed.")
    if config is not None and isinstance(config, MetricConfig):
        val = returns_series(price_values)
        return MetricResult(value=val)

    # V1 compatibility path
    return returns_series(price_values)


def total_return_usd(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate total return in currency units (ANL-NFR-190).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("total_return_usd: executed.")
    if config is not None and isinstance(config, MetricConfig):
        parsed = _parse_equity_curve(equity)
        if len(parsed) < 2:
            return MetricResult(value=0.0)
        val = parsed[-1][1] - parsed[0][1]
        return MetricResult(value=val)

    # V1 compatibility path
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return 0.0
    return parsed[-1][1] - parsed[0][1]


def returns_series_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate percentage returns between equity points (ANL-NFR-191).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated list[float value.
    """
    logger.debug("returns_series_metric: executed.")
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
    """Calculate logarithmic returns between equity points (ANL-NFR-192).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated list[float value.
    """
    logger.debug("log_returns_series_metric: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=[])
    eq_vals = [eq for _, eq in parsed]
    val = log_returns_series(eq_vals)
    return MetricResult(value=val)


def daily_returns(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate daily percentage returns from an equity curve (ANL-NFR-193).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated list[float] in V1 mode.
    """
    logger.debug("daily_returns: executed.")
    if config is not None and isinstance(config, MetricConfig):
        val = _group_returns(equity, "daily")
        return MetricResult(value=val)

    # V1 compatibility path
    return _group_returns(equity, "daily")


def weekly_returns(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate weekly percentage returns from an equity curve (ANL-NFR-194).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated list[float] in V1 mode.
    """
    logger.debug("weekly_returns: executed.")
    if config is not None and isinstance(config, MetricConfig):
        val = _group_returns(equity, "weekly")
        return MetricResult(value=val)

    # V1 compatibility path
    return _group_returns(equity, "weekly")


def monthly_returns(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate monthly percentage returns from an equity curve (ANL-NFR-195).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated list[float] in V1 mode.
    """
    logger.debug("monthly_returns: executed.")
    if config is not None and isinstance(config, MetricConfig):
        val = _group_returns(equity, "monthly")
        return MetricResult(value=val)

    # V1 compatibility path
    return _group_returns(equity, "monthly")


def annual_returns(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate annual percentage returns from an equity curve (ANL-NFR-196).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated list[float] in V1 mode.
    """
    logger.debug("annual_returns: executed.")
    if config is not None and isinstance(config, MetricConfig):
        val = _group_returns(equity, "annual")
        return MetricResult(value=val)

    # V1 compatibility path
    return _group_returns(equity, "annual")


def calculate_return_metrics(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate aggregate cumulative and average returns from an equity curve (ANL-NFR-197).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated dict in V1 mode.
    """
    logger.debug("calculate_return_metrics: executed.")
    if config is not None and isinstance(config, MetricConfig):
        parsed = _parse_equity_curve(equity)
        if not parsed:
            return MetricResult(value={})
        eq_vals = [eq for _, eq in parsed]
        pct_returns = returns_series(eq_vals)
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

    # V1 compatibility path
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return {}
    eq_vals = [eq for _, eq in parsed]
    pct_returns = returns_series(eq_vals)
    tot_ret = 0.0
    if len(parsed) >= 2 and parsed[0][1] > 0:
        tot_ret = ((parsed[-1][1] - parsed[0][1]) / parsed[0][1]) * 100.0
    avg_ret = sum(pct_returns) / len(pct_returns) if pct_returns else 0.0
    return {
        "total_return_percent": tot_ret,
        "average_return_percent": avg_ret * 100.0,
        "total_return_usd": parsed[-1][1] - parsed[0][1],
    }


def win_loss_streaks(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, list[int]]]:
    """Return winning and losing streak sequences (ANL-NFR-203).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, list[int value.
    """
    logger.debug("win_loss_streaks: executed.")
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
    """Calculate Kelly criterion percentage from R-multiples or returns (ANL-NFR-204).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("kelly_criterion: executed.")
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
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate arithmetic average monthly return (ANL-NFR-205).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("avg_monthly_return: executed.")
    if config is not None and isinstance(config, MetricConfig):
        m_returns = _group_returns(equity, "monthly")
        val = sum(m_returns) / len(m_returns) if m_returns else 0.0
        return MetricResult(value=val * 100.0)

    # V1 compatibility path
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return 0.0
    m_returns = _group_returns(equity, "monthly")
    return (sum(m_returns) / len(m_returns) if m_returns else 0.0) * 100.0


def monthly_return_stddev(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate monthly return volatility (ANL-NFR-206).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("monthly_return_stddev: executed.")
    if config is not None and isinstance(config, MetricConfig):
        m_returns = _group_returns(equity, "monthly")
        val = return_volatility(m_returns)
        return MetricResult(value=val * 100.0)

    # V1 compatibility path
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return 0.0
    m_returns = _group_returns(equity, "monthly")
    return return_volatility(m_returns) * 100.0


def annualized_return(
    equity_or_returns: Any,
    config_or_periods: Any = None,
) -> Any:
    """Calculate geometric annualized return.

    Args:
        equity_or_returns: Sequence of equity values/curve (V2) or period returns (V1).
        config_or_periods: MetricConfig (V2) or periods per year (V1).

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("annualized_return: executed.")
    if config_or_periods is not None and isinstance(config_or_periods, MetricConfig):
        parsed = _parse_equity_curve(equity_or_returns)
        if not parsed:
            return MetricResult(value=0.0)
        eq_vals = [eq for _, eq in parsed]
        rets = returns_series(eq_vals)
        periods_per_year = int(
            config_or_periods.annualization_periods if config_or_periods else 252
        )
        if not rets:
            return MetricResult(value=0.0)
        product = 1.0
        for r in rets:
            product *= 1.0 + r
        if product <= 0:
            return MetricResult(value=0.0)
        val = (math.pow(product, periods_per_year / len(rets)) - 1.0) * 100.0
        return MetricResult(value=val)

    # V1 compatibility path
    returns = equity_or_returns
    periods = 252 if config_or_periods is None else int(config_or_periods)
    if not returns:
        return 0.0
    product = 1.0
    for r in returns:
        product *= 1.0 + r
    if product <= 0:
        return 0.0
    return (math.pow(product, periods / len(returns)) - 1.0) * 100.0


def geometric_mean_return_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate geometric mean return (ANL-NFR-208).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("geometric_mean_return_metric: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    val = geometric_mean_return(rets)
    return MetricResult(value=val * 100.0)


def best_return(
    equity_or_returns: Any,
    config: Any = None,
) -> Any:
    """Calculate best single-period return (ANL-NFR-209).

    Args:
        equity_or_returns: Sequence of equity values/curve (V2) or period returns (V1).
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("best_return: executed.")
    if config is not None and isinstance(config, MetricConfig):
        parsed = _parse_equity_curve(equity_or_returns)
        if not parsed:
            return MetricResult(value=0.0)
        eq_vals = [eq for _, eq in parsed]
        rets = returns_series(eq_vals)
        val = max(rets, default=0.0)
        return MetricResult(value=val * 100.0)

    # V1 compatibility path
    returns = equity_or_returns
    return max(returns, default=0.0)


def worst_return(
    equity_or_returns: Any,
    config: Any = None,
) -> Any:
    """Calculate worst single-period return (ANL-NFR-210).

    Args:
        equity_or_returns: Sequence of equity values/curve (V2) or period returns (V1).
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("worst_return: executed.")
    if config is not None and isinstance(config, MetricConfig):
        parsed = _parse_equity_curve(equity_or_returns)
        if not parsed:
            return MetricResult(value=0.0)
        eq_vals = [eq for _, eq in parsed]
        rets = returns_series(eq_vals)
        val = min(rets, default=0.0)
        return MetricResult(value=val * 100.0)

    # V1 compatibility path
    returns = equity_or_returns
    return min(returns, default=0.0)


def buy_and_hold_return(
    equity_or_prices: Any,
    config: Any = None,
) -> Any:
    """Calculate total buy-and-hold return from price data (ANL-NFR-211).

    Args:
        equity_or_prices: Sequence of equity values/curve (V2) or price values (V1).
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("buy_and_hold_return: executed.")
    if config is not None and isinstance(config, MetricConfig):
        price_values = config.metadata.get("price_values", [])
        if len(price_values) < 2 or price_values[0] <= 0:
            return MetricResult(value=0.0)
        val = ((price_values[-1] - price_values[0]) / price_values[0]) * 100.0
        return MetricResult(value=val)

    # V1 compatibility path
    price_values = equity_or_prices
    if not price_values or len(price_values) < 2:
        return 0.0
    return ((price_values[-1] - price_values[0]) / price_values[0]) * 100.0


def return_volatility_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return standard deviation (ANL-NFR-212).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_volatility_metric: executed.")
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
    """Calculate volatility of returns below target (ANL-NFR-213).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("downside_return_volatility_metric: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    target = float(config.metadata.get("target_return", 0.0) if config else 0.0)
    val = downside_return_volatility(rets, target)
    return MetricResult(value=val * 100.0)


def return_skewness(
    equity_or_returns: Any,
    config: Any = None,
) -> Any:
    """Calculate return-distribution skewness (ANL-NFR-214).

    Args:
        equity_or_returns: Sequence of equity values/curve (V2) or period returns (V1).
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("return_skewness: executed.")
    if config is not None and isinstance(config, MetricConfig):
        parsed = _parse_equity_curve(equity_or_returns)
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

    # V1 compatibility path
    returns = equity_or_returns
    from app.services.analytics.metrics.distribution import skewness

    return skewness(returns)


def return_kurtosis(
    equity_or_returns: Any,
    config: Any = None,
) -> Any:
    """Calculate return-distribution excess kurtosis (ANL-NFR-215).

    Args:
        equity_or_returns: Sequence of equity values/curve (V2) or period returns (V1).
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("return_kurtosis: executed.")
    if config is not None and isinstance(config, MetricConfig):
        parsed = _parse_equity_curve(equity_or_returns)
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

    # V1 compatibility path
    returns = equity_or_returns
    from app.services.analytics.metrics.distribution import kurtosis

    return kurtosis(returns)


def return_on_account(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return on required account size (ANL-NFR-216).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_on_account: executed.")
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


def validate_request_id_strict(request_id: str | None) -> None:
    """Raise ``ValidationError`` when ``request_id`` is present but invalid.

    ``None`` is accepted (the field is optional).  A non-``None`` value must
    be a non-empty, non-whitespace string.
    """
    if request_id is None:
        logger.debug(
            "validate_request_id_strict: request_id is None, skipping validation."
        )
        return
    if not isinstance(request_id, str) or not request_id.strip():
        logger.warning("validate_request_id_strict: invalid request_id supplied.")
        raise ValidationError("request_id must be a non-empty string when supplied.")
    logger.debug("validate_request_id_strict: request_id successfully validated.")


def compute_equity_metrics(returns: list[float]) -> dict[str, Any]:
    """Compute equity metrics from a pre-computed return series.

    Args:
        returns: Decimal period-return series.

    Returns:
        Dict with ``total_return`` and ``return_volatility``; fallback
        zeros when ``returns`` is empty.

    Side effects:
        None.
    """
    logger.debug("compute_equity_metrics: executed.")
    if not returns:
        return {"total_return": 0.0, "return_volatility": 0.0}
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    vol = return_volatility(returns)
    return {
        "total_return": ((eq[-1] - eq[0]) / eq[0]) * 100.0,
        "return_volatility": vol * 100.0,
    }


def calculate_equity_metrics(
    equity_curve: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate aggregate return and drawdown metrics from an equity curve.

    Args:
        equity_curve: Equity curve in any supported format.
        request_id: Optional trace identifier.

    Returns:
        ``StandardResponse`` containing equity and drawdown metrics.

    Raises:
        ValidationError: When ``equity_curve`` contains no valid data
            points.  Caught internally and returned as an error response.

    Side effects:
        None.
    """
    logger.debug("calculate_equity_metrics: executed.")
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="calculate_equity_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        parsed = _parse_equity_curve(equity_curve)
        if not parsed:
            raise ValidationError(
                "equity_curve must contain at least one valid data point."
            )
        equities = [eq for _, eq in parsed]
        if not any(eq > 0 for eq in equities):
            raise ValidationError(
                "equity_curve must contain at least one positive equity value."
            )
        ret_metrics = calculate_return_metrics(equity_curve)

        from app.services.analytics.metrics.drawdown import calculate_drawdown_metrics

        dd_metrics = calculate_drawdown_metrics(equity_curve)

        pct_returns = returns_series(equities)
        from app.services.analytics.metrics.distribution import kurtosis, skewness

        data = {
            "total_return_percent": ret_metrics.get("total_return_percent", 0.0),
            "total_return_usd": ret_metrics.get("total_return_usd", 0.0),
            "average_return_percent": ret_metrics.get("average_return_percent", 0.0),
            "max_drawdown_percent": dd_metrics.get("max_drawdown_percent", 0.0),
            "max_drawdown_duration_hours": dd_metrics.get(
                "max_drawdown_duration_hours", 0.0
            ),
            "avg_underwater_drawdown_percent": dd_metrics.get(
                "avg_underwater_drawdown_percent", 0.0
            ),
            "max_drawdown_date": dd_metrics.get(
                "max_drawdown_date",
                "1970-01-01T00:00:00+00:00",
            ),
            "return_volatility": return_volatility(pct_returns) * 100.0,
            "return_skewness": skewness(pct_returns),
            "return_kurtosis": kurtosis(pct_returns),
        }
        return success_response(
            message="Successfully calculated equity metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as exc:
        return response_from_exception(exception=exc, metadata=meta)
