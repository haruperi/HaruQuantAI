# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Group-level composition and aggregation of metrics (ANL-NFR-100)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult

type TradeRecord = dict[str, Any]
type ReturnPoint = Any


def breakeven_epsilon(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[float]:
    """Return the configured breakeven epsilon value (ANL-NFR-102)."""
    eps = float(config.breakeven_epsilon if config else 1e-9)
    return MetricResult(value=eps)


def calculate_trade_metrics(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[dict[str, Any]]:
    """Calculate aggregate core trade metrics from normalized trade records (ANL-NFR-160)."""
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
    streaks = consecutive_wins_losses(trades, config).value or {"wins": 0, "losses": 0}
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
    return MetricResult(value=val)


def calculate_analytics_for_subset(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[dict[str, Any]]:
    """Calculate all analytics categories for a supplied trade subset (ANL-NFR-161)."""
    # For a subset we calculate trade metrics, drawdown, and cost impact
    trades = input_value if isinstance(input_value, Sequence) else ()
    trade_metrics = calculate_trade_metrics(trades, config).value or {}

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
    return MetricResult(value=val)


def compute_equity_metrics(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[dict[str, Any]]:
    """Calculate equity metrics from return inputs (ANL-NFR-189)."""
    returns = input_value if isinstance(input_value, Sequence) else ()
    from app.services.analytics.metrics.equity_returns import calculate_return_metrics
    from app.services.analytics.metrics.risk import annualized_volatility, volatility

    vol = volatility(returns, config).value or 0.0
    ann_vol = annualized_volatility(returns, config).value or 0.0
    ret_metrics = calculate_return_metrics(returns, config).value or {}

    val = {
        "volatility": vol,
        "annualized_volatility": ann_vol,
        "return_metrics": ret_metrics,
    }
    return MetricResult(value=val)
