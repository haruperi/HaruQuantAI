"""Unit tests for the pre-activation and simulation metadata checks."""

from __future__ import annotations

import pytest
from app.services.trading.contracts import PromotionStage, TradingRoute
from app.services.trading.promotion.preconditions import (
    validate_preactivation_conditions,
    validate_sim_metadata_lookup,
)
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)


def test_validate_preactivation_conditions_non_live_bypass() -> None:
    """Non-live routes or read-only stages bypass all precondition validations."""
    # SIM route with simulation stage
    validate_preactivation_conditions(
        route=TradingRoute.SIM,
        stage=PromotionStage.SIMULATION,
        active_kill_switches=True,
        reconciliation_blocked=True,
        context_is_stale=True,
        security_profile_missing=True,
    )

    # LIVE route with read-only connection stage
    validate_preactivation_conditions(
        route=TradingRoute.LIVE,
        stage=PromotionStage.READ_ONLY_BROKER_CONNECTION,
        active_kill_switches=True,
        reconciliation_blocked=True,
        context_is_stale=True,
        security_profile_missing=True,
    )


def test_validate_preactivation_conditions_live_mutation_checks() -> None:
    """Live mutation stages block execution on active issues."""
    # 1. Kill switches active
    with pytest.raises(TradingMappedError) as exc_info:
        validate_preactivation_conditions(
            route=TradingRoute.LIVE,
            stage=PromotionStage.MICRO_LIVE,
            active_kill_switches=True,
            reconciliation_blocked=False,
            context_is_stale=False,
            security_profile_missing=False,
        )
    assert exc_info.value.code == "LIVE_KILL_SWITCH_ACTIVE"

    # 2. Reconciliation blocked
    with pytest.raises(TradingMappedError) as exc_info:
        validate_preactivation_conditions(
            route=TradingRoute.LIVE,
            stage=PromotionStage.FULL_LIVE,
            active_kill_switches=False,
            reconciliation_blocked=True,
            context_is_stale=False,
            security_profile_missing=False,
        )
    assert exc_info.value.code == "LIVE_RECONCILIATION_REQUIRED"

    # 3. Context stale
    with pytest.raises(TradingMappedError) as exc_info:
        validate_preactivation_conditions(
            route=TradingRoute.LIVE,
            stage=PromotionStage.MICRO_LIVE,
            active_kill_switches=False,
            reconciliation_blocked=False,
            context_is_stale=True,
            security_profile_missing=False,
        )
    assert exc_info.value.code == "LIVE_STALE_CONTEXT"

    # 4. Security profile missing
    with pytest.raises(TradingMappedError) as exc_info:
        validate_preactivation_conditions(
            route=TradingRoute.LIVE,
            stage=PromotionStage.FULL_LIVE,
            active_kill_switches=False,
            reconciliation_blocked=False,
            context_is_stale=False,
            security_profile_missing=True,
        )
    assert exc_info.value.code == "CREDENTIALS_MISSING"

    # 5. All healthy passes
    validate_preactivation_conditions(
        route=TradingRoute.LIVE,
        stage=PromotionStage.FULL_LIVE,
        active_kill_switches=False,
        reconciliation_blocked=False,
        context_is_stale=False,
        security_profile_missing=False,
    )


def test_validate_sim_metadata_lookup_live_contexts() -> None:
    """Lookup allowed in live simulation/config/calibration contexts."""
    validate_sim_metadata_lookup(mode="configuration", has_captured_snapshot=False)
    validate_sim_metadata_lookup(mode="calibration", has_captured_snapshot=False)
    validate_sim_metadata_lookup(
        mode="live_metadata_simulation", has_captured_snapshot=False
    )


def test_validate_sim_metadata_lookup_historical_backtest() -> None:
    """Historical backtests require captured metadata snapshot."""
    # With snapshot -> Allowed
    validate_sim_metadata_lookup(mode="historical_backtest", has_captured_snapshot=True)

    # Without snapshot -> Blocked
    with pytest.raises(TradingValidationError, match="reproducibility"):
        validate_sim_metadata_lookup(
            mode="historical_backtest", has_captured_snapshot=False
        )


def test_validate_sim_metadata_lookup_invalid_contexts() -> None:
    """Unknown simulation context modes are blocked."""
    match_msg = "not permitted in simulation mode"
    with pytest.raises(TradingValidationError, match=match_msg):
        validate_sim_metadata_lookup(mode="arbitrary_mode", has_captured_snapshot=True)
