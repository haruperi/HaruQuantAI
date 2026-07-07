"""Warning and quality-flag catalogs, redaction policies, and constructors.

This module owns the catalogs for warnings and quality flags, recursive redaction
helpers to prevent leaking credentials/secrets, and validated building methods.
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.services.analytics.contracts.models import (
    AnalyticsWarning,
    QualityFlag,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger

# Patterns for sensitive keys and sensitive-looking string values (ANL-NFR-276)
SENSITIVE_KEYS_RE = re.compile(
    r"(api_key|secret|password|token|private_key|auth|account_id|account_number)",
    re.IGNORECASE,
)

SENSITIVE_VALUE_RE = re.compile(
    r"(eyJhbGciOi[-_a-zA-Z0-9.]+)|([a-fA-F0-9]{32,})",
)


@dataclass(frozen=True, slots=True)
class WarningCatalogEntry:
    """Catalog entry metadata for an AnalyticsWarning.

    Attributes:
        code: Unique warning catalog code.
        severity: Severity (informational/warning/major/critical/blocker).
        affected_section: Key name of the report section affected.
        source_backed_status: Code or status confirming the origin.
        blocks_promotion: True if this warning blocks report promotion.
        bounded_detail_rules: Allowed dictionary keys in detail payload.
        linked_test_fixture: Name of the test/fixture covering this case.
    """

    code: str
    severity: str
    affected_section: str
    source_backed_status: str
    blocks_promotion: bool
    bounded_detail_rules: tuple[str, ...]
    linked_test_fixture: str


@dataclass(frozen=True, slots=True)
class QualityFlagCatalogEntry:
    """Catalog entry metadata for a QualityFlag.

    Attributes:
        code: Unique quality flag code.
        severity: Severity level (informational/warning/major/critical/blocker).
        affected_section: Report section context target.
        source_backed_status: Code or status confirming the origin.
        blocks_promotion: True if this flag blocks report promotion.
        bounded_detail_rules: Allowed dictionary keys in detail payload.
        linked_test_fixture: Name of the test/fixture covering this case.
    """

    code: str
    severity: str
    affected_section: str
    source_backed_status: str
    blocks_promotion: bool
    bounded_detail_rules: tuple[str, ...]
    linked_test_fixture: str


# Canonical warning catalog (ANL-NFR-279)
WARNING_CATALOG: Mapping[str, WarningCatalogEntry] = {
    "LOW_SAMPLE_SIZE": WarningCatalogEntry(
        code="LOW_SAMPLE_SIZE",
        severity="warning",
        affected_section="trade_metrics",
        source_backed_status="active",
        blocks_promotion=False,
        bounded_detail_rules=("trade_count", "min_trades"),
        linked_test_fixture="test_report_low_sample_size",
    ),
    "DEGRADED_CONFIDENCE": WarningCatalogEntry(
        code="DEGRADED_CONFIDENCE",
        severity="warning",
        affected_section="metric",
        source_backed_status="active",
        blocks_promotion=False,
        bounded_detail_rules=("metric_name", "fallback_reason"),
        linked_test_fixture="test_r_multiple_fallback",
    ),
}

# Canonical quality flag catalog (ANL-NFR-279)
QUALITY_FLAG_CATALOG: Mapping[str, QualityFlagCatalogEntry] = {
    "LOW_PROFIT_FACTOR": QualityFlagCatalogEntry(
        code="LOW_PROFIT_FACTOR",
        severity="warning",
        affected_section="scorecard",
        source_backed_status="active",
        blocks_promotion=True,
        bounded_detail_rules=("profit_factor", "threshold"),
        linked_test_fixture="test_scorecard_profit_factor",
    ),
    "LOW_WIN_RATE": QualityFlagCatalogEntry(
        code="LOW_WIN_RATE",
        severity="warning",
        affected_section="scorecard",
        source_backed_status="active",
        blocks_promotion=True,
        bounded_detail_rules=("win_rate", "threshold"),
        linked_test_fixture="test_scorecard_win_rate",
    ),
    "HIGH_DRAWDOWN": QualityFlagCatalogEntry(
        code="HIGH_DRAWDOWN",
        severity="warning",
        affected_section="scorecard",
        source_backed_status="active",
        blocks_promotion=True,
        bounded_detail_rules=("max_drawdown", "threshold"),
        linked_test_fixture="test_scorecard_drawdown",
    ),
    "UNSTABLE_CURVE": QualityFlagCatalogEntry(
        code="UNSTABLE_CURVE",
        severity="major",
        affected_section="equity",
        source_backed_status="active",
        blocks_promotion=True,
        bounded_detail_rules=("r_squared", "threshold"),
        linked_test_fixture="test_unstable_curve",
    ),
}


def redact_sensitive_info(data: Any) -> Any:  # noqa: ANN401
    """Recursively redact sensitive keys and values from payloads (ANL-NFR-276).

    Args:
        data (Any): Input parameter `data`.

    Returns:
        Calculated Any value.
    """
    logger.debug("redact_sensitive_info: executed.")
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if isinstance(k, str) and SENSITIVE_KEYS_RE.search(k):
                new_dict[k] = "[REDACTED]"
            else:
                new_dict[k] = redact_sensitive_info(v)
        return new_dict
    if isinstance(data, list):
        return [redact_sensitive_info(x) for x in data]
    if isinstance(data, tuple):
        return tuple(redact_sensitive_info(x) for x in data)
    if isinstance(data, str):
        if SENSITIVE_VALUE_RE.search(data):
            return "[REDACTED]"
        if SENSITIVE_KEYS_RE.search(data) and ":" in data:
            return "[REDACTED]"
    return data


def build_warning(
    code: str,
    source_context: str | None = None,
    detail: dict[str, Any] | None = None,
) -> AnalyticsWarning:
    """Build a validated AnalyticsWarning (ANL-NFR-278, ANL-NFR-279).

    Args:
        code (str): Input parameter `code`.
        source_context (str | None): Input parameter `source_context`.
        detail (dict[str, Any] | None): Input parameter `detail`.

    Returns:
        Calculated AnalyticsWarning value.
    """
    logger.debug("build_warning: executed.")
    entry = WARNING_CATALOG.get(code)
    if entry is None:
        msg = f"Unknown warning catalog code: {code!r}."
        raise ValidationError(msg)

    raw_detail = detail or {}
    for k in raw_detail:
        if k not in entry.bounded_detail_rules:
            msg = f"Detail key {k!r} is not allowed for warning {code!r}."
            raise ValidationError(msg)

    redacted_detail = redact_sensitive_info(raw_detail)
    redacted_context = redact_sensitive_info(source_context) if source_context else None

    if not isinstance(redacted_detail, dict):
        msg = "Redacted details must be a dictionary."
        raise ValidationError(msg)

    return AnalyticsWarning(
        code=code,
        severity=entry.severity,
        affected_section=entry.affected_section,
        source_context=redacted_context,
        detail=redacted_detail,
    )


def build_quality_flag(
    code: str,
    source_context: str | None = None,
    detail: dict[str, Any] | None = None,
) -> QualityFlag:
    """Build a validated QualityFlag (ANL-NFR-278, ANL-NFR-279).

    Args:
        code (str): Input parameter `code`.
        source_context (str | None): Input parameter `source_context`.
        detail (dict[str, Any] | None): Input parameter `detail`.

    Returns:
        Calculated QualityFlag value.
    """
    logger.debug("build_quality_flag: executed.")
    entry = QUALITY_FLAG_CATALOG.get(code)
    if entry is None:
        msg = f"Unknown quality flag catalog code: {code!r}."
        raise ValidationError(msg)

    raw_detail = detail or {}
    for k in raw_detail:
        if k not in entry.bounded_detail_rules:
            msg = f"Detail key {k!r} is not allowed for quality flag {code!r}."
            raise ValidationError(msg)

    redacted_detail = redact_sensitive_info(raw_detail)
    redacted_context = redact_sensitive_info(source_context) if source_context else None

    if not isinstance(redacted_detail, dict):
        msg = "Redacted details must be a dictionary."
        raise ValidationError(msg)

    return QualityFlag(
        code=code,
        severity=entry.severity,
        affected_section=entry.affected_section,
        source_context=redacted_context,
        detail=redacted_detail,
    )
