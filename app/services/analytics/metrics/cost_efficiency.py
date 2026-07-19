"""Ledger cost, excursion, duration, and trade-efficiency evidence."""

from __future__ import annotations

from decimal import Decimal

from app.services.analytics.contracts.evidence import build_warning
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    AnalyticsWarning,
    MetricEvidence,
    SectionEvidence,
    TradingResult,
)
from app.utils import logger


def _metric(metric_key: str, value: object, unit: str) -> MetricEvidence:
    """Build calculated cost-efficiency metric evidence.

    Args:
        metric_key: Catalog metric key.
        value: Finite calculated value.
        unit: Catalog unit.

    Returns:
        Calculated metric evidence.
    """
    logger.debug("Building Analytics cost metric evidence")
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated",
        value=value,
        unit=unit,
        source_context="cost",
    )


def _optional_metric(
    metric_key: str,
    value: object | None,
    unit: str,
    warning: AnalyticsWarning,
) -> MetricEvidence:
    """Build calculated or undefined optional cost evidence.

    Args:
        metric_key: Catalog metric key.
        value: Optional calculated value.
        unit: Catalog unit.
        warning: Missing-source warning.

    Returns:
        Cost metric evidence.
    """
    logger.debug("Building optional Analytics cost metric evidence")
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated" if value is not None else "undefined",
        value=value,
        unit=unit,
        warnings=() if value is not None else (warning,),
        source_context="cost",
    )


def calculate_cost_efficiency_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
) -> SectionEvidence:
    """Calculate cataloged cost, excursion, duration, and efficiency evidence.

    Args:
        result: Canonical Analytics input.
        config: Required Analytics bounds supplying the warning detail bound.

    Returns:
        Ordered cost-efficiency section evidence.
    """
    logger.info("Calculating Analytics cost and efficiency evidence")
    commission = sum((trade.commission for trade in result.trades), Decimal(0))
    swap = sum((trade.swap for trade in result.trades), Decimal(0))
    gross = sum((trade.profit for trade in result.trades), Decimal(0))
    mae_values = [trade.mae for trade in result.trades if trade.mae is not None]
    mfe_values = [trade.mfe for trade in result.trades if trade.mfe is not None]
    efficiencies = [
        float(trade.profit / trade.mfe)
        for trade in result.trades
        if trade.mfe is not None and trade.mfe > 0
    ]
    warning = build_warning(
        "mae_mfe_absent",
        section="cost_efficiency",
        source_context="cost",
        detail={"missing_fields": ("mae", "mfe")},
        max_detail_bytes=config.max_warning_detail_bytes,
    )
    total_mae = sum(mae_values, Decimal(0)) if mae_values else None
    total_mfe = sum(mfe_values, Decimal(0)) if mfe_values else None
    max_excursion = min(mae_values) if mae_values else None
    efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else None
    duration = sum(
        (trade.exit_time - trade.entry_time).total_seconds() for trade in result.trades
    ) / len(result.trades)
    metrics = (
        _metric("total_commission", commission, "currency"),
        _metric("total_swap", swap, "currency"),
        _metric("total_cost_drag", commission + swap, "currency"),
        _metric("gross_pnl_before_costs", gross, "currency"),
        _optional_metric("total_mae", total_mae, "currency", warning),
        _optional_metric("total_mfe", total_mfe, "currency", warning),
        _optional_metric(
            "max_intratrade_excursion", max_excursion, "currency", warning
        ),
        _metric("average_trade_duration", duration, "duration"),
        _optional_metric("trade_efficiency", efficiency, "ratio", warning),
    )
    warnings = tuple(item for metric in metrics for item in metric.warnings)
    return SectionEvidence(
        section_key="cost_efficiency",
        criticality="optional",
        metrics=metrics,
        status="degraded" if warnings else "completed",
        warnings=warnings,
    )


__all__ = ["calculate_cost_efficiency_evidence"]
