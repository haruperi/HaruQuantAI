"""Controlled errors for the Optimization domain."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from app.utils import (
    get_logger,
    redact_mapping_value,
    validate_error_catalog,
)


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
        code="OPT_ADAPTER_INCOMPATIBLE",
        domain="optimization",
        description="The execution adapter is incompatible with the request",
        category="dependency",
        severity="error",
        retryable=False,
        operator_action="Use a compatible deterministic execution adapter",
    ),
    ErrorDefinition(
        code="OPT_CONSTRAINT_INVALID",
        domain="optimization",
        description="The optimization constraint is invalid",
        category="validation",
        severity="warning",
        retryable=False,
        operator_action="Correct the parameter constraint definition",
    ),
    ErrorDefinition(
        code="OPT_EVIDENCE_INCOMPLETE",
        domain="optimization",
        description="Required optimization evidence is incomplete",
        category="evidence",
        severity="warning",
        retryable=False,
        operator_action="Supply the missing bounded evidence before review",
    ),
    ErrorDefinition(
        code="OPT_EXECUTION_FAILED",
        domain="optimization",
        description="A candidate execution failed",
        category="execution",
        severity="error",
        retryable=True,
        operator_action="Inspect the safe execution evidence before retrying",
    ),
    ErrorDefinition(
        code="OPT_INTERNAL_ERROR",
        domain="optimization",
        description="Optimization failed with an unexpected internal error",
        category="internal",
        severity="critical",
        retryable=False,
        operator_action="Inspect redacted diagnostic evidence",
    ),
    ErrorDefinition(
        code="OPT_INVALID_REQUEST",
        domain="optimization",
        description="The optimization request is invalid",
        category="validation",
        severity="warning",
        retryable=False,
        operator_action="Correct the supplied optimization request",
    ),
    ErrorDefinition(
        code="OPT_LEAKAGE_DETECTED",
        domain="optimization",
        description="Time-series or evaluation leakage was detected",
        category="security",
        severity="critical",
        retryable=False,
        operator_action="Reject the run and review temporal evidence",
    ),
    ErrorDefinition(
        code="OPT_LIMIT_EXCEEDED",
        domain="optimization",
        description="An approved optimization limit was exceeded",
        category="resource_limit",
        severity="error",
        retryable=False,
        operator_action="Reduce the request within the approved bounds",
    ),
    ErrorDefinition(
        code="OPT_PERSISTENCE_FAILED",
        domain="optimization",
        description="Optimization evidence persistence failed",
        category="persistence",
        severity="error",
        retryable=True,
        operator_action="Verify the injected store before retrying",
    ),
    ErrorDefinition(
        code="OPT_STATE_CONFLICT",
        domain="optimization",
        description="Optimization state conflicts with the supplied identity",
        category="state",
        severity="error",
        retryable=False,
        operator_action="Reconcile the optimization state identity",
    ),
)

OPTIMIZATION_ERROR_CATALOG = validate_error_catalog(
    MappingProxyType(
        {definition.code: definition for definition in _OPTIMIZATION_ERROR_DEFINITIONS}
    )
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
