"""Kill-switch evaluation, dual-control clearing, and durable persistence.

Active kill switches (global, strategy, or symbol scoped) block all
non-emergency and risk-increasing live mutations; only policy-matrix
approved emergency/protective actions may proceed while a switch is active
(TRD-FR-097). Clearing a kill switch always requires validated governance
approval evidence (TRD-FR-098), and no caller-supplied flag can bypass an
active switch — only the injected policy matrix entry determines whether an
emergency action is exempt (TRD-FR-099). Kill-switch state is restored
through the injected ``TradingStateStore`` port so a process restart can
never silently clear or downgrade an active switch (TRD-FR-100).
"""
# ruff: noqa: SIM102 -- nested ifs kept flat and explicit for 100% branch coverage.

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from app.services.trading.contracts import JsonObject, TradingAction, TradingContract
from app.services.trading.gates.approval import (
    ApprovalScope,
    OperatorApprovalToken,
    validate_dual_operator_approval,
    validate_operator_approval,
)
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger

if TYPE_CHECKING:
    from datetime import datetime

    from app.services.trading.contracts import TradingRoute
    from app.services.trading.gates.policy_matrix import PolicyMatrixEntry
    from app.services.trading.state.ports import TradingStateStore

KILL_SWITCH_SNAPSHOT_KEY = "kill_switches"

_EMERGENCY_PROTECTIVE_ACTIONS = frozenset(
    {TradingAction.CANCEL_ALL_ORDERS, TradingAction.CLOSE_ALL_POSITIONS}
)


class KillSwitchScope(StrEnum):
    """Kill-switch activation scope."""

    GLOBAL = "global"
    STRATEGY = "strategy"
    SYMBOL = "symbol"


class OperationalMode(StrEnum):
    """Session-wide operational mode."""

    NORMAL = "normal"
    READ_ONLY = "read_only"
    CLOSE_ONLY = "close_only"
    REDUCE_ONLY = "reduce_only"
    EMERGENCY_FLATTEN = "emergency_flatten"
    STOPPED = "stopped"


class KillSwitchState(TradingContract):
    """Durable kill-switch activation record.

    Attributes:
        scope: Activation scope.
        scope_id: Strategy ID or symbol for scoped switches; ``None`` for
            the global switch.
        active: Whether the switch is currently active.
        reason: Operator/system reason for the activation.
        activated_at: UTC activation timestamp.
    """

    scope: KillSwitchScope
    scope_id: str | None = None
    active: bool
    reason: str | None = None
    activated_at: str | None = None


class KillSwitchEvaluation(TradingContract):
    """Kill-switch gate evaluation outcome.

    Attributes:
        blocked: Whether the requested action is blocked.
        reason_code: Stable public error code, when blocked.
        message: Human-readable, redacted outcome message.
    """

    blocked: bool
    reason_code: str | None = None
    message: str = ""


def evaluate_kill_switches(
    *,
    switches: tuple[KillSwitchState, ...],
    action: TradingAction,
    policy_entry: PolicyMatrixEntry,
) -> KillSwitchEvaluation:
    """Evaluate active kill switches against a requested action (TRD-FR-097).

    Whether an emergency/protective action may bypass an active switch is
    determined solely by ``policy_entry`` (TRD-FR-099); there is no
    caller-provided override.

    Args:
        switches: Current kill-switch states (global/strategy/symbol).
        action: Requested trading action.
        policy_entry: Resolved policy matrix entry for this action.

    Returns:
        KillSwitchEvaluation: Whether the action is blocked.
    """
    logger.info("Evaluating kill switches for action {}.", action.value)
    active_switches = [switch for switch in switches if switch.active]
    if not active_switches:
        logger.debug("No active kill switches for action {}.", action.value)
        return KillSwitchEvaluation(blocked=False)

    if action in _EMERGENCY_PROTECTIVE_ACTIONS:
        if policy_entry.emergency_allowed_under_kill_switch:
            logger.debug(
                "Emergency action {} allowed under active kill switch by policy.",
                action.value,
            )
            return KillSwitchEvaluation(
                blocked=False,
                message="emergency_protective_allowed_by_policy",
            )

    logger.info("Action {} blocked by active kill switch.", action.value)
    active_scopes = [switch.scope.value for switch in active_switches]
    return KillSwitchEvaluation(
        blocked=True,
        reason_code="LIVE_KILL_SWITCH_ACTIVE",
        message=f"Blocked by active kill switch(es): {active_scopes}",
    )


def clear_kill_switch_after_approval(
    *,
    current: KillSwitchState,
    tokens: tuple[OperatorApprovalToken, ...],
    now: datetime,
    expected_request_hash: str,
    expected_scope: ApprovalScope,
) -> KillSwitchState:
    """Clear a kill switch after validated governance approval (TRD-FR-098).

    Clearing the global kill switch requires dual-operator approval
    (TRD-FR-092); clearing a strategy or symbol switch requires a single
    valid operator approval.

    Args:
        current: Current kill-switch state to clear.
        tokens: Operator approval tokens presented for this clearance.
        now: Current UTC timestamp from an injected Clock.
        expected_request_hash: Canonical hash of the clearance request.
        expected_scope: Scope of the clearance request.

    Returns:
        KillSwitchState: The cleared (inactive) kill-switch state.

    Raises:
        TradingMappedError: If no approval token is presented for a
            non-global switch.
        TradingMappedError: If any presented approval fails validation.
    """
    logger.info("Clearing kill switch for scope {}.", current.scope.value)
    if current.scope is KillSwitchScope.GLOBAL:
        validate_dual_operator_approval(
            tokens=tokens,
            now=now,
            expected_request_hash=expected_request_hash,
            expected_scope=expected_scope,
        )
    else:
        if not tokens:
            raise TradingMappedError(
                "Kill switch clearing requires operator approval evidence.",
                code="APPROVAL_REQUIRED",
            )
        validate_operator_approval(
            token=tokens[0],
            now=now,
            expected_request_hash=expected_request_hash,
            expected_scope=expected_scope,
        )
    logger.debug("Kill switch cleared for scope {}.", current.scope.value)
    return current.model_copy(
        update={"active": False, "reason": None, "activated_at": None}
    )


def restore_kill_switch_state(
    *,
    state_store: TradingStateStore,
    route: TradingRoute,
    tenant_id: str,
    snapshot_id: str,
) -> tuple[KillSwitchState, ...]:
    """Restore durable kill-switch state before the first gate evaluation.

    Args:
        state_store: Injected trading state store.
        route: Runtime route.
        tenant_id: Tenant or session namespace.
        snapshot_id: Durable snapshot identifier.

    Returns:
        tuple[KillSwitchState, ...]: Restored kill-switch states. Empty when
        no durable snapshot exists yet (no prior activation history).
    """
    logger.info("Restoring kill switch state for tenant {}.", tenant_id)
    snapshot = state_store.load_state(
        route=route, tenant_id=tenant_id, snapshot_id=snapshot_id
    )
    if snapshot is None:
        logger.warning(
            "No durable kill switch snapshot found for tenant {}.", tenant_id
        )
        return ()
    raw_switches = snapshot.get(KILL_SWITCH_SNAPSHOT_KEY, [])
    if not isinstance(raw_switches, list):
        raw_switches = []
    restored = tuple(
        KillSwitchState.model_validate(item)
        for item in raw_switches
        if isinstance(item, dict)
    )
    logger.debug(
        "Restored {} kill switch state(s) for tenant {}.", len(restored), tenant_id
    )
    return restored


def persist_kill_switch_state(
    *,
    state_store: TradingStateStore,
    route: TradingRoute,
    tenant_id: str,
    switches: tuple[KillSwitchState, ...],
    expected_version: int | None,
) -> str:
    """Durably persist kill-switch state (TRD-FR-100).

    Args:
        state_store: Injected trading state store.
        route: Runtime route.
        tenant_id: Tenant or session namespace.
        switches: Kill-switch states to persist.
        expected_version: Optimistic concurrency version.

    Returns:
        str: Persisted snapshot reference.
    """
    logger.info(
        "Persisting {} kill switch state(s) for tenant {}.", len(switches), tenant_id
    )
    snapshot: JsonObject = {
        KILL_SWITCH_SNAPSHOT_KEY: [
            switch.model_dump(mode="json") for switch in switches
        ],
    }
    reference = state_store.save_state(
        route=route,
        tenant_id=tenant_id,
        snapshot=snapshot,
        expected_version=expected_version,
    )
    logger.debug(
        "Persisted kill switch snapshot {} for tenant {}.", reference, tenant_id
    )
    return reference
