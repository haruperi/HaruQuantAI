"""Strict reconstruction of canonical Analytics reports from JSON text.

``deserialize_performance_report`` is the inverse of ``serialize_report``:
it rebuilds the immutable ``PerformanceReport`` owner object from the
canonical JSON artifact Simulation stores beside a run. Reconstruction is
fail-closed — every field must be present with the declared shape, and the
report dataclasses re-run their own catalog and integrity validation, so a
tampered or malformed artifact is rejected rather than partially loaded.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.models import (
    AnalyticsWarning,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    QualityFlag,
    ReproducibilityHashes,
    SectionEvidence,
)
from app.utils import get_logger

logger = get_logger(__name__)

_SCHEMA_ID = "analytics.performance_report.v1"


def _mapping(value: object, name: str) -> Mapping[str, object]:
    """Require one mapping field.

    Args:
        value: Candidate field value.
        name: Field name for the failure message.

    Returns:
        The mapping.

    Raises:
        AnalyticsValidationError: If the value is not a mapping.
    """
    if not isinstance(value, Mapping):
        message = f"report field is not a mapping: {name}"
        raise AnalyticsValidationError(message)
    return value


def _text(value: object, name: str) -> str:
    """Require one non-empty text field.

    Args:
        value: Candidate field value.
        name: Field name for the failure message.

    Returns:
        The text.

    Raises:
        AnalyticsValidationError: If the value is not non-empty text.
    """
    if not isinstance(value, str) or not value:
        message = f"report field is not text: {name}"
        raise AnalyticsValidationError(message)
    return value


def _optional_text(value: object) -> str | None:
    """Read one optional text field.

    Args:
        value: Candidate field value.

    Returns:
        The text, or None when absent.
    """
    return value if isinstance(value, str) and value else None


def _items(value: object, name: str) -> list[object]:
    """Require one JSON array field.

    Args:
        value: Candidate field value.
        name: Field name for the failure message.

    Returns:
        The array elements.

    Raises:
        AnalyticsValidationError: If the value is not an array.
    """
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        message = f"report field is not an array: {name}"
        raise AnalyticsValidationError(message)
    return list(value)


def _warnings(value: object) -> tuple[AnalyticsWarning, ...]:
    """Reconstruct warning evidence rows.

    Args:
        value: Serialized warnings array.

    Returns:
        Immutable warning tuple.

    Raises:
        AnalyticsValidationError: If a row is malformed.
    """
    rows: list[AnalyticsWarning] = []
    for item in _items(value, "warnings"):
        row = _mapping(item, "warning")
        rows.append(
            AnalyticsWarning(
                code=_text(row.get("code"), "warning.code"),
                severity=_text(row.get("severity"), "warning.severity"),
                affected_section=_text(
                    row.get("affected_section"), "warning.affected_section"
                ),
                source_context=_text(
                    row.get("source_context"), "warning.source_context"
                ),
                detail=_mapping(row.get("detail"), "warning.detail"),
            )
        )
    return tuple(rows)


def _quality_flags(value: object) -> tuple[QualityFlag, ...]:
    """Reconstruct quality-flag evidence rows.

    Args:
        value: Serialized quality flags array.

    Returns:
        Immutable quality-flag tuple.

    Raises:
        AnalyticsValidationError: If a row is malformed.
    """
    rows: list[QualityFlag] = []
    for item in _items(value, "quality_flags"):
        row = _mapping(item, "quality_flag")
        blocker = row.get("blocker")
        if not isinstance(blocker, bool):
            raise AnalyticsValidationError("quality flag blocker is not boolean")
        rows.append(
            QualityFlag(
                code=_text(row.get("code"), "quality_flag.code"),
                severity=_text(row.get("severity"), "quality_flag.severity"),
                blocker=blocker,
                affected_sections=tuple(
                    _text(item, "quality_flag.affected_section")
                    for item in _items(
                        row.get("affected_sections"), "quality_flag.affected_sections"
                    )
                ),
                source_context=_text(
                    row.get("source_context"), "quality_flag.source_context"
                ),
                detail=_mapping(row.get("detail"), "quality_flag.detail"),
            )
        )
    return tuple(rows)


def _metrics(value: object) -> tuple[MetricEvidence, ...]:
    """Reconstruct metric evidence rows.

    Args:
        value: Serialized metrics array.

    Returns:
        Immutable metric tuple.

    Raises:
        AnalyticsValidationError: If a row is malformed.
    """
    rows: list[MetricEvidence] = []
    for item in _items(value, "metrics"):
        row = _mapping(item, "metric")
        confidence = row.get("confidence")
        rows.append(
            MetricEvidence(
                metric_key=_text(row.get("metric_key"), "metric.metric_key"),
                status=cast("Any", row.get("status")),
                value=row.get("value"),
                unit=_text(row.get("unit"), "metric.unit"),
                confidence=(
                    _mapping(confidence, "metric.confidence")
                    if confidence is not None
                    else None
                ),
                warnings=_warnings(row.get("warnings", [])),
                source_context=_text(
                    row.get("source_context", "all"), "metric.source_context"
                ),
            )
        )
    return tuple(rows)


def _sections(value: object) -> tuple[SectionEvidence, ...]:
    """Reconstruct report sections in their serialized order.

    Args:
        value: Serialized sections array.

    Returns:
        Immutable section tuple.

    Raises:
        AnalyticsValidationError: If a row is malformed.
    """
    rows: list[SectionEvidence] = []
    for item in _items(value, "sections"):
        row = _mapping(item, "section")
        rows.append(
            SectionEvidence(
                section_key=_text(row.get("section_key"), "section.section_key"),
                criticality=cast("Any", row.get("criticality")),
                metrics=_metrics(row.get("metrics")),
                status=cast("Any", row.get("status")),
                warnings=_warnings(row.get("warnings", [])),
                reason=_optional_text(row.get("reason")),
            )
        )
    return tuple(rows)


def deserialize_performance_report(report_json: str) -> PerformanceReport:
    """Rebuild one canonical report from its serialized JSON artifact.

    Args:
        report_json: Canonical JSON text produced by ``serialize_report``.

    Returns:
        Fully validated immutable PerformanceReport.

    Raises:
        AnalyticsValidationError: If the text is not canonical JSON, does
            not carry the report schema identity, or fails reconstruction
            validation.
    """
    logger.info("Deserializing Analytics performance report artifact")
    try:
        document = json.loads(report_json)
    except (json.JSONDecodeError, TypeError) as error:
        raise AnalyticsValidationError("report artifact is not valid JSON") from error
    if not isinstance(document, Mapping):
        raise AnalyticsValidationError("report artifact is not an object")
    if document.get("schema_id") != _SCHEMA_ID:
        raise AnalyticsValidationError("report artifact schema identity mismatch")
    created_at = document.get("created_at")
    if not isinstance(created_at, str):
        raise AnalyticsValidationError("report created_at is not ISO-8601 text")
    try:
        parsed_created_at = datetime.fromisoformat(created_at)
    except ValueError as error:
        raise AnalyticsValidationError("report created_at is not ISO-8601") from error
    try:
        lineage = _mapping(document.get("lineage"), "lineage")
        hashes = _mapping(document.get("hashes"), "hashes")
        report = PerformanceReport(
            contract_version="v1",
            schema_id=cast("Any", _SCHEMA_ID),
            report_id=_text(document.get("report_id"), "report_id"),
            request_id=_text(document.get("request_id"), "request_id"),
            created_at=parsed_created_at,
            account_currency=_text(
                document.get("account_currency"), "account_currency"
            ),
            sections=_sections(document.get("sections")),
            caveats=_warnings(document.get("caveats", [])),
            quality_flags=_quality_flags(document.get("quality_flags", [])),
            lineage=Lineage(
                source_contract=_text(lineage.get("source_contract"), "lineage.source"),
                source_version=_text(
                    lineage.get("source_version"), "lineage.source_version"
                ),
                source_schema_id=_text(
                    lineage.get("source_schema_id"), "lineage.source_schema_id"
                ),
                source_ids=tuple(
                    _text(item, "lineage.source_ids")
                    for item in _items(lineage.get("source_ids"), "lineage.source_ids")
                ),
                configuration_sources=tuple(
                    _text(item, "lineage.configuration_sources")
                    for item in _items(
                        lineage.get("configuration_sources", []),
                        "lineage.configuration_sources",
                    )
                ),
                account_currency=_text(
                    lineage.get("account_currency"), "lineage.account_currency"
                ),
                transformations=tuple(
                    _text(item, "lineage.transformations")
                    for item in _items(
                        lineage.get("transformations", []), "lineage.transformations"
                    )
                ),
            ),
            hashes=ReproducibilityHashes(
                input_hash=_text(hashes.get("input_hash"), "hashes.input_hash"),
                configuration_hash=_text(
                    hashes.get("configuration_hash"), "hashes.configuration_hash"
                ),
                trade_ledger_hash=_text(
                    hashes.get("trade_ledger_hash"), "hashes.trade_ledger_hash"
                ),
                equity_curve_hash=_text(
                    hashes.get("equity_curve_hash"), "hashes.equity_curve_hash"
                ),
                benchmark_hash=_optional_text(hashes.get("benchmark_hash")),
                report_hash=_optional_text(hashes.get("report_hash")),
            ),
            precision_metadata=_mapping(
                document.get("precision_metadata"), "precision_metadata"
            ),
        )
    except AnalyticsValidationError:
        raise
    except Exception as error:
        # Fail fully closed: any stray reconstruction or dataclass-validation
        # failure becomes a validation error rather than an unexpected exception,
        # so the public port reports ANALYTICS_VALIDATION_FAILED.
        raise AnalyticsValidationError(
            "report artifact failed strict reconstruction"
        ) from error
    logger.info("Deserialized Analytics report %s", report.report_id)
    return report


__all__ = ("deserialize_performance_report",)
