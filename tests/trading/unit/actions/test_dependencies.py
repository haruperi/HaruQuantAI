"""Shared fixtures and unit tests for Trading action dependencies."""

# ruff: noqa: ARG005, INP001
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal, cast

import pytest
from app.services.brokers import BrokerSymbolInfo
from app.services.data.evidence.account_contracts import (
    AccountBalance,
    AccountOrder,
    AccountPosition,
    AccountStateSnapshot,
)
from app.services.risk import (
    ActionPolicyVerdict,
    DecisionState,
    KillSwitchState,
    RiskApprovalToken,
    RiskDecisionPackage,
)
from app.services.trading.actions import TradingDependencies
from app.services.trading.contracts import (
    ExecutionReceipt,
    OrderIntent,
    PortfolioRebalanceExecutionRequest,
    TradingError,
    TradingRequest,
    TradingRoute,
)
from app.services.trading.state import (
    IdempotencyReservation,
    TradingEvent,
    TradingProjection,
)
from app.utils import logger

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
DATA_REQUEST_ID = "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class MemoryStore:
    """Minimal in-memory implementation of the Trading persistence port."""

    def __init__(self) -> None:
        """Initialize empty observable state."""
        self.projection: TradingProjection | None = None
        self.events: list[TradingEvent] = []
        self.reservations: dict[str, IdempotencyReservation] = {}

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> IdempotencyReservation:
        """Reserve or return one exact-material request key."""
        existing = self.reservations.get(key)
        if existing is not None:
            if existing.status in {
                "duplicate_completed",
                "reconciliation_required",
            }:
                return existing
            return existing.model_copy(update={"status": "duplicate_active"})
        reservation = IdempotencyReservation(
            key=key,
            material_hash=material_hash,
            material_version=material_version,
            status="new",
            reserved_at=reserved_at,
            expires_at=expires_at,
        )
        self.reservations[key] = reservation
        return reservation

    def append_event(self, event: TradingEvent) -> None:
        """Append one event."""
        self.events.append(event)

    def complete_idempotency(
        self,
        key: str,
        material_hash: str,
        receipt_id: str,
        completed_at: datetime,
        *,
        status: Literal["completed", "reconciliation_required"],
    ) -> None:
        """Persist a terminal or reconciliation-required reservation outcome."""
        existing = self.reservations[key]
        assert existing.material_hash == material_hash
        reservation_status = (
            "duplicate_completed"
            if status == "completed"
            else "reconciliation_required"
        )
        self.reservations[key] = existing.model_copy(
            update={
                "status": reservation_status,
                "receipt_id": receipt_id,
                "reserved_at": completed_at,
            }
        )

    def load_projection(self, scope) -> TradingProjection | None:
        """Load the current projection when its scope matches."""
        if self.projection is None:
            return None
        if (
            self.projection.route,
            self.projection.tenant_id,
            self.projection.authority_id,
        ) == scope:
            return self.projection
        return None

    def save_projection(
        self, projection: TradingProjection, expected_version: int
    ) -> None:
        """Save one optimistic projection."""
        current = 0 if self.projection is None else self.projection.version
        assert current == expected_version
        self.projection = projection

    def load_unresolved_attempts(self, _scope) -> tuple[TradingEvent, ...]:
        """Return persisted attempts still unresolved in the projection."""
        unresolved = (
            set()
            if self.projection is None
            else set(self.projection.unresolved_attempt_ids)
        )
        return tuple(event for event in self.events if event.event_id in unresolved)

    def load_report_evidence(self, _scope):
        """Return bounded empty report evidence in the fixture."""
        return {}


def request(**updates: object) -> TradingRequest:
    """Build one complete canonical Simulation request."""
    base: dict[str, object] = {
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "route": TradingRoute.SIM,
        "action": "submit_order",
        "provider_id": None,
        "account_id": "account-001",
        "strategy_id": "strategy-001",
        "strategy_version": "v1",
        "intent_id": "intent-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity_unit": "lots",
        "quantity": Decimal("1.00"),
        "risk_decision_id": "risk-001",
        "action_policy_verdict_id": "policy-001",
        "approval_token_ref": "token-001",
        "idempotency_key": "idempotency-001",
        "canonical_material_version": "v1",
        "system_time": NOW,
        "valid_until": NOW + timedelta(minutes=10),
        "instrument_min_quantity": Decimal("0.01"),
        "instrument_max_quantity": Decimal(10),
        "instrument_quantity_step": Decimal("0.01"),
        "instrument_price_tick": Decimal("0.0001"),
    }
    base.update(updates)
    return TradingRequest.model_validate(base)


def account_snapshot() -> AccountStateSnapshot:
    """Build current account, order, and position evidence."""
    return AccountStateSnapshot(
        account_id="account-001",
        currency="USD",
        balances=(
            AccountBalance(asset="USD", total=Decimal(10000), available=Decimal(9000)),
        ),
        equity=Decimal(10000),
        margin_available=Decimal(9000),
        positions=(
            AccountPosition(
                position_id="position-001",
                symbol="EURUSD",
                side="LONG",
                quantity=Decimal(2),
                entry_price=Decimal("1.1000"),
            ),
        ),
        orders=(
            AccountOrder(
                order_id="order-001",
                symbol="EURUSD",
                side="BUY",
                state="PENDING",
                quantity=Decimal(1),
            ),
            AccountOrder(
                order_id="order-filled",
                symbol="EURUSD",
                side="BUY",
                state="FILLED",
                quantity=Decimal(1),
            ),
        ),
        connected=True,
        trading_allowed=True,
        source_id="data-source-001",
        snapshot_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(minutes=10),
        request_id=DATA_REQUEST_ID,
    )


def policy(action: str = "submit_order", **scope: str) -> ActionPolicyVerdict:
    """Build one current allowed Risk action-policy verdict."""
    return ActionPolicyVerdict(
        verdict_id="policy-001",
        action=action,
        scope={"account_id": "account-001", **scope},
        policy_version="policy-v1",
        attestation_id="attestation-001",
        decision_id="risk-001",
        reservation_id="reservation-001",
        allowed=True,
        reasons=(),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def risk_decision(item: TradingRequest) -> RiskDecisionPackage:
    """Build an exact current Risk approval for one governed request."""
    token = RiskApprovalToken(
        token_id=item.approval_token_ref,
        decision_id=item.risk_decision_id,
        config_hash="config-hash",
        action=item.action,
        scope={"account_id": item.account_id},
        approver_id="risk-service",
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        nonce="nonce-001",
        signature="signature-001",
        request_id=item.request_id,
        workflow_id=item.workflow_id,
        correlation_id=item.correlation_id,
    )
    return RiskDecisionPackage(
        decision_id=item.risk_decision_id,
        intent_id=item.intent_id,
        state=DecisionState.APPROVE,
        requested_size=item.quantity,
        approved_size=item.quantity,
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"request": item.request_id},
        config_hash="config-hash",
        concurrency_disclosure="serialized",
        recommendations=(),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        token=token,
        request_id=item.request_id,
        workflow_id=item.workflow_id,
        correlation_id=item.correlation_id,
    )


def kill_switch_states(item: TradingRequest) -> tuple[KillSwitchState, ...]:
    """Build the exact inactive Risk kill-switch hierarchy for a request."""
    scopes = [
        ("global", {}),
        ("strategy", {"strategy_id": item.strategy_id}),
    ]
    if item.portfolio_id is not None:
        scopes.append(("portfolio", {"portfolio_id": item.portfolio_id}))
    if item.symbol is not None:
        scopes.append(("symbol", {"symbol": item.symbol}))
    return tuple(
        KillSwitchState(
            state_id=f"switch-{level}",
            scope_level=level,
            scope=scope,
            state="inactive",
            reason="clear",
            version=1,
            updated_at=NOW,
        )
        for level, scope in scopes
    )


def symbol_capability(route, provider_id, symbol):
    """Return normalized order-type evidence and exact Broker symbol metadata."""
    capability = {
        "provider_id": provider_id or "simulation",
        "contract_version": "v1",
        "schema_id": "brokers.adapter.v1",
        "provider_api_version": "v1",
        "supported_actions": [
            "submit_order",
            "modify_order",
            "cancel_order",
            "close_position",
            "modify_position",
            "reduce_exposure",
        ],
        "supported_order_types": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        "quantity_unit": "lots",
        "security_profile": "approved",
        "operation_timeout_seconds": "10",
        "malformed_response_policy": "unknown_outcome",
        "rate_limit_policy": "external",
        "mutation_retry_policy": "reconcile_before_retry",
        "redaction_applied": True,
    }
    info = BrokerSymbolInfo(
        provider_symbol=symbol,
        product_profile="fx",
        price_unit="quote",
        quantity_unit="lots",
        min_quantity=Decimal("0.01"),
        max_quantity=Decimal(10),
        quantity_step=Decimal("0.01"),
        price_step=Decimal("0.0001"),
    )
    return capability, info


async def simulation_dispatch(intent: OrderIntent) -> ExecutionReceipt:
    """Return one accepted Simulation authority receipt."""
    return ExecutionReceipt(
        receipt_id=f"receipt-{intent.request_id}",
        intent_id=intent.source_intent_id,
        client_order_id=intent.client_order_id,
        route=intent.route,
        authority="simulation",
        provider_order_id="sim-order-001",
        status="accepted",
        requested_quantity=intent.approved_volume,
        filled_quantity=Decimal(0),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="accepted",
        retry_safe=False,
        reconciliation_required=False,
        request_id=intent.request_id,
        correlation_id=intent.correlation_id,
    )


def rebalance_action_resolver(
    parent: PortfolioRebalanceExecutionRequest,
    action: dict[str, object],
) -> TradingRequest:
    """Resolve one Portfolio exposure reduction into a governed order request.

    Args:
        parent: Authorized immutable Portfolio plan request.
        action: One validated high-level exposure reduction.

    Returns:
        Trading-owned fully specified reduce-exposure request.
    """
    logger.debug("Resolving a Portfolio exposure reduction in Trading")
    action_id = str(action["action_id"])
    return request(
        request_id=action_id,
        workflow_id=parent.workflow_id,
        correlation_id=parent.correlation_id,
        causation_id=None,
        route=parent.route,
        action="reduce_exposure",
        portfolio_id=parent.portfolio_id,
        side="SELL",
        quantity=Decimal("0.50"),
        target_broker_position_id="position-001",
        position_id="position-001",
        expected_version=1,
        allocation_decision_id=parent.allocation_decision_id,
        eligibility_decision_id=str(action["eligibility_decision_id"]),
        idempotency_key=f"{parent.plan_id}:{action_id}",
    )


def dependencies(
    *,
    store: MemoryStore | None = None,
    action_policy: ActionPolicyVerdict | None = None,
) -> TradingDependencies:
    """Build complete dependencies with inert unused evaluation ports."""
    memory = store or MemoryStore()

    async def unavailable(*args):
        """Fail if an unrelated evaluation port is unexpectedly used."""
        raise AssertionError("unexpected evaluation port")

    async def transition(command, verdict):
        """Fail if an unrelated transition port is unexpectedly used."""
        raise AssertionError("unexpected transition port")

    def policy_for(item: TradingRequest) -> ActionPolicyVerdict:
        """Bind the selected test policy to the exact child trace."""
        selected = action_policy or policy(item.action)
        return selected.model_copy(
            update={
                "request_id": item.request_id,
                "workflow_id": item.workflow_id,
                "correlation_id": item.correlation_id,
            }
        )

    return TradingDependencies(
        store=memory,
        connection=None,
        broker_adapter=None,
        simulation_dispatch=simulation_dispatch,
        live_session=None,
        clock=lambda: NOW,
        idempotency_retention_seconds=600,
        concurrency_lock_timeout_seconds=Decimal(30),
        broker_operation_timeout_seconds=Decimal(10),
        max_staleness_seconds={
            "route_snapshot": Decimal(30),
            "risk_decision": Decimal(30),
            "kill_switch": Decimal(30),
        },
        event_sink=lambda event: None,
        account_state_source=lambda item: account_snapshot(),
        symbol_capability_source=symbol_capability,
        action_policy_source=policy_for,
        kill_switch_state_source=kill_switch_states,
        allocation_decision_source=lambda item: None,
        budget_verdict_source=lambda item: None,
        eligibility_source=lambda item: (),
        rebalance_action_resolver=rebalance_action_resolver,
        kill_switch_transition=transition,
        reconciliation_source=cast("object", lambda item: None),
        market_data_source=unavailable,
        evaluation_account_source=unavailable,
        market_context_source=unavailable,
        indicator_source=unavailable,
        strategy_source=unavailable,
        risk_source=unavailable,
        child_risk_decision_source=lambda item: None,
        execution_risk_decision_source=risk_decision,
    )


def execution_store() -> MemoryStore:
    """Build Trading state containing exact broker order and position targets."""
    store = MemoryStore()
    store.projection = TradingProjection(
        route="sim",
        tenant_id="account-001",
        authority_id="simulation",
        version=1,
        orders={"order-001": {"symbol": "EURUSD", "broker_order_id": "order-001"}},
        positions={
            "position-001": {
                "symbol": "EURUSD",
                "broker_position_id": "position-001",
            }
        },
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )
    return store


def test_dependencies_have_no_import_side_effect() -> None:
    """Dependency construction does not create routes, stores, or secrets."""
    deps = dependencies()
    assert deps.connection is None
    assert deps.broker_adapter is None


def test_dependencies_are_immutable() -> None:
    """The action dependency container is frozen after composition."""
    deps = dependencies()
    with pytest.raises(FrozenInstanceError):
        deps.connection = cast("object", object())


def test_dependencies_reject_explicit_missing_required_port() -> None:
    """Explicitly absent required ports fail at composition time."""
    with pytest.raises(TradingError, match="SERVICE_UNAVAILABLE"):
        dependencies().__class__(
            **{
                name: getattr(dependencies(), name)
                for name in dependencies().__dataclass_fields__
                if name != "store"
            },
            store=None,
        )
