# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Group-level composition and aggregation of metrics (ANL-NFR-100)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.utils import StandardResponse  # noqa: TC001
from app.utils.logger import logger

type TradeRecord = dict[str, Any]
type ReturnPoint = Any


def metrics_aggregate_boundary() -> dict[str, object]:
    """Describe aggregate metric boundary rules from the analytics architecture.

    Returns:
        Boundary evidence for closed-trade semantics, cost handling, context
        preservation, report sections, and deterministic hash coverage.
    """
    logger.debug("metrics_aggregate_boundary: executed.")
    return {
        "closed_trade_semantics": True,
        "excludes_open_or_placeholder_records": True,
        "merged_exposure_intervals": True,
        "direction_uses_trade_fields_not_pnl": True,
        "cost_inputs_are_read_only": ("spread", "slippage", "commission"),
        "source_contexts": (
            "all_trades",
            "long_trades",
            "short_trades",
            "benchmark_comparisons",
            "cost_analysis",
            "statistical_validation",
        ),
        "report_sections": (
            "summary",
            "trade_metrics",
            "equity_metrics",
            "return_metrics",
            "drawdown_metrics",
            "risk_metrics",
            "ratio_metrics",
            "distribution_metrics",
            "benchmark_metrics",
            "efficiency_metrics",
            "statistical_validation",
            "cost_breakdown",
            "warnings",
            "quality_flags",
            "dashboard_payloads",
            "lineage",
            "metadata",
        ),
        "hashes": (
            "input_hash",
            "config_hash",
            "report_hash",
            "trade_ledger_hash",
            "equity_curve_hash",
            "benchmark_hash",
        ),
    }


def breakeven_epsilon(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[float]:
    """Return the configured breakeven epsilon value (ANL-NFR-102).

    Args:
        input_value: Input value or list of values. Not used for this metric.
        config: Metric configuration containing the breakeven epsilon.

    Returns:
        MetricResult containing the breakeven epsilon float.
    """
    eps = float(config.breakeven_epsilon if config else 1e-9)
    logger.debug(f"breakeven_epsilon: resolved epsilon: {eps}")
    return MetricResult(value=eps)


def calculate_trade_metrics(
    input_value: object,
    config_or_request_id: MetricConfig | str | None = None,
) -> MetricResult[dict[str, Any]] | StandardResponse:
    """Calculate aggregate core trade metrics from normalized trade records (ANL-NFR-160).

    Args:
        input_value: Sequence of trade record dictionaries.
        config_or_request_id: MetricConfig or optional request identifier.

    Returns:
        MetricResult or StandardResponse containing calculated trade metrics dictionary.
    """
    logger.debug("calculate_trade_metrics: starting calculation.")
    if isinstance(config_or_request_id, MetricConfig):
        config = config_or_request_id
        trades = input_value if isinstance(input_value, Sequence) else ()
        from app.services.analytics.metrics.ratios import (
            payoff_ratio_metric,
            profit_factor_metric,
        )
        from app.services.analytics.metrics.trade_outcomes import (
            avg_consecutive_losses,
            avg_consecutive_wins,
            avg_loss_metric,
            avg_win_metric,
            consecutive_wins_losses,
            expectancy_r,
            win_rate_fraction,
        )

        win_rate = win_rate_fraction(trades, config).value or 0.0
        pf = profit_factor_metric(trades, config).value or 0.0
        payoff = payoff_ratio_metric(trades, config).value or 0.0
        exp_r = expectancy_r(trades, config).value or 0.0
        streaks = consecutive_wins_losses(trades, config).value or {
            "wins": 0,
            "losses": 0,
        }
        aw = avg_win_metric(trades, config).value or 0.0
        al = avg_loss_metric(trades, config).value or 0.0
        avg_win_streak = avg_consecutive_wins(trades, config).value or 0.0
        avg_loss_streak = avg_consecutive_losses(trades, config).value or 0.0

        val = {
            "win_rate": win_rate,
            "profit_factor": pf,
            "payoff_ratio": payoff,
            "r_expectancy": exp_r,
            "max_consecutive_wins": streaks.get("wins", 0),
            "max_consecutive_losses": streaks.get("losses", 0),
            "avg_win": aw,
            "avg_loss": al,
            "avg_win_streak": avg_win_streak,
            "avg_loss_streak": avg_loss_streak,
        }
        logger.debug(f"calculate_trade_metrics: finished calculation, metrics: {val}")
        return MetricResult(value=val)

    from app.utils import (
        build_metadata,
        response_from_exception,
        success_response,
    )

    try:
        from app.services.analytics.metrics.ratios import (
            payoff_ratio_metric,
            profit_factor_metric,
        )
        from app.services.analytics.metrics.trade_outcomes import (
            avg_consecutive_losses,
            avg_consecutive_wins,
            avg_loss_metric,
            avg_win_metric,
            consecutive_wins_losses,
            expectancy_r,
            win_rate_fraction,
        )

        trades = input_value if isinstance(input_value, Sequence) else ()
        config = MetricConfig()
        win_rate = win_rate_fraction(trades, config).value or 0.0
        pf = profit_factor_metric(trades, config).value or 0.0
        payoff = payoff_ratio_metric(trades, config).value or 0.0
        exp_r = expectancy_r(trades, config).value or 0.0
        streaks = consecutive_wins_losses(trades, config).value or {
            "wins": 0,
            "losses": 0,
        }
        aw = avg_win_metric(trades, config).value or 0.0
        al = avg_loss_metric(trades, config).value or 0.0
        avg_win_streak = avg_consecutive_wins(trades, config).value or 0.0
        avg_loss_streak = avg_consecutive_losses(trades, config).value or 0.0

        val = {
            "win_rate": win_rate,
            "profit_factor": pf,
            "payoff_ratio": payoff,
            "r_expectancy": exp_r,
            "max_consecutive_wins": streaks.get("wins", 0),
            "max_consecutive_losses": streaks.get("losses", 0),
            "avg_win": aw,
            "avg_loss": al,
            "avg_win_streak": avg_win_streak,
            "avg_loss_streak": avg_loss_streak,
        }
        meta = build_metadata(
            tool_name="calculate_trade_metrics",
            tool_category="analytics",
            tool_risk_level="low",
            request_id=config_or_request_id
            if isinstance(config_or_request_id, str)
            else None,
            reads=True,
        )
        return success_response(
            message="Successfully calculated trade metrics.", data=val, metadata=meta
        )
    except Exception as e:  # noqa: BLE001
        meta = build_metadata(
            tool_name="calculate_trade_metrics",
            tool_category="analytics",
            tool_risk_level="low",
            request_id=config_or_request_id
            if isinstance(config_or_request_id, str)
            else None,
            reads=True,
        )
        return response_from_exception(exception=e, metadata=meta)


def calculate_analytics_for_subset(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[dict[str, Any]]:
    """Calculate all analytics categories for a supplied trade subset (ANL-NFR-161).

    Args:
        input_value: Sequence of trade record dictionaries.
        config: Metric configuration.

    Returns:
        MetricResult containing subset analytics dictionary.
    """
    logger.debug("calculate_analytics_for_subset: starting calculation.")
    trades = input_value if isinstance(input_value, Sequence) else ()
    res = calculate_trade_metrics(trades, config)
    trade_metrics = res.value if isinstance(res, MetricResult) else {}

    from app.services.analytics.metrics.drawdown import max_close_to_close_drawdown

    max_dd = max_close_to_close_drawdown(trades, config).value or 0.0

    from app.services.analytics.metrics.position_exposure import (
        commission_paid,
        slippage_paid,
        swap_paid,
    )

    slip = slippage_paid(trades, config).value or 0.0
    comm = commission_paid(trades, config).value or 0.0
    swap = swap_paid(trades, config).value or 0.0

    val = {
        "trade_metrics": trade_metrics,
        "max_drawdown": max_dd,
        "total_slippage": slip,
        "total_commission": comm,
        "total_swap": swap,
    }
    logger.debug("calculate_analytics_for_subset: finished calculation.")
    return MetricResult(value=val)


def compute_equity_metrics(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[dict[str, Any]]:
    """Calculate equity metrics from return inputs (ANL-NFR-189).

    Args:
        input_value: Sequence of return floats.
        config: Metric configuration.

    Returns:
        MetricResult containing calculated equity metrics.
    """
    logger.debug("compute_equity_metrics: starting calculation.")
    returns = input_value if isinstance(input_value, Sequence) else ()
    from app.services.analytics.metrics.equity import calculate_return_metrics
    from app.services.analytics.metrics.risk import annualized_volatility, volatility

    vol = volatility(returns, config).value or 0.0
    ann_vol = annualized_volatility(returns, config).value or 0.0
    ret_metrics = calculate_return_metrics(returns, config).value or {}

    val = {
        "volatility": vol,
        "annualized_volatility": ann_vol,
        "return_metrics": ret_metrics,
    }
    logger.debug("compute_equity_metrics: finished calculation.")
    return MetricResult(value=val)
