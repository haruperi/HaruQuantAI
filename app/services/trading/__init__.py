"""Function-only public boundary for the complete Trading domain."""

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.trading.actions import (
        build_approved_trading_request,
        cancel_all_orders,
        cancel_order,
        clear_kill_switch,
        close_all_positions,
        close_position,
        create_monotonic_deadline_factory,
        create_trading_dependencies,
        evaluate_trading_permissions,
        execute_portfolio_rebalance,
        modify_order,
        modify_position,
        pause_strategy,
        reduce_exposure,
        resume_strategy,
        run_live_evaluation_cycle,
        submit_order,
        sync_positions,
        trigger_kill_switch,
    )
    from app.services.trading.contracts import (
        build_order_intent,
        create_closed_position_record,
        create_execution_evidence_report,
        create_execution_receipt,
        create_legacy_compatible_trading_request,
        create_order_intent,
        create_order_intent_v2,
        create_portfolio_rebalance_execution_request,
        create_trade_record,
        create_trading_action_draft,
        create_trading_error,
        create_trading_request,
        create_trading_request_v2,
        get_public_contracts,
        get_trading_contract_version,
        get_trading_route,
        is_execution_receipt,
        is_trading_error,
        map_trading_error,
        parse_order_intent,
        redact_trading_payload,
    )
    from app.services.trading.live import (
        create_live_session,
        evaluate_live_gate,
        get_live_session_status,
        is_live_session_admission_enabled,
        is_live_session_reconciliation_ready,
        is_live_session_started,
        start_live_session,
        stop_live_session,
    )
    from app.services.trading.monitoring import (
        build_broker_state_unknown_event,
        build_economic_execution_event,
        create_operational_event,
        emit_runtime_event,
        parse_economic_execution_event,
        validate_budget_authority,
    )
    from app.services.trading.monitoring.runtime import get_trading_operational_events
    from app.services.trading.persistence import (
        create_closed_position_record as persist_closed_position,
    )
    from app.services.trading.protective_orders import (
        build_protective_order_plan,
        create_protective_order_plan,
        parse_protective_order_plan,
        persist_protective_order_plan,
        resize_protective_orders,
        verify_protective_order_coverage,
    )
    from app.services.trading.reconciliation import (
        compare_authority_state,
        create_authority_resolution,
        create_authority_snapshot,
        create_reconciliation_report,
        reconcile_execution_state,
        resolve_unknown_outcome,
    )
    from app.services.trading.reporting import (
        build_execution_audit_record,
        build_trading_report,
        parse_execution_audit_record,
    )
    from app.services.trading.routing import (
        classify_authority_response,
        dispatch_order_intent,
        validate_adapter_capability,
    )
    from app.services.trading.session_registry import (
        archive_execution_session,
        assign_simulation_session_identity,
        complete_simulation_session_configuration,
        create_execution_session,
        get_execution_session,
        get_execution_session_events,
        list_execution_sessions,
        resolve_active_execution_session,
        set_default_execution_session,
        start_execution_session,
        stop_execution_session,
        update_execution_session_metadata,
    )
    from app.services.trading.state import (
        apply_execution_event,
        apply_order_fill,
        build_trading_state_store,
        create_execution_position,
        create_execution_position_store,
        create_fill_aggregate,
        create_idempotency_reservation,
        create_order_lifecycle,
        create_position_authority_event,
        create_trading_event,
        create_trading_projection,
        execute_trading_state_store_operation,
        get_execution_position,
        get_execution_position_snapshot,
        get_fill_residual,
        get_position_authority_watermark,
        get_trading_migrations,
        get_trading_projection,
        get_trading_schema_version,
        reconcile_execution_position_receipt,
        reconcile_position_authority_event,
        reserve_idempotency,
        restore_execution_position_store,
        run_trading_migrations,
        serialize_execution_position_store,
        set_execution_position,
        transition_execution_position,
        transition_order_lifecycle,
    )
    from app.services.trading.trade_ownership import (
        assign_trade_ownership,
        build_trade_ownership,
        create_trade_ownership_registry,
        detect_orphaned_trade,
        get_trade_ownership,
        parse_trade_ownership,
        persist_trade_ownership,
    )
    from app.services.trading.validation import (
        assess_execution_readiness,
        build_execution_plan,
        create_readiness_assessment,
        create_route_snapshot,
        get_route_snapshot,
        validate_order_request,
    )

# Public export name to the module and attribute that owns it. Resolved on
# first access so importing this boundary never loads every feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "apply_execution_event": ("app.services.trading.state", "apply_execution_event"),
    "apply_order_fill": ("app.services.trading.state", "apply_order_fill"),
    "archive_execution_session": (
        "app.services.trading.session_registry",
        "archive_execution_session",
    ),
    "assess_execution_readiness": (
        "app.services.trading.validation",
        "assess_execution_readiness",
    ),
    "assign_simulation_session_identity": (
        "app.services.trading.session_registry",
        "assign_simulation_session_identity",
    ),
    "assign_trade_ownership": (
        "app.services.trading.trade_ownership",
        "assign_trade_ownership",
    ),
    "build_approved_trading_request": (
        "app.services.trading.actions",
        "build_approved_trading_request",
    ),
    "build_broker_state_unknown_event": (
        "app.services.trading.monitoring",
        "build_broker_state_unknown_event",
    ),
    "build_economic_execution_event": (
        "app.services.trading.monitoring",
        "build_economic_execution_event",
    ),
    "build_execution_audit_record": (
        "app.services.trading.reporting",
        "build_execution_audit_record",
    ),
    "build_execution_plan": ("app.services.trading.validation", "build_execution_plan"),
    "build_order_intent": ("app.services.trading.contracts", "build_order_intent"),
    "build_protective_order_plan": (
        "app.services.trading.protective_orders",
        "build_protective_order_plan",
    ),
    "build_trade_ownership": (
        "app.services.trading.trade_ownership",
        "build_trade_ownership",
    ),
    "build_trading_report": ("app.services.trading.reporting", "build_trading_report"),
    "build_trading_state_store": (
        "app.services.trading.state",
        "build_trading_state_store",
    ),
    "cancel_all_orders": ("app.services.trading.actions", "cancel_all_orders"),
    "cancel_order": ("app.services.trading.actions", "cancel_order"),
    "classify_authority_response": (
        "app.services.trading.routing",
        "classify_authority_response",
    ),
    "clear_kill_switch": ("app.services.trading.actions", "clear_kill_switch"),
    "close_all_positions": ("app.services.trading.actions", "close_all_positions"),
    "close_position": ("app.services.trading.actions", "close_position"),
    "compare_authority_state": (
        "app.services.trading.reconciliation",
        "compare_authority_state",
    ),
    "complete_simulation_session_configuration": (
        "app.services.trading.session_registry",
        "complete_simulation_session_configuration",
    ),
    "create_authority_resolution": (
        "app.services.trading.reconciliation",
        "create_authority_resolution",
    ),
    "create_authority_snapshot": (
        "app.services.trading.reconciliation",
        "create_authority_snapshot",
    ),
    "create_closed_position_record": (
        "app.services.trading.contracts",
        "create_closed_position_record",
    ),
    "create_execution_evidence_report": (
        "app.services.trading.contracts",
        "create_execution_evidence_report",
    ),
    "create_execution_position": (
        "app.services.trading.state",
        "create_execution_position",
    ),
    "create_execution_position_store": (
        "app.services.trading.state",
        "create_execution_position_store",
    ),
    "create_execution_receipt": (
        "app.services.trading.contracts",
        "create_execution_receipt",
    ),
    "create_execution_session": (
        "app.services.trading.session_registry",
        "create_execution_session",
    ),
    "create_fill_aggregate": ("app.services.trading.state", "create_fill_aggregate"),
    "create_idempotency_reservation": (
        "app.services.trading.state",
        "create_idempotency_reservation",
    ),
    "create_legacy_compatible_trading_request": (
        "app.services.trading.contracts",
        "create_legacy_compatible_trading_request",
    ),
    "create_live_session": ("app.services.trading.live", "create_live_session"),
    "create_monotonic_deadline_factory": (
        "app.services.trading.actions",
        "create_monotonic_deadline_factory",
    ),
    "create_operational_event": (
        "app.services.trading.monitoring",
        "create_operational_event",
    ),
    "create_order_intent": ("app.services.trading.contracts", "create_order_intent"),
    "create_order_intent_v2": (
        "app.services.trading.contracts",
        "create_order_intent_v2",
    ),
    "create_order_lifecycle": ("app.services.trading.state", "create_order_lifecycle"),
    "create_portfolio_rebalance_execution_request": (
        "app.services.trading.contracts",
        "create_portfolio_rebalance_execution_request",
    ),
    "create_position_authority_event": (
        "app.services.trading.state",
        "create_position_authority_event",
    ),
    "create_protective_order_plan": (
        "app.services.trading.protective_orders",
        "create_protective_order_plan",
    ),
    "create_readiness_assessment": (
        "app.services.trading.validation",
        "create_readiness_assessment",
    ),
    "create_reconciliation_report": (
        "app.services.trading.reconciliation",
        "create_reconciliation_report",
    ),
    "create_route_snapshot": (
        "app.services.trading.validation",
        "create_route_snapshot",
    ),
    "create_trade_ownership_registry": (
        "app.services.trading.trade_ownership",
        "create_trade_ownership_registry",
    ),
    "create_trade_record": ("app.services.trading.contracts", "create_trade_record"),
    "create_trading_action_draft": (
        "app.services.trading.contracts",
        "create_trading_action_draft",
    ),
    "create_trading_dependencies": (
        "app.services.trading.actions",
        "create_trading_dependencies",
    ),
    "create_trading_error": ("app.services.trading.contracts", "create_trading_error"),
    "create_trading_event": ("app.services.trading.state", "create_trading_event"),
    "create_trading_projection": (
        "app.services.trading.state",
        "create_trading_projection",
    ),
    "create_trading_request": (
        "app.services.trading.contracts",
        "create_trading_request",
    ),
    "create_trading_request_v2": (
        "app.services.trading.contracts",
        "create_trading_request_v2",
    ),
    "detect_orphaned_trade": (
        "app.services.trading.trade_ownership",
        "detect_orphaned_trade",
    ),
    "dispatch_order_intent": ("app.services.trading.routing", "dispatch_order_intent"),
    "emit_runtime_event": ("app.services.trading.monitoring", "emit_runtime_event"),
    "evaluate_live_gate": ("app.services.trading.live", "evaluate_live_gate"),
    "evaluate_trading_permissions": (
        "app.services.trading.actions",
        "evaluate_trading_permissions",
    ),
    "execute_portfolio_rebalance": (
        "app.services.trading.actions",
        "execute_portfolio_rebalance",
    ),
    "execute_trading_state_store_operation": (
        "app.services.trading.state",
        "execute_trading_state_store_operation",
    ),
    "get_execution_position": ("app.services.trading.state", "get_execution_position"),
    "get_execution_position_snapshot": (
        "app.services.trading.state",
        "get_execution_position_snapshot",
    ),
    "get_execution_session": (
        "app.services.trading.session_registry",
        "get_execution_session",
    ),
    "get_execution_session_events": (
        "app.services.trading.session_registry",
        "get_execution_session_events",
    ),
    "get_fill_residual": ("app.services.trading.state", "get_fill_residual"),
    "get_live_session_status": ("app.services.trading.live", "get_live_session_status"),
    "get_position_authority_watermark": (
        "app.services.trading.state",
        "get_position_authority_watermark",
    ),
    "get_public_contracts": ("app.services.trading.contracts", "get_public_contracts"),
    "get_route_snapshot": ("app.services.trading.validation", "get_route_snapshot"),
    "get_trade_ownership": (
        "app.services.trading.trade_ownership",
        "get_trade_ownership",
    ),
    "get_trading_contract_version": (
        "app.services.trading.contracts",
        "get_trading_contract_version",
    ),
    "get_trading_migrations": ("app.services.trading.state", "get_trading_migrations"),
    "get_trading_operational_events": (
        "app.services.trading.monitoring.runtime",
        "get_trading_operational_events",
    ),
    "get_trading_projection": ("app.services.trading.state", "get_trading_projection"),
    "get_trading_route": ("app.services.trading.contracts", "get_trading_route"),
    "get_trading_schema_version": (
        "app.services.trading.state",
        "get_trading_schema_version",
    ),
    "is_execution_receipt": ("app.services.trading.contracts", "is_execution_receipt"),
    "is_live_session_admission_enabled": (
        "app.services.trading.live",
        "is_live_session_admission_enabled",
    ),
    "is_live_session_reconciliation_ready": (
        "app.services.trading.live",
        "is_live_session_reconciliation_ready",
    ),
    "is_live_session_started": ("app.services.trading.live", "is_live_session_started"),
    "is_trading_error": ("app.services.trading.contracts", "is_trading_error"),
    "list_execution_sessions": (
        "app.services.trading.session_registry",
        "list_execution_sessions",
    ),
    "map_trading_error": ("app.services.trading.contracts", "map_trading_error"),
    "modify_order": ("app.services.trading.actions", "modify_order"),
    "modify_position": ("app.services.trading.actions", "modify_position"),
    "parse_economic_execution_event": (
        "app.services.trading.monitoring",
        "parse_economic_execution_event",
    ),
    "parse_execution_audit_record": (
        "app.services.trading.reporting",
        "parse_execution_audit_record",
    ),
    "parse_order_intent": ("app.services.trading.contracts", "parse_order_intent"),
    "parse_protective_order_plan": (
        "app.services.trading.protective_orders",
        "parse_protective_order_plan",
    ),
    "parse_trade_ownership": (
        "app.services.trading.trade_ownership",
        "parse_trade_ownership",
    ),
    "pause_strategy": ("app.services.trading.actions", "pause_strategy"),
    "persist_closed_position": (
        "app.services.trading.persistence",
        "create_closed_position_record",
    ),
    "persist_protective_order_plan": (
        "app.services.trading.protective_orders",
        "persist_protective_order_plan",
    ),
    "persist_trade_ownership": (
        "app.services.trading.trade_ownership",
        "persist_trade_ownership",
    ),
    "reconcile_execution_position_receipt": (
        "app.services.trading.state",
        "reconcile_execution_position_receipt",
    ),
    "reconcile_execution_state": (
        "app.services.trading.reconciliation",
        "reconcile_execution_state",
    ),
    "reconcile_position_authority_event": (
        "app.services.trading.state",
        "reconcile_position_authority_event",
    ),
    "redact_trading_payload": (
        "app.services.trading.contracts",
        "redact_trading_payload",
    ),
    "reduce_exposure": ("app.services.trading.actions", "reduce_exposure"),
    "reserve_idempotency": ("app.services.trading.state", "reserve_idempotency"),
    "resize_protective_orders": (
        "app.services.trading.protective_orders",
        "resize_protective_orders",
    ),
    "resolve_active_execution_session": (
        "app.services.trading.session_registry",
        "resolve_active_execution_session",
    ),
    "resolve_unknown_outcome": (
        "app.services.trading.reconciliation",
        "resolve_unknown_outcome",
    ),
    "restore_execution_position_store": (
        "app.services.trading.state",
        "restore_execution_position_store",
    ),
    "resume_strategy": ("app.services.trading.actions", "resume_strategy"),
    "run_live_evaluation_cycle": (
        "app.services.trading.actions",
        "run_live_evaluation_cycle",
    ),
    "run_trading_migrations": ("app.services.trading.state", "run_trading_migrations"),
    "serialize_execution_position_store": (
        "app.services.trading.state",
        "serialize_execution_position_store",
    ),
    "set_default_execution_session": (
        "app.services.trading.session_registry",
        "set_default_execution_session",
    ),
    "set_execution_position": ("app.services.trading.state", "set_execution_position"),
    "start_execution_session": (
        "app.services.trading.session_registry",
        "start_execution_session",
    ),
    "start_live_session": ("app.services.trading.live", "start_live_session"),
    "stop_execution_session": (
        "app.services.trading.session_registry",
        "stop_execution_session",
    ),
    "stop_live_session": ("app.services.trading.live", "stop_live_session"),
    "submit_order": ("app.services.trading.actions", "submit_order"),
    "sync_positions": ("app.services.trading.actions", "sync_positions"),
    "transition_execution_position": (
        "app.services.trading.state",
        "transition_execution_position",
    ),
    "transition_order_lifecycle": (
        "app.services.trading.state",
        "transition_order_lifecycle",
    ),
    "trigger_kill_switch": ("app.services.trading.actions", "trigger_kill_switch"),
    "update_execution_session_metadata": (
        "app.services.trading.session_registry",
        "update_execution_session_metadata",
    ),
    "validate_adapter_capability": (
        "app.services.trading.routing",
        "validate_adapter_capability",
    ),
    "validate_budget_authority": (
        "app.services.trading.monitoring",
        "validate_budget_authority",
    ),
    "validate_order_request": (
        "app.services.trading.validation",
        "validate_order_request",
    ),
    "verify_protective_order_coverage": (
        "app.services.trading.protective_orders",
        "verify_protective_order_coverage",
    ),
}


def __getattr__(name: str) -> object:
    """Resolve one public export on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


__all__: tuple[str, ...] = (
    "apply_execution_event",
    "apply_order_fill",
    "archive_execution_session",
    "assess_execution_readiness",
    "assign_simulation_session_identity",
    "assign_trade_ownership",
    "build_approved_trading_request",
    "build_broker_state_unknown_event",
    "build_economic_execution_event",
    "build_execution_audit_record",
    "build_execution_plan",
    "build_order_intent",
    "build_protective_order_plan",
    "build_trade_ownership",
    "build_trading_report",
    "build_trading_state_store",
    "cancel_all_orders",
    "cancel_order",
    "classify_authority_response",
    "clear_kill_switch",
    "close_all_positions",
    "close_position",
    "compare_authority_state",
    "complete_simulation_session_configuration",
    "create_authority_resolution",
    "create_authority_snapshot",
    "create_closed_position_record",
    "create_execution_evidence_report",
    "create_execution_position",
    "create_execution_position_store",
    "create_execution_receipt",
    "create_execution_session",
    "create_fill_aggregate",
    "create_idempotency_reservation",
    "create_legacy_compatible_trading_request",
    "create_live_session",
    "create_monotonic_deadline_factory",
    "create_operational_event",
    "create_order_intent",
    "create_order_intent_v2",
    "create_order_lifecycle",
    "create_portfolio_rebalance_execution_request",
    "create_position_authority_event",
    "create_protective_order_plan",
    "create_readiness_assessment",
    "create_reconciliation_report",
    "create_route_snapshot",
    "create_trade_ownership_registry",
    "create_trade_record",
    "create_trading_action_draft",
    "create_trading_dependencies",
    "create_trading_error",
    "create_trading_event",
    "create_trading_projection",
    "create_trading_request",
    "create_trading_request_v2",
    "detect_orphaned_trade",
    "dispatch_order_intent",
    "emit_runtime_event",
    "evaluate_live_gate",
    "evaluate_trading_permissions",
    "execute_portfolio_rebalance",
    "execute_trading_state_store_operation",
    "get_execution_position",
    "get_execution_position_snapshot",
    "get_execution_session",
    "get_execution_session_events",
    "get_fill_residual",
    "get_live_session_status",
    "get_position_authority_watermark",
    "get_public_contracts",
    "get_route_snapshot",
    "get_trade_ownership",
    "get_trading_contract_version",
    "get_trading_migrations",
    "get_trading_operational_events",
    "get_trading_projection",
    "get_trading_route",
    "get_trading_schema_version",
    "is_execution_receipt",
    "is_live_session_admission_enabled",
    "is_live_session_reconciliation_ready",
    "is_live_session_started",
    "is_trading_error",
    "list_execution_sessions",
    "map_trading_error",
    "modify_order",
    "modify_position",
    "parse_economic_execution_event",
    "parse_execution_audit_record",
    "parse_order_intent",
    "parse_protective_order_plan",
    "parse_trade_ownership",
    "pause_strategy",
    "persist_closed_position",
    "persist_protective_order_plan",
    "persist_trade_ownership",
    "reconcile_execution_position_receipt",
    "reconcile_execution_state",
    "reconcile_position_authority_event",
    "redact_trading_payload",
    "reduce_exposure",
    "reserve_idempotency",
    "resize_protective_orders",
    "resolve_active_execution_session",
    "resolve_unknown_outcome",
    "restore_execution_position_store",
    "resume_strategy",
    "run_live_evaluation_cycle",
    "run_trading_migrations",
    "serialize_execution_position_store",
    "set_default_execution_session",
    "set_execution_position",
    "start_execution_session",
    "start_live_session",
    "stop_execution_session",
    "stop_live_session",
    "submit_order",
    "sync_positions",
    "transition_execution_position",
    "transition_order_lifecycle",
    "trigger_kill_switch",
    "update_execution_session_metadata",
    "validate_adapter_capability",
    "validate_budget_authority",
    "validate_order_request",
    "verify_protective_order_coverage",
)
