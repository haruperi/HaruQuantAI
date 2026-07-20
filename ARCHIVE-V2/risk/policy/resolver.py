"""Policy-as-code resolution and budget validation engine.

Responsible for matching scoped policy rules, resolving precedence,
and enforcing budget checks.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.services.risk.config import load_risk_config
from app.services.risk.config.schema import (
    MAX_DAILY_LOSS_PCT,
    MAX_EFFECTIVE_LEVERAGE,
    MAX_MARGIN_UTILIZATION_PCT,
    MAX_RISK_PER_TRADE,
    MAX_TOTAL_LOSS_PCT,
)
from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.models import (
    PolicyEnforcementResult,
    RiskConfig,
    RiskDecisionStatus,
)
from app.services.risk.policy.contracts import EffectiveRiskPolicy
from app.utils.logger import logger
from app.utils.normalization import utc_now

if TYPE_CHECKING:
    from app.services.risk.models import (
        PolicyRule,
        PolicyScope,
        RiskAssessmentRequest,
    )
    from app.services.risk.policy import PolicyBundle, PolicyResolutionQuery
    from app.services.risk.policy.contracts import RiskPolicy
    from app.services.risk.validations import ValidationResult

EVALUATED_SCOPE_FIELDS = [
    "environment",
    "mode",
    "account_id",
    "strategy_id",
    "symbol",
    "currency",
    "workflow_id",
    "operator_role",
]


def get_rule_specificity_score(scope: PolicyScope) -> int:
    """Calculate specificity score for policy rules sorting.

    More specific filters get higher scores.

    Args:
        scope: The PolicyScope to evaluate specificity for.

    Returns:
        int: Specificity score.
    """
    logger.debug("Calculating specificity score for policy scope.")
    score = 0
    if scope.workflow_id is not None:
        score += 10000
    if scope.symbol is not None:
        score += 1000
    if scope.strategy_id is not None:
        score += 100
    if scope.account_id is not None:
        score += 10
    if scope.currency is not None:
        score += 5
    if scope.operator_role is not None:
        score += 2
    if scope.mode is not None:
        score += 1
    if scope.environment is not None:
        score += 1
    return score


def _filter_matching_rules(
    rules: list[PolicyRule],
    context: dict[str, Any],
    now: datetime,
) -> list[PolicyRule]:
    """Filter candidate policy rules against context and expiration time.

    Args:
        rules: The list of candidate PolicyRules.
        context: Context dictionary representing current evaluation state.
        now: The current datetime.

    Returns:
        list[PolicyRule]: List of matched policy rules.
    """
    logger.debug("Filtering policy rules against context.")
    matched_rules: list[PolicyRule] = []
    for rule in rules:
        if rule.expiry_time is not None and now > rule.expiry_time:
            logger.debug("Ignoring expired policy rule '%s'", rule.rule_id)
            continue

        scope = rule.scope
        match = True

        for field_name in EVALUATED_SCOPE_FIELDS:
            scope_val = getattr(scope, field_name, None)
            if scope_val is not None:
                ctx_val = context.get(field_name)
                if ctx_val is None or str(scope_val).lower() != str(ctx_val).lower():
                    match = False
                    break

        if match:
            matched_rules.append(rule)

    logger.info("Found %d matching policy rules.", len(matched_rules))
    return matched_rules


def _apply_overrides(
    base_config: RiskConfig,
    matched_rules: list[PolicyRule],
) -> dict[str, Any]:
    """Apply rule overrides to config dict based on precedence rules.

    Args:
        base_config: The default loaded RiskConfig profile.
        matched_rules: Sorted/filtered matching PolicyRules.

    Returns:
        dict[str, Any]: Merged configuration dictionary.
    """
    logger.debug("Applying rule overrides based on specificity precedence.")
    # Precedence Rules sorting (lowest specificity first so highest overrides last)
    matched_rules.sort(key=lambda r: get_rule_specificity_score(r.scope))

    # Map flat keys to their nested path in config_dict
    nested_map = {
        "max_risk_per_trade": ("risk", "max_risk_per_trade"),
        "max_margin_utilization_pct": ("risk", "max_margin_usage"),
        "max_daily_loss_pct": ("drawdown", "daily_loss_hard_limit"),
        "max_total_loss_pct": ("drawdown", "total_drawdown_hard_limit"),
        "correlation_threshold": ("correlation", "reject_threshold"),
        "var_confidence": ("tail_risk", "var_confidence"),
        "es_confidence": ("tail_risk", "es_confidence"),
        "max_stress_loss_pct": ("tail_risk", "stress_loss_limit"),
        "m1_spread_to_sigma_ratio_filter": ("execution", "max_spread_to_sigma"),
    }

    config_dict = base_config.model_dump()
    for rule in matched_rules:
        for key, val in rule.overrides.items():
            if key in config_dict:
                orig_val = config_dict[key]
                if isinstance(orig_val, Decimal):
                    config_dict[key] = Decimal(str(val))
                elif isinstance(orig_val, int):
                    config_dict[key] = int(val)
                elif isinstance(orig_val, float):
                    config_dict[key] = float(val)
                elif isinstance(orig_val, bool):
                    config_dict[key] = bool(val)
                else:
                    config_dict[key] = val

                # Propagate flat field override to nested config dictionary if mapped
                if key in nested_map:
                    nested_name, nested_sub_name = nested_map[key]
                    if nested_name in config_dict and isinstance(
                        config_dict[nested_name], dict
                    ):
                        config_dict[nested_name][nested_sub_name] = config_dict[key]

    logger.info("Configuration overrides merged successfully.")
    return config_dict


def _check_resolved_ceilings(config_dict: dict[str, Any]) -> list[str]:
    """Verify resolved config values do not exceed hard safety ceilings.

    Args:
        config_dict: Resolved configuration dictionary.

    Returns:
        list[str]: List of validation breach messages.
    """
    logger.debug("Checking resolved configuration values against hard safety ceilings.")
    breaches = []
    try:
        if (
            Decimal(str(config_dict.get("max_daily_loss_pct", 0.0)))
            > MAX_DAILY_LOSS_PCT
        ):
            breaches.append(
                f"max_daily_loss_pct exceeds ceiling of {MAX_DAILY_LOSS_PCT}"
            )
        if (
            Decimal(str(config_dict.get("max_total_loss_pct", 0.0)))
            > MAX_TOTAL_LOSS_PCT
        ):
            breaches.append(
                f"max_total_loss_pct exceeds ceiling of {MAX_TOTAL_LOSS_PCT}"
            )
        if (
            Decimal(str(config_dict.get("max_margin_utilization_pct", 0.0)))
            > MAX_MARGIN_UTILIZATION_PCT
        ):
            breaches.append(
                f"max_margin_utilization_pct exceeds ceiling of "
                f"{MAX_MARGIN_UTILIZATION_PCT}"
            )
        if (
            Decimal(str(config_dict.get("max_effective_leverage", 0.0)))
            > MAX_EFFECTIVE_LEVERAGE
        ):
            breaches.append(
                f"max_effective_leverage exceeds ceiling of {MAX_EFFECTIVE_LEVERAGE}"
            )
        if (
            Decimal(str(config_dict.get("max_risk_per_trade", 0.0)))
            > MAX_RISK_PER_TRADE
        ):
            breaches.append(
                f"max_risk_per_trade exceeds ceiling of {MAX_RISK_PER_TRADE}"
            )
    except (ValueError, TypeError) as e:
        breaches.append(f"Ceiling check validation error: {e}")

    if breaches:
        logger.warning("Safety ceilings breached: %s", breaches)
    return breaches


def resolve_policy(
    base_config: RiskConfig,
    rules: list[PolicyRule],
    context: dict[str, Any],
) -> PolicyEnforcementResult:
    """Resolve the active RiskConfig by matching and merging policy rules.

    Legacy V1 compatibility wrapper.

    Args:
        base_config: The default loaded RiskConfig profile.
        rules: The list of candidate PolicyRules.
        context: Context dictionary representing current evaluation state.

    Returns:
        PolicyEnforcementResult: The result of policy resolution.
    """
    logger.info("Resolving policy with legacy resolve_policy helper.")
    now = utc_now()

    matched_rules = _filter_matching_rules(rules, context, now)
    config_dict = _apply_overrides(base_config, matched_rules)
    breaches = _check_resolved_ceilings(config_dict)

    # Compute stable policy hash
    applied_rules_ids = [rule.rule_id for rule in matched_rules]
    canonical_rules_str = ",".join(sorted(applied_rules_ids))
    policy_hash = hashlib.sha256(canonical_rules_str.encode("utf-8")).hexdigest()

    status = RiskDecisionStatus.APPROVE
    reason = "Policy resolved successfully"
    if breaches:
        status = RiskDecisionStatus.REJECT
        reason = f"Resolved config violates hard ceilings: {breaches}"

    # Stricter default policy for live-sensitive modes
    env = context.get("environment", "local").lower()
    is_live_sensitive = env in {"staging", "production"} or context.get("mode") in {
        "micro_live",
        "full_live",
    }
    if is_live_sensitive and not config_dict.get("allow_live_execution", False):
        status = RiskDecisionStatus.BLOCK
        reason = (
            "Execution blocked: environment/mode is live-sensitive but config "
            "disables allow_live_execution"
        )

    resolved_config = RiskConfig(**config_dict)

    return PolicyEnforcementResult(
        status=status,
        reason=reason,
        policy_hash=policy_hash,
        resolved_config=resolved_config,
        breaches=breaches,
        policy_version=context.get("policy_version") or "v1-default",
        policy_scope=context,
    )


def validate_policy_expiry(
    policy: RiskPolicy,
    now_utc: datetime,
) -> ValidationResult:
    """Validates time-bounded policies.

    Args:
        policy: The policy to validate.
        now_utc: The current UTC timestamp.

    Returns:
        ValidationResult: The validation result outcome.
    """
    logger.info("Validating expiry for policy_id=%s", policy.policy_id)
    if policy.expiry_time is not None and now_utc > policy.expiry_time:
        msg = (
            f"Policy '{policy.policy_id}' is expired (expiry: "
            f"{policy.expiry_time}, current: {now_utc})."
        )
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "POLICY_EXPIRED",
            "details": {"expiry_time": policy.expiry_time.isoformat()},
        }
    logger.debug("Policy is active.")
    return {
        "valid": True,
        "message": "Policy is active.",
        "code": "OK",
        "details": {},
    }


def resolve_effective_policy(
    context: dict[str, Any],
    policies: Sequence[RiskPolicy],
) -> EffectiveRiskPolicy:
    """Applies approved scope/precedence rules to resolve the effective policy.

    Args:
        context: Context variables representing the active transaction/query.
        policies: Sequence of candidate RiskPolicies to resolve against.

    Returns:
        EffectiveRiskPolicy: Resolved active policy record.

    Raises:
        ValidationError: If no matching policy is found (fail closed)
            or validation fails.
    """
    logger.info("Resolving effective policy from context.")
    now = utc_now()

    # 1. Filter policies whose scope matches the context and are not expired
    matched_policies: list[RiskPolicy] = []
    for policy in policies:
        # Check expiry
        expiry_res = validate_policy_expiry(policy, now)
        if not expiry_res["valid"]:
            continue

        # Check scope match
        scope_match = True
        if policy.scope is not None:
            for field_name in EVALUATED_SCOPE_FIELDS:
                scope_val = getattr(policy.scope, field_name, None)
                if scope_val is not None:
                    ctx_val = context.get(field_name)
                    if (
                        ctx_val is None
                        or str(scope_val).lower() != str(ctx_val).lower()
                    ):
                        scope_match = False
                        break

        if scope_match:
            matched_policies.append(policy)

    # 2. Fail closed if no policy matches context
    if not matched_policies:
        msg = "Fail closed: no active risk policy resolved for the current context."
        logger.error(msg)
        raise ValidationError(msg)

    # 3. Resolve the active policy. Sort by specificity score of policy scope.
    matched_policies.sort(
        key=lambda p: get_rule_specificity_score(p.scope) if p.scope else 0,
        reverse=True,
    )
    active_policy = matched_policies[0]
    logger.info(
        "Resolved active policy_id=%s (profile_name=%s)",
        active_policy.policy_id,
        active_policy.profile_name,
    )

    # 4. Load base risk config
    try:
        base_config = load_risk_config(active_policy.profile_name)
    except Exception as e:
        msg = (
            f"Failed to load risk configuration for profile "
            f"'{active_policy.profile_name}': {e}"
        )
        logger.error(msg)
        raise ValidationError(msg) from e

    # 5. Extract and apply matching rules from all active policies
    all_rules: list[PolicyRule] = []
    for p in matched_policies:
        all_rules.extend(p.rules)

    matched_rules = _filter_matching_rules(all_rules, context, now)
    config_dict = _apply_overrides(base_config, matched_rules)
    breaches = _check_resolved_ceilings(config_dict)

    if breaches:
        msg = f"Resolved configuration violates safety ceilings: {breaches}"
        logger.error(msg)
        raise ValidationError(msg)

    # Stricter default check for live execution
    env = context.get("environment", "local").lower()
    is_live_sensitive = env in {"staging", "production"} or context.get("mode") in {
        "micro_live",
        "full_live",
    }
    if is_live_sensitive and not config_dict.get("allow_live_execution", False):
        msg = (
            "Execution blocked: live execution is disabled "
            "in the resolved configuration."
        )
        logger.error(msg)
        raise ValidationError(msg)

    # Calculate stable rules hash signature
    applied_rules_ids = [rule.rule_id for rule in matched_rules]
    canonical_rules_str = ",".join(sorted(applied_rules_ids))
    policy_hash = hashlib.sha256(canonical_rules_str.encode("utf-8")).hexdigest()

    resolved_config = RiskConfig(**config_dict)

    # Set provenance context tracking
    provenance = {
        "policy_id": active_policy.policy_id,
        "policy_version": context.get("policy_version") or "v2-default",
        "policy_scope": context,
        "breaches": breaches,
    }

    return EffectiveRiskPolicy(
        policy_id=active_policy.policy_id,
        resolved_config=resolved_config,
        policy_hash=policy_hash,
        applied_rules=matched_rules,
        provenance=provenance,
    )


def evaluate_risk_budget(
    policy: EffectiveRiskPolicy,
    request: RiskAssessmentRequest,
) -> PolicyEnforcementResult:
    """Evaluates policy budget gates against a risk assessment request.

    Args:
        policy: The active resolved effective policy.
        request: The risk assessment request details.

    Returns:
        PolicyEnforcementResult: Pass/warn/fail result.
    """
    from app.services.risk.models import ProposedAllocation, ProposedTrade

    action = request.proposed_action
    strategy_id = ""
    if action is not None:
        if isinstance(action, ProposedAllocation):
            strategy_ids = list(action.allocations.keys())
            strategy_id = strategy_ids[0] if strategy_ids else ""
        else:
            strategy_id = getattr(action, "strategy_id", "") or ""

    logger.info(
        "Evaluating risk budget gates for strategy_id=%s",
        strategy_id,
    )

    breaches = []

    # 1. Strategy presence check
    if not strategy_id or not strategy_id.strip():
        breaches.append("Missing strategy_id in request.")

    # 2. Extract requested budget allocation
    budget = Decimal("0.0")
    if isinstance(action, ProposedAllocation):
        budget = action.allocations.get(strategy_id, Decimal("0.0"))
    elif isinstance(action, ProposedTrade):
        budget = (
            getattr(action, "risk", None)
            or getattr(action, "volume", None)
            or Decimal("0.0")
        )

    if budget <= 0:
        breaches.append(f"Invalid budget request value: {budget}")

    # 3. Check against maximum risk limit
    max_risk = policy.resolved_config.max_risk_per_trade
    if budget > max_risk:
        breaches.append(
            f"Requested budget {budget} exceeds maximum risk per trade {max_risk}."
        )

    # 4. Check advisory vs hard total loss limits
    if (
        policy.resolved_config.max_total_loss_pct_advisory
        > policy.resolved_config.max_total_loss_pct
    ):
        breaches.append("Advisory loss limit exceeds hard total drawdown limit.")

    status = RiskDecisionStatus.APPROVE
    reason = "Budget check passed successfully."
    if breaches:
        status = RiskDecisionStatus.REJECT
        reason = f"Budget checks failed: {breaches}"

    logger.info("Budget evaluation finished with status=%s", status.value)
    return PolicyEnforcementResult(
        status=status,
        reason=reason,
        policy_hash=policy.policy_hash,
        resolved_config=policy.resolved_config,
        breaches=breaches,
        policy_version=policy.provenance.get("policy_version"),
        policy_scope=policy.provenance.get("policy_scope"),
    )


class RiskPolicyEngine:
    """Core engine for matching and enforcing risk policies-as-code."""

    def __init__(self, bundle: PolicyBundle) -> None:
        """Initialize engine with a policy bundle.

        Args:
            bundle: The PolicyBundle containing policies.
        """
        logger.info("Initializing RiskPolicyEngine façade.")
        self.bundle = bundle

    def resolve(
        self,
        query: PolicyResolutionQuery,
        base_config: RiskConfig,
    ) -> PolicyEnforcementResult:
        """Resolve policy overrides against base config and matching rules.

        Legacy V1 façade compatibility wrapper.

        Args:
            query: The PolicyResolutionQuery context parameters.
            base_config: The default loaded RiskConfig profile.

        Returns:
            PolicyEnforcementResult: Resolved policy result.
        """
        logger.info("Resolving query via RiskPolicyEngine resolve façade.")
        context = query.model_dump()
        rules: list[PolicyRule] = []
        for policy in self.bundle.policies:
            rules.extend(policy.rules)
        res = resolve_policy(base_config, rules, context)
        res.policy_version = self.bundle.version.version_id
        res.policy_scope = context
        return res


def resolve_risk_policy(
    base_config: RiskConfig,
    rules: list[PolicyRule],
    context: dict[str, Any],
) -> PolicyEnforcementResult:
    """Resolve config by matching rules against context.

    Wrapper for resolve_policy.

    Args:
        base_config: The base risk configuration.
        rules: The override rules.
        context: Context parameters.

    Returns:
        PolicyEnforcementResult: Enforcement resolution result.
    """
    logger.info("Resolving risk policy via wrapper.")
    return resolve_policy(base_config, rules, context)
