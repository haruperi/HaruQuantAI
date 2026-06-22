"""Live action policy matrix.

Defines the authoritative policy for every live action: approval
requirements, emergency fail-safe eligibility, idempotency, side-
effect ceiling, and audit requirements.

This matrix is the single source of truth for gate enforcement.
Emergency fail-safe classification, approval requirements, and
side-effect ceilings MUST be read from this module. They MUST NOT
be inferred from request text, user role, API route, or chat
instruction.

Public exports:
    LIVE_POLICY_UNDEFINED, LiveActionPolicy,
    LIVE_ACTION_POLICY_MATRIX, get_action_policy.

Side effects:
    None.
"""

from __future__ import annotations

from dataclasses import dataclass

LIVE_POLICY_UNDEFINED = "LIVE_POLICY_UNDEFINED"


@dataclass(frozen=True)
class LiveActionPolicy:
    """Policy entry for a single live action.

    Attributes:
        action: Stable action name (matches gate/function name).
        owning_module: Module that implements the action.
        approval_required: Whether explicit approval context is
            required before broker mutation.
        emergency_fail_safe: ``True`` only for actions classified as
            emergency fail-safes by the owner/architect. This flag is
            set exclusively in this matrix; it MUST NOT be inferred
            from any other source.
        idempotency_required: Whether an idempotency key is mandatory
            before broker mutation.
        side_effect_ceiling: Maximum permitted side-effect mode string.
        required_audit_events: Required audit event type codes.
        retry_safety_default: Default retry-safety classification.
        operator_review_required: Whether post-action operator review
            is required before the next mutation is allowed.
    """

    action: str
    owning_module: str
    approval_required: bool
    emergency_fail_safe: bool
    idempotency_required: bool
    side_effect_ceiling: str
    required_audit_events: tuple[str, ...]
    retry_safety_default: str
    operator_review_required: bool


LIVE_ACTION_POLICY_MATRIX: dict[str, LiveActionPolicy] = {
    "submit_order": LiveActionPolicy(
        action="submit_order",
        owning_module="app.services.live.executor",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=True,
        side_effect_ceiling="broker_mutation_confirmed",
        required_audit_events=(
            "audit.pre_submit",
            "audit.post_submit",
        ),
        retry_safety_default="do_not_retry",
        operator_review_required=False,
    ),
    "modify_order": LiveActionPolicy(
        action="modify_order",
        owning_module="app.services.live.executor",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=True,
        side_effect_ceiling="broker_mutation_confirmed",
        required_audit_events=(
            "audit.pre_modify_order",
            "audit.post_modify_order",
        ),
        retry_safety_default="do_not_retry",
        operator_review_required=False,
    ),
    "cancel_order": LiveActionPolicy(
        action="cancel_order",
        owning_module="app.services.live.executor",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=True,
        side_effect_ceiling="broker_mutation_confirmed",
        required_audit_events=(
            "audit.pre_cancel_order",
            "audit.post_cancel_order",
        ),
        retry_safety_default="retry_after_reconciliation",
        operator_review_required=False,
    ),
    "close_position": LiveActionPolicy(
        action="close_position",
        owning_module="app.services.live.executor",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=True,
        side_effect_ceiling="broker_mutation_confirmed",
        required_audit_events=(
            "audit.pre_close_position",
            "audit.post_close_position",
        ),
        retry_safety_default="retry_after_reconciliation",
        operator_review_required=True,
    ),
    "modify_position": LiveActionPolicy(
        action="modify_position",
        owning_module="app.services.live.executor",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=True,
        side_effect_ceiling="broker_mutation_confirmed",
        required_audit_events=(
            "audit.pre_modify_position",
            "audit.post_modify_position",
        ),
        retry_safety_default="do_not_retry",
        operator_review_required=False,
    ),
    "reduce_exposure": LiveActionPolicy(
        action="reduce_exposure",
        owning_module="app.services.live.executor",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=True,
        side_effect_ceiling="broker_mutation_confirmed",
        required_audit_events=(
            "audit.pre_reduce_exposure",
            "audit.post_reduce_exposure",
        ),
        retry_safety_default="retry_after_reconciliation",
        operator_review_required=True,
    ),
    "pause_strategy": LiveActionPolicy(
        action="pause_strategy",
        owning_module="app.services.live.executor",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="packaged_only",
        required_audit_events=("audit.strategy_paused",),
        retry_safety_default="safe_to_retry",
        operator_review_required=False,
    ),
    "resume_strategy": LiveActionPolicy(
        action="resume_strategy",
        owning_module="app.services.live.executor",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="packaged_only",
        required_audit_events=("audit.strategy_resumed",),
        retry_safety_default="safe_to_retry",
        operator_review_required=False,
    ),
    "sync_positions": LiveActionPolicy(
        action="sync_positions",
        owning_module="app.services.live.executor",
        approval_required=False,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="packaged_only",
        required_audit_events=("audit.positions_synced",),
        retry_safety_default="safe_to_retry",
        operator_review_required=False,
    ),
    "reconcile_state": LiveActionPolicy(
        action="reconcile_state",
        owning_module="app.services.live.reconciliation",
        approval_required=False,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="none",
        required_audit_events=("audit.reconciliation_completed",),
        retry_safety_default="safe_to_retry",
        operator_review_required=False,
    ),
    "build_trading_report": LiveActionPolicy(
        action="build_trading_report",
        owning_module="app.services.live.executor",
        approval_required=False,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="none",
        required_audit_events=(),
        retry_safety_default="safe_to_retry",
        operator_review_required=False,
    ),
    "disable_new_orders": LiveActionPolicy(
        action="disable_new_orders",
        owning_module="app.services.live.gates",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="packaged_only",
        required_audit_events=("audit.orders_disabled",),
        retry_safety_default="do_not_retry",
        operator_review_required=True,
    ),
    "trigger_global_kill_switch": LiveActionPolicy(
        action="trigger_global_kill_switch",
        owning_module="app.services.live.gates",
        approval_required=False,
        emergency_fail_safe=True,
        idempotency_required=False,
        side_effect_ceiling="packaged_only",
        required_audit_events=("audit.kill_switch_triggered",),
        retry_safety_default="do_not_retry",
        operator_review_required=True,
    ),
    "trigger_strategy_kill_switch": LiveActionPolicy(
        action="trigger_strategy_kill_switch",
        owning_module="app.services.live.gates",
        approval_required=False,
        emergency_fail_safe=True,
        idempotency_required=False,
        side_effect_ceiling="packaged_only",
        required_audit_events=("audit.kill_switch_triggered",),
        retry_safety_default="do_not_retry",
        operator_review_required=True,
    ),
    "trigger_symbol_kill_switch": LiveActionPolicy(
        action="trigger_symbol_kill_switch",
        owning_module="app.services.live.gates",
        approval_required=False,
        emergency_fail_safe=True,
        idempotency_required=False,
        side_effect_ceiling="packaged_only",
        required_audit_events=("audit.kill_switch_triggered",),
        retry_safety_default="do_not_retry",
        operator_review_required=True,
    ),
    "cancel_all_orders": LiveActionPolicy(
        action="cancel_all_orders",
        owning_module="app.services.live.gates",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="broker_mutation_confirmed",
        required_audit_events=("audit.all_orders_cancelled",),
        retry_safety_default="retry_after_reconciliation",
        operator_review_required=True,
    ),
    "close_all_positions": LiveActionPolicy(
        action="close_all_positions",
        owning_module="app.services.live.gates",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="broker_mutation_confirmed",
        required_audit_events=("audit.all_positions_closed",),
        retry_safety_default="retry_after_reconciliation",
        operator_review_required=True,
    ),
    "clear_kill_switch_after_approval": LiveActionPolicy(
        action="clear_kill_switch_after_approval",
        owning_module="app.services.live.gates",
        approval_required=True,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="packaged_only",
        required_audit_events=("audit.kill_switch_cleared",),
        retry_safety_default="do_not_retry",
        operator_review_required=True,
    ),
    "check_kill_switch_conditions": LiveActionPolicy(
        action="check_kill_switch_conditions",
        owning_module="app.services.live.gates",
        approval_required=False,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="none",
        required_audit_events=(),
        retry_safety_default="safe_to_retry",
        operator_review_required=False,
    ),
    "record_kill_switch_event": LiveActionPolicy(
        action="record_kill_switch_event",
        owning_module="app.services.live.gates",
        approval_required=False,
        emergency_fail_safe=False,
        idempotency_required=False,
        side_effect_ceiling="none",
        required_audit_events=("audit.kill_switch_event_recorded",),
        retry_safety_default="safe_to_retry",
        operator_review_required=False,
    ),
}


def get_action_policy(action: str) -> LiveActionPolicy | None:
    """Return the policy entry for a live action.

    Args:
        action: Stable action name as defined in the matrix.

    Returns:
        ``LiveActionPolicy`` for the action, or ``None`` when the
        action has no entry in the matrix. Callers must treat a
        ``None`` return as ``LIVE_POLICY_UNDEFINED`` and block
        execution.
    """
    return LIVE_ACTION_POLICY_MATRIX.get(action)
