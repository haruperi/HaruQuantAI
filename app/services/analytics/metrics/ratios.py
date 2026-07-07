# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Ratio and performance index calculations (ANL-NFR-218)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.drawdown import (
    ulcer_index,
)
from app.services.analytics.metrics.equity_returns import (
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

type ReturnPoint = Any
type TradeRecord = dict[str, Any]


def _parse_returns(returns: Sequence[ReturnPoint | float]) -> list[float]:
    res = []
    for r in returns:
        if isinstance(r, (float, int)):
            res.append(float(r))
        elif isinstance(r, dict):
            val = r.get("return") or r.get("value") or r.get("pnl") or 0.0
            res.append(float(val))
    return res


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def sharpe_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate reward-to-variability Sharpe ratio (ANL-NFR-218)."""
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
    """Calculate return relative to downside deviation Sortino ratio (ANL-NFR-219)."""
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
    """Calculate gains-to-losses relative to target threshold Omega ratio (ANL-NFR-220)."""
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
    """Calculate probabilistic Sharpe ratio (ANL-NFR-221)."""
    ret_list = _parse_returns(returns)
    n = len(ret_list)
    if n < 4:
        return MetricResult(value=0.0)
    sr_metric = sharpe_ratio(returns, config).value or 0.0
    sr_benchmark = float(config.metadata.get("sr_benchmark", 0.0) if config else 0.0)
    from app.services.analytics.metrics.equity_returns import (
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
    """Calculate 95th percentile divided by absolute 5th percentile return (ANL-NFR-222)."""
    ret_list = _parse_returns(returns)
    if not ret_list:
        return MetricResult(value=0.0)
    from app.services.analytics.statistics.distributions import tail_ratio as dist_tail_ratio

    val = dist_tail_ratio(ret_list)
    return MetricResult(value=val)


def profit_factor(
    trades: Sequence[TradeRecord],
) -> float:
    """Calculate gross winning profit divided by absolute gross losing loss (ANL-NFR-223)."""
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
    """Profit factor exposed as a metric wrapper (ANL-NFR-223)."""
    trades = config.metadata.get("trades", [])
    val = profit_factor(trades)
    return MetricResult(value=val)


def profit_factor_by_volume(
    trades: Sequence[TradeRecord],
) -> float:
    """Calculate sum of volume of winning trades divided by losing trades (ANL-NFR-224)."""
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
    """Profit factor by volume exposed as a metric (ANL-NFR-224)."""
    trades = config.metadata.get("trades", [])
    val = profit_factor_by_volume(trades)
    return MetricResult(value=val)


def payoff_ratio(
    trades: Sequence[TradeRecord],
    config: MetricConfig | None = None,
) -> float:
    """Calculate average win divided by average absolute loss (ANL-NFR-225)."""
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
    """Payoff ratio exposed as a metric (ANL-NFR-225)."""
    trades = config.metadata.get("trades", [])
    val = payoff_ratio(trades, config)
    return MetricResult(value=val)


def average_win_loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Alias for payoff_ratio_metric (ANL-NFR-226)."""
    return payoff_ratio_metric(returns, config)


def adjusted_profit_factor(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate profit factor excluding outliers (ANL-NFR-227)."""
    trades = config.metadata.get("trades", [])
    from app.services.analytics.metrics.pnl import (
        adjusted_gross_loss,
        adjusted_gross_profit,
    )

    ag_p = adjusted_gross_profit(trades, config).value or 0.0
    ag_l = abs(adjusted_gross_loss(trades, config).value or 0.0)
    val = (999.0 if ag_p > 0 else 0.0) if ag_l == 0 else ag_p / ag_l
    return MetricResult(value=val)


def adjusted_payoff_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average winning trade PnL to average losing trade PnL excluding outliers (ANL-NFR-228)."""
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
    """Calculate Sunny Harris CPC Index (ANL-NFR-229)."""
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
    """Calculate Van Tharp System Quality Number (ANL-NFR-230)."""
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
    """Alias for system_quality_number (ANL-NFR-231)."""
    return system_quality_number(returns, config)


def information_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate active annualized return divided by annualized tracking error (ANL-NFR-232)."""
    ret_list = _parse_returns(returns)
    benchmark_returns = config.metadata.get("benchmark_returns", [])
    bench_list = _parse_returns(benchmark_returns)
    from app.services.analytics.benchmark import information_ratio as bench_ir

    val = bench_ir(ret_list, bench_list)
    return MetricResult(value=val)


def treynor_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate excess return per unit of systematic risk (ANL-NFR-233)."""
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
    from app.services.analytics.benchmark import beta

    b = beta(ret_list, bench_list)
    if b == 0:
        return MetricResult(value=0.0)
    val = (ann_ret - risk_free_rate) / b
    return MetricResult(value=val)


def active_premium(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate annualized difference between strategy and benchmark return (ANL-NFR-234)."""
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
    """Calculate standard deviation of return differences (ANL-NFR-235)."""
    ret_list = _parse_returns(returns)
    benchmark_returns = config.metadata.get("benchmark_returns", [])
    bench_list = _parse_returns(benchmark_returns)
    from app.services.analytics.benchmark import tracking_error as bench_te

    val = bench_te(ret_list, bench_list)
    return MetricResult(value=val)


def expectancy(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate arithmetic expectancy per trade (ANL-NFR-236)."""
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
    """Calculate mean R-multiple (ANL-NFR-237)."""
    trades = config.metadata.get("trades", [])
    from app.services.analytics.trade import _get_r_multiples_flat

    r_mults = _get_r_multiples_flat(trades)
    val = sum(r_mults) / len(r_mults) if r_mults else 0.0
    return MetricResult(value=val)


def profit_loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average winning trade PnL to average losing trade PnL (ANL-NFR-238)."""
    return payoff_ratio_metric(returns, config)


def gain_loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total gains divided by total absolute losses (ANL-NFR-239)."""
    return profit_factor_metric(returns, config)


def win_loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate win count divided by loss count (ANL-NFR-240)."""
    trades = config.metadata.get("trades", [])
    wins = classify_trades(trades, config)["wins"]
    losses = classify_trades(trades, config)["losses"]
    val = (999.0 if wins else 0.0) if not losses else len(wins) / len(losses)
    return MetricResult(value=val)


def profit_factor_by_count(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate win count divided by loss count (ANL-NFR-241)."""
    return win_loss_ratio(returns, config)


def loss_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate loss count divided by total trade count (ANL-NFR-242)."""
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
    """Calculate annualized return divided by ulcer index (ANL-NFR-243)."""
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
    """Calculate annualized return divided by ulcer index (ANL-NFR-244)."""
    return ulcer_performance_index(returns, config)


def adjusted_expectancy(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate expectancy excluding outlier trades (ANL-NFR-245)."""
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
    """Calculate adjusted gross profit divided by adjusted gross loss (ANL-NFR-246)."""
    return adjusted_profit_factor(returns, config)


def expected_value(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probability-weighted outcome in currency units (ANL-NFR-247)."""
    return expectancy(returns, config)


def expected_value_r(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probability-weighted outcome in R-multiple units (ANL-NFR-248)."""
    return expectancy_r(returns, config)


def odds_calculator(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate probability odds indicators (ANL-NFR-249)."""
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
    """Calculate risk-reward ratio (ANL-NFR-250)."""
    return payoff_ratio_metric(returns, config)


def drawdown_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return over maximum drawdown ratio (ANL-NFR-251)."""
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
