"""Live runtime service public registry.

This module exposes the approved public API of the live runtime service.
It acts as a strict middleware/gateway for live-route trading requests
and does NOT implement broker adapters, strategy logic, risk policy, or
UI rendering.

Ownership boundaries:
    OWNS:
        Live readiness validation, gate evaluation, response
        classification, error mapping, session lifecycle, monitoring,
        and reconciliation authority state.

    DOES NOT OWN:
        Broker adapter implementation, market-data ingestion, strategy
        signal generation, risk policy creation, approval-policy
        creation, UI rendering, websocket management, or frontend
        workflow policy.

Export classification legend:
    [PUBLIC API]       Stable versioned contract for external callers.
    [INTERNAL HELPER]  Used within the live package; may change.
    [CALLABLE TOOL]    Official live tool callable from approved callers.
    [PORT CONTRACT]    Persistence port Protocol for infrastructure.
    [POLICY]           Live action policy matrix types and lookups.

Public exports (with classification):
    -- Ports (PORT CONTRACT) --
    LiveStateStore, AuditSink, IdempotencyStore

    -- Policy (POLICY) --
    LiveActionPolicy, LIVE_ACTION_POLICY_MATRIX,
    LIVE_POLICY_UNDEFINED, get_action_policy

    -- Gates (CALLABLE TOOL) --
    LiveGateDecision, LiveGateResult,
    evaluate_live_gate, require_live_approval,
    enforce_kill_switch_gate,
    trigger_global_kill_switch, trigger_strategy_kill_switch,
    trigger_symbol_kill_switch,
    cancel_all_orders, close_all_positions,
    clear_kill_switch_after_approval,
    check_kill_switch_conditions, record_kill_switch_event

    -- Executor (CALLABLE TOOL) --
    LiveSideEffectMode, LiveTradeExecutor,
    execute_live_order_intent, validate_live_execution_request

    -- Monitoring (CALLABLE TOOL) --
    LiveMonitor, LiveHealthSnapshot,
    check_live_readiness, record_live_incident,
    emit_live_monitoring_event

    -- Reconciliation (CALLABLE TOOL) --
    ReconciliationMismatch, ReconciliationResult,
    ReconciliationStartupGuard, reconcile_state

    -- Session (PUBLIC API) --
    LiveSession, LiveSessionStatus,
    start_live_session, stop_live_session,
    recover_live_session, get_live_session_status

Side effects:
    None. Importing this module does NOT start broker sessions, open
    sockets, spawn threads, start async tasks, initialise broker SDK
    sessions, resolve raw secret values, or mutate any state.
"""

from __future__ import annotations

# -- Port contracts --
from app.services.live.ports import (
    AuditSink,
    IdempotencyStore,
    LiveStateStore,
)

# -- Policy --
from app.services.live.policy import (
    LIVE_ACTION_POLICY_MATRIX,
    LIVE_POLICY_UNDEFINED,
    LiveActionPolicy,
    get_action_policy,
)

# -- Gates --
from app.services.live.gates import (
    LiveGateDecision,
    LiveGateResult,
    cancel_all_orders,
    check_kill_switch_conditions,
    clear_kill_switch_after_approval,
    close_all_positions,
    enforce_kill_switch_gate,
    evaluate_live_gate,
    record_kill_switch_event,
    require_live_approval,
    trigger_global_kill_switch,
    trigger_strategy_kill_switch,
    trigger_symbol_kill_switch,
)

# -- Executor --
from app.services.live.executor import (
    LiveSideEffectMode,
    LiveTradeExecutor,
    execute_live_order_intent,
    validate_live_execution_request,
)

# -- Monitoring --
from app.services.live.monitoring import (
    LiveHealthSnapshot,
    LiveMonitor,
    check_live_readiness,
    emit_live_monitoring_event,
    record_live_incident,
)

# -- Reconciliation --
from app.services.live.reconciliation import (
    ReconciliationMismatch,
    ReconciliationResult,
    ReconciliationStartupGuard,
    reconcile_state,
)

# -- Session --
from app.services.live.session import (
    LiveSession,
    LiveSessionStatus,
    get_live_session_status,
    recover_live_session,
    start_live_session,
    stop_live_session,
)

__all__ = [
    # ── Port contracts [PORT CONTRACT] ────────────────────────────────
    "AuditSink",
    "IdempotencyStore",
    "LiveStateStore",
    # ── Policy [POLICY] ───────────────────────────────────────────────
    "LIVE_ACTION_POLICY_MATRIX",
    "LIVE_POLICY_UNDEFINED",
    "LiveActionPolicy",
    "get_action_policy",
    # ── Gates [CALLABLE TOOL] ─────────────────────────────────────────
    "LiveGateDecision",
    "LiveGateResult",
    "cancel_all_orders",
    "check_kill_switch_conditions",
    "clear_kill_switch_after_approval",
    "close_all_positions",
    "enforce_kill_switch_gate",
    "evaluate_live_gate",
    "record_kill_switch_event",
    "require_live_approval",
    "trigger_global_kill_switch",
    "trigger_strategy_kill_switch",
    "trigger_symbol_kill_switch",
    # ── Executor [CALLABLE TOOL] ──────────────────────────────────────
    "LiveSideEffectMode",
    "LiveTradeExecutor",
    "execute_live_order_intent",
    "validate_live_execution_request",
    # ── Monitoring [CALLABLE TOOL] ────────────────────────────────────
    "LiveHealthSnapshot",
    "LiveMonitor",
    "check_live_readiness",
    "emit_live_monitoring_event",
    "record_live_incident",
    # ── Reconciliation [CALLABLE TOOL] ────────────────────────────────
    "ReconciliationMismatch",
    "ReconciliationResult",
    "ReconciliationStartupGuard",
    "reconcile_state",
    # ── Session [PUBLIC API] ──────────────────────────────────────────
    "LiveSession",
    "LiveSessionStatus",
    "get_live_session_status",
    "recover_live_session",
    "start_live_session",
    "stop_live_session",
]
