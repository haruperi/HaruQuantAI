"""Research-owned immutable error catalogue for public responses."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal


class ResearchError(ValueError):
    """Research-owned symbolic exception safe for public boundaries."""

    def __init__(self, code: str, detail: str) -> None:
        """Initialize symbolic Research failure evidence."""
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


class ConfigurationError(ResearchError):
    """Research configuration or stage dependency is invalid."""


class ValidationError(ResearchError):
    """Research input or evidence is invalid."""


class SecurityError(ResearchError, PermissionError):
    """Research publication or persistence violates a safety boundary."""


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


_DEFINITIONS = (
    ErrorDefinition(
        code="RES_CONFIGURATION_INVALID",
        domain="research",
        description="Research configuration is invalid",
        category="configuration",
        severity="error",
        retryable=False,
        operator_action="Correct the Research configuration before retrying",
    ),
    ErrorDefinition(
        code="RES_STAGE_DEPENDENCY_INVALID",
        domain="research",
        description="Selected Research stages have an invalid dependency",
        category="configuration",
        severity="error",
        retryable=False,
        operator_action="Select stages with their required Research prerequisites",
    ),
    ErrorDefinition(
        code="RES_STAGE_UNAVAILABLE",
        domain="research",
        description="A selected Research stage is unavailable",
        category="capability",
        severity="warning",
        retryable=False,
        operator_action="Select a stage from the supported Research workflow",
    ),
    ErrorDefinition(
        code="RES_INPUT_INVALID",
        domain="research",
        description="Research input is invalid",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Correct the supplied Research input",
    ),
    ErrorDefinition(
        code="RES_INSUFFICIENT_DATA",
        domain="research",
        description="Research input contains insufficient usable data",
        category="validation",
        severity="warning",
        retryable=True,
        operator_action="Supply a larger bounded research-ready dataset",
    ),
    ErrorDefinition(
        code="RES_NONFINITE_DATA",
        domain="research",
        description="Research input contains non-finite data",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Supply finite research input values",
    ),
    ErrorDefinition(
        code="RES_RESOURCE_LIMIT_EXCEEDED",
        domain="research",
        description="Research execution exceeds an approved resource limit",
        category="resource",
        severity="error",
        retryable=False,
        operator_action="Reduce the request to the approved Research bounds",
    ),
    ErrorDefinition(
        code="RES_VERSION_INCOMPATIBLE",
        domain="research",
        description="Research evidence uses an incompatible contract version",
        category="compatibility",
        severity="error",
        retryable=False,
        operator_action="Use the supported Research contract version",
    ),
    ErrorDefinition(
        code="RES_MODEL_FIT_FAILED",
        domain="research",
        description="A Research model could not be fit",
        category="calculation",
        severity="error",
        retryable=False,
        operator_action="Inspect bounded model inputs and configuration",
    ),
    ErrorDefinition(
        code="RES_PERMISSION_DENIED",
        domain="research",
        description="Research permission was denied",
        category="authorization",
        severity="error",
        retryable=False,
        operator_action="Use an authorized Research principal",
    ),
    ErrorDefinition(
        code="RES_LEAKAGE_DETECTED",
        domain="research",
        description="Research evidence failed the leakage gate",
        category="safety",
        severity="critical",
        retryable=False,
        operator_action="Remove the leakage before publishing evidence",
    ),
    ErrorDefinition(
        code="RES_ARTIFACT_PATH_REJECTED",
        domain="research",
        description="The Research artifact path was rejected",
        category="security",
        severity="critical",
        retryable=False,
        operator_action="Use a destination under the approved artifact root",
    ),
    ErrorDefinition(
        code="RES_SENSITIVE_OUTPUT_REJECTED",
        domain="research",
        description="Research output contains rejected sensitive content",
        category="security",
        severity="critical",
        retryable=False,
        operator_action="Remove sensitive content before sharing Research output",
    ),
    ErrorDefinition(
        code="RES_ARTIFACT_CONFLICT",
        domain="research",
        description="The Research artifact destination conflicts with existing state",
        category="persistence",
        severity="error",
        retryable=False,
        operator_action="Choose an unused destination or explicitly allow overwrite",
    ),
    ErrorDefinition(
        code="RES_ARTIFACT_TOO_LARGE",
        domain="research",
        description="The Research artifact exceeds its size limit",
        category="resource",
        severity="error",
        retryable=False,
        operator_action="Reduce the artifact to the approved size bound",
    ),
    ErrorDefinition(
        code="RES_ARTIFACT_ATOMICITY_UNAVAILABLE",
        domain="research",
        description="Atomic Research artifact replacement is unavailable",
        category="persistence",
        severity="critical",
        retryable=False,
        operator_action="Use a storage target supporting the required atomic operation",
    ),
    ErrorDefinition(
        code="RES_ARTIFACT_WRITE_FAILED",
        domain="research",
        description="The Research artifact could not be written",
        category="persistence",
        severity="error",
        retryable=True,
        operator_action="Inspect the approved artifact destination and retry safely",
    ),
    ErrorDefinition(
        code="RES_AUDIT_PERSISTENCE_FAILED",
        domain="research",
        description="The Research audit event could not be persisted",
        category="persistence",
        severity="critical",
        retryable=True,
        operator_action="Restore audit persistence before repeating the write",
    ),
    ErrorDefinition(
        code="RES_PERSISTENCE_FAILED",
        domain="research",
        description="A Research-owned durable record could not be confirmed",
        category="persistence",
        severity="error",
        retryable=True,
        operator_action="Inspect the approved persistence target and retry safely",
    ),
    ErrorDefinition(
        code="RES_GOVERNANCE_TRANSITION_INVALID",
        domain="research",
        description="An approved expectancy governance transition is invalid",
        category="governance",
        severity="error",
        retryable=False,
        operator_action="Apply a governance transition permitted for the current state",
    ),
    ErrorDefinition(
        code="RES_EXPECTANCY_NOT_ELIGIBLE",
        domain="research",
        description="No approved expectancy profile is eligible for the request",
        category="governance",
        severity="warning",
        retryable=False,
        operator_action="Supply exact-match keys covered by an approved profile",
    ),
    ErrorDefinition(
        code="RES_DRIFT_INSUFFICIENT_EVIDENCE",
        domain="research",
        description="Drift evidence cannot be evaluated without an approved envelope",
        category="validation",
        severity="warning",
        retryable=True,
        operator_action="Supply an approved expectancy profile envelope",
    ),
    ErrorDefinition(
        code="RES_STRESS_SCENARIO_INVALID",
        domain="research",
        description="A stress-scenario evidence basis is invalid or invented",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Cite a historical event or an explicit reasoned assumption",
    ),
)

RESEARCH_ERROR_CATALOG = MappingProxyType(
    {definition.code: definition for definition in _DEFINITIONS}
)

__all__ = (
    "RESEARCH_ERROR_CATALOG",
    "ConfigurationError",
    "ResearchError",
    "SecurityError",
    "ValidationError",
)
