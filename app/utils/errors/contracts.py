"""Business-neutral contracts for immutable error catalogues."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

type ErrorSeverity = Literal["info", "warning", "error", "critical"]

_SYMBOLIC_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z")
_DOMAIN_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_MAX_TEXT_LENGTH = 512


def _validate_text(value: str, field_name: str) -> None:
    """Validate one bounded, trimmed catalogue string.

    Args:
        value: Candidate string.
        field_name: Field name used in the validation error.

    Raises:
        ValueError: If the value is blank, untrimmed, or oversized.
    """
    if not value or value != value.strip() or len(value) > _MAX_TEXT_LENGTH:
        message = (
            f"{field_name} must be a trimmed string of 1..{_MAX_TEXT_LENGTH} characters"
        )
        raise ValueError(message)


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorDefinition:
    """Safe metadata describing one approved symbolic error code.

    Attributes:
        code: Globally unique uppercase symbolic error code.
        domain: Lowercase domain that owns the code.
        description: Safe human-readable description.
        category: Safe machine-readable error category.
        severity: Diagnostic severity.
        retryable: Whether a caller may retry under the owning domain's policy.
        operator_action: Safe recommended operator action.
    """

    code: str
    domain: str
    description: str
    category: str
    severity: ErrorSeverity
    retryable: bool
    operator_action: str

    def __post_init__(self) -> None:
        """Validate immutable catalogue metadata.

        Raises:
            ValueError: If a field is malformed, blank, untrimmed, or oversized.
        """
        if _SYMBOLIC_CODE.fullmatch(self.code) is None:
            raise ValueError("code must be an uppercase symbolic token")
        if _DOMAIN_NAME.fullmatch(self.domain) is None:
            raise ValueError("domain must be a lowercase symbolic token")
        _validate_text(self.description, "description")
        _validate_text(self.category, "category")
        _validate_text(self.operator_action, "operator_action")


__all__ = ["ErrorDefinition", "ErrorSeverity"]
