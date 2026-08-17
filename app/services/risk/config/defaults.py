"""Registered default account Risk policy builders and bootstrap operation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

from app.services.risk.config.factories import create_risk_config
from app.services.risk.config.runtime import register_risk_policy
from app.services.risk.contracts.responses import (
    guard_risk_boundary,
    unwrap_risk_response,
)
from app.utils import get_logger

logger = get_logger(__name__)


def _base_values(
    profile: str = "demo",
    execution_route: str = "demo",
) -> dict[str, object]:
    """Return shared configuration material for one profile and route.

    The account's risk appetite does not change with the venue it trades on, so
    every profile reuses the same thresholds; only the profile/route pair the
    policy is scoped to differs.

    Args:
        profile: Risk profile the policy is scoped to.
        execution_route: Compatible execution route for that profile.

    Returns:
        Fresh mutable configuration mapping.
    """
    return {
        "profile": profile,
        "execution_route": execution_route,
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


def build_personal_account_risk_config(
    profile: str = "demo",
    execution_route: str = "demo",
) -> object:
    """Build the registered personal-account default Risk policy.

    Args:
        profile: Risk profile the policy is scoped to; defaults to the
            registered demo policy.
        execution_route: Compatible execution route for that profile.

    Returns:
        Validated immutable Risk configuration.

    Raises:
        ValueError: If the profile and route are incompatible, or the profile
            demands safety policy these defaults do not carry. The ``live``
            profile does: it additionally requires stressed regime policy and a
            complete emergency/audit/drawdown threshold set, which is owner
            policy rather than a default, so a live policy fails closed here
            until those values are registered.
    """
    live_values: dict[str, object] = {}
    if profile == "live":
        live_values = {
            "missing_calendar_mode": "block",
            "stressed_lookback_days": 252,
            "crisis_windows_utc": {
                "covid_market_shock": (
                    datetime(2020, 2, 20, tzinfo=UTC),
                    datetime(2020, 4, 7, 23, 59, 59, tzinfo=UTC),
                ),
                "ukraine_invasion_market_shock": (
                    datetime(2022, 2, 24, tzinfo=UTC),
                    datetime(2022, 3, 31, 23, 59, 59, tzinfo=UTC),
                ),
            },
            "audit_timeout_seconds": Decimal(5),
            "token_state_timeout_seconds": Decimal(5),
            "double_spend_owner": "risk_store",
            "drawdown_caution_threshold": Decimal("0.03"),
            "drawdown_restricted_threshold": Decimal("0.06"),
            "drawdown_critical_threshold": Decimal("0.08"),
            "emergency_flash_crash_move_pct": Decimal("0.05"),
            "emergency_flash_crash_window_seconds": 60,
            "emergency_connectivity_loss_seconds": 30,
            "emergency_margin_call_utilization_pct": Decimal("0.80"),
            "emergency_recovery_lock_seconds": 900,
            "assessment_recalc_events": (
                "fill",
                "cancellation",
                "position_change",
                "valuation_change",
                "policy_change",
            ),
            "assessment_max_staleness_seconds": 120,
        }
    return create_risk_config(
        **_base_values(profile, execution_route),
        **live_values,
        policy_version=f"personal-account-{execution_route}-v1",
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
    logger.info("Registering the default Risk policy profiles")
    hashes: dict[str, str] = {}
    for name, config in (
        (
            "personal_account_sim",
            build_personal_account_risk_config("simulation", "sim"),
        ),
        ("personal_account_demo", build_personal_account_risk_config()),
        (
            "personal_account_live",
            build_personal_account_risk_config("live", "live"),
        ),
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
