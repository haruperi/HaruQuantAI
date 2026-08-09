"""Immutable catalogue of business-neutral system error definitions."""

from types import MappingProxyType

from app.utils.errors.contracts import ErrorDefinition

_COMMON_DEFINITIONS = (
    ErrorDefinition(
        code="CONFIGURATION_INVALID",
        domain="utils",
        description="Configuration is invalid",
        category="PERMANENT",
        severity="error",
        retryable=False,
        operator_action="Correct the active configuration",
    ),
    ErrorDefinition(
        code="EXTERNAL_SERVICE_UNAVAILABLE",
        domain="utils",
        description="External service is unavailable",
        category="TRANSIENT",
        severity="error",
        retryable=True,
        operator_action="Verify dependency readiness before retrying",
    ),
    ErrorDefinition(
        code="INTERNAL_ERROR",
        domain="utils",
        description="Internal error",
        category="INTEGRITY",
        severity="critical",
        retryable=False,
        operator_action="Inspect redacted diagnostic evidence",
    ),
    ErrorDefinition(
        code="SECURITY_POLICY_VIOLATION",
        domain="utils",
        description="Security policy violation",
        category="POLICY",
        severity="critical",
        retryable=False,
        operator_action="Review the governing security policy",
    ),
    ErrorDefinition(
        code="SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE",
        domain="app",
        description="Runtime profile and execution route are incompatible",
        category="POLICY",
        severity="error",
        retryable=False,
        operator_action="Select a compatible runtime profile and execution route",
    ),
    ErrorDefinition(
        code="VALIDATION_FAILED",
        domain="utils",
        description="Validation failed",
        category="PERMANENT",
        severity="warning",
        retryable=False,
        operator_action="Correct the supplied values",
    ),
    ErrorDefinition(
        code="UNKNOWN_STATE",
        domain="utils",
        description="Dependency state is unknown",
        category="UNKNOWN_STATE",
        severity="critical",
        retryable=False,
        operator_action="Reconcile dependency state before continuing",
    ),
)

COMMON_ERROR_CATALOG = MappingProxyType(
    {definition.code: definition for definition in _COMMON_DEFINITIONS}
)


def get_common_error_catalog() -> MappingProxyType[str, ErrorDefinition]:
    """Return the immutable common error catalogue mapping.

    Returns:
        Immutable dictionary mapping error codes to ErrorDefinition instances.
    """
    return COMMON_ERROR_CATALOG


__all__ = ["COMMON_ERROR_CATALOG", "get_common_error_catalog"]
