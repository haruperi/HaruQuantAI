"""Currency-safe aggregation of compatible Analytics component reports."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    PortfolioPerformanceReport,
    SectionEvidence,
)
from app.services.analytics.reports.hashes import _compute_portfolio_hashes
from app.utils import logger

_FX_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "source_currency",
        "target_currency",
        "legs",
        "composite_rate",
        "as_of",
        "expires_at",
        "path_policy_id",
        "path_policy_version",
        "provenance",
        "request_id",
    }
)


def _measurement_window(report: PerformanceReport) -> tuple[datetime, datetime]:
    """Read the builder-owned UTC measurement window from precision metadata.

    Args:
        report: Component report.

    Returns:
        Measurement start and end.

    Raises:
        AnalyticsValidationError: If exact UTC window evidence is absent.
    """
    logger.debug("Reading Analytics component measurement window")
    start = report.precision_metadata.get("measurement_start")
    end = report.precision_metadata.get("measurement_end")
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        raise AnalyticsValidationError("component measurement window is missing")
    if (
        start.tzinfo is None
        or end.tzinfo is None
        or start.utcoffset() != timedelta(0)
        or end.utcoffset() != timedelta(0)
        or end < start
    ):
        raise AnalyticsValidationError("component measurement window is invalid")
    return start, end


def _fx_rate(
    source_currency: str,
    base_currency: str,
    fx_evidence: Mapping[str, object] | None,
    *,
    evidence_time: datetime,
) -> Decimal:
    """Validate and return a caller-supplied exact Data-owned FX rate.

    Args:
        source_currency: Component report currency.
        base_currency: Requested aggregate currency.
        fx_evidence: Optional Data-owned conversion mapping.
        evidence_time: Time at which the report requires fresh evidence.

    Returns:
        Identity or supplied exact conversion rate.

    Raises:
        AnalyticsValidationError: If conversion evidence is missing or invalid.
    """
    logger.debug("Validating Analytics portfolio FX evidence")
    if source_currency == base_currency:
        return Decimal(1)
    if fx_evidence is None or set(fx_evidence) != _FX_FIELDS:
        raise AnalyticsValidationError("required FX conversion evidence is missing")
    if (
        fx_evidence["contract_version"] != "v1"
        or fx_evidence["schema_id"] != "data.fx_conversion_evidence.v1"
        or fx_evidence["source_currency"] != source_currency
        or fx_evidence["target_currency"] != base_currency
    ):
        raise AnalyticsValidationError("FX conversion evidence is incompatible")
    rate = fx_evidence["composite_rate"]
    as_of = fx_evidence["as_of"]
    expires_at = fx_evidence["expires_at"]
    if (
        not isinstance(rate, Decimal)
        or not rate.is_finite()
        or rate <= 0
        or not isinstance(as_of, datetime)
        or not isinstance(expires_at, datetime)
        or as_of.tzinfo is None
        or expires_at.tzinfo is None
        or as_of.utcoffset() != timedelta(0)
        or expires_at.utcoffset() != timedelta(0)
        or not as_of <= evidence_time <= expires_at
    ):
        raise AnalyticsValidationError("FX conversion evidence is stale or invalid")
    return rate


def _currency_metrics(report: PerformanceReport) -> tuple[MetricEvidence, ...]:
    """Select calculated component currency evidence.

    Args:
        report: Component report.

    Returns:
        Calculated currency metrics.
    """
    logger.debug("Selecting Analytics component currency metrics")
    return tuple(
        metric
        for section in report.sections
        for metric in section.metrics
        if metric.status == "calculated"
        and metric.unit == "currency"
        and isinstance(metric.value, Decimal)
    )


def build_portfolio_performance_report(
    reports: Sequence[PerformanceReport],
    *,
    base_currency: str,
    fx_evidence: Mapping[str, object] | None,
    config: AnalyticsRunConfig,
) -> PortfolioPerformanceReport:
    """Aggregate compatible actual component monetary evidence after FX validation.

    Args:
        reports: Ordered component reports.
        base_currency: Required aggregate currency.
        fx_evidence: Caller-supplied Data-owned conversion evidence.
        config: Required component bound.

    Returns:
        Internal non-binding portfolio performance report.

    Raises:
        AnalyticsValidationError: If component, window, currency, FX, or bounds fail.
    """
    logger.info("Building currency-safe Analytics portfolio report")
    components = tuple(reports)
    if not components or len(components) > config.max_portfolio_components:
        raise AnalyticsValidationError("portfolio component count is invalid")
    if not base_currency or base_currency != base_currency.strip():
        raise AnalyticsValidationError("portfolio base currency is required")
    if any(
        report.contract_version != "v1"
        or report.schema_id != "analytics.performance_report.v1"
        for report in components
    ):
        raise AnalyticsValidationError("portfolio component schema is incompatible")
    windows = tuple(_measurement_window(report) for report in components)
    if len(set(windows)) != 1:
        raise AnalyticsValidationError("portfolio component windows do not match")
    measurement_start, measurement_end = windows[0]
    totals: dict[tuple[str, str], Decimal] = {}
    for report in components:
        rate = _fx_rate(
            report.account_currency,
            base_currency,
            fx_evidence,
            evidence_time=report.created_at,
        )
        for metric in _currency_metrics(report):
            key = (metric.metric_key, metric.source_context)
            value = metric.value
            if not isinstance(value, Decimal):
                raise AnalyticsValidationError("currency metric must be Decimal")
            totals[key] = totals.get(key, Decimal(0)) + value * rate
    if not totals:
        raise AnalyticsValidationError("portfolio has no aggregable currency evidence")
    metrics = tuple(
        MetricEvidence(
            metric_key=metric_key,
            status="calculated",
            value=value,
            unit="currency",
            source_context=source_context,
        )
        for (metric_key, source_context), value in sorted(totals.items())
    )
    section = SectionEvidence(
        section_key="pnl",
        criticality="required",
        metrics=metrics,
        status="completed",
    )
    component_ids = tuple(report.report_id for report in components)
    payload: Mapping[str, object] = {
        "component_report_ids": component_ids,
        "measurement_start": measurement_start,
        "measurement_end": measurement_end,
        "base_currency": base_currency,
        "sections": (section,),
        "fx": fx_evidence,
    }
    fx_source_id = (
        str(fx_evidence["request_id"])
        if fx_evidence is not None and "request_id" in fx_evidence
        else "identity-currency"
    )
    return PortfolioPerformanceReport(
        schema_id="analytics.portfolio_performance_report.v1",
        report_id=_compute_portfolio_hashes(payload).input_hash,
        component_report_ids=component_ids,
        measurement_start=measurement_start,
        measurement_end=measurement_end,
        base_currency=base_currency,
        sections=(section,),
        caveats=tuple(warning for report in components for warning in report.caveats),
        quality_flags=tuple(
            flag for report in components for flag in report.quality_flags
        ),
        fx_lineage=Lineage(
            source_contract=(
                "data.fx_conversion_evidence"
                if fx_evidence is not None
                else "identity_currency"
            ),
            source_version="v1",
            source_schema_id=(
                str(fx_evidence["schema_id"])
                if fx_evidence is not None and "schema_id" in fx_evidence
                else "analytics.identity_currency.v1"
            ),
            source_ids=(fx_source_id,),
            configuration_sources=("caller",),
            account_currency=base_currency,
            transformations=("apply_exact_fx_rate",),
        ),
        hashes=_compute_portfolio_hashes(payload),
    )


__all__ = ["build_portfolio_performance_report"]
