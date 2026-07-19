"""Core Sharpe, Sortino, Calmar, profit, payoff, and expectancy ratios."""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import Decimal

import numpy as np

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    AnalyticsWarning,
    MetricEvidence,
    SectionEvidence,
    TradingResult,
)
from app.services.analytics.metrics.trades import (
    ANNUALIZATION_POLICY,
    MIN_METRIC_SAMPLES,
)
from app.utils import logger

_VARIANCE_MIN_SAMPLES = MIN_METRIC_SAMPLES["variance"]


def _metric(
    metric_key: str,
    value: float | None,
    *,
    unit: str = "ratio",
) -> MetricEvidence:
    """Build calculated or undefined ratio evidence.

    Args:
        metric_key: Catalog metric key.
        value: Optional finite ratio.
        unit: Catalog unit.

    Returns:
        Ratio metric evidence.
    """
    logger.debug("Building Analytics ratio metric evidence")
    warnings: tuple[AnalyticsWarning, ...] = ()
    if value is None:
        warnings = (
            AnalyticsWarning(
                code="undefined_zero_denominator",
                severity="warning",
                affected_section="ratios",
                source_context="daily",
                detail={"metric_key": metric_key},
            ),
        )
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated" if value is not None else "undefined",
        value=value,
        unit=unit,
        warnings=warnings,
    )


def _cagr_and_drawdown(result: TradingResult) -> tuple[float, float]:
    """Calculate CAGR and maximum closed-trade drawdown.

    Args:
        result: Canonical Analytics input.

    Returns:
        CAGR and positive maximum drawdown ratio.

    Raises:
        AnalyticsValidationError: If the equity curve has invalid values.
    """
    logger.debug("Calculating Analytics Calmar inputs")
    ending = result.initial_balance + sum(
        (trade.net_trade_pnl for trade in result.trades), Decimal(0)
    )
    years = max(
        (result.window_end - result.window_start).total_seconds() / 31_557_600,
        1.0 / 365.25,
    )
    cagr = (float(ending / result.initial_balance) ** (1.0 / years)) - 1.0
    peak = result.initial_balance
    max_drawdown = 0.0
    for point in result.equity_curve:
        equity = point["equity"]
        if not isinstance(equity, Decimal):
            raise AnalyticsValidationError("equity curve must contain Decimal values")
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, float((peak - equity) / peak))
    return cagr, max_drawdown


def calculate_ratio_evidence(
    result: TradingResult,
    returns: Sequence[float],
    *,
    config: AnalyticsRunConfig,
) -> SectionEvidence:
    """Calculate catalog-approved core ratios without infinite values.

    Args:
        result: Canonical Analytics input.
        returns: Ordered daily simple returns.
        config: Required risk-free and bounded runtime settings.

    Returns:
        Ordered ratio section evidence.

    Raises:
        AnalyticsValidationError: If risk-free or numeric evidence is invalid.
    """
    logger.info("Calculating Analytics core ratio evidence")
    if config.risk_free_rate is None:
        raise AnalyticsValidationError("risk-free-rate evidence is required")
    values = np.asarray(tuple(returns), dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise AnalyticsValidationError("returns contain non-finite values")
    annualization_days = ANNUALIZATION_POLICY["trading_days"]
    daily_risk_free = float(config.risk_free_rate.rate) / annualization_days
    excess = values - daily_risk_free
    stdev = (
        float(np.std(excess, ddof=1)) if len(excess) >= _VARIANCE_MIN_SAMPLES else 0.0
    )
    sharpe = (
        float(np.mean(excess) / stdev * math.sqrt(annualization_days))
        if stdev > 0
        else None
    )
    downside = (
        math.sqrt(float(np.mean(np.minimum(values, 0.0) ** 2))) if len(values) else 0.0
    )
    sortino = (
        float(np.mean(excess) / downside * math.sqrt(annualization_days))
        if downside > 0
        else None
    )
    cagr, max_drawdown = _cagr_and_drawdown(result)
    calmar = cagr / max_drawdown if max_drawdown > 0 else None
    wins = [trade.net_trade_pnl for trade in result.trades if trade.net_trade_pnl > 0]
    losses = [trade.net_trade_pnl for trade in result.trades if trade.net_trade_pnl < 0]
    sum_wins = sum(wins, Decimal(0))
    sum_losses = sum(losses, Decimal(0))
    profit_factor = float(sum_wins / abs(sum_losses)) if sum_losses != 0 else None
    mean_win = sum_wins / len(wins) if wins else None
    mean_loss = sum_losses / len(losses) if losses else None
    payoff: float | None = None
    if mean_win is not None and mean_loss is not None and mean_loss != 0:
        payoff = float(mean_win / abs(mean_loss))
    expectancy = (
        float(
            sum(
                (trade.net_trade_pnl for trade in result.trades),
                Decimal(0),
            )
            / len(result.trades)
        )
        if result.trades
        else None
    )
    metrics = tuple(
        _metric(key, value, unit="currency" if key == "expectancy" else "ratio")
        for key, value in (
            ("sharpe_ratio", sharpe),
            ("sortino_ratio", sortino),
            ("calmar_ratio", calmar),
            ("profit_factor", profit_factor),
            ("payoff_ratio", payoff),
            ("expectancy", expectancy),
        )
    )
    warnings = tuple(warning for metric in metrics for warning in metric.warnings)
    return SectionEvidence(
        section_key="ratios",
        criticality="optional",
        metrics=metrics,
        status="degraded" if warnings else "completed",
        warnings=warnings,
    )


__all__ = ["calculate_ratio_evidence"]
