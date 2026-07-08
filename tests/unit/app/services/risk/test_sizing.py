"""Unit tests for the position sizing engine (both V1 interfaces and V2 pure functions)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    PortfolioState,
    PositionSizingRequest,
    RiskConfig,
    SizingMethod,
    calculate_position_size,
)
from app.services.risk.config import load_risk_config
from app.services.risk.models import RiskReasonCode
from app.services.risk.sizing import (
    CorrelationImpact,
    KellyEvidence,
    RiskMilestone,
    SymbolRiskMetadata,
    build_volume_rejection,
    calculate_correlation_adjusted_size,
    calculate_fixed_fractional_size,
    calculate_fixed_risk_size,
    calculate_kelly_reference_size,
    calculate_milestone_size,
    calculate_stop_distance,
    calculate_volatility_adjusted_size,
    convert_stop_distance_to_account_risk,
    normalize_volume,
    validate_normalized_volume,
    validate_symbol_volume_metadata,
)


@pytest.fixture
def base_config() -> RiskConfig:
    """Load default base risk config."""
    cfg = load_risk_config("default")
    cfg.max_risk_per_trade = Decimal("0.05")
    cfg.min_kelly_trades = 30
    return cfg


@pytest.fixture
def base_portfolio() -> PortfolioState:
    """Provide a standard portfolio state."""
    return PortfolioState(
        account_id="acc-123",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
    )


@pytest.fixture
def eur_usd_context() -> dict[str, Any]:
    """Provide standard EURUSD quote symbol context."""
    return {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "contract_size": 100000.0,
        "digits": 5,
        "tick_size": 0.00001,
        "tick_value": 1.0,  # $1 per tick/point per standard lot
        "conversion_rate": 1.0,
    }


@pytest.fixture
def standard_symbol() -> SymbolRiskMetadata:
    """Provide a standard EURUSD symbol metadata for V2 tests."""
    return SymbolRiskMetadata(
        symbol="EURUSD",
        volume_min=Decimal("0.01"),
        volume_max=Decimal("100.00"),
        volume_step=Decimal("0.01"),
        contract_size=Decimal("100000.0"),
        digits=5,
        tick_size=Decimal("0.00001"),
        tick_value=Decimal("1.0"),
        conversion_rate=Decimal("1.0"),
    )


# =====================================================================
# V1 Sizing Engine Legacy Integration Tests
# =====================================================================


def test_invalid_sizing_inputs(
    base_portfolio: PortfolioState, base_config: RiskConfig
) -> None:
    """Test validation failure conditions."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("-10.0"),  # Negative stop
    )

    # 1. Negative stop distance -> 0.0 lot
    res = calculate_position_size(
        req,
        base_portfolio,
        {
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "contract_size": 100000.0,
        },
        base_config,
    )
    assert res.calculated_volume == Decimal("0.0")
    assert "invalid_stop_distance" in res.constraints_applied

    # 2. Missing symbol specs -> 0.0 lot
    res_missing = calculate_position_size(req, base_portfolio, {}, base_config)
    assert res_missing.calculated_volume == Decimal("0.0")
    assert "missing_symbol_metadata" in res_missing.constraints_applied


def test_fixed_lot_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test static lot sizing with broker steps formatting."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_LOT,
        fixed_volume=Decimal("1.2345"),
    )

    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    # 1.2345 should round down to volume_step 0.01 -> 1.23 lots
    assert res.calculated_volume == Decimal("1.23")


def test_fixed_risk_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test fixed risk sizing logic."""
    # Equity = 100,000. Max risk per trade = 2% (2,000 USD).
    # Stop loss distance = 20 pips = 200 points.
    # Risk per standard lot = 200 points * $1 tick_value = $200.
    # Raw volume = $2000 / $200 = 10.0 lots.
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )

    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    assert res.calculated_volume == Decimal("10.0")
    assert res.risk_contribution == Decimal("2000.00")

    # Override with static risk_amount of $1,000.
    req_amt = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_amount=Decimal("1000.00"),
    )
    res_amt = calculate_position_size(
        req_amt, base_portfolio, eur_usd_context, base_config
    )
    # $1000 / $200 = 5.0 lots
    assert res_amt.calculated_volume == Decimal("5.00")


def test_volatility_adjusted_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test ATR volatility-adjusted sizing calculations."""
    # ATR = 0.00100 (10 pips). Multiplier = 2.0x.
    # Stop distance = 20 pips (200 points).
    # Risk amount = 100,000 * 2% = 2,000 USD.
    # Raw size = 2000 / (200 points * 1.0 tick_val) = 10.0 lots.
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED,
        atr_value=Decimal("0.00100"),
        multiplier=Decimal("2.0"),
        risk_percent=Decimal("0.02"),
    )

    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    assert res.calculated_volume == Decimal("10.0")
    assert "atr_volatility_stop" in res.constraints_applied

    # Test M1 volatility override in context
    eur_usd_context["m1_volatility"] = 0.00050  # 5 pips
    res_m1 = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    # Stop distance = 0.00050 * 2.0 = 0.00100 (10 pips = 100 points).
    # Risk per standard lot = 100 points * $1 = $100.
    # Raw size = 2000 / 100 = 20.0 lots.
    assert res_m1.calculated_volume == Decimal("20.0")
    assert "m1_volatility_stop" in res_m1.constraints_applied


def test_sizing_downward_multipliers(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test drawdown step-down and exposure reductions."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )

    # Inject multipliers: step-down 0.5, ccy-red 0.8, cluster-red 0.9
    eur_usd_context["drawdown_step_down_multiplier"] = 0.5
    eur_usd_context["currency_exposure_reduction"] = 0.8
    eur_usd_context["correlation_cluster_reduction"] = 0.9

    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    # Raw size = 10.0 lots
    # Adjusted size = 10.0 * 0.5 * 0.8 * 0.9 = 3.6 lots
    assert res.calculated_volume == Decimal("3.60")
    assert "drawdown_step_down" in res.constraints_applied
    assert "currency_exposure_reduction" in res.constraints_applied
    assert "correlation_cluster_reduction" in res.constraints_applied


def test_jpy_pair_sizing(
    base_portfolio: PortfolioState, base_config: RiskConfig
) -> None:
    """Test FX JPY pair pip and quote digit scaling."""
    jpy_context = {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "contract_size": 100000.0,
        "digits": 3,
        "tick_size": 0.001,
        "tick_value": 0.91,
        "conversion_rate": 0.0091,  # JPY to USD rate
    }
    req = PositionSizingRequest(
        symbol="USDJPY",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("50.0"),
        risk_percent=Decimal("0.01"),
    )

    res = calculate_position_size(req, base_portfolio, jpy_context, base_config)
    assert res.calculated_volume == Decimal("2.19")


def test_correlation_adjusted_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test correlation adjusted sizing formula."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.CORRELATION_ADJUSTED,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )

    eur_usd_context["portfolio_correlation"] = 0.8
    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    assert res.calculated_volume == Decimal("6.00")
    assert "correlation_adjustment" in res.constraints_applied


def test_kelly_reference_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test Kelly reference sizing and historical trades threshold gating."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.KELLY,
        stop_loss_pips=Decimal("20.0"),
    )

    # 1. Under minimum trade history evidence.
    # Kelly is advisory-only (returns 0.0 lot).
    eur_usd_context["kelly_win_rate"] = 0.60
    eur_usd_context["kelly_win_loss_ratio"] = 2.0
    eur_usd_context["historical_trade_count"] = 10
    eur_usd_context["kelly_min_trades"] = 30

    res_insufficient = calculate_position_size(
        req, base_portfolio, eur_usd_context, base_config
    )
    assert res_insufficient.calculated_volume == Decimal("0.00")
    assert (
        "kelly_advisory_insufficient_evidence" in res_insufficient.constraints_applied
    )

    # 2. Meets evidence threshold -> Kelly size calculated
    eur_usd_context["historical_trade_count"] = 50
    res_sufficient = calculate_position_size(
        req, base_portfolio, eur_usd_context, base_config
    )
    assert res_sufficient.calculated_volume == Decimal("100.00")
    assert "kelly_fraction_applied" in res_sufficient.constraints_applied
    assert "volume_max_cap" in res_sufficient.constraints_applied


# =====================================================================
# V2 Stateless Pure Calculator Tests
# =====================================================================


def test_normalization_validation(standard_symbol: SymbolRiskMetadata) -> None:
    """Test validate_symbol_volume_metadata and lot step check."""
    # 1. Valid metadata
    assert validate_symbol_volume_metadata(standard_symbol)["valid"] is True

    # 2. Invalid metadata (min lot is zero)
    bad_symbol = SymbolRiskMetadata.model_construct(
        symbol="EURUSD",
        volume_min=Decimal("0.0"),
        volume_max=Decimal("100.00"),
        volume_step=Decimal("0.01"),
        contract_size=Decimal("100000.0"),
        digits=5,
    )
    assert validate_symbol_volume_metadata(bad_symbol)["valid"] is False

    # 3. None metadata fields
    bad_symbol_none = SymbolRiskMetadata.model_construct(
        symbol="EURUSD",
        volume_min=None,
        volume_max=Decimal("100.0"),
        volume_step=None,
        contract_size=Decimal("100000.0"),
        digits=5,
    )
    assert validate_symbol_volume_metadata(bad_symbol_none)["valid"] is False

    # 4. Step flooring
    assert normalize_volume(Decimal("1.2345"), standard_symbol) == Decimal("1.23")
    assert normalize_volume(Decimal("0.005"), standard_symbol) == Decimal("0.00")

    # 5. Invalid step size in normalize_volume
    zero_step_symbol = SymbolRiskMetadata.model_construct(
        symbol="EURUSD",
        volume_min=Decimal("0.01"),
        volume_max=Decimal("100.00"),
        volume_step=Decimal("0.00"),
        contract_size=Decimal("100000.0"),
        digits=5,
    )
    assert normalize_volume(Decimal("1.0"), zero_step_symbol) == Decimal("0.0")

    # 6. Validate normalized volume bounds
    assert validate_normalized_volume(Decimal("1.23"), standard_symbol)["valid"] is True
    assert validate_normalized_volume(Decimal("0.005"), standard_symbol)["valid"] is False
    assert validate_normalized_volume(Decimal("101.00"), standard_symbol)["valid"] is False
    assert validate_normalized_volume(Decimal("1.2345"), standard_symbol)["valid"] is False


def test_build_volume_rejection(standard_symbol: SymbolRiskMetadata) -> None:
    """Test build_volume_rejection helper."""
    res = build_volume_rejection(Decimal("1.0"), standard_symbol, RiskReasonCode.INVALID_INPUT)
    assert res.calculated_volume == Decimal("0.0")
    assert any(c in res.constraints_applied for c in ("INVALID_INPUT", "invalid_input"))


def test_stop_distance_calculations(standard_symbol: SymbolRiskMetadata) -> None:
    """Test calculate_stop_distance and convert_stop_distance_to_account_risk."""
    # 1. Price pips distance
    req_pip = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK.value,
        stop_loss_pips=Decimal("15.0"),
    )
    dist = calculate_stop_distance(req_pip, standard_symbol)
    assert dist == Decimal("0.00150")

    # 2. Volatility adaptive stops (M1 volatility)
    req_vol = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED.value,
        multiplier=Decimal("2.5"),
    )
    dist_vol = calculate_stop_distance(req_vol, standard_symbol, {"m1_volatility": 0.00040})
    assert dist_vol == Decimal("0.00100")

    # 3. Volatility adaptive stops (ATR fallback)
    req_atr = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED.value,
        atr_value=Decimal("0.00030"),
        multiplier=Decimal("3.0"),
    )
    dist_atr = calculate_stop_distance(req_atr, standard_symbol)
    assert dist_atr == Decimal("0.00090")

    # 4. Missing Volatility exception
    req_missing_vol = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED.value,
    )
    with pytest.raises(ValueError, match="Missing volatility inputs"):
        calculate_stop_distance(req_missing_vol, standard_symbol)

    # 5. Convert to account currency risk
    risk_per_lot = convert_stop_distance_to_account_risk(Decimal("0.00150"), standard_symbol, "USD")
    assert risk_per_lot == Decimal("150.0")

    # 6. Default tick metadata fallbacks
    symbol_default_tick = standard_symbol.model_copy(update={"tick_size": None, "tick_value": None})
    risk_default = convert_stop_distance_to_account_risk(Decimal("0.00150"), symbol_default_tick, "USD")
    assert risk_default == Decimal("150.0")

    # 7. Zero stop distance cases
    assert calculate_stop_distance(
        PositionSizingRequest(symbol="EURUSD", method=SizingMethod.FIXED_LOT.value),
        standard_symbol
    ) == Decimal("0.0")

    assert convert_stop_distance_to_account_risk(Decimal("0.0"), standard_symbol, "USD") == Decimal("0.0")


def test_calculate_fixed_risk_size_v2(
    standard_symbol: SymbolRiskMetadata, base_config: RiskConfig
) -> None:
    """Test fixed-risk V2 pure sizing calculator."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK.value,
        risk_amount=Decimal("500.00"),
        stop_loss_pips=Decimal("10.0"),
    )

    res = calculate_fixed_risk_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
    )
    assert res.calculated_volume == Decimal("5.00")
    assert res.risk_contribution == Decimal("500.00")

    # Percent-based risk (1.5% of $100k = $1500)
    req_pct = req.model_copy(update={"risk_amount": None, "risk_percent": Decimal("0.015")})
    res_pct = calculate_fixed_risk_size(
        request=req_pct,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
    )
    assert res_pct.calculated_volume == Decimal("15.00")

    # Risk cap applied (request 10% but max_risk_per_trade cap is 5%)
    req_cap = req.model_copy(update={"risk_amount": None, "risk_percent": Decimal("0.10")})
    res_cap = calculate_fixed_risk_size(
        request=req_cap,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
    )
    assert res_cap.calculated_volume == Decimal("50.00")
    assert "max_risk_per_trade_cap" in res_cap.constraints_applied

    # Failure: invalid conversion rate
    bad_rate_symbol = SymbolRiskMetadata.model_construct(
        symbol="EURUSD",
        volume_min=Decimal("0.01"),
        volume_max=Decimal("100.00"),
        volume_step=Decimal("0.01"),
        contract_size=Decimal("100000.0"),
        digits=5,
        conversion_rate=Decimal("0.0"),
    )
    res_bad_rate = calculate_fixed_risk_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=bad_rate_symbol,
        config=base_config,
    )
    assert res_bad_rate.calculated_volume == Decimal("0.0")
    assert "invalid_conversion_rate" in res_bad_rate.constraints_applied

    # Failure: zero or negative equity
    res_bad_equity = calculate_fixed_risk_size(
        request=req,
        portfolio_equity=Decimal("0.0"),
        symbol_metadata=standard_symbol,
        config=base_config,
    )
    assert res_bad_equity.calculated_volume == Decimal("0.0")
    assert "zero_or_negative_equity" in res_bad_equity.constraints_applied

    # Failure: missing volatility inputs
    req_vol_fail = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED.value,
    )
    res_vol_fail = calculate_fixed_risk_size(
        request=req_vol_fail,
        portfolio_equity=Decimal("100000.0"),
        symbol_metadata=standard_symbol,
        config=base_config,
    )
    assert res_vol_fail.calculated_volume == Decimal("0.0")
    assert "missing_volatility_inputs" in res_vol_fail.constraints_applied

    # Failure: invalid stop distance (<= 0)
    req_zero_stop = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK.value,
        stop_loss_pips=Decimal("0.0"),
    )
    res_zero_stop = calculate_fixed_risk_size(
        request=req_zero_stop,
        portfolio_equity=Decimal("100000.0"),
        symbol_metadata=standard_symbol,
        config=base_config,
    )
    assert res_zero_stop.calculated_volume == Decimal("0.0")
    assert "invalid_stop_distance" in res_zero_stop.constraints_applied

    # Testing reductions
    res_reduced = calculate_fixed_risk_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
        drawdown_step_down_multiplier=Decimal("0.5"),
        currency_exposure_reduction=Decimal("0.8"),
        correlation_cluster_reduction=Decimal("0.9"),
    )
    assert res_reduced.calculated_volume == Decimal("1.80")
    assert "drawdown_step_down" in res_reduced.constraints_applied
    assert "currency_exposure_reduction" in res_reduced.constraints_applied
    assert "correlation_cluster_reduction" in res_reduced.constraints_applied

    # Below minimum volume case
    req_tiny = req.model_copy(update={"risk_amount": Decimal("0.10")})
    res_tiny = calculate_fixed_risk_size(
        request=req_tiny,
        portfolio_equity=Decimal("100000.0"),
        symbol_metadata=standard_symbol,
        config=base_config,
    )
    assert res_tiny.calculated_volume == Decimal("0.0")
    assert "below_minimum_volume" in res_tiny.constraints_applied

    # Over maximum volume cap case
    req_huge = req.model_copy(update={"risk_amount": Decimal("50000.0")})
    huge_config = base_config.model_copy(update={"max_risk_per_trade": Decimal("1.00")})
    res_huge = calculate_fixed_risk_size(
        request=req_huge,
        portfolio_equity=Decimal("100000.0"),
        symbol_metadata=standard_symbol,
        config=huge_config,
    )
    assert res_huge.calculated_volume == Decimal("100.00")
    assert "volume_max_cap" in res_huge.constraints_applied


def test_calculate_fixed_fractional_size_v2(
    standard_symbol: SymbolRiskMetadata, base_config: RiskConfig
) -> None:
    """Test fixed-fractional V2 pure calculator and its edge cases."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_FRACTIONAL.value,
        risk_percent=Decimal("0.01"),
        stop_loss_pips=Decimal("10.0"),
    )

    res = calculate_fixed_fractional_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
    )
    assert res.calculated_volume == Decimal("10.00")

    # Invalid spec metadata validation bypass
    bad_meta = SymbolRiskMetadata.model_construct(symbol="EURUSD")
    res_bad = calculate_fixed_fractional_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=bad_meta,
        config=base_config,
    )
    assert res_bad.calculated_volume == Decimal("0.0")
    assert "missing_symbol_metadata" in res_bad.constraints_applied


def test_calculate_volatility_adjusted_size_v2(
    standard_symbol: SymbolRiskMetadata, base_config: RiskConfig
) -> None:
    """Test volatility-adjusted V2 pure calculator and its edge cases."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED.value,
        risk_percent=Decimal("0.01"),
        multiplier=Decimal("2.0"),
    )

    res = calculate_volatility_adjusted_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
        market_context={"m1_volatility": Decimal("0.00050")},
    )
    assert res.calculated_volume == Decimal("10.00")
    assert "m1_volatility_stop" in res.constraints_applied

    # Invalid spec validation bypass
    bad_meta = SymbolRiskMetadata.model_construct(symbol="EURUSD")
    res_bad = calculate_volatility_adjusted_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=bad_meta,
        config=base_config,
    )
    assert res_bad.calculated_volume == Decimal("0.0")
    assert "missing_symbol_metadata" in res_bad.constraints_applied


def test_calculate_correlation_adjusted_size_v2(
    standard_symbol: SymbolRiskMetadata, base_config: RiskConfig
) -> None:
    """Test correlation-adjusted V2 pure calculator and its edge cases."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.CORRELATION_ADJUSTED.value,
        risk_percent=Decimal("0.01"),
        stop_loss_pips=Decimal("10.0"),
    )
    impact = CorrelationImpact(portfolio_correlation=Decimal("0.60"))

    res = calculate_correlation_adjusted_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
        correlation=impact,
    )
    assert res.calculated_volume == Decimal("7.00")
    assert "correlation_adjustment" in res.constraints_applied

    # Invalid spec validation bypass
    bad_meta = SymbolRiskMetadata.model_construct(symbol="EURUSD")
    res_bad = calculate_correlation_adjusted_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=bad_meta,
        config=base_config,
        correlation=impact,
    )
    assert res_bad.calculated_volume == Decimal("0.0")
    assert "missing_symbol_metadata" in res_bad.constraints_applied


def test_calculate_milestone_size_v2(
    standard_symbol: SymbolRiskMetadata, base_config: RiskConfig
) -> None:
    """Test milestone-adjusted V2 pure calculator and its edge cases."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.MILESTONE.value,
        risk_percent=Decimal("0.01"),
        stop_loss_pips=Decimal("10.0"),
    )
    milestones = [RiskMilestone(name="drawdown_threshold", multiplier=Decimal("0.50"))]

    res = calculate_milestone_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
        milestones=milestones,
    )
    assert res.calculated_volume == Decimal("5.00")
    assert "milestone_adjustment" in res.constraints_applied

    # Invalid spec validation bypass
    bad_meta = SymbolRiskMetadata.model_construct(symbol="EURUSD")
    res_bad = calculate_milestone_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=bad_meta,
        config=base_config,
        milestones=milestones,
    )
    assert res_bad.calculated_volume == Decimal("0.0")
    assert "missing_symbol_metadata" in res_bad.constraints_applied


def test_calculate_kelly_reference_size_v2(
    standard_symbol: SymbolRiskMetadata, base_config: RiskConfig
) -> None:
    """Test Kelly reference V2 pure calculator and its edge cases."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.KELLY.value,
        stop_loss_pips=Decimal("10.0"),
    )
    evidence = KellyEvidence(
        win_rate=Decimal("0.60"),
        win_loss_ratio=Decimal("1.50"),
        historical_trade_count=35,
        min_kelly_trades=30,
        enable_fractional_kelly=False,
    )

    res = calculate_kelly_reference_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
        evidence=evidence,
    )
    assert res.calculated_volume == pytest.approx(Decimal("333.333333"), abs=1e-4)
    assert res.is_advisory_only is True

    # Zero win loss ratio
    evidence_zero = evidence.model_copy(update={"win_loss_ratio": Decimal("0.0")})
    res_zero = calculate_kelly_reference_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
        evidence=evidence_zero,
    )
    assert res_zero.kelly_fraction_applied == Decimal("0.0")

    # Insufficient trade count
    evidence_low = evidence.model_copy(update={"historical_trade_count": 10})
    res_low = calculate_kelly_reference_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
        evidence=evidence_low,
    )
    assert res_low.calculated_volume == Decimal("0.0")
    assert "kelly_advisory_insufficient_evidence" in res_low.constraints_applied

    # Fractional Kelly active
    evidence_active = evidence.model_copy(update={"enable_fractional_kelly": True})
    res_active = calculate_kelly_reference_size(
        request=req,
        portfolio_equity=Decimal("100000.00"),
        symbol_metadata=standard_symbol,
        config=base_config,
        evidence=evidence_active,
    )
    assert res_active.is_advisory_only is False
    assert "kelly_advisory_only" not in res_active.constraints_applied
