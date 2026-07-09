"""Unit tests for trading action validation primitives."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.actions.validation import (
    ConversionRateEvidence,
    LocateSnapshot,
    MarketSessionEvidence,
    OrderIntent,
    OrderSide,
    OrderType,
    compute_account_currency_notional,
    normalize_decimal_to_step,
    normalize_stop_price,
    normalize_volume,
    validate_defense_in_depth_rails,
    validate_execution_protections,
    validate_fat_finger_ceiling,
    validate_margin,
    validate_market_session,
    validate_order_request,
    validate_short_locate,
    validate_stops,
    validate_time_in_force,
    validate_volume,
)
from app.services.trading.contracts import TimeInForce, TradingRoute
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)

from tests.services.trading.actions._fixtures import (
    as_dict,
    build_account,
    build_constraints,
    build_context,
    build_rail_limits,
    build_rail_state,
)


def test_normalize_decimal_to_step_rounds_down_and_up() -> None:
    """Step normalization rounds by the requested rounding mode."""
    assert normalize_decimal_to_step(
        Decimal("1.237"), step=Decimal("0.01"), rounding="ROUND_DOWN"
    ) == Decimal("1.23")
    assert normalize_decimal_to_step(
        Decimal("1.231"), step=Decimal("0.01"), rounding="ROUND_UP"
    ) == Decimal("1.24")


def test_normalize_volume_rounds_down_by_default() -> None:
    """Volume normalization rounds down unless round-up is authorized."""
    constraints = build_constraints(volume_step=Decimal("0.1"))
    original, normalized = normalize_volume(Decimal("0.37"), constraints=constraints)
    assert original == Decimal("0.37")
    assert normalized == Decimal("0.3")


def test_normalize_volume_allows_round_up_when_authorized() -> None:
    """Volume normalization rounds up only when explicitly authorized."""
    constraints = build_constraints(volume_step=Decimal("0.1"))
    _, normalized = normalize_volume(
        Decimal("0.31"), constraints=constraints, allow_round_up=True
    )
    assert normalized == Decimal("0.4")


def test_normalize_stop_price_rounds_away_from_market() -> None:
    """Stop price normalization never moves a stop closer to the market."""
    _, below = normalize_stop_price(
        Decimal("1.09994"), tick_size=Decimal("0.0001"), below_market=True
    )
    _, above = normalize_stop_price(
        Decimal("1.10006"), tick_size=Decimal("0.0001"), below_market=False
    )
    assert below == Decimal("1.0999")
    assert above == Decimal("1.1001")


def test_compute_account_currency_notional_same_currency() -> None:
    """Notional in the account currency requires no conversion rate."""
    constraints = build_constraints()
    notional, rate = compute_account_currency_notional(
        volume=Decimal("0.10"),
        reference_price=Decimal("1.10000"),
        constraints=constraints,
        account_currency="USD",
        conversion=None,
    )
    assert notional == Decimal("0.10") * Decimal(100000) * Decimal("1.10000")
    assert rate is None


def test_compute_account_currency_notional_requires_fresh_conversion() -> None:
    """Cross-currency notional fails closed without fresh conversion evidence."""
    constraints = build_constraints(quote_currency="EUR")
    with pytest.raises(TradingValidationError):
        compute_account_currency_notional(
            volume=Decimal("0.10"),
            reference_price=Decimal("1.10000"),
            constraints=constraints,
            account_currency="USD",
            conversion=None,
        )


def test_compute_account_currency_notional_rejects_mismatched_pair() -> None:
    """A conversion rate for the wrong currency pair fails closed."""
    constraints = build_constraints(quote_currency="EUR")
    conversion = ConversionRateEvidence(
        from_currency="GBP",
        to_currency="USD",
        rate=Decimal("1.25"),
        source="test",
        captured_at="2026-07-09T10:00:00Z",
        freshness_age_ms=10,
        ttl_ms=1000,
    )
    with pytest.raises(TradingValidationError):
        compute_account_currency_notional(
            volume=Decimal("0.10"),
            reference_price=Decimal("1.10000"),
            constraints=constraints,
            account_currency="USD",
            conversion=conversion,
        )


def test_compute_account_currency_notional_applies_conversion_rate() -> None:
    """A fresh, matching conversion rate is applied to the notional."""
    constraints = build_constraints(quote_currency="EUR")
    conversion = ConversionRateEvidence(
        from_currency="EUR",
        to_currency="USD",
        rate=Decimal("1.10"),
        source="test",
        captured_at="2026-07-09T10:00:00Z",
        freshness_age_ms=10,
        ttl_ms=1000,
    )
    notional, rate = compute_account_currency_notional(
        volume=Decimal(1),
        reference_price=Decimal(1),
        constraints=constraints,
        account_currency="USD",
        conversion=conversion,
    )
    assert rate == Decimal("1.10")
    assert notional == Decimal(100000) * Decimal("1.10")


def test_validate_volume_bounds_and_step() -> None:
    """Volume validation enforces min/max bounds and step alignment."""
    constraints = build_constraints()
    validate_volume(Decimal("0.10"), constraints=constraints)
    with pytest.raises(TradingValidationError):
        validate_volume(Decimal("0.001"), constraints=constraints)
    with pytest.raises(TradingValidationError):
        validate_volume(Decimal(1000), constraints=constraints)
    with pytest.raises(TradingValidationError):
        validate_volume(Decimal("0.015"), constraints=constraints)


def test_validate_stops_direction_and_distance() -> None:
    """Stop validation enforces market-side direction and minimum distance."""
    constraints = build_constraints()
    validate_stops(
        side=OrderSide.BUY,
        sl=Decimal("1.09000"),
        tp=Decimal("1.11000"),
        reference_price=Decimal("1.10000"),
        constraints=constraints,
    )
    with pytest.raises(TradingValidationError):
        validate_stops(
            side=OrderSide.BUY,
            sl=Decimal("1.11000"),
            tp=None,
            reference_price=Decimal("1.10000"),
            constraints=constraints,
        )
    with pytest.raises(TradingValidationError):
        validate_stops(
            side=OrderSide.BUY,
            sl=None,
            tp=Decimal("1.09000"),
            reference_price=Decimal("1.10000"),
            constraints=constraints,
        )
    with pytest.raises(TradingValidationError):
        validate_stops(
            side=OrderSide.BUY,
            sl=Decimal("1.09999"),
            tp=None,
            reference_price=Decimal("1.10000"),
            constraints=constraints,
        )


def test_validate_margin_insufficient_free_margin() -> None:
    """Margin validation fails closed when free margin is insufficient."""
    constraints = build_constraints()
    account = build_account(free_margin=Decimal(1))
    with pytest.raises(TradingValidationError):
        validate_margin(
            volume=Decimal(1),
            reference_price=Decimal("1.10000"),
            constraints=constraints,
            account=account,
            conversion=None,
        )


def test_validate_market_session_rules() -> None:
    """Session validation fails closed for live routes and honors freshness."""
    with pytest.raises(TradingValidationError):
        validate_market_session(route=TradingRoute.LIVE, symbol="EURUSD", evidence=None)
    assert validate_market_session(
        route=TradingRoute.SIM, symbol="EURUSD", evidence=None
    ) == {"session_checked": False}
    stale = MarketSessionEvidence(
        symbol="EURUSD",
        source="calendar",
        is_open=True,
        freshness_age_ms=5000,
        ttl_ms=1000,
    )
    with pytest.raises(TradingValidationError):
        validate_market_session(
            route=TradingRoute.LIVE, symbol="EURUSD", evidence=stale
        )
    mismatched = MarketSessionEvidence(
        symbol="GBPUSD",
        source="calendar",
        is_open=True,
        freshness_age_ms=5,
        ttl_ms=1000,
    )
    with pytest.raises(TradingValidationError):
        validate_market_session(
            route=TradingRoute.LIVE, symbol="EURUSD", evidence=mismatched
        )
    closed = MarketSessionEvidence(
        symbol="EURUSD",
        source="calendar",
        is_open=False,
        freshness_age_ms=5,
        ttl_ms=1000,
    )
    with pytest.raises(TradingValidationError):
        validate_market_session(
            route=TradingRoute.LIVE, symbol="EURUSD", evidence=closed
        )
    fresh_open = MarketSessionEvidence(
        symbol="EURUSD",
        source="calendar",
        is_open=True,
        freshness_age_ms=5,
        ttl_ms=1000,
    )
    result = validate_market_session(
        route=TradingRoute.LIVE, symbol="EURUSD", evidence=fresh_open
    )
    assert result["session_checked"] is True


def test_validate_time_in_force_supported_and_unsupported() -> None:
    """TIF validation enforces the broker-supported set."""
    validate_time_in_force(tif=TimeInForce.GTC, supported=(TimeInForce.GTC,))
    with pytest.raises(TradingValidationError):
        validate_time_in_force(tif=TimeInForce.FOK, supported=(TimeInForce.GTC,))


def test_validate_execution_protections_market_and_pending() -> None:
    """Execution protection validation enforces slippage and price collars."""
    with pytest.raises(TradingValidationError):
        validate_execution_protections(
            order_type=OrderType.MARKET,
            max_slippage_points=None,
            price=None,
            reference_price=Decimal("1.10000"),
            price_collar_bps=Decimal(50),
        )
    validate_execution_protections(
        order_type=OrderType.MARKET,
        max_slippage_points=10,
        price=None,
        reference_price=Decimal("1.10000"),
        price_collar_bps=Decimal(50),
    )
    with pytest.raises(TradingMappedError):
        validate_execution_protections(
            order_type=OrderType.LIMIT,
            max_slippage_points=None,
            price=None,
            reference_price=Decimal("1.10000"),
            price_collar_bps=Decimal(50),
        )
    with pytest.raises(TradingValidationError):
        validate_execution_protections(
            order_type=OrderType.LIMIT,
            max_slippage_points=None,
            price=Decimal("1.20000"),
            reference_price=Decimal("1.10000"),
            price_collar_bps=Decimal(50),
        )
    validate_execution_protections(
        order_type=OrderType.LIMIT,
        max_slippage_points=None,
        price=Decimal("1.10001"),
        reference_price=Decimal("1.10000"),
        price_collar_bps=Decimal(50),
    )


def test_validate_fat_finger_ceiling_blocks_excess_notional() -> None:
    """Fat-finger ceiling validation fails closed above the configured cap."""
    constraints = build_constraints()
    with pytest.raises(TradingValidationError):
        validate_fat_finger_ceiling(
            volume=Decimal(10),
            reference_price=Decimal("1.10000"),
            constraints=constraints,
            account_currency="USD",
            conversion=None,
            ceiling=Decimal(1000),
        )
    result = validate_fat_finger_ceiling(
        volume=Decimal("0.01"),
        reference_price=Decimal("1.10000"),
        constraints=constraints,
        account_currency="USD",
        conversion=None,
        ceiling=Decimal(100000),
    )
    assert "notional" in result


def test_validate_defense_in_depth_rails_each_ceiling() -> None:
    """Each defense-in-depth rail fails closed independently."""
    limits = build_rail_limits(
        max_mutation_attempts_per_window=1,
        max_open_positions=1,
        daily_notional_ceiling=Decimal(100),
    )
    with pytest.raises(TradingValidationError):
        validate_defense_in_depth_rails(
            notional=Decimal(1),
            limits=limits,
            state=build_rail_state(mutation_attempts_in_window=1),
        )
    with pytest.raises(TradingValidationError):
        validate_defense_in_depth_rails(
            notional=Decimal(1),
            limits=limits,
            state=build_rail_state(open_positions_count=1),
        )
    with pytest.raises(TradingValidationError):
        validate_defense_in_depth_rails(
            notional=Decimal(200),
            limits=limits,
            state=build_rail_state(),
        )
    result = validate_defense_in_depth_rails(
        notional=Decimal(10),
        limits=limits,
        state=build_rail_state(),
    )
    assert result["projected_daily_notional"] == "10"


def test_validate_short_locate_rules() -> None:
    """Short-locate validation skips non-shorts and fails closed otherwise."""
    assert validate_short_locate(is_short=False, locate=None) == {
        "locate_required": False
    }
    with pytest.raises(TradingValidationError):
        validate_short_locate(is_short=True, locate=None)
    stale = LocateSnapshot(
        symbol="TSLA",
        available_shares=Decimal(10),
        source="feed",
        freshness_age_ms=5000,
        ttl_ms=100,
    )
    with pytest.raises(TradingValidationError):
        validate_short_locate(is_short=True, locate=stale)
    empty = LocateSnapshot(
        symbol="TSLA",
        available_shares=Decimal(0),
        source="feed",
        freshness_age_ms=1,
        ttl_ms=100,
    )
    with pytest.raises(TradingValidationError):
        validate_short_locate(is_short=True, locate=empty)
    ok = LocateSnapshot(
        symbol="TSLA",
        available_shares=Decimal(10),
        source="feed",
        freshness_age_ms=1,
        ttl_ms=100,
    )
    result = validate_short_locate(is_short=True, locate=ok)
    assert result["locate_required"] is True


def test_order_intent_structural_validation() -> None:
    """Order intent validation enforces structural completeness rules."""
    with pytest.raises(ValueError, match="price is required"):
        OrderIntent(
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            volume=Decimal("0.1"),
        )
    with pytest.raises(ValueError, match="stop_limit_price is required"):
        OrderIntent(
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.STOP_LIMIT,
            volume=Decimal("0.1"),
            price=Decimal("1.1"),
        )
    with pytest.raises(ValueError, match="expiration is required"):
        OrderIntent(
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=Decimal("0.1"),
            tif=TimeInForce.GTD,
        )


def test_validate_order_request_success_path() -> None:
    """A fully valid order intent passes every sub-validation once."""
    context = build_context()
    intent = OrderIntent(
        symbol="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        volume=Decimal("0.10"),
        sl=Decimal("1.09000"),
        tp=Decimal("1.11000"),
        max_slippage_points=10,
    )
    result = validate_order_request(intent, context=context)
    assert result.normalized_intent["volume"] == "0.10"
    assert as_dict(result.audit["volume_check"])["volume"] == "0.10"


def test_validate_order_request_rejects_symbol_mismatch() -> None:
    """A symbol mismatch between intent and context fails closed."""
    context = build_context()
    intent = OrderIntent(
        symbol="GBPUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        volume=Decimal("0.10"),
        max_slippage_points=10,
    )
    with pytest.raises(TradingMappedError):
        validate_order_request(intent, context=context)


def test_validate_order_request_short_circuits_on_first_failure() -> None:
    """Validation short-circuits at the first failing sub-check."""
    context = build_context()
    intent = OrderIntent(
        symbol="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        volume=Decimal(999),
        max_slippage_points=10,
    )
    with pytest.raises(TradingValidationError):
        validate_order_request(intent, context=context)
