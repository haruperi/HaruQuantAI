"""Strict config schema and validation rules for Risk Governance.

Enforces hard ceilings, live profile authorization checks, prop firm limits,
and owner/admin approvals. Returns TypedDict ValidationResult.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.risk.models import RiskConfig
    from app.services.risk.validations import ValidationResult

# Hard ceiling constraints
MAX_DAILY_LOSS_PCT = Decimal("0.20")
MAX_TOTAL_LOSS_PCT = Decimal("0.50")
MAX_MARGIN_UTILIZATION_PCT = Decimal("1.00")
MAX_EFFECTIVE_LEVERAGE = Decimal("500.0")
MAX_RISK_PER_TRADE = Decimal("0.10")
MAX_STRESS_LOSS_PCT = Decimal("0.30")

# Conservative baseline defaults for live validation comparison
CONSERVATIVE_DEFAULTS = {
    "max_risk_per_trade": Decimal("0.002"),
    "max_daily_loss_pct": Decimal("0.02"),
    "max_total_loss_pct": Decimal("0.05"),
    "max_margin_utilization_pct": Decimal("0.50"),
    "max_effective_leverage": Decimal("5.0"),
    "max_stress_loss_pct": Decimal("0.08"),
}


def validate_risk_config(config: RiskConfig) -> ValidationResult:
    """Validate a loaded RiskConfig object against strict ceilings.

    Also verifies authorization rules, live operator approvals, prop-firm
    ceilings, and owner/admin approval for increased thresholds.

    Args:
        config: The RiskConfig instance to validate.

    Returns:
        ValidationResult: The TypedDict containing validation status, message,
            code, and details.
    """
    logger.info(f"Validating configuration profile: {config.profile_name}")
    raw_dict = config.model_dump()

    # 1. Validate hard ceilings
    ceiling_res = _validate_ceilings(raw_dict)
    if ceiling_res is not None:
        return ceiling_res

    # 2. Check for unknown/experimental keys
    if config.model_extra:
        for key, val in config.model_extra.items():
            if key.startswith("experimental_") and val is False:
                continue
            msg = f"Unknown configuration keys found in '{config.profile_name}': {key}"
            logger.error(msg)
            return {
                "valid": False,
                "message": msg,
                "code": "VALIDATION_FAILED",
                "details": {"unknown_key": key},
            }

    # 3. Live profile checks
    live_res = _validate_live_checks(config, raw_dict)
    if live_res is not None:
        return live_res

    logger.info(f"Validation successful for profile: {config.profile_name}")
    return {
        "valid": True,
        "message": "Validation passed.",
        "code": "OK",
        "details": {},
    }


def _validate_ceilings(raw_dict: dict[str, Any]) -> ValidationResult | None:
    """Validate values against hard-coded global ceilings."""
    ceilings = [
        ("max_daily_loss_pct", MAX_DAILY_LOSS_PCT),
        ("max_total_loss_pct", MAX_TOTAL_LOSS_PCT),
        ("max_margin_utilization_pct", MAX_MARGIN_UTILIZATION_PCT),
        ("max_effective_leverage", MAX_EFFECTIVE_LEVERAGE),
        ("max_risk_per_trade", MAX_RISK_PER_TRADE),
        ("max_stress_loss_pct", MAX_STRESS_LOSS_PCT),
    ]

    for key, ceiling in ceilings:
        val = raw_dict.get(key)
        if val is not None:
            try:
                dec_val = Decimal(str(val))
            except (ValueError, TypeError) as e:
                msg = f"Invalid decimal value for '{key}': {val}"
                logger.error(msg)
                return {
                    "valid": False,
                    "message": msg,
                    "code": "INVALID_INPUT",
                    "details": {"key": key, "value": val, "error": str(e)},
                }
            if dec_val > ceiling:
                msg = (
                    f"Unsafe config: '{key}' value {dec_val} "
                    f"exceeds hard ceiling of {ceiling}"
                )
                logger.error(msg)
                return {
                    "valid": False,
                    "message": msg,
                    "code": "VALIDATION_FAILED",
                    "details": {"key": key, "value": dec_val, "ceiling": ceiling},
                }
    return None


def _validate_live_checks(
    config: RiskConfig, raw_dict: dict[str, Any]
) -> ValidationResult | None:
    """Run authorization and guardrail checks for live execution profiles."""
    allow_live = raw_dict.get("allow_live_execution", False)
    profile_name_lower = config.profile_name.lower()
    if "live" in profile_name_lower and not allow_live:
        msg = (
            f"Live configuration profile '{config.profile_name}' must explicitly "
            "set allow_live_execution to true."
        )
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "PERMISSION_DENIED",
            "details": {"profile_name": config.profile_name},
        }

    if allow_live:
        operator_approval = raw_dict.get("operator_approval_fields")
        if not operator_approval:
            msg = (
                f"Live configuration profile '{config.profile_name}' requires "
                "explicit operator approval fields to authorize live mode."
            )
            logger.error(msg)
            return {
                "valid": False,
                "message": msg,
                "code": "APPROVAL_REQUIRED",
                "details": {"profile_name": config.profile_name},
            }

        op_res = _validate_operator_signatures(config, operator_approval)
        if op_res is not None:
            return op_res

        drawdown_res = _validate_prop_firm_drawdowns(config, raw_dict)
        if drawdown_res is not None:
            return drawdown_res

        role_res = _validate_increased_risk_approvals(
            config, raw_dict, operator_approval
        )
        if role_res is not None:
            return role_res

    return None


def _validate_operator_signatures(
    config: RiskConfig, operator_approval: dict[str, Any] | None
) -> ValidationResult | None:
    """Verify required keys in operator approval."""
    required_approval_keys = {"operator_id", "approved_at", "approval_token"}
    if not isinstance(operator_approval, dict) or not required_approval_keys.issubset(
        operator_approval.keys()
    ):
        msg = (
            f"Live configuration profile '{config.profile_name}' operator "
            f"approval fields must contain keys: {required_approval_keys}"
        )
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "VALIDATION_FAILED",
            "details": {
                "missing_keys": list(
                    required_approval_keys
                    - set(
                        operator_approval.keys()
                        if isinstance(operator_approval, dict)
                        else []
                    )
                )
            },
        }
    return None


def _validate_prop_firm_drawdowns(
    config: RiskConfig, raw_dict: dict[str, Any]
) -> ValidationResult | None:
    """Validate prop-firm drawdown ceilings."""
    daily_limit = Decimal("0.04")
    total_limit = Decimal("0.08")
    daily_val = Decimal(str(raw_dict.get("max_daily_loss_pct", 0.0)))
    total_val = Decimal(str(raw_dict.get("max_total_loss_pct", 0.0)))

    if daily_val > daily_limit:
        msg = (
            f"Live configuration '{config.profile_name}' daily loss limit "
            f"{daily_val} exceeds external prop-firm ceiling of {daily_limit}."
        )
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "VALIDATION_FAILED",
            "details": {
                "max_daily_loss_pct": daily_val,
                "prop_firm_limit": daily_limit,
            },
        }

    if total_val > total_limit:
        msg = (
            f"Live configuration '{config.profile_name}' total loss limit "
            f"{total_val} exceeds external prop-firm ceiling of {total_limit}."
        )
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "VALIDATION_FAILED",
            "details": {
                "max_total_loss_pct": total_val,
                "prop_firm_limit": total_limit,
            },
        }
    return None


def _validate_increased_risk_approvals(
    config: RiskConfig, raw_dict: dict[str, Any], operator_approval: dict[str, Any]
) -> ValidationResult | None:
    """Verify owner/admin approval for increased risk thresholds."""
    increased_keys = []
    for key, default_val in CONSERVATIVE_DEFAULTS.items():
        val = raw_dict.get(key)
        if val is not None and Decimal(str(val)) > default_val:
            increased_keys.append(key)

    if increased_keys:
        operator_id = operator_approval.get("operator_id", "")
        if operator_id not in {"owner", "admin"}:
            msg = (
                f"Increasing risk thresholds {increased_keys} above conservative "
                f"defaults in live profile '{config.profile_name}' requires explicit "
                f"owner/admin approval. Current operator: '{operator_id}'."
            )
            logger.error(msg)
            return {
                "valid": False,
                "message": msg,
                "code": "PERMISSION_DENIED",
                "details": {
                    "increased_keys": increased_keys,
                    "operator_id": operator_id,
                },
            }
    return None
