"""Policy-as-code resolution and governance API.

Exposes contracts, resolver engine, and override validation guards.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field

from app.services.risk.config import load_risk_config, validate_risk_config
from app.services.risk.models import (
    PolicyEnforcementResult,
    PolicyRule,
    PolicyScope,
    RiskApprovalToken,
    RiskConfig,
    RiskContract,
)
from app.services.risk.policy.contracts import (
    EffectiveRiskPolicy,
    OverrideValidationResult,
    PolicyPrecedenceRule,
    RiskOverrideRequest,
    RiskPolicy,
    validate_policy_scope,
)
from app.services.risk.policy.overrides import (
    requires_override_approval,
    validate_risk_override_request,
    validate_token_config_compatibility,
)
from app.services.risk.policy.resolver import (
    RiskPolicyEngine,
    evaluate_risk_budget,
    resolve_effective_policy,
    resolve_policy,
    resolve_risk_policy,
    validate_policy_expiry,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger
from app.utils.normalization import utc_now


class PolicyVersion(RiskContract):
    """Metadata tracking policy schema and release versions."""

    version_id: str = Field(..., description="Unique version identifier.")
    author: str = Field(
        ..., description="Author or system entity releasing this version."
    )
    created_at: str = Field(
        default_factory=lambda: utc_now().isoformat(),
        description="Version creation timestamp.",
    )


class PolicyBundle(RiskContract):
    """Consolidated bundle of active risk policies and rules."""

    bundle_id: str = Field(..., description="Unique identifier for the bundle.")
    version: PolicyVersion = Field(..., description="Version details.")
    policies: list[RiskPolicy] = Field(
        default_factory=list, description="List of wrapped policies."
    )


class PolicyResolutionQuery(RiskContract):
    """Context query parameters for resolving a policy enforcement state."""

    environment: str = Field(
        ..., description="Target environment (e.g. production, staging, local)."
    )
    mode: str = Field(..., description="Execution mode (e.g. live_readonly, paper).")
    account_id: str | None = Field(default=None, description="Account scope.")
    strategy_id: str | None = Field(default=None, description="Strategy scope.")
    symbol: str | None = Field(default=None, description="Symbol scope.")
    currency: str | None = Field(default=None, description="Currency scope.")
    workflow_id: str | None = Field(default=None, description="Workflow scope.")
    operator_role: str | None = Field(default=None, description="Operator role scope.")


class PolicyOverrideRequest(RiskContract):
    """Governed request to override config parameters with signed token."""

    request_id: str = Field(..., description="Associated request ID.")
    token: RiskApprovalToken = Field(
        ..., description="Governed override approval token."
    )
    target_overrides: dict[str, Any] = Field(
        ..., description="Requested parameter overrides."
    )


def load_risk_policy(profile_name: str) -> RiskConfig:
    """Load and parse a risk policy configuration by profile name.

    Args:
        profile_name: Name of the YAML config file without extension.

    Returns:
        RiskConfig: The loaded configuration profile.
    """
    logger.info("Loading risk policy configuration via profile: %s", profile_name)
    return load_risk_config(profile_name)


def validate_risk_policy(config: RiskConfig) -> None:
    """Validate a loaded risk policy configuration against hard ceilings.

    Args:
        config: The RiskConfig instance to validate.

    Raises:
        ValidationError: If validation fails or ceilings are breached.
    """
    logger.info("Validating risk policy profile configuration.")
    if not isinstance(config, RiskConfig):
        raise ValidationError("Invalid RiskConfig object.")
    res = validate_risk_config(config)
    if not res["valid"]:
        raise ValidationError(res["message"])


def validate_override_token(
    token: RiskApprovalToken,
    expected_scope: dict[str, Any],
    active_config_hash: str,
) -> bool:
    """Validate a RiskApprovalToken override against current limits and scopes.

    Backwards compatibility wrapper.

    Args:
        token: Signed approval token.
        expected_scope: Scope criteria to verify.
        active_config_hash: Hash of current active configuration.

    Returns:
        bool: True if validation succeeds.
    """
    logger.info("Validating override token %s", token.token_id)
    now = utc_now()

    # 1. Check token expiry
    if token.expiry_time is not None and now > token.expiry_time:
        logger.warning("Override token '%s' is expired.", token.token_id)
        return False

    # 2. Check compatibility
    compat_res = validate_token_config_compatibility(token, active_config_hash)
    if not compat_res["valid"]:
        return False

    # 3. Check scope alignment
    for key, expected_val in expected_scope.items():
        token_val = token.scope.get(key)
        if token_val is None or str(token_val).lower() != str(expected_val).lower():
            logger.warning(
                "Override token '%s' scope mismatch for key '%s' "
                "(expected: %s, got: %s).",
                token.token_id,
                key,
                expected_val,
                token_val,
            )
            return False

    # 4. Check role authority for staging/production
    if token.scope.get("environment") in {
        "staging",
        "production",
    } and token.approver not in {
        "risk_manager",
        "admin",
        "compliance_officer",
    }:
        logger.warning(
            "Override token '%s' rejected: approver '%s' has insufficient authority.",
            token.token_id,
            token.approver,
        )
        return False

    return True


def validate_risk_budget_gates(
    strategy_id: str,
    requested_budget: Decimal,
    resolved_config: RiskConfig,
) -> bool:
    """Verify that strategy's requested allocation fits within limits.

    Backwards compatibility wrapper.

    Args:
        strategy_id: ID of the strategy.
        requested_budget: Target allocation budget.
        resolved_config: Resolved configuration.

    Returns:
        bool: True if passes budget gates.
    """
    logger.info("Validating budget gates for strategy=%s", strategy_id)
    if not strategy_id.strip():
        return False

    if requested_budget <= 0:
        return False

    max_trade_risk = resolved_config.max_risk_per_trade
    if max_trade_risk <= 0:
        return False

    return (
        resolved_config.max_total_loss_pct_advisory
        <= resolved_config.max_total_loss_pct
    )


def check_policy_permission(role: str, action: str, env: str) -> bool:
    """Check if the operator role has permission to execute the action in env.

    Args:
        role: The role name.
        action: The target action to verify.
        env: The execution environment name.

    Returns:
        bool: True if authorized.
    """
    logger.info(
        "Checking permissions for role=%s, action=%s, env=%s", role, action, env
    )
    env_lower = env.lower()
    role_lower = role.lower()

    if env_lower in {"staging", "production"}:
        allowed_roles = {"admin", "compliance_officer", "risk_manager"}
        if role_lower not in allowed_roles:
            return False
        return not (
            action == "force_resume"
            and role_lower not in {"admin", "compliance_officer"}
        )

    return role_lower in {
        "admin",
        "compliance_officer",
        "risk_manager",
        "developer",
        "operator",
    }


__all__ = [
    "EffectiveRiskPolicy",
    "OverrideValidationResult",
    "PolicyBundle",
    "PolicyEnforcementResult",
    "PolicyOverrideRequest",
    "PolicyPrecedenceRule",
    "PolicyResolutionQuery",
    "PolicyRule",
    "PolicyScope",
    "PolicyVersion",
    "RiskOverrideRequest",
    "RiskPolicy",
    "RiskPolicyEngine",
    "check_policy_permission",
    "evaluate_risk_budget",
    "load_risk_policy",
    "requires_override_approval",
    "resolve_effective_policy",
    "resolve_policy",
    "resolve_risk_policy",
    "validate_override_token",
    "validate_policy_expiry",
    "validate_policy_scope",
    "validate_risk_budget_gates",
    "validate_risk_override_request",
    "validate_risk_policy",
    "validate_token_config_compatibility",
]
