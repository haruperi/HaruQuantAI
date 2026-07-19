"""Bounded seeded bootstrap, permutation, and sample diagnostics."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import build_warning
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    MetricEvidence,
    SectionEvidence,
)
from app.services.analytics.metrics.trades import MIN_METRIC_SAMPLES
from app.utils import logger

_ADEQUATE_STATISTICAL_SAMPLES = MIN_METRIC_SAMPLES["statistical"]


def _metric(metric_key: str, value: object) -> MetricEvidence:
    """Build calculated statistical metric evidence.

    Args:
        metric_key: Catalog metric key.
        value: Finite calculated evidence.

    Returns:
        Calculated metric evidence.
    """
    logger.debug("Building Analytics statistical metric evidence")
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated",
        value=value,
        unit="ratio",
        source_context="statistical",
    )


def run_statistical_validation(
    values: Sequence[float],
    *,
    config: AnalyticsRunConfig,
) -> SectionEvidence:
    """Run reproducible bounded bootstrap and permutation validation.

    Args:
        values: Finite numeric observations.
        config: Required bounds, seed, iterations, confidence, and alpha.

    Returns:
        Ordered statistical section evidence.

    Raises:
        AnalyticsValidationError: If sample or configured bounds are invalid.
    """
    logger.info("Running bounded Analytics statistical validation")
    array = np.asarray(tuple(values), dtype=np.float64)
    if len(array) > config.max_statistical_observations:
        raise AnalyticsValidationError(
            "statistical observations exceed configured bound"
        )
    if not np.all(np.isfinite(array)):
        raise AnalyticsValidationError("statistical observations must be finite")
    if config.statistics.bootstrap_iterations > config.max_bootstrap_iterations:
        raise AnalyticsValidationError("bootstrap iterations exceed configured bound")
    if config.statistics.permutation_iterations > config.max_permutation_iterations:
        raise AnalyticsValidationError("permutation iterations exceed configured bound")
    if len(array) < _ADEQUATE_STATISTICAL_SAMPLES:
        warning = build_warning(
            "statistical_evidence_skipped",
            section="statistical",
            source_context="sample",
            detail={"reason": "insufficient sample", "observed_count": len(array)},
            max_detail_bytes=config.max_warning_detail_bytes,
        )
        return SectionEvidence(
            section_key="statistical",
            criticality="optional",
            metrics=(
                _metric(
                    "sample_adequacy",
                    {
                        "observed_count": len(array),
                        "required_count": _ADEQUATE_STATISTICAL_SAMPLES,
                        "adequate": False,
                        "alpha": config.statistics.alpha,
                    },
                ),
            ),
            status="degraded",
            warnings=(warning,),
        )
    generator = np.random.default_rng(config.statistics.seed)
    bootstrap_means = np.asarray(
        [
            float(np.mean(generator.choice(array, size=len(array), replace=True)))
            for _ in range(config.statistics.bootstrap_iterations)
        ]
    )
    tail = (1.0 - config.statistics.confidence) / 2.0
    interval = tuple(
        float(item)
        for item in np.quantile(bootstrap_means, (tail, 1.0 - tail), method="linear")
    )
    observed = abs(float(np.mean(array)))
    exceedances = 0
    for _ in range(config.statistics.permutation_iterations):
        signs = generator.choice((-1.0, 1.0), size=len(array), replace=True)
        exceedances += int(abs(float(np.mean(array * signs))) >= observed)
    p_value = (exceedances + 1) / (config.statistics.permutation_iterations + 1)
    adjusted = min(p_value, 1.0)
    adequacy = {
        "observed_count": len(array),
        "required_count": _ADEQUATE_STATISTICAL_SAMPLES,
        "adequate": len(array) >= _ADEQUATE_STATISTICAL_SAMPLES,
        "alpha": config.statistics.alpha,
    }
    return SectionEvidence(
        section_key="statistical",
        criticality="optional",
        metrics=(
            _metric("bootstrap_confidence_interval", interval),
            _metric("permutation_p_value", p_value),
            _metric("multiple_comparison_adjustment", adjusted),
            _metric("sample_adequacy", adequacy),
        ),
        status="completed",
        warnings=(),
    )


__all__ = ["run_statistical_validation"]
