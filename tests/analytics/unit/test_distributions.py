"""Unit tests for Analytics distribution evidence."""

# ruff: noqa: INP001

from app.services.analytics.metrics.distributions import (
    calculate_distribution_evidence,
)
from app.utils import logger


def test_distribution_constant_sample_is_explicit() -> None:
    """Constant samples skip histograms and expose undefined moments."""
    logger.debug("Testing Analytics constant distribution sample")
    section = calculate_distribution_evidence((1.0, 1.0, 1.0, 1.0))
    metrics = {item.metric_key: item for item in section.metrics}
    assert metrics["skewness"].status == "undefined"
    assert metrics["kurtosis"].status == "undefined"
    assert metrics["histogram"].status == "skipped"
    assert metrics["outliers"].value == 0


def test_distribution_uses_complete_fixed_percentiles() -> None:
    """All nine cataloged percentile points are emitted."""
    logger.debug("Testing Analytics fixed percentile set")
    section = calculate_distribution_evidence(
        tuple(float(value) for value in range(20))
    )
    metric = next(item for item in section.metrics if item.metric_key == "percentiles")
    assert tuple(metric.value) == (
        "p01",
        "p05",
        "p10",
        "p25",
        "p50",
        "p75",
        "p90",
        "p95",
        "p99",
    )
