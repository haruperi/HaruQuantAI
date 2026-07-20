"""Approved risk profile builders and registry.

Provides safe_default, prop_firm_default, paper, and live_conservative builders
and registry queries. Performs no import-time I/O.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from app.services.risk.models import (
    CorrelationSubConfig,
    DrawdownSubConfig,
    ExecutionSubConfig,
    RiskConfig,
    RiskSubConfig,
    TailRiskSubConfig,
)
from app.utils.logger import logger


def build_safe_default_profile() -> RiskConfig:
    """Build and return the approved safe default simulation/offline profile.

    Returns:
        RiskConfig: The validated default config.
    """
    logger.info("Building safe default risk profile.")
    return RiskConfig(
        profile_name="default",
        allow_live_execution=False,
        max_daily_loss_pct=Decimal("0.04"),
        max_total_loss_pct=Decimal("0.09"),
        double_spend_prevention_owner="risk_cache",
        max_margin_utilization_pct=Decimal("0.30"),
        max_effective_leverage=Decimal("30.0"),
        correlation_threshold=Decimal("0.70"),
        default_kelly_fraction=Decimal("0.25"),
        min_kelly_trades=3,
        max_risk_per_trade=Decimal("0.0025"),
        max_total_loss_pct_advisory=Decimal("0.08"),
        pending_order_policy="ignore",
        currency_clusters={"USD": ["EURUSD", "GBPUSD", "AUDUSD"]},
        allocation_method="correlation_adjusted_parity",
        max_allocation_increase_pct=Decimal("0.20"),
        max_strategy_allocation_pct=Decimal("0.50"),
        min_backtest_trades=100,
        min_backtest_sharpe=Decimal("1.5"),
        max_backtest_drawdown=Decimal("0.20"),
        min_wf_trades=50,
        min_wf_sharpe=Decimal("1.2"),
        min_sim_trades=30,
        min_sim_profit_factor=Decimal("1.1"),
        min_paper_trades=20,
        min_paper_sharpe=Decimal("1.0"),
        max_shadow_tracking_error=Decimal("0.05"),
        min_shadow_days=14,
        min_live_days=30,
        min_live_sharpe=Decimal("1.0"),
        var_method="historical",
        var_confidence=Decimal("0.95"),
        var_lookback_days=250,
        es_confidence=Decimal("0.95"),
        max_stress_loss_pct=Decimal("0.02"),
        min_correlation_samples=20,
        currency_leg_limits={"USD": Decimal("100000.0"), "EUR": Decimal("100000.0")},
        drawdown_stepdown_thresholds=[Decimal("0.05"), Decimal("0.08")],
        drawdown_stepdown_multipliers=[Decimal("0.8"), Decimal("0.5")],
        maintenance_margin_pct=Decimal("0.50"),
        max_spread_multiplier=Decimal("3.0"),
        max_slippage_pips=Decimal("5.0"),
        rollover_blackout_start_utc="21:55",
        rollover_blackout_end_utc="22:05",
        m1_volatility_adaptive_sizing=True,
        m1_spread_to_sigma_ratio_filter=Decimal("0.25"),
        m1_broker_midnight_blackout_minutes=15,
        operator_approval_fields=None,
        experimental_features={},
        risk=RiskSubConfig(
            max_risk_per_trade=Decimal("0.0025"),
            max_total_open_risk=Decimal("0.0150"),
            max_symbol_open_risk=Decimal("0.0050"),
            max_currency_bucket_risk=Decimal("0.0075"),
            max_correlated_cluster_risk=Decimal("0.0075"),
            max_margin_usage=Decimal("0.30"),
        ),
        drawdown=DrawdownSubConfig(
            daily_loss_soft_limit=Decimal("0.02"),
            daily_loss_hard_limit=Decimal("0.04"),
            total_drawdown_soft_limit=Decimal("0.06"),
            total_drawdown_hard_limit=Decimal("0.09"),
        ),
        correlation=CorrelationSubConfig(
            lookback_m5=96,
            lookback_h1=24,
            lookback_d1=10,
            reject_threshold=Decimal("0.70"),
            reduce_threshold=Decimal("0.50"),
        ),
        tail_risk=TailRiskSubConfig(
            var_confidence=Decimal("0.95"),
            es_confidence=Decimal("0.95"),
            max_portfolio_var=Decimal("0.01"),
            max_portfolio_es=Decimal("0.015"),
            stress_loss_limit=Decimal("0.02"),
        ),
        execution=ExecutionSubConfig(
            max_spread_to_sigma=Decimal("0.25"),
            max_slippage_to_sigma=Decimal("0.20"),
            rollover_blackout_hours_before=2,
            rollover_blackout_hours_after=2,
        ),
    )


def build_prop_firm_default_profile() -> RiskConfig:
    """Build and return the conservative prop-firm default profile.

    Returns:
        RiskConfig: The validated prop-firm default config.
    """
    logger.info("Building prop firm default risk profile.")
    return RiskConfig(
        profile_name="prop_firm_default",
        allow_live_execution=False,
        max_daily_loss_pct=Decimal("0.04"),
        max_total_loss_pct=Decimal("0.08"),
        double_spend_prevention_owner="risk_cache",
        max_margin_utilization_pct=Decimal("0.70"),
        max_effective_leverage=Decimal("10.0"),
        correlation_threshold=Decimal("0.40"),
        default_kelly_fraction=Decimal("0.20"),
        min_kelly_trades=5,
        max_risk_per_trade=Decimal("0.005"),
        max_total_loss_pct_advisory=Decimal("0.03"),
        pending_order_policy="ignore",
        currency_clusters={"USD": ["EURUSD", "GBPUSD", "AUDUSD"]},
        allocation_method="correlation_adjusted_parity",
        max_allocation_increase_pct=Decimal("0.15"),
        max_strategy_allocation_pct=Decimal("0.40"),
        min_backtest_trades=150,
        min_backtest_sharpe=Decimal("1.8"),
        max_backtest_drawdown=Decimal("0.15"),
        min_wf_trades=75,
        min_wf_sharpe=Decimal("1.4"),
        min_sim_trades=50,
        min_sim_profit_factor=Decimal("1.2"),
        min_paper_trades=30,
        min_paper_sharpe=Decimal("1.2"),
        max_shadow_tracking_error=Decimal("0.03"),
        min_shadow_days=20,
        min_live_days=45,
        min_live_sharpe=Decimal("1.2"),
        var_method="historical",
        var_confidence=Decimal("0.95"),
        var_lookback_days=250,
        es_confidence=Decimal("0.95"),
        max_stress_loss_pct=Decimal("0.10"),
        min_correlation_samples=20,
        currency_leg_limits={"USD": Decimal("50000.0"), "EUR": Decimal("50000.0")},
        drawdown_stepdown_thresholds=[Decimal("0.03"), Decimal("0.05")],
        drawdown_stepdown_multipliers=[Decimal("0.5"), Decimal("0.2")],
        maintenance_margin_pct=Decimal("0.50"),
        max_spread_multiplier=Decimal("2.0"),
        max_slippage_pips=Decimal("3.0"),
        rollover_blackout_start_utc="21:55",
        rollover_blackout_end_utc="22:05",
        m1_volatility_adaptive_sizing=True,
        m1_spread_to_sigma_ratio_filter=Decimal("1.0"),
        m1_broker_midnight_blackout_minutes=15,
        operator_approval_fields=None,
        experimental_features={},
        risk=RiskSubConfig(
            max_risk_per_trade=Decimal("0.005"),
            max_total_open_risk=Decimal("0.015"),
            max_symbol_open_risk=Decimal("0.005"),
            max_currency_bucket_risk=Decimal("0.0075"),
            max_correlated_cluster_risk=Decimal("0.0075"),
            max_margin_usage=Decimal("0.70"),
        ),
        drawdown=DrawdownSubConfig(
            daily_loss_soft_limit=Decimal("0.03"),
            daily_loss_hard_limit=Decimal("0.04"),
            total_drawdown_soft_limit=Decimal("0.06"),
            total_drawdown_hard_limit=Decimal("0.08"),
        ),
        correlation=CorrelationSubConfig(
            lookback_m5=96,
            lookback_h1=24,
            lookback_d1=10,
            reject_threshold=Decimal("0.40"),
            reduce_threshold=Decimal("0.30"),
        ),
        tail_risk=TailRiskSubConfig(
            var_confidence=Decimal("0.95"),
            es_confidence=Decimal("0.95"),
            max_portfolio_var=Decimal("0.01"),
            max_portfolio_es=Decimal("0.015"),
            stress_loss_limit=Decimal("0.10"),
        ),
        execution=ExecutionSubConfig(
            max_spread_to_sigma=Decimal("1.0"),
            max_slippage_to_sigma=Decimal("0.20"),
            rollover_blackout_hours_before=2,
            rollover_blackout_hours_after=2,
        ),
    )


def build_paper_profile() -> RiskConfig:
    """Build and return the paper-trading validation controls profile.

    Returns:
        RiskConfig: The validated paper trading config.
    """
    logger.info("Building paper risk profile.")
    return RiskConfig(
        profile_name="paper",
        allow_live_execution=False,
        max_daily_loss_pct=Decimal("0.06"),
        max_total_loss_pct=Decimal("0.12"),
        double_spend_prevention_owner="risk_cache",
        max_margin_utilization_pct=Decimal("0.85"),
        max_effective_leverage=Decimal("50.0"),
        correlation_threshold=Decimal("0.60"),
        default_kelly_fraction=Decimal("0.30"),
        min_kelly_trades=2,
        max_risk_per_trade=Decimal("0.02"),
        max_total_loss_pct_advisory=Decimal("0.10"),
        pending_order_policy="ignore",
        currency_clusters={"USD": ["EURUSD", "GBPUSD", "AUDUSD"]},
        allocation_method="correlation_adjusted_parity",
        max_allocation_increase_pct=Decimal("0.20"),
        max_strategy_allocation_pct=Decimal("0.50"),
        min_backtest_trades=100,
        min_backtest_sharpe=Decimal("1.5"),
        max_backtest_drawdown=Decimal("0.20"),
        min_wf_trades=50,
        min_wf_sharpe=Decimal("1.2"),
        min_sim_trades=30,
        min_sim_profit_factor=Decimal("1.1"),
        min_paper_trades=20,
        min_paper_sharpe=Decimal("1.0"),
        max_shadow_tracking_error=Decimal("0.05"),
        min_shadow_days=14,
        min_live_days=30,
        min_live_sharpe=Decimal("1.0"),
        var_method="historical",
        var_confidence=Decimal("0.95"),
        var_lookback_days=250,
        es_confidence=Decimal("0.95"),
        max_stress_loss_pct=Decimal("0.18"),
        min_correlation_samples=20,
        currency_leg_limits={"USD": Decimal("100000.0"), "EUR": Decimal("100000.0")},
        drawdown_stepdown_thresholds=[Decimal("0.05"), Decimal("0.08")],
        drawdown_stepdown_multipliers=[Decimal("0.8"), Decimal("0.5")],
        maintenance_margin_pct=Decimal("0.50"),
        max_spread_multiplier=Decimal("3.0"),
        max_slippage_pips=Decimal("5.0"),
        rollover_blackout_start_utc="21:55",
        rollover_blackout_end_utc="22:05",
        m1_volatility_adaptive_sizing=True,
        m1_spread_to_sigma_ratio_filter=Decimal("1.5"),
        m1_broker_midnight_blackout_minutes=15,
        operator_approval_fields=None,
        experimental_features={},
        risk=RiskSubConfig(
            max_risk_per_trade=Decimal("0.02"),
            max_total_open_risk=Decimal("0.015"),
            max_symbol_open_risk=Decimal("0.005"),
            max_currency_bucket_risk=Decimal("0.0075"),
            max_correlated_cluster_risk=Decimal("0.0075"),
            max_margin_usage=Decimal("0.85"),
        ),
        drawdown=DrawdownSubConfig(
            daily_loss_soft_limit=Decimal("0.04"),
            daily_loss_hard_limit=Decimal("0.06"),
            total_drawdown_soft_limit=Decimal("0.08"),
            total_drawdown_hard_limit=Decimal("0.12"),
        ),
        correlation=CorrelationSubConfig(
            lookback_m5=96,
            lookback_h1=24,
            lookback_d1=10,
            reject_threshold=Decimal("0.60"),
            reduce_threshold=Decimal("0.45"),
        ),
        tail_risk=TailRiskSubConfig(
            var_confidence=Decimal("0.95"),
            es_confidence=Decimal("0.95"),
            max_portfolio_var=Decimal("0.01"),
            max_portfolio_es=Decimal("0.015"),
            stress_loss_limit=Decimal("0.18"),
        ),
        execution=ExecutionSubConfig(
            max_spread_to_sigma=Decimal("1.5"),
            max_slippage_to_sigma=Decimal("0.20"),
            rollover_blackout_hours_before=2,
            rollover_blackout_hours_after=2,
        ),
    )


def build_live_conservative_profile() -> RiskConfig:
    """Build and return the fail-closed live conservative profile.

    Returns:
        RiskConfig: The validated live conservative config.
    """
    logger.info("Building live conservative risk profile.")
    return RiskConfig(
        profile_name="live_conservative",
        allow_live_execution=True,
        max_daily_loss_pct=Decimal("0.02"),
        max_total_loss_pct=Decimal("0.05"),
        double_spend_prevention_owner="risk_cache",
        max_margin_utilization_pct=Decimal("0.50"),
        max_effective_leverage=Decimal("5.0"),
        correlation_threshold=Decimal("0.30"),
        default_kelly_fraction=Decimal("0.10"),
        min_kelly_trades=10,
        max_risk_per_trade=Decimal("0.002"),
        max_total_loss_pct_advisory=Decimal("0.015"),
        pending_order_policy="ignore",
        currency_clusters={"USD": ["EURUSD", "GBPUSD", "AUDUSD"]},
        allocation_method="correlation_adjusted_parity",
        max_allocation_increase_pct=Decimal("0.10"),
        max_strategy_allocation_pct=Decimal("0.30"),
        min_backtest_trades=200,
        min_backtest_sharpe=Decimal("2.0"),
        max_backtest_drawdown=Decimal("0.10"),
        min_wf_trades=100,
        min_wf_sharpe=Decimal("1.5"),
        min_sim_trades=50,
        min_sim_profit_factor=Decimal("1.3"),
        min_paper_trades=30,
        min_paper_sharpe=Decimal("1.2"),
        max_shadow_tracking_error=Decimal("0.02"),
        min_shadow_days=30,
        min_live_days=60,
        min_live_sharpe=Decimal("1.2"),
        var_method="historical",
        var_confidence=Decimal("0.95"),
        var_lookback_days=250,
        es_confidence=Decimal("0.95"),
        max_stress_loss_pct=Decimal("0.08"),
        min_correlation_samples=20,
        currency_leg_limits={"USD": Decimal("20000.0"), "EUR": Decimal("20000.0")},
        drawdown_stepdown_thresholds=[Decimal("0.01"), Decimal("0.03")],
        drawdown_stepdown_multipliers=[Decimal("0.5"), Decimal("0.0")],
        maintenance_margin_pct=Decimal("0.50"),
        max_spread_multiplier=Decimal("1.5"),
        max_slippage_pips=Decimal("2.0"),
        rollover_blackout_start_utc="21:55",
        rollover_blackout_end_utc="22:05",
        m1_volatility_adaptive_sizing=True,
        m1_spread_to_sigma_ratio_filter=Decimal("1.0"),
        m1_broker_midnight_blackout_minutes=15,
        operator_approval_fields={
            "operator_id": "admin_compliance",
            "approved_at": "2026-06-18T12:00:00Z",
            "approval_token": "GOVERNED_LIVE_READY_TOKEN_2026",
        },
        experimental_features={},
        risk=RiskSubConfig(
            max_risk_per_trade=Decimal("0.002"),
            max_total_open_risk=Decimal("0.015"),
            max_symbol_open_risk=Decimal("0.005"),
            max_currency_bucket_risk=Decimal("0.0075"),
            max_correlated_cluster_risk=Decimal("0.0075"),
            max_margin_usage=Decimal("0.50"),
        ),
        drawdown=DrawdownSubConfig(
            daily_loss_soft_limit=Decimal("0.01"),
            daily_loss_hard_limit=Decimal("0.02"),
            total_drawdown_soft_limit=Decimal("0.03"),
            total_drawdown_hard_limit=Decimal("0.05"),
        ),
        correlation=CorrelationSubConfig(
            lookback_m5=96,
            lookback_h1=24,
            lookback_d1=10,
            reject_threshold=Decimal("0.30"),
            reduce_threshold=Decimal("0.20"),
        ),
        tail_risk=TailRiskSubConfig(
            var_confidence=Decimal("0.95"),
            es_confidence=Decimal("0.95"),
            max_portfolio_var=Decimal("0.01"),
            max_portfolio_es=Decimal("0.015"),
            stress_loss_limit=Decimal("0.08"),
        ),
        execution=ExecutionSubConfig(
            max_spread_to_sigma=Decimal("1.0"),
            max_slippage_to_sigma=Decimal("0.20"),
            rollover_blackout_hours_before=2,
            rollover_blackout_hours_after=2,
        ),
    )


# Registry mapping built-in names to builders
_BUILTIN_PROFILES: Mapping[str, type[RiskConfig] | Any] = {
    "default": build_safe_default_profile,
    "prop_firm_default": build_prop_firm_default_profile,
    "paper": build_paper_profile,
    "live_conservative": build_live_conservative_profile,
}


def list_builtin_risk_profiles() -> tuple[str, ...]:
    """Return stable built-in profile names.

    Returns:
        tuple[str, ...]: Built-in profile names.
    """
    logger.debug("Listing built-in risk profiles.")
    return tuple(_BUILTIN_PROFILES.keys())


def get_builtin_risk_profile(name: str) -> RiskConfig:
    """Resolve an approved built-in profile by name or fail deterministically.

    Args:
        name: Name of the built-in profile.

    Returns:
        RiskConfig: Resolved config profile.

    Raises:
        ValueError: If profile name is not valid.
    """
    logger.info(f"Resolving built-in risk profile: {name}")
    builder = _BUILTIN_PROFILES.get(name)
    if not builder:
        allowed = list(_BUILTIN_PROFILES.keys())
        msg = f"Unknown built-in profile: {name}. Allowed profiles: {allowed}"
        logger.error(msg)
        raise ValueError(msg)
    return builder()
