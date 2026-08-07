"""Registered default account Risk policy builders and bootstrap operation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from app.services.risk.config.factories import create_risk_config
from app.services.risk.config.runtime import register_risk_policy
from app.services.risk.contracts.responses import (
    guard_risk_boundary,
    unwrap_risk_response,
)
from app.utils import get_logger

logger = get_logger(__name__)


def _base_values() -> dict[str, object]:
    """Return shared safe paper-profile configuration material.

    Returns:
        Fresh mutable configuration mapping.
    """
    return {
        "profile": "paper",
        "execution_route": "paper",
        "base_currency": "USD",
        "pending_order_exposure_policy": "include_full_remaining_exposure",
        "evidence_max_age_seconds": {"portfolio": 60, "market": 30},
        "clock_skew_tolerance_seconds": Decimal(0),
        "var_min_observations": 30,
        "var_lookback": 250,
        "regime_assessment_enabled": True,
        "approval_signing_key_ref": "credentials/risk-signing-key",
        "decision_ttl_seconds": Decimal(30),
        "kill_switch_activation_permissions": ("risk.kill.activate",),
        "kill_switch_clearance_permissions": ("risk.kill.clear",),
        "report_timeout_seconds": Decimal(5),
    }


def build_personal_account_risk_config() -> object:
    """Build the registered personal-account default Risk policy.

    Returns:
        Validated immutable Risk configuration.
    """
    return create_risk_config(
        **_base_values(),
        policy_version="personal-account-default-v1",
        max_risk_per_trade_pct=Decimal("0.01"),
        preferred_risk_per_trade_pct=Decimal("0.005"),
        max_daily_loss=Decimal("0.03"),
        max_daily_loss_pct=Decimal("0.03"),
        max_weekly_loss_pct=Decimal("0.06"),
        max_monthly_loss_pct=Decimal("0.10"),
        max_drawdown=Decimal("0.12"),
        max_portfolio_drawdown_pct=Decimal("0.12"),
        max_strategy_drawdown_pct=Decimal("0.08"),
        max_symbol_drawdown_pct=Decimal("0.08"),
        max_symbol_exposure_pct=Decimal("0.20"),
        max_currency_cluster_exposure_pct=Decimal("0.35"),
        max_correlated_exposure_pct=Decimal("0.35"),
        max_total_exposure_pct=Decimal("1.50"),
        max_gross_exposure_pct=Decimal("2.00"),
        max_net_exposure_pct=Decimal("1.00"),
        max_effective_leverage=Decimal("5.0"),
        max_leverage=Decimal("5.0"),
        max_margin_utilization=Decimal("0.50"),
        max_total_margin_usage_pct=Decimal("0.50"),
        min_free_margin_pct=Decimal("0.30"),
        min_margin_level_pct=Decimal("200.0"),
        max_open_positions=10,
        max_pending_orders=10,
        max_live_strategies=3,
        max_trades_per_day=20,
        max_trades_per_strategy_per_day=5,
        max_consecutive_losses=5,
        max_spread_pips_default=Decimal("2.0"),
        max_slippage_pips_default=Decimal("1.0"),
        max_commission_burden_pct=Decimal("0.20"),
        max_swap_burden_pct=Decimal("0.10"),
        approval_token_ttl_seconds=Decimal(900),
        kill_switch_daily_loss_pct=Decimal("0.04"),
        kill_switch_portfolio_drawdown_pct=Decimal("0.18"),
    )


def build_prop_firm_risk_config() -> object:
    """Build the registered generic prop-firm default Risk policy.

    Returns:
        Validated immutable Risk configuration.
    """
    return create_risk_config(
        **_base_values(),
        policy_version="prop-firm-default-v1",
        max_risk_per_trade_pct=Decimal("0.005"),
        preferred_risk_per_trade_pct=Decimal("0.0025"),
        max_daily_loss=Decimal("0.02"),
        max_daily_loss_pct=Decimal("0.02"),
        max_weekly_loss_pct=Decimal("0.04"),
        max_monthly_loss_pct=Decimal("0.06"),
        max_drawdown=Decimal("0.08"),
        max_portfolio_drawdown_pct=Decimal("0.08"),
        max_strategy_drawdown_pct=Decimal("0.05"),
        max_symbol_drawdown_pct=Decimal("0.05"),
        max_symbol_exposure_pct=Decimal("0.10"),
        max_currency_cluster_exposure_pct=Decimal("0.20"),
        max_correlated_exposure_pct=Decimal("0.20"),
        max_total_exposure_pct=Decimal("1.00"),
        max_gross_exposure_pct=Decimal("1.25"),
        max_net_exposure_pct=Decimal("0.75"),
        max_effective_leverage=Decimal("3.0"),
        max_leverage=Decimal("3.0"),
        max_margin_utilization=Decimal("0.35"),
        max_total_margin_usage_pct=Decimal("0.35"),
        min_free_margin_pct=Decimal("0.50"),
        min_margin_level_pct=Decimal("300.0"),
        max_open_positions=5,
        max_pending_orders=5,
        max_live_strategies=2,
        max_trades_per_day=10,
        max_trades_per_strategy_per_day=3,
        max_consecutive_losses=3,
        max_spread_pips_default=Decimal("1.5"),
        max_slippage_pips_default=Decimal("0.5"),
        max_commission_burden_pct=Decimal("0.15"),
        max_swap_burden_pct=Decimal("0.05"),
        approval_token_ttl_seconds=Decimal(300),
        kill_switch_daily_loss_pct=Decimal("0.025"),
        kill_switch_portfolio_drawdown_pct=Decimal("0.10"),
    )


@guard_risk_boundary(risk_level="medium", read_only=False, modifies_database=True)
def register_default_risk_policies(
    *, effective_at: datetime, request_id: str, correlation_id: str
) -> Mapping[str, str]:
    """Register both immutable default policies idempotently.

    Args:
        effective_at: Aware UTC activation timestamp for both versions.
        request_id: Canonical request identifier.
        correlation_id: Canonical correlation identifier.

    Returns:
        Policy names mapped to their canonical configuration hashes.
    """
    logger.info("Registering the two default Risk policy profiles")
    hashes: dict[str, str] = {}
    for name, config in (
        ("personal_account", build_personal_account_risk_config()),
        ("prop_firm", build_prop_firm_risk_config()),
    ):
        response = register_risk_policy(
            config,
            effective_at=effective_at,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        hashes[name] = unwrap_risk_response(response, operation="register_risk_policy")
    return hashes


__all__ = [
    "build_personal_account_risk_config",
    "build_prop_firm_risk_config",
    "register_default_risk_policies",
]
