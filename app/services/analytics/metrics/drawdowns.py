"""Closed-trade drawdown depth, duration, recovery, ulcer, and pain evidence."""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal

from app.services.analytics.contracts.errors import AnalyticsValidationError
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
    """Build calculated drawdown metric evidence.

    Args:
        metric_key: Catalog metric key.
        value: Finite calculated value.
        unit: Catalog unit.

    Returns:
        Calculated metric evidence.
    """
    logger.debug("Building Analytics drawdown metric evidence")
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated",
        value=value,
        unit=unit,
    )


def calculate_drawdown_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
) -> SectionEvidence:
    """Calculate core drawdown evidence from the closed-trade equity curve.

    Args:
        result: Canonical Analytics input.
        config: Required Analytics bounds supplying the warning detail bound.

    Returns:
        Ordered drawdown section evidence.

    Raises:
        AnalyticsValidationError: If an equity-curve point has invalid types.
    """
    logger.info("Calculating Analytics closed-trade drawdown evidence")
    peak = result.initial_balance
    peak_at = result.window_start
    drawdowns: list[float] = []
    max_drawdown = 0.0
    trough_at = result.window_start
    max_peak_at = result.window_start
    recovery_at: datetime | None = None
    target_peak = result.initial_balance
    for point in result.equity_curve:
        equity = point["equity"]
        timestamp = point["timestamp"]
        if not isinstance(equity, Decimal) or not isinstance(timestamp, datetime):
            raise AnalyticsValidationError("equity curve point has invalid types")
        if equity > peak:
            peak = equity
            peak_at = timestamp
        drawdown = float((peak - equity) / peak)
        drawdowns.append(drawdown)
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            trough_at = timestamp
            max_peak_at = peak_at
            target_peak = peak
            recovery_at = None
        elif max_drawdown > 0 and timestamp > trough_at and equity >= target_peak:
            recovery_at = timestamp
    duration = (trough_at - max_peak_at).total_seconds()
    warnings: tuple[AnalyticsWarning, ...] = ()
    if max_drawdown > 0 and recovery_at is None:
        warnings = (
            build_warning(
                "drawdown_unrecovered",
                section="drawdown",
                source_context="all",
                detail={"trough_at": trough_at, "window_end": result.window_end},
                max_detail_bytes=config.max_warning_detail_bytes,
            ),
        )
    recovery = (
        (recovery_at - trough_at).total_seconds() if recovery_at is not None else None
    )
    ulcer = math.sqrt(sum(value**2 for value in drawdowns) / len(drawdowns))
    pain = sum(drawdowns) / len(drawdowns)
    recovery_metric = MetricEvidence(
        metric_key="drawdown_recovery",
        status="calculated" if recovery is not None else "undefined",
        value=recovery,
        unit="duration",
        warnings=warnings,
    )
    return SectionEvidence(
        section_key="drawdown",
        criticality="required",
        metrics=(
            _metric("max_drawdown", max_drawdown, "ratio"),
            _metric("max_drawdown_duration", duration, "duration"),
            recovery_metric,
            _metric("ulcer_index", ulcer, "ratio"),
            _metric("pain_index", pain, "ratio"),
        ),
        status="degraded" if warnings else "completed",
        warnings=warnings,
    )


__all__ = ["calculate_drawdown_evidence"]
