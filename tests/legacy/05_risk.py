"""Direct, copyable usage catalogue demonstrating Risk domain workflows using real MT5 data.

Example 1: Risk Configuration Profiles and Firm Mandates
Example 2: Position Sizing and Stop Loss Validation
Example 3: Portfolio Risk Limits and Market Context (with real MT5 EURUSD H1 data)
Example 4: Trade Risk Review and Risk Governor Evaluation
Example 5: Risk Kill Switch Governance and Emergency Action Validation
Example 6: Allocation Proposal Review and Approval Token Lifecycle
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.composition.config import load_broker_provider_settings
from app.kernel.identity import generate_id
from app.services.data import (
    build_account_state_snapshot,
    build_market_data_request,
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    get_market_data,
)
from app.services.risk import (
    build_development_risk_config,
    build_personal_account_risk_config,
    build_portfolio_risk_snapshot,
    build_prop_firm_risk_config,
    build_stop_validation,
    calculate_planned_risk_reward,
    calculate_position_size,
    check_risk_kill_switch,
    compute_config_hash,
    create_allocation_review_request,
    create_firm_mandate,
    create_kill_switch_command,
    create_portfolio_risk_snapshot,
    create_portfolio_state,
    create_position_sizing_request,
    create_proposed_trade,
    evaluate_market_context,
    evaluate_portfolio_limits,
    evaluate_trade_readiness,
    review_allocation_proposal,
    validate_stop_loss,
)
from app.services.strategy import create_trade_intent_value

_START = datetime(2026, 8, 1, tzinfo=UTC)
_END = _START + timedelta(hours=1000)
_PROVIDER_FIELDS = {
    "MT5_ENABLED": "mt5_enabled",
    "MT5_TERMINAL_PATH": "mt5_terminal_path",
}


def _header(title: str) -> None:
    """Print a bounded example heading.

    Args:
        title: Human-readable example title.

    Returns:
        None.
    """
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


@contextmanager
def _provider_runtime_context(*, offline: bool) -> Iterator[bool]:
    """Inject database-backed provider settings for a verified usage run.

    Args:
        offline: Whether to suppress external provider reads.

    Yields:
        Whether provider reads are enabled for this run.

    Raises:
        ValueError: If persisted settings do not prove a dev/demo boundary.
    """
    if offline:
        yield False
        return
    from app.services.api import (
        build_system_broker_connection_config,
        get_api_settings,
        get_system_settings,
    )

    record = get_system_settings(request_id=generate_id("req"))
    environment = record.settings.get("ENVIRONMENT", get_api_settings().environment)
    if environment != "dev":
        raise ValueError(
            "provider reads require the effective API environment to be dev"
        )
    mt5_config = build_system_broker_connection_config(
        "mt5",
        request_id=generate_id("req"),
    )
    if getattr(mt5_config, "environment", None) != "demo":
        raise ValueError("MT5 provider reads require a composed demo environment")
    explicit_values = {
        field: record.settings[key]
        for key, field in _PROVIDER_FIELDS.items()
        if key in record.settings
    }
    provider_settings = load_broker_provider_settings(explicit_values)
    with (
        data_provider_settings_context(provider_settings),
        data_provider_connection_resolver_context(
            lambda broker_id, request_id: (
                mt5_config
                if broker_id == "mt5"
                else build_system_broker_connection_config(
                    broker_id,
                    request_id=request_id,
                )
            )
        ),
    ):
        yield True


def _get_dataset(*, timeframe: str = "H1", limit: int = 100) -> Any:
    """Retrieve MT5 market dataset through the Data public API.

    Args:
        timeframe: Assigned canonical timeframe.
        limit: Number of records to retrieve.

    Returns:
        Canonical market dataset if available, else None.
    """
    req = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe=timeframe,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    return get_market_data(req).data


def example_01_risk_config_and_mandates() -> None:
    """Demonstrate Risk domain configuration building and firm mandate policies."""
    _header("Example 1: Risk Configuration Profiles and Firm Mandates")

    dev_config = build_development_risk_config()
    print(f"Development Risk Profile: {dev_config.profile}")
    print(f"  Base Currency: {dev_config.base_currency}")
    print(
        f"  Pending Order Exposure Policy: {dev_config.pending_order_exposure_policy}"
    )

    prop_config = build_prop_firm_risk_config()
    print(f"\nProp Firm Risk Profile: {prop_config.profile}")
    print(f"  Base Currency: {prop_config.base_currency}")

    personal_config = build_personal_account_risk_config()
    print(f"\nPersonal Account Risk Profile: {personal_config.profile}")

    mandate = create_firm_mandate(
        account_id="acc-001",
        mandate_version="2026.07.28-01",
        firm="Example Prop Firm",
        model="fx_cfd",
        phase="funded",
        initial_balance=Decimal("10000.00"),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash="a" * 64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.10")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.05"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.10"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
    )
    print(f"\nCreated Firm Mandate: {mandate.firm} (version={mandate.mandate_version})")


def example_02_position_sizing_and_stop_loss() -> None:
    """Demonstrate position sizing calculation and stop-loss validation."""
    _header("Example 2: Position Sizing and Stop Loss Validation")

    now = datetime.now(UTC)
    config = build_development_risk_config()

    snap = create_portfolio_risk_snapshot(
        snapshot_id="snap-usage-01",
        account_id="acc-001",
        base_currency="USD",
        equity=Decimal("10000.00"),
        daily_loss=Decimal("0.00"),
        total_loss=Decimal("0.00"),
        gross_exposure=Decimal("0.00"),
        net_exposure=Decimal("0.00"),
        drawdown=Decimal("0.00"),
        margin_utilization=Decimal("0.00"),
        effective_leverage=Decimal("0.00"),
        historical_var=None,
        historical_cvar=None,
        volatility=None,
        portfolio_correlation=Decimal("0.00"),
        exposure_by_dimension={},
        contributions={},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=now,
        config_hash="a" * 64,
        evidence_refs={"account": "acc-001"},
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
    )

    sizing_req = create_position_sizing_request(
        method="fixed_risk",
        requested_size=None,
        fixed_lot=None,
        risk_amount=Decimal("100.00"),
        risk_fraction=None,
        stop_distance=Decimal(100),
        unit_value=Decimal(10),
        milestone_multiplier=None,
        win_rate=None,
        payoff_ratio=None,
        trade_count=None,
        volatility_multiplier=None,
        asset_volatility=None,
        broker_min_size=Decimal("0.01"),
        broker_max_size=Decimal(100),
        broker_size_step=Decimal("0.01"),
        evidence_refs={"snapshot": snap.snapshot_id},
        request_id=generate_id("req"),
    )

    sizing_result = calculate_position_size(sizing_req, snap, config)
    print(f"Position Sizing Response Status: {sizing_result.status}")
    if sizing_result.data is not None:
        print(f"  Normalized Size: {sizing_result.data.normalized_size}")

    rr_ratio = calculate_planned_risk_reward(
        entry_price=Decimal("1.1500"),
        stop_loss_price=Decimal("1.1450"),
        take_profit_price=Decimal("1.1600"),
    )
    print(f"  Planned Risk-Reward Ratio: {rr_ratio.data}")

    stop_map = build_stop_validation(
        symbol="EURUSD",
        side="BUY",
        entry_price=Decimal("1.1500"),
        stop_price=Decimal("1.1450"),
        tick_size=Decimal("0.0001"),
        min_stop_distance=Decimal("0.0020"),
        contract_value=Decimal(100000),
        quantity=Decimal("0.10"),
        evaluated_at=now,
    )
    stop_val = validate_stop_loss(stop_map)
    print(f"  Stop Loss Validation Status: {stop_val.status}")
    if stop_val.data is not None:
        checks = {item.limit_id: item.status for item in stop_val.data}
        print(f"  Stop Loss Checks Evaluated: {checks}")


def example_03_portfolio_limits_and_market_context() -> None:
    """Demonstrate portfolio risk limit evaluation with MT5 market data context."""
    _header("Example 3: Portfolio Risk Limits and Market Context (MT5 EURUSD H1)")

    dataset = _get_dataset(timeframe="H1", limit=100)
    now = datetime.now(UTC)

    if dataset is not None:
        print(
            f"Retrieved {len(dataset.records)} MT5 EURUSD H1 bars for market context evaluation"
        )
        mkt_context = evaluate_market_context(
            dataset=dataset,
            request_id=generate_id("req"),
        )
        print(f"  Market Context Status: {mkt_context.status}")
    else:
        print("Market dataset offline -> Using baseline risk evaluation context")

    acct = build_account_state_snapshot(
        account_id="acc-001",
        currency="USD",
        balances=(
            {
                "asset": "USD",
                "total": Decimal("10000.00"),
                "available": Decimal("10000.00"),
            },
        ),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        margin_available=Decimal("10000.00"),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-mt5",
        snapshot_at=now,
        expires_at=now + timedelta(minutes=1),
        request_id=generate_id("req"),
    )

    port_state = create_portfolio_state(
        account_snapshot=acct,
        peak_equity=Decimal("10000.00"),
        day_start_equity=Decimal("10000.00"),
        inception_equity=Decimal("10000.00"),
        symbol_prices={"EURUSD": Decimal("1.1500")},
        symbol_contract_sizes={"EURUSD": Decimal(100000)},
        symbol_quote_currencies={"EURUSD": "USD"},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations={},
        exposure_dimensions={},
        as_of=now,
        expires_at=now + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("returns",),
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
    )

    config = build_development_risk_config()
    snapshot = build_portfolio_risk_snapshot(port_state, config)
    limits_result = evaluate_portfolio_limits(snapshot=snapshot, config=config)

    print("\nPortfolio Limit Evaluation Result:")
    print(f"  Status: {limits_result.status}")
    if limits_result.data is not None:
        print(f"  Limit Statuses Evaluated: {len(limits_result.data.limit_statuses)}")


def example_04_trade_risk_review_and_governor() -> None:
    """Demonstrate ProposedTrade readiness evaluation."""
    _header("Example 4: Trade Risk Review and Readiness Evaluation")

    now = datetime.now(UTC)
    config = build_development_risk_config()

    intent = create_trade_intent_value(
        intent_id="intent-001",
        decision_id="dec-001",
        idempotency_key="idempotency-001",
        strategy_id="trend-following-v1",
        strategy_version="1.0.0",
        strategy_sequence=1,
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        limit_price=None,
        stop_price=None,
        time_in_force=None,
        requested_sizing_mode="fixed_risk",
        quantity_hint=Decimal("0.10"),
        notional_hint=None,
        signal_timestamp=now,
        decision_timestamp=now,
        parent_intent_id=None,
        stop_loss=Decimal("1.1450"),
        take_profit=None,
        expiration=now + timedelta(minutes=5),
        allow_partial_fills=False,
        min_fill_size=None,
        rationale_ref=None,
        lineage={"strategy_config": "a" * 64},
    )

    trade = create_proposed_trade(
        intent=intent,
        account_id="acc-001",
        portfolio_id="port-001",
        requested_size=Decimal("0.10"),
        current_price=Decimal("1.1500"),
        stop_distance=Decimal("0.0050"),
        market_as_of=now,
        expires_at=now + timedelta(minutes=5),
        risk_profile=config.profile,
        evidence_refs={"market": generate_id("req")},
        provenance={"source": "strategy"},
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
    )

    acct = build_account_state_snapshot(
        account_id="acc-001",
        currency="USD",
        balances=(
            {
                "asset": "USD",
                "total": Decimal("10000.00"),
                "available": Decimal("10000.00"),
            },
        ),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        margin_available=Decimal("10000.00"),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-mt5",
        snapshot_at=now,
        expires_at=now + timedelta(minutes=1),
        request_id=generate_id("req"),
    )

    port_state = create_portfolio_state(
        account_snapshot=acct,
        peak_equity=Decimal("10000.00"),
        day_start_equity=Decimal("10000.00"),
        inception_equity=Decimal("10000.00"),
        symbol_prices={"EURUSD": Decimal("1.1500")},
        symbol_contract_sizes={"EURUSD": Decimal(100000)},
        symbol_quote_currencies={"EURUSD": "USD"},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations={},
        exposure_dimensions={},
        as_of=now,
        expires_at=now + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("returns",),
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
    )

    snapshot = build_portfolio_risk_snapshot(port_state, config)
    readiness = evaluate_trade_readiness(
        trade=trade,
        snapshot=snapshot,
        config=config,
    )
    print(f"Trade Readiness Review Status: {readiness.status}")


def example_05_kill_switch_governance() -> None:
    """Demonstrate Risk Kill Switch status check and emergency commands."""
    _header("Example 5: Risk Kill Switch Governance and Emergency Action Validation")

    now = datetime.now(UTC)
    ks_status = check_risk_kill_switch()
    print(f"Kill Switch Status Check: {ks_status.status}")

    cmd = create_kill_switch_command(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="operator safety stop",
        requested_at=now,
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
    )
    print(
        f"Created Kill Switch Command: action={cmd.action} scope={cmd.scope_level} reason='{cmd.reason}'"
    )


def example_06_allocation_review_and_approval_tokens() -> None:
    """Demonstrate strategy allocation proposal review."""
    _header("Example 6: Allocation Proposal Review")

    now = datetime.now(UTC)
    config = build_development_risk_config()
    cfg_hash_res = compute_config_hash(config)
    cfg_hash = cfg_hash_res.data if cfg_hash_res.data is not None else "a" * 64

    alloc_req = create_allocation_review_request(
        projection_kind="construction",
        portfolio_id="portfolio-001",
        portfolio_version="v1",
        result_id="construction-001",
        plan_id=None,
        ordered_components=(
            {
                "component_id": "c1",
                "dimension": "symbol:EURUSD",
                "weight": "0.05",
            },
        ),
        eligibility_decision_refs=("eligibility-1",),
        account_evidence_ref="acc-001",
        market_evidence_ref=generate_id("req"),
        fx_evidence_refs=(),
        evidence_hashes={"snapshot_config": cfg_hash},
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        requested_at=now,
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
    )

    acct = build_account_state_snapshot(
        account_id="acc-001",
        currency="USD",
        balances=(
            {
                "asset": "USD",
                "total": Decimal("10000.00"),
                "available": Decimal("10000.00"),
            },
        ),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        margin_available=Decimal("10000.00"),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-mt5",
        snapshot_at=now,
        expires_at=now + timedelta(minutes=1),
        request_id=generate_id("req"),
    )

    port_state = create_portfolio_state(
        account_snapshot=acct,
        peak_equity=Decimal("10000.00"),
        day_start_equity=Decimal("10000.00"),
        inception_equity=Decimal("10000.00"),
        symbol_prices={"EURUSD": Decimal("1.1500")},
        symbol_contract_sizes={"EURUSD": Decimal(100000)},
        symbol_quote_currencies={"EURUSD": "USD"},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations={},
        exposure_dimensions={},
        as_of=now,
        expires_at=now + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("returns",),
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
    )

    snapshot = build_portfolio_risk_snapshot(port_state, config)
    review_res = review_allocation_proposal(alloc_req, snapshot, config)
    print(f"Allocation Proposal Review Status: {review_res.status}")


def main() -> None:
    """Execute all Risk public boundary usage examples.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Direct, copyable usage catalogue for the Risk service public API using real MT5 data."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip external provider reads for deterministic validation.",
    )
    args = parser.parse_args()

    with _provider_runtime_context(offline=args.offline):
        example_01_risk_config_and_mandates()
        example_02_position_sizing_and_stop_loss()
        example_03_portfolio_limits_and_market_context()
        example_04_trade_risk_review_and_governor()
        example_05_kill_switch_governance()
        example_06_allocation_review_and_approval_tokens()


if __name__ == "__main__":
    main()
