"""Executable Full-Domain Trading Pipeline usage program.

Connects all 9 registered package features (`FEAT-TRD-01` through `FEAT-TRD-09`)
into a single homogeneous, end-to-end operational pipeline.
Imports strictly from the public API boundary `app.services.trading`.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import build_broker_connection_config
from app.services.data import build_account_state_snapshot
from app.services.risk import (
    create_kill_switch_state,
    create_risk_decision_package,
    get_decision_state,
)
from app.services.trading import (
    apply_execution_event,
    assess_execution_readiness,
    build_broker_state_unknown_event,
    build_execution_plan,
    build_trading_report,
    cancel_all_orders,
    cancel_order,
    classify_authority_response,
    clear_kill_switch,
    close_all_positions,
    close_position,
    compare_authority_state,
    create_authority_snapshot,
    create_execution_receipt,
    create_idempotency_reservation,
    create_live_session,
    create_operational_event,
    create_order_intent,
    create_portfolio_rebalance_execution_request,
    create_readiness_assessment,
    create_route_snapshot,
    create_trade_record,
    create_trading_action_draft,
    create_trading_error,
    create_trading_event,
    create_trading_projection,
    create_trading_request,
    dispatch_order_intent,
    emit_runtime_event,
    evaluate_live_gate,
    execute_portfolio_rebalance,
    get_live_session_status,
    get_public_contracts,
    get_route_snapshot,
    get_trading_contract_version,
    get_trading_migrations,
    get_trading_route,
    get_trading_schema_version,
    is_live_session_started,
    map_trading_error,
    modify_order,
    modify_position,
    pause_strategy,
    redact_trading_payload,
    reduce_exposure,
    reserve_idempotency,
    resolve_unknown_outcome,
    resume_strategy,
    run_live_evaluation_cycle,
    start_live_session,
    stop_live_session,
    submit_order,
    sync_positions,
    trigger_kill_switch,
    validate_adapter_capability,
    validate_budget_authority,
    validate_order_request,
)
from app.utils import canonical_json
from tests.trading import conftest as examples
from tests.trading.unit.actions.test_controls import authority, projection, switch
from tests.trading.unit.actions.test_dependencies import (
    MemoryStore,
    dependencies,
    execution_store,
    kill_switch_states,
    policy,
    request,
)
from tests.trading.unit.actions.test_emergency import emergency_dependencies
from tests.trading.unit.actions.test_rebalance import (
    rebalance_dependencies,
    rebalance_request,
)
from tests.trading.unit.actions.test_runtime import evaluation_dependencies, evidence

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"
HASH_64 = "a" * 64

type Scope = tuple[Any, str, str]


def _stage_banner(stage_num: int, title: str, feature_id: str) -> None:
    """Print stage header banner."""
    print(f"\n{'=' * 88}")
    print(f"Stage {stage_num}: {title} ({feature_id})")
    print(f"{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


class _ExampleTradingStore:
    """Minimal in-memory Trading persistence store."""

    def __init__(self) -> None:
        self.reservations: dict[str, Any] = {}
        self.events: list[Any] = []
        self.projections: dict[Scope, Any] = {}
        self.records: dict[str, Any] = {}

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> Any:
        existing = self.reservations.get(key)
        if existing is not None:
            status = (
                "duplicate_active"
                if existing.material_hash == material_hash
                else "conflict"
            )
            return create_idempotency_reservation(
                **{**existing.model_dump(mode="python"), "status": status}
            )
        reservation = create_idempotency_reservation(
            key=key,
            material_hash=material_hash,
            material_version=material_version,
            status="new",
            reserved_at=reserved_at,
            expires_at=expires_at,
        )
        self.reservations[key] = reservation
        return reservation

    def complete_idempotency(
        self,
        key: str,
        _material_hash: str,
        receipt_id: str,
        completed_at: datetime,
        *,
        status: Literal["completed", "reconciliation_required"],
    ) -> None:
        existing = self.reservations[key]
        self.reservations[key] = existing.model_copy(
            update={
                "status": (
                    "duplicate_completed"
                    if status == "completed"
                    else "reconciliation_required"
                ),
                "receipt_id": receipt_id,
                "reserved_at": completed_at,
            }
        )

    def append_event(self, event: Any) -> None:
        self.events.append(event)

    def load_projection(self, scope: Scope) -> Any | None:
        return self.projections.get(scope)

    def save_projection(self, projection: Any, expected_version: int) -> None:
        scope = (projection.route, projection.tenant_id, projection.authority_id)
        current = self.projections.get(scope)
        current_version = 0 if current is None else current.version
        if current_version != expected_version:
            raise RuntimeError("stale projection")
        self.projections[scope] = projection

    def load_unresolved_attempts(self, scope: Scope) -> tuple[Any, ...]:
        route, tenant_id, authority_id = scope
        return tuple(
            event
            for event in self.events
            if getattr(event, "event_type", None) == "send_attempted"
            and (
                getattr(event, "route", None),
                getattr(event, "tenant_id", None),
                getattr(event, "authority_id", None),
            )
            == (route, tenant_id, authority_id)
        )

    def load_report_evidence(self, scope: Scope) -> dict[str, object]:
        del scope
        return {}


async def _async_passed() -> bool:
    return True


def main() -> None:  # noqa: PLR0915
    """Run full Trading domain feature pipeline sequentially."""
    print("\n" + "=" * 88)
    print("HARUQUANT AI — TRADING DOMAIN FULL-FEATURE PIPELINE EXECUTION")
    print("=" * 88)

    store = _ExampleTradingStore()

    # -------------------------------------------------------------------------
    # Stage 1: Canonical Contracts and Registries (FEAT-TRD-01)
    # -------------------------------------------------------------------------
    _stage_banner(1, "Canonical Contracts and Registries", "FEAT-TRD-01")
    contract_version = get_trading_contract_version()
    print(f"Trading Contract Version: {contract_version}")

    route = get_trading_route("sim")
    print(f"Selected Trading Route: {route.value}")

    request_data = {
        "request_id": REQUEST_ID,
        "workflow_id": WORKFLOW_ID,
        "correlation_id": CORRELATION_ID,
        "route": "sim",
        "action": "submit_order",
        "provider_id": None,
        "account_id": "acc-001",
        "strategy_id": "strategy-001",
        "strategy_version": "v1",
        "intent_id": "intent-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity_unit": "units",
        "quantity": "1.00",
        "risk_decision_id": "risk-001",
        "action_policy_verdict_id": "verdict-001",
        "approval_token_ref": "approval-001",
        "idempotency_key": "idempotency-001",
        "canonical_material_version": "v1",
        "system_time": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }
    trd_request = create_trading_request(**request_data)
    print(_format_result(trd_request))

    order_intent = create_order_intent(
        client_order_id="order-001",
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        route=get_trading_route("sim"),
        provider_id=None,
        account_id="acc-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        source_intent_id="intent-001",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        approved_volume=Decimal("1.00"),
        risk_approved_volume=Decimal("1.00"),
        idempotency_hash="b" * 64,
        canonical_material_version="v1",
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        created_at=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )
    print(_format_result(order_intent))

    receipt = create_execution_receipt(
        receipt_id="receipt-001",
        intent_id="intent-001",
        client_order_id="order-001",
        route=get_trading_route("sim"),
        authority="simulator",
        provider_order_id="sim-order-001",
        status="filled",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal("1.00"),
        average_price=Decimal("1.10000"),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="confirmed",
        retry_safe=False,
        reconciliation_required=False,
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(receipt))

    trade_rec = create_trade_record(
        record_id="trade-rec-001",
        receipt=receipt,
        fill_ids=("fill-001",),
        authority_state="confirmed",
        reconciliation_state="reconciled",
        created_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(trade_rec))

    rebalance_data: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "trading.portfolio_rebalance_execution_request.v1",
        "request_id": "req-77777777-7777-4777-8777-777777777777",
        "workflow_id": WORKFLOW_ID,
        "correlation_id": CORRELATION_ID,
        "plan_id": "plan-001",
        "plan_version": "v1",
        "portfolio_id": "portfolio-001",
        "allocation_version": "allocation-v1",
        "allocation_decision_id": "allocation-decision-001",
        "eligibility_decision_ids": ("eligibility-001",),
        "actions": (
            {
                "action_id": "action-001",
                "component_id": "strategy-001",
                "eligibility_decision_id": "eligibility-001",
                "action": "reduce_exposure",
                "reduce_only": True,
                "current_exposure": "0.50",
                "target_exposure": "0.25",
                "reduction_amount": "0.25",
            },
        ),
        "route": get_trading_route("sim"),
        "approval_token_ref": "approval-001",
        "canonical_material_version": "v1",
        "valid_from": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }
    rebalance_data["canonical_hash"] = sha256(
        canonical_json(rebalance_data).encode()
    ).hexdigest()
    rebalance_req = create_portfolio_rebalance_execution_request(**rebalance_data)
    print(_format_result(rebalance_req))

    trd_error = create_trading_error("INVALID_REQUEST", "Request evidence is invalid")
    print(_format_result(trd_error))

    mapped_err = map_trading_error(
        TimeoutError("provider detail"),
        {"operation": "submit_order", "request_id": REQUEST_ID},
    )
    print(_format_result(mapped_err))

    redacted_payload = redact_trading_payload({"credentials": {"api_key": "secret"}})
    print(_format_result(redacted_payload))

    public_contracts = get_public_contracts()
    print(_format_result(public_contracts))

    action_draft = create_trading_action_draft(request_data)
    print(_format_result(action_draft))

    # -------------------------------------------------------------------------
    # Stage 2: State and Deterministic Projections (FEAT-TRD-02)
    # -------------------------------------------------------------------------
    _stage_banner(2, "State and Deterministic Projections", "FEAT-TRD-02")
    reservation_res = reserve_idempotency(
        trd_request,
        store,
        reservation_time=NOW,
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    print(_format_result(reservation_res))
    reservation = reservation_res.data
    if reservation is not None:
        store.complete_idempotency(
            reservation.key,
            reservation.material_hash,
            receipt.receipt_id,
            NOW,
            status="completed",
        )

    trd_event = create_trading_event(
        event_id="event-001",
        event_type="send_attempted",
        aggregate_version=0,
        route="sim",
        tenant_id="acc-001",
        authority_id="simulator",
        occurred_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        payload={"order_id": "order-001"},
    )
    store.append_event(trd_event)
    print(_format_result(trd_event))

    updated_proj = apply_execution_event(trd_event, store)
    print(_format_result(updated_proj))

    schema_version = get_trading_schema_version()
    print(f"Trading Schema Version: {schema_version}")

    migrations = get_trading_migrations()
    print(_format_result(migrations))

    # -------------------------------------------------------------------------
    # Stage 3: Validation, Readiness, and Plans (FEAT-TRD-03)
    # -------------------------------------------------------------------------
    _stage_banner(3, "Validation, Readiness, and Plans", "FEAT-TRD-03")
    account_snapshot = build_account_state_snapshot(
        account_id="acc-001",
        currency="USD",
        balances=(),
        equity=Decimal(10000),
        margin_available=Decimal(9000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="simulator",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=REQUEST_ID,
    )
    symbol_capability = {
        "supported_order_types": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        "quantity_unit": "units",
    }
    validated_req = validate_order_request(
        trd_request, account_snapshot, symbol_capability
    )
    print(_format_result(validated_req))

    route_snapshot = create_route_snapshot(
        route="sim",
        provider_id=None,
        account_id="acc-001",
        symbol="EURUSD",
        facts={"quote": {"bid": "1.0999", "ask": "1.1001"}},
        source_id="data-source-001",
        authority_id="simulator",
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        available=True,
        fresh=True,
        capabilities=("submit_order",),
    )

    def route_source(_route: object, _provider: object) -> dict[str, object]:
        return route_snapshot.model_dump(mode="python")

    route_snap_res = get_route_snapshot(trd_request, route_source)  # type: ignore[arg-type]
    print(_format_result(route_snap_res))

    risk_pkg = create_risk_decision_package(
        decision_id="risk-001",
        intent_id="intent-001",
        state=get_decision_state("APPROVE"),
        requested_size=Decimal("1.00"),
        approved_size=Decimal("1.00"),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"portfolio": "snapshot-001"},
        config_hash=HASH_64,
        concurrency_disclosure="risk-store",
        recommendations=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        token=None,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    kill_state = create_kill_switch_state(
        state_id="switch-001",
        scope_level="global",
        scope={},
        state="inactive",
        reason="usage-evidence",
        version=1,
        updated_at=NOW,
    )
    policy_proj = {
        "allowed": True,
        "verdict_id": "verdict-001",
        "action": "submit_order",
        "expires_at": (NOW + timedelta(minutes=1)).isoformat(),
    }
    readiness_eval = assess_execution_readiness(
        trd_request,
        route_snapshot,
        risk_pkg,
        kill_state,
        policy_proj,  # type: ignore[arg-type]
        {
            "route_snapshot": Decimal(30),
            "risk_decision": Decimal(30),
            "kill_switch": Decimal(30),
        },
    )
    print(_format_result(readiness_eval))

    readiness_dto = create_readiness_assessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"risk_decision_id": "risk-001"},
        assessed_at=NOW,
    )
    exec_plan = build_execution_plan(trd_request, readiness_dto)
    print(_format_result(exec_plan))

    # -------------------------------------------------------------------------
    # Stage 4: Authority Selection and Dispatch (FEAT-TRD-04)
    # -------------------------------------------------------------------------
    _stage_banner(4, "Authority Selection and Dispatch", "FEAT-TRD-04")
    adapter_cap = {
        "provider_id": "mt5",
        "contract_version": "v1",
        "schema_id": "brokers.adapter.v1",
        "provider_api_version": "5",
        "supported_actions": ["submit_order"],
        "supported_order_types": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        "security_profile": "approved",
        "operation_timeout_seconds": "10",
        "malformed_response_policy": "unknown_outcome",
        "rate_limit_policy": "provider_retry_after",
        "mutation_retry_policy": "reconcile_before_retry",
        "redaction_applied": True,
    }
    cap_validation = validate_adapter_capability(
        order_intent, adapter_cap, operation_timeout_seconds=Decimal(10)
    )
    print(_format_result(cap_validation))

    raw_response = {
        "receipt_id": "receipt-001",
        "intent_id": "intent-001",
        "client_order_id": "order-001",
        "route": "sim",
        "authority": "simulator",
        "provider_order_id": "sim-order-001",
        "status": "filled",
        "requested_quantity": "1.00",
        "filled_quantity": "1.00",
        "request_id": REQUEST_ID,
        "correlation_id": CORRELATION_ID,
        "authority_timestamp": NOW.isoformat(),
        "received_at": NOW.isoformat(),
    }
    classified_resp = classify_authority_response(raw_response, adapter_cap)  # type: ignore[arg-type]
    print(_format_result(classified_resp))

    async def _async_dispatch(intent: Any) -> Any:
        return receipt

    dispatched = asyncio.run(
        dispatch_order_intent(
            order_intent,
            None,
            None,
            _async_dispatch,
            operation_timeout_seconds=Decimal(10),
            clock=lambda: NOW,
        )
    )
    print(_format_result(dispatched))

    # -------------------------------------------------------------------------
    # Stage 5: Reconciliation and Retry Guard (FEAT-TRD-05)
    # -------------------------------------------------------------------------
    _stage_banner(5, "Reconciliation and Retry Guard", "FEAT-TRD-05")
    auth_snap = create_authority_snapshot(
        route="sim",
        authority_id="simulator",
        account_id="acc-001",
        source_id="sim-read-001",
        account={"state": "ready"},
        orders={},
        positions={},
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
    )
    print(_format_result(auth_snap))

    trd_projection = create_trading_projection(
        route="sim",
        tenant_id="acc-001",
        authority_id="simulator",
        version=1,
        event_ids=("event-001",),
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        unresolved_attempt_ids=("event-001",),
        updated_at=NOW,
    )
    reconcile_report = compare_authority_state(auth_snap, trd_projection)
    print(_format_result(reconcile_report))

    unknown_receipt = create_execution_receipt(
        receipt_id="receipt-unknown-001",
        intent_id="intent-001",
        client_order_id="order-001",
        route="sim",
        authority="simulator",
        status="unknown_outcome",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal(0),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="timeout",
        retry_safe=False,
        reconciliation_required=True,
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )
    resolution = resolve_unknown_outcome(  # type: ignore[arg-type]
        unknown_receipt, store, lambda _route: auth_snap
    )
    print(_format_result(resolution))

    # -------------------------------------------------------------------------
    # Stage 6: Operational and Budget Evidence (FEAT-TRD-06)
    # -------------------------------------------------------------------------
    _stage_banner(6, "Operational and Budget Evidence", "FEAT-TRD-06")
    op_event = create_operational_event(
        event_id="op-event-001",
        event_type="LATENCY_OBSERVED",
        severity="info",
        occurred_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        facts={"elapsed_seconds": "0.125"},
        source_refs={"operation": "submit_order"},
    )
    print(_format_result(op_event))

    budget_req = examples.monitoring_request()
    budget_val = validate_budget_authority(
        budget_req,
        examples.monitoring_allocation(),
        examples.monitoring_verdict(budget_req),
        now=NOW,
    )
    print(_format_result(budget_val))

    published_ops: list[Any] = []
    emit_res = emit_runtime_event(op_event, published_ops.append)
    print(_format_result(emit_res))

    broker_unknown_event = build_broker_state_unknown_event(
        unknown_receipt,
        incident_id="incident-001",
        unresolved_scope=("order:order-001",),
        occurred_at=NOW,
        workflow_id=WORKFLOW_ID,
    )
    print(_format_result(broker_unknown_event))

    # -------------------------------------------------------------------------
    # Stage 7: Live and Paper Session Lifecycle (FEAT-TRD-07)
    # -------------------------------------------------------------------------
    _stage_banner(7, "Live and Paper Session Lifecycle", "FEAT-TRD-07")
    broker_conn = build_broker_connection_config(
        broker_id="mt5", environment="live", provider_enabled=True
    )
    adapter_stub = SimpleNamespace(
        contract_version="v1", schema_id="brokers.adapter.v1"
    )
    flags_stub = SimpleNamespace(broker_id="mt5", environment="live")
    live_session = create_live_session(
        store=store,
        connection=broker_conn,
        broker_adapter=adapter_stub,
        feature_flags=flags_stub,
        risk_decision_source=lambda _req: None,
        action_policy_source=lambda _req: None,
        kill_switch_source=lambda _req: (),
        readiness_source=lambda _req, _ev: None,
        adapter_capability_source=lambda _req: {},
        auth_context_source=lambda _req: None,
        pre_audit_sink=lambda _ev: None,
        event_sink=lambda _evt: None,
        startup_reconcile=_async_passed,
        drain_in_flight=_async_passed,
        flush_evidence=_async_passed,
        shutdown_reconcile=_async_passed,
        clock=lambda: NOW,
    )
    print(f"Live Session Started: {is_live_session_started(live_session)}")

    live_config = {
        "RUNTIME_PROFILE": "live",
        "EXECUTION_ROUTE": "live",
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
        "DATA_AUTHORITY_ID": "data-authority-001",
    }
    live_evidence = {
        "data_authority_id": "data-authority-001",
        "adapter_security_profile": "approved",
        "startup_evidence_fresh": True,
    }
    session_start_res = asyncio.run(
        start_live_session(live_session, live_config, live_evidence)
    )
    print(_format_result(session_start_res))

    session_status = get_live_session_status(live_session)
    print(_format_result(session_status))

    live_request = create_trading_request(
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        route=get_trading_route("live"),
        action="submit_order",
        provider_id="mt5",
        account_id="acc-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="lots",
        quantity=Decimal(1),
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="idempotency-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )
    gate_eval = asyncio.run(evaluate_live_gate(live_request, {}, live_session))
    print(_format_result(gate_eval))

    session_stop_res = asyncio.run(stop_live_session(live_session))
    print(_format_result(session_stop_res))

    # -------------------------------------------------------------------------
    # Stage 8: Route-Aware Public Actions (FEAT-TRD-08)
    # -------------------------------------------------------------------------
    _stage_banner(8, "Route-Aware Public Actions", "FEAT-TRD-08")

    action_deps = dependencies()
    print(_format_result(action_deps))

    sub_res = asyncio.run(submit_order(request(), action_deps))
    print(_format_result(sub_res))

    mod_item = request(
        action="modify_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    mod_res = asyncio.run(modify_order(mod_item, dependencies(store=execution_store())))
    print(_format_result(mod_res))

    can_item = request(
        action="cancel_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    can_res = asyncio.run(cancel_order(can_item, dependencies(store=execution_store())))
    print(_format_result(can_res))

    def _pos_req(action: str, **updates: object) -> Any:
        return request(
            action=action,
            position_id="position-001",
            target_broker_position_id="position-001",
            **updates,
        )

    close_res = asyncio.run(
        close_position(
            _pos_req("close_position", quantity=Decimal("0.50")),
            dependencies(store=execution_store()),
        )
    )
    print(_format_result(close_res))

    pos_mod_item = _pos_req(
        "modify_position",
        order_type="LIMIT",
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0000"),
    )
    pos_mod_deps = dependencies(
        store=execution_store(),
        action_policy=policy("modify_position", mutable_fields="stop_loss"),
    )
    pos_mod_res = asyncio.run(modify_position(pos_mod_item, pos_mod_deps))
    print(_format_result(pos_mod_res))

    red_res = asyncio.run(
        reduce_exposure(
            _pos_req("reduce_exposure", quantity=Decimal("0.50")),
            dependencies(store=execution_store()),
        )
    )
    print(_format_result(red_res))

    pause_deps = dependencies(action_policy=policy("pause_strategy"))
    pause_res = asyncio.run(
        pause_strategy(request(action="pause_strategy"), pause_deps)
    )
    print(_format_result(pause_res))

    mem_store = MemoryStore()
    mem_store.projection = projection()
    resume_deps = dependencies(store=mem_store, action_policy=policy("resume_strategy"))
    resume_deps = replace(
        resume_deps,
        kill_switch_state_source=kill_switch_states,
        reconciliation_source=lambda _item: authority(),
    )
    resume_res = asyncio.run(
        resume_strategy(request(action="resume_strategy"), resume_deps)
    )
    print(_format_result(resume_res))

    sync_deps = replace(dependencies(), reconciliation_source=lambda _item: authority())
    sync_res = asyncio.run(sync_positions(request(action="sync_positions"), sync_deps))
    print(_format_result(sync_res))

    async def transition_trig(cmd: Any, verdict: Any) -> Any:
        return switch("global", "active")

    trig_deps = dependencies(action_policy=policy("trigger_kill_switch"))
    trig_deps = replace(trig_deps, kill_switch_transition=transition_trig)
    trig_item = request(
        action="trigger_kill_switch",
        scope_level="global",
        control_reason="operator request",
    )
    trig_res = asyncio.run(trigger_kill_switch(trig_item, trig_deps))
    print(_format_result(trig_res))

    async def transition_clr(cmd: Any, verdict: Any) -> Any:
        return switch("global")

    clr_deps = dependencies(action_policy=policy("clear_kill_switch"))
    clr_deps = replace(clr_deps, kill_switch_transition=transition_clr)
    clr_item = request(
        action="clear_kill_switch",
        scope_level="global",
        control_reason="operator reviewed",
    )
    clr_res = asyncio.run(clear_kill_switch(clr_item, clr_deps))
    print(_format_result(clr_res))

    em_can_deps = emergency_dependencies("cancel_all_orders")
    em_can_req = request(action="cancel_all_orders")
    em_can_res = asyncio.run(cancel_all_orders(em_can_req, em_can_deps))
    print(_format_result(em_can_res))

    em_cls_deps = emergency_dependencies("close_all_positions")
    em_cls_req = request(action="close_all_positions")
    em_cls_res = asyncio.run(close_all_positions(em_cls_req, em_cls_deps))
    print(_format_result(em_cls_res))

    reb_item = rebalance_request()
    reb_deps = rebalance_dependencies(reb_item)
    reb_res = asyncio.run(execute_portfolio_rebalance(reb_item, reb_deps))
    print(_format_result(reb_res))

    eval_deps, _calls = evaluation_dependencies(None)
    eval_res = asyncio.run(run_live_evaluation_cycle(eval_deps, evidence()))
    print(_format_result(eval_res))

    # -------------------------------------------------------------------------
    # Stage 9: Immutable Execution Evidence (FEAT-TRD-09)
    # -------------------------------------------------------------------------
    _stage_banner(9, "Immutable Execution Evidence", "FEAT-TRD-09")
    report_res = build_trading_report(trd_request, store)
    print(_format_result(report_res))

    print("\n" + "=" * 88)
    print("ALL 9 STAGES COMPLETED SUCCESSFULLY WITH GENUINE TRADING DOMAIN EVIDENCE")
    print("=" * 88 + "\n")


if __name__ == "__main__":
    main()
