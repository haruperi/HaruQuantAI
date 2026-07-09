"""Unit tests for the asynchronous execution coordinator primitives."""
# ruff: noqa: ARG002

from __future__ import annotations

from concurrent.futures import Future
from decimal import Decimal

import pytest
from app.services.trading.contracts import (
    AllocationVector,
    NormalizedTradeResult,
    TradingAction,
    TradingRoute,
)
from app.services.trading.execution import coordinator as c
from app.services.trading.execution.broker_capability_validation import (
    BrokerCapabilityProfile,
)
from app.services.trading.security.error_mapping import TradingMappedError


class FakeRng:
    """Deterministic RNG test double."""

    def __init__(self, value: int = 7) -> None:
        """Initialize with a fixed return value."""
        self._value = value

    def random(self) -> float:
        """Return a fixed float."""
        return 0.5

    def randint(self, lower_inclusive: int, upper_inclusive: int) -> int:
        """Return the fixed integer value."""
        return self._value


class SyncExecutor:
    """Synchronous AsyncDispatchExecutor test double."""

    def submit(self, dispatch_callable):
        """Run the dispatch callable immediately and wrap it in a Future."""
        future: Future = Future()
        try:
            result = dispatch_callable()
        except Exception as exc:  # noqa: BLE001
            future.set_exception(exc)
        else:
            future.set_result(result)
        return future


def _profile(**overrides: object) -> BrokerCapabilityProfile:
    defaults: dict[str, object] = {
        "provider": "mt5",
        "supported_order_types": ("market",),
        "supported_filling_modes": ("IOC",),
        "price_precision_digits": 5,
        "volume_precision_step": Decimal("0.01"),
        "max_requests_per_second": Decimal(10),
    }
    defaults.update(overrides)
    return BrokerCapabilityProfile(**defaults)  # type: ignore[arg-type]


def test_resolve_dispatch_target_covers_all_routes() -> None:
    """Every runtime route resolves to a distinct dispatch target."""
    assert c.resolve_dispatch_target(route=TradingRoute.SIM) == "simulator"
    assert c.resolve_dispatch_target(route=TradingRoute.PAPER) == "paper_store"
    assert c.resolve_dispatch_target(route=TradingRoute.SHADOW) == "shadow_comparison"
    assert c.resolve_dispatch_target(route=TradingRoute.LIVE) == "broker_router"


def test_generate_client_order_id_deterministic() -> None:
    """Same request_id and RNG draw produce the same client_order_id."""
    first = c.generate_client_order_id(request_id="req-1", rng=FakeRng(7))
    second = c.generate_client_order_id(request_id="req-1", rng=FakeRng(7))
    assert first == second
    assert first.startswith("clord-")


def test_generate_client_order_id_rejects_blank_request_id() -> None:
    """A blank request_id fails closed."""
    with pytest.raises(TradingMappedError):
        c.generate_client_order_id(request_id="  ", rng=FakeRng())


def test_truncate_client_order_id_returns_unchanged_when_short_enough() -> None:
    """An ID already within the limit is returned unchanged."""
    assert c.truncate_client_order_id(client_order_id="short", max_length=20) == "short"


def test_truncate_client_order_id_truncates_with_hash_suffix() -> None:
    """A long ID is truncated with a deterministic hash suffix."""
    coid = c.generate_client_order_id(request_id="req-1", rng=FakeRng())
    truncated = c.truncate_client_order_id(client_order_id=coid, max_length=15)
    assert len(truncated) <= 15
    assert "-" in truncated


def test_truncate_client_order_id_extreme_short_limit() -> None:
    """A limit shorter than the hash tail truncates the tail itself."""
    coid = c.generate_client_order_id(request_id="req-1", rng=FakeRng())
    truncated = c.truncate_client_order_id(client_order_id=coid, max_length=4)
    assert len(truncated) == 4


def test_truncate_client_order_id_rejects_non_positive_max_length() -> None:
    """A non-positive max_length fails closed."""
    with pytest.raises(TradingMappedError):
        c.truncate_client_order_id(client_order_id="clord-abc", max_length=0)


def test_build_client_order_id_mapping() -> None:
    """The mapping propagates truncated fields and a deterministic magic number."""
    coid = c.generate_client_order_id(request_id="req-1", rng=FakeRng())
    mapping = c.build_client_order_id_mapping(
        client_order_id=coid, comment_max_length=20, external_id_max_length=10
    )
    assert mapping.client_order_id == coid
    assert len(mapping.comment) <= 20
    assert len(mapping.external_id) <= 10
    assert mapping.magic_number >= 0


def test_client_order_id_mapping_rejects_blank_client_order_id() -> None:
    """A blank client_order_id fails model validation."""
    with pytest.raises(ValueError, match="client_order_id"):
        c.ClientOrderIdMapping(
            client_order_id="  ", comment="c", external_id="e", magic_number=1
        )


def test_plan_allocation_dispatch_native_block() -> None:
    """Native allocation support returns a single block plan."""
    allocation = AllocationVector(weights={"acct-1": Decimal(1)})
    plan = c.plan_allocation_dispatch(
        allocation=allocation,
        base_payload={"symbol": "EURUSD"},
        total_volume=Decimal(1),
        broker_supports_native_allocation=True,
    )
    assert plan.native_block is True
    assert plan.child_payloads == ()


def test_plan_allocation_dispatch_slices_by_weight() -> None:
    """Non-native allocation slices volume proportionally to weights."""
    allocation = AllocationVector(weights={"acct-1": Decimal(1), "acct-2": Decimal(3)})
    plan = c.plan_allocation_dispatch(
        allocation=allocation,
        base_payload={"symbol": "EURUSD"},
        total_volume=Decimal(4),
        broker_supports_native_allocation=False,
    )
    assert plan.native_block is False
    assert len(plan.child_payloads) == 2
    volumes = {p["account_id"]: p["volume"] for p in plan.child_payloads}
    assert volumes["acct-1"] == "1"
    assert volumes["acct-2"] == "3"


def test_requires_two_step_protection() -> None:
    """Two-step protection is required only when SL/TP attachment is unsupported."""
    unsupported_profile = _profile(supports_sl_tp_attachment=False)
    assert c.requires_two_step_protection(profile=unsupported_profile)
    assert not c.requires_two_step_protection(
        profile=_profile(supports_sl_tp_attachment=True)
    )


def test_evaluate_two_step_protection_outcome_success() -> None:
    """A confirmed open and confirmed protect is not a critical incident."""
    result = c.evaluate_two_step_protection_outcome(
        open_succeeded=True, protect_succeeded=True
    )
    assert result.critical_incident is False


def test_evaluate_two_step_protection_outcome_open_failed() -> None:
    """An open that never succeeded is not a critical incident."""
    result = c.evaluate_two_step_protection_outcome(
        open_succeeded=False, protect_succeeded=False
    )
    assert result.critical_incident is False


def test_evaluate_two_step_protection_outcome_critical_incident() -> None:
    """An open that succeeds without confirmed protection is a critical incident."""
    result = c.evaluate_two_step_protection_outcome(
        open_succeeded=True, protect_succeeded=False
    )
    assert result.critical_incident is True
    assert result.reason_code == "LIVE_PROTECTIVE_MODIFY_FAILED"


@pytest.mark.parametrize("policy", list(c.ResidualPolicy))
def test_apply_residual_policy_covers_every_policy(policy: c.ResidualPolicy) -> None:
    """Every residual policy resolves to a distinct stable action."""
    decision = c.apply_residual_policy(
        order_id="ord-1", policy=policy, remaining_volume=Decimal("0.5")
    )
    assert decision.policy is policy
    assert decision.action == c._RESIDUAL_ACTIONS[policy]


def test_non_atomic_modify_happy_path() -> None:
    """The full reserve/cancel/replace workflow succeeds in sequence."""
    state = c.begin_non_atomic_modify(order_id="ord-1")
    state = c.record_cancel_dispatched(state=state)
    state = c.record_cancel_confirmed(state=state)
    state = c.record_replace_dispatched(state=state)
    resolution = c.resolve_replace_outcome(
        state=state, replace_succeeded=True, reentry_allowed=True
    )
    assert resolution.critical_incident is False
    assert resolution.state.stage is c.NonAtomicModifyStage.REPLACE_CONFIRMED


def test_non_atomic_modify_replace_failure_reentry_allowed() -> None:
    """A failed replace with re-entry allowed recommends re-entry."""
    state = c.begin_non_atomic_modify(order_id="ord-1")
    state = c.record_cancel_dispatched(state=state)
    state = c.record_cancel_confirmed(state=state)
    state = c.record_replace_dispatched(state=state)
    resolution = c.resolve_replace_outcome(
        state=state, replace_succeeded=False, reentry_allowed=True
    )
    assert resolution.critical_incident is True
    assert resolution.recommended_action == "reenter_original_order"
    assert resolution.reason_code == "LIVE_NON_ATOMIC_MODIFY_ESCALATED"


def test_non_atomic_modify_replace_failure_escalates_to_dead_letter() -> None:
    """A failed replace without re-entry permission escalates to dead-letter."""
    state = c.begin_non_atomic_modify(order_id="ord-1")
    state = c.record_cancel_dispatched(state=state)
    state = c.record_cancel_confirmed(state=state)
    state = c.record_replace_dispatched(state=state)
    resolution = c.resolve_replace_outcome(
        state=state, replace_succeeded=False, reentry_allowed=False
    )
    assert resolution.recommended_action == "escalate_to_dead_letter"


def test_non_atomic_modify_out_of_sequence_transitions_fail_closed() -> None:
    """Every workflow transition rejects an out-of-sequence precondition."""
    state = c.begin_non_atomic_modify(order_id="ord-1")
    with pytest.raises(TradingMappedError):
        c.record_cancel_confirmed(state=state)
    with pytest.raises(TradingMappedError):
        c.record_replace_dispatched(state=state)
    dispatched = c.record_cancel_dispatched(state=state)
    with pytest.raises(TradingMappedError):
        c.record_cancel_dispatched(state=dispatched)
    with pytest.raises(TradingMappedError):
        c.resolve_replace_outcome(
            state=dispatched, replace_succeeded=True, reentry_allowed=True
        )


def test_resolve_oco_execution_mode_native() -> None:
    """A native-OCO-supporting adapter resolves to NATIVE regardless of emulation."""
    profile = _profile(supports_native_oco=True)
    assert (
        c.resolve_oco_execution_mode(profile=profile, synthetic_emulation_enabled=False)
        is c.OcoExecutionMode.NATIVE
    )


def test_resolve_oco_execution_mode_synthetic() -> None:
    """A non-native adapter with emulation enabled resolves to SYNTHETIC_WATCHDOG."""
    profile = _profile(supports_native_oco=False)
    assert (
        c.resolve_oco_execution_mode(profile=profile, synthetic_emulation_enabled=True)
        is c.OcoExecutionMode.SYNTHETIC_WATCHDOG
    )


def test_resolve_oco_execution_mode_unsupported_blocked() -> None:
    """A non-native adapter with emulation disabled resolves to UNSUPPORTED_BLOCKED."""
    profile = _profile(supports_native_oco=False)
    mode = c.resolve_oco_execution_mode(
        profile=profile, synthetic_emulation_enabled=False
    )
    assert mode is c.OcoExecutionMode.UNSUPPORTED_BLOCKED


def test_require_oco_submission_allowed_passes_for_native_and_synthetic() -> None:
    """Native and synthetic modes never raise."""
    c.require_oco_submission_allowed(mode=c.OcoExecutionMode.NATIVE)
    c.require_oco_submission_allowed(mode=c.OcoExecutionMode.SYNTHETIC_WATCHDOG)


def test_require_oco_submission_allowed_fails_closed_when_unsupported() -> None:
    """UNSUPPORTED_BLOCKED raises OCO_UNSUPPORTED."""
    with pytest.raises(TradingMappedError) as exc_info:
        c.require_oco_submission_allowed(mode=c.OcoExecutionMode.UNSUPPORTED_BLOCKED)
    assert exc_info.value.code == "OCO_UNSUPPORTED"


def test_evaluate_oco_sibling_cancellation_excludes_filled_order() -> None:
    """Sibling cancellation excludes the order that triggered it."""
    siblings = c.evaluate_oco_sibling_cancellation(
        filled_order_id="o1", sibling_order_ids=("o1", "o2", "o3")
    )
    assert siblings == ("o2", "o3")


def test_oco_watchdog_resolves_once_on_fill() -> None:
    """The watchdog resolves sibling cancellation exactly once per group."""
    watchdog = c.OcoWatchdog()
    watchdog.register_group(group_id="g1", order_ids=("o1", "o2"))
    siblings = watchdog.on_execution_report(
        group_id="g1", order_id="o1", execution_state="Filled"
    )
    assert siblings == ("o2",)
    again = watchdog.on_execution_report(
        group_id="g1", order_id="o2", execution_state="Filled"
    )
    assert again == ()


def test_oco_watchdog_triggers_on_partial_fill() -> None:
    """A partial fill also triggers sibling cancellation."""
    watchdog = c.OcoWatchdog()
    watchdog.register_group(group_id="g1", order_ids=("o1", "o2"))
    siblings = watchdog.on_execution_report(
        group_id="g1", order_id="o1", execution_state="Partially Filled"
    )
    assert siblings == ("o2",)


def test_oco_watchdog_ignores_unregistered_group() -> None:
    """An unregistered group produces no cancellation."""
    watchdog = c.OcoWatchdog()
    assert (
        watchdog.on_execution_report(
            group_id="ghost", order_id="o1", execution_state="Filled"
        )
        == ()
    )


def test_oco_watchdog_ignores_non_triggering_state() -> None:
    """A non-fill state does not trigger cancellation."""
    watchdog = c.OcoWatchdog()
    watchdog.register_group(group_id="g1", order_ids=("o1", "o2"))
    assert (
        watchdog.on_execution_report(
            group_id="g1", order_id="o1", execution_state="Submitted"
        )
        == ()
    )


def test_multi_leg_coordinator_rejects_invalid_tolerance() -> None:
    """Tolerance outside [0, 1] fails closed at construction."""
    with pytest.raises(TradingMappedError):
        c.MultiLegExecutionCoordinator(partial_fill_tolerance=Decimal("1.5"))
    with pytest.raises(TradingMappedError):
        c.MultiLegExecutionCoordinator(partial_fill_tolerance=Decimal("-0.1"))


def test_multi_leg_coordinator_rollback_on_rejection() -> None:
    """A rejected leg triggers rollback of every other registered leg."""
    coordinator = c.MultiLegExecutionCoordinator(partial_fill_tolerance=Decimal("0.1"))
    coordinator.register_legs(group_id="ml1", leg_order_ids=("l1", "l2", "l3"))
    decision = coordinator.on_leg_outcome(
        group_id="ml1", leg_order_id="l2", rejected=True, unfilled_fraction=Decimal(0)
    )
    assert decision.rollback_required is True
    assert set(decision.legs_to_rollback) == {"l1", "l3"}
    assert decision.reason_code == "LIVE_MULTI_LEG_ROLLBACK_TRIGGERED"


def test_multi_leg_coordinator_rollback_on_tolerance_breach() -> None:
    """A partial fill beyond tolerance also triggers rollback."""
    coordinator = c.MultiLegExecutionCoordinator(partial_fill_tolerance=Decimal("0.1"))
    coordinator.register_legs(group_id="ml1", leg_order_ids=("l1", "l2"))
    decision = coordinator.on_leg_outcome(
        group_id="ml1",
        leg_order_id="l1",
        rejected=False,
        unfilled_fraction=Decimal("0.5"),
    )
    assert decision.rollback_required is True


def test_multi_leg_coordinator_within_tolerance_no_rollback() -> None:
    """A fill within tolerance does not trigger rollback."""
    coordinator = c.MultiLegExecutionCoordinator(partial_fill_tolerance=Decimal("0.1"))
    coordinator.register_legs(group_id="ml1", leg_order_ids=("l1", "l2"))
    decision = coordinator.on_leg_outcome(
        group_id="ml1",
        leg_order_id="l1",
        rejected=False,
        unfilled_fraction=Decimal("0.05"),
    )
    assert decision.rollback_required is False


def test_multi_leg_coordinator_ignores_unregistered_group() -> None:
    """An unregistered group never triggers rollback."""
    coordinator = c.MultiLegExecutionCoordinator(partial_fill_tolerance=Decimal("0.1"))
    decision = coordinator.on_leg_outcome(
        group_id="ghost", leg_order_id="l1", rejected=True, unfilled_fraction=Decimal(0)
    )
    assert decision.rollback_required is False


def test_multi_leg_coordinator_resolves_once() -> None:
    """A group resolves rollback at most once."""
    coordinator = c.MultiLegExecutionCoordinator(partial_fill_tolerance=Decimal("0.1"))
    coordinator.register_legs(group_id="ml1", leg_order_ids=("l1", "l2"))
    first = coordinator.on_leg_outcome(
        group_id="ml1", leg_order_id="l1", rejected=True, unfilled_fraction=Decimal(0)
    )
    assert first.rollback_required is True
    second = coordinator.on_leg_outcome(
        group_id="ml1", leg_order_id="l2", rejected=True, unfilled_fraction=Decimal(0)
    )
    assert second.rollback_required is False


def test_in_flight_request_counter_increment_decrement() -> None:
    """The counter increments, decrements, and never goes negative."""
    counter = c.InFlightRequestCounter()
    assert counter.is_drained() is True
    counter.increment()
    counter.increment()
    assert counter.current() == 2
    assert counter.is_drained() is False
    counter.decrement()
    counter.decrement()
    counter.decrement()
    assert counter.current() == 0
    assert counter.is_drained() is True


def test_capture_transaction_cost() -> None:
    """Transaction cost facts are captured with the adjustment flag propagated."""
    facts = c.TransactionCostFacts(commission=Decimal("1.25"))
    event = c.capture_transaction_cost(
        order_id="ord-1",
        cost_facts=facts,
        recorded_at="2026-07-09T00:00:00Z",
        is_adjustment=True,
    )
    assert event.is_adjustment is True
    assert event.cost_facts.commission == Decimal("1.25")


def test_capture_transaction_cost_rejects_blank_order_id() -> None:
    """A blank order_id fails closed."""
    with pytest.raises(TradingMappedError):
        c.capture_transaction_cost(
            order_id="  ",
            cost_facts=c.TransactionCostFacts(),
            recorded_at="2026-07-09T00:00:00Z",
        )


class _RecordingTradeStore:
    """Minimal TradeStore test double recording save_order_state calls."""

    def __init__(self) -> None:
        """Initialize the recorder."""
        self.saved: list[dict[str, object]] = []

    def save_order_state(self, *, route, tenant_id, order_state, expected_version):
        """Record the call and return a synthetic reference."""
        self.saved.append(
            {
                "route": route,
                "tenant_id": tenant_id,
                "order_state": order_state,
                "expected_version": expected_version,
            }
        )
        return "order-ref-1"

    def save_position_state(self, **kwargs):
        """Unused in this test double."""
        raise NotImplementedError

    def record_execution_fill(self, **kwargs):
        """Unused in this test double."""
        raise NotImplementedError

    def apply_corporate_action(self, **kwargs):
        """Unused in this test double."""
        raise NotImplementedError


class _RecordingIdempotencyStore:
    """Minimal IdempotencyStore test double recording complete() calls."""

    def __init__(self) -> None:
        """Initialize the recorder."""
        self.completed: list[dict[str, object]] = []

    def reserve(self, **kwargs):
        """Unused in this test double."""
        raise NotImplementedError

    def resolve(self, **kwargs):
        """Unused in this test double."""
        raise NotImplementedError

    def complete(self, *, route, tenant_id, key, outcome, completed_at):
        """Record the completion call."""
        self.completed.append(
            {
                "route": route,
                "tenant_id": tenant_id,
                "key": key,
                "outcome": outcome,
                "completed_at": completed_at,
            }
        )


def test_finalize_dispatch_outcome_releases_lease_and_completes_idempotency() -> None:
    """Finalization saves state, releases the lease, and completes idempotency."""
    trade_store = _RecordingTradeStore()
    idempotency_store = _RecordingIdempotencyStore()
    released = []
    reference = c.finalize_dispatch_outcome(
        trade_store=trade_store,
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        order_state={"order_id": "ord-1"},
        expected_version=1,
        idempotency_store=idempotency_store,
        idempotency_key="idem-1",
        idempotency_outcome={"status": "success"},
        completed_at="2026-07-09T00:00:00Z",
        release_concurrency_lease=lambda: released.append(True),
    )
    assert reference == "order-ref-1"
    assert len(trade_store.saved) == 1
    assert len(idempotency_store.completed) == 1
    assert released == [True]


def test_finalize_dispatch_outcome_without_lease_callback() -> None:
    """Finalization skips lease release entirely when no callback is injected."""
    trade_store = _RecordingTradeStore()
    idempotency_store = _RecordingIdempotencyStore()
    c.finalize_dispatch_outcome(
        trade_store=trade_store,
        route=TradingRoute.PAPER,
        tenant_id="tenant-1",
        order_state={"order_id": "ord-1"},
        expected_version=None,
        idempotency_store=idempotency_store,
        idempotency_key="idem-1",
        idempotency_outcome={"status": "success"},
        completed_at="2026-07-09T00:00:00Z",
    )
    assert len(idempotency_store.completed) == 1


def test_execution_coordinator_build_broker_dispatch_payload() -> None:
    """The coordinator still exposes broker-independent payload packaging."""
    from app.services.trading.contracts import (
        MutationCapability,
        PromotionStage,
        TradingRequestEnvelope,
    )

    coordinator = c.ExecutionCoordinator()
    request = TradingRequestEnvelope(
        route=TradingRoute.PAPER,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.PAPER_TRADING,
        mutation_capability=MutationCapability.PAPER_ONLY,
        request_id="req-1",
        correlation_id="corr-1",
        payload={"symbol": "EURUSD"},
    )
    payload = coordinator.build_broker_dispatch_payload(request)
    assert payload["symbol"] == "EURUSD"


def test_execution_coordinator_dispatch_async_success() -> None:
    """A successful dispatch decrements in-flight and invokes on_complete."""
    coordinator = c.ExecutionCoordinator()
    completions: list[object] = []
    accepted = coordinator.dispatch_async(
        request_id="req-1",
        action=TradingAction.SUBMIT_ORDER,
        accepted_at="2026-07-09T00:00:00Z",
        executor=SyncExecutor(),
        dispatch_callable=lambda: NormalizedTradeResult(
            retcode="10009", request_id="req-1", provider="mt5"
        ),
        on_complete=completions.append,
    )
    assert accepted.request_id == "req-1"
    assert coordinator.in_flight.current() == 0
    assert len(completions) == 1
    assert isinstance(completions[0], NormalizedTradeResult)


def test_execution_coordinator_dispatch_async_failure() -> None:
    """A raised dispatch exception still decrements in-flight and is forwarded."""
    coordinator = c.ExecutionCoordinator()
    completions: list[object] = []

    def _failing_dispatch() -> NormalizedTradeResult:
        raise ValueError("boom")

    coordinator.dispatch_async(
        request_id="req-1",
        action=TradingAction.SUBMIT_ORDER,
        accepted_at="2026-07-09T00:00:00Z",
        executor=SyncExecutor(),
        dispatch_callable=_failing_dispatch,
        on_complete=completions.append,
    )
    assert coordinator.in_flight.current() == 0
    assert len(completions) == 1
    assert isinstance(completions[0], ValueError)
