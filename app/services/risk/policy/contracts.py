"""Policy-as-code contract definitions.

Provides immutable schemas for scopes, rules, resolved policy envelopes,
and validation results.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, TypedDict

from pydantic import Field

from app.services.risk.models import (
    PolicyEnforcementResult,
    PolicyRule,
    PolicyScope,
    RiskApprovalToken,
    RiskConfig,
    RiskContract,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.utils.validations import ValidationResult

# Re-export key contract models from domain contracts
__all__ = [
    "EffectiveRiskPolicy",
    "OverrideValidationResult",
    "PolicyEnforcementResult",
    "PolicyPrecedenceRule",
    "PolicyRule",
    "PolicyScope",
    "RiskOverrideRequest",
    "RiskPolicy",
    "validate_policy_scope",
]


class OverrideValidationResult(TypedDict):
    """Result of running override validation checks."""

    valid: bool
    message: str
    code: str
    details: dict[str, Any]


class RiskOverrideRequest(RiskContract):
    """Governed request to override config parameters with signed token."""

    request_id: str = Field(..., description="Associated request ID.")
    token: RiskApprovalToken = Field(
        ..., description="Governed override approval token."
    )
    target_overrides: dict[str, Any] = Field(
        ..., description="Requested parameter overrides."
    )


class RiskPolicy(RiskContract):
    """Immutable policy record with thresholds and authority.

    Tracks expiry, scope, and policy signature hash material.
    """

    policy_id: str = Field(..., description="Unique policy identifier.")
    profile_name: str = Field(
        ..., description="Target risk configuration profile name."
    )
    rules: list[PolicyRule] = Field(
        default_factory=list, description="Associated policy override rules."
    )
    authority: str | None = Field(
        default=None, description="The governance authority releasing this policy."
    )
    expiry_time: datetime | None = Field(
        default=None, description="Expiry timestamp of this policy."
    )
    scope: PolicyScope | None = Field(
        default=None, description="Optional scope criteria for policy itself."
    )
    policy_hash: str | None = Field(
        default=None, description="Optional stable signature hash of the policy."
    )


class EffectiveRiskPolicy(RiskContract):
    """Resolved policy applied to a request with provenance and precedence evidence."""

    policy_id: str = Field(..., description="Unique resolved policy identifier.")
    resolved_config: RiskConfig = Field(
        ..., description="Merged configuration after applying rule overrides."
    )
    policy_hash: str = Field(
        ..., description="Calculated signature hash of applied rules."
    )
    applied_rules: list[PolicyRule] = Field(
        default_factory=list,
        description="Rules matching the context in order of precedence.",
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata traces on how resolution occurred.",
    )


class PolicyPrecedenceRule(RiskContract):
    """Explicit global/account/strategy/symbol/workflow ordering record."""

    scope_type: str = Field(
        ...,
        description="Scope filter type (e.g. 'global', 'symbol', 'strategy').",
    )
    priority: int = Field(
        ...,
        description="Specificity priority score (higher score overrides lower).",
    )


def validate_policy_scope(scope: PolicyScope) -> ValidationResult:
    """Validates policy scope selectors, rejecting empty/malformed values.

    Args:
        scope: The PolicyScope contract to validate.

    Returns:
        ValidationResult: The validation result outcome.
    """
    logger.info("Validating policy scope selectors.")

    # 1. Scope must have at least one filter criterion defined
    fields = [
        scope.environment,
        scope.mode,
        scope.account_id,
        scope.strategy_id,
        scope.symbol,
        scope.currency,
        scope.workflow_id,
        scope.operator_role,
    ]
    if all(f is None for f in fields):
        msg = "Malformed scope: at least one filter criterion must be defined."
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "EMPTY_SCOPE",
            "details": {},
        }

    # 2. Check for empty strings in provided values
    for field_name in [
        "environment",
        "account_id",
        "strategy_id",
        "symbol",
        "currency",
        "workflow_id",
        "operator_role",
    ]:
        val = getattr(scope, field_name)
        if val is not None and not str(val).strip():
            msg = f"Scope field '{field_name}' contains empty or whitespace-only value."
            logger.error(msg)
            return {
                "valid": False,
                "message": msg,
                "code": "MALFORMED_SCOPE_FIELD",
                "details": {"field": field_name},
            }

    logger.debug("Policy scope validation passed.")
    return {
        "valid": True,
        "message": "Policy scope is valid.",
        "code": "OK",
        "details": {},
    }
