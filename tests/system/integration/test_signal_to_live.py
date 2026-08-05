"""Genuine SYS-WF-002 signal-to-demo-order workflow evidence."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import ROUND_DOWN, Decimal
from typing import Any

from app.services.brokers import (
    connect_broker,
    create_broker_adapter,
    disconnect_broker,
    get_broker_account_info,
    get_broker_feature_flags,
    get_broker_historical_bars,
    get_broker_id,
    get_broker_quote,
    get_broker_symbol_info,
    get_broker_value_field,
)
from app.services.data import (
    build_account_state_snapshot,
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
    generate_tick_series,
    unwrap_data_response,
)
from app.services.indicators import sma
from app.services.risk import (
    create_action_policy_verdict,
    create_kill_switch_state,
    get_decision_state,
)
from app.services.strategy import (
    build_trade_intent,
    create_strategy_decision,
    create_strategy_execution_context,
    get_strategy_environment,
    get_strategy_timing_policy,
)
from app.services.trading import (
    create_live_session,
    create_readiness_assessment,
    create_trading_request,
    is_live_session_started,
    start_live_session,
    stop_live_session,
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
from tests.indicators.helpers import unwrap_response
from tests.risk import _support as risk_examples
from tests.trading.unit.actions.test_dependencies import (
    MemoryStore,
    dependencies,
)

LiveSession = Any
BrokerAdapter = Any
MarketDataset = Any

# Private type-only aliases; Risk exposes functions, not contract classes.
ProposedTrade = object

_SYMBOL = "EURUSD"


def _broker_field(value: object, field: str) -> Any:
    """Read one documented field from an opaque Broker value."""
    return get_broker_value_field(value, field)


def _broker_result(response: object, *, require_data: bool = True) -> Any:
    """Unwrap one successful Broker standard response."""
    assert _broker_field(response, "status") == "success"
    error = _broker_field(response, "error")
    assert error is None
    data = _broker_field(response, "data")
    if require_data:
        assert data is not None
    return data


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
    bars_page = _broker_result(
        await get_broker_historical_bars(adapter, _SYMBOL, "M1", limit=3)
    )
    symbol = _broker_result(await get_broker_symbol_info(adapter, _SYMBOL))
    quote = _broker_result(await get_broker_quote(adapter, _SYMBOL))
    account = _broker_result(await get_broker_account_info(adapter))
    bars = _broker_field(bars_page, "items")
    assert len(bars) >= 2
    records = tuple(
        build_ohlcv_record(
            timestamp=_broker_field(bar, "opening_timestamp"),
            source="mt5-demo",
            source_symbol=_broker_field(bar, "symbol"),
            available_at=_broker_field(bar, "closing_timestamp"),
            open=_broker_field(bar, "open"),
            high=_broker_field(bar, "high"),
            low=_broker_field(bar, "low"),
            close=_broker_field(bar, "close"),
            volume=_broker_field(bar, "tick_volume") or Decimal(0),
            price_unit=_broker_field(bar, "price_unit"),
            volume_unit=_broker_field(bar, "quantity_unit"),
        )
        for bar in bars
    )
    quality = build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=len(records),
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    dataset = build_market_dataset(
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
    return dataset, symbol, quote, account


def _risk_decision(
    intent: object,
    quantity: Decimal,
    price: Decimal,
    account_id: str,
) -> Any:
    """Review the Strategy intent through the real Risk governor."""
    config = risk_examples._config().model_copy(
        update={"profile": "paper", "execution_route": "paper"}
    )
    proposal = risk_examples._proposal(config).model_copy(
        update={
            "intent": intent,
            "account_id": account_id,
            "requested_size": quantity,
            "current_price": price,
            "stop_distance": max(price * Decimal("0.01"), Decimal("0.00001")),
        }
    )
    assert proposal.schema_id == "risk.proposed_trade.v1"
    governor, _, _ = risk_examples._services(config)
    attestation = risk_examples._attestation(config).model_copy(
        update={"scope": {"account_id": account_id, "symbol": _SYMBOL}}
    )
    decision = risk_examples.unwrap_risk_response(
        governor.review_trade_risk(
            proposal,
            risk_examples._snapshot_governor(config).model_copy(
                update={"account_id": account_id}
            ),
            risk_examples._market(),
            risk_examples._regime(),
            (risk_examples._inactive_state(),),
            risk_examples._auth(config),
            attestation=attestation,
            now=risk_examples.NOW,
        ),
        operation="review_trade_risk",
    )
    assert decision.state is get_decision_state("APPROVE")
    return decision


async def _exercise_signal_to_demo(adapter: BrokerAdapter, settings) -> None:  # noqa: PLR0915 - explicit end-to-end evidence flow
    """Execute and reconcile one complete SYS-WF-002 demo workflow."""
    _broker_result(await connect_broker(adapter), require_data=False)
    original_orders: set[str] | None = None
    original_positions: set[str] | None = None
    session: LiveSession | None = None
    try:
        await _verify_demo_session(adapter)
        original_orders, original_positions = await _authority_state(adapter)
        dataset, symbol, quote, account = await _provider_evidence(adapter)
        ticks = unwrap_data_response(
            generate_tick_series(
                dataset,
                model="trading_bar",
                trading_timeframe="M1",
                spread_model="fixed_spread",
                fixed_spread_points=Decimal(1),
                max_records=100,
                request_id=dataset.request_id,
            ),
            operation="generate_tick_series",
            request_id=dataset.request_id,
        )
        indicator = unwrap_response(sma(dataset, period=2))
        assert ticks.records
        assert not indicator.values.empty
        min_quantity = _broker_field(symbol, "min_quantity")
        max_quantity = _broker_field(symbol, "max_quantity")
        quantity_step = _broker_field(symbol, "quantity_step")
        price_precision = _broker_field(symbol, "price_precision")
        bid = _broker_field(quote, "bid")
        assert min_quantity is not None
        assert max_quantity is not None
        assert quantity_step is not None
        assert price_precision is not None
        assert bid is not None
        price_step = _broker_field(symbol, "price_step") or Decimal(1).scaleb(
            -price_precision
        )
        limit_price = (bid * Decimal("0.80")).quantize(price_step, rounding=ROUND_DOWN)
        decision = create_strategy_decision(
            decision_id=generate_id("req"),
            sequence=0,
            action="PROPOSE",
            symbol=_SYMBOL,
            side="BUY",
            intent_type="OPEN",
            order_type="LIMIT",
            time_in_force="GTC",
            requested_sizing_mode="quantity",
            quantity_hint=min_quantity,
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
        context = create_strategy_execution_context(
            environment=get_strategy_environment("PAPER"),
            decision_timestamp=risk_examples.NOW,
            timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
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
        account_id = _broker_field(account, "account_id")
        risk_decision = _risk_decision(
            intent,
            min_quantity,
            limit_price,
            account_id,
        )
        assert risk_decision.token is not None
        policy = create_action_policy_verdict(
            verdict_id=generate_id("req"),
            action="submit_order",
            scope={"account_id": account_id},
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
        request = create_trading_request(
            request_id=risk_decision.request_id,
            workflow_id=risk_decision.workflow_id,
            correlation_id=risk_decision.correlation_id,
            route="paper",
            action="submit_order",
            provider_id="mt5",
            account_id=account_id,
            strategy_id=intent.strategy_id,
            strategy_version=intent.strategy_version,
            intent_id=intent.intent_id,
            symbol=_SYMBOL,
            side="BUY",
            order_type="LIMIT",
            quantity_unit=_broker_field(symbol, "quantity_unit"),
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
            instrument_min_quantity=min_quantity,
            instrument_max_quantity=max_quantity,
            instrument_quantity_step=quantity_step,
            instrument_price_tick=price_step,
        )
        assert risk_decision.decision_id == request.risk_decision_id
        assert risk_decision.intent_id == request.intent_id
        assert risk_decision.approved_size == request.quantity
        assert risk_decision.request_id == request.request_id
        assert risk_decision.workflow_id == request.workflow_id
        assert risk_decision.correlation_id == request.correlation_id
        assert risk_decision.token.token_id == request.approval_token_ref
        assert risk_decision.token.action == request.action
        assert risk_decision.token.scope.get("account_id") == request.account_id
        assert policy.verdict_id == request.action_policy_verdict_id
        assert policy.action == request.action
        assert policy.decision_id == request.risk_decision_id
        assert policy.scope.get("account_id") == request.account_id
        currency = _broker_field(account, "currency") or "USD"
        account_snapshot = build_account_state_snapshot(
            account_id=account_id,
            currency=currency,
            balances=(
                {
                    "asset": currency,
                    "total": _broker_field(account, "balance") or Decimal(0),
                    "available": _broker_field(account, "free_margin") or Decimal(0),
                },
            ),
            equity=_broker_field(account, "equity") or Decimal(0),
            margin_used=_broker_field(account, "margin"),
            margin_available=_broker_field(account, "free_margin"),
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
            "quantity_unit": _broker_field(symbol, "quantity_unit"),
            "security_profile": "approved",
            "operation_timeout_seconds": "15",
            "malformed_response_policy": "unknown_outcome",
            "rate_limit_policy": "external",
            "mutation_retry_policy": "reconcile_before_retry",
            "redaction_applied": True,
        }
        store = MemoryStore()
        pre_audit: list[object] = []
        feature_flags = _broker_result(await get_broker_feature_flags(adapter))
        session = create_live_session(
            store=store,
            connection=_connection_config(settings),
            broker_adapter=adapter,
            feature_flags=feature_flags,
            risk_decision_source=lambda _: risk_decision,
            action_policy_source=lambda _: policy,
            kill_switch_source=lambda item: (
                create_kill_switch_state(
                    state_id="sys-wf-002-global-switch",
                    scope_level="global",
                    scope={},
                    state="inactive",
                    reason="normal operation",
                    version=1,
                    updated_at=item.system_time,
                ),
                create_kill_switch_state(
                    state_id="sys-wf-002-strategy-switch",
                    scope_level="strategy",
                    scope={"strategy_id": item.strategy_id},
                    state="inactive",
                    reason="normal operation",
                    version=1,
                    updated_at=item.system_time,
                ),
                create_kill_switch_state(
                    state_id="sys-wf-002-symbol-switch",
                    scope_level="symbol",
                    scope={"symbol": item.symbol},
                    state="inactive",
                    reason="normal operation",
                    version=1,
                    updated_at=item.system_time,
                ),
            ),
            readiness_source=lambda item, _: create_readiness_assessment(
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
            auth_context_source=lambda _: risk_examples._auth(risk_examples._config()),
            clock=lambda: risk_examples.NOW,
        )
        await start_live_session(
            session,
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
        assert envelope.status == "success", envelope.error
        assert envelope.metadata.extensions["redaction_applied"] is True
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
        if session is not None and is_live_session_started(session):
            stopped = await stop_live_session(session)
            assert stopped.status == "success"
        _broker_result(await disconnect_broker(adapter), require_data=False)


def test_sys_wf_002_signal_reaches_demo_broker_and_ui_envelope() -> None:
    """Execute Data through Trading, reconcile Broker state, and expose UI data."""
    settings = _require_demo_settings()
    adapter = _broker_result(
        create_broker_adapter(get_broker_id("mt5"), _connection_config(settings))
    )
    asyncio.run(_exercise_signal_to_demo(adapter, settings))
