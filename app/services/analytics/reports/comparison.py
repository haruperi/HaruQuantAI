"""Compatible actual-metric comparison for Analytics reports."""

from __future__ import annotations

from decimal import Decimal

from app.services.analytics.contracts.catalogs import (
    METRIC_DEFINITION_CATALOG,
    validate_contract_version,
)
from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.models import (
    MetricEvidence,
    PerformanceReport,
    SectionEvidence,
)
from app.utils import logger


def _numeric_metrics(
    report: PerformanceReport,
) -> dict[tuple[str, str], MetricEvidence]:
    """Index calculated numeric metrics by key and source context.

    Args:
        report: Validated Analytics report.

    Returns:
        Numeric metric evidence index.
    """
    logger.debug("Indexing comparable Analytics report metrics")
    return {
        (metric.metric_key, metric.source_context): metric
        for section in report.sections
        for metric in section.metrics
        if metric.status == "calculated"
        and not isinstance(metric.value, bool)
        and isinstance(metric.value, (int, float, Decimal))
    }


def _delta(reference: object, candidate: object) -> int | float | Decimal:
    """Subtract one compatible numeric evidence value from another.

    Args:
        reference: Reference numeric value.
        candidate: Candidate numeric value.

    Returns:
        Candidate-minus-reference delta.

    Raises:
        AnalyticsValidationError: If numeric types cannot be compared exactly.
    """
    logger.debug("Calculating actual Analytics metric delta")
    if isinstance(reference, Decimal) and isinstance(candidate, Decimal):
        return candidate - reference
    if isinstance(reference, (int, float)) and isinstance(candidate, (int, float)):
        return candidate - reference
    raise AnalyticsValidationError("comparison metric numeric types are incompatible")


def compare_performance_reports(
    reference: PerformanceReport,
    candidate: PerformanceReport,
) -> SectionEvidence:
    """Compare compatible reports using actual common cataloged metrics.

    Args:
        reference: Baseline report.
        candidate: Candidate report.

    Returns:
        Ordered common-metric delta evidence.

    Raises:
        AnalyticsValidationError: If schemas, pairing, or metrics are incompatible.
    """
    logger.info("Comparing compatible Analytics performance reports")
    validate_contract_version(
        "analytics.performance_report", reference.contract_version
    )
    validate_contract_version(
        "analytics.performance_report", candidate.contract_version
    )
    if reference.schema_id != candidate.schema_id:
        raise AnalyticsValidationError("performance report schemas are incompatible")
    if (
        reference.account_currency != candidate.account_currency
        or reference.lineage.source_contract != candidate.lineage.source_contract
    ):
        raise AnalyticsValidationError("performance report pairing is incompatible")
    reference_metrics = _numeric_metrics(reference)
    candidate_metrics = _numeric_metrics(candidate)
    common = tuple(sorted(set(reference_metrics) & set(candidate_metrics)))
    metrics = tuple(
        MetricEvidence(
            metric_key=metric_key,
            status="calculated",
            value=_delta(
                reference_metrics[(metric_key, source_context)].value,
                candidate_metrics[(metric_key, source_context)].value,
            ),
            unit=reference_metrics[(metric_key, source_context)].unit,
            source_context=source_context,
        )
        for metric_key, source_context in common
        if metric_key in METRIC_DEFINITION_CATALOG
        and reference_metrics[(metric_key, source_context)].unit
        == candidate_metrics[(metric_key, source_context)].unit
    )
    if not metrics:
        raise AnalyticsValidationError("reports have no common numeric metrics")
    caveats = tuple(
        warning for report in (reference, candidate) for warning in report.caveats
    )
    return SectionEvidence(
        section_key="comparison",
        criticality="optional",
        metrics=metrics,
        status="degraded" if caveats else "completed",
        warnings=caveats,
    )


__all__ = ["compare_performance_reports"]
