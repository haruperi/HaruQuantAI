"""Route-aware public order action verbs."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from typing import TYPE_CHECKING

from app.services.trading.actions._shared import authority_id, require_action
from app.services.trading.contracts import (
    ExecutionReceipt,
    OrderIntent,
    StandardTradingEnvelope,
    TradeRecord,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.live import evaluate_live_gate
from app.services.trading.monitoring import (
    build_broker_state_unknown_event,
    emit_runtime_event,
)
from app.services.trading.reconciliation import resolve_unknown_outcome
from app.services.trading.routing import dispatch_order_intent
from app.services.trading.state import (
    TradingEvent,
    apply_execution_event,
    reserve_idempotency,
)
from app.services.trading.validation import (
    ReadinessAssessment,
    build_execution_plan,
    validate_order_request,
)
from app.services.trading.validation.authority import (
    validate_action_policy,
    validate_kill_switch_hierarchy,
    validate_risk_authority,
)
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.trading.actions.dependencies import TradingDependencies
    from app.services.trading.contracts.models import JsonValue


def _envelope(
    request: TradingRequest,
    receipt: ExecutionReceipt,
) -> StandardTradingEnvelope:
    """Package one authority receipt in the standard envelope.

    Args:
        request: Source governed request.
        receipt: Canonical authority receipt.

    Returns:
        Immutable JSON-safe Trading envelope.
    """
    logger.debug("Packaging Trading authority receipt")
    status_map = {
        "accepted": "sent",
        "rejected": "rejected",
        "partial": "partial",
        "filled": "filled",
        "cancelled": "cancelled",
        "unknown_outcome": "unknown_outcome",
    }
    data = _redacted_envelope_data({"receipt": receipt.model_dump(mode="json")})
    return StandardTradingEnvelope(
        status=status_map[receipt.status],  # type: ignore[arg-type]
        message="Trading authority receipt recorded",
        data=data,
        errors=(),
        warnings=(
            ({"code": "RECONCILIATION_REQUIRED"},)
            if receipt.reconciliation_required
            else ()
        ),
        audit_metadata={
            "operation": request.action,
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
            "redaction_applied": True,
        },
    )


def _event_id(event_type: str, material: Mapping[str, JsonValue]) -> str:
    """Build one deterministic Trading state-event identity.

    Args:
        event_type: Stable event category.
        material: Canonical identity material.

    Returns:
        Full SHA-256 event identity.
    """
    digest = sha256(
        canonical_json({"event_type": event_type, **material}).encode("utf-8")
    ).hexdigest()
    return f"trd-event-{digest}"


def _record_send_attempt(
    request: TradingRequest,
    intent: OrderIntent,
    deps: TradingDependencies,
) -> str:
    """Persist the mutation attempt before crossing the authority boundary.

    Args:
        request: Source governed request.
        intent: Exact executable intent.
        deps: Injected action dependencies.

    Returns:
        Persisted attempt event identifier.
    """
    logger.info("Recording Trading send attempt for %s", request.request_id)
    scope = (request.route, request.account_id, authority_id(request))
    current = deps.store.load_projection(scope)
    version = 0 if current is None else current.version
    event_id = _event_id(
        "send_attempted",
        {
            "request_id": request.request_id,
            "client_order_id": intent.client_order_id,
        },
    )
    event = TradingEvent(
        event_id=event_id,
        event_type="send_attempted",
        aggregate_version=version,
        route=request.route,
        tenant_id=request.account_id,
        authority_id=authority_id(request),
        occurred_at=deps.clock(),
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        causation_id=request.causation_id,
        payload=_redacted_envelope_data(
            {
                "request_id": request.request_id,
                "intent": intent.model_dump(mode="json"),
                "idempotency_key_hash": sha256(
                    request.idempotency_key.encode("utf-8")
                ).hexdigest(),
            }
        ),
    )
    apply_execution_event(event, deps.store)
    return event_id


def _record_receipt(
    request: TradingRequest,
    receipt: ExecutionReceipt,
    attempt_event_id: str,
    deps: TradingDependencies,
) -> None:
    """Persist one receipt as ordered Trading evidence.

    Args:
        request: Source governed request.
        receipt: Authority result to persist.
        attempt_event_id: Persisted pre-dispatch attempt identity.
        deps: Injected action dependencies.
    """
    logger.info("Recording Trading receipt %s", receipt.receipt_id)
    scope = (request.route, request.account_id, authority_id(request))
    current = deps.store.load_projection(scope)
    version = 0 if current is None else current.version
    event_id = _event_id(
        "receipt_recorded",
        {"receipt_id": receipt.receipt_id, "request_id": request.request_id},
    )
    record = TradeRecord(
        record_id=_event_id(
            "trade_record",
            {"receipt_id": receipt.receipt_id, "request_id": request.request_id},
        ),
        receipt=receipt,
        fill_ids=receipt.provider_deal_ids,
        authority_state=receipt.status,
        reconciliation_state=(
            "unreconciled" if receipt.reconciliation_required else "reconciled"
        ),
        warnings=(),
        incidents=(),
        created_at=receipt.received_at,
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
    )
    payload = _redacted_envelope_data(
        {
            "receipt": receipt.model_dump(mode="json"),
            "attempt_event_id": attempt_event_id,
            "trade_record": record.model_dump(mode="json"),
        }
    )
    event = TradingEvent(
        event_id=event_id,
        event_type="receipt_recorded",
        aggregate_version=version,
        route=request.route,
        tenant_id=request.account_id,
        authority_id=authority_id(request),
        occurred_at=receipt.received_at,
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        causation_id=request.causation_id,
        payload=payload,
    )
    apply_execution_event(event, deps.store)
    for deal_id in receipt.provider_deal_ids:
        projection = deps.store.load_projection(scope)
        fill_version = 0 if projection is None else projection.version
        fill = TradingEvent(
            event_id=_event_id(
                "fill_recorded",
                {"receipt_id": receipt.receipt_id, "deal_id": deal_id},
            ),
            event_type="fill_recorded",
            aggregate_version=fill_version,
            route=request.route,
            tenant_id=request.account_id,
            authority_id=authority_id(request),
            occurred_at=receipt.received_at,
            request_id=request.request_id,
            workflow_id=request.workflow_id,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            payload={
                "provider_deal_id": deal_id,
                "receipt_id": receipt.receipt_id,
                "filled_quantity": str(receipt.filled_quantity),
                "average_price": (
                    None
                    if receipt.average_price is None
                    else str(receipt.average_price)
                ),
            },
        )
        apply_execution_event(fill, deps.store)


def _require_clear_authority_scope(
    request: TradingRequest, deps: TradingDependencies
) -> None:
    """Block mutation while any prior attempt remains unresolved in scope.

    Args:
        request: Governed request defining the conflict scope.
        deps: Injected action dependencies.

    Raises:
        TradingError: If persisted authority scope contains unresolved mutation.
    """
    projection = deps.store.load_projection(
        (request.route, request.account_id, authority_id(request))
    )
    if projection is not None and projection.unresolved_attempt_ids:
        raise TradingError(
            "RECONCILIATION_REQUIRED",
            "Trading authority scope contains an unresolved mutation",
        )


def _complete_reservation(
    request: TradingRequest,
    receipt: ExecutionReceipt,
    deps: TradingDependencies,
) -> None:
    """Persist an idempotency outcome after its receipt is durable.

    Args:
        request: Source governed request.
        receipt: Persisted authority receipt.
        deps: Injected action dependencies.

    Raises:
        TradingError: If reservation completion cannot be persisted.
    """
    digest = sha256(
        canonical_json(request.model_dump(mode="python")).encode("utf-8")
    ).hexdigest()
    try:
        deps.store.complete_idempotency(
            request.idempotency_key,
            digest,
            receipt.receipt_id,
            deps.clock(),
            status=(
                "reconciliation_required"
                if receipt.reconciliation_required
                else "completed"
            ),
        )
    except Exception as error:
        raise TradingError(
            "PERSISTENCE_FAILED", "Idempotency completion persistence failed"
        ) from error


def _resolve_unknown(
    request: TradingRequest,
    receipt: ExecutionReceipt,
    deps: TradingDependencies,
) -> None:
    """Reconcile and publish one critical retry-lock transition when required.

    Args:
        request: Source governed request.
        receipt: Persisted unknown-outcome receipt.
        deps: Injected action dependencies.
    """
    resolution = resolve_unknown_outcome(
        receipt,
        deps.store,
        lambda _route: deps.reconciliation_source(request),
    )
    if resolution.transition != "retry_locked":
        return
    event = build_broker_state_unknown_event(
        receipt,
        incident_id=resolution.incident_reference,
        unresolved_scope=resolution.remaining_unresolved_scope,
        occurred_at=deps.clock(),
        workflow_id=request.workflow_id,
    )
    emit_runtime_event(event, deps.event_sink)


def _passed_readiness(request: TradingRequest) -> ReadinessAssessment:
    """Construct passed readiness after direct sim validation.

    Args:
        request: Fully validated Simulation request.

    Returns:
        Explicit passed readiness evidence.
    """
    logger.debug("Recording direct Simulation readiness")
    return ReadinessAssessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"request_id": request.request_id, "route": request.route},
        assessed_at=request.system_time,
    )


def _intent_from_gate(
    request: TradingRequest,
    gate: StandardTradingEnvelope,
) -> OrderIntent | None:
    """Read canonical intent evidence from a successful live gate.

    Args:
        request: Source governed request.
        gate: Gate result envelope.

    Returns:
        Executable intent, or ``None`` when no dispatch is authorized.

    Raises:
        TradingError: If successful dispatch evidence is malformed.
    """
    logger.debug("Reading executable intent from live gate evidence")
    data = gate.data
    if not isinstance(data, dict) or data.get("dispatch_allowed") is not True:
        return None
    intent = data.get("intent")
    if not isinstance(intent, dict):
        raise TradingError("MALFORMED_RECEIPT", "Live gate omitted order intent")
    parsed = OrderIntent.model_validate(intent)
    if parsed.request_id != request.request_id:
        raise TradingError("SCOPE_MISMATCH", "Live gate intent mismatches request")
    return parsed


async def _execute_request(
    request: TradingRequest,
    deps: TradingDependencies,
    evidence: Mapping[str, JsonValue] | None = None,
) -> StandardTradingEnvelope:
    """Validate, gate, dispatch, and persist one canonical request.

    Args:
        request: Canonical Risk-approved request.
        deps: Explicit action dependencies.
        evidence: Optional JSON-safe live readiness facts.

    Returns:
        Package-only, duplicate, or authority-result envelope.

    Raises:
        TradingError: If validation, gating, authority, or persistence fails.
    """
    logger.info("Executing Trading request %s", request.request_id)
    account_state = deps.account_state_source(request)
    if request.symbol is None:
        raise TradingError("INVALID_REQUEST", "Order symbol is required")
    capability, _symbol_info = deps.symbol_capability_source(
        request.route, request.provider_id, request.symbol
    )
    validate_order_request(request, account_state, capability)
    _require_clear_authority_scope(request, deps)
    intent: OrderIntent | None
    if request.route.value in {"paper", "live"}:
        if deps.live_session is None:
            raise TradingError("SERVICE_UNAVAILABLE", "Live session is absent")
        gate = await evaluate_live_gate(request, evidence or {}, deps.live_session)
        intent = _intent_from_gate(request, gate)
        if intent is None:
            return gate
    else:
        now = deps.clock()
        validate_action_policy(request, deps.action_policy_source(request), now)
        validate_risk_authority(
            request, deps.execution_risk_decision_source(request), now
        )
        validate_kill_switch_hierarchy(
            request,
            deps.kill_switch_state_source(request),
            deps.max_staleness_seconds["kill_switch"],
            now,
        )
        reservation = reserve_idempotency(
            request,
            deps.store,
            reservation_time=deps.clock(),
            retention_seconds=deps.idempotency_retention_seconds,
            concurrency_lock_timeout_seconds=(deps.concurrency_lock_timeout_seconds),
        )
        if reservation.status == "duplicate_completed":
            data = _redacted_envelope_data({"receipt_id": reservation.receipt_id})
            return StandardTradingEnvelope(
                status="success",
                message="Completed idempotent request requires no dispatch",
                data=data,
                errors=(),
                warnings=(),
                audit_metadata={
                    "operation": request.action,
                    "request_id": request.request_id,
                    "redaction_applied": True,
                },
            )
        if reservation.status != "new":
            raise TradingError(
                "TRADING_CONCURRENCY_CONFLICT", "Request is already unresolved"
            )
        intent = build_execution_plan(request, _passed_readiness(request))
    attempt_event_id = _record_send_attempt(request, intent, deps)
    receipt = await dispatch_order_intent(
        intent,
        deps.connection,
        deps.broker_adapter,
        deps.simulation_dispatch,
        operation_timeout_seconds=deps.broker_operation_timeout_seconds,
        clock=deps.clock,
    )
    _record_receipt(request, receipt, attempt_event_id, deps)
    _complete_reservation(request, receipt, deps)
    if receipt.reconciliation_required:
        _resolve_unknown(request, receipt, deps)
    return _envelope(request, receipt)


def _require_order_target_state(
    request: TradingRequest, deps: TradingDependencies
) -> None:
    """Prove order target identity and version from Trading-owned state.

    Args:
        request: Canonical order mutation request.
        deps: Explicit action dependencies.

    Raises:
        TradingError: If projection, target identity, or optimistic version differs.
    """
    logger.debug("Validating broker order target against Trading state")
    projection = deps.store.load_projection(
        (request.route, request.account_id, authority_id(request))
    )
    if projection is None:
        raise TradingError("RECONCILIATION_REQUIRED", "Trading order state is absent")
    if request.expected_version != projection.version:
        raise TradingError("VERSION_CONFLICT", "Order projection version is stale")
    targets = {
        target
        for identity, facts in projection.orders.items()
        for target in (
            facts.get("broker_order_id", identity) if isinstance(facts, dict) else None,
        )
        if isinstance(target, str)
    }
    if request.target_broker_order_id not in targets:
        raise TradingError(
            "RECONCILIATION_REQUIRED", "Broker order target is not in Trading state"
        )


async def submit_order(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Submit one validated Risk-approved order.

    Args:
        request: Canonical submit request.
        deps: Explicit action dependencies.

    Returns:
        Route-authority outcome.
    """
    logger.info("Submitting governed Trading order")
    require_action(request, "submit_order")
    return await _execute_request(request, deps)


async def modify_order(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Modify one order within approved identity and version scope.

    Args:
        request: Canonical modify request.
        deps: Explicit action dependencies.

    Returns:
        Route-authority outcome.

    Raises:
        TradingError: If version or target evidence is absent.
    """
    logger.info("Modifying governed Trading order")
    require_action(request, "modify_order")
    if request.expected_version is None or request.target_broker_order_id is None:
        raise TradingError("VERSION_CONFLICT", "Modify requires version and target")
    _require_order_target_state(request, deps)
    return await _execute_request(request, deps)


async def cancel_order(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Cancel one pending order after ordinary gates.

    Args:
        request: Canonical cancellation request.
        deps: Explicit action dependencies.

    Returns:
        Route-authority outcome.

    Raises:
        TradingError: If target identity is absent.
    """
    logger.info("Cancelling governed Trading order")
    require_action(request, "cancel_order")
    if request.target_broker_order_id is None:
        raise TradingError("INVALID_REQUEST", "Cancellation requires target order")
    _require_order_target_state(request, deps)
    return await _execute_request(request, deps)


__all__ = ["cancel_order", "modify_order", "submit_order"]
