"""Risk-local validation result helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict


class ValidationResult(TypedDict):
    """Native risk validation result."""

    valid: bool
    message: str
    code: str
    details: dict[str, object]


def _ok(message: str = "Validation passed.") -> ValidationResult:
    """Return a successful validation result.

    Args:
        message: Human-readable validation message.

    Returns:
        Successful risk validation result.
    """
    return {"valid": True, "message": message, "code": "OK", "details": {}}


def _fail(
    message: str,
    *,
    code: str,
    details: Mapping[str, object],
) -> ValidationResult:
    """Return a failed validation result.

    Args:
        message: Human-readable validation failure message.
        code: Deterministic failure code.
        details: JSON-safe failure context.

    Returns:
        Failed risk validation result.
    """
    return {
        "valid": False,
        "message": message,
        "code": code,
        "details": dict(details),
    }


__all__ = ["ValidationResult", "_fail", "_ok"]
