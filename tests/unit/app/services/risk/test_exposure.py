"""Unit tests for the FX currency exposure engine."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    PortfolioState,
    PositionState,
    ProposedTrade,
    RiskConfig,
    RiskMode,
    calculate_currency_exposure,
    decompose_position,
)
from app.utils.errors import ValidationError


@pytest.fixture
def base_config() -> RiskConfig:
    """Provide standard risk config."""
    return RiskConfig(
        profile_name="test_exposure",
        allow_live_execution=False,
    )


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
        "EURUSD_contract_size": 100000.0,
        "EURUSD_price": 1.10,
        "USDJPY_contract_size": 100000.0,
        "USDJPY_price": 150.0,
        "mode": RiskMode.PAPER,
        "conversion_rates": {
            "EUR": 1.10,
            "JPY": 0.0067,
        },
    }


def test_decompose_position() -> None:
    """Test position decomposition into currency legs."""
    # Long 1.0 standard lot EURUSD (contract 100k, price 1.10)
    legs_long = decompose_position(
        symbol="EURUSD",
        side="buy",
        quantity=Decimal("1.0"),
        price=Decimal("1.10"),
        contract_size=Decimal("100000.0"),
        base_ccy="EUR",
        quote_ccy="USD",
    )
    # Expected: Long 100k EUR, Short 110k USD
    assert len(legs_long) == 2
    assert legs_long[0].currency == "EUR"
    assert legs_long[0].signed_amount == Decimal("100000.0")
    assert legs_long[1].currency == "USD"
    assert legs_long[1].signed_amount == Decimal("-110000.0")

    # Short 0.5 lot USDJPY (contract 100k, price 150.0)
    legs_short = decompose_position(
        symbol="USDJPY",
        side="sell",
        quantity=Decimal("0.5"),
        price=Decimal("150.0"),
        contract_size=Decimal("100000.0"),
        base_ccy="USD",
        quote_ccy="JPY",
    )
    # Expected: Short 50k USD, Long 7.5M JPY
    assert len(legs_short) == 2
    assert legs_short[0].currency == "USD"
    assert legs_short[0].signed_amount == Decimal("-50000.0")
    assert legs_short[1].currency == "JPY"
    assert legs_short[1].signed_amount == Decimal("7500000.0")


def test_exposure_aggregation(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test currency exposure aggregation and USD conversion."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]

    res = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )

    # EUR leg: Long 100,000 EUR * 1.10 = 110,000 USD gross and net
    assert "EUR" in res
    assert res["EUR"].gross == Decimal("110000.0")
    assert res["EUR"].net == Decimal("110000.0")

    # USD leg: Short 110,000 USD gross = 110,000 USD, net = -110,000 USD
    assert "USD" in res
    assert res["USD"].gross == Decimal("110000.0")
    assert res["USD"].net == Decimal("-110000.0")


def test_exposure_conversion_failure(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test behavior when conversion rate is missing."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURMXN",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("20.00"),
            current_price=Decimal("20.00"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]
    context = eur_usd_context.copy()
    context["conversion_rates"] = {}

    with pytest.raises(ValidationError, match="Missing conversion rate for MXN to USD"):
        calculate_currency_exposure(base_portfolio, None, base_config, context)


def test_pending_order_exposure_policies(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test ignore, full-potential, near-market-only, and prob-weighted policies."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 1.0,
            "price": 1.09,
            "distance_pips": 100.0,
            "probability": 0.3,
            "status": "active",
        }
    ]

    # 1. ignore policy
    base_config.pending_order_policy = "ignore"
    res_ignore = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_ignore["EUR"].net == Decimal("110000.0")

    # 2. full-potential policy
    base_config.pending_order_policy = "full-potential"
    res_full = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_full["EUR"].net == Decimal("220000.0")

    # 3. near-market-only policy (threshold 50 pips)
    base_config.pending_order_policy = "near-market-only"
    # Order has distance 100 pips > 50 pips, should be excluded
    res_near_ex = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_near_ex["EUR"].net == Decimal("110000.0")

    # Change order distance to 30 pips <= 50 pips, should be included
    base_portfolio.orders[0]["distance_pips"] = 30.0
    res_near_in = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_near_in["EUR"].net == Decimal("220000.0")

    # 4. probability-weighted policy
    base_config.pending_order_policy = "probability-weighted"
    res_prob = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_prob["EUR"].net == Decimal("143000.00")


def test_live_mode_fail_closed_checks(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test live environment fail-closed behavior for unknown/unreconciled states."""
    base_portfolio.positions = []
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 1.0,
            "price": 1.10,
            "status": "unknown",
        }
    ]

    base_config.pending_order_policy = "full-potential"
    context = eur_usd_context.copy()
    context["mode"] = RiskMode.FULL_LIVE

    # 1. Unknown order status should raise ValidationError
    with pytest.raises(ValidationError, match="Fail-Closed: Unknown order status"):
        calculate_currency_exposure(base_portfolio, None, base_config, context)

    base_portfolio.orders[0]["status"] = "active"

    # 2. Unreconciled portfolio state should raise ValidationError
    context["is_reconciled"] = False
    with pytest.raises(
        ValidationError, match="Fail-Closed: Portfolio state is unreconciled"
    ):
        calculate_currency_exposure(base_portfolio, None, base_config, context)


def test_proposed_trade_evaluation(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test that candidate proposed trade is included in calculations."""
    base_portfolio.positions = []
    proposed = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.10"),
    )

    res = calculate_currency_exposure(
        base_portfolio, proposed, base_config, eur_usd_context
    )
    assert res["EUR"].net == Decimal("110000.0")


def test_custom_currency_clusters(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test aggregation of custom currency clusters from config/context."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        ),
        PositionState(
            position_id="pos-2",
            symbol="USDJPY",
            direction="short",
            quantity=Decimal("0.5"),
            entry_price=Decimal("150.0"),
            current_price=Decimal("150.0"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        ),
    ]

    base_config.currency_clusters = {"USD_CLUSTER": ["EUR", "JPY"]}

    res = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert "USD_CLUSTER" in res
    assert res["USD_CLUSTER"].gross == Decimal("160250.0")
    assert res["USD_CLUSTER"].net == Decimal("160250.0")


def test_exposure_filtering_by_strategy_and_symbol(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test filtering currency exposure calculations by strategy ID and symbol."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        ),
        PositionState(
            position_id="pos-2",
            symbol="USDJPY",
            direction="short",
            quantity=Decimal("0.5"),
            entry_price=Decimal("150.0"),
            current_price=Decimal("150.0"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-2",
            open_time=datetime.now(UTC),
        ),
    ]

    # 1. Filter by strategy-1 -> only EURUSD should be included
    res_strat1 = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context, strategy_id="strat-1"
    )
    assert "EUR" in res_strat1
    assert "JPY" not in res_strat1

    # 2. Filter by strategy-2 -> only USDJPY should be included
    res_strat2 = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context, strategy_id="strat-2"
    )
    assert "JPY" in res_strat2
    assert "EUR" not in res_strat2

    # 3. Filter by symbol USDJPY -> only USDJPY should be included
    res_symbol = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context, symbol="USDJPY"
    )
    assert "JPY" in res_symbol
    assert "EUR" not in res_symbol


def test_calculate_symbol_exposure(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test symbol exposure calculation."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]
    from app.services.risk import calculate_symbol_exposure

    res = calculate_symbol_exposure(base_portfolio, None, base_config, eur_usd_context)
    assert "EURUSD" in res
    assert res["EURUSD"].symbol == "EURUSD"
    # Long 1.0 standard lot EURUSD = 100k contract size
    assert res["EURUSD"].signed_amount == Decimal("100000.0")
    # Base rate to account currency (USD) is 1.10, so gross and
    # net should be 110,000 USD.
    assert res["EURUSD"].gross == Decimal("110000.0")
    assert res["EURUSD"].net == Decimal("110000.0")
    assert res["EURUSD"].account_currency_equivalent == Decimal("110000.0")


def test_nzd_support(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test default NZD resolving and fallback conversion rate."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="NZDUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("0.60"),
            current_price=Decimal("0.60"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]
    # Do not supply NZDUSD contract size or rates in context,
    # should use default/fallback conversion.
    res = calculate_currency_exposure(
        base_portfolio, None, base_config, {"mode": RiskMode.PAPER}
    )
    # NZD leg: Long 100k NZD. Fallback conversion rate to USD is 0.60.
    # NZD net equivalent in USD = 60,000 USD
    assert "NZD" in res
    assert res["NZD"].net == Decimal("60000.0")


def test_hidden_concentration_detection(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test detection of hidden USD short concentration."""
    from app.services.risk import detect_hidden_concentration

    # 1. Single pair long EURUSD -> no concentration warning
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]
    warnings = detect_hidden_concentration(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert len(warnings) == 0

    # 2. Add long GBPUSD -> USD-short concentration warning
    base_portfolio.positions.append(
        PositionState(
            position_id="pos-2",
            symbol="GBPUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.25"),
            current_price=Decimal("1.25"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    )
    warnings = detect_hidden_concentration(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert len(warnings) == 1
    assert "Hidden USD short concentration detected" in warnings[0]
    assert "EURUSD" in warnings[0]
    assert "GBPUSD" in warnings[0]


def test_exposure_engines_and_snapshot(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test engines (Currency, Symbol, Cluster) and snapshot builder."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]
    base_config.currency_clusters = {"EURO_PE": ["EUR"]}

    from app.services.risk import (
        ClusterExposureEngine,
        CurrencyExposureEngine,
        ExposureSnapshotBuilder,
        SymbolExposureEngine,
        calculate_currency_leg_exposure,
        calculate_net_currency_exposure,
        calculate_projected_exposure,
    )

    # Test calculate_currency_leg_exposure
    legs = calculate_currency_leg_exposure(
        "EURUSD",
        "buy",
        Decimal("1.0"),
        Decimal("1.10"),
        Decimal("100000.0"),
        "EUR",
        "USD",
    )
    assert len(legs) == 2

    # Test calculate_net_currency_exposure
    net_ccy = calculate_net_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert net_ccy["EUR"] == Decimal("110000.0")

    # Test calculate_projected_exposure
    proj = calculate_projected_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert proj["EUR"].net == Decimal("110000.0")

    # Test CurrencyExposureEngine
    ccy_engine = CurrencyExposureEngine(base_config)
    ccy_res = ccy_engine.calculate_exposure(base_portfolio, None, eur_usd_context)
    assert "EUR" in ccy_res

    # Test SymbolExposureEngine
    sym_engine = SymbolExposureEngine(base_config)
    sym_res = sym_engine.calculate_exposure(base_portfolio, None, eur_usd_context)
    assert "EURUSD" in sym_res

    # Test ClusterExposureEngine
    cluster_engine = ClusterExposureEngine(base_config)
    cluster_res = cluster_engine.calculate_exposure(
        base_portfolio, None, eur_usd_context
    )
    assert "EURO_PE" in cluster_res

    # Test ExposureSnapshotBuilder
    builder = ExposureSnapshotBuilder(base_config)
    snap = builder.build_snapshot(base_portfolio, None, eur_usd_context)
    assert snap["portfolio_id"] == "acc-123"
    assert snap["portfolio_exposure"] == Decimal("220000.0")
    assert "EURUSD" in snap["symbol_exposures"]
    assert "strat-1" in snap["strategy_exposures"]


def test_exposure_resolve_base_quote_edge_cases() -> None:
    """Test _resolve_base_quote fallback and suffix parsing logic."""
    from app.services.risk.exposure import _resolve_base_quote

    # 1. Dictionary specs in market context
    ctx_spec = {"EURUSD": {"base": "eur", "quote": "usd"}}
    assert _resolve_base_quote("EURUSD", ctx_spec) == ("EUR", "USD")

    # 2. Suffix keys in context
    ctx_keys = {"EURUSD_base": "EUR", "EURUSD_quote": "USD"}
    assert _resolve_base_quote("EURUSD", ctx_keys) == ("EUR", "USD")

    # 3. Custom suffix matching
    assert _resolve_base_quote("GOLDUSD", {}) == ("GOLD", "USD")
    assert _resolve_base_quote("US30", {}) == ("US30", "USD")


def test_exposure_conversion_rate_formatting_lookups() -> None:
    """Test rates lookup with slashes, underscores, and direct pairs in context."""
    from app.services.risk.exposure import _resolve_conversion_rate

    # Slashes lookup
    ctx_slash = {"EUR/USD": 1.09}
    assert _resolve_conversion_rate("EUR", "USD", ctx_slash) == Decimal("1.09")

    # Underscores lookup
    ctx_und = {"EUR_USD": 1.085}
    assert _resolve_conversion_rate("EUR", "USD", ctx_und) == Decimal("1.085")

    # Slashes reverse lookup
    ctx_slash_rev = {"USD/EUR": 0.90}
    assert _resolve_conversion_rate("EUR", "USD", ctx_slash_rev) == Decimal(
        "1.0"
    ) / Decimal("0.90")


def test_exposure_proposed_trade_fallback_price(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
) -> None:
    """Test ProposedTrade with <= 0 price falls back to market context price."""
    proposed = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("0.0"),
    )
    ctx = {
        "mode": RiskMode.PAPER,
        "EURUSD_contract_size": 100000.0,
        "EURUSD_price": 1.12,
    }
    res = calculate_currency_exposure(base_portfolio, proposed, base_config, ctx)
    # EUR leg: Long 100k, USD leg: Short 112k USD equivalent
    assert res["USD"].net == Decimal("-112000.0")


def test_decompose_position_invalid_side() -> None:
    """Test decompose_position raises ValueError on invalid side."""
    with pytest.raises(ValueError, match="Invalid position/order side"):
        decompose_position(
            symbol="EURUSD",
            side="invalid",
            quantity=Decimal("1.0"),
            price=Decimal("1.10"),
            contract_size=Decimal("100000.0"),
            base_ccy="EUR",
            quote_ccy="USD",
        )


def test_exposure_live_mode_missing_fields_validation(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
) -> None:
    """Test live mode validation rejects orders with missing required fields."""
    base_config.pending_order_policy = "full-potential"
    # Order missing side
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "quantity": 1.0,
            "price": 1.10,
            "status": "active",
        }
    ]
    ctx = {
        "mode": RiskMode.FULL_LIVE,
        "is_reconciled": True,
        "portfolio_reconciled": True,
        "broker_connected": True,
    }
    with pytest.raises(ValidationError, match="Missing required order fields"):
        calculate_currency_exposure(base_portfolio, None, base_config, ctx)


def test_symbol_exposure_with_orders_and_proposed_trade(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test calculate_symbol_exposure with orders and proposed trade."""
    from app.services.risk import calculate_symbol_exposure

    base_config.pending_order_policy = "full-potential"
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "side": "sell",
            "quantity": 0.5,
            "status": "active",
        }
    ]
    proposed = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.2"),
    )

    res = calculate_symbol_exposure(
        base_portfolio, proposed, base_config, eur_usd_context
    )
    assert "EURUSD" in res
    # 0.5 lot sell orders = -50k, 0.2 lot proposed buy = +20k. Net exposure = -30k
    assert res["EURUSD"].signed_amount == Decimal("-30000.0")


def test_hidden_concentration_with_orders(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test detect_hidden_concentration with pending orders."""
    from app.services.risk import detect_hidden_concentration

    base_config.pending_order_policy = "full-potential"
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 1.0,
            "status": "active",
        },
        {
            "symbol": "GBPUSD",
            "side": "buy",
            "quantity": 1.0,
            "status": "active",
        },
    ]

    warnings = detect_hidden_concentration(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert len(warnings) == 1
    assert "Hidden USD short concentration detected" in warnings[0]


def test_v2_parse_fx_symbol() -> None:
    """Test parse_fx_symbol with standard and non-standard symbols."""
    from app.services.risk.exposure import parse_fx_symbol

    pair = parse_fx_symbol("EURUSD")
    assert pair.base == "EUR"
    assert pair.quote == "USD"

    pair2 = parse_fx_symbol("EUR_USD")
    assert pair2.base == "EUR"
    assert pair2.quote == "USD"

    pair3 = parse_fx_symbol("USDJPY")
    assert pair3.base == "USD"
    assert pair3.quote == "JPY"

    pair4 = parse_fx_symbol("GBPCHF")
    assert pair4.base == "GBP"
    assert pair4.quote == "CHF"

    with pytest.raises(ValueError, match="Invalid FX symbol format"):
        parse_fx_symbol("INVALID")


def test_v2_decompose_fx_trade() -> None:
    """Test decompose_fx_trade with buy and sell sides."""
    from app.services.risk.exposure import (
        ContractSpecification,
        decompose_fx_trade,
    )

    trade = ProposedTrade(
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.5"),
        strategy_id="strat-1",
        price=Decimal("1.10"),
    )
    contract = ContractSpecification(symbol="EURUSD", contract_size=Decimal("100000.0"))

    base, quote = decompose_fx_trade(trade, Decimal("1.10"), contract)
    assert base.currency == "EUR"
    assert base.signed_amount == Decimal("150000.0")
    assert quote.currency == "USD"
    assert quote.signed_amount == Decimal("-165000.0")

    trade_sell = ProposedTrade(
        symbol="USDJPY",
        side="sell",
        volume=Decimal("0.5"),
        strategy_id="strat-1",
        price=Decimal("150.0"),
    )
    contract2 = ContractSpecification(symbol="USDJPY", contract_size=Decimal("100000.0"))
    base2, quote2 = decompose_fx_trade(trade_sell, Decimal("150.0"), contract2)
    assert base2.currency == "USD"
    assert base2.signed_amount == Decimal("-50000.0")
    assert quote2.currency == "JPY"
    assert quote2.signed_amount == Decimal("7500000.0")


def test_v2_validate_currency_conversion_requirements() -> None:
    """Test validate_currency_conversion_requirements."""
    from app.services.risk import CurrencyLegExposure
    from app.services.risk.exposure import (
        validate_currency_conversion_requirements,
    )

    exposures = [
        CurrencyLegExposure(currency="EUR", signed_amount=Decimal("1000.0")),
        CurrencyLegExposure(currency="JPY", signed_amount=Decimal("20000.0")),
    ]
    rates = {"EURUSD": Decimal("1.10"), "USDJPY": Decimal("150.0")}

    res = validate_currency_conversion_requirements(exposures, rates, "USD")
    assert res["valid"] is True

    # Missing JPY conversion
    bad_rates = {"EURUSD": Decimal("1.10")}
    res_bad = validate_currency_conversion_requirements(exposures, bad_rates, "USD")
    assert res_bad["valid"] is False
    assert "JPY" in res_bad["reason"]


def test_v2_extra_helpers() -> None:
    """Test extra pure exposure helpers."""
    from app.services.risk import CurrencyLegExposure
    from app.services.risk.exposure import (
        aggregate_currency_legs,
        calculate_gross_and_net_exposure,
        enforce_currency_rounding,
    )

    legs = [
        CurrencyLegExposure(currency="EUR", signed_amount=Decimal("1000.0")),
        CurrencyLegExposure(currency="EUR", signed_amount=Decimal("-300.0")),
        CurrencyLegExposure(currency="USD", signed_amount=Decimal("-500.0")),
    ]
    aggregated = aggregate_currency_legs(legs)
    assert aggregated["EUR"] == Decimal("700.0")
    assert aggregated["USD"] == Decimal("-500.0")

    totals = calculate_gross_and_net_exposure(aggregated)
    assert totals["gross"] == Decimal("1200.0")
    assert totals["net"] == Decimal("200.0")

    assert enforce_currency_rounding(Decimal("123.456"), "USD") == Decimal("123.46")
    assert enforce_currency_rounding(Decimal("123.456"), "JPY") == Decimal(123)

