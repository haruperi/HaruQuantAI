"""Secret-free authoritative Risk development policy manifest."""

from decimal import Decimal

from app.services.risk.config.factories import create_risk_config


def build_development_risk_config() -> object:
    """Build the fail-closed research-profile Risk policy.

    Returns:
        Validated immutable Risk configuration with only a key reference.
    """
    return create_risk_config(
        profile="research",
        execution_route="none",
        policy_version="risk-development-v1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=30,
        var_lookback=250,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="credentials/risk-signing-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


__all__ = ("build_development_risk_config",)
