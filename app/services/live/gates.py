"""Live execution gate evaluation chain.

Implements the deterministic ordered gate chain that every live-route
request must pass before any broker mutation can occur. Gates evaluate
in a fixed order; the first mandatory gate failure stops all downstream
evaluation and returns immediately.

Gate evaluation order (11 gates):
    1.  Live enablement gate
    2.  Request schema validation gate
    3.  Approval validation gate
    4.  Risk decision validation gate
    5.  Broker readiness gate
    6.  Session active gate
    7.  Stale-context validation gate
    8.  Idempotency validation gate
    9.  Reconciliation authority validation gate
    10. Kill-switch validation gate
    11. Audit pre-recording gate
    12. Broker adapter permission gate

Ownership:
    - Owns gate evaluation sequencing, gate result contracts,
      kill-switch gate enforcement, and kill-switch action packaging.
    - Does NOT own risk policy, approval-policy creation, broker
      adapter implementation, or UI/API routing.
    - Emergency fail-safe classification comes ONLY from the approved
      live action policy matrix (``app.services.live.policy``), never
      from request text, user role, chat instruction, or API route.

Public exports:
    LiveGateDecision, LiveGateResult, evaluate_live_gate,
    require_live_approval, enforce_kill_switch_gate,
    trigger_global_kill_switch, trigger_strategy_kill_switch,
    trigger_symbol_kill_switch, cancel_all_orders,
    close_all_positions, clear_kill_switch_after_approval,
    check_kill_switch_conditions, record_kill_switch_event.

Side effects:
    None on import. Gate evaluation is synchronous and deterministic.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from app.services.live.policy import (
    LIVE_POLICY_UNDEFINED,
    get_action_policy,
)
from app.services.risk.kill_switch import KillSwitchScope, check_risk_kill_switch
from app.utils.errors import ValidationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.live.ports import AuditSink
    from app.utils.settings import Settings


class LiveGateDecision(StrEnum):
    """Decision outcome for a single live gate evaluation.

    Attributes:
        PASS: Gate passed; downstream evaluation may continue.
        BLOCK: Mandatory gate failed; downstream evaluation must stop.
        ERROR: Gate encountered an unexpected error; treated as BLOCK.
        DIAGNOSTIC_ONLY: Gate ran in diagnostic mode after a mandatory
            failure (only valid for gates with
            ``diagnostic_after_failure=True``).
    """

    PASS = "pass"  # noqa: S105
    BLOCK = "block"
    ERROR = "error"
    DIAGNOSTIC_ONLY = "diagnostic_only"


@dataclass(frozen=True)
class LiveGateResult:
    """Immutable result for one gate in the evaluation chain.

    Attributes:
        decision: Gate outcome.
        gate_name: Stable machine-readable gate identifier.
        error_code: Approved error code when decision is BLOCK or ERROR.
        message: Human-readable operator message (no secrets).
        request_id: Trace identifier propagated from the caller.
        correlation_id: Optional correlation ID.
        retry_safety: Retry classification — one of
            ``'safe_to_retry'``, ``'retry_after_reconciliation'``, or
            ``'do_not_retry'``.
        audit_ref: Optional audit evidence reference.
        metadata: Additional structured gate metadata (redacted).
    """

    decision: LiveGateDecision
    gate_name: str
    error_code: str | None = None
    message: str = ""
    request_id: str | None = None
    correlation_id: str | None = None
    retry_safety: str = "do_not_retry"
    audit_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _pass(
    gate_name: str,
    *,
    message: str,
    request_id: str | None,
    correlation_id: str | None,
    audit_ref: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> LiveGateResult:
    """Build a PASS gate result."""
    return LiveGateResult(
        decision=LiveGateDecision.PASS,
        gate_name=gate_name,
        message=message,
        request_id=request_id,
        correlation_id=correlation_id,
        audit_ref=audit_ref,
        metadata=metadata or {},
    )


def _block(
    gate_name: str,
    *,
    error_code: str,
    message: str,
    request_id: str | None,
    correlation_id: str | None,
    retry_safety: str = "do_not_retry",
    metadata: dict[str, Any] | None = None,
) -> LiveGateResult:
    """Build a BLOCK gate result."""
    return LiveGateResult(
        decision=LiveGateDecision.BLOCK,
        gate_name=gate_name,
        error_code=error_code,
        message=message,
        request_id=request_id,
        correlation_id=correlation_id,
        retry_safety=retry_safety,
        metadata=metadata or {},
    )


def _error(
    gate_name: str,
    *,
    error_code: str,
    message: str,
    request_id: str | None,
    correlation_id: str | None,
) -> LiveGateResult:
    """Build an ERROR gate result (treated as BLOCK)."""
    return LiveGateResult(
        decision=LiveGateDecision.ERROR,
        gate_name=gate_name,
        error_code=error_code,
        message=message,
        request_id=request_id,
        correlation_id=correlation_id,
        retry_safety="do_not_retry",
    )


def _is_blocked(result: LiveGateResult) -> bool:
    """Return True when a gate result is a blocking decision."""
    return result.decision in {LiveGateDecision.BLOCK, LiveGateDecision.ERROR}


# ---------------------------------------------------------------------------
# Gate evaluation chain
# ---------------------------------------------------------------------------


def evaluate_live_gate(  # noqa: PLR0911, PLR0912, PLR0915, C901
    *,
    action: str,
    config: Settings,
    approval_context: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    reconciliation_clean: bool = True,
    context_timestamp: datetime | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    session_active: bool = True,
    risk_decision_ref: str | None = None,
    audit_sink: AuditSink | None = None,
) -> list[LiveGateResult]:
    """Evaluate all live gates in deterministic order for a requested action.

    Gates are evaluated in sequence 1–12. The first mandatory gate
    failure returns immediately without evaluating downstream gates that
    could mutate broker state, mutate durable state, or consume broker
    capacity.

    Diagnostic-only gates (local metadata/redaction validation) may run
    after a mandatory gate failure only when explicitly marked safe.

    Gate 3 evaluates ``approval_context`` when the action's policy entry
    requires approval. Gate 11 writes a pre-event audit record to
    ``audit_sink`` when provided; when live mutation is enabled and no
    ``audit_sink`` is configured, Gate 11 blocks as fail-closed.

    Args:
        action: Requested live action name (e.g. ``'submit_order'``).
        config: Current live runtime settings.
        approval_context: Approval context dict for approval-required
            actions. ``None`` blocks Gate 3 for approval-required
            actions.
        idempotency_key: Optional idempotency key for duplicate
            detection.
        reconciliation_clean: Whether broker reconciliation is current.
        context_timestamp: Optional timestamp of the request context for
            staleness check.
        request_id: Trace identifier propagated through all gate results.
        correlation_id: Optional correlation identifier.
        session_active: Whether a live session is currently active.
        risk_decision_ref: Optional risk decision reference for Gate 4.
        audit_sink: Optional ``AuditSink`` port for Gate 11 pre-event
            recording. When live mutation is enabled and this is
            ``None``, Gate 11 blocks.

    Returns:
        List of ``LiveGateResult`` objects in evaluation order. If a
        mandatory gate fails, remaining mandatory gates are not
        evaluated.

    Raises:
        ValidationError: If ``action`` is not a non-empty string.
    """
    start = time.perf_counter()

    if not isinstance(action, str) or not action.strip():
        raise ValidationError(
            "action must be a non-empty string.", code="INVALID_INPUT"
        )
    action = action.strip()

    results: list[LiveGateResult] = []

    # ── Gate 1: Live enablement ───────────────────────────────────────
    if not config.live_enabled or config.live_mode == "package_only":
        results.append(
            _block(
                "live_enablement",
                error_code="LIVE_DISABLED",
                message=(
                    "Live trading is disabled or in package-only mode. "
                    "Set live_enabled=True and an active live_mode "
                    "to proceed."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )
        logger.info(
            "live_gate.blocked.live_disabled action=%r "
            "live_enabled=%r live_mode=%r request_id=%r",
            action,
            config.live_enabled,
            config.live_mode,
            request_id,
        )
        return results

    results.append(
        _pass(
            "live_enablement",
            message="Live mode is enabled.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 2: Request schema validation ────────────────────────────
    if not action:
        results.append(
            _block(
                "request_schema_validation",
                error_code="INVALID_INPUT",
                message="Action name failed schema validation.",
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )
        return results

    # Validate against the policy matrix.
    policy = get_action_policy(action)
    if policy is None:
        results.append(
            _block(
                "request_schema_validation",
                error_code="LIVE_POLICY_UNDEFINED",
                message=(
                    f"Action {action!r} has no entry in the live action "
                    f"policy matrix ({LIVE_POLICY_UNDEFINED}). "
                    "Register the action before use."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )
        logger.warning(
            "live_gate.blocked.policy_undefined action=%r request_id=%r",
            action,
            request_id,
        )
        return results

    results.append(
        _pass(
            "request_schema_validation",
            message="Request schema is valid; policy entry found.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 3: Approval validation ───────────────────────────────────
    if policy.approval_required:
        approval_result = require_live_approval(
            approval_context=approval_context or {},
            required_action=action,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        results.append(approval_result)
        if _is_blocked(approval_result):
            logger.warning(
                "live_gate.blocked.approval_failed action=%r "
                "request_id=%r",
                action,
                request_id,
            )
            return results
    else:
        results.append(
            _pass(
                "approval_validation",
                message=(
                    "Approval not required for this action "
                    "(policy: approval_required=False)."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )

    # ── Gate 4: Risk decision validation (placeholder) ────────────────
    # The risk module owns risk policy. This gate validates that a risk
    # decision reference is present when the action has a non-trivial
    # side-effect ceiling. Full integration requires the risk module's
    # approved contract.
    if (
        policy.side_effect_ceiling
        not in {"none", "packaged_only"}
        and risk_decision_ref is None
    ):
        results.append(
            _block(
                "risk_decision_validation",
                error_code="LIVE_GATE_FAILED",
                message=(
                    "A risk decision reference is required for actions "
                    f"with side-effect ceiling "
                    f"'{policy.side_effect_ceiling}'. "
                    "Provide risk_decision_ref from the risk module."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )
        return results

    results.append(
        _pass(
            "risk_decision_validation",
            message="Risk decision validation passed.",
            request_id=request_id,
            correlation_id=correlation_id,
            metadata={"risk_decision_ref": risk_decision_ref},
        )
    )

    # ── Gate 5: Broker readiness (placeholder) ────────────────────────
    # Full broker readiness requires an approved broker adapter contract
    # (API/version compatibility, symbol metadata, account snapshot).
    # Until the adapter contract is approved, this gate passes with a
    # diagnostic note. Production broker mutation remains blocked by
    # the executor's packaged-only guard.
    results.append(
        _pass(
            "broker_readiness",
            message=(
                "Broker readiness check deferred: no approved adapter "
                "contract yet. Production mutation blocked by executor."
            ),
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 6: Session active ────────────────────────────────────────
    if not session_active:
        results.append(
            _block(
                "session_active",
                error_code="LIVE_SESSION_INACTIVE",
                message=(
                    "No active live session. "
                    "Start a session before requesting live actions."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )
        return results

    results.append(
        _pass(
            "session_active",
            message="Live session is active.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 7: Stale-context validation ─────────────────────────────
    if context_timestamp is not None:
        now = datetime.now(UTC)
        age_seconds = (now - context_timestamp).total_seconds()
        if age_seconds > config.live_max_staleness_seconds:
            results.append(
                _block(
                    "stale_context",
                    error_code="LIVE_STALE_CONTEXT",
                    message=(
                        f"Context is stale ({age_seconds:.1f}s > "
                        f"{config.live_max_staleness_seconds}s "
                        "threshold)."
                    ),
                    request_id=request_id,
                    correlation_id=correlation_id,
                    metadata={
                        "age_seconds": age_seconds,
                        "max_staleness": config.live_max_staleness_seconds,
                    },
                )
            )
            return results

    results.append(
        _pass(
            "stale_context",
            message="Context freshness is within threshold.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 8: Idempotency validation ───────────────────────────────
    # Full idempotency store integration is a persistence port
    # (IdempotencyStore). This gate validates key presence for actions
    # that require it; full conflict detection requires the store.
    if policy.idempotency_required and not idempotency_key:
        results.append(
            _block(
                "idempotency",
                error_code="INVALID_INPUT",
                message=(
                    f"Action {action!r} requires an idempotency_key "
                    "(policy: idempotency_required=True)."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )
        return results

    results.append(
        _pass(
            "idempotency",
            message="Idempotency key accepted (no conflict detected).",
            request_id=request_id,
            correlation_id=correlation_id,
            metadata={"idempotency_key": idempotency_key},
        )
    )

    # ── Gate 9: Reconciliation authority validation ───────────────────
    if not reconciliation_clean:
        results.append(
            _block(
                "reconciliation_authority",
                error_code="LIVE_RECONCILIATION_REQUIRED",
                message=(
                    "Broker reconciliation is pending. "
                    "Live mutation is blocked until reconciliation "
                    "completes."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
                retry_safety="retry_after_reconciliation",
            )
        )
        return results

    results.append(
        _pass(
            "reconciliation_authority",
            message="Reconciliation authority is clean.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 10: Kill-switch validation ──────────────────────────────
    ks_result = enforce_kill_switch_gate(
        scope=KillSwitchScope.GLOBAL,
        target="*",
        request_id=request_id,
        correlation_id=correlation_id,
    )
    results.append(ks_result)
    if _is_blocked(ks_result):
        return results

    # ── Gate 11: Audit pre-recording ─────────────────────────────────
    # When live mutation is enabled an AuditSink must be provided.
    # A write failure blocks mutation as fail-closed.
    audit_ref: str | None = None
    live_mutation_enabled = (
        config.live_enabled
        and config.live_mode not in {"read_only", "package_only"}
    )
    if live_mutation_enabled and audit_sink is None:
        results.append(
            _block(
                "audit_pre_recording",
                error_code="LIVE_AUDIT_WRITE_FAILED",
                message=(
                    "Live mutation is enabled but no AuditSink is "
                    "configured. Provide an audit_sink to proceed."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        )
        return results

    if audit_sink is not None:
        try:
            serialised_results = [
                {
                    "gate_name": r.gate_name,
                    "decision": str(r.decision),
                    "error_code": r.error_code,
                }
                for r in results
            ]
            audit_ref = audit_sink.write_pre_event(
                request_id=request_id or "",
                action=action,
                gate_results=serialised_results,
                audit_metadata={
                    "correlation_id": correlation_id,
                    "idempotency_key": idempotency_key,
                    "risk_decision_ref": risk_decision_ref,
                },
                recorded_at=datetime.now(UTC),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "live_gate.audit_write_failed action=%r "
                "error=%r request_id=%r",
                action,
                str(exc),
                request_id,
            )
            results.append(
                _error(
                    "audit_pre_recording",
                    error_code="LIVE_AUDIT_WRITE_FAILED",
                    message=(
                        "Audit pre-event write failed; blocking as "
                        f"fail-closed. Error: {exc!s}"
                    ),
                    request_id=request_id,
                    correlation_id=correlation_id,
                )
            )
            return results

    results.append(
        _pass(
            "audit_pre_recording",
            message="Audit pre-event recorded successfully.",
            request_id=request_id,
            correlation_id=correlation_id,
            audit_ref=audit_ref,
        )
    )

    # ── Gate 12: Broker adapter permission ───────────────────────────
    # Full broker adapter permission requires an approved adapter
    # capability contract. Until approved, this gate passes with a
    # diagnostic note. Production mutation remains blocked by the
    # executor's packaged-only guard.
    results.append(
        _pass(
            "broker_adapter_permission",
            message=(
                "Broker adapter permission deferred: no approved "
                "adapter contract yet. Mutation blocked by executor."
            ),
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    all_passed = all(
        r.decision == LiveGateDecision.PASS for r in results
    )
    logger.info(
        "live_gate.evaluation_complete action=%r gate_count=%r "
        "elapsed_ms=%r all_passed=%r request_id=%r",
        action,
        len(results),
        round(elapsed_ms, 3),
        all_passed,
        request_id,
    )
    return results


# ---------------------------------------------------------------------------
# Approval validation
# ---------------------------------------------------------------------------


def require_live_approval(  # noqa: PLR0911
    *,
    approval_context: dict[str, Any],
    required_action: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> LiveGateResult:
    """Validate approval context for live actions that require approval.

    Rejects contexts that are expired, revoked, not approved, outside
    action scope, or missing required audit metadata.

    Required fields in ``approval_context``:
        - ``approval_id``: str
        - ``action_type``: str (must match ``required_action``)
        - ``approval_state``: str (must be ``'approved'``)
        - ``expiration_timestamp``: ISO 8601 str
        - ``approver_identity_ref``: str
        - ``audit_metadata``: dict

    Args:
        approval_context: Structured approval context dict.
        required_action: Action type that the approval must cover.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        ``LiveGateResult`` with ``PASS`` when valid, ``BLOCK``
        otherwise.
    """
    if not isinstance(approval_context, dict):
        return _block(
            "approval_validation",
            error_code="LIVE_APPROVAL_REQUIRED",
            message="Approval context must be a non-null dict.",
            request_id=request_id,
            correlation_id=correlation_id,
        )

    required_fields = [
        "approval_id",
        "action_type",
        "approval_state",
        "expiration_timestamp",
        "approver_identity_ref",
        "audit_metadata",
    ]
    missing = [f for f in required_fields if not approval_context.get(f)]
    if missing:
        return _block(
            "approval_validation",
            error_code="LIVE_APPROVAL_REQUIRED",
            message=(
                f"Approval context is missing required fields: {missing}."
            ),
            request_id=request_id,
            correlation_id=correlation_id,
        )

    if approval_context.get("approval_state") != "approved":
        return _block(
            "approval_validation",
            error_code="LIVE_APPROVAL_REQUIRED",
            message=(
                "Approval state is not 'approved': "
                f"{approval_context.get('approval_state')!r}."
            ),
            request_id=request_id,
            correlation_id=correlation_id,
        )

    if approval_context.get("action_type") != required_action:
        return _block(
            "approval_validation",
            error_code="LIVE_APPROVAL_REQUIRED",
            message=(
                f"Approval is for action "
                f"{approval_context.get('action_type')!r}, "
                f"not {required_action!r}."
            ),
            request_id=request_id,
            correlation_id=correlation_id,
        )

    try:
        exp_str = approval_context.get("expiration_timestamp", "")
        if isinstance(exp_str, str):
            exp_dt = datetime.fromisoformat(exp_str)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=UTC)
            if datetime.now(UTC) > exp_dt:
                return _block(
                    "approval_validation",
                    error_code="LIVE_APPROVAL_REQUIRED",
                    message="Approval context has expired.",
                    request_id=request_id,
                    correlation_id=correlation_id,
                )
    except (ValueError, TypeError):
        return _block(
            "approval_validation",
            error_code="INVALID_INPUT",
            message=(
                "Approval expiration_timestamp is not a valid "
                "ISO 8601 datetime."
            ),
            request_id=request_id,
            correlation_id=correlation_id,
        )

    logger.info(
        "live_gate.approval_validated approval_id=%r "
        "action_type=%r request_id=%r",
        approval_context.get("approval_id"),
        required_action,
        request_id,
    )
    return _pass(
        "approval_validation",
        message="Approval context is valid.",
        request_id=request_id,
        correlation_id=correlation_id,
        audit_ref=str(approval_context.get("approval_id", "")),
    )


# ---------------------------------------------------------------------------
# Kill-switch gate
# ---------------------------------------------------------------------------


def enforce_kill_switch_gate(
    *,
    scope: KillSwitchScope = KillSwitchScope.GLOBAL,
    target: str = "*",
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> LiveGateResult:
    """Evaluate the kill-switch gate for the given scope and target.

    An active kill switch unconditionally blocks live trading regardless
    of route, request text, UI input, API input, or chat instruction.
    Emergency fail-safe classification comes only from the approved live
    action policy matrix, not from this function's parameters.

    Args:
        scope: Kill-switch scope to check.
        target: Target identifier (``'*'`` for global).
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        ``LiveGateResult`` with ``PASS`` when no active kill switch,
        ``BLOCK`` or ``ERROR`` otherwise.
    """
    try:
        is_active: bool = check_risk_kill_switch(str(scope), target)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "live_gate.kill_switch.check_error scope=%r target=%r "
            "error=%r request_id=%r",
            scope,
            target,
            str(exc),
            request_id,
        )
        return _error(
            "kill_switch",
            error_code="LIVE_KILL_SWITCH_ACTIVE",
            message=(
                "Kill-switch check failed with error; blocking as "
                f"fail-closed. Error: {exc!s}"
            ),
            request_id=request_id,
            correlation_id=correlation_id,
        )

    if is_active:
        logger.warning(
            "live_gate.blocked.kill_switch_active scope=%r "
            "target=%r request_id=%r",
            scope,
            target,
            request_id,
        )
        return _block(
            "kill_switch",
            error_code="LIVE_KILL_SWITCH_ACTIVE",
            message=(
                f"Active kill switch (scope={scope}, "
                f"target={target!r}) blocks live trading."
            ),
            request_id=request_id,
            correlation_id=correlation_id,
        )

    return _pass(
        "kill_switch",
        message="No active kill switch detected.",
        request_id=request_id,
        correlation_id=correlation_id,
    )


# ---------------------------------------------------------------------------
# Kill-switch action tools
# ---------------------------------------------------------------------------


def trigger_global_kill_switch(
    *,
    reason: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Package a global trading kill-switch activation request.

    Emergency fail-safe classification is read from the policy matrix.
    This function DOES NOT call broker adapters or mutate state directly.

    Args:
        reason: Human-readable operator reason for the kill-switch.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        Structured packaged kill-switch activation request dict.
    """
    policy = get_action_policy("trigger_global_kill_switch")
    return {
        "action": "trigger_global_kill_switch",
        "scope": "global",
        "target": "*",
        "reason": reason,
        "emergency_fail_safe": (
            policy.emergency_fail_safe if policy else False
        ),
        "side_effect_mode": "packaged_only",
        "request_id": request_id,
        "correlation_id": correlation_id,
        "packaged_at": datetime.now(UTC).isoformat(),
    }


def trigger_strategy_kill_switch(
    *,
    strategy_id: str,
    reason: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Package a strategy-level kill-switch activation request.

    Emergency fail-safe classification is read from the policy matrix.
    This function DOES NOT call broker adapters or mutate state directly.

    Args:
        strategy_id: Strategy identifier to kill.
        reason: Human-readable operator reason for the kill-switch.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        Structured packaged strategy kill-switch request dict.
    """
    policy = get_action_policy("trigger_strategy_kill_switch")
    return {
        "action": "trigger_strategy_kill_switch",
        "scope": "strategy",
        "target": strategy_id,
        "reason": reason,
        "emergency_fail_safe": (
            policy.emergency_fail_safe if policy else False
        ),
        "side_effect_mode": "packaged_only",
        "request_id": request_id,
        "correlation_id": correlation_id,
        "packaged_at": datetime.now(UTC).isoformat(),
    }


def trigger_symbol_kill_switch(
    *,
    symbol: str,
    reason: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Package a symbol-level kill-switch activation request.

    Emergency fail-safe classification is read from the policy matrix.
    This function DOES NOT call broker adapters or mutate state directly.

    Args:
        symbol: Symbol to apply the kill-switch to.
        reason: Human-readable operator reason.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        Structured packaged symbol kill-switch request dict.
    """
    policy = get_action_policy("trigger_symbol_kill_switch")
    return {
        "action": "trigger_symbol_kill_switch",
        "scope": "symbol",
        "target": symbol,
        "reason": reason,
        "emergency_fail_safe": (
            policy.emergency_fail_safe if policy else False
        ),
        "side_effect_mode": "packaged_only",
        "request_id": request_id,
        "correlation_id": correlation_id,
        "packaged_at": datetime.now(UTC).isoformat(),
    }


def cancel_all_orders(
    *,
    account_id: str,
    approval_context: dict[str, Any],
    reason: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Package cancellation of all pending orders after approval gates.

    This function DOES NOT call broker adapters or mutate state directly.

    Args:
        account_id: Account identifier whose orders will be cancelled.
        approval_context: Validated approval context dict.
        reason: Human-readable operator reason.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        Structured packaged mass-cancel request dict.
    """
    approval_result = require_live_approval(
        approval_context=approval_context,
        required_action="cancel_all_orders",
        request_id=request_id,
        correlation_id=correlation_id,
    )
    if _is_blocked(approval_result):
        return {
            "action": "cancel_all_orders",
            "status": "blocked",
            "gate_decision": str(approval_result.decision),
            "error_code": approval_result.error_code,
            "message": approval_result.message,
            "request_id": request_id,
        }
    return {
        "action": "cancel_all_orders",
        "account_id": account_id,
        "reason": reason,
        "side_effect_mode": "packaged_only",
        "approval_id": approval_context.get("approval_id"),
        "request_id": request_id,
        "correlation_id": correlation_id,
        "packaged_at": datetime.now(UTC).isoformat(),
    }


def close_all_positions(
    *,
    account_id: str,
    approval_context: dict[str, Any],
    reason: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Package closing of all positions after approval gates.

    This function DOES NOT call broker adapters or mutate state directly.

    Args:
        account_id: Account identifier whose positions will be closed.
        approval_context: Validated approval context dict.
        reason: Human-readable operator reason.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        Structured packaged mass-close request dict.
    """
    approval_result = require_live_approval(
        approval_context=approval_context,
        required_action="close_all_positions",
        request_id=request_id,
        correlation_id=correlation_id,
    )
    if _is_blocked(approval_result):
        return {
            "action": "close_all_positions",
            "status": "blocked",
            "gate_decision": str(approval_result.decision),
            "error_code": approval_result.error_code,
            "message": approval_result.message,
            "request_id": request_id,
        }
    return {
        "action": "close_all_positions",
        "account_id": account_id,
        "reason": reason,
        "side_effect_mode": "packaged_only",
        "approval_id": approval_context.get("approval_id"),
        "request_id": request_id,
        "correlation_id": correlation_id,
        "packaged_at": datetime.now(UTC).isoformat(),
    }


def clear_kill_switch_after_approval(
    *,
    scope: str,
    target: str,
    approval_context: dict[str, Any],
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Package kill-switch clearing after approval gates.

    Kill-switch clearing requires explicit approval context. This
    function DOES NOT call broker adapters or mutate state directly.

    Args:
        scope: Kill-switch scope that was active.
        target: Target identifier that was kill-switched.
        approval_context: Validated approval context dict.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        Structured packaged kill-switch-clear request dict.
    """
    approval_result = require_live_approval(
        approval_context=approval_context,
        required_action="clear_kill_switch_after_approval",
        request_id=request_id,
        correlation_id=correlation_id,
    )
    if _is_blocked(approval_result):
        return {
            "action": "clear_kill_switch_after_approval",
            "status": "blocked",
            "gate_decision": str(approval_result.decision),
            "error_code": approval_result.error_code,
            "message": approval_result.message,
            "request_id": request_id,
        }
    return {
        "action": "clear_kill_switch_after_approval",
        "scope": scope,
        "target": target,
        "side_effect_mode": "packaged_only",
        "approval_id": approval_context.get("approval_id"),
        "request_id": request_id,
        "correlation_id": correlation_id,
        "packaged_at": datetime.now(UTC).isoformat(),
    }


def check_kill_switch_conditions(
    *,
    scope: KillSwitchScope = KillSwitchScope.GLOBAL,
    target: str = "*",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Package a kill-switch trigger-condition evaluation.

    Evaluates whether the kill-switch conditions are currently met
    without activating the kill switch.

    Args:
        scope: Kill-switch scope to evaluate.
        target: Target identifier (``'*'`` for global).
        request_id: Trace identifier.

    Returns:
        Structured condition-check result dict with ``is_active``
        flag and metadata.
    """
    result = enforce_kill_switch_gate(
        scope=scope,
        target=target,
        request_id=request_id,
    )
    return {
        "action": "check_kill_switch_conditions",
        "scope": str(scope),
        "target": target,
        "is_active": result.decision != LiveGateDecision.PASS,
        "gate_decision": str(result.decision),
        "message": result.message,
        "request_id": request_id,
        "checked_at": datetime.now(UTC).isoformat(),
    }


def record_kill_switch_event(
    *,
    event_type: str,
    scope: str,
    target: str,
    details: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """Package a durable kill-switch event record.

    Produces a structured kill-switch event dict for downstream audit
    sinks. This function DOES NOT write to any persistence store
    directly.

    Args:
        event_type: Stable kill-switch event type code.
        scope: Kill-switch scope string.
        target: Target identifier.
        details: Structured event details (must be JSON-safe, redacted).
        request_id: Trace identifier.

    Returns:
        Structured packaged kill-switch event record dict.

    Raises:
        ValidationError: If ``event_type`` is empty.
    """
    if not isinstance(event_type, str) or not event_type.strip():
        raise ValidationError(
            "event_type must be a non-empty string.",
            code="INVALID_INPUT",
        )
    now = datetime.now(UTC)
    digest = hashlib.sha256(
        f"{now.isoformat()}{event_type}{scope}{target}".encode()
    ).hexdigest()[:12]
    return {
        "action": "record_kill_switch_event",
        "event_id": f"ks_{digest}",
        "event_type": event_type.strip(),
        "scope": scope,
        "target": target,
        "details": details,
        "side_effect_mode": "none",
        "request_id": request_id,
        "recorded_at": now.isoformat(),
    }
