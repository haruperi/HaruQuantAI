"""Unit tests for the Margin Governance module.

Verifies margin, leverage, pending-order margin policies,
and exit-liquidity stress checks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    LeverageSnapshot,
    LiquiditySnapshot,
    MarginRequirement,
    MarginRiskEngine,
    PortfolioState,
    PositionState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    calculate_free_margin_after_trade,
    calculate_margin_requirement,
    check_exit_liquidity,
    check_leverage_limit,
    check_margin_usage,
)
from app.services.risk.feasibility.margin import (
    calculate_current_margin,
    calculate_current_margin_usage,
    calculate_free_margin_after_orders,
    calculate_free_margin_after_reservations,
    calculate_projected_margin,
    calculate_projected_margin_usage,
    check_margin_limits,
    check_strategy_margin_limit,
    exit_liquidity_stress_check,
    verify_margin_limits,
)
from app.services.risk.models import (
    AccountRiskSnapshot,
    PendingOrderRiskSnapshot,
    PortfolioRiskSnapshot,
)
from app.services.risk.policy.contracts import EffectiveRiskPolicy
from app.services.risk.errors import RiskValidationError as ValidationError


@pytest.fixture
def base_portfolio() -> PortfolioState:
    """Fixture for baseline PortfolioState."""
    return PortfolioState(
        account_id="acc-margin",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("1000.00"),
        free_margin=Decimal("9000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-eur",
                symbol="EURUSD",
                direction="long",
                quantity=Decimal("1.0"),
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1000"),
                floating_pnl=Decimal("0.0"),
                margin_required=Decimal("1000.0"),
                strategy_id="TF-01",
                open_time=datetime.now(UTC),
            )
        ],
        orders=[],
        strategy_allocations={"TF-01": Decimal("5000.00")},
    )


@pytest.fixture
def base_config() -> RiskConfig:
    """Fixture for baseline RiskConfig."""
    return RiskConfig(
        profile_name="default",
        max_margin_utilization_pct=Decimal("0.80"),
        max_effective_leverage=Decimal("30.0"),
        max_risk_per_trade=Decimal("0.02"),
    )


@pytest.fixture
def market_context() -> dict[str, Any]:
    """Fixture for market context."""
    return {
        "EURUSD_contract_size": 100000.0,
        "EURUSD_pip_size": 0.0001,
        "EURUSD_spread": 0.0002,
        "conversion_rates": {
            "EUR": 1.10,
            "USD": 1.0,
        },
    }


def test_margin_calculations(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify current and projected margin calculations."""
    # Current margin should be 1000
    assert calculate_current_margin(base_portfolio) == Decimal("1000.0")

    # Proposed trade: buy 1.0 EURUSD at 1.10
    # contract size = 100k, leverage = 30 (capped by config from default broker 30)
    # margin_quote = (1.0 * 100000 * 1.10) / 30 = 3666.67 USD
    # rate = 1.0 (quote USD to account USD)
    # projected_margin = 1000 + 3666.67 = 4666.67
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    proj = calculate_projected_margin(
        base_portfolio, trade, market_context, base_config
    )
    assert proj == pytest.approx(Decimal("4666.6667"))


def test_missing_margin_metadata(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify that calculations reject missing broker metadata."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    bad_context = {"conversion_rates": {"USD": 1.0}}
    with pytest.raises(ValidationError, match="Missing contract size metadata"):
        calculate_projected_margin(base_portfolio, trade, bad_context, base_config)


def test_free_margin_pending_orders_policies(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify free margin calculation under different pending order policies."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    # Add active pending order: buy 1.0 EURUSD at 1.10
    # margin required: 3666.67 USD
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "status": "active",
            "quantity": 1.0,
            "price": 1.1000,
            "probability": 0.5,
            "distance_pips": 20.0,
        }
    ]

    # 1. Ignore policy
    base_config.pending_order_policy = "ignore"
    free_ignore = calculate_free_margin_after_orders(
        base_portfolio, trade, market_context, base_config
    )
    # free_margin = 10000 - 4666.67 = 5333.33
    assert free_ignore == pytest.approx(Decimal("5333.3333"))

    # 2. Full potential policy
    base_config.pending_order_policy = "full-potential"
    free_full = calculate_free_margin_after_orders(
        base_portfolio, trade, market_context, base_config
    )
    # free_margin = 10000 - 4666.67 - 3666.67 = 1666.67
    assert free_full == pytest.approx(Decimal("1666.6667"))

    # 3. Probability weighted policy
    base_config.pending_order_policy = "probability-weighted"
    free_prob = calculate_free_margin_after_orders(
        base_portfolio, trade, market_context, base_config
    )
    # free_margin = 10000 - 4666.67 - (3666.67 * 0.5) = 3500.00
    assert free_prob == pytest.approx(Decimal("3500.00"))


def test_exit_liquidity_stress_check(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify exit liquidity stress check triggers fail under wide spreads."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    # Normal spread check passes
    exit_pass, exit_loss = exit_liquidity_stress_check(
        base_portfolio,
        trade,
        market_context,
        base_config,
        spread_multiplier=Decimal("5.0"),
    )
    # exit loss = (1.0 + 1.0) * 100000 * 0.0002 * 5 = 200 USD.
    # free_margin = 5333.33 -> passes
    assert exit_pass
    assert exit_loss == Decimal("200.00")

    # High spread multiplier triggers failure
    exit_fail, fail_loss = exit_liquidity_stress_check(
        base_portfolio,
        trade,
        market_context,
        base_config,
        spread_multiplier=Decimal("150.0"),
    )
    # loss = 2.0 * 100k * 0.0002 * 150 = 6000 USD > 5333.33 -> fails
    assert not exit_fail
    assert fail_loss == Decimal("6000.00")


def test_verify_margin_limits(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify limit checks for margin utilization and leverage limits."""
    # Pass path
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.5"),
        price=Decimal("1.1000"),
    )
    res = verify_margin_limits(base_portfolio, trade, market_context, base_config)
    assert res.status == RiskDecisionStatus.APPROVE
    assert not res.breached

    # Margin utilization breach (> 80%)
    # proposed volume = 2.0 lots -> margin = 7333.33.
    # total projected = 8333.33. Ratio = 83.33% > 80%
    trade_large = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("2.0"),
        price=Decimal("1.1000"),
    )
    res_large = verify_margin_limits(
        base_portfolio, trade_large, market_context, base_config
    )
    assert res_large.status == RiskDecisionStatus.REJECT
    assert res_large.reason_code == RiskReasonCode.MARGIN_BREACH

    # Leverage breach
    # total gross exposure for 4.0 lots EURUSD = 5.0 lots * 100000 * 1.10 = 550,000 USD
    # leverage = 550k / 10k = 55.0 > 30.0 config cap
    trade_leverage = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("4.0"),
        price=Decimal("1.1000"),
    )
    base_config.max_margin_utilization_pct = Decimal("5.0")
    res_lev = verify_margin_limits(
        base_portfolio, trade_leverage, market_context, base_config
    )
    assert res_lev.status == RiskDecisionStatus.REJECT
    assert res_lev.reason_code == RiskReasonCode.LEVERAGE_BREACH


def test_new_margin_standalone_functions(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify new margin standalone checker functions."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    req = calculate_margin_requirement(
        base_portfolio, trade, market_context, base_config
    )
    assert req == pytest.approx(Decimal("4666.6667"))

    free = calculate_free_margin_after_trade(
        base_portfolio, trade, market_context, base_config
    )
    assert free == pytest.approx(Decimal("5333.3333"))

    margin_check = check_margin_usage(
        base_portfolio, trade, market_context, base_config
    )
    assert margin_check.status == RiskDecisionStatus.APPROVE
    assert not margin_check.breached

    leverage_check = check_leverage_limit(
        base_portfolio, trade, market_context, base_config
    )
    assert leverage_check.status == RiskDecisionStatus.APPROVE
    assert not leverage_check.breached

    exit_check = check_exit_liquidity(
        base_portfolio, trade, market_context, base_config
    )
    assert exit_check.status == RiskDecisionStatus.APPROVE
    assert not exit_check.breached


def test_margin_risk_engine_evaluation(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify MarginRiskEngine evaluation flow and result wrappers."""
    engine = MarginRiskEngine(base_config)
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    margin_req = engine.evaluate_margin(base_portfolio, trade, market_context)
    assert isinstance(margin_req, MarginRequirement)
    assert margin_req.current_margin == Decimal("1000.0")
    assert margin_req.projected_margin == pytest.approx(Decimal("4666.6667"))
    assert margin_req.pass_status

    lev_snap = engine.evaluate_leverage(base_portfolio, trade, market_context)
    assert isinstance(lev_snap, LeverageSnapshot)
    assert lev_snap.effective_leverage == pytest.approx(
        Decimal("22.0")
    )  # (110k + 110k) / 10k
    assert lev_snap.pass_status

    liq_snap = engine.evaluate_exit_liquidity(
        base_portfolio, trade, market_context, spread_multiplier=Decimal("5.0")
    )
    assert isinstance(liq_snap, LiquiditySnapshot)
    assert liq_snap.exit_liquidity_loss == Decimal("200.00")
    assert liq_snap.pass_status


@pytest.fixture
def account_snapshot() -> AccountRiskSnapshot:
    """Fixture for a canonical AccountRiskSnapshot."""
    return AccountRiskSnapshot(
        equity=Decimal("10000.00"),
        balance=Decimal("10000.00"),
        free_margin=Decimal("9000.00"),
        margin_used=Decimal("1000.00"),
        leverage=Decimal("30.0"),
        base_currency="USD",
        timestamp=datetime.now(UTC),
    )


@pytest.fixture
def portfolio_snapshot() -> PortfolioRiskSnapshot:
    """Fixture for a canonical PortfolioRiskSnapshot."""
    return PortfolioRiskSnapshot(
        exposure=Decimal("110000.00"),
        var_es=Decimal("0.0"),
        stress_loss=Decimal("0.0"),
        drawdown=Decimal("0.0"),
    )


@pytest.fixture
def effective_policy(base_config: RiskConfig) -> EffectiveRiskPolicy:
    """Fixture for a resolved EffectiveRiskPolicy wrapping base_config."""
    return EffectiveRiskPolicy(
        policy_id="test-margin-policy",
        resolved_config=base_config,
        policy_hash="test-hash",
    )


def test_calculate_current_margin_usage(
    account_snapshot: AccountRiskSnapshot, portfolio_snapshot: PortfolioRiskSnapshot
) -> None:
    """Verify canonical current margin usage snapshot calculation."""
    snap = calculate_current_margin_usage(account_snapshot, portfolio_snapshot)
    assert snap.projected_margin == Decimal("1000.00")
    assert snap.margin_usage == pytest.approx(Decimal("0.10"))
    assert snap.leverage == Decimal("30.0")


def test_calculate_projected_margin_usage(
    account_snapshot: AccountRiskSnapshot, portfolio_snapshot: PortfolioRiskSnapshot
) -> None:
    """Verify canonical projected margin usage snapshot calculation."""
    proposal = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )
    snap = calculate_projected_margin_usage(
        account_snapshot, portfolio_snapshot, proposal
    )
    # proposed_margin = (1.0 * 100000 * 1.10) / 30 = 3666.67; projected = 1000 + 3666.67
    assert snap.projected_margin == pytest.approx(Decimal("4666.6667"))
    assert snap.free_margin == pytest.approx(Decimal("5333.3333"))


def test_calculate_free_margin_after_reservations(
    account_snapshot: AccountRiskSnapshot,
) -> None:
    """Verify free margin reservation calculation for pending/in-flight orders."""
    pending = [PendingOrderRiskSnapshot(order_id="p1", exposure=Decimal("1000.0"))]
    inflight = [PendingOrderRiskSnapshot(order_id="i1", exposure=Decimal("500.0"))]
    remaining = calculate_free_margin_after_reservations(
        account_snapshot, pending, inflight
    )
    assert remaining == Decimal("7500.0")

    # Reservations exceeding free margin clamp to zero
    big_pending = [PendingOrderRiskSnapshot(order_id="p2", exposure=Decimal("50000.0"))]
    remaining_zero = calculate_free_margin_after_reservations(
        account_snapshot, big_pending, []
    )
    assert remaining_zero == Decimal("0.0")


def test_check_margin_limits(
    account_snapshot: AccountRiskSnapshot,
    portfolio_snapshot: PortfolioRiskSnapshot,
    effective_policy: EffectiveRiskPolicy,
) -> None:
    """Verify margin/leverage limit checks against a resolved policy."""
    snap = calculate_current_margin_usage(account_snapshot, portfolio_snapshot)
    results = check_margin_limits(snap, effective_policy)
    assert len(results) == 2
    assert all(r.status == RiskDecisionStatus.APPROVE for r in results)

    breaching_policy = effective_policy.model_copy(
        update={
            "resolved_config": effective_policy.resolved_config.model_copy(
                update={"max_margin_utilization_pct": Decimal("0.01")}
            )
        }
    )
    breach_results = check_margin_limits(snap, breaching_policy)
    assert breach_results[0].status == RiskDecisionStatus.REJECT
    assert breach_results[0].reason_code == RiskReasonCode.MARGIN_BREACH


def test_margin_none_trade_and_price_fallbacks(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify None-trade and proposed-price resolution fallback branches."""
    # No proposed trade: projected margin equals current margin.
    proj = calculate_projected_margin(base_portfolio, None, market_context, base_config)
    assert proj == Decimal("1000.0")

    lev_res = check_leverage_limit(base_portfolio, None, market_context, base_config)
    assert lev_res.status == RiskDecisionStatus.APPROVE

    # Proposed trade with zero price resolves from a matching open position.
    trade_zero_price = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("0.0"),
    )
    proj_resolved = calculate_projected_margin(
        base_portfolio, trade_zero_price, market_context, base_config
    )
    assert proj_resolved > Decimal("1000.0")

    # Proposed trade with zero price and no matching position resolves from
    # a market_context "<symbol>_price" key.
    trade_gbp = ProposedTrade(
        strategy_id="TF-01",
        symbol="GBPUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("0.0"),
    )
    ctx_with_price = dict(market_context)
    ctx_with_price["GBPUSD_price"] = 1.25
    ctx_with_price["GBPUSD_contract_size"] = 100000.0
    proj_gbp = calculate_projected_margin(
        base_portfolio, trade_gbp, ctx_with_price, base_config
    )
    assert proj_gbp > Decimal("1000.0")

    lev_gbp = check_leverage_limit(
        base_portfolio, trade_gbp, ctx_with_price, base_config
    )
    assert lev_gbp.status == RiskDecisionStatus.APPROVE


def test_free_margin_near_market_only_and_inactive_orders(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify near-market-only pending order policy and inactive order skipping."""
    base_config.pending_order_policy = "near-market-only"
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "status": "inactive",
            "quantity": 5.0,
            "price": 1.1000,
        },
        {
            "symbol": "EURUSD",
            "status": "active",
            "quantity": 1.0,
            "price": 1.1000,
            "distance_pips": 10.0,
        },
        {
            "symbol": "EURUSD",
            "status": "active",
            "quantity": 1.0,
            "price": 1.1000,
            "distance_pips": 200.0,
        },
    ]
    free = calculate_free_margin_after_orders(
        base_portfolio, None, market_context, base_config
    )
    # Only the near-market order (10 pips) contributes; inactive and far
    # (200 pips) orders are excluded.
    assert free == pytest.approx(Decimal("5333.3333"))


def test_check_exit_liquidity_rejection(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify check_exit_liquidity rejects when simulated exit loss is too high."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )
    res = check_exit_liquidity(
        base_portfolio,
        trade,
        market_context,
        base_config,
        spread_multiplier=Decimal("150.0"),
    )
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.MARGIN_BREACH


def test_check_margin_usage_metadata_error(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
) -> None:
    """Verify check_margin_usage blocks on missing broker margin metadata."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )
    res = check_margin_usage(base_portfolio, trade, {}, base_config)
    assert res.status == RiskDecisionStatus.BLOCK
    assert res.reason_code == RiskReasonCode.INVALID_INPUT


def test_check_strategy_margin_limit_branches(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify strategy margin limit no-trade, no-cap, and breach branches."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    # No proposed trade: skipped.
    assert (
        check_strategy_margin_limit(base_portfolio, None, market_context, base_config)
        is None
    )

    # No strategy cap configured: skipped.
    base_portfolio.strategy_allocations = {}
    assert (
        check_strategy_margin_limit(base_portfolio, trade, market_context, base_config)
        is None
    )

    # Strategy cap configured and breached.
    base_portfolio.strategy_allocations = {"TF-01": Decimal("500.00")}
    result = check_strategy_margin_limit(
        base_portfolio, trade, market_context, base_config
    )
    assert result is not None
    assert result.status == RiskDecisionStatus.REJECT
    assert result.reason_code == RiskReasonCode.CONCENTRATION_BREACH


def test_verify_margin_limits_strategy_and_exit_breaches(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify verify_margin_limits surfaces strategy and exit-liquidity breaches."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
        price=Decimal("1.1000"),
    )

    # Strategy breach path (margin/leverage pass, strategy cap is tiny).
    base_portfolio.strategy_allocations = {"TF-01": Decimal("1.00")}
    res_strat = verify_margin_limits(base_portfolio, trade, market_context, base_config)
    assert res_strat.status == RiskDecisionStatus.REJECT
    assert res_strat.reason_code == RiskReasonCode.CONCENTRATION_BREACH

    # Exit-liquidity breach path (no strategy cap; extreme spread in context).
    base_portfolio.strategy_allocations = {}
    ctx_wide_spread = dict(market_context)
    ctx_wide_spread["EURUSD_spread"] = 0.05
    res_exit = verify_margin_limits(base_portfolio, trade, ctx_wide_spread, base_config)
    assert res_exit.status == RiskDecisionStatus.REJECT
    assert res_exit.reason_code == RiskReasonCode.MARGIN_BREACH
