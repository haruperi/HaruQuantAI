# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Ratio and performance index calculations (ANL-NFR-218)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.services.analytics.metrics.drawdown import (
    ulcer_index,
)
from app.services.analytics.metrics.equity import (
    _parse_equity_curve,
    return_volatility,
)
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    avg_loss,
    avg_win,
    classify_trades,
    get_closed_trades,
)
from app.utils import StandardResponse  # noqa: TC001
from app.utils.logger import logger

type ReturnPoint = Any
type TradeRecord = dict[str, Any]


def _parse_returns(returns: Sequence[ReturnPoint | float]) -> list[float]:
    """Expose behavior for `_parse_returns`.

    Args:
        returns (Sequence[ReturnPoint | float]): Sequence of return floats.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("_parse_returns: executed.")
    res = []
    for r in returns:
        if isinstance(r, (float, int)):
            res.append(float(r))
        elif isinstance(r, dict):
            val = r.get("return") or r.get("value") or r.get("pnl") or 0.0
            res.append(float(val))
    return res


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function.

    Args:
        x (float): Input parameter `x`.

    Returns:
        Calculated float value.
    """
    logger.debug("normal_cdf: executed.")
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def sharpe_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate reward-to-variability Sharpe ratio (ANL-NFR-218).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("sharpe_ratio: executed.")
    ret_list = _parse_returns(returns)
    if len(ret_list) < 2:
        return MetricResult(value=0.0)
    risk_free_rate = float(
        config.metadata.get("risk_free_rate", 0.0) if config else 0.0
    )
    mean_ret = sum(ret_list) / len(ret_list)
    excess = mean_ret - risk_free_rate
    std_ret = return_volatility(ret_list)
    if std_ret == 0:
        return MetricResult(value=0.0)
    val = excess / std_ret
    return MetricResult(value=val)


def sortino_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return relative to downside deviation Sortino ratio (ANL-NFR-219).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("sortino_ratio: executed.")
    ret_list = _parse_returns(returns)
    if len(ret_list) < 2:
        return MetricResult(value=0.0)
    risk_free_rate = float(
        config.metadata.get("risk_free_rate", 0.0) if config else 0.0
    )
    float(config.metadata.get("target_return", 0.0) if config else 0.0)
    mean_ret = sum(ret_list) / len(ret_list)
    excess = mean_ret - risk_free_rate
    from app.services.analytics.metrics.risk import downside_volatility

    down_vol = downside_volatility(ret_list, config).value or 0.0
    down_vol /= 100.0
    if down_vol == 0:
        return MetricResult(value=0.0)
    val = excess / down_vol
    return MetricResult(value=val)


def omega_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate gains-to-losses relative to target threshold Omega ratio (ANL-NFR-220).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("omega_ratio: executed.")
    ret_list = _parse_returns(returns)
    target = float(config.metadata.get("target_return", 0.0) if config else 0.0)
    gains = sum(max(r - target, 0.0) for r in ret_list)
    losses = sum(max(target - r, 0.0) for r in ret_list)
    val = (999.0 if gains > 0 else 0.0) if losses == 0 else gains / losses
    return MetricResult(value=val)


def probabilistic_sharpe_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probabilistic Sharpe ratio (ANL-NFR-221).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("probabilistic_sharpe_ratio: executed.")
    ret_list = _parse_returns(returns)
    n = len(ret_list)
    if n < 4:
        return MetricResult(value=0.0)
    sr_metric = sharpe_ratio(returns, config).value or 0.0
    sr_benchmark = float(config.metadata.get("sr_benchmark", 0.0) if config else 0.0)
    from app.services.analytics.metrics.equity import (
        return_kurtosis,
        return_skewness,
    )

    skew = return_skewness(returns, config).value or 0.0
    kurt = (return_kurtosis(returns, config).value or 0.0) + 3.0
    denom_val = 1.0 - skew * sr_metric + ((kurt - 1.0) / 4.0) * (sr_metric**2)
    if denom_val <= 0:
        return MetricResult(value=0.0)
    std_err = math.sqrt(denom_val / (n - 1))
    z = (sr_metric - sr_benchmark) / std_err
    val = normal_cdf(z)
    return MetricResult(value=val)


def tail_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate 95th percentile divided by absolute 5th percentile return (ANL-NFR-222).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("tail_ratio: executed.")
    ret_list = _parse_returns(returns)
    if not ret_list:
        return MetricResult(value=0.0)
    from app.services.analytics.statistics.distributions import (
        tail_ratio as dist_tail_ratio,
    )

    val = dist_tail_ratio(ret_list)
    return MetricResult(value=val)


def profit_factor(
    trades: Sequence[TradeRecord],
) -> float:
    """Calculate gross winning profit divided by absolute gross losing loss (ANL-NFR-223).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.

    Returns:
        Calculated float value.
    """
    logger.debug("profit_factor: executed.")
    pnls = [_get_trade_pnl(t) for t in trades]
    wins = sum(x for x in pnls if x > 0)
    losses = sum(abs(x) for x in pnls if x < 0)
    if losses == 0:
        return 999.0 if wins > 0 else 0.0
    return wins / losses


def profit_factor_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Profit factor exposed as a metric wrapper (ANL-NFR-223).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("profit_factor_metric: executed.")
    trades = config.metadata.get("trades", [])
    val = profit_factor(trades)
    return MetricResult(value=val)


def profit_factor_by_volume(
    trades: Sequence[TradeRecord],
) -> float:
    """Calculate sum of volume of winning trades divided by losing trades (ANL-NFR-224).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.

    Returns:
        Calculated float value.
    """
    logger.debug("profit_factor_by_volume: executed.")
    wins_vol = 0.0
    loss_vol = 0.0
    for t in trades:
        pnl = _get_trade_pnl(t)
        vol = float(t.get("size") or t.get("volume") or 0.0)
        if pnl > 0:
            wins_vol += vol
        elif pnl < 0:
            loss_vol += vol
    if loss_vol == 0:
        return 999.0 if wins_vol > 0 else 0.0
    return wins_vol / loss_vol


def profit_factor_by_volume_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Profit factor by volume exposed as a metric (ANL-NFR-224).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("profit_factor_by_volume_metric: executed.")
    trades = config.metadata.get("trades", [])
    val = profit_factor_by_volume(trades)
    return MetricResult(value=val)


def payoff_ratio(
    trades: Sequence[TradeRecord],
    config: MetricConfig | None = None,
) -> float:
    """Calculate average win divided by average absolute loss (ANL-NFR-225).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig | None): Metric configuration.

    Returns:
        Calculated float value.
    """
    logger.debug("payoff_ratio: executed.")
    cfg = config if config is not None else MetricConfig()
    aw = avg_win(trades, cfg).value or 0.0
    al = abs(avg_loss(trades, cfg).value or 0.0)
    if al == 0:
        return 0.0
    return aw / al


def payoff_ratio_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Payoff ratio exposed as a metric (ANL-NFR-225).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("payoff_ratio_metric: executed.")
    trades = config.metadata.get("trades", [])
    val = payoff_ratio(trades, config)
    return MetricResult(value=val)


def average_win_loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Alias for payoff_ratio_metric (ANL-NFR-226).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("average_win_loss_ratio: executed.")
    return payoff_ratio_metric(returns, config)


def adjusted_profit_factor(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate profit factor excluding outliers (ANL-NFR-227).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("adjusted_profit_factor: executed.")
    trades = config.metadata.get("trades", [])
    from app.services.analytics.metrics.pnl import (
        adjusted_gross_loss,
        adjusted_gross_profit,
    )

    ag_p = adjusted_gross_profit(trades, config).value or 0.0
    ag_l = abs(adjusted_gross_loss(trades, config).value or 0.0)
    val = (999.0 if ag_p > 0 else 0.0) if ag_l == 0 else ag_p / ag_l
    return MetricResult(value=val)


def select_profit_factor(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate select profit factor excluding largest wins/losses (ANL-NFR-228).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("select_profit_factor: executed.")
    trades = config.metadata.get("trades", [])
    from app.services.analytics.metrics.pnl import (
        select_gross_loss,
        select_gross_profit,
    )

    sg_p = select_gross_profit(trades, config).value or 0.0
    sg_l = abs(select_gross_loss(trades, config).value or 0.0)
    val = (999.0 if sg_p > 0 else 0.0) if sg_l == 0 else sg_p / sg_l
    return MetricResult(value=val)


def adjusted_payoff_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average winning trade PnL to average losing trade PnL excluding outliers (ANL-NFR-228).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("adjusted_payoff_ratio: executed.")
    trades = config.metadata.get("trades", [])
    wins = classify_trades(trades, config)["wins"]
    losses = classify_trades(trades, config)["losses"]
    if not wins or not losses:
        return MetricResult(value=0.0)
    from app.services.analytics.metrics.pnl import (
        adjusted_gross_loss,
        adjusted_gross_profit,
    )

    ag_p = adjusted_gross_profit(trades, config).value or 0.0
    ag_l = abs(adjusted_gross_loss(trades, config).value or 0.0)
    avg_win_adj = ag_p / len(wins)
    avg_loss_adj = ag_l / len(losses)
    if avg_loss_adj == 0:
        return MetricResult(value=0.0)
    val = avg_win_adj / avg_loss_adj
    return MetricResult(value=val)


def cpc_index(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate Sunny Harris CPC Index (ANL-NFR-229).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("cpc_index: executed.")
    trades = config.metadata.get("trades", [])
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    pf = profit_factor(closed)
    win_rate = len(classify_trades(closed, config)["wins"]) / len(closed)
    payoff = payoff_ratio(closed)
    val = pf * win_rate * payoff
    return MetricResult(value=val)


def system_quality_number(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate Van Tharp System Quality Number (ANL-NFR-230).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("system_quality_number: executed.")
    trades = config.metadata.get("trades", [])
    closed = get_closed_trades(trades)
    n = len(closed)
    if n < 2:
        return MetricResult(value=0.0)
    pnls = [_get_trade_pnl(t) for t in closed]
    mean = sum(pnls) / n
    var = sum((x - mean) ** 2 for x in pnls) / (n - 1)
    if var == 0:
        return MetricResult(value=0.0)
    val = math.sqrt(n) * mean / math.sqrt(var)
    return MetricResult(value=val)


def sqn(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Alias for system_quality_number (ANL-NFR-231).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("sqn: executed.")
    return system_quality_number(returns, config)


def information_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate active annualized return divided by annualized tracking error (ANL-NFR-232).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("information_ratio: executed.")
    ret_list = _parse_returns(returns)
    benchmark_returns = config.metadata.get("benchmark_returns", [])
    bench_list = _parse_returns(benchmark_returns)
    from app.services.analytics.benchmarks import information_ratio as bench_ir

    val = bench_ir(ret_list, bench_list)
    return MetricResult(value=val)


def treynor_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate excess return per unit of systematic risk (ANL-NFR-233).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("treynor_ratio: executed.")
    ret_list = _parse_returns(returns)
    benchmark_returns = config.metadata.get("benchmark_returns", [])
    bench_list = _parse_returns(benchmark_returns)
    periods = int(config.annualization_periods if config else 252)
    product = 1.0
    for r in ret_list:
        product *= 1.0 + r
    ann_ret = (
        (math.pow(product, periods / len(ret_list)) - 1.0) * 100.0
        if ret_list and product > 0
        else 0.0
    )
    risk_free_rate = float(
        config.metadata.get("risk_free_rate", 0.0) if config else 0.0
    )
    from app.services.analytics.benchmarks import beta

    b = beta(ret_list, bench_list)
    if b == 0:
        return MetricResult(value=0.0)
    val = (ann_ret - risk_free_rate) / b
    return MetricResult(value=val)


def active_premium(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate annualized difference between strategy and benchmark return (ANL-NFR-234).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("active_premium: executed.")
    ret_list = _parse_returns(returns)
    benchmark_returns = config.metadata.get("benchmark_returns", [])
    bench_list = _parse_returns(benchmark_returns)
    periods = int(config.annualization_periods if config else 252)
    # Strategy annualized return
    product_s = 1.0
    for r in ret_list:
        product_s *= 1.0 + r
    ann_ret_s = (
        (math.pow(product_s, periods / len(ret_list)) - 1.0) * 100.0
        if ret_list and product_s > 0
        else 0.0
    )
    # Benchmark annualized return
    product_b = 1.0
    for r in bench_list:
        product_b *= 1.0 + r
    ann_ret_b = (
        (math.pow(product_b, periods / len(bench_list)) - 1.0) * 100.0
        if bench_list and product_b > 0
        else 0.0
    )
    val = ann_ret_s - ann_ret_b
    return MetricResult(value=val)


def tracking_error(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate standard deviation of return differences (ANL-NFR-235).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("tracking_error: executed.")
    ret_list = _parse_returns(returns)
    benchmark_returns = config.metadata.get("benchmark_returns", [])
    bench_list = _parse_returns(benchmark_returns)
    from app.services.analytics.benchmarks import tracking_error as bench_te

    val = bench_te(ret_list, bench_list)
    return MetricResult(value=val)


def expectancy(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate arithmetic expectancy per trade (ANL-NFR-236).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("expectancy: executed.")
    trades = config.metadata.get("trades", [])
    from app.services.analytics.metrics.pnl import net_profit

    net_p = net_profit(trades, config).value or 0.0
    closed = get_closed_trades(trades)
    val = net_p / len(closed) if closed else 0.0
    return MetricResult(value=val)


def expectancy_r(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate mean R-multiple (ANL-NFR-237).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("expectancy_r: executed.")
    trades = config.metadata.get("trades", [])
    from app.services.analytics.metrics.r_multiples import _get_r_multiples_flat

    r_mults = _get_r_multiples_flat(trades)
    val = sum(r_mults) / len(r_mults) if r_mults else 0.0
    return MetricResult(value=val)


def profit_loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average winning trade PnL to average losing trade PnL (ANL-NFR-238).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("profit_loss_ratio: executed.")
    return payoff_ratio_metric(returns, config)


def gain_loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total gains divided by total absolute losses (ANL-NFR-239).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("gain_loss_ratio: executed.")
    return profit_factor_metric(returns, config)


def win_loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate win count divided by loss count (ANL-NFR-240).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("win_loss_ratio: executed.")
    trades = config.metadata.get("trades", [])
    wins = classify_trades(trades, config)["wins"]
    losses = classify_trades(trades, config)["losses"]
    val = (999.0 if wins else 0.0) if not losses else len(wins) / len(losses)
    return MetricResult(value=val)


def profit_factor_by_count(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate win count divided by loss count (ANL-NFR-241).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("profit_factor_by_count: executed.")
    return win_loss_ratio(returns, config)


def loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate loss count divided by total trade count (ANL-NFR-242).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("loss_ratio: executed.")
    trades = config.metadata.get("trades", [])
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    losses = classify_trades(closed, config)["losses"]
    val = len(losses) / len(closed)
    return MetricResult(value=val)


def ulcer_performance_index(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate annualized return divided by ulcer index (ANL-NFR-243).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("ulcer_performance_index: executed.")
    ret_list = _parse_returns(returns)
    periods = int(config.annualization_periods if config else 252)
    product = 1.0
    for r in ret_list:
        product *= 1.0 + r
    ann_ret = (
        (math.pow(product, periods / len(ret_list)) - 1.0) * 100.0
        if ret_list and product > 0
        else 0.0
    )
    risk_free_rate = float(
        config.metadata.get("risk_free_rate", 0.0) if config else 0.0
    )
    # Using equity curve to compute ulcer index
    equity_curve = config.metadata.get("equity_curve", [])
    ulcer = ulcer_index(equity_curve, config).value or 0.0
    if ulcer <= 0:
        return MetricResult(value=0.0)
    val = (ann_ret - risk_free_rate) / ulcer
    return MetricResult(value=val)


def martin_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate annualized return divided by ulcer index (ANL-NFR-244).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("martin_ratio: executed.")
    return ulcer_performance_index(returns, config)


def adjusted_expectancy(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate expectancy excluding outlier trades (ANL-NFR-245).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("adjusted_expectancy: executed.")
    trades = config.metadata.get("trades", [])
    from app.services.analytics.metrics.pnl import adjusted_net_profit

    adj_net = adjusted_net_profit(trades, config).value or 0.0
    closed = get_closed_trades(trades)
    val = adj_net / len(closed) if closed else 0.0
    return MetricResult(value=val)


def ratio_of_adjusted_gross_profit_to_adjusted_gross_loss(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate adjusted gross profit divided by adjusted gross loss (ANL-NFR-246).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("ratio_of_adjusted_gross_profit_to_adjusted_gross_loss: executed.")
    return adjusted_profit_factor(returns, config)


def expected_value(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probability-weighted outcome in currency units (ANL-NFR-247).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("expected_value: executed.")
    return expectancy(returns, config)


def expected_value_r(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probability-weighted outcome in R-multiple units (ANL-NFR-248).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("expected_value_r: executed.")
    return expectancy_r(returns, config)


def odds_calculator(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate probability odds indicators (ANL-NFR-249).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("odds_calculator: executed.")
    trades = config.metadata.get("trades", [])
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value={})
    win_rate = len(classify_trades(closed, config)["wins"]) / len(closed)
    payoff = payoff_ratio(closed)
    val = {
        "win_rate": win_rate,
        "loss_rate": 1.0 - win_rate,
        "payoff_ratio": payoff,
        "odds_ratio": win_rate / (1.0 - win_rate) if win_rate < 1.0 else 999.0,
    }
    return MetricResult(value=val)


def risk_reward_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate risk-reward ratio (ANL-NFR-250).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("risk_reward_ratio: executed.")
    return payoff_ratio_metric(returns, config)


def drawdown_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return over maximum drawdown ratio (ANL-NFR-251).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("drawdown_ratio: executed.")
    # Simply using recovery factor / Calmar ratio style
    equity_curve = config.metadata.get("equity_curve", [])
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    from app.services.analytics.metrics.drawdown import max_strategy_drawdown

    max_dd = max_strategy_drawdown(equity_curve, config).value or 0.0
    val = net_p / max_dd if max_dd > 0 else 0.0
    return MetricResult(value=val)


def _validate_request_id(request_id: str | None) -> None:
    """Validate request_id format strictly.

    Args:
        request_id: Optional trace ID.
    """
    if request_id is not None and not isinstance(request_id, str):
        logger.warning("validate_request_id: invalid request_id type.")
        raise ValidationError("request_id must be a string or None.")


def annualized_sharpe_ratio(
    returns: list[float], risk_free_rate: float = 0.0, periods: int = 252
) -> float:
    """Compute the Annualized Sharpe Ratio.

    Args:
        returns: Period return series.
        risk_free_rate: Annual risk-free rate.
        periods: Number of periods per year.

    Returns:
        Annualized Sharpe Ratio.
    """
    logger.debug("annualized_sharpe_ratio: executed.")
    if len(returns) < 2:
        return 0.0
    r_f = risk_free_rate / periods
    mean_ret = sum(returns) / len(returns)
    excess = mean_ret - r_f
    n = len(returns)
    var = sum((x - mean_ret) ** 2 for x in returns) / (n - 1)
    if var == 0:
        return 0.0
    sr = excess / math.sqrt(var)
    res = sr * math.sqrt(periods)
    return res


def gain_to_pain_ratio(returns: list[float]) -> float:
    """Compute the Gain-to-Pain Ratio.

    Args:
        returns: Period return series.

    Returns:
        Gain-to-Pain Ratio.
    """
    logger.debug("gain_to_pain_ratio: executed.")
    gains = sum(r for r in returns if r > 0)
    losses = sum(abs(r) for r in returns if r < 0)
    if losses == 0:
        res = 999.0 if gains > 0 else 0.0
        return res
    res = gains / losses
    return res


def kappa_ratio(returns: list[float], target: float = 0.0, order: int = 3) -> float:
    """Compute the Kappa Ratio.

    Args:
        returns: Period return series.
        target: Target return threshold.
        order: Order of the lower partial moment.

    Returns:
        Kappa Ratio.
    """
    logger.debug("kappa_ratio: executed.")
    if not returns:
        return 0.0
    mean = sum(returns) / len(returns)
    lpm = sum(max(target - r, 0.0) ** order for r in returns) / len(returns)
    if lpm == 0:
        return 0.0
    res = float((mean - target) / (lpm ** (1.0 / order)))
    return res


def edge_ratio(trades: list[dict[str, Any]]) -> float:
    """Compute the Edge Ratio.

    Args:
        trades: List of trade dictionaries.

    Returns:
        Edge Ratio.
    """
    logger.debug("edge_ratio: executed.")
    from app.services.analytics.metrics.trade_outcomes import win_rate_fraction

    w = win_rate_fraction(trades, MetricConfig()).value or 0.0
    r = payoff_ratio(trades)
    res = w * r - (1.0 - w)
    return res


def profit_to_mae_ratio(trades: list[dict[str, Any]]) -> float:
    """Compute the Profit-to-MAE Ratio.

    Args:
        trades: List of trade dictionaries.

    Returns:
        Profit-to-MAE Ratio.
    """
    logger.debug("profit_to_mae_ratio: executed.")
    from app.services.analytics.metrics.efficiency import return_per_unit_mae

    res = return_per_unit_mae(trades, MetricConfig()).value or 0.0
    return res


def mfe_to_mae_ratio(trades: list[dict[str, Any]]) -> float:
    """Compute the MFE-to-MAE Ratio.

    Args:
        trades: List of trade dictionaries.

    Returns:
        MFE-to-MAE Ratio.
    """
    logger.debug("mfe_to_mae_ratio: executed.")
    total_mfe = sum(float(t.get("mfe") or 0.0) for t in trades)
    total_mae = sum(abs(float(t.get("mae") or 0.0)) for t in trades)
    if total_mae <= 0:
        return 0.0
    res = total_mfe / total_mae
    return res


def expectancy_over_std(trades: list[dict[str, Any]]) -> float:
    """Compute expectancy divided by standard deviation of PnL.

    Args:
        trades: List of trade dictionaries.

    Returns:
        Expectancy over standard deviation of PnL.
    """
    logger.debug("expectancy_over_std: executed.")
    from app.services.analytics.metrics.trade_outcomes import (
        _get_trade_pnl,
        get_ordered_closed_trades,
    )

    closed = get_ordered_closed_trades(trades)
    n = len(closed)
    if n == 0:
        return 0.0
    pnls = [_get_trade_pnl(t) for t in closed]
    mean = sum(pnls) / n
    if n < 2:
        return 0.0
    var = sum((x - mean) ** 2 for x in pnls) / (n - 1)
    if var == 0:
        return 0.0
    res = mean / math.sqrt(var)
    return res


def net_profit_as_percent_of_largest_loss(
    net_profit: float, largest_loss: float
) -> float:
    """Express net profit as a percentage of largest loss.

    Args:
        net_profit: Net profit.
        largest_loss: Largest loss value.

    Returns:
        Ratio as a percentage.
    """
    logger.debug("net_profit_as_percent_of_largest_loss: executed.")
    if largest_loss == 0:
        return 0.0
    res = (net_profit / abs(largest_loss)) * 100.0
    return res


def select_net_profit_as_percent_of_largest_loss(
    select_net_profit: float, largest_loss: float
) -> float:
    """Express trimmed net profit as a percentage of largest loss.

    Args:
        select_net_profit: Trimmed net profit.
        largest_loss: Largest loss value.

    Returns:
        Ratio as a percentage.
    """
    logger.debug("select_net_profit_as_percent_of_largest_loss: executed.")
    res = net_profit_as_percent_of_largest_loss(select_net_profit, largest_loss)
    return res


def adjusted_net_profit_as_percent_of_largest_loss(
    adjusted_net_profit: float, largest_loss: float
) -> float:
    """Express adjusted net profit as a percentage of largest loss.

    Args:
        adjusted_net_profit: Adjusted net profit.
        largest_loss: Largest loss value.

    Returns:
        Ratio as a percentage.
    """
    logger.debug("adjusted_net_profit_as_percent_of_largest_loss: executed.")
    res = net_profit_as_percent_of_largest_loss(adjusted_net_profit, largest_loss)
    return res


def calculate_ratio_metrics(
    returns: Sequence[float],
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate ratio metrics for a series of returns.

    Args:
        returns: The sequence of returns.
        request_id: Optional request identifier.

    Returns:
        StandardResponse containing the ratio metrics dictionary.
    """
    logger.debug("calculate_ratio_metrics: executed.")
    from app.services.analytics.statistics.distributions import _to_float_list

    ret_list = _to_float_list(returns)
    if not ret_list:
        raise ValidationError("returns series must contain at least one valid number.")

    from app.utils import (
        build_metadata,
        response_from_exception,
        success_response,
    )

    try:
        meta = build_metadata(
            tool_name="calculate_ratio_metrics",
            tool_category="analytics",
            tool_risk_level="low",
            request_id=request_id,
            reads=True,
        )
        data = {
            "sharpe_ratio": sharpe_ratio(ret_list, MetricConfig()).value or 0.0,
            "annualized_sharpe_ratio": annualized_sharpe_ratio(ret_list) or 0.0,
            "sortino_ratio": sortino_ratio(ret_list, MetricConfig()).value or 0.0,
            "omega_ratio": omega_ratio(ret_list, MetricConfig()).value or 0.0,
            "gain_to_pain_ratio": gain_to_pain_ratio(ret_list) or 0.0,
        }
        return success_response(
            message="Successfully calculated ratio metrics.", data=data, metadata=meta
        )
    except Exception as e:  # noqa: BLE001
        meta = build_metadata(
            tool_name="calculate_ratio_metrics",
            tool_category="analytics",
            tool_risk_level="low",
            request_id=request_id,
            reads=True,
        )
        return response_from_exception(exception=e, metadata=meta)


def up_down_capture(
    strategy_returns: Sequence[float],
    benchmark_returns: Sequence[float],
) -> dict[str, float]:
    """Calculate up-capture and down-capture ratios.

    Args:
        strategy_returns: Strategy return sequence.
        benchmark_returns: Benchmark return sequence.

    Returns:
        Up-capture and down-capture ratios.
    """
    logger.debug("ratios.up_down_capture: executed.")
    from app.services.analytics.benchmarks.metrics import (
        up_down_capture as benchmark_up_down_capture,
    )

    return benchmark_up_down_capture(strategy_returns, benchmark_returns)


def deflated_sharpe_ratio(sharpe: float, returns: list[float]) -> float:
    """Adjust Sharpe ratio diagnostics for multiple testing and non-normality.

    Args:
        sharpe: Observed Sharpe ratio.
        returns: Return sequence used for diagnostic context.

    Returns:
        Deflated Sharpe diagnostic value.
    """
    logger.debug("ratios.deflated_sharpe_ratio: executed.")
    from app.services.analytics.statistics.multiple_testing import (
        deflated_sharpe_ratio as statistics_deflated_sharpe_ratio,
    )

    return statistics_deflated_sharpe_ratio(sharpe, returns)
