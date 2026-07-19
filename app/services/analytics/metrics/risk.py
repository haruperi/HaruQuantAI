"""Annualized volatility and historical tail-risk evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import build_warning
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    AnalyticsWarning,
    MetricEvidence,
    SectionEvidence,
)
from app.services.analytics.metrics.trades import (
    ANNUALIZATION_POLICY,
    MIN_METRIC_SAMPLES,
)
from app.utils import logger

_VARIANCE_MIN_SAMPLES = MIN_METRIC_SAMPLES["variance"]
_TAIL_MIN_SAMPLES = MIN_METRIC_SAMPLES["tail"]


def _optional_metric(
    metric_key: str,
    value: float | None,
    warnings: tuple[AnalyticsWarning, ...],
) -> MetricEvidence:
    """Build calculated or undefined risk evidence.

    Args:
        metric_key: Catalog metric key.
        value: Optional calculated value.
        warnings: Supporting warnings.

    Returns:
        Metric evidence with explicit undefined status.
    """
    logger.debug("Building Analytics risk metric evidence")
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated" if value is not None else "undefined",
        value=value,
        unit="ratio",
        warnings=warnings if value is None else (),
    )


def calculate_risk_evidence(
    daily_returns: Sequence[float],
    *,
    config: AnalyticsRunConfig,
    confidence: float = 0.95,
) -> SectionEvidence:
    """Calculate catalog-approved volatility, VaR, and conditional VaR.

    Args:
        daily_returns: Ordered daily simple returns.
        config: Required Analytics bounds supplying the warning detail bound.
        confidence: Historical tail confidence.

    Returns:
        Ordered risk section evidence.

    Raises:
        AnalyticsValidationError: If values or confidence are invalid.
    """
    logger.info("Calculating Analytics daily risk evidence")
    if not 0.0 < confidence < 1.0:
        raise AnalyticsValidationError("confidence must be between zero and one")
    values = np.asarray(tuple(daily_returns), dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise AnalyticsValidationError("daily returns contain non-finite values")
    variance_warning = (
        build_warning(
            "insufficient_samples",
            section="risk",
            source_context="daily",
            detail={
                "observed_count": len(values),
                "required_count": _VARIANCE_MIN_SAMPLES,
            },
            max_detail_bytes=config.max_warning_detail_bytes,
        ),
    )
    tail_warning = (
        build_warning(
            "insufficient_samples",
            section="risk",
            source_context="daily",
            detail={
                "observed_count": len(values),
                "required_count": _TAIL_MIN_SAMPLES,
            },
            max_detail_bytes=config.max_warning_detail_bytes,
        ),
    )
    volatility = (
        float(np.std(values, ddof=1) * math.sqrt(ANNUALIZATION_POLICY["trading_days"]))
        if len(values) >= _VARIANCE_MIN_SAMPLES
        else None
    )
    value_at_risk: float | None = None
    conditional_var: float | None = None
    if len(values) >= _TAIL_MIN_SAMPLES:
        value_at_risk = float(np.quantile(values, 1.0 - confidence, method="linear"))
        tail = values[values <= value_at_risk]
        conditional_var = float(np.mean(tail)) if len(tail) else None
    warnings: tuple[AnalyticsWarning, ...] = (
        () if len(values) >= _TAIL_MIN_SAMPLES else tail_warning
    )
    if len(values) < _VARIANCE_MIN_SAMPLES:
        warnings = variance_warning + warnings
    return SectionEvidence(
        section_key="risk",
        criticality="optional",
        metrics=(
            _optional_metric("volatility", volatility, variance_warning),
            _optional_metric("value_at_risk", value_at_risk, tail_warning),
            _optional_metric("conditional_var", conditional_var, tail_warning),
        ),
        status="degraded" if warnings else "completed",
        warnings=warnings,
    )


__all__ = ["calculate_risk_evidence"]
