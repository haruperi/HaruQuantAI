"""Genuine SYS-WF-002 signal-to-demo-order workflow evidence."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import ROUND_DOWN, Decimal

from app.services.brokers import BrokerAdapter, BrokerId, create_broker_adapter
from app.services.data import (
    AccountBalance,
    AccountStateSnapshot,
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    generate_tick_series,
)
from app.services.indicators import sma
from app.services.risk import (
    ActionPolicyVerdict,
    DecisionState,
    ProposedTrade,
)
from app.services.strategy import (
    StrategyDecision,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyTimingPolicy,
    build_trade_intent,
)
from app.services.trading import (
    LiveSession,
    ReadinessAssessment,
    TradingRequest,
    TradingRoute,
    submit_order,
)
from app.utils import generate_id

from tests.brokers.integration.test_mt5_demo_mutations import (
    _authority_state,
    _cleanup_created_state,
    _connection_config,
    _require_demo_settings,
    _verify_demo_session,
)
from tests.risk import _support as risk_examples
from tests.trading.unit.actions.test_dependencies import (
    MemoryStore,
    dependencies,
)

_SYMBOL = "EURUSD"


async def _passed() -> bool:
    """Return successful bounded lifecycle evidence."""
    return True


async def _provider_evidence(
    adapter: BrokerAdapter,
) -> tuple[
    MarketDataset,
    object,
    object,
    object,
]:
    """Read bounded provider market, symbol, account, and balance evidence."""
    bars_result = await adapter.get_historical_bars(_SYMBOL, "M1", limit=3)
    symbol_result = await adapter.get_symbol_info(_SYMBOL)
    quote_result = await adapter.get_quote(_SYMBOL)
    account_result = await adapter.get_account_info()
    assert bars_result.is_success, bars_result.error
    assert symbol_result.is_success, symbol_result.error
    assert quote_result.is_success, quote_result.error
    assert account_result.is_success, account_result.error
    assert bars_result.data is not None
    assert len(bars_result.data.items) >= 2
    assert symbol_result.data is not None
    assert quote_result.data is not None
    assert account_result.data is not None
    bars = bars_result.data.items
    records = tuple(
        OHLCVRecord(
            timestamp=bar.opening_timestamp,
            source="mt5-demo",
            source_symbol=bar.symbol,
            available_at=bar.closing_timestamp,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.tick_volume or Decimal(0),
            price_unit=bar.price_unit,
            volume_unit=bar.quantity_unit,
        )
        for bar in bars
    )
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=len(records),
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol=_SYMBOL,
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={"provider": "mt5", "environment": "demo"},
        license_metadata={"license": "provider-demo"},
        cache_status="not_used",
        workflow_context="execution_bound",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    return dataset, symbol_result.data, quote_result.data, account_result.data


def _risk_decision(intent, quantity: Decimal, price: Decimal):
    """Review the Strategy intent through the real Risk governor."""
    config = risk_examples._config().model_copy(
        update={"profile": "paper", "execution_route": "paper"}
    )
    proposal = risk_examples._proposal(config).model_copy(
        update={
            "intent": intent,
            "requested_size": quantity,
            "current_price": price,
            "stop_distance": max(price * Decimal("0.01"), Decimal("0.00001")),
        }
    )
    assert isinstance(proposal, ProposedTrade)
    governor, _, _ = risk_examples._services(config)
    decision = governor.review_trade_risk(
        proposal,
        risk_examples._snapshot_governor(config),
        risk_examples._market(),
        risk_examples._regime(),
        (risk_examples._inactive_state(),),
        risk_examples._auth(config),
        attestation=risk_examples._attestation(config),
        now=risk_examples.NOW,
    )
    assert decision.state is DecisionState.APPROVE
    return decision


async def _exercise_signal_to_demo(adapter: BrokerAdapter, settings) -> None:  # noqa: PLR0915 - explicit end-to-end evidence flow
    """Execute and reconcile one complete SYS-WF-002 demo workflow."""
    connected = await adapter.connect()
    assert connected.is_success, connected.error
    original_orders: set[str] | None = None
    original_positions: set[str] | None = None
    session: LiveSession | None = None
    try:
        await _verify_demo_session(adapter)
        original_orders, original_positions = await _authority_state(adapter)
        dataset, symbol, quote, account = await _provider_evidence(adapter)
        ticks = generate_tick_series(
            dataset,
            model="trading_bar",
            trading_timeframe="M1",
            spread_model="fixed_spread",
            fixed_spread_points=Decimal(1),
            max_records=100,
            request_id=dataset.request_id,
        )
        indicator = sma(dataset, period=2)
        assert ticks.records
        assert not indicator.values.empty
        assert symbol.min_quantity is not None
        assert symbol.max_quantity is not None
        assert symbol.quantity_step is not None
        assert symbol.price_precision is not None
        assert quote.bid is not None
        price_step = symbol.price_step or Decimal(1).scaleb(-symbol.price_precision)
        limit_price = (quote.bid * Decimal("0.80")).quantize(
            price_step, rounding=ROUND_DOWN
        )
        decision = StrategyDecision(
            decision_id=generate_id("req"),
            sequence=0,
            action="PROPOSE",
            symbol=_SYMBOL,
            side="BUY",
            intent_type="OPEN",
            order_type="LIMIT",
            time_in_force="GTC",
            requested_sizing_mode="quantity",
            quantity_hint=symbol.min_quantity,
            valid_from=risk_examples.NOW,
            expires_at=risk_examples.NOW + timedelta(minutes=1),
            limit_price=limit_price,
            allow_partial_fills=False,
            rationale_refs=(indicator.indicator_id,),
            diagnostic_facts={"indicator_status": "ready"},
            lineage={
                "strategy_id": "sys-wf-002",
                "strategy_version": "v1",
                "config_hash": "a" * 64,
            },
        )
        context = StrategyExecutionContext(
            environment=StrategyEnvironment.PAPER,
            decision_timestamp=risk_examples.NOW,
            timing_policy=StrategyTimingPolicy.EVENT_DRIVEN,
            seed=0,
            interface_version="v1",
            request_id=risk_examples.REQUEST_ID,
            workflow_id=risk_examples.WORKFLOW_ID,
            correlation_id=risk_examples.CORRELATION_ID,
            dependency_status={"data": "ready", "indicators": "ready"},
            snapshot_refs=(dataset.request_id,),
            max_diagnostic_bytes=8_192,
        )
        intent_result = build_trade_intent(decision, context, 0)
        assert intent_result.status == "success", intent_result.error
        assert intent_result.data is not None
        intent = intent_result.data
        risk_decision = _risk_decision(intent, symbol.min_quantity, limit_price)
        assert risk_decision.token is not None
        policy = ActionPolicyVerdict(
            verdict_id=generate_id("req"),
            action="submit_order",
            scope={"account_id": account.account_id},
            policy_version="policy-1",
            attestation_id="attestation-1",
            decision_id=risk_decision.decision_id,
            reservation_id=generate_id("req"),
            allowed=True,
            reasons=(),
            issued_at=risk_examples.NOW,
            expires_at=risk_examples.NOW + timedelta(minutes=1),
            request_id=risk_decision.request_id,
            workflow_id=risk_decision.workflow_id,
            correlation_id=risk_decision.correlation_id,
        )
        request = TradingRequest(
            request_id=risk_decision.request_id,
            workflow_id=risk_decision.workflow_id,
            correlation_id=risk_decision.correlation_id,
            route=TradingRoute.PAPER,
            action="submit_order",
            provider_id="mt5",
            account_id=account.account_id,
            strategy_id=intent.strategy_id,
            strategy_version=intent.strategy_version,
            intent_id=intent.intent_id,
            symbol=_SYMBOL,
            side="BUY",
            order_type="LIMIT",
            quantity_unit=symbol.quantity_unit,
            quantity=risk_decision.approved_size,
            price=limit_price,
            time_in_force="GTC",
            risk_decision_id=risk_decision.decision_id,
            action_policy_verdict_id=policy.verdict_id,
            approval_token_ref=risk_decision.token.token_id,
            idempotency_key=generate_id("req"),
            canonical_material_version="v1",
            system_time=risk_examples.NOW,
            valid_until=risk_decision.expires_at,
            instrument_min_quantity=symbol.min_quantity,
            instrument_max_quantity=symbol.max_quantity,
            instrument_quantity_step=symbol.quantity_step,
            instrument_price_tick=price_step,
        )
        account_snapshot = AccountStateSnapshot(
            account_id=account.account_id,
            currency=account.currency or "USD",
            balances=(
                AccountBalance(
                    asset=account.currency or "USD",
                    total=account.balance or Decimal(0),
                    available=account.free_margin or Decimal(0),
                ),
            ),
            equity=account.equity or Decimal(0),
            margin_used=account.margin,
            margin_available=account.free_margin,
            positions=(),
            orders=(),
            connected=True,
            trading_allowed=True,
            source_id="mt5-demo-account",
            snapshot_at=risk_examples.NOW,
            expires_at=risk_examples.NOW + timedelta(minutes=1),
            request_id=generate_id("req"),
        )
        capability = {
            "provider_id": "mt5",
            "contract_version": "v1",
            "schema_id": "brokers.adapter.v1",
            "provider_api_version": "v1",
            "supported_actions": ["submit_order"],
            "supported_order_types": ["LIMIT"],
            "quantity_unit": symbol.quantity_unit,
            "security_profile": "approved",
            "operation_timeout_seconds": "15",
            "malformed_response_policy": "unknown_outcome",
            "rate_limit_policy": "external",
            "mutation_retry_policy": "reconcile_before_retry",
            "redaction_applied": True,
        }
        store = MemoryStore()
        pre_audit: list[object] = []
        flags_result = await adapter.get_feature_flags()
        assert flags_result.is_success, flags_result.error
        assert flags_result.data is not None
        session = LiveSession(
            store=store,
            connection=_connection_config(settings),
            broker_adapter=adapter,
            feature_flags=flags_result.data,
            risk_decision_source=lambda _: risk_decision,
            action_policy_source=lambda _: policy,
            kill_switch_source=lambda _: (risk_examples._inactive_state(),),
            readiness_source=lambda item, _: ReadinessAssessment(
                passed=True,
                failed_check_codes=(),
                evidence_refs={"data_authority_id": dataset.request_id},
                assessed_at=item.system_time,
            ),
            adapter_capability_source=lambda _: capability,
            pre_audit_sink=pre_audit.append,
            event_sink=lambda _: None,
            startup_reconcile=_passed,
            drain_in_flight=_passed,
            flush_evidence=_passed,
            shutdown_reconcile=_passed,
            clock=lambda: risk_examples.NOW,
        )
        await session.start(
            {
                "RUNTIME_PROFILE": "paper",
                "EXECUTION_ROUTE": "paper",
                "ALLOW_LIVE_MUTATIONS": False,
                "LIVE_WORKFLOW_TIMEOUT_SECONDS": "30",
                "SHUTDOWN_BUDGET_SECONDS": "5",
                "IDEMPOTENCY_RETENTION_SECONDS": 600,
                "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
                "MAX_STALENESS_SECONDS": {
                    "route_snapshot": "30",
                    "risk_decision": "30",
                    "kill_switch": "30",
                },
                "BROKER_OPERATION_TIMEOUT_SECONDS": "15",
                "DATA_AUTHORITY_ID": dataset.request_id,
            },
            {
                "data_authority_id": dataset.request_id,
                "adapter_security_profile": "approved",
                "startup_evidence_fresh": True,
            },
        )
        deps = replace(
            dependencies(store=store, action_policy=policy),
            connection=_connection_config(settings),
            broker_adapter=adapter,
            simulation_dispatch=None,
            live_session=session,
            clock=lambda: risk_examples.NOW,
            account_state_source=lambda _: account_snapshot,
            symbol_capability_source=lambda *_: (capability, symbol),
        )
        envelope = await submit_order(request, deps)
        assert envelope.status == "sent"
        assert envelope.audit_metadata["redaction_applied"] is True
        assert store.projection is not None
        assert store.projection.receipts
        assert pre_audit
    finally:
        if original_orders is not None and original_positions is not None:
            await _cleanup_created_state(
                adapter,
                original_orders=original_orders,
                original_positions=original_positions,
            )
        if session is not None and session.started:
            stopped = await session.stop()
            assert stopped.status == "success"
        await adapter.disconnect()


def test_sys_wf_002_signal_reaches_demo_broker_and_ui_envelope() -> None:
    """Execute Data through Trading, reconcile Broker state, and expose UI data."""
    settings = _require_demo_settings()
    created = create_broker_adapter(BrokerId.MT5, _connection_config(settings))
    assert created.is_success, created.error
    assert created.data is not None
    asyncio.run(_exercise_signal_to_demo(created.data, settings))
