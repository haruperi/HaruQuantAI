"""Immutable metadata for normalized shared error codes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.utils.errors.exceptions import ValidationError

_SYMBOLIC_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z")


@dataclass(frozen=True, slots=True)
class ErrorMetadata:
    """Safe display and handling metadata for one symbolic error code."""

    code: str
    title: str
    severity: Literal["info", "warning", "error", "critical"]
    retryable: bool


_ERROR_METADATA = {
    "CONFIGURATION_INVALID": ErrorMetadata(
        code="CONFIGURATION_INVALID",
        title="Configuration is invalid",
        severity="error",
        retryable=False,
    ),
    "EXTERNAL_SERVICE_UNAVAILABLE": ErrorMetadata(
        code="EXTERNAL_SERVICE_UNAVAILABLE",
        title="External service is unavailable",
        severity="error",
        retryable=True,
    ),
    "INTERNAL_ERROR": ErrorMetadata(
        code="INTERNAL_ERROR",
        title="Internal error",
        severity="critical",
        retryable=False,
    ),
    "SECURITY_POLICY_VIOLATION": ErrorMetadata(
        code="SECURITY_POLICY_VIOLATION",
        title="Security policy violation",
        severity="critical",
        retryable=False,
    ),
    "VALIDATION_FAILED": ErrorMetadata(
        code="VALIDATION_FAILED",
        title="Validation failed",
        severity="warning",
        retryable=False,
    ),
}


def normalize_error_code(code: str) -> str:
    """Normalize a human-entered code to uppercase symbolic syntax.

    Args:
        code: Error code containing letters, digits, spaces, hyphens, or underscores.

    Returns:
        Canonical uppercase symbolic error code.

    Raises:
        ValidationError: If the normalized code is empty or malformed.
    """
    if not isinstance(code, str):
        raise ValidationError("ERROR_CODE_INVALID")
    normalized = re.sub(r"[\s-]+", "_", code.strip()).upper()
    if _SYMBOLIC_CODE.fullmatch(normalized) is None:
        raise ValidationError("ERROR_CODE_INVALID")
    return normalized


def get_error_metadata(code: str) -> ErrorMetadata:
    """Look up safe immutable metadata for a normalized error code.

    Unknown valid codes receive deterministic generic metadata without mutating a
    process-wide registry.

    Args:
        code: Human-entered or canonical symbolic error code.

    Returns:
        Built-in or deterministic generic immutable metadata.

    Raises:
        ValidationError: If the code cannot be normalized.
    """
    normalized = normalize_error_code(code)
    return _ERROR_METADATA.get(
        normalized,
        ErrorMetadata(
            code=normalized,
            title="Application error",
            severity="error",
            retryable=False,
        ),
    )
