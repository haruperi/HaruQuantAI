"""Canonical fail-fast live/paper Trading mutation gate sequence."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal

from app.services.risk.contracts import (
    ActionPolicyVerdict,
    DecisionState,
    KillSwitchState,
    RiskDecisionPackage,
)
from app.services.trading.contracts import (
    StandardTradingEnvelope,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.contracts.models import JsonValue
from app.services.trading.live.session import LiveSession
from app.services.trading.routing import validate_adapter_capability
from app.services.trading.state import reserve_idempotency
from app.services.trading.validation import build_execution_plan
from app.utils import logger


def _validate_policy(
    request: TradingRequest,
    verdict: ActionPolicyVerdict | None,
    now: datetime,
) -> ActionPolicyVerdict:
    """Validate exact current Risk action-policy authority.

    Args:
        request: Governed Trading request.
        verdict: Current Risk-owned action-policy verdict.
        now: Current injected time.

    Returns:
        Exact valid verdict.

    Raises:
        TradingError: If verdict identity, scope, state, or lifetime fails.
    """
    logger.debug("Running Trading action-policy gate")
    valid = verdict is not None and (
        verdict.verdict_id == request.action_policy_verdict_id
        and verdict.action == request.action
        and verdict.decision_id == request.risk_decision_id
        and verdict.request_id == request.request_id
        and verdict.workflow_id == request.workflow_id
        and verdict.correlation_id == request.correlation_id
        and verdict.scope.get("account_id") == request.account_id
        and verdict.allowed
        and verdict.issued_at <= now < verdict.expires_at
    )
    if not valid or verdict is None:
        raise TradingError("GATE_BLOCKED", "Action-policy authority is invalid")
    optional_scope = {
        "portfolio_id": request.portfolio_id,
        "strategy_id": request.strategy_id,
        "symbol": request.symbol,
    }
    if any(
        key in verdict.scope and verdict.scope[key] != value
        for key, value in optional_scope.items()
    ):
        raise TradingError("SCOPE_MISMATCH", "Action-policy scope is mismatched")
    return verdict


def _validate_risk(
    request: TradingRequest,
    decision: RiskDecisionPackage | None,
    now: datetime,
) -> RiskDecisionPackage:
    """Validate exact current Risk approval and token binding.

    Args:
        request: Governed Trading request.
        decision: Current Risk-owned decision package.
        now: Current injected time.

    Returns:
        Exact valid Risk decision.

    Raises:
        TradingError: If decision, size, token, or lifetime fails.
    """
    logger.debug("Running Trading Risk-decision gate")
    if decision is None or decision.token is None:
        raise TradingError("GATE_BLOCKED", "Real Risk approval is required")
    token = decision.token
    valid = (
        decision.decision_id == request.risk_decision_id
        and decision.intent_id == request.intent_id
        and decision.state is DecisionState.APPROVE
        and decision.approved_size == request.quantity
        and decision.issued_at <= now < decision.expires_at
        and token.token_id == request.approval_token_ref
        and token.decision_id == decision.decision_id
        and token.action == request.action
        and token.request_id == request.request_id
        and token.workflow_id == request.workflow_id
        and token.correlation_id == request.correlation_id
        and token.issued_at <= now < token.expires_at
    )
    if not valid:
        raise TradingError("GATE_BLOCKED", "Risk approval is invalid or stale")
    return decision


def _validate_kill_switches(
    states: Sequence[KillSwitchState],
    max_staleness_seconds: Decimal,
    now: datetime,
) -> None:
    """Fail closed on active, unknown, absent, or stale kill-switch evidence.

    Args:
        states: Every applicable Risk-owned scope state.
        max_staleness_seconds: Exact positive kill-switch evidence age bound.
        now: Current injected time.

    Raises:
        TradingError: If hierarchy evidence is absent, active, unknown, or stale.
    """
    logger.debug("Running Trading kill-switch hierarchy gate")
    if not states or any(state.state == "unknown" for state in states):
        raise TradingError("KILL_SWITCH_UNKNOWN", "Kill-switch state is unproven")
    if any(state.state == "active" for state in states):
        raise TradingError("KILL_SWITCH_ACTIVE", "Kill-switch hierarchy is active")
    if any(
        Decimal(str((now - state.updated_at).total_seconds())) > max_staleness_seconds
        for state in states
    ):
        raise TradingError(
            "KILL_SWITCH_STALE",
            "Kill-switch hierarchy evidence is stale and cannot prove clearance",
        )


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
    policy = _validate_policy(request, session.action_policy_for(request), now)
    decision = _validate_risk(request, session.risk_decision_for(request), now)
    _validate_kill_switches(
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
            _redacted_envelope_data(
                {
                    "request_id": request.request_id,
                    "workflow_id": request.workflow_id,
                    "correlation_id": request.correlation_id,
                    "risk_decision_id": decision.decision_id,
                    "action_policy_verdict_id": policy.verdict_id,
                    "redaction_applied": True,
                }
            )
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
