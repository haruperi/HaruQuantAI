"""Tests for the two registered default Risk account profiles."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.services.data import build_data_settings, data_settings_context
from app.services.risk import (
    build_personal_account_risk_config,
    build_prop_firm_risk_config,
    get_risk_policy,
    register_default_risk_policies,
    run_risk_migrations,
)
from app.services.risk.contracts.responses import unwrap_risk_response
from app.utils import generate_id


def _settings(tmp_path: Path) -> object:
    """Return disposable database settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///default-risk-policies.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=5.0,
        approved_storage_roots=(Path(),),
    )


def test_default_policies_contain_every_registered_operational_limit() -> None:
    """Keep all owner-approved keys in both immutable policy payloads."""
    expected = {
        "max_risk_per_trade_pct",
        "preferred_risk_per_trade_pct",
        "max_daily_loss_pct",
        "max_weekly_loss_pct",
        "max_monthly_loss_pct",
        "max_portfolio_drawdown_pct",
        "max_strategy_drawdown_pct",
        "max_symbol_drawdown_pct",
        "max_symbol_exposure_pct",
        "max_currency_cluster_exposure_pct",
        "max_correlated_exposure_pct",
        "max_total_exposure_pct",
        "max_gross_exposure_pct",
        "max_net_exposure_pct",
        "max_leverage",
        "max_total_margin_usage_pct",
        "min_free_margin_pct",
        "min_margin_level_pct",
        "max_open_positions",
        "max_pending_orders",
        "max_live_strategies",
        "max_trades_per_day",
        "max_trades_per_strategy_per_day",
        "max_consecutive_losses",
        "max_spread_pips_default",
        "max_slippage_pips_default",
        "max_commission_burden_pct",
        "max_swap_burden_pct",
        "approval_token_ttl_seconds",
        "kill_switch_daily_loss_pct",
        "kill_switch_portfolio_drawdown_pct",
    }
    personal = build_personal_account_risk_config()
    prop = build_prop_firm_risk_config()
    assert expected <= personal.model_fields_set
    assert expected <= prop.model_fields_set
    assert personal.max_risk_per_trade_pct == Decimal("0.01")
    assert prop.max_risk_per_trade_pct == Decimal("0.005")
    assert personal.max_slippage_pips_default == Decimal("1.0")
    assert prop.max_slippage_pips_default == Decimal("0.5")


def test_default_policy_registration_round_trips_idempotently(tmp_path: Path) -> None:
    """Register exactly two defaults and reconstruct both by canonical hash."""
    with data_settings_context(_settings(tmp_path)):
        migration = run_risk_migrations(request_id=generate_id("req"))
        assert migration.status == "success"
        arguments = {
            "effective_at": datetime(2026, 8, 6, tzinfo=UTC),
            "request_id": generate_id("req"),
            "correlation_id": generate_id("cor"),
        }
        first = unwrap_risk_response(
            register_default_risk_policies(**arguments),
            operation="register_default_risk_policies",
        )
        second = unwrap_risk_response(
            register_default_risk_policies(**arguments),
            operation="register_default_risk_policies",
        )
        assert first == second
        assert set(first) == {"personal_account", "prop_firm"}
        versions = {
            unwrap_risk_response(
                get_risk_policy(config_hash), operation="get_risk_policy"
            ).policy_version
            for config_hash in first.values()
        }
        assert versions == {
            "personal-account-default-v1",
            "prop-firm-default-v1",
        }
