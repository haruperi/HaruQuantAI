"""Canonical JSON and minimal text serialization for Analytics reports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import to_report_json_safe
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.analytics.contracts.models import (
        AnalyticsRunConfig,
        PerformanceReport,
    )


def _human_readable(report: PerformanceReport) -> str:
    """Render the sole approved minimal human-readable representation.

    Args:
        report: Validated Analytics report.

    Returns:
        Bounded line-oriented report summary.
    """
    logger.debug("Rendering minimal human-readable Analytics report")
    lines = [
        f"PerformanceReport {report.report_id}",
        f"currency: {report.account_currency}",
        f"non_binding: {str(report.non_binding).lower()}",
    ]
    lines.extend(
        f"section {section.section_key}: {section.status}"
        for section in report.sections
    )
    return "\n".join(lines)


def serialize_report(
    report: PerformanceReport,
    *,
    format_name: str,
    config: AnalyticsRunConfig,
) -> str:
    """Serialize a report without writes and enforce the response byte bound.

    Args:
        report: Validated canonical report.
        format_name: ``json`` or ``text``.
        config: Required response-size bound.

    Returns:
        Canonical JSON or minimal human-readable text.

    Raises:
        AnalyticsValidationError: If format, evidence, or size is invalid.
    """
    logger.info("Serializing Analytics performance report")
    if format_name not in {"json", "text"}:
        message = f"unsupported Analytics report format: {format_name}"
        raise AnalyticsValidationError(message)
    try:
        if format_name == "json":
            rendered = canonical_json(to_report_json_safe(report), max_items=None)
        else:
            rendered = _human_readable(report)
    except Exception as error:
        raise AnalyticsValidationError("report serialization failed") from error
    if len(rendered.encode("utf-8")) > config.max_response_bytes:
        raise AnalyticsValidationError("serialized report exceeds configured bound")
    return rendered


__all__ = ["serialize_report"]
