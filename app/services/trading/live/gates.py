"""Canonical fail-fast live/paper Trading mutation gate sequence."""

from collections.abc import Mapping

from app.services.trading.contracts import (
    StandardTradingEnvelope,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.contracts.models import (
    JsonValue,  # noqa: TC001 - runtime annotation and model resolution
)
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
from app.utils import logger


def _gate_envelope(
    request: TradingRequest,
    *,
    status: str,
    message: str,
    data: Mapping[str, JsonValue],
) -> StandardTradingEnvelope:
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
    return StandardTradingEnvelope(
        status=status,  # type: ignore[arg-type]
        message=message,
        data=redacted_data,
        errors=(),
        warnings=(),
        audit_metadata={
            "operation": "evaluate_live_gate",
            "request_id": request.request_id,
            "correlation_id": request.correlation_id,
            "route": request.route,
            "provider_id": request.provider_id,
            "redaction_applied": True,
        },
    )


async def evaluate_live_gate(
    request: TradingRequest,
    evidence: Mapping[str, JsonValue],
    session: LiveSession,
) -> StandardTradingEnvelope:
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
    if request.contract_version != "v1" or request.schema_id != (
        "trading.trading_request.v1"
    ):
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
    policy = validate_action_policy(request, session.action_policy_for(request), now)
    decision = validate_risk_authority(request, session.risk_decision_for(request), now)
    validate_kill_switch_hierarchy(
        request,
        session.kill_switches_for(request),
        session.config.max_staleness_seconds["kill_switch"],
        now,
    )
    readiness = session.readiness_for(request, evidence)
    if not readiness.passed:
        raise TradingError(
            "GATE_BLOCKED",
            "Execution readiness failed",
            trace_context={"failed_checks": list(readiness.failed_check_codes)},
        )
    reservation = reserve_idempotency(
        request,
        session.store,
        reservation_time=now,
        retention_seconds=session.config.idempotency_retention_seconds,
        concurrency_lock_timeout_seconds=(
            session.config.concurrency_lock_timeout_seconds
        ),
    )
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
        session.write_pre_audit(
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
    except Exception as error:
        raise TradingError("AUDIT_FAILED", "Pre-mutation audit write failed") from error
    intent = build_execution_plan(request, readiness)
    validate_adapter_capability(
        intent,
        session.adapter_capability_for(request),
        operation_timeout_seconds=session.config.broker_operation_timeout_seconds,
    )
    return _gate_envelope(
        request,
        status="success",
        message="Every mandatory live gate passed",
        data={
            "dispatch_allowed": True,
            "intent": intent.model_dump(mode="json"),
        },
    )


__all__ = ["evaluate_live_gate"]
