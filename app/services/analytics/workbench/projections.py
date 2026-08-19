"""Owner-produced finite workbench projections (FEAT-ANLT-11).

Every calculation stays inside Analytics. The projection reads only a
validated ``PerformanceReport`` and a canonical Simulation result mapping;
it never recalculates metrics, never substitutes zero for missing evidence,
and never persists anything. Series sections are projected from owner
evidence (report presentation series, owner distribution metrics, and the
canonical closed-trade ledger); when that evidence is absent the section
is returned as unavailable with the exact owner reason.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import to_report_json_safe
from app.services.analytics.contracts.models import PerformanceReport
from app.services.analytics.workbench import presentations
from app.services.analytics.workbench.contracts import (
    AnalyticsWorkbenchPayload,
    AnalyticsWorkbenchSection,
)
from app.utils import get_logger

logger = get_logger(__name__)

#: Maximum retained items per workbench section.
WORKBENCH_MAX_POINTS = 5_000

_UNAVAILABLE = "authoritative_evidence_unavailable"

#: Report section keys projected as dedicated metric sections.
_METRIC_SECTION_SOURCES: Mapping[str, str] = {
    "distribution": "distribution",
    "benchmark": "benchmark",
    "cost_efficiency": "costs",
}

#: Consistent units for series sections whose rows share one unit.
_SERIES_UNITS: Mapping[str, str] = {
    "drawdown_curve": "ratio",
    "returns_series": "ratio",
    "vami": "index",
    "monthly_returns": "ratio",
    "histogram": "count",
    "duration": "seconds",
}


def _unavailable(key: str) -> AnalyticsWorkbenchSection:
    """Build one unavailable section with the exact owner reason.

    Args:
        key: Stable workbench section identifier.

    Returns:
        Unavailable section carrying no items and no substituted values.
    """
    return AnalyticsWorkbenchSection(
        key=key,
        status="unavailable",
        unit=None,
        source_context="all",
        sample_count=0,
        reason=_UNAVAILABLE,
        truncated=False,
        total_count=0,
        items=(),
    )


def _metric_row(section: object, metric: object) -> dict[str, object]:
    """Project one owner metric as a JSON-safe row.

    Args:
        section: Owning report section.
        metric: Owner metric evidence.

    Returns:
        Row preserving the owner's key, status, value, unit, and context.
    """
    typed_section = cast("Any", section)
    typed_metric = cast("Any", metric)
    return {
        "section_key": typed_section.section_key,
        "metric_key": typed_metric.metric_key,
        "status": typed_metric.status,
        "value": to_report_json_safe(typed_metric.value),
        "unit": typed_metric.unit,
        "source_context": typed_metric.source_context,
    }


def _completed(
    key: str,
    rows: Sequence[Mapping[str, object]],
    *,
    unit: str | None,
    source_context: str,
    max_points: int,
) -> AnalyticsWorkbenchSection:
    """Build one completed section bounded to the workbench item cap.

    Args:
        key: Stable workbench section identifier.
        rows: JSON-safe projection rows in owner order.
        unit: Section unit when every row shares one.
        source_context: Owner source context for the section.
        max_points: Maximum retained items.

    Returns:
        Completed section with explicit truncation evidence.
    """
    total = len(rows)
    retained = tuple(rows[:max_points])
    return AnalyticsWorkbenchSection(
        key=key,
        status="completed",
        unit=unit,
        source_context=source_context,
        sample_count=len(retained),
        reason=None,
        truncated=len(retained) < total,
        total_count=total,
        items=retained,
    )


def _equity_points(report: PerformanceReport) -> list[Mapping[str, object]]:
    """Read the report-owned presentation equity series.

    Args:
        report: Validated source report.

    Returns:
        Existing presentation points without recomputation.

    Raises:
        AnalyticsValidationError: If presentation evidence is absent or invalid.
    """
    presentation = report.precision_metadata.get("presentation_series")
    if not isinstance(presentation, Mapping):
        raise AnalyticsValidationError("report presentation series is missing")
    points = presentation.get("equity_curve")
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes, bytearray)):
        raise AnalyticsValidationError("report equity presentation is invalid")
    return [dict(point) for point in cast("Sequence[Mapping[str, object]]", points)]


def _section_units(rows: Sequence[Mapping[str, object]]) -> str | None:
    """Return one consistent unit across projected rows.

    Args:
        rows: Projected metric rows.

    Returns:
        The shared unit, or ``None`` when rows disagree or carry none.
    """
    units = {str(row["unit"]) for row in rows}
    return units.pop() if len(units) == 1 else None


def _evidence_row(value: object) -> dict[str, object]:
    """Project one warning or quality flag as a JSON-safe row.

    Args:
        value: Owner warning or quality-flag evidence.

    Returns:
        Row preserving the owner's declared fields.
    """
    typed = cast("Any", value)
    return cast(
        "dict[str, object]",
        to_report_json_safe(
            {
                "code": typed.code,
                "severity": typed.severity,
                "source_context": typed.source_context,
                **(
                    {"detail": typed.detail}
                    if hasattr(typed, "detail")
                    else {"affected_sections": typed.affected_sections}
                ),
            }
        ),
    )


def _truncation_row(section: AnalyticsWorkbenchSection) -> Mapping[str, object] | None:
    """Build truncation evidence for one truncated section.

    Args:
        section: Completed section.

    Returns:
        Truncation row, or ``None`` when nothing was truncated.
    """
    if not section.truncated:
        return None
    return {
        "key": section.key,
        "sample_count": section.sample_count,
        "total_count": section.total_count,
        "policy": "first_n_owner_ordered_items",
    }


def _build_series_sections(
    report: PerformanceReport,
    simulation_result: Mapping[str, object],
    *,
    max_points: int,
) -> dict[str, AnalyticsWorkbenchSection]:
    """Build every owner-evidence series section.

    Args:
        report: Canonical validated Analytics performance report.
        simulation_result: Canonical Simulation result mapping.
        max_points: Maximum retained items per section.

    Returns:
        Section per series key, completed when owner evidence exists and
        explicitly unavailable otherwise.
    """
    series_builders: Mapping[str, Callable[[], tuple[dict[str, object], ...]]] = {
        "drawdown_curve": lambda: presentations.build_drawdown_curve(report),
        "returns_series": lambda: presentations.build_returns_series(report),
        "vami": lambda: presentations.build_vami_series(report),
        "monthly_returns": lambda: presentations.build_monthly_returns(report),
        "period_tables": lambda: presentations.build_period_tables(simulation_result),
        "trade_calendar": lambda: presentations.build_trade_calendar(simulation_result),
        "streaks": lambda: presentations.build_streaks(simulation_result),
        "histogram": lambda: presentations.build_histogram(report),
        "outliers": lambda: presentations.build_outliers(simulation_result, report),
        "excursions": lambda: presentations.build_excursions(simulation_result),
        "duration": lambda: presentations.build_duration(simulation_result),
    }
    sections: dict[str, AnalyticsWorkbenchSection] = {}
    for key, builder in series_builders.items():
        rows = builder()
        if rows:
            sections[key] = _completed(
                key,
                rows,
                unit=_SERIES_UNITS.get(key),
                source_context="all",
                max_points=max_points,
            )
        else:
            sections[key] = _unavailable(key)
    return sections


def build_workbench_payload(
    report: PerformanceReport,
    simulation_result: Mapping[str, object],
    *,
    max_points: int = WORKBENCH_MAX_POINTS,
) -> AnalyticsWorkbenchPayload:
    """Project one validated report into a finite workbench payload.

    Args:
        report: Canonical validated Analytics performance report.
        simulation_result: Canonical Simulation result mapping.
        max_points: Maximum retained items per section.

    Returns:
        Finite, versioned, non-binding workbench payload.

    Raises:
        AnalyticsValidationError: If inputs are not canonical owner evidence.
    """
    if not isinstance(report, PerformanceReport):
        raise AnalyticsValidationError("workbench source must be PerformanceReport")
    if (
        not isinstance(simulation_result, Mapping)
        or simulation_result.get("schema_id") != "simulation.result.v1"
    ):
        raise AnalyticsValidationError(
            "workbench simulation evidence must be a canonical Simulation result"
        )
    if max_points <= 0:
        raise AnalyticsValidationError("workbench max_points must be positive")

    sections = {section.section_key: section for section in report.sections}

    summary_rows: list[Mapping[str, object]] = []
    grouped_rows: list[Mapping[str, object]] = []
    metric_rows: dict[str, list[Mapping[str, object]]] = {
        key: [] for key in _METRIC_SECTION_SOURCES.values()
    }
    for section in report.sections:
        for metric in section.metrics:
            row = _metric_row(section, metric)
            summary_rows.append(row)
            source = _METRIC_SECTION_SOURCES.get(section.section_key)
            if source is not None:
                metric_rows[source].append(row)
        grouped_rows.append(
            {
                "section_key": section.section_key,
                "status": section.status,
                "reason": section.reason,
                "metric_count": len(section.metrics),
            }
        )

    built: dict[str, AnalyticsWorkbenchSection] = {
        "summary": _completed(
            "summary",
            summary_rows,
            unit=None,
            source_context="all",
            max_points=max_points,
        ),
        "equity_curve": _completed(
            "equity_curve",
            _equity_points(report),
            unit=report.account_currency,
            source_context="all",
            max_points=max_points,
        ),
        "grouped_performance": _completed(
            "grouped_performance",
            grouped_rows,
            unit=None,
            source_context="all",
            max_points=max_points,
        ),
    }
    built.update(
        _build_series_sections(report, simulation_result, max_points=max_points)
    )
    for source, key in _METRIC_SECTION_SOURCES.items():
        rows = metric_rows[key]
        if source in sections and rows:
            built[key] = _completed(
                key,
                rows,
                unit=_section_units(rows),
                source_context="all",
                max_points=max_points,
            )
        else:
            built[key] = _unavailable(key)

    truncation = tuple(
        row
        for row in (
            _truncation_row(built[key])
            for key in (
                "summary",
                "equity_curve",
                "drawdown_curve",
                "returns_series",
                "vami",
                "monthly_returns",
                "period_tables",
                "trade_calendar",
                "streaks",
                "distribution",
                "histogram",
                "outliers",
                "excursions",
                "duration",
                "grouped_performance",
                "benchmark",
                "costs",
            )
        )
        if row is not None
    )
    lineage = cast(
        "Mapping[str, object]",
        to_report_json_safe(
            {
                "source_contract": report.lineage.source_contract,
                "source_version": report.lineage.source_version,
                "source_schema_id": report.lineage.source_schema_id,
                "source_ids": report.lineage.source_ids,
                "account_currency": report.lineage.account_currency,
                "transformations": report.lineage.transformations,
                "simulation_run_id": simulation_result.get("run_id"),
            }
        ),
    )
    payload = AnalyticsWorkbenchPayload(
        contract_version="v1",
        schema_id="analytics.workbench_payload.v1",
        payload_id=f"workbench-{report.report_id}",
        report_id=report.report_id,
        generated_at=report.created_at,
        summary=built["summary"],
        equity_curve=built["equity_curve"],
        drawdown_curve=built["drawdown_curve"],
        returns_series=built["returns_series"],
        vami=built["vami"],
        monthly_returns=built["monthly_returns"],
        period_tables=built["period_tables"],
        trade_calendar=built["trade_calendar"],
        streaks=built["streaks"],
        distribution=built["distribution"],
        histogram=built["histogram"],
        outliers=built["outliers"],
        excursions=built["excursions"],
        duration=built["duration"],
        grouped_performance=built["grouped_performance"],
        benchmark=built["benchmark"],
        costs=built["costs"],
        warnings=tuple(_evidence_row(value) for value in report.caveats),
        quality_flags=tuple(_evidence_row(value) for value in report.quality_flags),
        lineage=lineage,
        truncation=truncation,
    )
    logger.info(
        "Built Analytics workbench payload for report %s: %d completed sections, "
        "%d unavailable sections",
        report.report_id,
        sum(1 for section in built.values() if section.status == "completed"),
        sum(1 for section in built.values() if section.status == "unavailable"),
    )
    return payload


__all__ = ("WORKBENCH_MAX_POINTS", "build_workbench_payload")
