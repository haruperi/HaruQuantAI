"""Report formatters and serializers for Analytics.

All calculations are stateless pure functions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.reports.sections import (
    AnalyticsReport,
    build_analytics_report,
)


class ReportFormat(StrEnum):
    """Supported export formats for Analytics reports."""

    JSON = "json"
    MARKDOWN = "markdown"


@dataclass(frozen=True, slots=True)
class SerializedReport:
    """Container for serialized report content.

    Args:
        content: Serialized string content.
        format: Export format representation.
    """

    content: str
    format: ReportFormat


def format_summary_as_rows(
    report: object,  # noqa: ARG001
    config: MetricConfig | None = None,
) -> list[dict[str, Any]] | MetricResult[object]:
    """Format raw summary data into display rows."""
    if config is not None:
        return MetricResult(value=[])
    return []


def build_backtest_report(
    trading_result: dict[str, Any],
    config: MetricConfig | None = None,
) -> dict[str, Any] | MetricResult[object]:
    """Build a structured backtest report dict payload."""
    if config is not None:
        return MetricResult(value={})
    resp = build_analytics_report(trading_result)
    return (
        cast("dict[str, Any]", resp["data"])
        if resp["status"] == "success" and isinstance(resp["data"], dict)
        else {}
    )


def print_statistical_validation_report(
    returns: object,  # noqa: ARG001
    config: MetricConfig | None = None,
) -> str | MetricResult[object]:
    """Package a statistical validation report as text."""
    if config is not None:
        return MetricResult(value="")
    return ""


def serialize_report(
    report: AnalyticsReport | dict[str, Any],
    report_format: ReportFormat,
) -> SerializedReport:
    """Serialize report object or dict representation deterministically."""
    # Convert report to dict safely
    rep_dict: dict[str, Any] = {}
    if isinstance(report, dict):
        rep_dict = report
    elif hasattr(report, "sections"):
        rep_dict = {
            "report_id": getattr(report, "report_id", ""),
            "report_status": getattr(report, "report_status", ""),
            "sections": getattr(report, "sections", {}),
            "warnings": getattr(report, "warnings", []),
            "quality_flags": getattr(report, "quality_flags", []),
            "metadata": getattr(report, "metadata", {}),
        }

    if report_format == ReportFormat.MARKDOWN:
        lines = [
            f"# Performance Report: {rep_dict.get('report_id', 'N/A')}",
            f"Status: {rep_dict.get('report_status', 'N/A')}",
            "---",
            "## Summary Sections:",
        ]
        for name, sec in rep_dict.get("sections", {}).items():
            lines.append(f"- **{name}**: {sec.get('status', 'N/A')}")
        return SerializedReport(content="\n".join(lines), format=report_format)

    # JSON output
    content = json.dumps(rep_dict, sort_keys=True)
    return SerializedReport(content=content, format=report_format)
