# ruff: noqa: ARG002 -- test doubles mirror real port signatures.
"""Tests for the concrete 16-step live gate pipeline (BF-TRD-003, BF-TRD-004).

Every gate must block in isolation and short-circuit the remainder as
diagnostic-skipped. The happy path must reach DISPATCH and return a
non-``packaged_only`` side effect -- the acceptance criterion for retiring
``app/services/trader``.
"""

from __future__ import annotations

import concurrent.futures
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading.contracts import (
    MutationCapability,
    NormalizedTradeResult,
    PromotionStage,
    QuoteSnapshot,
    RetrySafety,
    SideEffectMode,
    TradingAction,
    TradingRequestEnvelope,
    TradingRoute,
    TradingStatus,
)
from app.services.trading.execution.broker_capability_validation import (
    BrokerCapabilityProfile,
)
from app.services.trading.gates._common import GateName, GateStepStatus
from app.services.trading.gates.kill_switch import (
    KillSwitchScope,
    KillSwitchState,
    OperationalMode,
)
from app.services.trading.gates.live_pipeline import (
    LiveGateEvidence,
    LiveGatePipelineImpl,
    passthrough_risk_evaluator,
)
from app.services.trading.gates.pipeline import (
    ComplianceEvidence,
    MarketTurbulenceMonitor,
)
from app.services.trading.gates.policy_matrix import PolicyMatrix, PolicyMatrixEntry
from app.services.trading.gates.readiness import (
    BrokerReadinessEvidence,
    ClockDriftEvidence,
)
from app.services.trading.reconciliation.authority_and_retry_guard import (
    AuthorityAndRetryGuard,
)
from app.services.trading.runtime.coordination import ConcurrencyLockManager
from app.services.trading.runtime.session_manager import SessionState
from app.services.trading.state.trade_store import InMemoryTradeStore

ACCOUNT = "acct-1"
SYMBOL = "EURUSD"
TENANT = "tenant-1"


class FakeClock:
    def now_utc(self) -> datetime:
        return datetime(2026, 7, 9, 10, 0, tzinfo=UTC)

    def now_ptp(self) -> datetime:
        return self.now_utc()

    def monotonic(self) -> float:
        return 0.0


class FakeSessionManager:
    def __init__(
        self,
        state: SessionState = SessionState.RUNNING,
        mode: OperationalMode = OperationalMode.NORMAL,
        halted: tuple[str, ...] = (),
    ) -> None:
        self.state = state
        self.mode = mode
        self._halted = set(halted)

    def is_symbol_halted(self, symbol: str) -> bool:
        return symbol in self._halted


class FakeAuditSink:
    def __init__(self, fail: bool = False) -> None:
        self.events: list[dict] = []
        self._fail = fail

    def append(self, *, event, recorded_at) -> str:
        if self._fail:
            raise OSError("audit sink unavailable")
        self.events.append(event)
        return f"audit-{len(self.events)}"

    def flush(self) -> None:
        return


class FakeIdempotencyStore:
    def __init__(self, decision: str = "reserved") -> None:
        self.decision = decision
        self.completed: list[str] = []

    def reserve(self, *, route, tenant_id, key, material_hash, expires_at) -> dict:
        return {"decision": self.decision}

    def resolve(self, **_) -> dict | None:
        return None

    def complete(self, *, route, tenant_id, key, outcome, completed_at) -> None:
        self.completed.append(key)


class SyncExecutor:
    """Runs the dispatch callable inline and wraps it in a resolved Future."""

    def __init__(self) -> None:
        self.calls = 0

    def submit(self, dispatch_callable):
        self.calls += 1
        future: concurrent.futures.Future = concurrent.futures.Future()
        try:
            future.set_result(dispatch_callable())
        except BaseException as exc:  # noqa: BLE001
            future.set_exception(exc)
        return future


class TimeoutExecutor:
    """Returns a Future that never resolves, forcing a dispatch timeout."""

    def __init__(self) -> None:
        self.calls = 0

    def submit(self, dispatch_callable):
        self.calls += 1
        return concurrent.futures.Future()


class FakeBroker:
    """Records the dispatch payload and returns a canned normalized result."""

    def __init__(self, retcode: str = "10009", raises: Exception | None = None) -> None:
        self.retcode = retcode
        self.raises = raises
        self.payloads: list[dict] = []

    def factory(self, payload, request_id):
        def _dispatch() -> NormalizedTradeResult:
            if self.raises is not None:
                raise self.raises
            self.payloads.append(payload)
            return NormalizedTradeResult(
                retcode=self.retcode,
                order="ord-9001",
                deal="deal-9001",
                volume=Decimal("0.10"),
                price=Decimal("1.10010"),
                request_id=request_id,
                provider="mt5",
            )

        return _dispatch


def _quote() -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=SYMBOL,
        bid=Decimal("1.09990"),
        ask=Decimal("1.10010"),
        spread=Decimal("0.00020"),
        timestamp="2026-07-09T10:00:00+00:00",
        source="test",
        freshness_age_ms=5,
    )


def _request(
    action: TradingAction = TradingAction.SUBMIT_ORDER,
) -> TradingRequestEnvelope:
    return TradingRequestEnvelope(
        route=TradingRoute.LIVE,
        action=action,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-1",
        correlation_id="corr-1",
        symbol=SYMBOL,
        payload={"side": "buy", "volume": "0.10", "price": "1.10010"},
        quote_snapshot=_quote(),
    )


def _evidence(**overrides) -> LiveGateEvidence:
    defaults = {
        "account_id": ACCOUNT,
        "strategy_id": "strat-1",
        "compliance_evidence": ComplianceEvidence(),
        "broker_readiness": BrokerReadinessEvidence(
            connected=True,
            trade_allowed=True,
            account_permissions_ok=True,
            rate_limit_available=True,
        ),
        "clock_drift": ClockDriftEvidence(offset_ms=Decimal(5)),
        "capability_profile": BrokerCapabilityProfile(
            provider="mt5",
            supported_order_types=("market",),
            supported_filling_modes=("IOC",),
            price_precision_digits=5,
            volume_precision_step=Decimal("0.01"),
            max_requests_per_second=Decimal(10),
        ),
        "idempotency_key": "idem-1",
        "idempotency_material_hash": "hash-1",
        "idempotency_expires_at": datetime(2026, 7, 9, 10, 5, tzinfo=UTC),
    }
    defaults.update(overrides)
    return LiveGateEvidence(**defaults)


def _policy_matrix(requires_approval: bool = False) -> PolicyMatrix:
    """Cover every action, so tests exercise the gate under test.

    A missing entry fails closed at the kill-switch gate with
    TRADING_POLICY_UNDEFINED, which would mask whatever the test is asserting.
    """
    return PolicyMatrix(
        entries={
            action: PolicyMatrixEntry(
                action=action, requires_approval=requires_approval
            )
            for action in TradingAction
        }
    )


def _pipeline(
    *,
    broker: FakeBroker | None = None,
    executor=None,
    evidence: LiveGateEvidence | None = None,
    policy_matrix: PolicyMatrix | None = None,
    session_manager=None,
    idempotency_store=None,
    audit_sink=None,
    authority_guard=None,
    lock_manager=None,
    reconciliation_hook=None,
    risk_evaluator=passthrough_risk_evaluator,
) -> tuple[LiveGatePipelineImpl, FakeBroker]:
    broker = broker or FakeBroker()
    return (
        LiveGatePipelineImpl(
            clock=FakeClock(),
            tenant_id=TENANT,
            evidence=evidence or _evidence(),
            policy_matrix=policy_matrix or _policy_matrix(),
            session_manager=session_manager or FakeSessionManager(),
            turbulence_monitor=MarketTurbulenceMonitor(
                window_size=5, velocity_threshold_bps=Decimal(500)
            ),
            idempotency_store=idempotency_store or FakeIdempotencyStore(),
            lock_manager=lock_manager or ConcurrencyLockManager(),
            authority_guard=authority_guard or AuthorityAndRetryGuard(),
            audit_sink=audit_sink or FakeAuditSink(),
            trade_store=InMemoryTradeStore(),
            dispatch_executor=executor or SyncExecutor(),
            dispatch_callable_factory=broker.factory,
            risk_evaluator=risk_evaluator,
            reconciliation_hook=reconciliation_hook or (lambda: None),
        ),
        broker,
    )


def _gate_status(response, gate: GateName) -> str | None:
    for step in response.data["gate_decision"]["steps"]:
        if step["gate"] == gate.value:
            return step["status"]
    return None


# ----------------------------------------------------------------------
# Acceptance criterion: the pipeline actually dispatches.
# ----------------------------------------------------------------------


def test_happy_path_dispatches_and_is_not_packaged_only() -> None:
    pipeline, broker = _pipeline()
    response = pipeline.evaluate(_request())

    assert response.side_effect_mode is SideEffectMode.BROKER_MUTATION_CONFIRMED
    assert response.side_effect_mode is not SideEffectMode.PACKAGED_ONLY
    assert response.status is TradingStatus.SUCCESS
    assert response.retry_safety is RetrySafety.DO_NOT_RETRY
    assert len(broker.payloads) == 1


def test_dispatch_payload_carries_request_fields() -> None:
    pipeline, broker = _pipeline()
    pipeline.evaluate(_request())
    payload = broker.payloads[0]
    assert payload["side"] == "buy"
    assert payload["volume"] == "0.10"


def test_all_sixteen_gates_run_on_happy_path() -> None:
    pipeline, _ = _pipeline()
    response = pipeline.evaluate(_request())
    gates = [s["gate"] for s in response.data["gate_decision"]["steps"]]
    assert gates == [g.value for g in GateName]


def test_success_envelope_carries_audit_ref() -> None:
    sink = FakeAuditSink()
    pipeline, _ = _pipeline(audit_sink=sink)
    response = pipeline.evaluate(_request())
    assert response.audit_ref == "audit-1"


def test_in_flight_counter_drains_after_dispatch() -> None:
    pipeline, _ = _pipeline()
    pipeline.evaluate(_request())
    assert pipeline.coordinator.in_flight.is_drained()


def test_order_state_persisted_and_idempotency_completed() -> None:
    store = FakeIdempotencyStore()
    pipeline, _ = _pipeline(idempotency_store=store)
    pipeline.evaluate(_request())
    assert store.completed == ["idem-1"]


# ----------------------------------------------------------------------
# Each gate blocks in isolation and short-circuits the rest.
# ----------------------------------------------------------------------


def test_gate_01_local_schema_blocks_on_empty_payload() -> None:
    pipeline, broker = _pipeline()
    request = _request().model_copy(update={"payload": {}})
    response = pipeline.evaluate(request)
    assert response.error.code == "VALIDATION_FAILED"
    assert _gate_status(response, GateName.LOCAL_SCHEMA_VALIDATION) == "blocked"
    assert broker.payloads == []


def test_gate_02_compliance_blocks_restricted_symbol() -> None:
    pipeline, broker = _pipeline(
        evidence=_evidence(
            compliance_evidence=ComplianceEvidence(restricted_symbols=(SYMBOL,))
        )
    )
    response = pipeline.evaluate(_request())
    assert response.error.code == "POLICY_BLOCKED"
    assert _gate_status(response, GateName.COMPLIANCE) == "blocked"
    assert broker.payloads == []


def test_gate_03_promotion_stage_blocks_incompatible_capability() -> None:
    pipeline, broker = _pipeline()
    request = _request().model_copy(
        update={"mutation_capability": MutationCapability.FULL_LIVE}
    )
    response = pipeline.evaluate(request)
    assert _gate_status(response, GateName.PROMOTION_STAGE) == "blocked"
    assert broker.payloads == []


def test_gate_04_session_status_blocks_when_not_running() -> None:
    pipeline, broker = _pipeline(
        session_manager=FakeSessionManager(state=SessionState.PAUSED)
    )
    response = pipeline.evaluate(_request())
    assert response.error.code == "SERVICE_UNAVAILABLE"
    assert _gate_status(response, GateName.SESSION_STATUS) == "blocked"
    assert broker.payloads == []


def test_gate_04_session_status_blocks_read_only_mode() -> None:
    pipeline, _ = _pipeline(
        session_manager=FakeSessionManager(mode=OperationalMode.READ_ONLY)
    )
    response = pipeline.evaluate(_request())
    assert response.error.code == "POLICY_BLOCKED"


def test_gate_04_session_status_blocks_halted_symbol() -> None:
    pipeline, broker = _pipeline(session_manager=FakeSessionManager(halted=(SYMBOL,)))
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.SESSION_STATUS) == "blocked"
    assert broker.payloads == []


def test_gate_05_kill_switch_blocks_when_active() -> None:
    pipeline, broker = _pipeline(
        evidence=_evidence(
            kill_switches=(KillSwitchState(scope=KillSwitchScope.GLOBAL, active=True),)
        )
    )
    response = pipeline.evaluate(_request())
    assert response.error.code == "LIVE_KILL_SWITCH_ACTIVE"
    assert _gate_status(response, GateName.KILL_SWITCH) == "blocked"
    assert broker.payloads == []


def test_gate_05_undefined_policy_entry_fails_closed() -> None:
    """An action with no policy matrix entry must never dispatch."""
    empty = PolicyMatrix(entries={})
    pipeline, broker = _pipeline(policy_matrix=empty)
    response = pipeline.evaluate(_request())
    assert response.error.code == "TRADING_POLICY_UNDEFINED"
    assert _gate_status(response, GateName.KILL_SWITCH) == "blocked"
    assert broker.payloads == []


def test_gate_06_operator_approval_blocks_when_required_and_absent() -> None:
    pipeline, broker = _pipeline(policy_matrix=_policy_matrix(requires_approval=True))
    response = pipeline.evaluate(_request())
    assert response.error.code == "APPROVAL_REQUIRED"
    assert _gate_status(response, GateName.OPERATOR_APPROVAL) == "blocked"
    assert broker.payloads == []


def test_gate_06_approval_hash_binds_to_the_nested_intent() -> None:
    """actions/orders.py nests the order under payload['intent'].

    If the hash were computed from the flat payload it would be identical for
    every order, so an approval token issued for a 0.01-lot buy would validate
    a 100-lot sell. Two different intents must produce two different hashes.
    """
    pipeline, _ = _pipeline()
    small_buy = _request().model_copy(
        update={"payload": {"intent": {"side": "buy", "volume": "0.01"}}}
    )
    large_sell = _request().model_copy(
        update={"payload": {"intent": {"side": "sell", "volume": "100"}}}
    )
    assert pipeline._canonical_request_hash(
        small_buy
    ) != pipeline._canonical_request_hash(large_sell)


def test_gate_06_approval_hash_falls_back_to_flat_payload() -> None:
    pipeline, _ = _pipeline()
    flat_a = _request().model_copy(update={"payload": {"side": "buy", "volume": "1"}})
    flat_b = _request().model_copy(update={"payload": {"side": "sell", "volume": "1"}})
    assert pipeline._canonical_request_hash(flat_a) != pipeline._canonical_request_hash(
        flat_b
    )


def test_gate_07_risk_passthrough_passes_and_warns(caplog) -> None:
    pipeline, _ = _pipeline()
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.RISK_DECISION) == "passed"


def test_gate_07_risk_evaluator_can_block() -> None:
    from app.services.trading.gates._common import blocked_step

    def denying_risk() -> object:
        return blocked_step(
            gate=GateName.RISK_DECISION,
            reason_code="POLICY_BLOCKED",
            message="risk denied",
        )

    pipeline, broker = _pipeline(risk_evaluator=denying_risk)
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.RISK_DECISION) == "blocked"
    assert broker.payloads == []


def test_gate_08_turbulence_blocks_on_velocity_breach() -> None:
    monitor = MarketTurbulenceMonitor(
        window_size=2, velocity_threshold_bps=Decimal("0.0001")
    )
    monitor.observe(symbol=SYMBOL, mid_price=Decimal("1.00000"))
    pipeline, broker = _pipeline()
    pipeline._turbulence_monitor = monitor
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.MARKET_TURBULENCE) == "blocked"
    assert broker.payloads == []


def test_gate_09_broker_readiness_blocks_when_disconnected() -> None:
    pipeline, broker = _pipeline(
        evidence=_evidence(
            broker_readiness=BrokerReadinessEvidence(
                connected=False,
                trade_allowed=True,
                account_permissions_ok=True,
                rate_limit_available=True,
            )
        )
    )
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.BROKER_READINESS) == "blocked"
    assert broker.payloads == []


def test_gate_09_broker_readiness_blocks_when_rate_limited() -> None:
    pipeline, _ = _pipeline(
        evidence=_evidence(
            broker_readiness=BrokerReadinessEvidence(
                connected=True,
                trade_allowed=True,
                account_permissions_ok=True,
                rate_limit_available=False,
            )
        )
    )
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.BROKER_READINESS) == "blocked"


def test_gate_10_clock_drift_blocks_beyond_threshold() -> None:
    pipeline, broker = _pipeline(
        evidence=_evidence(clock_drift=ClockDriftEvidence(offset_ms=Decimal(100_000)))
    )
    response = pipeline.evaluate(_request())
    assert response.error.code == "CLOCK_DRIFT_DETECTED"
    assert _gate_status(response, GateName.CLOCK_DRIFT) == "blocked"
    assert broker.payloads == []


def test_gate_11_idempotency_blocks_duplicate() -> None:
    pipeline, broker = _pipeline(
        idempotency_store=FakeIdempotencyStore(decision="duplicate_in_progress")
    )
    response = pipeline.evaluate(_request())
    assert response.error.code == "LIVE_IDEMPOTENCY_CONFLICT"
    assert _gate_status(response, GateName.IDEMPOTENCY) == "blocked"
    assert broker.payloads == []


def test_gate_12_concurrency_blocks_when_lease_held() -> None:
    lock_manager = ConcurrencyLockManager()
    assert lock_manager.acquire_lock(ACCOUNT, SYMBOL, timeout=0.1)
    pipeline, broker = _pipeline(lock_manager=lock_manager)
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.CONCURRENCY_LEASE) == "blocked"
    assert broker.payloads == []


def test_gate_12_lease_released_after_success() -> None:
    lock_manager = ConcurrencyLockManager()
    pipeline, _ = _pipeline(lock_manager=lock_manager)
    pipeline.evaluate(_request())
    # The lease must be free again, or the next request would deadlock.
    assert lock_manager.acquire_lock(ACCOUNT, SYMBOL, timeout=0.1)


def test_gate_12_lease_released_after_downstream_block() -> None:
    lock_manager = ConcurrencyLockManager()
    pipeline, _ = _pipeline(
        lock_manager=lock_manager, audit_sink=FakeAuditSink(fail=True)
    )
    pipeline.evaluate(_request())
    assert lock_manager.acquire_lock(ACCOUNT, SYMBOL, timeout=0.1)


def test_gate_13_reconciliation_authority_blocks_on_stream_gap() -> None:
    guard = AuthorityAndRetryGuard()
    guard.report_stream_gap(ACCOUNT, SYMBOL)
    pipeline, broker = _pipeline(authority_guard=guard)
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.RECONCILIATION_AUTHORITY) == "blocked"
    assert broker.payloads == []


def test_gate_14_audit_blocks_on_sink_failure() -> None:
    pipeline, broker = _pipeline(audit_sink=FakeAuditSink(fail=True))
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.AUDIT_PRE_RECORD) == "blocked"
    assert broker.payloads == []


def test_gate_15_adapter_permission_blocks_unsupported_filling_mode() -> None:
    pipeline, broker = _pipeline(evidence=_evidence(filling_mode="RETURN"))
    response = pipeline.evaluate(_request())
    assert _gate_status(response, GateName.ADAPTER_PERMISSION) == "blocked"
    assert broker.payloads == []


def test_gate_15_tolerates_absent_volume_and_price() -> None:
    """A full position close packages volume=None; a market order price=None.

    Decimal(str(None)) raises ConversionSyntax, so absence must be distinguished
    from zero rather than coerced through str().
    """
    pipeline, broker = _pipeline()
    request = _request(action=TradingAction.CLOSE_POSITION).model_copy(
        update={
            "payload": {
                "close_mode": "by_ticket",
                "ticket": "pos-1",
                "volume": None,
                "price": None,
            }
        }
    )
    response = pipeline.evaluate(request)
    assert response.status is TradingStatus.SUCCESS
    assert len(broker.payloads) == 1


def test_gate_15_falls_back_to_quote_ask_when_price_absent() -> None:
    pipeline, _ = _pipeline()
    request = _request().model_copy(
        update={"payload": {"side": "buy", "volume": "0.10", "price": None}}
    )
    response = pipeline.evaluate(request)
    assert _gate_status(response, GateName.ADAPTER_PERMISSION) == "passed"


def test_ticket_addressed_close_without_symbol_is_admitted() -> None:
    """position_close by ticket legitimately packages symbol=None.

    Gate 1 must not require a symbol for it, and the concurrency lease must
    resolve to a coherent scope rather than locking on an empty string.
    """
    pipeline, broker = _pipeline()
    request = _request(action=TradingAction.CLOSE_POSITION).model_copy(
        update={"symbol": None, "payload": {"ticket": "pos-1", "volume": None}}
    )
    response = pipeline.evaluate(request)
    assert response.status is TradingStatus.SUCCESS
    assert len(broker.payloads) == 1


def test_order_submission_still_requires_a_symbol() -> None:
    pipeline, broker = _pipeline()
    request = _request().model_copy(update={"symbol": None})
    response = pipeline.evaluate(request)
    assert _gate_status(response, GateName.LOCAL_SCHEMA_VALIDATION) == "blocked"
    assert broker.payloads == []


def test_symbol_resolution_falls_back_through_payload_then_quote() -> None:
    pipeline, _ = _pipeline()
    from_envelope = _request()
    assert pipeline._resolve_symbol(from_envelope) == SYMBOL

    from_payload = _request().model_copy(
        update={"symbol": None, "payload": {"symbol": "USDJPY"}}
    )
    assert pipeline._resolve_symbol(from_payload) == "USDJPY"

    from_quote = _request().model_copy(update={"symbol": None, "payload": {"a": 1}})
    assert pipeline._resolve_symbol(from_quote) == SYMBOL

    no_symbol_at_all = _request().model_copy(
        update={"symbol": None, "payload": {"a": 1}, "quote_snapshot": None}
    )
    assert pipeline._resolve_symbol(no_symbol_at_all) == "GLOBAL"


# ----------------------------------------------------------------------
# Gate 16: dispatch outcomes.
# ----------------------------------------------------------------------


def test_gate_16_broker_rejection_is_rejected_not_confirmed() -> None:
    pipeline, _broker = _pipeline(broker=FakeBroker(retcode="10004"))
    response = pipeline.evaluate(_request())
    assert response.status is TradingStatus.REJECTED
    assert response.side_effect_mode is SideEffectMode.BROKER_MUTATION_REJECTED
    assert response.retry_safety is RetrySafety.SAFE_TO_RETRY
    assert response.error.code == "LIVE_BROKER_REJECTED"


@pytest.mark.parametrize("retcode", ["10009", "10008", "0"])
def test_gate_16_trader_success_retcodes_preserved(retcode: str) -> None:
    pipeline, _ = _pipeline(broker=FakeBroker(retcode=retcode))
    response = pipeline.evaluate(_request())
    assert response.status is TradingStatus.SUCCESS


def test_gate_16_timeout_is_unknown_outcome_and_forces_reconciliation() -> None:
    reconciled: list[bool] = []
    pipeline, _broker = _pipeline(
        executor=TimeoutExecutor(),
        reconciliation_hook=lambda: reconciled.append(True),
    )
    pipeline._dispatch_timeout_seconds = 0.01
    response = pipeline.evaluate(_request())

    assert response.side_effect_mode is SideEffectMode.UNKNOWN_OUTCOME
    assert response.retry_safety is RetrySafety.RETRY_AFTER_RECONCILIATION
    assert response.error.code == "LIVE_UNKNOWN_OUTCOME"
    assert reconciled == [True]


def test_gate_16_timeout_drains_in_flight_counter() -> None:
    pipeline, _ = _pipeline(
        executor=TimeoutExecutor(), reconciliation_hook=lambda: None
    )
    pipeline._dispatch_timeout_seconds = 0.01
    pipeline.evaluate(_request())
    assert pipeline.coordinator.in_flight.is_drained()


def test_gate_16_broker_exception_is_mapped_not_raised() -> None:
    pipeline, _ = _pipeline(broker=FakeBroker(raises=ConnectionError("socket down")))
    response = pipeline.evaluate(_request())
    assert response.status is TradingStatus.ERROR
    assert response.side_effect_mode is SideEffectMode.BROKER_MUTATION_ATTEMPTED
    assert "socket down" not in response.message


def test_gate_16_failure_does_not_complete_idempotency() -> None:
    store = FakeIdempotencyStore()
    pipeline, _ = _pipeline(broker=FakeBroker(retcode="10004"), idempotency_store=store)
    pipeline.evaluate(_request())
    assert store.completed == []


# ----------------------------------------------------------------------
# Short-circuit semantics.
# ----------------------------------------------------------------------


def test_downstream_gates_are_diagnostic_skipped_after_a_block() -> None:
    pipeline, _ = _pipeline(
        evidence=_evidence(
            compliance_evidence=ComplianceEvidence(restricted_symbols=(SYMBOL,))
        )
    )
    response = pipeline.evaluate(_request())
    steps = response.data["gate_decision"]["steps"]
    after_compliance = steps[2:]
    assert all(s["status"] == GateStepStatus.SKIPPED.value for s in after_compliance)


def test_blocked_response_reports_the_blocking_gate() -> None:
    pipeline, _ = _pipeline(
        evidence=_evidence(
            compliance_evidence=ComplianceEvidence(restricted_symbols=(SYMBOL,))
        )
    )
    response = pipeline.evaluate(_request())
    decision = response.data["gate_decision"]
    assert decision["blocked_at_gate"] == GateName.COMPLIANCE.value


def test_blocked_before_dispatch_reports_no_side_effect() -> None:
    pipeline, _ = _pipeline(
        evidence=_evidence(
            compliance_evidence=ComplianceEvidence(restricted_symbols=(SYMBOL,))
        )
    )
    response = pipeline.evaluate(_request())
    assert response.side_effect_mode is SideEffectMode.NONE
    assert response.metadata.trades is False


def test_deadline_exceeded_blocks_before_dispatch() -> None:
    pipeline, broker = _pipeline()
    request = _request().model_copy(
        update={
            "deadline_utc": (FakeClock().now_utc() - timedelta(seconds=1)).isoformat()
        }
    )
    response = pipeline.evaluate(request)
    assert response.error.code == "DEADLINE_EXCEEDED"
    assert broker.payloads == []
