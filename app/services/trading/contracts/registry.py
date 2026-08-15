"""Exact public contract catalog and non-executable Trading drafts."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Literal

from pydantic import ValidationError as PydanticValidationError

from app.services.trading.contracts.models import (
    TRADING_CONTRACT_VERSION,
    JsonValue,
    TradingRequest,
)
from app.services.trading.contracts.responses import (
    error_trading_response,
    success_trading_response,
)
from app.utils import get_logger, redact_text_value

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)


def _contract_entry(
    symbol: str,
    kind: str,
    schema_id: str | None,
    *,
    side_effects: list[str] | None = None,
    approval_required: bool = False,
    idempotency: str = "none",
    statuses: list[str] | None = None,
    errors: list[str] | None = None,
) -> Mapping[str, JsonValue]:
    """Build one immutable public-catalog entry.

    Args:
        symbol: Public Python symbol.
        kind: Contract category.
        schema_id: Versioned schema identifier when applicable.
        side_effects: Declared external side effects.
        approval_required: Whether execution approval is required.
        idempotency: Idempotency behavior.
        statuses: Finite result statuses.
        errors: Finite error families.

    Returns:
        Immutable JSON-safe catalog entry.
    """
    logger.debug("Building Trading public-catalog entry for %s", symbol)
    safe_side_effects: list[JsonValue] = list(side_effects or [])
    safe_statuses: list[JsonValue] = list(statuses or [])
    safe_errors: list[JsonValue] = list(errors or [])
    entry: dict[str, JsonValue] = {
        "symbol": symbol,
        "kind": kind,
        "contract_version": TRADING_CONTRACT_VERSION,
        "schema_id": schema_id,
        "routes": ["sim", "paper", "live"],
        "side_effects": safe_side_effects,
        "approval_required": approval_required,
        "idempotency": idempotency,
        "statuses": safe_statuses,
        "errors": safe_errors,
        "stability": "stable",
    }
    return MappingProxyType(entry)


_PUBLIC_FUNCTION_NAMES = (
    "build_economic_execution_event",
    "build_execution_audit_record",
    "evaluate_trading_permissions",
    "parse_economic_execution_event",
    "parse_execution_audit_record",
    "reconcile_execution_state",
    "apply_order_fill",
    "assign_trade_ownership",
    "build_order_intent",
    "build_protective_order_plan",
    "build_trade_ownership",
    "create_fill_aggregate",
    "create_order_lifecycle",
    "create_protective_order_plan",
    "create_trade_ownership_registry",
    "detect_orphaned_trade",
    "get_fill_residual",
    "get_trade_ownership",
    "parse_order_intent",
    "parse_protective_order_plan",
    "parse_trade_ownership",
    "persist_protective_order_plan",
    "persist_trade_ownership",
    "resize_protective_orders",
    "transition_order_lifecycle",
    "verify_protective_order_coverage",
    "apply_execution_event",
    "assess_execution_readiness",
    "build_broker_state_unknown_event",
    "build_execution_plan",
    "build_trading_report",
    "build_trading_state_store",
    "cancel_all_orders",
    "cancel_order",
    "classify_authority_response",
    "clear_kill_switch",
    "close_all_positions",
    "close_position",
    "compare_authority_state",
    "create_authority_resolution",
    "create_authority_snapshot",
    "create_closed_position_record",
    "create_execution_evidence_report",
    "create_execution_position",
    "create_execution_position_store",
    "create_execution_receipt",
    "create_legacy_compatible_trading_request",
    "create_idempotency_reservation",
    "create_live_session",
    "create_operational_event",
    "create_order_intent",
    "create_order_intent_v2",
    "create_portfolio_rebalance_execution_request",
    "create_readiness_assessment",
    "create_reconciliation_report",
    "create_route_snapshot",
    "create_trade_record",
    "create_trading_action_draft",
    "create_trading_dependencies",
    "create_trading_error",
    "create_trading_event",
    "create_trading_projection",
    "create_trading_request",
    "create_trading_request_v2",
    "dispatch_order_intent",
    "emit_runtime_event",
    "evaluate_live_gate",
    "execute_portfolio_rebalance",
    "execute_trading_state_store_operation",
    "get_execution_position",
    "get_execution_position_snapshot",
    "get_live_session_status",
    "get_public_contracts",
    "get_route_snapshot",
    "get_trading_contract_version",
    "get_trading_migrations",
    "get_trading_operational_events",
    "get_trading_projection",
    "get_trading_route",
    "get_trading_schema_version",
    "is_live_session_admission_enabled",
    "is_live_session_reconciliation_ready",
    "is_live_session_started",
    "is_execution_receipt",
    "is_trading_error",
    "map_trading_error",
    "modify_order",
    "modify_position",
    "pause_strategy",
    "persist_closed_position",
    "redact_trading_payload",
    "reduce_exposure",
    "reserve_idempotency",
    "resolve_unknown_outcome",
    "resume_strategy",
    "run_live_evaluation_cycle",
    "run_trading_migrations",
    "set_execution_position",
    "start_live_session",
    "stop_live_session",
    "submit_order",
    "sync_positions",
    "trigger_kill_switch",
    "transition_execution_position",
    "validate_adapter_capability",
    "validate_budget_authority",
    "validate_order_request",
)

_MUTATING_FUNCTIONS = frozenset(
    {
        "apply_order_fill",
        "assign_trade_ownership",
        "cancel_all_orders",
        "cancel_order",
        "clear_kill_switch",
        "close_all_positions",
        "close_position",
        "dispatch_order_intent",
        "execute_portfolio_rebalance",
        "modify_order",
        "modify_position",
        "pause_strategy",
        "persist_closed_position",
        "persist_protective_order_plan",
        "persist_trade_ownership",
        "reduce_exposure",
        "resize_protective_orders",
        "resume_strategy",
        "run_live_evaluation_cycle",
        "start_live_session",
        "stop_live_session",
        "submit_order",
        "sync_positions",
        "set_execution_position",
        "transition_execution_position",
        "transition_order_lifecycle",
        "trigger_kill_switch",
    }
)


def _build_public_contracts() -> tuple[Mapping[str, JsonValue], ...]:
    """Build the immutable ordered public API catalog on demand.

    Returns:
        Immutable ordered public-contract entries.
    """
    logger.debug("Building the Trading public-contract catalog")
    return tuple(
        _contract_entry(
            symbol,
            "function",
            None,
            side_effects=["route_or_state_mutation"]
            if symbol in _MUTATING_FUNCTIONS
            else [],
            approval_required=symbol in _MUTATING_FUNCTIONS,
            idempotency="caller_key" if symbol in _MUTATING_FUNCTIONS else "none",
        )
        for symbol in _PUBLIC_FUNCTION_NAMES
    )


def get_public_contracts() -> StandardResponse[tuple[Mapping[str, JsonValue], ...]]:
    """Return the exact stable Trading contracts API catalog.

    Returns:
        Immutable ordered public-contract entries.
    """
    logger.debug("Returning the Trading public-contract catalog")
    return success_trading_response(
        _build_public_contracts(),
        operation="trading.get_public_contracts",
        message="Trading public contracts returned",
        risk_level="low",
        read_only=True,
    )


def create_trading_action_draft(
    request: Mapping[str, JsonValue],
) -> StandardResponse[TradingRequest]:
    """Validate and package a request without invoking route authority.

    Args:
        request: Canonical request material to package.

    Returns:
        Non-executable packaged Trading envelope.

    Raises:
        TradingError: If request material is invalid.
    """
    logger.info("Creating a non-executable Trading action draft")
    try:
        validated = TradingRequest.model_validate(dict(request))
    except PydanticValidationError:
        logger.warning("Rejecting invalid Trading draft material")
        return error_trading_response(
            code="INVALID_DRAFT",
            details={
                "request_id": request.get("request_id")
                if isinstance(request.get("request_id"), str)
                else None,
                "correlation_id": request.get("correlation_id")
                if isinstance(request.get("correlation_id"), str)
                else None,
            },
            operation="trading.create_trading_action_draft",
            message="Trading draft material is invalid",
            risk_level="high",
            read_only=True,
        )
    safe_validated = validated
    if validated.control_reason is not None:
        safe_validated = validated.model_copy(
            update={
                "control_reason": str(redact_text_value(validated.control_reason).value)
            }
        )
    return success_trading_response(
        safe_validated,
        operation="trading.create_trading_action_draft",
        message="Trading action draft packaged without execution",
        risk_level="high",
        request_id=safe_validated.request_id,
        correlation_id=safe_validated.correlation_id,
        read_only=True,
        legacy_status="packaged",
        extensions={
            "route": safe_validated.route.value,
            "provider_id": safe_validated.provider_id,
            "approval_token_ref": safe_validated.approval_token_ref,
            "risk_decision_id": safe_validated.risk_decision_id,
            "risk_classification": "risk_approved",
            "side_effect_classification": "none",
            "idempotency_key": safe_validated.idempotency_key,
            "payload_version": safe_validated.canonical_material_version,
            "redaction_applied": True,
        },
    )


__all__ = ["create_trading_action_draft", "get_public_contracts"]
