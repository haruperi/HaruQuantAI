"""Canonical fail-fast live/paper Trading mutation gate sequence."""

from collections.abc import Mapping
from typing import Any, Literal

from app.services.trading.contracts import (
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.contracts.models import (
    JsonValue,  # noqa: TC001 - runtime annotation and model resolution
)
from app.services.trading.contracts.responses import success_trading_response
from app.services.trading.live.session import (
    LiveSession,  # noqa: TC001 - runtime annotation and model resolution
)
from app.services.trading.routing import validate_adapter_capability
from app.services.trading.state import reserve_idempotency
from app.services.trading.validation import build_execution_plan
from app.services.trading.validation.authority import (
    validate_action_policy,
    validate_kill_switch_hierarchy,
    validate_risk_authority,
)
from app.utils import get_logger

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)


def _gate_envelope(
    request: TradingRequest,
    *,
    status: str,
    message: str,
    data: Mapping[str, JsonValue],
) -> StandardResponse[Mapping[str, JsonValue]]:
    """Build one canonical live-gate result envelope.

    Args:
        request: Governed Trading request.
        status: Canonical result status.
        message: Bounded result summary.
        data: JSON-safe gate evidence.

    Returns:
        Canonical Trading envelope.
    """
    logger.debug("Building live-gate envelope for request %s", request.request_id)
    redacted_data = _redacted_envelope_data(data)
    return success_trading_response(
        redacted_data,
        operation="trading.evaluate_live_gate",
        message=message,
        risk_level="critical",
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        read_only=False,
        modifies_database=True,
        places_trade=True,
        requires_network=request.route.value in {"paper", "live"},
        legacy_status=status,
        extensions={
            "route": request.route.value,
            "provider_id": request.provider_id,
            "redaction_applied": True,
        },
    )


async def _evaluate_live_gate_value(  # noqa: C901, PLR0912
    request: TradingRequest,
    evidence: Mapping[str, JsonValue],
    session: LiveSession,
) -> StandardResponse[Mapping[str, JsonValue]]:
    """Run the mandatory fail-fast gate sequence before route mutation.

    Args:
        request: Canonical immutable governed request.
        evidence: JSON-safe readiness facts/references only.
        session: Stateful owner of typed authority sources and side-effect ports.

    Returns:
        Package-only, duplicate, or dispatch-authorized gate evidence.

    Raises:
        TradingError: At the first mandatory gate failure.
    """
    logger.info("Evaluating canonical live gate for %s", request.request_id)
    compatible_schemas = {
        ("v1", "trading.trading_request.v1"),
        ("v2", "trading.trading_request.v2"),
    }
    if (request.contract_version, request.schema_id) not in compatible_schemas:
        raise TradingError("INVALID_REQUEST", "Trading request schema is incompatible")
    now = session.now()
    if not session.started or request.valid_until <= now:
        raise TradingError("GATE_BLOCKED", "Session or request validity is inactive")
    if not session.admission_enabled:
        return _gate_envelope(
            request,
            status="packaged",
            message="Live mutation is disabled; request remains packaged",
            data={"dispatch_allowed": False, "gate": "enablement"},
        )
    policy_response = session.action_policy_for(request)
    decision_response = session.risk_decision_for(request)
    switches_response = session.kill_switches_for(request)
    readiness_response = session.readiness_for(request, evidence)
    capability_response = session.adapter_capability_for(request)
    for response in (
        policy_response,
        decision_response,
        switches_response,
        readiness_response,
        capability_response,
    ):
        if response.status == "error":
            raise TradingError("GATE_BLOCKED", "Live gate authority read failed")
    if policy_response.data is None or decision_response.data is None:
        raise TradingError("GATE_BLOCKED", "Risk gate authority is absent")
    if switches_response.data is None or readiness_response.data is None:
        raise TradingError("GATE_BLOCKED", "Live gate state is absent")
    if capability_response.data is None:
        raise TradingError("ADAPTER_INCOMPATIBLE", "Adapter capability is absent")
    policy = validate_action_policy(request, policy_response.data, now)
    decision = validate_risk_authority(request, decision_response.data, now)
    validate_kill_switch_hierarchy(
        request,
        switches_response.data,
        session.config.max_staleness_seconds["kill_switch"],
        now,
    )
    readiness = readiness_response.data
    if not readiness.passed:
        raise TradingError(
            "GATE_BLOCKED",
            "Execution readiness failed",
            trace_context={"failed_checks": list(readiness.failed_check_codes)},
        )
    reservation_response = reserve_idempotency(
        request,
        session.store,
        reservation_time=now,
        retention_seconds=session.config.idempotency_retention_seconds,
        concurrency_lock_timeout_seconds=(
            session.config.concurrency_lock_timeout_seconds
        ),
    )
    if reservation_response.status == "error" or reservation_response.data is None:
        raise TradingError(
            "TRADING_CONCURRENCY_CONFLICT",
            "Idempotency reservation failed",
        )
    reservation = reservation_response.data
    if reservation.status in {
        "duplicate_active",
        "conflict",
        "reconciliation_required",
    }:
        raise TradingError(
            "TRADING_CONCURRENCY_CONFLICT",
            "Request scope is already active or unresolved",
        )
    if reservation.status == "duplicate_completed":
        return _gate_envelope(
            request,
            status="success",
            message="Completed idempotent request requires no dispatch",
            data={
                "dispatch_allowed": False,
                "receipt_id": reservation.receipt_id,
            },
        )
    if not session.reconciliation_ready:
        raise TradingError(
            "RECONCILIATION_REQUIRED",
            "Reconciliation authority is not ready",
        )
    try:
        audit_response = session.write_pre_audit(
            request,
            _redacted_envelope_data(
                {
                    "request_id": request.request_id,
                    "workflow_id": request.workflow_id,
                    "correlation_id": request.correlation_id,
                    "risk_decision_id": decision.decision_id,
                    "action_policy_verdict_id": policy.verdict_id,
                    "redaction_applied": True,
                }
            ),
        )
        if audit_response.status == "error":
            raise TradingError(  # noqa: TRY301
                "AUDIT_FAILED", "Pre-mutation audit write failed"
            )
    except Exception as error:
        raise TradingError("AUDIT_FAILED", "Pre-mutation audit write failed") from error
    plan_response = build_execution_plan(request, readiness)
    if plan_response.status == "error" or plan_response.data is None:
        raise TradingError("GATE_BLOCKED", "Execution plan could not be built")
    intent = plan_response.data
    capability_validation = validate_adapter_capability(
        intent,
        capability_response.data,
        operation_timeout_seconds=session.config.broker_operation_timeout_seconds,
    )
    if capability_validation.status == "error":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Adapter capability is unsafe")
    return _gate_envelope(
        request,
        status="success",
        message="Every mandatory live gate passed",
        data={
            "dispatch_allowed": True,
            "intent": intent.model_dump(mode="json"),
        },
    )


async def evaluate_live_gate(
    request: TradingRequest,
    evidence: Mapping[str, JsonValue],
    session: LiveSession,
) -> StandardResponse[Mapping[str, JsonValue]]:
    """Run live gates and return a standard response.

    Args:
        request: Governed trading request envelope.
        evidence: Route fact and environment evidence mapping.
        session: Active live session instance.

    Returns:
        Standard response containing gate evidence or a canonical error.
    """
    try:
        return await _evaluate_live_gate_value(request, evidence, session)
    except TradingError as error:
        logger.exception("LIVE GATE ERROR DETAILS: %s", error.details)
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(
            error,
            {
                "operation": "trading.evaluate_live_gate",
                "request_id": request.request_id,
                "correlation_id": request.correlation_id,
                "route": request.route.value,
            },
        )


__all__ = ["evaluate_live_gate"]
