"""Validation reason-code and severity rules."""

import re

from app.utils.errors.exceptions import ValidationError

_REASON = re.compile(r"[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+\Z")
_SEVERITY = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}


def validate_reason_code(code: str) -> str:
    """Validate canonical uppercase dotted reason syntax.

    Args:
        code: Candidate reason code.

    Returns:
        Validated code.

    Raises:
        ValidationError: If syntax is invalid.
    """
    if _REASON.fullmatch(code) is None:
        raise ValidationError("REASON_CODE_INVALID")
    return code


def get_severity_rank(severity: str) -> int:
    """Return the strictness rank for a supported severity.

    Args:
        severity: Supported severity.

    Returns:
        Severity rank.

    Raises:
        ValidationError: If severity is unknown.
    """
    try:
        return _SEVERITY[severity]
    except KeyError as error:
        raise ValidationError("SEVERITY_INVALID") from error
