"""Unit tests for kill-switch evaluation, clearing, and persistence."""
# ruff: noqa: ARG002

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.trading.contracts import JsonObject, TradingAction, TradingRoute
from app.services.trading.gates.approval import (
    ApprovalScope,
    OperatorApprovalToken,
    compute_canonical_request_hash,
)
from app.services.trading.gates.kill_switch import (
    KillSwitchScope,
    KillSwitchState,
    clear_kill_switch_after_approval,
    evaluate_kill_switches,
    persist_kill_switch_state,
    restore_kill_switch_state,
)
from app.services.trading.gates.policy_matrix import PolicyMatrixEntry
from app.services.trading.security.error_mapping import TradingMappedError

NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
REQUEST_HASH = compute_canonical_request_hash(
    symbol="EURUSD",
    account_id="acct-1",
    side="buy",
    volume="0.10",
    price=None,
    sl=None,
    tp=None,
    route="live",
    strategy_id="strat-1",
)


class FakeStateStore:
    """In-memory TradingStateStore port double."""

    def __init__(self) -> None:
        """Initialize the empty in-memory snapshot table."""
        self._snapshots: dict[str, JsonObject] = {}

    def save_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot: JsonObject,
        expected_version: int | None,
    ) -> str:
        """Persist a snapshot in memory."""
        key = f"{route.value}:{tenant_id}"
        self._snapshots[key] = snapshot
        return f"snapshot-ref-{key}"

    def load_state(
        self, *, route: TradingRoute, tenant_id: str, snapshot_id: str
    ) -> JsonObject | None:
        """Load a previously saved snapshot from memory."""
        return self._snapshots.get(f"{route.value}:{tenant_id}")


def _token(**overrides: object) -> OperatorApprovalToken:
    defaults: dict[str, object] = {
        "approval_id": "appr-1",
        "operator_id": "op-1",
        "governed_action_id": "clear_global_kill_switch",
        "scope": ApprovalScope(),
        "canonical_request_hash": REQUEST_HASH,
        "issued_at": "2026-07-09T10:00:00Z",
        "expires_at": "2026-07-09T13:00:00Z",
    }
    defaults.update(overrides)
    return OperatorApprovalToken(**defaults)  # type: ignore[arg-type]


def test_evaluate_kill_switches_passes_when_none_active() -> None:
    """No blocking occurs when no kill switch is active."""
    policy = PolicyMatrixEntry(action=TradingAction.SUBMIT_ORDER)
    evaluation = evaluate_kill_switches(
        switches=(KillSwitchState(scope=KillSwitchScope.GLOBAL, active=False),),
        action=TradingAction.SUBMIT_ORDER,
        policy_entry=policy,
    )
    assert evaluation.blocked is False


def test_evaluate_kill_switches_blocks_non_emergency_action() -> None:
    """A non-emergency action is blocked while any switch is active."""
    policy = PolicyMatrixEntry(action=TradingAction.SUBMIT_ORDER)
    evaluation = evaluate_kill_switches(
        switches=(KillSwitchState(scope=KillSwitchScope.GLOBAL, active=True),),
        action=TradingAction.SUBMIT_ORDER,
        policy_entry=policy,
    )
    assert evaluation.blocked is True
    assert evaluation.reason_code == "LIVE_KILL_SWITCH_ACTIVE"


def test_evaluate_kill_switches_blocks_emergency_action_without_policy_allowance() -> (
    None
):
    """An emergency-protective action is still blocked unless policy allows it."""
    policy = PolicyMatrixEntry(
        action=TradingAction.CANCEL_ALL_ORDERS,
        emergency_allowed_under_kill_switch=False,
    )
    evaluation = evaluate_kill_switches(
        switches=(KillSwitchState(scope=KillSwitchScope.GLOBAL, active=True),),
        action=TradingAction.CANCEL_ALL_ORDERS,
        policy_entry=policy,
    )
    assert evaluation.blocked is True


def test_evaluate_kill_switches_allows_emergency_action_with_policy_allowance() -> None:
    """An emergency-protective action passes when policy explicitly allows it."""
    policy = PolicyMatrixEntry(
        action=TradingAction.CANCEL_ALL_ORDERS, emergency_allowed_under_kill_switch=True
    )
    evaluation = evaluate_kill_switches(
        switches=(KillSwitchState(scope=KillSwitchScope.GLOBAL, active=True),),
        action=TradingAction.CANCEL_ALL_ORDERS,
        policy_entry=policy,
    )
    assert evaluation.blocked is False


def test_clear_kill_switch_global_requires_dual_approval() -> None:
    """Clearing the global kill switch requires two distinct operators."""
    current = KillSwitchState(
        scope=KillSwitchScope.GLOBAL, active=True, reason="incident"
    )
    tokens = (
        _token(approval_id="a1", operator_id="op-1"),
        _token(approval_id="a2", operator_id="op-2"),
    )
    cleared = clear_kill_switch_after_approval(
        current=current,
        tokens=tokens,
        now=NOW,
        expected_request_hash=REQUEST_HASH,
        expected_scope=ApprovalScope(),
    )
    assert cleared.active is False


def test_clear_kill_switch_global_rejects_single_operator() -> None:
    """Clearing the global kill switch with only one operator fails closed."""
    current = KillSwitchState(scope=KillSwitchScope.GLOBAL, active=True)
    with pytest.raises(TradingMappedError):
        clear_kill_switch_after_approval(
            current=current,
            tokens=(_token(),),
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(),
        )


def test_clear_kill_switch_strategy_requires_at_least_one_token() -> None:
    """Clearing a non-global kill switch requires at least one approval token."""
    current = KillSwitchState(
        scope=KillSwitchScope.STRATEGY, scope_id="strat-1", active=True
    )
    with pytest.raises(TradingMappedError) as exc_info:
        clear_kill_switch_after_approval(
            current=current,
            tokens=(),
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(),
        )
    assert exc_info.value.code == "APPROVAL_REQUIRED"


def test_clear_kill_switch_symbol_passes_with_single_valid_token() -> None:
    """Clearing a symbol-scoped kill switch passes with one valid operator."""
    current = KillSwitchState(
        scope=KillSwitchScope.SYMBOL, scope_id="EURUSD", active=True
    )
    cleared = clear_kill_switch_after_approval(
        current=current,
        tokens=(_token(governed_action_id="clear_symbol_kill_switch"),),
        now=NOW,
        expected_request_hash=REQUEST_HASH,
        expected_scope=ApprovalScope(),
    )
    assert cleared.active is False
    assert cleared.reason is None


def test_restore_kill_switch_state_returns_empty_when_no_snapshot() -> None:
    """Restoration returns no switches when no durable snapshot exists yet."""
    store = FakeStateStore()
    restored = restore_kill_switch_state(
        state_store=store,
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        snapshot_id="snap-1",
    )
    assert restored == ()


def test_restore_kill_switch_state_ignores_malformed_snapshot_shape() -> None:
    """A snapshot whose kill_switches value is not a list restores empty."""
    store = FakeStateStore()
    store.save_state(
        route=TradingRoute.LIVE,
        tenant_id="tenant-2",
        snapshot={"kill_switches": "not-a-list"},
        expected_version=None,
    )
    restored = restore_kill_switch_state(
        state_store=store,
        route=TradingRoute.LIVE,
        tenant_id="tenant-2",
        snapshot_id="snap-1",
    )
    assert restored == ()


def test_restore_kill_switch_state_skips_non_dict_entries() -> None:
    """Non-dict entries within the kill_switches list are skipped."""
    store = FakeStateStore()
    store.save_state(
        route=TradingRoute.LIVE,
        tenant_id="tenant-3",
        snapshot={"kill_switches": ["not-a-dict", {"scope": "global", "active": True}]},
        expected_version=None,
    )
    restored = restore_kill_switch_state(
        state_store=store,
        route=TradingRoute.LIVE,
        tenant_id="tenant-3",
        snapshot_id="snap-1",
    )
    assert len(restored) == 1
    assert restored[0].scope is KillSwitchScope.GLOBAL


def test_persist_and_restore_kill_switch_state_round_trips() -> None:
    """Persisted kill switch state can be restored durably."""
    store = FakeStateStore()
    switches = (
        KillSwitchState(scope=KillSwitchScope.GLOBAL, active=True, reason="incident"),
        KillSwitchState(scope=KillSwitchScope.SYMBOL, scope_id="EURUSD", active=False),
    )
    ref = persist_kill_switch_state(
        state_store=store,
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        switches=switches,
        expected_version=None,
    )
    assert ref.startswith("snapshot-ref-")

    restored = restore_kill_switch_state(
        state_store=store,
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        snapshot_id="snap-1",
    )
    assert len(restored) == 2
    assert restored[0].scope is KillSwitchScope.GLOBAL
    assert restored[0].active is True
