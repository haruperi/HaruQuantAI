# ruff: noqa: E501, E402
"""Usage example script for app/services/risk.

Demonstrates typical workflows using the official risk contracts, profiles, and policy engine.
Each of the 20 examples corresponds to a specific risk module file, ordered by their real-life chronological execution.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.agentic.tools.risk import build_portfolio_risk_snapshot
from app.services.risk import (
    STAGE_SEQUENCE,
    AccountRiskSnapshot,
    ContractSpecification,
    DependencyStatus,
    DrawdownState,
    ExpectedShortfallMethod,
    InMemoryRiskStateStore,
    MarketRiskSnapshot,
    PolicyRule,
    PolicyScope,
    PortfolioState,
    PositionSizingRequest,
    PositionState,
    ProposedAllocation,
    ProposedTrade,
    ReadinessDeliveryPlan,
    ReturnType,
    RiskAction,
    RiskApprovalToken,
    RiskAssessmentRequest,
    RiskConfig,
    RiskDecisionPackage,
    RiskDecisionStatus,
    RiskGovernor,
    RiskMode,
    RiskModeMatrix,
    RiskReadinessManifest,
    RiskReasonCode,
    SizingMethod,
    SymbolRiskMetadata,
    VaRMethod,
    VolatilitySizingEngine,
    assess_risk_regime,
    build_default_scenario_registry,
    build_readiness_dry_run,
    calculate_correlation_snapshot,
    calculate_currency_exposure,
    calculate_daily_drawdown,
    calculate_fixed_risk_size,
    calculate_position_size,
    calculate_returns,
    calculate_total_drawdown,
    calculate_var_es_snapshots,
    correlation_adjusted_risk_parity_allocation,
    decompose_fx_trade,
    decompose_position,
    detect_correlation_spikes,
    determine_drawdown_throttling,
    equal_risk_allocation,
    evaluate_execution_feasibility,
    evaluate_lifecycle_promotion,
    evaluate_live_readiness,
    evaluate_margin_governance,
    evaluate_proposed_trade_correlation,
    exit_liquidity_stress_check,
    generate_risk_report,
    get_kill_switch_manager,
    parse_fx_symbol,
    run_limit_checks,
    validate_currency_conversion_requirements,
    validate_custom_scenario,
    validate_delivery_plan,
    validate_phase_dependencies,
    validate_risk_mode_matrix,
    verify_allocation_limits,
    verify_drawdown_limits,
    verify_execution_limits,
    verify_margin_limits,
    verify_risk_audit_chain,
    volatility_parity_allocation,
)
from app.services.risk.config import (
    compare_risk_config_hashes,
    hash_risk_config,
    load_risk_config,
    validate_risk_config,
    validate_risk_config_hash,
)
from app.services.risk.models.serialization import (
    from_canonical_risk_payload,
    to_canonical_risk_payload,
    validate_risk_model_round_trip,
)
from app.services.risk.policy import (
    RiskOverrideRequest,
    RiskPolicy,
    evaluate_risk_budget,
    requires_override_approval,
    resolve_effective_policy,
    validate_risk_override_request,
)
from app.services.risk.reports import RISK_METRICS_REGISTRY
from app.services.risk.stress import PriceShockScenario


def print_header(example_num: int, title: str) -> None:
    """Print the header for an example section."""
    print("\n" + "=" * 100)
    print(f"--- Example {example_num}: {title} ---")
    print("=" * 100)


# ==============================================================================
# PHASE 1: SETUP & CONFIGURATION (INITIALIZATION)
# ==============================================================================


def example_01_core_models_and_contracts() -> None:
    """Demonstrate creation, validation, and serialization of core risk models (models.py)."""
    print_header(1, "Core Models and Contracts")

    # 1. Enums
    print(f"Risk Decision Statuses: {list(RiskDecisionStatus)}")
    print(f"Risk Modes: {list(RiskMode)}")
    print(f"Risk Actions: {list(RiskAction)}")
    print(f"Risk Reason Codes: {list(RiskReasonCode)}")

    # 2. ProposedTrade validation
    trade = ProposedTrade(
        strategy_id="trend-following-v1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
    )
    print(f"\nProposedTrade instantiated: {trade.symbol} {trade.side} {trade.volume}")
    trade_json = trade.to_json()
    print(f"Serialized ProposedTrade:\n{trade_json[:120]}...")

    deserialized_trade = ProposedTrade.model_validate_json(trade_json)
    print(f"Deserialized successfully. Volume: {deserialized_trade.volume}")

    # 3. PositionState and PortfolioState
    position = PositionState(
        position_id="pos-001",
        symbol="EURUSD",
        direction="long",
        quantity=Decimal("0.10"),
        entry_price=Decimal("1.0850"),
        current_price=Decimal("1.0870"),
        floating_pnl=Decimal("20.00"),
        margin_required=Decimal("100.00"),
        strategy_id="trend-following-v1",
        open_time=datetime.now(UTC),
    )
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("10000.00"),
        equity=Decimal("10020.00"),
        margin_used=Decimal("100.00"),
        free_margin=Decimal("9920.00"),
        floating_pnl=Decimal("20.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[position],
    )
    print(
        f"\nPortfolioState: Balance={portfolio.balance}, Positions={len(portfolio.positions)}"
    )

    # 4. Snapshot structures
    account_snap = AccountRiskSnapshot(
        equity=portfolio.equity,
        balance=portfolio.balance,
        free_margin=portfolio.free_margin,
        margin_used=portfolio.margin_used,
        leverage=Decimal("30.0"),
        base_currency="USD",
        timestamp=datetime.now(UTC),
    )
    market_snap = MarketRiskSnapshot(
        spread=Decimal("0.0001"),
        volatility=Decimal("0.0050"),
        session="NY",
        freshness=datetime.now(UTC),
    )
    decision = RiskDecisionPackage(
        decision_id="dec-001",
        request_id="req-001",
        workflow_id="wf-001",
        status=RiskDecisionStatus.APPROVE,
        rule_key="rule-001",
        snapshot_as_of=datetime.now(UTC),
        config_hash="config-hash-001",
        reason="Limits cleared",
        calculated_volume=Decimal("0.10"),
    )
    print(
        f"Snapshots created: Base Currency={account_snap.base_currency}, Volatility={market_snap.volatility}, Decision Status={decision.status}"
    )

    # 5. Canonical Serialization & Round-trip Validation
    payload = to_canonical_risk_payload(decision)
    print(
        f"\nCanonical payload generated (calculated_volume is float): {payload.get('calculated_volume')} ({type(payload.get('calculated_volume')).__name__})"
    )

    restored_decision = from_canonical_risk_payload(payload, RiskDecisionPackage)
    print(
        f"Restored decision calculated_volume is Decimal: {restored_decision.calculated_volume} ({type(restored_decision.calculated_volume).__name__})"
    )

    rt_res = validate_risk_model_round_trip(decision)
    print(f"Round-trip validation result: {rt_res}")


def example_02_system_config_profiles() -> None:
    """Demonstrate configuration loading, profile validation, and config hashing (config.py)."""
    print_header(2, "System Configuration Profiles")

    # 1. Loading configs
    default_config = load_risk_config("default")
    print(
        f"Loaded 'default' profile. Daily loss limit: {default_config.max_daily_loss_pct}"
    )
    print(f"Default config hash: {default_config.contract_hash()}")

    prop_firm_config = load_risk_config("prop_firm_default")
    print(
        f"Loaded 'prop_firm_default' profile. Max leverage: {prop_firm_config.max_effective_leverage}"
    )

    # 2. Config Hashing
    config_hash = hash_risk_config(default_config)
    print(f"Hashed config: {config_hash}")

    # 3. Validate config
    validation_res = validate_risk_config(default_config)
    print(
        f"Validate config check: valid={validation_res['valid']}, message={validation_res['message']}"
    )

    # 4. Hash comparison & Validation
    paper_config = load_risk_config("paper")
    comparison = compare_risk_config_hashes(default_config, paper_config)
    print(
        f"Compare default vs paper: materially_changed={comparison.materially_changed}, changed_fields={comparison.changed_fields}"
    )

    hash_res = validate_risk_config_hash(config_hash, default_config)
    print(f"Validate config hash: valid={hash_res['valid']}, code={hash_res['code']}")


def example_03_policy_resolution_engine() -> None:
    """Demonstrate policy overrides precedence, override token verification, and safeguards (policy.py)."""
    print_header(3, "Policy Resolution Engine (V2)")

    # 1. Resolve Effective Policy from Policy Bundle
    now = datetime.now(UTC)
    base_policy = RiskPolicy(
        policy_id="pol-global",
        profile_name="default",
        rules=[
            PolicyRule(
                rule_id="rule-symbol-eurusd",
                scope=PolicyScope(symbol="EURUSD"),
                requires_approval=True,
                overrides={"max_daily_loss_pct": Decimal("0.06")},
            )
        ],
        provenance={
            "policy_version": "2.0.0",
            "policy_scope": {"environment": "local"},
        },
    )

    context = {
        "symbol": "EURUSD",
        "environment": "local",
    }

    effective_policy = resolve_effective_policy(context, [base_policy])
    print(f"Effective Policy resolved: {effective_policy.policy_id}")
    print(
        f"Resolved daily loss pct: {effective_policy.resolved_config.max_daily_loss_pct}"
    )
    print(f"Applied rules count: {len(effective_policy.applied_rules)}")

    # 2. Evaluate Risk Budget gates
    from app.services.risk.models import PortfolioState

    portfolio_state = PortfolioState(
        account_id="acc-001",
        balance=Decimal("10000.0"),
        equity=Decimal("10000.0"),
        margin_used=Decimal("0.0"),
        free_margin=Decimal("10000.0"),
        floating_pnl=Decimal("0.0"),
        realized_pnl=Decimal("0.0"),
        currency="USD",
        as_of=now,
    )
    req = RiskAssessmentRequest(
        strategy_id="strat-1",
        proposed_action=ProposedAllocation(
            allocations={"strat-1": Decimal("0.0001")}, as_of=now
        ),
        portfolio_state=portfolio_state,
        risk_config=effective_policy.resolved_config,
    )
    budget_result = evaluate_risk_budget(effective_policy, req)
    print(f"\nBudget gate evaluation status: {budget_result.status}")

    # 3. Check and validate a Limit Override Request
    token = RiskApprovalToken(
        token_id="tok-001",
        request_id="req-123",
        workflow_id="wf-123",
        approved_action="override",
        approver="risk_manager",
        expiry_time=now + timedelta(hours=1),
        config_hash=effective_policy.resolved_config.content_hash(),
        decision_hash="dec-123",
        nonce="nonce-123",
        signature="sig-123",
        scope={"symbol": "EURUSD"},
    )

    override_request = RiskOverrideRequest(
        request_id="req-123",
        token=token,
        target_overrides={"max_daily_loss_pct": Decimal("0.08")},
    )

    # Check if approval is required
    needs_approval = requires_override_approval(override_request, effective_policy)
    print(f"\nOverride requires approval: {needs_approval}")

    # Validate the override request
    validation = validate_risk_override_request(override_request, effective_policy)
    print(
        f"Override validation: valid={validation['valid']}, code={validation['code']}, msg={validation['message']}"
    )


# ==============================================================================
# PHASE 2: PRE-TRADE ANALYSIS & INPUTS
# ==============================================================================


def example_04_market_regime_classification() -> None:
    """Demonstrate volatility, spread, news calendar, and rollover blackout classifications (regime.py)."""
    print_header(4, "Market Regime Classification")

    base_config = load_risk_config("default")
    normal_snap = MarketRiskSnapshot(
        spread=Decimal("0.0002"),
        volatility=Decimal("0.0150"),
        session="NY",
        freshness=datetime.now(UTC),
    )

    # 1. Normal Case
    context_normal = {
        "spread_mean": 0.0002,
        "spread_std": 0.0001,
        "vol_short": 0.015,
        "vol_med": 0.015,
        "vol_long": 0.015,
        "tick_frequency": 30,
        "missing_bars": 0,
        "stale_seconds": 2,
    }
    result_normal = assess_risk_regime(normal_snap, [], base_config, context_normal)
    print(f"Normal Case Status: {result_normal.status} (expected APPROVE)")
    print(f"  Volatility Regime: {result_normal.volatility_regime}")

    # 2. Volatility Spike (short-term vol > 2x medium/long term)
    context_spike = {"vol_short": 0.025, "vol_med": 0.010, "vol_long": 0.010}
    result_spike = assess_risk_regime(normal_snap, [], base_config, context_spike)
    print(f"\nVolatility Spike Status: {result_spike.status} (expected REJECT)")
    print(f"  Reason: {result_spike.reason}")

    # 3. News Blackout Schedule
    now = datetime.now(UTC)
    calendar_news = [
        {"time": now + timedelta(minutes=2), "symbol": "EURUSD", "impact": "HIGH"}
    ]
    result_news = assess_risk_regime(
        normal_snap,
        calendar_news,
        base_config,
        {"symbol": "EURUSD", "news_blackout_mins": 5.0},
    )
    print(f"\nNews Blackout Status: {result_news.status} (expected REJECT)")
    print(f"  Reason: {result_news.reason}")

    # 4. Rollover Blackout
    rollover_snap = normal_snap.model_copy(
        update={"rollover_time": now + timedelta(minutes=2)}
    )
    result_rollover = assess_risk_regime(
        rollover_snap, [], base_config, {"rollover_blackout_before_mins": 5.0}
    )
    print(f"\nRollover Blackout Status: {result_rollover.status} (expected REJECT)")


def example_06_regime() -> None:
    """Demonstrate market regime assessors and validation rules (regime module)."""
    print_header(6, "Market Regime Gate & Assessors")

    base_config = load_risk_config("default")
    from app.services.risk.policy.contracts import EffectiveRiskPolicy

    policy = EffectiveRiskPolicy(
        policy_id="example-policy-id",
        resolved_config=base_config,
        policy_hash="example-policy-hash",
    )

    from app.services.risk.regime import (
        SpreadSigmaThresholds,
        VolatilityThresholds,
        classify_spread_regime,
        classify_volatility_regime,
        is_rollover_blackout,
        validate_market_freshness,
    )

    # 1. Spread regime classification directly
    spread_thresholds = SpreadSigmaThresholds(
        threshold_normal=Decimal("1.5"), threshold_wide=Decimal("3.0")
    )
    spread_status = classify_spread_regime(
        spread=Decimal("0.0004"),
        sigma=Decimal("0.0001"),
        thresholds=spread_thresholds,
        mean=Decimal("0.0002"),
    )
    print(f"Direct Spread Regime Class: {spread_status} (expected wide)")

    # 2. Volatility regime classification directly
    vol_thresholds = VolatilityThresholds(
        spike_multiplier=Decimal("2.0"),
        high_multiplier=Decimal("1.3"),
        low_multiplier=Decimal("0.5"),
    )
    vol_status = classify_volatility_regime(
        short_sigma=Decimal("0.025"),
        medium_sigma=Decimal("0.010"),
        long_sigma=Decimal("0.010"),
        thresholds=vol_thresholds,
    )
    print(f"Direct Volatility Regime Class: {vol_status} (expected spike)")

    # 3. Freshness validation
    snap = MarketRiskSnapshot(
        spread=Decimal("0.0002"),
        volatility=Decimal("0.0150"),
        session="NY",
        freshness=datetime.now(UTC) - timedelta(seconds=120),
    )
    fresh_res = validate_market_freshness(
        snap, policy, datetime.now(UTC), {"max_stale_seconds": 60}
    )
    print(
        f"Freshness check with 120s old data: valid={fresh_res['valid']} "
        f"(expected False)"
    )

    # 4. UTC Rollover blackout window check
    now = datetime.now(UTC)
    rollover_status = is_rollover_blackout(now, policy)
    print(f"Is currently in rollover blackout: {rollover_status}")


def example_05_portfolio_correlation_dynamics() -> None:
    """Demonstrate returns calculation, alignment, correlation matrix estimation, and proposed trade impacts (correlation.py)."""
    print_header(5, "Portfolio Correlation Dynamics")

    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    bars_a = [
        {"time": base_time + timedelta(minutes=i), "open": 100 + i, "close": 101 + i}
        for i in range(10)
    ]
    bars_b = [
        {
            "time": base_time + timedelta(minutes=i),
            "open": 200 + 2 * i,
            "close": 202 + 2 * i,
        }
        for i in range(10)
    ]

    # 1. Returns calculation
    rets_a = calculate_returns(bars_a, ReturnType.CLOSE_TO_CLOSE, exclude_last=False)
    print(f"Calculated {len(rets_a)} returns for asset A.")

    # 2. Correlation Matrix Snapshot
    snapshot = calculate_correlation_snapshot(
        {"EURUSD": bars_a, "GBPUSD": bars_b}, min_samples=2, exclude_last=False
    )
    print("\nCorrelation Matrix Snapshot:")
    for sym1, row in snapshot.matrix.items():
        for sym2, val in row.items():
            print(f"  Corr({sym1}, {sym2}): {val:.4f}")

    # 3. Detect Spikes
    spikes = detect_correlation_spikes(snapshot, Decimal("0.80"))
    print(f"Correlation Spikes (>0.80): {spikes}")

    # 4. Marginal Correlation Impact on Proposed Trade
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-1",
                symbol="EURUSD",
                direction="long",
                quantity=Decimal("1.0"),
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1000"),
                floating_pnl=Decimal("0.0"),
                margin_required=Decimal("1000.0"),
                strategy_id="strat-1",
                open_time=datetime.now(UTC),
            )
        ],
    )
    market_context = {
        "EURUSD_contract_size": 100000.0,
        "GBPUSD_contract_size": 100000.0,
        "conversion_rates": {"EUR": 1.10, "GBP": 1.25, "USD": 1.0},
        "market_data": {"EURUSD": bars_a, "GBPUSD": bars_b},
        "GBPUSD_volume_step": 0.01,
    }
    proposed = ProposedTrade(
        strategy_id="strat-1",
        symbol="GBPUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.2500"),
    )
    config = RiskConfig(
        profile_name="usage_profile", correlation_threshold=Decimal("0.50")
    )

    status, vol, msg = evaluate_proposed_trade_correlation(
        proposed_trade=proposed,
        portfolio_state=portfolio,
        snapshot=snapshot,
        config=config,
        market_context=market_context,
    )
    print("\nProposed Trade Correlation Evaluation:")
    print(f"  Status: {status}, Adjusted Volume: {vol:.2f}, Reason: {msg}")

    # 5. Demonstrate new V2 Correlation Engine functions
    from app.services.risk.correlation.contracts import (
        ClosedBar,
        CorrelationAlignmentPolicy,
        CorrelationFallbackContext,
        CorrelationMethod,
        ReturnMethod,
    )
    from app.services.risk.correlation.engine import (
        build_correlation_clusters,
        calculate_cluster_exposure,
        calculate_correlation_matrix,
    )
    from app.services.risk.correlation.fallbacks import resolve_correlation_fallback
    from app.services.risk.correlation.returns import (
        align_return_series,
        build_return_series,
        validate_correlation_inputs,
    )

    print("\n[V2] Correlation Engine calculations:")
    # Build ClosedBar models
    v2_bars_a = [
        ClosedBar(
            time=b["time"], open=Decimal(str(b["open"])), close=Decimal(str(b["close"]))
        )
        for b in bars_a
    ]
    v2_bars_b = [
        ClosedBar(
            time=b["time"], open=Decimal(str(b["open"])), close=Decimal(str(b["close"]))
        )
        for b in bars_b
    ]

    series_a = build_return_series(v2_bars_a, ReturnMethod.CLOSE_TO_CLOSE)
    series_b = build_return_series(v2_bars_b, ReturnMethod.CLOSE_TO_CLOSE)

    series_map = {"EURUSD": series_a, "GBPUSD": series_b}
    aligned_v2 = align_return_series(series_map, CorrelationAlignmentPolicy.INTERSECT)
    print(f"  [V2] Aligned timestamps count: {len(aligned_v2.timestamps)}")

    val_res = validate_correlation_inputs(aligned_v2, minimum_samples=5)
    print(f"  [V2] Input validation: valid={val_res['valid']}")

    matrix_v2 = calculate_correlation_matrix(aligned_v2, CorrelationMethod.PEARSON)
    print(f"  [V2] Matrix correlation: {matrix_v2.matrix['EURUSD']['GBPUSD']:.4f}")

    clusters_v2 = build_correlation_clusters(matrix_v2, threshold=Decimal("0.50"))
    print(f"  [V2] Correlation clusters: {[c.symbols for c in clusters_v2]}")

    exposures_v2 = {"EURUSD": Decimal("110000.0"), "GBPUSD": Decimal("125000.0")}
    c_exp_v2 = calculate_cluster_exposure(clusters_v2, exposures_v2)
    print(f"  [V2] Cluster exposures: {dict(c_exp_v2.exposures)}")

    fallback_ctx = CorrelationFallbackContext(
        symbols=["EURUSD", "GBPUSD"], mode="paper", sample_count=2, minimum_samples=10
    )
    fallback_res = resolve_correlation_fallback(fallback_ctx, config)
    print(
        f"  [V2] Fallback matrix resolved under paper mode: EURUSD-GBPUSD corr={fallback_res.matrix['EURUSD']['GBPUSD']:.2f}"
    )


def example_06_value_at_risk_and_expected_shortfall() -> None:
    """Demonstrate Parametric & Historical Value-at-Risk (VaR) and Expected Shortfall (ES) (var_es.py)."""
    print_header(6, "Value-at-Risk and Expected Shortfall")

    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    bars_a = []
    price_a = 100.0
    for i in range(25):
        change = 1.0 if i % 2 == 0 else -1.5
        price_a += change
        bars_a.append(
            {
                "time": base_time + timedelta(minutes=i),
                "open": price_a - change,
                "close": price_a,
            }
        )

    bars_b = []
    price_b = 200.0
    for i in range(25):
        change = 2.0 if i % 2 == 0 else -3.0
        price_b += change
        bars_b.append(
            {
                "time": base_time + timedelta(minutes=i),
                "open": price_b - change,
                "close": price_b,
            }
        )

    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-1",
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
    )
    market_context = {
        "EURUSD_contract_size": 100000.0,
        "GBPUSD_contract_size": 100000.0,
        "conversion_rates": {"EUR": 1.10, "GBP": 1.25, "USD": 1.0},
        "market_data": {"EURUSD": bars_a, "GBPUSD": bars_b},
    }
    config = RiskConfig(profile_name="usage_profile")

    # 1. Parametric VaR / ES via V2 snapshots helper
    var_snap, es_snap = calculate_var_es_snapshots(
        portfolio_state=portfolio,
        proposed_trade=None,
        market_context=market_context,
        config=config,
        var_confidence=Decimal("0.95"),
        es_confidence=Decimal("0.95"),
        var_method=VaRMethod.PARAMETRIC,
        es_method=ExpectedShortfallMethod.PARAMETRIC,
        min_samples=10,
        exclude_last=False,
    )
    print("Parametric metrics (95% confidence):")
    print(f"  Portfolio Volatility: {var_snap.portfolio_volatility:.6f}")
    print(f"  Parametric VaR: {var_snap.result:.2f} USD")
    print(f"  Parametric ES: {es_snap.average_tail_loss:.2f} USD")

    # 2. Historical VaR / ES via V2 snapshots helper
    var_hist, es_hist = calculate_var_es_snapshots(
        portfolio_state=portfolio,
        proposed_trade=None,
        market_context=market_context,
        config=config,
        var_confidence=Decimal("0.95"),
        es_confidence=Decimal("0.95"),
        var_method=VaRMethod.HISTORICAL,
        es_method=ExpectedShortfallMethod.HISTORICAL,
        min_samples=10,
        exclude_last=False,
    )
    print(f"\nHistorical VaR: {var_hist.result:.2f} USD")
    print(f"Historical ES: {es_hist.average_tail_loss:.2f} USD")

    # 3. [V2 Pure API] Parametric & Historical calculators using Request Contracts
    from app.services.risk.tail_risk.contracts import (
        ExpectedShortfallRequest,
        VaRCalculationRequest,
    )
    from app.services.risk.tail_risk.expected_shortfall import (
        calculate_expected_shortfall,
    )
    from app.services.risk.tail_risk.var import (
        calculate_historical_var,
        calculate_parametric_var,
        calculate_var_component_contribution,
    )

    var_req = VaRCalculationRequest(
        portfolio_state=portfolio,
        market_context=market_context,
        proposed_trade=None,
        lookback=15,
        confidence=Decimal("0.95"),
        method=VaRMethod.PARAMETRIC,
        cov_method="parametric",
        min_samples=10,
        exclude_last=False,
    )
    v2_var_parametric = calculate_parametric_var(var_req)
    print(
        f"\n[V2 Pure API] Parametric VaR Snapshot Result: {v2_var_parametric.result:.2f} USD"
    )

    var_req_hist = VaRCalculationRequest(
        portfolio_state=portfolio,
        market_context=market_context,
        proposed_trade=None,
        lookback=15,
        confidence=Decimal("0.95"),
        method=VaRMethod.HISTORICAL,
        min_samples=10,
        exclude_last=False,
    )
    v2_var_historical = calculate_historical_var(var_req_hist)
    print(
        f"[V2 Pure API] Historical VaR Snapshot Result: {v2_var_historical.result:.2f} USD"
    )

    es_req = ExpectedShortfallRequest(
        portfolio_state=portfolio,
        market_context=market_context,
        proposed_trade=None,
        lookback=15,
        confidence=Decimal("0.95"),
        method=ExpectedShortfallMethod.HISTORICAL,
        min_samples=10,
        exclude_last=False,
    )
    v2_es = calculate_expected_shortfall(es_req)
    print(
        f"[V2 Pure API] Expected Shortfall Snapshot Result: {v2_es.average_tail_loss:.2f} USD"
    )

    # Component contributions
    contribs = calculate_var_component_contribution(var_req)
    print(f"[V2 Pure API] Component Contributions: {contribs.contributions}")

    # 4. [V2 Engine API] Using PortfolioVaREngine and ExpectedShortfallEngine wrappers
    from app.services.risk.tail_risk.expected_shortfall import ExpectedShortfallEngine
    from app.services.risk.tail_risk.var import PortfolioVaREngine

    var_engine = PortfolioVaREngine(config)
    legacy_var_res = var_engine.calculate_var(
        portfolio_state=portfolio,
        market_context=market_context,
        lookback=15,
        confidence=Decimal("0.95"),
        method="parametric",
        min_samples=10,
        exclude_last=False,
    )
    print(
        f"\n[V2 Engine API] PortfolioVaREngine Result: {legacy_var_res.result:.2f} USD"
    )

    es_engine = ExpectedShortfallEngine(config)
    legacy_es_res = es_engine.calculate_es(
        portfolio_state=portfolio,
        market_context=market_context,
        lookback=15,
        confidence=Decimal("0.95"),
        method="historical",
        min_samples=10,
        exclude_last=False,
    )
    print(
        f"[V2 Engine API] ExpectedShortfallEngine Result: {legacy_es_res.average_tail_loss:.2f} USD"
    )


def example_07_portfolio_stress_scenario_testing() -> None:
    """Demonstrate portfolio stress scenario evaluations and custom scenario verification (stress.py)."""
    print_header(7, "Portfolio Stress Scenario Testing")

    # 1. Load default scenario registry
    registry = build_default_scenario_registry()
    print(f"Registry initialized with {len(registry.scenarios)} scenarios.")

    # 2. Setup portfolio with positions
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("2000.00"),
        free_margin=Decimal("8000.00"),
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
                floating_pnl=Decimal("0.00"),
                margin_required=Decimal("1000.00"),
                strategy_id="TF-01",
                open_time=datetime.now(UTC),
            )
        ],
    )
    market_context = {
        "EURUSD_contract_size": 100000.0,
        "EURUSD_pip_size": 0.0001,
        "EURUSD_spread": 0.0002,
        "EURUSD_volatility": Decimal("0.015"),
        "conversion_rates": {"EUR": 1.10, "USD": 1.0},
        "quote_age_stale": False,
    }
    config = RiskConfig(
        profile_name="usage_profile",
        max_daily_loss_pct=Decimal("0.05"),
        max_total_loss_pct=Decimal("0.10"),
    )

    # 3. Evaluate portfolio
    results = registry.evaluate_portfolio(portfolio, None, market_context, config)
    for res in results[:3]:  # Print first 3 default scenarios
        status_str = "PASS" if res.pass_status else "FAIL"
        print(
            f"  Scenario: {res.scenario_name:<20} | Status: {status_str:<4} | Loss Impact: {res.impact_pct * 100:>6.2f}%"
        )

    # 4. Custom scenario validation
    custom_config = {
        "name": "Custom EUR Crash",
        "price_shocks": {"EURUSD": -0.08},
    }
    custom_scenario = validate_custom_scenario(custom_config)
    print(f"\nValidated custom scenario: {custom_scenario.name}")

    # Run custom scenario evaluation
    custom_shock = PriceShockScenario(
        custom_scenario.name, custom_scenario.price_shocks
    )
    res_custom = custom_shock.evaluate(portfolio, None, market_context, config)
    print(
        f"  Evaluation result - Projected Equity: {res_custom.projected_equity:.2f} USD (Impact: {res_custom.impact_pct * 100:.2f}%)"
    )

    # 5. Demonstrate new V2 Declarative Stress Engine APIs
    from app.services.risk.policy.contracts import EffectiveRiskPolicy
    from app.services.risk.stress import StressScenarioRegistry
    from app.services.risk.stress.contracts import StressContext, StressScenario
    from app.services.risk.stress.engine import evaluate_stress_scenarios

    print("\n[V2] Declarative Stress Engine evaluation:")
    v2_registry = StressScenarioRegistry()
    # Register V2 declarative stress scenario
    v2_scenario = StressScenario(
        scenario_id="extreme_eur_down_v2",
        name="EURUSD Down 10%",
        price_shocks={"EURUSD": Decimal("-0.10")},
    )
    v2_registry.scenarios[v2_scenario.scenario_id] = v2_scenario

    v2_context = StressContext(
        portfolio_state=portfolio,
        proposed_trade=None,
        market_context=market_context,
    )
    v2_policy = EffectiveRiskPolicy(
        policy_id="v2_usage_policy",
        resolved_config=config,
        policy_hash="default_hash",
    )
    v2_summary = evaluate_stress_scenarios(
        context=v2_context,
        registry=v2_registry,
        policy=v2_policy,
    )
    print(f"  V2 evaluation summary status: {v2_summary.pass_status}")
    for res_v2 in v2_summary.results:
        print(
            f"  V2 Scenario: {res_v2.scenario_name:<20} | Pass: {res_v2.pass_status:<5} | Loss: {res_v2.impact_pct * 100:.2f}%"
        )


# ==============================================================================
# PHASE 3: ALLOCATION & LIFECYCLE
# ==============================================================================


def example_08_risk_budgeting_allocation() -> None:
    """Demonstrate Capital Allocation Parity and budget limits checking (allocation.py)."""
    print_header(8, "Capital Allocation and Risk Budgeting")

    strategies = ["strat1", "strat2", "strat3"]
    vols = {
        "strat1": Decimal("0.015"),
        "strat2": Decimal("0.025"),
        "strat3": Decimal("0.020"),
    }
    correlation_matrix = {
        "strat1": {"strat2": Decimal("0.50"), "strat3": Decimal("0.30")},
        "strat2": {"strat1": Decimal("0.50"), "strat3": Decimal("0.40")},
        "strat3": {"strat1": Decimal("0.30"), "strat2": Decimal("0.40")},
    }
    total_budget = Decimal("10000.00")

    # 1. Budgeting Calculations
    equal_allocs = equal_risk_allocation(strategies, total_budget)
    vol_parity_allocs = volatility_parity_allocation(strategies, vols, total_budget)
    corr_parity_allocs = correlation_adjusted_risk_parity_allocation(
        strategies, vols, correlation_matrix, total_budget
    )

    print("Allocation budgets:")
    print(f"  Equal Risk Alloc: {equal_allocs}")
    print(f"  Vol Parity Alloc: {vol_parity_allocs}")
    print(f"  Correlation Parity Alloc: {corr_parity_allocs}")

    # 2. Verify Allocation Limits
    portfolio = PortfolioState(
        account_id="acc-alloc-demo",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        strategy_allocations={
            "strat1": Decimal("3000.00"),
            "strat2": Decimal("3000.00"),
        },
    )
    config = RiskConfig(
        profile_name="usage_profile",
        max_allocation_increase_pct=Decimal("0.20"),
        max_strategy_allocation_pct=Decimal("0.50"),
    )
    # strat1 from 3000 to 4500 is +50% increase (exceeds max_allocation_increase_pct = 0.20)
    proposal = ProposedAllocation(
        allocations={"strat1": Decimal("4500.00"), "strat2": Decimal("3000.00")},
        as_of=datetime.now(UTC),
    )
    alloc_res = verify_allocation_limits(portfolio, proposal, {}, config)
    print(
        f"\nAllocation Limit Verification: Status={alloc_res.status}, Message={alloc_res.message}"
    )


def example_09_strategy_lifecycle_promotion() -> None:
    """Demonstrate strategy staging sequence, walk-forward gates, and live readiness checks (lifecycle.py)."""
    print_header(9, "Strategy Lifecycle Promotion")

    print(f"Lifecycle Staging Sequence: {STAGE_SEQUENCE}")

    config = RiskConfig(
        profile_name="usage_profile",
        min_backtest_trades=100,
        min_backtest_sharpe=Decimal("1.5"),
    )

    # 1. Lifecycle Promotion Check
    promotion_pass = evaluate_lifecycle_promotion(
        "strat1",
        "backtest",
        "walk-forward",
        {
            "trade_count": 120,
            "sharpe_ratio": Decimal("1.7"),
            "max_drawdown": Decimal("0.10"),
        },
        config,
    )
    print(f"Promotion (Backtest -> Walk-Forward): Status={promotion_pass.status}")

    promotion_fail = evaluate_lifecycle_promotion(
        "strat1",
        "backtest",
        "simulation",  # Skip walk-forward -> should fail
        {},
        config,
    )
    print(
        f"Promotion (Backtest -> Simulation directly): Status={promotion_fail.status}, Message={promotion_fail.message}"
    )

    # 2. Live shadow readiness checks
    readiness_res = evaluate_live_readiness(
        "strat1",
        "shadow",
        {
            "audit_persistence_active": True,
            "kill_switch_configured": True,
            "portfolio_reconciliation_active": True,
            "idempotency_evidence_present": True,
        },
        config,
    )
    print(
        f"Live readiness review: Status={readiness_res.status}, Message={readiness_res.message}"
    )


# ==============================================================================
# PHASE 4: TRADE EXECUTION GATE (PRE-TRADE DECISION)
# ==============================================================================


def example_10_position_sizing_engines() -> None:
    """Demonstrate position sizing engines under fixed risk and volatility structures (sizing.py)."""
    print_header(10, "Position Sizing Engines")

    base_config = load_risk_config("default")
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    eurusd_context = {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "contract_size": 100000.0,
        "digits": 5,
        "tick_size": 0.00001,
        "tick_value": 1.0,
        "conversion_rate": 1.0,
    }

    # 1. Fixed Risk Sizing (2% risk, 20 pips stop distance) -> expected 10.0 lots
    req_fixed = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )
    res_fixed = calculate_position_size(
        req_fixed, portfolio, eurusd_context, base_config
    )
    print(
        f"Fixed Risk (2%): Calculated Volume={res_fixed.calculated_volume} lots, Risk={res_fixed.risk_contribution} USD"
    )

    # 2. Volatility Adjusted Sizing (ATR based stop distance)
    req_vol = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED,
        atr_value=Decimal("0.00100"),
        multiplier=Decimal("2.0"),
        risk_percent=Decimal("0.02"),
    )
    res_vol = calculate_position_size(req_vol, portfolio, eurusd_context, base_config)
    print(
        f"Volatility-Adjusted: Calculated Volume={res_vol.calculated_volume} lots, Stop Distance (pips)={res_vol.stop_distance_pips}"
    )

    # 3. VolatilitySizingEngine Class coordinator
    engine = VolatilitySizingEngine(base_config)
    res_engine = engine.calculate_position_size(req_fixed, portfolio, eurusd_context)
    print(
        f"VolatilitySizingEngine: Calculated Volume={res_engine.calculated_volume} lots, Risk={res_engine.risk_contribution} USD"
    )

    # 4. Pure Stateless Calculator direct call
    symbol_metadata = SymbolRiskMetadata(
        symbol="EURUSD",
        volume_min=Decimal(str(eurusd_context["volume_min"])),
        volume_max=Decimal(str(eurusd_context["volume_max"])),
        volume_step=Decimal(str(eurusd_context["volume_step"])),
        contract_size=Decimal(str(eurusd_context["contract_size"])),
        digits=int(eurusd_context["digits"]),
        tick_size=Decimal(str(eurusd_context["tick_size"])),
        tick_value=Decimal(str(eurusd_context["tick_value"])),
        conversion_rate=Decimal(str(eurusd_context["conversion_rate"])),
    )
    res_pure = calculate_fixed_risk_size(
        request=req_fixed,
        portfolio_equity=portfolio.equity,
        symbol_metadata=symbol_metadata,
        config=base_config,
        drawdown_step_down_multiplier=Decimal("1.0"),
        currency_exposure_reduction=Decimal("1.0"),
        correlation_cluster_reduction=Decimal("1.0"),
        market_context=eurusd_context,
    )
    print(
        f"Pure calculate_fixed_risk_size: Calculated Volume={res_pure.calculated_volume} lots, Risk={res_pure.risk_contribution} USD"
    )


def example_11_fx_currency_and_cluster_exposures() -> None:
    """Demonstrate fx leg decomposition, cluster exposure, and pending order potential calculation (exposure.py)."""
    print_header(11, "FX Currency and Cluster Exposures")

    base_config = load_risk_config("default")
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-101",
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
        ],
        orders=[
            {
                "symbol": "EURUSD",
                "side": "buy",
                "quantity": 1.0,
                "price": 1.09,
                "distance_pips": 100.0,
                "probability": 0.3,
                "status": "active",
            }
        ],
    )
    market_context = {
        "EURUSD_contract_size": 100000.0,
        "EURUSD_price": 1.10,
        "mode": RiskMode.PAPER,
        "conversion_rates": {"EUR": 1.10, "USD": 1.0},
    }

    # 1. Leg Decomposition (EURUSD Buy 1.0 lot)
    legs = decompose_position(
        "EURUSD",
        "buy",
        Decimal("1.0"),
        Decimal("1.10"),
        Decimal("100000.0"),
        "EUR",
        "USD",
    )
    print("FX Legs decomposition:")
    for leg in legs:
        print(f"  Currency: {leg.currency}, Signed Amount: {leg.signed_amount}")

    # V2 Symbol parsing example
    fx_pair = parse_fx_symbol("EUR_USD")
    print(f"\nParsed base/quote from EUR_USD: {fx_pair.base}/{fx_pair.quote}")

    # V2 Trade decomposition example
    proposed = ProposedTrade(
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.5"),
        strategy_id="strat-1",
        price=Decimal("1.10"),
    )
    contract_spec = ContractSpecification(
        symbol="EURUSD", contract_size=Decimal("100000.0")
    )
    v2_legs = decompose_fx_trade(proposed, Decimal("1.10"), contract_spec)
    print("V2 Decomposed ProposedTrade Legs:")
    for leg in v2_legs:
        print(f"  Currency: {leg.currency}, Signed Amount: {leg.signed_amount}")

    # V2 Validation of conversion requirements
    conversion_validation = validate_currency_conversion_requirements(
        v2_legs, {"EURUSD": Decimal("1.10")}, "USD"
    )
    print(f"Currency conversion validation result: {conversion_validation['reason']}")

    # 2. Currency Exposure Calculations (ignore pending order vs full potential)
    base_config.pending_order_policy = "ignore"
    exp_ignore = calculate_currency_exposure(
        portfolio, None, base_config, market_context
    )
    print(f"\nIgnore pending orders - EUR Net Exposure: {exp_ignore['EUR'].net} USD")

    base_config.pending_order_policy = "full-potential"
    exp_full = calculate_currency_exposure(portfolio, None, base_config, market_context)
    print(f"Full-potential orders  - EUR Net Exposure: {exp_full['EUR'].net} USD")


def example_12_deterministic_limits_governance() -> None:
    """Demonstrate checking deterministic limits and resolving composite/multiple breach statuses (limits.py)."""
    print_header(12, "Deterministic Limits Governance")

    base_config = load_risk_config("default")
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("1000.00"),
        free_margin=Decimal("99000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    trade = ProposedTrade(
        strategy_id="strat-1", symbol="EURUSD", side="buy", volume=Decimal("0.10")
    )

    # Context setup
    request = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=base_config,
        calendar_evidence=[],
        market_context={
            "kill_switch_active": False,
            "freshness": datetime.now(UTC),
            "daily_loss_pct": 0.0,
            "mode": RiskMode.PAPER,
            "portfolio_gross_exposure": 100000.0,
            "max_portfolio_exposure": 5.0,
        },
    )

    # 1. Normal limit pass checks
    status, code, _msg, flags, primary, _ = run_limit_checks(request, base_config)
    print(f"Normal Case Status: {status} (expected APPROVE), Reason Code: {code}")

    # 2. Composite breaches check (exposure breach + daily loss breach + kill switch)
    request.market_context["portfolio_gross_exposure"] = 600000.0
    request.market_context["daily_loss_pct"] = 0.06
    request.market_context["kill_switch_active"] = True
    status, code, _msg, flags, primary, _ = run_limit_checks(request, base_config)
    print(
        f"\nComposite Breach Status: {status} (expected BLOCK), Breached flags: {flags}"
    )
    print(f"  Primary failure resolved: {primary!r}")


def example_13_margin_liquidity_and_leverage_limits() -> None:
    """Demonstrate margin requirement projections, leverage limitations, and exit liquidity stress check (margin.py)."""
    print_header(13, "Margin, Liquidity, and Leverage Limits")

    portfolio = PortfolioState(
        account_id="acc-13",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("1000.00"),
        free_margin=Decimal("9000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )
    market_context = {
        "EURUSD_contract_size": 100000.0,
        "EURUSD_spread": 0.0002,
        "conversion_rates": {"EUR": 1.10, "USD": 1.0},
    }
    config = RiskConfig(
        profile_name="usage_profile",
        max_margin_utilization_pct=Decimal("0.80"),
        max_effective_leverage=Decimal("30.0"),
    )

    # 1. Margin Governance Calculation
    margin_snap = evaluate_margin_governance(portfolio, trade, market_context, config)
    print(
        f"Projected Margin: {margin_snap.projected_margin:.2f} USD, Margin Usage: {margin_snap.margin_usage:.2%}"
    )
    print(f"Effective Leverage: {margin_snap.leverage:.2f}")

    margin_limits_res = verify_margin_limits(portfolio, trade, market_context, config)
    print(
        f"Margin Limits status check: Status={margin_limits_res.status}, Breached={margin_limits_res.breached}"
    )

    # 2. Exit Liquidity stress check
    pass_liquid, est_loss = exit_liquidity_stress_check(
        portfolio, trade, market_context, config, spread_multiplier=Decimal("5.0")
    )
    print(
        f"Exit Liquidity stress (5x spread): Pass={pass_liquid}, Loss={est_loss:.2f} USD"
    )


def example_14_drawdown_governor_and_throttling() -> None:
    """Demonstrate drawdown computation and dynamic risk throttling logic (drawdown.py)."""
    print_header(14, "Drawdown Governor and Throttling")

    portfolio = PortfolioState(
        account_id="acc-14",
        balance=Decimal("10000.00"),
        equity=Decimal("9500.00"),  # 5% paper loss
        margin_used=Decimal("0.00"),
        free_margin=Decimal("9500.00"),
        floating_pnl=Decimal("-500.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    market_context = {
        "peak_balance": 10500.00
    }  # Peak from which total drawdown is calculated
    config = RiskConfig(
        profile_name="usage_profile",
        max_total_loss_pct_advisory=Decimal("0.05"),
        max_total_loss_pct=Decimal("0.10"),
    )

    # 1. Drawdown calculations
    daily_dd = calculate_daily_drawdown(
        portfolio, Decimal("10000.00")
    )  # Peak balance today
    total_dd = calculate_total_drawdown(
        portfolio, Decimal(str(market_context["peak_balance"]))
    )
    print(
        f"Daily Drawdown: {daily_dd:.2%}, Peak-to-Trough Total Drawdown: {total_dd:.2%}"
    )

    # 2. Check throttling transition state
    state, multiplier = determine_drawdown_throttling(
        total_dd, config.max_total_loss_pct_advisory, config.max_total_loss_pct
    )
    print(f"Drawdown Throttling: State={state.value}, Multiplier enforced={multiplier}")

    drawdown_limits_res = verify_drawdown_limits(
        portfolio,
        ProposedTrade(
            strategy_id="TF-01", symbol="EURUSD", side="buy", volume=Decimal("1.0")
        ),
        {"peak_balance": 10500.00},
        config,
    )
    print(
        f"Drawdown Limits verification result: Status={drawdown_limits_res.status}, Reason={drawdown_limits_res.reason_code}"
    )


def example_15_execution_gate_and_broker_feasibility() -> None:
    """Demonstrate pre-trade broker constraints, slippage limits, stop distances, and spread validations (execution_gate.py)."""
    print_header(15, "Execution Gate and Broker Feasibility")

    portfolio = PortfolioState(
        account_id="acc-15",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    trade = ProposedTrade(
        strategy_id="strat-15",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )
    market_context = {
        "EURUSD_contract_size": 100000.0,
        "EURUSD_pip_size": 0.0001,
        "EURUSD_spread": 0.0002,
        "EURUSD_volatility": Decimal("0.0001"),
        "EURUSD_slippage_limit": 3.0,
        "EURUSD_stop_level": 5.0,
        "EURUSD_freeze_level": 2.0,
        "EURUSD_volume_min": Decimal("0.01"),
        "EURUSD_volume_max": Decimal("100.0"),
        "EURUSD_volume_step": Decimal("0.01"),
        "session": "OPEN",
        "historical_avg_volume": 2.0,
        "spread_sigma_multiplier": 3.0,
        "slippage_sigma_multiplier": 3.0,
    }
    config = RiskConfig(
        profile_name="usage_profile", max_risk_per_trade=Decimal("0.02")
    )

    # 1. Evaluate execution feasibility
    exec_snap = evaluate_execution_feasibility(portfolio, trade, market_context, config)
    print(f"Marketability (session open): {exec_snap.marketability}")
    print(f"Calculated slippage allowance: {exec_snap.slippage:.5f} (Quote currency)")

    # 2. Verify constraints
    limits_res = verify_execution_limits(portfolio, trade, market_context, config)
    print(
        f"Execution Gate Verification: Status={limits_res.status}, Reason={limits_res.reason_code}"
    )


# ==============================================================================
# PHASE 5: POST-TRADE, AUDIT & CONTROL
# ==============================================================================


def example_16_risk_governor_orchestration() -> None:
    """Demonstrate governor coordination of risk check pipeline and allocation/admission reviews (governor.py)."""
    print_header(16, "Risk Governor Orchestration")

    # Initialize Governor with storage ports
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    trade = ProposedTrade(
        strategy_id="strat_1", symbol="EURUSD", side="buy", volume=Decimal("0.1")
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={"mode": "paper", "environment": "local"},
    )
    req.request_id = "req_gov_demo"

    # Orchestrated trade review
    decision = gov.review_trade_risk(req)
    print(
        f"Governor Trade Review Status: {decision.status} (Reason: {decision.reason})"
    )
    print(f"  Calculated approved volume: {decision.calculated_volume}")


def example_17_kill_switch_halting_protocols() -> None:
    """Demonstrate manual halts, hierarchical checking, and token validation triggers (kill_switch.py)."""
    print_header(17, "Kill Switch Halting Protocols")

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        persistence_path = Path(tmpdir) / "kill_switch_state.json"
        manager = get_kill_switch_manager(persistence_path=persistence_path)

        # 1. Trigger symbol halt
        print("Triggering symbol kill switch on GBPUSD...")
        manager.trigger(
            scope="symbol",
            target="GBPUSD",
            reason="Excessive volatility spike",
            triggered_by="operator_01",
        )
        print(f"  Is GBPUSD blocked? {manager.is_blocked('symbol', 'GBPUSD')}")
        print(f"  Is EURUSD blocked? {manager.is_blocked('symbol', 'EURUSD')}")

        # 2. Trigger global halt
        print("Triggering global switch...")
        manager.trigger(
            scope="global",
            target="*",
            reason="System maintenance shutdown",
            triggered_by="admin_01",
        )
        print(
            f"  Is EURUSD blocked now (hierarchical)? {manager.is_blocked('symbol', 'EURUSD')}"
        )

        # 3. Resume switch with admin credentials
        manager.resume(scope="global", target="*", operator_role="admin")
        print(
            f"  Is EURUSD blocked after global resume? {manager.is_blocked('symbol', 'EURUSD')}"
        )
        print(f"  Is GBPUSD still blocked? {manager.is_blocked('symbol', 'GBPUSD')}")

        # Reset states for cleanup
        manager.resume(scope="symbol", target="GBPUSD", operator_role="admin")


def example_18_state_persistence_stores() -> None:
    """Demonstrate state save, retrieve, token revocation, and policy persistence checks (storage.py)."""
    print_header(18, "State Persistence Stores")

    store = InMemoryRiskStateStore()

    # 1. Save and retrieve drawdown state
    state = DrawdownState(
        current_drawdown=Decimal("0.05"),
        soft_limit=Decimal("0.05"),
        hard_limit=Decimal("0.10"),
        multiplier=Decimal("1.0"),
    )
    store.save_drawdown_state(state, strategy_id="strat_demo")
    loaded_state = store.get_drawdown_state(strategy_id="strat_demo")
    print(
        f"Saved and retrieved DrawdownState. Current drawdown: {loaded_state.current_drawdown if loaded_state else None}"
    )

    # 2. Token Revocation Check
    store.revoke_token("tok-12345")
    print(
        f"Revoked token state check: is tok-12345 revoked? {store.is_token_revoked('tok-12345')}"
    )
    print(
        f"Is unrevoked token tok-99999 revoked? {store.is_token_revoked('tok-99999')}"
    )

    # 3. Policy Persistence
    rule = PolicyRule(
        rule_id="rule_storage_test",
        scope=PolicyScope(symbol="EURUSD"),
        overrides={"max_effective_leverage": 20},
    )
    store.save_rule(rule)
    rules = store.get_rules()
    print(f"Saved and loaded policy rules count: {len(rules)}")


def example_19_cryptographic_audit_hash_chain() -> None:
    """Demonstrate secure audit log event writing and hash chain consistency validations (audit.py)."""
    print_header(19, "Cryptographic Audit Hash Chain")

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    # 1. Validate empty chain
    print(f"Verify initial empty audit chain: {verify_risk_audit_chain(store)}")

    # 2. Perform a check that records a hashed block
    trade = ProposedTrade(
        strategy_id="strat_1", symbol="EURUSD", side="buy", volume=Decimal("0.1")
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={"mode": "paper", "environment": "local"},
    )
    req.request_id = "req_audit_demo"

    # Evaluate to write audit log
    gov.review_trade_risk(req)
    print(f"Events recorded: {len(store.get_all_events())}")
    print(f"Verify audit chain status: {verify_risk_audit_chain(store)}")


def example_20_observability_metrics_and_reporting() -> None:
    """Demonstrate compilation of reports, path traversal file safeguards, Prometheus metrics, and AI tools (reports.py)."""
    print_header(20, "Observability Metrics and Reporting")

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    trade = ProposedTrade(
        strategy_id="strat_reporting",
        symbol="GBPUSD",
        side="buy",
        volume=Decimal("0.5"),
    )
    portfolio = PortfolioState(
        account_id="acc_reporting",
        balance=Decimal("20000.00"),
        equity=Decimal("20000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("20000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={"mode": "paper", "environment": "local"},
    )
    req.request_id = "req_reporting_demo"
    gov.review_trade_risk(req)

    # 1. Report compilation
    report = generate_risk_report(
        state_store=store,
        audit_sink=store,
        decision_store=store,
        request_id="trace_reporting_demo",
    )
    print(
        f"Report generated: ID={report.report_id}, Decision count={len(report.decisions)}"
    )

    # 2. File write path traversal safety check
    report_file_path = "risk_report_demo.json"
    generate_risk_report(
        state_store=store,
        audit_sink=store,
        decision_store=store,
        request_id="trace_reporting_demo",
        write_to_path=report_file_path,
    )
    print(f"  Report written to file safety: {Path(report_file_path).exists()}")
    if Path(report_file_path).exists():
        Path(report_file_path).unlink()

    # 3. Prometheus metrics export
    prometheus_metrics = RISK_METRICS_REGISTRY.export_prometheus_text()
    lines = [
        line for line in prometheus_metrics.split("\n") if "haruquant_risk" in line
    ]
    print("\nPrometheus metrics export (sample):")
    for line in lines[:5]:
        print(f"  {line}")

    # 4. Official AI callable tool snap review
    portfolio_dict = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    tool_res = build_portfolio_risk_snapshot(
        portfolio_state=portfolio_dict,
        market_context={"mode": "paper"},
        request_id="req_tool_demo",
    )
    print(f"\nAI Tool Status: {tool_res.get('status')}")


def example_21_readiness() -> None:
    """Demonstrate readiness checks validation."""
    print_header(21, "Readiness checks validation")

    # 1. Dependency status mapping
    deps = {
        "ports": DependencyStatus(
            file_path="app/services/risk/storage/ports.py",
            implemented=True,
            importable=True,
            side_effect_safe=True,
            covered_by_tests=True,
        ),
        "resolver": DependencyStatus(
            file_path="app/services/risk/policy/resolver.py",
            implemented=True,
            importable=True,
            side_effect_safe=True,
            covered_by_tests=True,
        ),
    }

    dep_assessment = validate_phase_dependencies(deps)
    print(f"Dependency readiness assessment: ready={dep_assessment.ready}")
    print(f"Failure reasons: {dep_assessment.failure_reasons}")

    # 2. Mode Matrix validation
    matrix = RiskModeMatrix(
        covered_modes=[
            "offline",
            "simulation",
            "paper",
            "shadow",
            "read-only live",
            "micro-live",
            "full-live",
        ],
        policies_mapped={
            "offline": "default",
            "simulation": "default",
            "paper": "paper",
            "shadow": "live_conservative",
            "read-only live": "live_conservative",
            "micro-live": "live_conservative",
            "full-live": "live_conservative",
        },
    )
    matrix_res = validate_risk_mode_matrix(matrix)
    print(
        f"Risk mode matrix validation result: valid={matrix_res['valid']}, "
        f"message={matrix_res['message']}"
    )

    # 3. Delivery Plan verification
    plan = ReadinessDeliveryPlan(
        traceability_matrix_present=True,
        synthetic_fixtures_only=True,
        deterministic_seeds={"stress": 42},
        benchmark_dataset_shapes={"var": (100, 10)},
        redaction_rules_defined=True,
        tool_classifications={"validate_phase_dependencies": "helper"},
        audit_failure_policy="fail-closed",
    )
    plan_res = validate_delivery_plan(plan)
    print(
        f"Delivery plan validation result: valid={plan_res['valid']}, "
        f"message={plan_res['message']}"
    )

    # 4. Manifest and Dry-run Compilation
    manifest = RiskReadinessManifest(
        dependencies=deps,
        mode_matrix=matrix,
        delivery_plan=plan,
        author="agentic-builder",
    )
    print(
        f"Readiness manifest instantiated. Author: {manifest.author}, "
        f"Created: {manifest.created_at}"
    )

    report = build_readiness_dry_run(manifest)
    print(f"Dry-run report files to change: {report.files_to_change}")
    print(f"Dry-run planned commands: {report.commands_planned}")


if __name__ == "__main__":
    """Execute all risk governance usage examples."""
    print("==================================================")
    print("STARTING RISK GOVERNANCE USAGE EXAMPLES")
    print("==================================================")

    example_01_core_models_and_contracts()
    example_02_system_config_profiles()
    example_03_policy_resolution_engine()
    example_04_market_regime_classification()
    example_05_portfolio_correlation_dynamics()
    example_06_regime()
    example_06_value_at_risk_and_expected_shortfall()
    example_07_portfolio_stress_scenario_testing()
    example_08_risk_budgeting_allocation()
    example_09_strategy_lifecycle_promotion()
    example_10_position_sizing_engines()
    example_11_fx_currency_and_cluster_exposures()
    example_12_deterministic_limits_governance()
    example_13_margin_liquidity_and_leverage_limits()
    example_14_drawdown_governor_and_throttling()
    example_15_execution_gate_and_broker_feasibility()
    example_16_risk_governor_orchestration()
    example_17_kill_switch_halting_protocols()
    example_18_state_persistence_stores()
    example_19_cryptographic_audit_hash_chain()
    example_20_observability_metrics_and_reporting()
    example_21_readiness()

    print("==================================================")
    print("ALL RISK GOVERNANCE USAGE EXAMPLES COMPLETED")
    print("==================================================")
