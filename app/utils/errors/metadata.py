"""Provide immutable display metadata for normalized shared error codes."""

import re
from dataclasses import dataclass
from typing import Literal

from app.utils.errors.exceptions import ValidationError

_SYMBOLIC_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z")


@dataclass(frozen=True, slots=True)
class ErrorMetadata:
    """Represent safe display metadata for one symbolic error code.

    Attributes:
        code: Normalized uppercase symbolic error code.
        title: Secret-safe human-readable title.
        severity: Stable display severity classification.
        retryable: Whether a caller may safely retry the failed operation.
    """

    code: str
    title: str
    severity: Literal["info", "warning", "error", "critical"]
    retryable: bool


_ERROR_METADATA = {
    "CONFIGURATION_INVALID": ErrorMetadata(
        "CONFIGURATION_INVALID", "Configuration is invalid", "error", False
    ),
    "EXTERNAL_SERVICE_UNAVAILABLE": ErrorMetadata(
        "EXTERNAL_SERVICE_UNAVAILABLE", "External service is unavailable", "error", True
    ),
    "INTERNAL_ERROR": ErrorMetadata(
        "INTERNAL_ERROR", "Internal error", "critical", False
    ),
    "SECURITY_POLICY_VIOLATION": ErrorMetadata(
        "SECURITY_POLICY_VIOLATION", "Security policy violation", "critical", False
    ),
    "VALIDATION_FAILED": ErrorMetadata(
        "VALIDATION_FAILED", "Validation failed", "warning", False
    ),
}


def normalize_error_code(code: str) -> str:
    """Normalize a human-entered code to uppercase symbolic syntax.

    Args:
        code: Candidate code containing letters, digits, spaces, or hyphens.

    Returns:
        A trimmed uppercase token with whitespace and hyphens converted to
        underscores.

    Raises:
        ValidationError: The input is not a string or cannot be normalized to
            the approved symbolic-token grammar.
    """
    if not isinstance(code, str):
        raise ValidationError("ERROR_CODE_INVALID")
    normalized = re.sub(r"[\s-]+", "_", code.strip()).upper()
    if _SYMBOLIC_CODE.fullmatch(normalized) is None:
        raise ValidationError("ERROR_CODE_INVALID")
    return normalized


def get_error_metadata(code: str) -> ErrorMetadata:
    """Return immutable metadata for a normalized error code.

    Args:
        code: Candidate symbolic code accepted by ``normalize_error_code``.

    Returns:
        Built-in metadata when registered, otherwise deterministic generic
        metadata carrying the normalized code.

    Raises:
        ValidationError: The code cannot be normalized safely.
    """
    normalized = normalize_error_code(code)
    return _ERROR_METADATA.get(
        normalized,
        ErrorMetadata(normalized, "Application error", "error", False),
    )
