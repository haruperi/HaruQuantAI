"""Deterministic composition of approved Analytics metric groups."""

from __future__ import annotations

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    AnalyticsWarning,
    SectionEvidence,
    TradingResult,
)
from app.services.analytics.metrics.benchmarks import calculate_benchmark_evidence
from app.services.analytics.metrics.cost_efficiency import (
    calculate_cost_efficiency_evidence,
)
from app.services.analytics.metrics.distributions import (
    calculate_distribution_evidence,
)
from app.services.analytics.metrics.drawdowns import calculate_drawdown_evidence
from app.services.analytics.metrics.ratios import calculate_ratio_evidence
from app.services.analytics.metrics.returns import calculate_return_evidence
from app.services.analytics.metrics.risk import calculate_risk_evidence
from app.services.analytics.metrics.statistics import run_statistical_validation
from app.services.analytics.metrics.trades import calculate_trade_evidence
from app.utils import logger


def _daily_returns(return_section: SectionEvidence) -> tuple[float, ...]:
    """Extract the canonical daily return series from section evidence.

    Args:
        return_section: Calculated equity-return evidence.

    Returns:
        Ordered daily simple returns.

    Raises:
        AnalyticsValidationError: If return evidence has an invalid value type.
    """
    logger.debug("Extracting Analytics daily returns from evidence")
    metric = next(
        item for item in return_section.metrics if item.metric_key == "period_returns"
    )
    if metric.status == "undefined":
        return ()
    if not isinstance(metric.value, tuple):
        raise AnalyticsValidationError("period_returns evidence must be a tuple")
    return tuple(float(item) for item in metric.value)


def _split_returns(
    return_section: SectionEvidence,
) -> tuple[SectionEvidence, SectionEvidence]:
    """Split monetary PnL and equity-return evidence into required sections.

    Args:
        return_section: Combined return-kernel evidence.

    Returns:
        PnL section followed by equity-return section.
    """
    logger.debug("Splitting Analytics PnL and equity-return sections")
    pnl_keys = {"sum_winning_pnl", "sum_losing_pnl", "net_pnl"}
    pnl = tuple(item for item in return_section.metrics if item.metric_key in pnl_keys)
    equity = tuple(
        item for item in return_section.metrics if item.metric_key not in pnl_keys
    )
    return (
        SectionEvidence(
            section_key="pnl",
            criticality="required",
            metrics=pnl,
            status="completed",
        ),
        SectionEvidence(
            section_key="equity_returns",
            criticality="required",
            metrics=equity,
            status=return_section.status,
            warnings=return_section.warnings,
        ),
    )


def _skipped_benchmark() -> SectionEvidence:
    """Build explicit optional benchmark-unavailable evidence.

    Returns:
        Skipped benchmark section.
    """
    logger.debug("Building skipped Analytics benchmark section")
    warning = AnalyticsWarning(
        code="optional_section_skipped",
        severity="informational",
        affected_section="benchmark",
        source_context="builder",
        detail={"section": "benchmark", "reason": "benchmark not supplied"},
    )
    return SectionEvidence(
        section_key="benchmark",
        criticality="optional",
        metrics=(),
        status="skipped",
        warnings=(warning,),
        reason="benchmark not supplied",
    )


def _trade_contexts(result: TradingResult) -> SectionEvidence:
    """Compose all, long, and short trade evidence in one report section.

    Args:
        result: Canonical Analytics input.

    Returns:
        Trade evidence with explicit metric source contexts.
    """
    logger.debug("Composing Analytics all, long, and short trade contexts")
    contexts = tuple(
        calculate_trade_evidence(result, source_context=context)
        for context in ("all", "long", "short")
    )
    warnings = tuple(warning for section in contexts for warning in section.warnings)
    return SectionEvidence(
        section_key="trades",
        criticality="required",
        metrics=tuple(metric for section in contexts for metric in section.metrics),
        status="degraded" if warnings else "completed",
        warnings=warnings,
    )


def calculate_grouped_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
) -> tuple[SectionEvidence, ...]:
    """Execute all approved metric groups in deterministic report order.

    Args:
        result: Canonical Analytics input.
        config: Required bounded calculation settings.

    Returns:
        Ordered required and optional section evidence.
    """
    logger.info("Calculating deterministic grouped Analytics evidence")
    return_section = calculate_return_evidence(result)
    pnl_section, equity_section = _split_returns(return_section)
    daily_returns = _daily_returns(return_section)
    net_values = tuple(float(trade.net_trade_pnl) for trade in result.trades)
    benchmark = (
        calculate_benchmark_evidence(result, config=config)
        if result.benchmark is not None
        else _skipped_benchmark()
    )
    return (
        _trade_contexts(result),
        pnl_section,
        equity_section,
        calculate_drawdown_evidence(result),
        calculate_risk_evidence(daily_returns),
        calculate_ratio_evidence(result, daily_returns, config=config),
        benchmark,
        calculate_distribution_evidence(net_values),
        calculate_cost_efficiency_evidence(result),
        run_statistical_validation(net_values, config=config),
    )


__all__ = ["calculate_grouped_evidence"]
