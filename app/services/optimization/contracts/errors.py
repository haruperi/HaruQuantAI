"""Controlled errors for the Optimization domain."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from app.utils import get_logger, redact_mapping_value


class HaruQuantError(Exception):
    """Local safe error base for Optimization exceptions."""

    def __init__(self, code: str, detail: str = "UNSPECIFIED") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Immutable domain-owned error catalogue entry."""

    code: str
    domain: str
    description: str
    category: str
    severity: Literal["info", "warning", "error", "critical"]
    retryable: bool
    operator_action: str


logger = get_logger(__name__)

_OPTIMIZATION_ERROR_DEFINITIONS = (
    ErrorDefinition(
        "OPT_ADAPTER_INCOMPATIBLE",
        "optimization",
        "The execution adapter is incompatible with the request",
        "dependency",
        "error",
        False,
        "Use a compatible deterministic execution adapter",
    ),
    ErrorDefinition(
        "OPT_CONSTRAINT_INVALID",
        "optimization",
        "The optimization constraint is invalid",
        "validation",
        "warning",
        False,
        "Correct the parameter constraint definition",
    ),
    ErrorDefinition(
        "OPT_EVIDENCE_INCOMPLETE",
        "optimization",
        "Required optimization evidence is incomplete",
        "evidence",
        "warning",
        False,
        "Supply the missing bounded evidence before review",
    ),
    ErrorDefinition(
        "OPT_EXECUTION_FAILED",
        "optimization",
        "A candidate execution failed",
        "execution",
        "error",
        True,
        "Inspect the safe execution evidence before retrying",
    ),
    ErrorDefinition(
        "OPT_INTERNAL_ERROR",
        "optimization",
        "Optimization failed with an unexpected internal error",
        "internal",
        "critical",
        False,
        "Inspect redacted diagnostic evidence",
    ),
    ErrorDefinition(
        "OPT_INVALID_REQUEST",
        "optimization",
        "The optimization request is invalid",
        "validation",
        "warning",
        False,
        "Correct the supplied optimization request",
    ),
    ErrorDefinition(
        "OPT_LEAKAGE_DETECTED",
        "optimization",
        "Time-series or evaluation leakage was detected",
        "security",
        "critical",
        False,
        "Reject the run and review temporal evidence",
    ),
    ErrorDefinition(
        "OPT_LIMIT_EXCEEDED",
        "optimization",
        "An approved optimization limit was exceeded",
        "resource_limit",
        "error",
        False,
        "Reduce the request within the approved bounds",
    ),
    ErrorDefinition(
        "OPT_PERSISTENCE_FAILED",
        "optimization",
        "Optimization evidence persistence failed",
        "persistence",
        "error",
        True,
        "Verify the injected store before retrying",
    ),
    ErrorDefinition(
        "OPT_STATE_CONFLICT",
        "optimization",
        "Optimization state conflicts with the supplied identity",
        "state",
        "error",
        False,
        "Reconcile the optimization state identity",
    ),
)

OPTIMIZATION_ERROR_CATALOG = MappingProxyType(
    {definition.code: definition for definition in _OPTIMIZATION_ERROR_DEFINITIONS}
)


class OptimizationError(HaruQuantError):
    """Fail-closed Optimization error with redacted JSON-safe details."""

    def __init__(
        self,
        code: str,
        detail: str = "UNSPECIFIED",
        *,
        safe_details: Mapping[str, object] | None = None,
    ) -> None:
        """Initialize a controlled Optimization error.

        Args:
            code: Cataloged Optimization error code.
            detail: Uppercase symbolic safe detail.
            safe_details: Optional detail mapping redacted at construction.

        Raises:
            TypeError: If redaction does not return a mapping.
            ValueError: If the error code or detail is invalid.
        """
        logger.debug("Creating OptimizationError with code %s", code)
        if code not in OPTIMIZATION_ERROR_CATALOG:
            raise ValueError("Optimization error code is not cataloged")
        super().__init__(code, detail)
        redacted = redact_mapping_value(safe_details or {}).value
        if not isinstance(redacted, Mapping):
            raise TypeError("Optimization error details must be a mapping")
        self.safe_details = MappingProxyType(dict(redacted))

    def to_payload(self) -> dict[str, object]:
        """Return the controlled JSON-safe public payload.

        Returns:
            Stable error code, symbolic detail, and redacted details.
        """
        logger.info("Building Optimization error payload")
        return {
            "code": self.code,
            "detail": self.detail,
            "details": dict(self.safe_details),
        }


__all__ = ["OPTIMIZATION_ERROR_CATALOG", "OptimizationError"]
