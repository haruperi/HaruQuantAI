"""Catalog-backed Analytics evidence construction and output safety."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import numpy as np
import pandas as pd

from app.services.analytics.contracts.catalogs import EVIDENCE_CATALOG
from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.models import AnalyticsWarning, QualityFlag
from app.utils import (
    ValidationError as UtilsValidationError,
)
from app.utils import (
    canonical_json,
    logger,
    redact_mapping_value,
)
from app.utils import (
    to_json_safe as _utils_to_json_safe,
)


def _normalize_analytical_value(value: object) -> object:
    """Normalize pandas and NumPy values before Utils serialization.

    Args:
        value: Candidate report value.

    Returns:
        Python/Utils-supported representation.
    """
    logger.debug("Normalizing analytical value for Analytics output")
    result = value
    if isinstance(value, np.generic):
        result = value.item()
    elif isinstance(value, np.ndarray):
        result = tuple(_normalize_analytical_value(item) for item in value.tolist())
    elif isinstance(value, pd.Timestamp):
        result = value.to_pydatetime()
    elif isinstance(value, (pd.Series, pd.Index)):
        result = tuple(_normalize_analytical_value(item) for item in value.tolist())
    elif isinstance(value, pd.DataFrame):
        result = tuple(
            {str(key): _normalize_analytical_value(item) for key, item in row.items()}
            for row in value.to_dict(orient="records")
        )
    elif isinstance(value, Mapping):
        result = {
            str(key): _normalize_analytical_value(item) for key, item in value.items()
        }
    elif isinstance(value, (tuple, list)):
        result = tuple(_normalize_analytical_value(item) for item in value)
    return result


def _safe_detail(
    detail: Mapping[str, object],
    *,
    max_detail_bytes: int,
) -> dict[str, object]:
    """Return bounded redacted catalog detail.

    Args:
        detail: Candidate detail mapping.
        max_detail_bytes: Positive maximum canonical byte size.

    Returns:
        Redacted JSON-safe detail.

    Raises:
        AnalyticsValidationError: If detail or its bound is invalid.
    """
    logger.debug("Bounding and redacting Analytics evidence detail")
    if max_detail_bytes <= 0:
        raise AnalyticsValidationError("max_detail_bytes must be positive")
    try:
        safe = _utils_to_json_safe(_normalize_analytical_value(detail))
        if not isinstance(safe, dict):
            raise AnalyticsValidationError("evidence detail must remain a mapping")
        redacted = redact_mapping_value(safe)
        if not isinstance(redacted.value, dict):
            raise AnalyticsValidationError("redacted evidence detail is invalid")
        result = dict(redacted.value)
        if len(canonical_json(result).encode("utf-8")) > max_detail_bytes:
            raise AnalyticsValidationError("evidence detail exceeds configured bound")
        return result
    except UtilsValidationError as error:
        raise AnalyticsValidationError("evidence detail is unsafe") from error


def build_warning(
    code: str,
    *,
    section: str,
    source_context: str,
    detail: Mapping[str, object],
    max_detail_bytes: int,
) -> AnalyticsWarning:
    """Build one catalog-backed bounded warning.

    Args:
        code: Warning catalog code.
        section: Affected report section.
        source_context: Evidence source context.
        detail: Required structured detail.
        max_detail_bytes: Positive canonical detail bound.

    Returns:
        Immutable warning evidence.

    Raises:
        AnalyticsValidationError: If catalog or detail validation fails.
    """
    logger.info("Building catalog-backed Analytics warning")
    definition = EVIDENCE_CATALOG["warnings"].get(code)
    if definition is None:
        message = f"uncataloged warning code: {code}"
        raise AnalyticsValidationError(message)
    safe_detail = _safe_detail(detail, max_detail_bytes=max_detail_bytes)
    required = cast("tuple[str, ...]", definition["required_detail_keys"])
    if not set(required).issubset(safe_detail):
        raise AnalyticsValidationError("warning detail is incomplete")
    return AnalyticsWarning(
        code=code,
        severity=str(definition["severity"]),
        affected_section=section,
        source_context=source_context,
        detail=safe_detail,
    )


def build_quality_flag(
    code: str,
    *,
    section: str,
    source_context: str,
    detail: Mapping[str, object],
    max_detail_bytes: int,
) -> QualityFlag:
    """Build one catalog-backed non-governing quality flag.

    Args:
        code: Quality-flag catalog code.
        section: Affected report section.
        source_context: Evidence source context.
        detail: Required structured detail.
        max_detail_bytes: Positive canonical detail bound.

    Returns:
        Immutable quality-flag evidence.

    Raises:
        AnalyticsValidationError: If catalog or detail validation fails.
    """
    logger.info("Building catalog-backed Analytics quality flag")
    definition = EVIDENCE_CATALOG["quality_flags"].get(code)
    if definition is None:
        message = f"uncataloged quality flag code: {code}"
        raise AnalyticsValidationError(message)
    safe_detail = _safe_detail(detail, max_detail_bytes=max_detail_bytes)
    required = cast("tuple[str, ...]", definition["required_detail_keys"])
    if not set(required).issubset(safe_detail):
        raise AnalyticsValidationError("quality-flag detail is incomplete")
    return QualityFlag(
        code=code,
        severity=str(definition["severity"]),
        blocker=bool(definition["blocker"]),
        affected_sections=(section,),
        source_context=source_context,
        detail=safe_detail,
    )


def to_report_json_safe(value: object) -> object:
    """Convert report-specific analytical values through Utils serialization.

    Args:
        value: Candidate report evidence.

    Returns:
        Finite JSON-safe evidence.

    Raises:
        AnalyticsValidationError: If conversion is unsafe or unsupported.
    """
    logger.info("Converting Analytics report evidence to JSON-safe values")
    try:
        return _utils_to_json_safe(_normalize_analytical_value(value))
    except UtilsValidationError as error:
        raise AnalyticsValidationError(
            "report value is not finite JSON-safe evidence"
        ) from error


__all__ = ["build_quality_flag", "build_warning", "to_report_json_safe"]
