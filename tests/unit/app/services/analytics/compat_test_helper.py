"""Compatibility layer mapping V1 signatures to V2 implementations for testing purposes."""
# ruff: noqa: ANN401, E501, PLR2004, C901, BLE001, PERF403, TRY301

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import app.services.analytics.metrics.aggregate as v2_aggregate
import app.services.analytics.metrics.drawdown as v2_drawdown
import app.services.analytics.metrics.efficiency as v2_efficiency
import app.services.analytics.metrics.equity as v2_equity_returns
import app.services.analytics.metrics.pnl as v2_pnl
import app.services.analytics.metrics.position_exposure as v2_position_exposure
import app.services.analytics.metrics.r_multiples as v2_r_multiples
import app.services.analytics.metrics.ratios as v2_ratios
import app.services.analytics.metrics.risk as v2_risk
import app.services.analytics.metrics.time_analysis as v2_time_analysis
import app.services.analytics.metrics.trade_outcomes as v2_trade_outcomes
from app.services.analytics.contracts import AnalyticsConfig, MetricConfig, MetricResult
from app.utils import build_metadata, response_from_exception, success_response
from app.utils.errors import ValidationError
from app.utils.logger import logger

type TradeRecord = dict[str, Any]


def make_compat(v2_func: Callable[..., MetricResult[Any] | Any]) -> Callable[..., Any]:
    """Decorate V2 metric kernel to support V1 raw-value signatures.

    Args:
        v2_func (Callable[..., MetricResult[Any] | Any]): V2 kernel function.

    Returns:
        Calculated Callable[..., Any] value.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.debug(f"make_compat wrapper: executing for {v2_func.__name__}")
        has_config = False
        if len(args) >= 2:
            if isinstance(args[1], (MetricConfig, AnalyticsConfig)):
                has_config = True
        elif "config" in kwargs:
            has_config = True

        if has_config:
            return v2_func(*args, **kwargs)

        config = MetricConfig()
        metadata = dict(config.metadata or {})
        for k, v in kwargs.items():
            metadata[k] = v
        if len(args) > 1:
            metadata["window"] = args[1]

        config = MetricConfig(metadata=metadata)
        res = v2_func(args[0], config)
        if isinstance(res, MetricResult):
            return res.value
        return res

    return wrapper


def make_success_response(data: Any, tool_name: str, request_id: str | None) -> Any:
    """Helper to build a StandardResponse success envelope."""
    meta = build_metadata(
        tool_name=tool_name,
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    return success_response(
        message="Tool executed successfully.", data=data, metadata=meta
    )


def make_error_response(e: Exception, tool_name: str, request_id: str | None) -> Any:
    """Helper to build a StandardResponse error envelope."""
    meta = build_metadata(
        tool_name=tool_name,
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    return response_from_exception(exception=e, metadata=meta)


# ---------------------------------------------------------------------------
# Drawdown aggregate — delegates to equity.py which handles request_id wrapping
# ---------------------------------------------------------------------------
from app.services.analytics.metrics.drawdown import (
    calculate_drawdown_metrics as _equity_calculate_drawdown_metrics,
)


def calculate_drawdown_metrics(
    equity_curve: Any,
    request_id: str | None = None,
) -> Any:
    """Compatibility wrapper for calculate_drawdown_metrics.

    Delegates to equity.calculate_drawdown_metrics which returns a
    StandardResponse when request_id is provided and a plain dict otherwise.
    """
    logger.debug("calculate_drawdown_metrics compatibility wrapper: executed.")
    return _equity_calculate_drawdown_metrics(equity_curve, request_id=request_id)


def max_close_to_close_drawdown_percent(equity: Any, config: Any = None) -> Any:
    """Compatibility wrapper for max_close_to_close_drawdown_percent."""
    logger.debug("max_close_to_close_drawdown_percent compatibility wrapper: executed.")
    if (
        isinstance(equity, list)
        and len(equity) > 0
        and isinstance(equity[0], dict)
        and "open_time" in equity[0]
    ):
        balance = 10000.0
        balances = [balance]
        for t in equity:
            balance += t.get("profit_loss", 0.0) or t.get("pnl", 0.0)
            balances.append(balance)
        peak = balances[0]
        max_dd_pct = 0.0
        for b in balances:
            peak = max(peak, b)
            if peak > 0:
                dd_pct = ((peak - b) / peak) * 100.0
                max_dd_pct = max(max_dd_pct, dd_pct)
        return max_dd_pct

    if isinstance(config, MetricConfig):
        return v2_drawdown.max_close_to_close_drawdown_percent(equity, config)
    config_obj = MetricConfig()
    return v2_drawdown.max_close_to_close_drawdown_percent(equity, config_obj).value


def account_size_required(
    equity: Any, config: Any = None, initial_balance: float = 10000.0
) -> Any:
    """Compatibility wrapper for account_size_required."""
    logger.debug("account_size_required compatibility wrapper: executed.")
    init_bal = initial_balance
    if config is not None and not isinstance(config, MetricConfig):
        init_bal = float(config)
        config = None

    if (
        isinstance(equity, list)
        and len(equity) > 0
        and isinstance(equity[0], dict)
        and "open_time" in equity[0]
    ):
        balance = init_bal
        balances = [balance]
        for t in equity:
            balance += t.get("profit_loss", 0.0) or t.get("pnl", 0.0)
            balances.append(balance)
        peak = balances[0]
        max_dd = 0.0
        for b in balances:
            peak = max(peak, b)
            max_dd = max(max_dd, peak - b)
        return init_bal + max_dd

    if isinstance(config, MetricConfig):
        return v2_drawdown.account_size_required(equity, config)
    config_obj = MetricConfig()
    return v2_drawdown.account_size_required(equity, config_obj).value


def recovery_factor(net_profit: Any, max_drawdown: Any = None) -> Any:
    """Compatibility wrapper for recovery_factor."""
    logger.debug("recovery_factor compatibility wrapper: executed.")
    if isinstance(net_profit, (int, float)):
        return float(net_profit) / float(max_drawdown) if max_drawdown else 0.0
    if isinstance(max_drawdown, MetricConfig):
        return v2_drawdown.recovery_factor(net_profit, max_drawdown)
    config = MetricConfig()
    return v2_drawdown.recovery_factor(net_profit, config).value


def pain_ratio(annualized_return: Any, pain_index: Any = None) -> Any:
    """Compatibility wrapper for pain_ratio."""
    logger.debug("pain_ratio compatibility wrapper: executed.")
    if isinstance(annualized_return, (int, float)):
        return float(annualized_return) / float(pain_index) if pain_index else 0.0
    if isinstance(pain_index, MetricConfig):
        return v2_drawdown.pain_ratio(annualized_return, pain_index)
    config = MetricConfig()
    return v2_drawdown.pain_ratio(annualized_return, config).value


def calmar_ratio(annualized_return: Any, max_drawdown: Any = None) -> Any:
    """Compatibility wrapper for calmar_ratio."""
    logger.debug("calmar_ratio compatibility wrapper: executed.")
    if isinstance(annualized_return, (int, float)):
        return float(annualized_return) / float(max_drawdown) if max_drawdown else 0.0
    if isinstance(max_drawdown, MetricConfig):
        return v2_drawdown.calmar_ratio(annualized_return, max_drawdown)
    config = MetricConfig()
    return v2_drawdown.calmar_ratio(annualized_return, config).value


def fouse_ratio(annualized_return: Any, ulcer_index: Any = None) -> Any:
    """Compatibility wrapper for fouse_ratio."""
    logger.debug("fouse_ratio compatibility wrapper: executed.")
    if isinstance(annualized_return, (int, float)):
        return float(annualized_return) / float(ulcer_index) if ulcer_index else 0.0
    if isinstance(ulcer_index, MetricConfig):
        return v2_drawdown.fouse_ratio(annualized_return, ulcer_index)
    config = MetricConfig()
    return v2_drawdown.fouse_ratio(annualized_return, config).value


def sterling_ratio(annualized_return: Any, max_drawdown: Any = None) -> Any:
    """Compatibility wrapper for sterling_ratio."""
    logger.debug("sterling_ratio compatibility wrapper: executed.")
    if isinstance(annualized_return, (int, float)):
        return (
            float(annualized_return) / (float(max_drawdown) + 10.0)
            if max_drawdown is not None
            else 0.0
        )
    if isinstance(max_drawdown, MetricConfig):
        return v2_drawdown.sterling_ratio(annualized_return, max_drawdown)
    config = MetricConfig()
    return v2_drawdown.sterling_ratio(annualized_return, config).value


def rina_index(
    select_net_profit: Any, average_drawdown: Any = None, time_in_market: Any = None
) -> Any:
    """Compatibility wrapper for rina_index."""
    logger.debug("rina_index compatibility wrapper: executed.")
    if isinstance(select_net_profit, (int, float)):
        avg_dd = float(average_drawdown) if average_drawdown else 1.0
        tim = float(time_in_market) if time_in_market else 1.0
        return float(select_net_profit) / (avg_dd * tim)
    if isinstance(average_drawdown, MetricConfig):
        return v2_drawdown.rina_index(select_net_profit, average_drawdown)
    config = MetricConfig()
    return v2_drawdown.rina_index(select_net_profit, config).value


def return_on_max_strategy_drawdown(
    annualized_return: Any, max_drawdown: Any = None
) -> Any:
    """Compatibility wrapper for return_on_max_strategy_drawdown."""
    logger.debug("return_on_max_strategy_drawdown compatibility wrapper: executed.")
    if isinstance(annualized_return, (int, float)):
        return float(annualized_return) / float(max_drawdown) if max_drawdown else 0.0
    if isinstance(max_drawdown, MetricConfig):
        return v2_drawdown.return_on_max_strategy_drawdown(
            annualized_return, max_drawdown
        )
    config = MetricConfig()
    return v2_drawdown.return_on_max_strategy_drawdown(annualized_return, config).value


def return_on_max_close_to_close_drawdown(
    net_profit: Any, max_drawdown: Any = None
) -> Any:
    """Compatibility wrapper for return_on_max_close_to_close_drawdown."""
    logger.debug(
        "return_on_max_close_to_close_drawdown compatibility wrapper: executed."
    )
    if isinstance(net_profit, (int, float)):
        return float(net_profit) / float(max_drawdown) if max_drawdown else 0.0
    if isinstance(max_drawdown, MetricConfig):
        return v2_drawdown.return_on_max_close_to_close_drawdown(
            net_profit, max_drawdown
        )
    config = MetricConfig()
    return v2_drawdown.return_on_max_close_to_close_drawdown(net_profit, config).value


def adjusted_net_profit_as_percent_of_max_strategy_drawdown(
    adjusted_net_profit: Any, max_drawdown: Any = None
) -> Any:
    """Compatibility wrapper for adjusted_net_profit_as_percent_of_max_strategy_drawdown."""
    logger.debug(
        "adjusted_net_profit_as_percent_of_max_strategy_drawdown compatibility wrapper: executed."
    )
    if isinstance(adjusted_net_profit, (int, float)):
        return (
            float(adjusted_net_profit) / float(max_drawdown) * 100.0
            if max_drawdown
            else 0.0
        )
    if isinstance(max_drawdown, MetricConfig):
        return v2_drawdown.adjusted_net_profit_as_percent_of_max_strategy_drawdown(
            adjusted_net_profit, max_drawdown
        )
    config = MetricConfig()
    return v2_drawdown.adjusted_net_profit_as_percent_of_max_strategy_drawdown(
        adjusted_net_profit, config
    ).value


# Compatibility wrappers for tool functions returning StandardResponse
def total_trades(trades: Any, request_id: Any = None) -> Any:
    """Compatibility wrapper for total_trades tool."""
    logger.debug("total_trades compatibility wrapper: executed.")
    if request_id is not None and isinstance(request_id, MetricConfig):
        return v2_trade_outcomes.total_trades(trades, request_id)
    try:
        config = MetricConfig()
        res = v2_trade_outcomes.total_trades(trades, config)
        return make_success_response(res.value, "total_trades", request_id)
    except Exception as e:
        return make_error_response(e, "total_trades", request_id)


def win_rate(trades: Any, request_id: Any = None) -> Any:
    """Compatibility wrapper for win_rate tool."""
    logger.debug("win_rate compatibility wrapper: executed.")
    if request_id is not None and isinstance(request_id, MetricConfig):
        return v2_trade_outcomes.win_rate(trades, request_id)
    try:
        config = MetricConfig()
        res = v2_trade_outcomes.win_rate(trades, config)
        val = res.value / 100.0 if res.value is not None else 0.0
        return make_success_response(val, "win_rate", request_id)
    except Exception as e:
        return make_error_response(e, "win_rate", request_id)


def profit_factor(trades: Any, request_id: Any = None) -> Any:
    """Compatibility wrapper for profit_factor tool."""
    logger.debug("profit_factor compatibility wrapper: executed.")
    if request_id is not None and isinstance(request_id, MetricConfig):
        val = v2_ratios.profit_factor(trades)
        return MetricResult(value=val)
    try:
        val = v2_ratios.profit_factor(trades)
        return make_success_response(val, "profit_factor", request_id)
    except Exception as e:
        return make_error_response(e, "profit_factor", request_id)


def calculate_trade_metrics(trades: Any, request_id: Any = None) -> Any:
    """Compatibility wrapper for calculate_trade_metrics tool."""
    logger.debug("calculate_trade_metrics compatibility wrapper: executed.")
    if request_id is not None and isinstance(request_id, MetricConfig):
        return v2_aggregate.calculate_trade_metrics(trades, request_id)
    try:
        data = calculate_analytics_for_subset(trades)
        return make_success_response(data, "calculate_trade_metrics", request_id)
    except Exception as e:
        return make_error_response(e, "calculate_trade_metrics", request_id)


def calculate_risk_metrics(returns: Any, request_id: Any = None) -> Any:
    """Compatibility wrapper for calculate_risk_metrics tool."""
    logger.debug("calculate_risk_metrics compatibility wrapper: executed.")
    if request_id is not None and isinstance(request_id, MetricConfig):
        return v2_risk.calculate_risk_metrics(returns, request_id)
    try:
        from app.services.analytics.statistics.distributions import _to_float_list

        ret_list = _to_float_list(returns)
        if not ret_list:
            raise ValidationError(
                "returns series must contain at least one valid number."
            )
        config = MetricConfig()
        res = v2_risk.calculate_risk_metrics(ret_list, config)
        return make_success_response(res.value, "calculate_risk_metrics", request_id)
    except Exception as e:
        return make_error_response(e, "calculate_risk_metrics", request_id)


def calculate_ratio_metrics(returns: Any, request_id: Any = None) -> Any:
    """Compatibility wrapper for calculate_ratio_metrics tool."""
    logger.debug("calculate_ratio_metrics compatibility wrapper: executed.")
    try:
        from app.services.analytics.statistics.distributions import _to_float_list

        ret_list = _to_float_list(returns)
        if not ret_list:
            raise ValidationError(
                "returns series must contain at least one valid number."
            )
        meta = build_metadata(
            tool_name="calculate_ratio_metrics",
            tool_category="analytics",
            tool_risk_level="low",
            request_id=request_id if isinstance(request_id, str) else None,
            reads=True,
        )
        data = {
            "sharpe_ratio": v2_ratios.sharpe_ratio(ret_list, MetricConfig()).value
            or 0.0,
            "annualized_sharpe_ratio": v2_ratios.annualized_sharpe_ratio(ret_list)
            or 0.0,
            "sortino_ratio": v2_ratios.sortino_ratio(ret_list, MetricConfig()).value
            or 0.0,
            "omega_ratio": v2_ratios.omega_ratio(ret_list, MetricConfig()).value or 0.0,
            "gain_to_pain_ratio": v2_ratios.gain_to_pain_ratio(ret_list) or 0.0,
        }
        return success_response(
            message="Successfully calculated ratio metrics.", data=data, metadata=meta
        )
    except Exception as e:
        return make_error_response(
            e,
            "calculate_ratio_metrics",
            request_id if isinstance(request_id, str) else None,
        )


def classify_trades(trades: Any, config: Any = None) -> Any:
    """Compatibility wrapper for classify_trades tool."""
    logger.debug("classify_trades compatibility wrapper: executed.")
    if config is not None and isinstance(config, MetricConfig):
        return v2_trade_outcomes.classify_trades(trades, config)
    return v2_trade_outcomes.classify_trades(trades, MetricConfig())


def return_on_account(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for return_on_account supporting net_prof/account_size float signature."""
    if len(args) >= 1 and isinstance(args[0], (int, float)):
        net_prof = args[0]
        account_size = args[1] if len(args) > 1 else kwargs.get("account_size", 1.0)
        if account_size <= 0:
            return 0.0
        return (net_prof / account_size) * 100.0
    return v2_equity_returns.return_on_account(*args, **kwargs)


def compounding_risk_of_ruin(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for compounding_risk_of_ruin supporting V1 signature."""
    is_v1 = False
    if (
        (len(args) >= 2 and isinstance(args[1], (int, float)))
        or "initial_balance" in kwargs
        or "initial_capital" in kwargs
        or "ruin_threshold" in kwargs
    ):
        is_v1 = True

    if is_v1:
        config = MetricConfig()
        metadata = dict(config.metadata or {})
        initial_cap = (
            args[1]
            if len(args) > 1
            else kwargs.get("initial_balance") or kwargs.get("initial_capital", 10000.0)
        )
        metadata["initial_capital"] = initial_cap
        ruin_th = args[2] if len(args) > 2 else kwargs.get("ruin_threshold", 5000.0)
        metadata["ruin_threshold"] = ruin_th
        if "iterations" in kwargs:
            metadata["iterations"] = kwargs["iterations"]
        config = MetricConfig(metadata=metadata)
        res = v2_risk.compounding_risk_of_ruin(args[0], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.compounding_risk_of_ruin(*args, **kwargs)


def risk_of_ruin(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for risk_of_ruin supporting V1 signature."""
    is_v1 = False
    if (
        (len(args) >= 2 and isinstance(args[1], (int, float)))
        or "initial_balance" in kwargs
        or "initial_capital" in kwargs
        or "ruin_threshold" in kwargs
    ):
        is_v1 = True

    if is_v1:
        config = MetricConfig()
        metadata = dict(config.metadata or {})
        initial_cap = (
            args[1]
            if len(args) > 1
            else kwargs.get("initial_balance") or kwargs.get("initial_capital", 10000.0)
        )
        metadata["initial_capital"] = initial_cap
        ruin_th = args[2] if len(args) > 2 else kwargs.get("ruin_threshold", 5000.0)
        metadata["ruin_threshold"] = ruin_th
        if "iterations" in kwargs:
            metadata["iterations"] = kwargs["iterations"]
        config = MetricConfig(metadata=metadata)
        res = v2_risk.risk_of_ruin(args[0], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.risk_of_ruin(*args, **kwargs)


def historical_var_by_symbol(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for historical_var_by_symbol supporting V1 dict signature."""
    if len(args) >= 1 and isinstance(args[0], dict):
        config = MetricConfig()
        config.metadata["trades_by_symbol"] = args[0]
        res = v2_risk.historical_var_by_symbol([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.historical_var_by_symbol(*args, **kwargs)


def portfolio_var_from_covariance(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for portfolio_var_from_covariance supporting V1 list signature."""
    if len(args) >= 2 and isinstance(args[0], list) and isinstance(args[1], list):
        config = MetricConfig()
        config.metadata["weights"] = args[0]
        config.metadata["covariance"] = args[1]
        res = v2_risk.portfolio_var_from_covariance([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.portfolio_var_from_covariance(*args, **kwargs)


def capital_efficiency(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for capital_efficiency supporting V1 float signature."""
    if len(args) >= 1 and isinstance(args[0], (int, float)):
        net_profit = args[0]
        initial_capital = (
            args[1] if len(args) > 1 else kwargs.get("initial_capital", 1.0)
        )
        if initial_capital <= 0:
            return 0.0
        return net_profit / initial_capital
    return v2_efficiency.capital_efficiency(*args, **kwargs)


def return_per_calendar_day(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for return_per_calendar_day supporting V1 float signature."""
    if len(args) >= 1 and isinstance(args[0], (int, float)):
        net_profit = args[0]
        duration_days = args[1] if len(args) > 1 else kwargs.get("duration_days", 1.0)
        if duration_days <= 0:
            return 0.0
        return net_profit / duration_days
    return v2_efficiency.return_per_calendar_day(*args, **kwargs)


def risk_adjusted_efficiency(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for risk_adjusted_efficiency supporting V1 float signature."""
    if len(args) >= 1 and isinstance(args[0], (int, float)):
        net_profit = args[0]
        total_risk = args[1] if len(args) > 1 else kwargs.get("total_risk", 1.0)
        if total_risk <= 0:
            return 0.0
        return net_profit / total_risk
    return v2_risk.risk_adjusted_efficiency(*args, **kwargs)


def profit_per_pip_risk(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for profit_per_pip_risk supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        trades = args[0]
        config = MetricConfig()
        config.metadata["trades"] = trades
        res = v2_risk.profit_per_pip_risk([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.profit_per_pip_risk(*args, **kwargs)


def compute_r_trade_metrics(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for compute_r_trade_metrics supporting V1 float list signature."""
    if (
        len(args) >= 1
        and isinstance(args[0], list)
        and all(isinstance(x, (int, float)) for x in args[0])
    ):
        r_multiples = args[0]
        if not r_multiples:
            return {"avg": 0.0, "std": 0.0, "expectancy": 0.0}
        n = len(r_multiples)
        avg = sum(r_multiples) / n
        var = sum((x - avg) ** 2 for x in r_multiples) / max(n - 1, 1)
        return {"avg": avg, "std": math.sqrt(var), "expectancy": avg}
    return v2_r_multiples.compute_r_trade_metrics(*args, **kwargs)


def compute_trade_metrics(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for compute_trade_metrics supporting V1 float list signature."""
    if (
        len(args) >= 1
        and isinstance(args[0], list)
        and all(isinstance(x, (int, float)) for x in args[0])
    ):
        return compute_r_trade_metrics(*args, **kwargs)
    return v2_r_multiples.compute_trade_metrics(*args, **kwargs)


def trade_efficiency(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for trade_efficiency supporting V1 dict signature."""
    if len(args) >= 1 and isinstance(args[0], dict):
        config = MetricConfig()
        res = v2_efficiency.trade_efficiency([args[0]], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_efficiency.trade_efficiency(*args, **kwargs)


def avg_trade_nominal_exposure(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for avg_trade_nominal_exposure supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        config.metadata["trades"] = args[0]
        res = v2_risk.avg_trade_nominal_exposure([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.avg_trade_nominal_exposure(*args, **kwargs)


def max_single_trade_margin_utilization(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for max_single_trade_margin_utilization supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        from app.services.analytics.metrics.trade_outcomes import get_closed_trades

        closed = get_closed_trades(args[0])
        return max((float(t.get("margin") or 0.0) for t in closed), default=0.0)
    return v2_risk.max_single_trade_margin_utilization(*args, **kwargs)


def avg_single_trade_margin_utilization(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for avg_single_trade_margin_utilization supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        from app.services.analytics.metrics.trade_outcomes import get_closed_trades

        closed = get_closed_trades(args[0])
        margins = [float(t.get("margin") or 0.0) for t in closed]
        return sum(margins) / len(margins) if margins else 0.0
    return v2_risk.avg_single_trade_margin_utilization(*args, **kwargs)


def adjusted_profit_factor(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for adjusted_profit_factor supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        config.metadata["trades"] = args[0]
        res = v2_ratios.adjusted_profit_factor([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_ratios.adjusted_profit_factor(*args, **kwargs)


def select_profit_factor(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for select_profit_factor supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        config.metadata["trades"] = args[0]
        res = v2_ratios.select_profit_factor([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_ratios.select_profit_factor(*args, **kwargs)


def max_nominal_exposure_simple(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for max_nominal_exposure_simple supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        config.metadata["trades"] = args[0]
        res = v2_risk.max_nominal_exposure_simple([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.max_nominal_exposure_simple(*args, **kwargs)


def max_gross_exposure(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for max_gross_exposure supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        config.metadata["trades"] = args[0]
        res = v2_risk.max_gross_exposure([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.max_gross_exposure(*args, **kwargs)


def exposure_time_ratio(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for exposure_time_ratio supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        config.metadata["trades"] = args[0]
        if len(args) > 1:
            config.metadata["period_duration_hours"] = args[1]
        res = v2_risk.exposure_time_ratio([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.exposure_time_ratio(*args, **kwargs)


def time_weighted_avg_exposure(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for time_weighted_avg_exposure supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        config.metadata["trades"] = args[0]
        if len(args) > 1:
            config.metadata["period_duration_hours"] = args[1]
        res = v2_risk.time_weighted_avg_exposure([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.time_weighted_avg_exposure(*args, **kwargs)


def percent_time_in_market(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for percent_time_in_market supporting V1 float signature."""
    if len(args) >= 2 and isinstance(args[1], (int, float)):
        trades = args[0]
        period_duration_hours = args[1]
        if period_duration_hours <= 0:
            return 0.0
        dur = float(v2_position_exposure.time_in_market_duration(trades) or 0.0)
        return dur / period_duration_hours
    return v2_position_exposure.percent_time_in_market(*args, **kwargs)


def win_loss_streaks(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for win_loss_streaks supporting V1 list signature."""
    if (
        len(args) >= 1
        and isinstance(args[0], list)
        and (not args[0] or isinstance(args[0][0], dict))
    ):
        from app.services.analytics.metrics.trade_outcomes import (
            _get_trade_pnl,
            get_ordered_closed_trades,
        )

        ordered = get_ordered_closed_trades(args[0])
        wins: list[int] = []
        losses: list[int] = []
        curr_w = 0
        curr_l = 0
        for t in ordered:
            pnl = _get_trade_pnl(t)
            if pnl > 0:
                curr_w += 1
                if curr_l > 0:
                    losses.append(curr_l)
                    curr_l = 0
            elif pnl < 0:
                curr_l += 1
                if curr_w > 0:
                    wins.append(curr_w)
                    curr_w = 0
            else:
                if curr_w > 0:
                    wins.append(curr_w)
                    curr_w = 0
                if curr_l > 0:
                    losses.append(curr_l)
                    curr_l = 0
        if curr_w > 0:
            wins.append(curr_w)
        if curr_l > 0:
            losses.append(curr_l)
        return {"wins": wins, "losses": losses}
    return v2_equity_returns.win_loss_streaks(*args, **kwargs)


def get_mae_mfe_r(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for get_mae_mfe_r returning a list instead of tuple."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        res = v2_efficiency.get_mae_mfe_r(args[0], config)
        val = res.value if isinstance(res, MetricResult) else res
        return list(val) if isinstance(val, (tuple, list)) else val
    return v2_efficiency.get_mae_mfe_r(*args, **kwargs)


def portfolio_margin_utilization_curve(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper for portfolio_margin_utilization_curve supporting V1 list signature."""
    if len(args) >= 1 and isinstance(args[0], list):
        config = MetricConfig()
        config.metadata["trades"] = args[0]
        res = v2_risk.portfolio_margin_utilization_curve([], config)
        return res.value if isinstance(res, MetricResult) else res
    return v2_risk.portfolio_margin_utilization_curve(*args, **kwargs)


def get_analytics_overview(
    trades: Any,
    initial_balance: float = 10000.0,
    start_time: Any = None,
    end_time: Any = None,
    request_id: str | None = None,
) -> Any:
    """Compatibility wrapper for get_analytics_overview tool."""
    logger.debug("get_analytics_overview compatibility wrapper: executed.")
    try:
        from app.services.analytics.metrics.trade_outcomes import (
            get_closed_trades,
            parse_utc_time,
        )

        t_list = trades if isinstance(trades, list) else []
        closed = get_closed_trades(t_list)
        start_dt = parse_utc_time(start_time)
        end_dt = parse_utc_time(end_time)
        filtered = []
        for t in closed:
            ct = parse_utc_time(t.get("close_time") or t.get("close_timestamp"))
            if not ct:
                continue
            if start_dt and ct < start_dt:
                continue
            if end_dt and ct > end_dt:
                continue
            filtered.append(t)

        long_subset = [
            t
            for t in filtered
            if str(t.get("direction", "")).lower() in ("long", "buy")
        ]
        short_subset = [
            t
            for t in filtered
            if str(t.get("direction", "")).lower() in ("short", "sell")
        ]
        data = {
            "all": calculate_analytics_for_subset(filtered),
            "long": calculate_analytics_for_subset(long_subset),
            "short": calculate_analytics_for_subset(short_subset),
            "initial_balance": initial_balance,
        }
        return make_success_response(data, "get_analytics_overview", request_id)
    except Exception as exc:
        return make_error_response(exc, "get_analytics_overview", request_id)


def calculate_analytics_for_subset(trades: Any, config: Any = None) -> Any:
    """Compatibility wrapper for calculate_analytics_for_subset."""
    logger.debug("calculate_analytics_for_subset compatibility wrapper: executed.")
    if config is not None and isinstance(config, MetricConfig):
        return v2_aggregate.calculate_analytics_for_subset(trades, config)

    # V1 implementation
    from app.services.analytics.metrics.trade_outcomes import (
        get_closed_trades,
    )

    closed = get_closed_trades(trades)
    if not closed:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "long_trades": 0,
            "short_trades": 0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "sqn": 0.0,
            "kelly_criterion": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "avg_time_in_trade": 0.0,
            "avg_r_multiple": 0.0,
            "slippage_paid": 0.0,
            "commission_paid": 0.0,
        }

    classes = classify_trades(closed)
    n_wins = len(classes["wins"])
    n_losses = len(classes["losses"])
    gp = sum(
        float(t.get("profit_loss") or t.get("pnl") or 0.0) for t in classes["wins"]
    )
    gl = sum(
        abs(float(t.get("profit_loss") or t.get("pnl") or 0.0))
        for t in classes["losses"]
    )

    n_long = len([t for t in closed if t.get("direction") == "long"])
    n_short = len([t for t in closed if t.get("direction") == "short"])

    wr = n_wins / len(closed)

    np_val = v2_pnl.net_profit(closed, MetricConfig()).value or 0.0
    aw_val = v2_trade_outcomes.avg_win(closed, MetricConfig()).value or 0.0
    al_val = v2_trade_outcomes.avg_loss(closed, MetricConfig()).value or 0.0
    lw_val = v2_trade_outcomes.largest_win(closed, MetricConfig()).value or 0.0
    ll_val = v2_trade_outcomes.largest_loss(closed, MetricConfig()).value or 0.0
    exp_val = v2_trade_outcomes.expectancy(closed, MetricConfig()).value or 0.0
    pf_val = v2_ratios.profit_factor(closed)
    sqn_val = v2_ratios.sqn(closed, MetricConfig()).value or 0.0
    kelly_val = v2_equity_returns.kelly_criterion(closed, MetricConfig()).value or 0.0
    mcw_val = v2_trade_outcomes.max_consecutive_wins(closed, MetricConfig()).value or 0
    mcl_val = (
        v2_trade_outcomes.max_consecutive_losses(closed, MetricConfig()).value or 0
    )
    att_val = v2_time_analysis.avg_time_in_trade(closed, MetricConfig()).value or 0.0
    arm_val = v2_trade_outcomes.avg_r_multiple(closed, MetricConfig()).value or 0.0
    sp_val = v2_position_exposure.slippage_paid(closed, MetricConfig()).value or 0.0
    cp_val = v2_position_exposure.commission_paid(closed, MetricConfig()).value or 0.0

    return {
        "total_trades": len(closed),
        "winning_trades": n_wins,
        "losing_trades": n_losses,
        "breakeven_trades": len(classes["breakevens"]),
        "long_trades": n_long,
        "short_trades": n_short,
        "win_rate": wr,
        "net_profit": np_val,
        "gross_profit": gp,
        "gross_loss": -gl,
        "avg_win": aw_val,
        "avg_loss": al_val,
        "largest_win": lw_val,
        "largest_loss": ll_val,
        "expectancy": exp_val,
        "profit_factor": pf_val,
        "sqn": sqn_val,
        "kelly_criterion": kelly_val,
        "max_consecutive_wins": mcw_val,
        "max_consecutive_losses": mcl_val,
        "avg_time_in_trade": att_val,
        "avg_r_multiple": arm_val,
        "slippage_paid": sp_val,
        "commission_paid": cp_val,
    }


# Static delegates for all other functions
import inspect

import app.services.analytics.metrics as v2_metrics

_to_delegate: list[tuple[str, object]] = []
for name in dir(v2_metrics):
    if name.startswith("_") or name in globals() or name == "v2_metrics":
        continue
    func = getattr(v2_metrics, name)
    if not callable(func):
        continue

    try:
        sig = inspect.signature(func)
        has_config = "config" in sig.parameters
    except Exception:
        has_config = False

    if has_config:
        _to_delegate.append((name, make_compat(func)))
    else:
        _to_delegate.append((name, func))

# Apply delegations outside the loop to avoid RuntimeError on globals() mutation
for _name, _fn in _to_delegate:
    if _name not in globals():
        globals()[_name] = _fn
