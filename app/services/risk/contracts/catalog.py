"""Immutable Risk error definitions for public response boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from app.services.risk.contracts.enums import RiskErrorCode
from app.utils import normalize_error_code

type ErrorSeverity = Literal["info", "warning", "error", "critical"]


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


def _definition(
    code: RiskErrorCode,
    description: str,
    category: str,
    severity: ErrorSeverity,
    retryable: bool,
    operator_action: str,
) -> ErrorDefinition:
    """Build one immutable Risk-owned error definition.

    Args:
        code: Stable Risk error code.
        description: Safe operator-facing description.
        category: Machine-readable failure category.
        severity: Diagnostic severity.
        retryable: Whether retry may be considered by the owning policy.
        operator_action: Safe operator action.

    Returns:
        Validated immutable error definition.
    """
    return ErrorDefinition(
        code=code.value,
        domain="risk",
        description=description,
        category=category,
        severity=severity,
        retryable=retryable,
        operator_action=operator_action,
    )


_DEFINITIONS = (
    _definition(
        RiskErrorCode.INVALID_INPUT,
        "Risk input is invalid",
        "validation",
        "warning",
        False,
        "Correct the supplied Risk input",
    ),
    _definition(
        RiskErrorCode.VALIDATION_FAILED,
        "Risk validation failed",
        "validation",
        "warning",
        False,
        "Correct the supplied Risk evidence",
    ),
    _definition(
        RiskErrorCode.INVALID_PORTFOLIO_STATE,
        "Portfolio state is invalid",
        "evidence",
        "critical",
        False,
        "Provide complete valid portfolio evidence",
    ),
    _definition(
        RiskErrorCode.INVALID_RISK_CONFIG,
        "Risk configuration is invalid",
        "configuration",
        "critical",
        False,
        "Correct the active Risk configuration",
    ),
    _definition(
        RiskErrorCode.MISSING_EVIDENCE,
        "Required Risk evidence is missing",
        "evidence",
        "critical",
        False,
        "Provide the required evidence",
    ),
    _definition(
        RiskErrorCode.STALE_EVIDENCE,
        "Required Risk evidence is stale",
        "evidence",
        "critical",
        False,
        "Refresh the required evidence",
    ),
    _definition(
        RiskErrorCode.LIMIT_FAILED,
        "A Risk limit failed",
        "policy",
        "critical",
        False,
        "Review the failed Risk limit",
    ),
    _definition(
        RiskErrorCode.POLICY_BLOCKED,
        "Risk policy blocked the operation",
        "policy",
        "critical",
        False,
        "Resolve the governing Risk policy block",
    ),
    _definition(
        RiskErrorCode.PERMISSION_DENIED,
        "Risk permission was denied",
        "authorization",
        "critical",
        False,
        "Use an authorized Risk principal",
    ),
    _definition(
        RiskErrorCode.KILL_SWITCH_ACTIVE,
        "A Risk kill switch is active",
        "safety",
        "critical",
        False,
        "Keep execution blocked until authorized clearance",
    ),
    _definition(
        RiskErrorCode.KILL_SWITCH_UNKNOWN,
        "Risk kill-switch state is unproven",
        "safety",
        "critical",
        False,
        "Reconcile and prove kill-switch state",
    ),
    _definition(
        RiskErrorCode.APPROVAL_REQUIRED,
        "Risk approval is required",
        "authorization",
        "warning",
        False,
        "Provide valid approval evidence",
    ),
    _definition(
        RiskErrorCode.APPROVAL_TOKEN_INVALID,
        "Risk approval token is invalid",
        "authorization",
        "critical",
        False,
        "Reject the token and request a valid one",
    ),
    _definition(
        RiskErrorCode.APPROVAL_TOKEN_EXPIRED,
        "Risk approval token is expired",
        "authorization",
        "critical",
        False,
        "Issue a current approval token",
    ),
    _definition(
        RiskErrorCode.APPROVAL_TOKEN_REVOKED,
        "Risk approval token is revoked",
        "authorization",
        "critical",
        False,
        "Issue a new approval after review",
    ),
    _definition(
        RiskErrorCode.APPROVAL_TOKEN_CONSUMED,
        "Risk approval token is already consumed",
        "authorization",
        "critical",
        False,
        "Do not replay the token",
    ),
    _definition(
        RiskErrorCode.CONFIG_VERSION_MISMATCH,
        "Risk configuration version mismatched",
        "configuration",
        "critical",
        False,
        "Refresh the Risk decision and configuration",
    ),
    _definition(
        RiskErrorCode.PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED,
        "Pending approval double spend was blocked",
        "concurrency",
        "critical",
        False,
        "Reconcile pending approval state",
    ),
    _definition(
        RiskErrorCode.PAYLOAD_TOO_LARGE,
        "Risk payload exceeds the configured bound",
        "validation",
        "warning",
        False,
        "Reduce the bounded Risk payload",
    ),
    _definition(
        RiskErrorCode.MISSING_STOP_LOSS,
        "Required stop-loss evidence is missing",
        "evidence",
        "critical",
        False,
        "Provide a valid stop-loss",
    ),
    _definition(
        RiskErrorCode.INSUFFICIENT_VOLATILITY_EVIDENCE,
        "Volatility evidence is insufficient",
        "evidence",
        "critical",
        False,
        "Provide sufficient volatility evidence",
    ),
    _definition(
        RiskErrorCode.INSUFFICIENT_K_EVIDENCE,
        "Kelly evidence is insufficient",
        "evidence",
        "critical",
        False,
        "Provide sufficient Kelly evidence",
    ),
    _definition(
        RiskErrorCode.LIVE_STATE_STALE,
        "Live Risk state is stale",
        "evidence",
        "critical",
        False,
        "Refresh live state before proceeding",
    ),
    _definition(
        RiskErrorCode.IN_FLIGHT_TOLERANCE_EXCEEDED,
        "In-flight tolerance was exceeded",
        "reconciliation",
        "critical",
        False,
        "Freeze execution and reconcile state",
    ),
    _definition(
        RiskErrorCode.IN_FLIGHT_RECONCILIATION_EXPIRED,
        "In-flight reconciliation evidence expired",
        "reconciliation",
        "critical",
        False,
        "Reconcile current execution state",
    ),
    _definition(
        RiskErrorCode.AUDIT_CHAIN_TAMPER_DETECTED,
        "Risk audit-chain tamper was detected",
        "integrity",
        "critical",
        False,
        "Stop processing and investigate the audit chain",
    ),
    _definition(
        RiskErrorCode.CALCULATION_FAILED,
        "Risk calculation failed",
        "calculation",
        "critical",
        False,
        "Inspect the bounded calculation failure",
    ),
    _definition(
        RiskErrorCode.SNAPSHOT_BUILD_FAILED,
        "Risk snapshot construction failed",
        "calculation",
        "critical",
        False,
        "Refresh and validate portfolio evidence",
    ),
    _definition(
        RiskErrorCode.GOVERNOR_DECISION_FAILED,
        "Risk governor decision failed",
        "governance",
        "critical",
        False,
        "Keep the action blocked and inspect evidence",
    ),
    _definition(
        RiskErrorCode.REPORT_GENERATION_FAILED,
        "Risk report generation failed",
        "reporting",
        "error",
        False,
        "Retry only after verifying the source result",
    ),
    _definition(
        RiskErrorCode.STORAGE_ERROR,
        "Risk persistence failed",
        "persistence",
        "critical",
        True,
        "Keep the operation blocked and verify storage",
    ),
    _definition(
        RiskErrorCode.TOOL_EXECUTION_FAILED,
        "Risk tool execution failed",
        "execution",
        "critical",
        False,
        "Keep the operation blocked and inspect the boundary",
    ),
    _definition(
        RiskErrorCode.UNKNOWN_ERROR,
        "An unknown Risk error occurred",
        "internal",
        "critical",
        False,
        "Inspect redacted diagnostic evidence",
    ),
)


def _validate_catalog(
    definitions: tuple[ErrorDefinition, ...],
) -> MappingProxyType[str, ErrorDefinition]:
    """Validate and freeze Risk-owned error definitions.

    Args:
        definitions: Ordered Risk error definitions.

    Returns:
        Immutable code-keyed Risk error catalogue.

    Raises:
        ValueError: If a code is malformed, duplicated, or mismatched.
    """
    validated: dict[str, ErrorDefinition] = {}
    for definition in definitions:
        code = normalize_error_code(definition.code)
        if code != definition.code or code in validated:
            raise ValueError("Risk error catalogue is inconsistent")
        validated[code] = definition
    return MappingProxyType(validated)


RISK_ERROR_CATALOG = _validate_catalog(_DEFINITIONS)

__all__ = ["RISK_ERROR_CATALOG"]
