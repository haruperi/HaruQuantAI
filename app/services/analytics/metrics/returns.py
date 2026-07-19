"""Monetary PnL, equity, return, and annualized return evidence."""

from __future__ import annotations

from decimal import Decimal

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import build_warning
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    MetricEvidence,
    SectionEvidence,
    TradingResult,
)
from app.utils import logger

_PERIOD_RETURN_MIN_SAMPLES = 2
_CAGR_MIN_WINDOW_DAYS = 1


def _metric(metric_key: str, value: object, unit: str) -> MetricEvidence:
    """Build calculated return metric evidence.

    Args:
        metric_key: Catalog metric key.
        value: Finite calculated value.
        unit: Catalog unit.

    Returns:
        Calculated metric evidence.
    """
    logger.debug("Building Analytics return metric evidence")
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated",
        value=value,
        unit=unit,
    )


def _optional_metric(
    metric_key: str,
    value: object | None,
    unit: str,
    *,
    observed_count: int,
    required_count: int,
    config: AnalyticsRunConfig,
) -> MetricEvidence:
    """Build calculated or explicitly undefined return evidence.

    Args:
        metric_key: Catalog metric key.
        value: Optional finite calculated value.
        unit: Catalog unit.
        observed_count: Observations actually available.
        required_count: Cataloged minimum observations.
        config: Required Analytics bounds supplying the warning detail bound.

    Returns:
        Calculated or undefined metric evidence.
    """
    logger.debug("Building optional Analytics return metric evidence")
    if value is not None:
        return MetricEvidence(
            metric_key=metric_key,
            status="calculated",
            value=value,
            unit=unit,
        )
    warning = build_warning(
        "insufficient_samples",
        section="equity_returns",
        source_context="daily",
        detail={
            "observed_count": observed_count,
            "required_count": required_count,
        },
        max_detail_bytes=config.max_warning_detail_bytes,
    )
    return MetricEvidence(
        metric_key=metric_key,
        status="undefined",
        value=None,
        unit=unit,
        warnings=(warning,),
    )


def _daily_returns(result: TradingResult) -> tuple[float, ...]:
    """Derive simple daily returns from the closed-trade daily curve.

    Args:
        result: Canonical Analytics input.

    Returns:
        Ordered simple daily returns.

    Raises:
        AnalyticsValidationError: If daily equity is not exact Decimal evidence.
    """
    logger.debug("Deriving Analytics daily return series")
    returns: list[float] = []
    previous = result.initial_balance
    for point in result.daily_equity_curve:
        equity = point["equity"]
        if not isinstance(equity, Decimal):
            raise AnalyticsValidationError("daily equity must be Decimal")
        returns.append(float((equity - previous) / previous))
        previous = equity
    return tuple(returns)


def calculate_return_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
) -> SectionEvidence:
    """Calculate cataloged PnL, equity, returns, and CAGR evidence.

    Args:
        result: Canonical Analytics input.
        config: Required Analytics bounds supplying the warning detail bound.

    Returns:
        Ordered equity-return section evidence.
    """
    logger.info("Calculating Analytics return and PnL evidence")
    winning = sum(
        (trade.net_trade_pnl for trade in result.trades if trade.net_trade_pnl > 0),
        Decimal(0),
    )
    losing = sum(
        (trade.net_trade_pnl for trade in result.trades if trade.net_trade_pnl < 0),
        Decimal(0),
    )
    net = sum((trade.net_trade_pnl for trade in result.trades), Decimal(0))
    ending = result.initial_balance + net
    returns = _daily_returns(result)
    days = (result.window_end - result.window_start).total_seconds() / 86_400
    years = days / 365.25
    cagr = (
        float(ending / result.initial_balance) ** (1.0 / years) - 1.0
        if days >= 1.0
        else None
    )
    period_returns: tuple[float, ...] | None = (
        returns if len(returns) >= _PERIOD_RETURN_MIN_SAMPLES else None
    )
    metrics = (
        _metric("sum_winning_pnl", winning, "currency"),
        _metric("sum_losing_pnl", losing, "currency"),
        _metric("net_pnl", net, "currency"),
        _metric("starting_equity", result.initial_balance, "currency"),
        _metric("ending_equity", ending, "currency"),
        _optional_metric(
            "period_returns",
            period_returns,
            "ratio",
            observed_count=len(returns),
            required_count=_PERIOD_RETURN_MIN_SAMPLES,
            config=config,
        ),
        _optional_metric(
            "cagr",
            cagr,
            "ratio",
            observed_count=int(days),
            required_count=_CAGR_MIN_WINDOW_DAYS,
            config=config,
        ),
    )
    warnings = tuple(warning for metric in metrics for warning in metric.warnings)
    return SectionEvidence(
        section_key="equity_returns",
        criticality="required",
        metrics=metrics,
        status="degraded" if warnings else "completed",
        warnings=warnings,
    )


__all__ = ["calculate_return_evidence"]
