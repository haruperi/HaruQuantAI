"""Versioned finite dashboard projection from canonical Analytics reports."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import to_report_json_safe
from app.services.analytics.contracts.models import DashboardPayload, PerformanceReport
from app.services.analytics.dashboards.truncation import (
    DASHBOARD_MAX_POINTS,
    truncate_series,
)
from app.utils import get_logger

logger = get_logger(__name__)

DASHBOARD_REQUIRED_PAYLOADS = ("equity_curve", "summary_table")
DASHBOARD_OPTIONAL_PAYLOADS = ("drawdown_chart", "monthly_returns_table")


def _metric_rows(report: PerformanceReport) -> tuple[Mapping[str, object], ...]:
    """Project report metrics without recalculation.

    Args:
        report: Validated source report.

    Returns:
        Ordered JSON-safe section rows with exact metric values.
    """
    logger.debug("Projecting Analytics dashboard summary rows")
    rows: list[Mapping[str, object]] = []
    for section in report.sections:
        metrics = tuple(
            {
                "metric_key": metric.metric_key,
                "status": metric.status,
                "value": to_report_json_safe(metric.value),
                "unit": metric.unit,
                "source_context": metric.source_context,
            }
            for metric in section.metrics
        )
        rows.append(
            {
                "section_key": section.section_key,
                "status": section.status,
                "reason": section.reason,
                "metrics": metrics,
            }
        )
    return tuple(rows)


def _units(report: PerformanceReport) -> Mapping[str, str]:
    """Collect one consistent unit for every projected metric key.

    Args:
        report: Validated source report.

    Returns:
        Deterministically ordered metric-unit mapping.

    Raises:
        AnalyticsValidationError: If one metric key has conflicting units.
    """
    logger.debug("Collecting Analytics dashboard metric units")
    units: dict[str, str] = {}
    for section in report.sections:
        for metric in section.metrics:
            previous = units.setdefault(metric.metric_key, metric.unit)
            if previous != metric.unit:
                raise AnalyticsValidationError("dashboard metric units conflict")
    return dict(sorted(units.items()))


def _equity_points(report: PerformanceReport) -> Sequence[Mapping[str, object]]:
    """Read the report-owned presentation equity series.

    Args:
        report: Validated source report.

    Returns:
        Existing report equity points without recomputation.

    Raises:
        AnalyticsValidationError: If required presentation evidence is absent.
    """
    logger.debug("Reading Analytics report presentation equity series")
    presentation = report.precision_metadata.get("presentation_series")
    if not isinstance(presentation, Mapping):
        raise AnalyticsValidationError("report presentation series is missing")
    points = presentation.get("equity_curve")
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes, bytearray)):
        raise AnalyticsValidationError("report equity presentation is invalid")
    return points


def _presentation_points(
    report: PerformanceReport, key: str
) -> Sequence[Mapping[str, object]] | None:
    """Read one optional report-owned presentation series.

    Args:
        report: Validated source report.
        key: Presentation series key.

    Returns:
        Presentation rows, or None when the report carries no such series.
    """
    presentation = report.precision_metadata.get("presentation_series")
    if not isinstance(presentation, Mapping):
        return None
    points = presentation.get(key)
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes, bytearray)):
        return None
    return points or None


def _evidence_sections(report: PerformanceReport) -> tuple[Mapping[str, object], ...]:
    """Project warning and quality-flag evidence as visible payload classes.

    Args:
        report: Validated source report.

    Returns:
        Warning and quality-flag payload sections.
    """
    logger.debug("Projecting Analytics dashboard warning evidence")
    return (
        {
            "payload_class": "warnings",
            "status": "completed",
            "items": to_report_json_safe(report.caveats),
        },
        {
            "payload_class": "quality_flags",
            "status": "completed",
            "items": to_report_json_safe(report.quality_flags),
        },
    )


def build_dashboard_payload(report: PerformanceReport) -> DashboardPayload:
    """Project approved report evidence into a bounded DashboardPayload v1.

    Args:
        report: Canonical validated Analytics report.

    Returns:
        Finite, versioned, non-binding dashboard payload.

    Raises:
        AnalyticsValidationError: If required report or projection evidence fails.
    """
    logger.info("Building bounded Analytics dashboard payload")
    if not isinstance(report, PerformanceReport):
        raise AnalyticsValidationError("dashboard source must be PerformanceReport")
    equity_points, truncation = truncate_series(
        _equity_points(report),
        max_points=DASHBOARD_MAX_POINTS,
    )
    drawdown_series = _presentation_points(report, "drawdown_curve")
    if drawdown_series is not None:
        drawdown_points, drawdown_truncation = truncate_series(
            drawdown_series,
            max_points=DASHBOARD_MAX_POINTS,
        )
        drawdown_section: Mapping[str, object] = {
            "payload_class": "drawdown_chart",
            "status": "completed",
            "points": drawdown_points,
        }
        drawdown_truncation_row: Mapping[str, object] | None = {
            "payload_class": "drawdown_chart",
            **drawdown_truncation,
        }
    else:
        drawdown_section = {
            "payload_class": "drawdown_chart",
            "status": "skipped",
            "reason": "report_has_no_presentation_drawdown_series",
        }
        drawdown_truncation_row = None
    monthly_rows = _presentation_points(report, "monthly_returns")
    if monthly_rows is not None:
        monthly_total = len(monthly_rows)
        monthly_retained = monthly_rows[:DASHBOARD_MAX_POINTS]
        monthly_section: Mapping[str, object] = {
            "payload_class": "monthly_returns_table",
            "status": "completed",
            "rows": monthly_retained,
        }
        monthly_truncation_row: Mapping[str, object] | None = (
            {
                "payload_class": "monthly_returns_table",
                "sample_count": len(monthly_retained),
                "total_count": monthly_total,
                "policy": "first_n_owner_ordered_items",
            }
            if len(monthly_retained) < monthly_total
            else None
        )
    else:
        monthly_section = {
            "payload_class": "monthly_returns_table",
            "status": "skipped",
            "reason": "report_has_no_presentation_monthly_returns",
        }
        monthly_truncation_row = None
    sections: tuple[Mapping[str, object], ...] = (
        {
            "payload_class": "summary_table",
            "status": "completed",
            "rows": _metric_rows(report),
        },
        {
            "payload_class": "equity_curve",
            "status": "completed",
            "points": equity_points,
        },
        drawdown_section,
        monthly_section,
        *_evidence_sections(report),
    )
    projected_classes = {
        section["payload_class"]
        for section in sections
        if section["status"] == "completed"
    }
    if not set(DASHBOARD_REQUIRED_PAYLOADS) <= projected_classes:
        raise AnalyticsValidationError("required dashboard payload class is missing")
    payload = DashboardPayload(
        contract_version="v1",
        schema_id="analytics.dashboard_payload.v1",
        payload_id=f"dashboard-{report.report_id}",
        report_id=report.report_id,
        generated_at=report.created_at,
        sections=sections,
        warnings=report.caveats,
        quality_flags=report.quality_flags,
        units=_units(report),
        truncation_metadata=tuple(
            row
            for row in (
                {"payload_class": "equity_curve", **truncation},
                drawdown_truncation_row,
                monthly_truncation_row,
            )
            if row is not None
        ),
    )
    logger.info("Completed bounded Analytics dashboard payload")
    return payload


__all__ = [
    "DASHBOARD_OPTIONAL_PAYLOADS",
    "DASHBOARD_REQUIRED_PAYLOADS",
    "build_dashboard_payload",
]
