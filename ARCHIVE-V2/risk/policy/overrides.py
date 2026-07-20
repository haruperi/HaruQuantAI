"""Governed policy override validation logic.

Verifies that requested limit overrides comply with scope, authority, expiry,
and hard safety ceilings.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from app.services.risk.config.schema import (
    MAX_DAILY_LOSS_PCT,
    MAX_EFFECTIVE_LEVERAGE,
    MAX_MARGIN_UTILIZATION_PCT,
    MAX_RISK_PER_TRADE,
    MAX_STRESS_LOSS_PCT,
    MAX_TOTAL_LOSS_PCT,
)
from app.utils.logger import logger
from app.utils.normalization import utc_now

if TYPE_CHECKING:
    from app.services.risk.models import (
        RiskApprovalToken,
        RiskDecisionToken,
    )
    from app.services.risk.policy.contracts import (
        EffectiveRiskPolicy,
        OverrideValidationResult,
        RiskOverrideRequest,
    )
    from app.services.risk.validations import ValidationResult


def validate_token_config_compatibility(
    token: RiskDecisionToken | RiskApprovalToken,
    config_hash: str,
) -> ValidationResult:
    """Validates configuration compatibility for approval/decision tokens.

    Args:
        token: Cryptographically signed token.
        config_hash: The current configuration hash to verify.

    Returns:
        ValidationResult: The validation result outcome.
    """
    logger.info("Validating token configuration compatibility.")
    # Check config compatibility
    if token.config_hash != config_hash:
        # Check if explicitly allowed via compatible_config_hashes in scope
        compatible_hashes = token.scope.get("compatible_config_hashes", [])
        if isinstance(compatible_hashes, list) and config_hash in compatible_hashes:
            logger.info(
                "Token '%s' config mismatch explicitly allowed "
                "by governed compatibility (active: %s).",
                token.token_id,
                config_hash,
            )
        else:
            msg = (
                f"Token '{token.token_id}' has mismatched config hash "
                f"(token: {token.config_hash}, active: {config_hash})."
            )
            logger.warning(msg)
            return {
                "valid": False,
                "message": msg,
                "code": "CONFIG_HASH_MISMATCH",
                "details": {
                    "token_config_hash": token.config_hash,
                    "active_config_hash": config_hash,
                },
            }

    logger.debug("Token configuration compatibility validation passed.")
    return {
        "valid": True,
        "message": "Token configuration is compatible.",
        "code": "OK",
        "details": {},
    }


def requires_override_approval(
    request: RiskOverrideRequest,
    policy: EffectiveRiskPolicy,
) -> bool:
    """Determines whether override approval is mandatory.

    Args:
        request: The override request.
        policy: The active resolved effective policy.

    Returns:
        bool: True if approval is required, False otherwise.
    """
    logger.info("Determining if override request requires approval.")

    # 1. Stricter defaults: staging/production environments always
    # require approval for overrides.
    policy_scope = policy.provenance.get("policy_scope") or {}
    env = policy_scope.get("environment", "local").lower()
    if env in {"staging", "production"}:
        logger.info(
            "Override request is in live-sensitive environment, requiring approval."
        )
        return True

    # 2. Check if any matching applied rules require approval
    for rule in policy.applied_rules:
        if rule.requires_approval:
            logger.info(
                "Applied policy rule '%s' explicitly requires approval.",
                rule.rule_id,
            )
            return True

    # 3. If override exceeds max limit (i.e. high-risk parameters relaxation)
    for param_name, val in request.target_overrides.items():
        base_val = getattr(policy.resolved_config, param_name, None)
        if base_val is not None:
            try:
                # If overriding to a looser value, require approval
                if Decimal(str(val)) > Decimal(str(base_val)):
                    logger.info(
                        "Overriding parameter '%s' to looser value requires approval.",
                        param_name,
                    )
                    return True
            except (ValueError, TypeError):
                pass

    logger.debug("Override request does not require approval.")
    return False


def validate_risk_override_request(
    request: RiskOverrideRequest,
    policy: EffectiveRiskPolicy,
) -> OverrideValidationResult:
    """Validates override scope and maximum threshold bounds against active policy.

    Args:
        request: The override request payload.
        policy: The active resolved effective policy.

    Returns:
        OverrideValidationResult: Dict carrying validation status, code, and details.
    """
    logger.info(
        "Validating override request strategy_id=%s, request_id=%s",
        policy.provenance.get("policy_scope", {}).get("strategy_id"),
        request.request_id,
    )

    # 1. Validate token config compatibility
    compat_res = validate_token_config_compatibility(
        request.token,
        policy.resolved_config.content_hash(),
    )
    if not compat_res["valid"]:
        logger.warning("Token config hash mismatch during override validation.")
        return {
            "valid": False,
            "message": compat_res["message"],
            "code": compat_res["code"],
            "details": compat_res["details"],
        }

    # 2. Check token expiry
    now = utc_now()
    if request.token.expiry_time is not None and now > request.token.expiry_time:
        msg = f"Override token '{request.token.token_id}' is expired."
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "TOKEN_EXPIRED",
            "details": {"expiry_time": request.token.expiry_time.isoformat()},
        }

    # 3. Check token scope restrictions against resolution context scope
    policy_scope = policy.provenance.get("policy_scope") or {}
    for key, val in request.token.scope.items():
        if key == "compatible_config_hashes":
            continue
        ctx_val = policy_scope.get(key)
        if ctx_val is None or str(val).lower() != str(ctx_val).lower():
            msg = (
                f"Override token scope mismatch for key '{key}' "
                f"(expected: {ctx_val}, token has: {val})."
            )
            logger.warning(msg)
            return {
                "valid": False,
                "message": msg,
                "code": "SCOPE_MISMATCH",
                "details": {
                    "field": key,
                    "token_val": val,
                    "expected_val": ctx_val,
                },
            }

    # 4. Check role authority for live-sensitive environments
    env = policy_scope.get("environment", "local").lower()
    is_live_sensitive = env in {"staging", "production"} or policy_scope.get(
        "mode"
    ) in {
        "micro_live",
        "full_live",
    }
    if is_live_sensitive and request.token.approver not in {
        "risk_manager",
        "admin",
        "compliance_officer",
    }:
        msg = (
            f"Override token '{request.token.token_id}' rejected: "
            f"approver '{request.token.approver}' has insufficient authority "
            f"for live overrides."
        )
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "INSUFFICIENT_AUTHORITY",
            "details": {"approver": request.token.approver},
        }

    # 5. Check hard safety ceilings limits for overrides
    ceilings = {
        "max_daily_loss_pct": MAX_DAILY_LOSS_PCT,
        "max_total_loss_pct": MAX_TOTAL_LOSS_PCT,
        "max_margin_utilization_pct": MAX_MARGIN_UTILIZATION_PCT,
        "max_effective_leverage": MAX_EFFECTIVE_LEVERAGE,
        "max_risk_per_trade": MAX_RISK_PER_TRADE,
        "max_stress_loss_pct": MAX_STRESS_LOSS_PCT,
    }

    for param_name, override_val in request.target_overrides.items():
        ceiling = ceilings.get(param_name)
        if ceiling is not None:
            try:
                dec_val = Decimal(str(override_val))
                if dec_val > ceiling:
                    msg = (
                        f"Requested override '{param_name}'={dec_val} "
                        f"exceeds hard safety ceiling of {ceiling}."
                    )
                    logger.warning(msg)
                    return {
                        "valid": False,
                        "message": msg,
                        "code": "CEILING_BREACH",
                        "details": {
                            "parameter": param_name,
                            "value": dec_val,
                            "ceiling": ceiling,
                        },
                    }
            except (ValueError, TypeError, InvalidOperation) as e:
                msg = f"Invalid numeric override format for '{param_name}': {e}"
                logger.error(msg)
                return {
                    "valid": False,
                    "message": msg,
                    "code": "INVALID_NUMERIC_FORMAT",
                    "details": {"parameter": param_name, "error": str(e)},
                }

    logger.info("Override request successfully validated.")
    return {
        "valid": True,
        "message": "Override request matches all limits and requirements.",
        "code": "OK",
        "details": {},
    }
