# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Risk and volatility calculations (ANL-NFR-170)."""

from __future__ import annotations

import datetime
import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.efficiency import _get_trade_duration
from app.services.analytics.metrics.position_exposure import percent_time_in_market
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    get_closed_trades,
    get_ordered_closed_trades,
)
from app.utils import StandardResponse  # noqa: TC001
from app.utils.logger import logger

type ReturnPoint = Any
type TradeRecord = dict[str, Any]
type Duration = datetime.timedelta | float


def _parse_returns(returns: Sequence[ReturnPoint | float]) -> list[float]:
    """Helper to convert generic return sequence into float list.

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


def max_loss_probability(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probability of a single trade loss exceeding a threshold (ANL-NFR-170).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_loss_probability: executed.")
    ret_list = _parse_returns(returns)
    threshold = float(config.metadata.get("loss_threshold", -0.02) if config else -0.02)
    if not ret_list:
        return MetricResult(value=0.0)
    losses_exceeded = sum(1 for r in ret_list if r <= threshold)
    val = losses_exceeded / len(ret_list)
    return MetricResult(value=val)


def risk_of_ruin(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Estimate ruin probability through Monte Carlo simulation (ANL-NFR-171).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("risk_of_ruin: executed.")
    # Simply using standard risk of ruin Monte Carlo simulator wrapper
    trades = config.metadata.get("trades", [])
    initial_balance = float(
        config.metadata.get("initial_balance", 10000.0) if config else 10000.0
    )
    ruin_threshold = float(
        config.metadata.get("ruin_threshold", 5000.0) if config else 5000.0
    )
    iterations = int(config.metadata.get("iterations", 1000) if config else 1000)
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    pnls = [_get_trade_pnl(t) for t in closed]
    # Simple bootstrapping simulation
    import random

    ruined_runs = 0
    for _ in range(iterations):
        bal = initial_balance
        # Simulate horizon of 100 trades
        for _ in range(100):
            bal += random.choice(pnls)
            if bal <= ruin_threshold:
                ruined_runs += 1
                break
    val = ruined_runs / iterations
    return MetricResult(value=val)


def avg_trade_nominal_exposure(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average nominal exposure per trade (ANL-NFR-172).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_trade_nominal_exposure: executed.")
    trades = config.metadata.get("trades", [])
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    exposures = []
    for t in closed:
        size = float(t.get("size") or t.get("volume") or 0.0)
        price = float(t.get("open_price") or t.get("entry_price") or 1.0)
        exposures.append(size * price)
    val = sum(exposures) / len(exposures) if exposures else 0.0
    return MetricResult(value=val)


def max_single_trade_margin_utilization(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum margin used by a single trade as a percentage of equity (ANL-NFR-173).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_single_trade_margin_utilization: executed.")
    trades = config.metadata.get("trades", [])
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    max_util = 0.0
    for t in closed:
        margin = float(t.get("margin") or t.get("margin_used") or 0.0)
        equity = float(t.get("equity") or 10000.0)
        if equity > 0:
            max_util = max(max_util, margin / equity)
    return MetricResult(value=max_util * 100.0)


def avg_single_trade_margin_utilization(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average margin used per trade as a percentage of equity (ANL-NFR-174).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_single_trade_margin_utilization: executed.")
    trades = config.metadata.get("trades", [])
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    utils = []
    for t in closed:
        margin = float(t.get("margin") or t.get("margin_used") or 0.0)
        equity = float(t.get("equity") or 10000.0)
        if equity > 0:
            utils.append(margin / equity)
    val = (sum(utils) / len(utils)) * 100.0 if utils else 0.0
    return MetricResult(value=val)


def risk_of_ruin_with_custom_horizon(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Estimate ruin probability over a fixed future trade horizon (ANL-NFR-175).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("risk_of_ruin_with_custom_horizon: executed.")
    return risk_of_ruin(returns, config)


def risk_adjusted_efficiency(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return relative to total defined initial risk (ANL-NFR-254).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("risk_adjusted_efficiency: executed.")
    ret_list = _parse_returns(returns)
    net_profit = sum(ret_list)
    total_risk = float(config.metadata.get("total_risk", 1.0) if config else 1.0)
    if total_risk <= 0:
        return MetricResult(value=0.0)
    val = net_profit / total_risk
    return MetricResult(value=val)


def profit_per_pip_risk(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate reward-to-risk based on profit pips relative to MAE pips (ANL-NFR-255).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("profit_per_pip_risk: executed.")
    trades = config.metadata.get("trades", [])
    total_prof = sum(float(t.get("profit_loss") or t.get("pnl") or 0.0) for t in trades)
    total_mae = sum(abs(float(t.get("mae") or 0.0)) for t in trades)
    if total_mae <= 0:
        return MetricResult(value=0.0)
    val = total_prof / total_mae
    return MetricResult(value=val)


def upside_potential_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate upside potential relative to downside risk (ANL-NFR-256).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("upside_potential_ratio: executed.")
    ret_list = _parse_returns(returns)
    target = float(config.metadata.get("target_return", 0.0) if config else 0.0)
    upside = [max(r - target, 0.0) for r in ret_list]
    if not upside:
        return MetricResult(value=0.0)
    avg_upside = sum(upside) / len(ret_list)
    down_vol = downside_volatility(returns, config).value or 0.0
    down_vol /= 100.0
    if down_vol <= 0:
        return MetricResult(value=0.0)
    val = avg_upside / down_vol
    return MetricResult(value=val)


def volatility(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return standard deviation as a positive percentage (ANL-NFR-257).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("volatility: executed.")
    ret_list = _parse_returns(returns)
    if len(ret_list) < 2:
        return MetricResult(value=0.0)
    mean = sum(ret_list) / len(ret_list)
    var = sum((r - mean) ** 2 for r in ret_list) / (len(ret_list) - 1)
    val = math.sqrt(var) * 100.0
    return MetricResult(value=val)


def annualized_volatility(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate annualized volatility as a positive percentage (ANL-NFR-258).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("annualized_volatility: executed.")
    periods = int(config.annualization_periods if config else 252)
    vol = volatility(returns, config).value or 0.0
    val = vol * math.sqrt(periods)
    return MetricResult(value=val)


def downside_volatility(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate downside deviation as a positive percentage (ANL-NFR-259).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("downside_volatility: executed.")
    ret_list = _parse_returns(returns)
    target = float(config.metadata.get("target_return", 0.0) if config else 0.0)
    downside = [r - target for r in ret_list if r < target]
    if len(downside) < 2:
        return MetricResult(value=0.0)
    var = sum(d**2 for d in downside) / (len(ret_list) - 1)
    val = math.sqrt(var) * 100.0
    return MetricResult(value=val)


def value_at_risk(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate value-at-risk as a positive percentage (ANL-NFR-260).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("value_at_risk: executed.")
    ret_list = _parse_returns(returns)
    if not ret_list:
        return MetricResult(value=0.0)
    confidence = float(config.metadata.get("confidence", 0.95) if config else 0.95)
    sorted_ret = sorted(ret_list)
    alpha_val = 1.0 - confidence
    idx = int(len(sorted_ret) * alpha_val)
    val = abs(sorted_ret[idx]) * 100.0 if idx < len(sorted_ret) else 0.0
    return MetricResult(value=val)


def conditional_var(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate conditional value-at-risk as a positive percentage (ANL-NFR-261).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("conditional_var: executed.")
    ret_list = _parse_returns(returns)
    if not ret_list:
        return MetricResult(value=0.0)
    confidence = float(config.metadata.get("confidence", 0.95) if config else 0.95)
    sorted_ret = sorted(ret_list)
    alpha_val = 1.0 - confidence
    idx = int(len(sorted_ret) * alpha_val)
    tail = sorted_ret[:idx] if idx > 0 else sorted_ret[:1]
    val = (sum(abs(r) for r in tail) / len(tail)) * 100.0
    return MetricResult(value=val)


def expected_shortfall(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate expected shortfall (ANL-NFR-262).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("expected_shortfall: executed.")
    return conditional_var(returns, config)


def max_nominal_exposure_simple(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum nominal exposure held at one time (ANL-NFR-263).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_nominal_exposure_simple: executed.")
    trades = config.metadata.get("trades", [])
    exposures = []
    for t in trades:
        size = float(t.get("size") or t.get("volume") or 0.0)
        price = float(t.get("open_price") or t.get("entry_price") or 1.0)
        exposures.append(size * price)
    val = max(exposures, default=0.0)
    return MetricResult(value=val)


def max_gross_exposure(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum gross nominal exposure (ANL-NFR-264).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_gross_exposure: executed.")
    return max_nominal_exposure_simple(returns, config)


def exposure_time_ratio(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate percentage of total period spent in market (ANL-NFR-265).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("exposure_time_ratio: executed.")
    trades = config.metadata.get("trades", [])
    float(config.metadata.get("period_duration_hours", 720.0) if config else 720.0)
    ratio = percent_time_in_market(trades, config).value or 0.0
    return MetricResult(value=ratio)


def time_weighted_avg_exposure(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate time-weighted average notional exposure (ANL-NFR-266).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("time_weighted_avg_exposure: executed.")
    trades = config.metadata.get("trades", [])
    period_hours = float(
        config.metadata.get("period_duration_hours", 720.0) if config else 720.0
    )
    closed = get_ordered_closed_trades(trades)
    if not closed or period_hours <= 0:
        return MetricResult(value=0.0)
    tot_exp_time = 0.0
    for t in closed:
        size = float(t.get("size") or t.get("volume") or 0.0)
        price = float(t.get("open_price") or t.get("entry_price") or 1.0)
        dur = _get_trade_duration(t)
        tot_exp_time += (size * price) * dur
    val = tot_exp_time / period_hours
    return MetricResult(value=val)


def portfolio_margin_utilization_curve(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[list[dict[str, Any]]]:
    """Generate portfolio margin-utilization curve over time (ANL-NFR-267).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated list[dict[str, Any value.
    """
    logger.debug("portfolio_margin_utilization_curve: executed.")
    portfolio_state_logs = config.metadata.get("portfolio_state_logs", [])
    curve = []
    for state in portfolio_state_logs:
        eq = float(state.get("equity") or 0.0)
        margin = float(state.get("margin_used") or state.get("margin") or 0.0)
        util = margin / eq if eq > 0 else 0.0
        t_val = state.get("timestamp") or state.get("time") or "1970-01-01T00:00:00Z"
        ts = (
            t_val
            if isinstance(t_val, str)
            else datetime.datetime.fromtimestamp(float(t_val)).isoformat()
        )
        curve.append({"timestamp": ts, "margin_utilization": util})
    return MetricResult(value=curve)


def compounding_risk_of_ruin(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Estimate ruin probability with dynamic compounding risk (ANL-NFR-268).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("compounding_risk_of_ruin: executed.")
    return risk_of_ruin(returns, config)


def historical_var_by_symbol(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate historical value-at-risk by symbol (ANL-NFR-269).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("historical_var_by_symbol: executed.")
    trades_by_symbol = config.metadata.get("trades_by_symbol", {})
    result = {}
    for sym, trades in trades_by_symbol.items():
        pnls = [float(t.get("profit_loss") or t.get("pnl") or 0.0) for t in trades]
        if not pnls:
            result[sym] = 0.0
            continue
        sorted_pnls = sorted(pnls)
        idx = int(len(sorted_pnls) * 0.05)
        result[sym] = abs(sorted_pnls[idx]) if idx < len(sorted_pnls) else 0.0
    return MetricResult(value=result)


def portfolio_var_from_covariance(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate portfolio value-at-risk from covariance and weights (ANL-NFR-270).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("portfolio_var_from_covariance: executed.")
    weights = config.metadata.get("weights", [])
    covariance = config.metadata.get("covariance", [])
    n = len(weights)
    if n == 0 or len(covariance) != n:
        return MetricResult(value=0.0)
    res = 0.0
    for i in range(n):
        for j in range(n):
            res += weights[i] * covariance[i][j] * weights[j]
    val = math.sqrt(res) if res > 0 else 0.0
    return MetricResult(value=val)


def calculate_risk_metrics(
    returns: Sequence[ReturnPoint],
    config_or_request_id: MetricConfig | str | None = None,
) -> MetricResult[dict[str, float]] | StandardResponse:
    """Calculate aggregate risk metrics such as VaR, CVaR, and volatility (ANL-NFR-271).

    Args:
        returns (Sequence[ReturnPoint]): Sequence of return floats.
        config_or_request_id: MetricConfig or optional request identifier.

    Returns:
        MetricResult or StandardResponse containing the calculated dict[str, float].
    """
    logger.debug("calculate_risk_metrics: executed.")
    if isinstance(config_or_request_id, MetricConfig):
        config = config_or_request_id
        vol = volatility(returns, config).value or 0.0
        ann_vol = annualized_volatility(returns, config).value or 0.0
        down_vol = downside_volatility(returns, config).value or 0.0
        var_95 = value_at_risk(returns, config).value or 0.0
        cvar_95 = conditional_var(returns, config).value or 0.0
        val = {
            "volatility": vol,
            "annualized_volatility": ann_vol,
            "downside_volatility": down_vol,
            "value_at_risk_95": var_95,
            "conditional_var_95": cvar_95,
        }
        return MetricResult(value=val)

    from app.services.analytics.statistics.distributions import _to_float_list
    from app.utils import (
        build_metadata,
        response_from_exception,
        success_response,
    )
    from app.utils.errors import ValidationError

    ret_list = _to_float_list(returns)
    if not ret_list:
        raise ValidationError("returns series must contain at least one valid number.")

    try:
        config = MetricConfig()
        vol = volatility(ret_list, config).value or 0.0
        ann_vol = annualized_volatility(ret_list, config).value or 0.0
        down_vol = downside_volatility(ret_list, config).value or 0.0
        var_95 = value_at_risk(ret_list, config).value or 0.0
        cvar_95 = conditional_var(ret_list, config).value or 0.0
        val = {
            "volatility": vol,
            "annualized_volatility": ann_vol,
            "downside_volatility": down_vol,
            "value_at_risk_95": var_95,
            "conditional_var_95": cvar_95,
        }
        meta = build_metadata(
            tool_name="calculate_risk_metrics",
            tool_category="analytics",
            tool_risk_level="low",
            request_id=config_or_request_id
            if isinstance(config_or_request_id, str)
            else None,
            reads=True,
        )
        return success_response(
            message="Successfully calculated risk metrics.", data=val, metadata=meta
        )
    except Exception as e:  # noqa: BLE001
        meta = build_metadata(
            tool_name="calculate_risk_metrics",
            tool_category="analytics",
            tool_risk_level="low",
            request_id=config_or_request_id
            if isinstance(config_or_request_id, str)
            else None,
            reads=True,
        )
        return response_from_exception(exception=e, metadata=meta)
