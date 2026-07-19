"""Trading runtime controls and Risk-owned kill-switch transition verbs."""

from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING

from app.services.risk.contracts import ActionPolicyVerdict, KillSwitchCommand
from app.services.trading.actions._shared import authority_id, require_action
from app.services.trading.contracts import (
    StandardTradingEnvelope,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.reconciliation import compare_authority_state
from app.services.trading.state import (
    TradingEvent,
    TradingProjection,
    apply_execution_event,
)
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.trading.actions.dependencies import TradingDependencies
    from app.services.trading.contracts.models import JsonValue


def _policy(request: TradingRequest, deps: TradingDependencies) -> ActionPolicyVerdict:
    """Return a current exact action-policy verdict.

    Args:
        request: Canonical control request.
        deps: Explicit action dependencies.

    Returns:
        Current compatible Risk verdict.

    Raises:
        TradingError: If policy authority is absent, stale, denied, or mismatched.
    """
    logger.debug("Validating Risk action policy for Trading control")
    verdict = deps.action_policy_source(request)
    if (
        verdict is None
        or not verdict.allowed
        or verdict.verdict_id != request.action_policy_verdict_id
        or verdict.action != request.action
        or verdict.expires_at <= deps.clock()
    ):
        raise TradingError("PERMISSION_DENIED", "Compatible action policy is absent")
    return verdict


def _record_control(
    request: TradingRequest,
    deps: TradingDependencies,
    facts: dict[str, JsonValue],
) -> TradingProjection:
    """Persist one local control or synchronization transition.

    Args:
        request: Canonical control request.
        deps: Explicit action dependencies.
        facts: Redacted transition facts.

    Returns:
        Updated Trading projection.
    """
    logger.info("Recording Trading control transition %s", request.action)
    authority = authority_id(request)
    current = deps.store.load_projection((request.route, request.account_id, authority))
    version = 0 if current is None else current.version
    digest = sha256(
        canonical_json(
            {
                "request_id": request.request_id,
                "action": request.action,
                "version": version,
            }
        ).encode("utf-8")
    ).hexdigest()
    event = TradingEvent(
        event_id=digest,
        event_type="reconciliation_transitioned",
        aggregate_version=version,
        route=request.route,
        tenant_id=request.account_id,
        authority_id=authority,
        occurred_at=deps.clock(),
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        causation_id=request.causation_id,
        payload=_redacted_envelope_data(facts),
    )
    return apply_execution_event(event, deps.store)


def _control_envelope(
    request: TradingRequest,
    data: dict[str, JsonValue],
) -> StandardTradingEnvelope:
    """Package a successful control result.

    Args:
        request: Source control request.
        data: Redacted control evidence.

    Returns:
        Standard successful Trading envelope.
    """
    logger.debug("Packaging Trading control result")
    redacted_data = _redacted_envelope_data(data)
    return StandardTradingEnvelope(
        status="success",
        message="Trading control transition completed",
        data=redacted_data,
        errors=(),
        warnings=(),
        audit_metadata={
            "operation": request.action,
            "request_id": request.request_id,
            "correlation_id": request.correlation_id,
            "redaction_applied": True,
        },
    )


async def pause_strategy(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Pause Trading admission without changing Strategy lifecycle state.

    Args:
        request: Canonical pause request.
        deps: Explicit action dependencies.

    Returns:
        Persisted pause evidence.
    """
    logger.info("Pausing Trading strategy admission")
    require_action(request, "pause_strategy")
    _policy(request, deps)
    projection = _record_control(
        request,
        deps,
        {"admission": "paused", "strategy_id": request.strategy_id},
    )
    return _control_envelope(request, {"projection_version": projection.version})


async def resume_strategy(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Resume Trading admission after policy, switch, and readiness checks.

    Args:
        request: Canonical resume request.
        deps: Explicit action dependencies.

    Returns:
        Persisted resume evidence.

    Raises:
        TradingError: If hierarchy or reconciliation remains blocking.
    """
    logger.info("Resuming Trading strategy admission")
    require_action(request, "resume_strategy")
    _policy(request, deps)
    if any(
        state.state != "inactive" for state in deps.kill_switch_state_source(request)
    ):
        raise TradingError("KILL_SWITCH_ACTIVE", "Kill-switch hierarchy blocks resume")
    snapshot = deps.reconciliation_source(request)
    current = deps.store.load_projection(
        (request.route, request.account_id, authority_id(request))
    )
    if current is None or compare_authority_state(snapshot, current).unresolved:
        raise TradingError("RECONCILIATION_REQUIRED", "Route state is not reconciled")
    projection = _record_control(
        request,
        deps,
        {"admission": "enabled", "strategy_id": request.strategy_id},
    )
    return _control_envelope(request, {"projection_version": projection.version})


async def sync_positions(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Synchronize Trading projections from read-only route truth.

    Args:
        request: Canonical synchronization request.
        deps: Explicit action dependencies.

    Returns:
        Persisted reconciliation evidence.
    """
    logger.info("Synchronizing Trading positions from route truth")
    require_action(request, "sync_positions")
    snapshot = deps.reconciliation_source(request)
    current = deps.store.load_projection(
        (request.route, request.account_id, authority_id(request))
    )
    unresolved = (
        True
        if current is None
        else compare_authority_state(snapshot, current).unresolved
    )
    projection = _record_control(
        request,
        deps,
        {
            "source_id": snapshot.source_id,
            "authority_observed_at": snapshot.observed_at.isoformat(),
            "readiness": {"reconciled": not unresolved},
        },
    )
    return _control_envelope(
        request,
        {"projection_version": projection.version, "unresolved": unresolved},
    )


def _kill_switch_command(request: TradingRequest, action: str) -> KillSwitchCommand:
    """Build a Risk-owned kill-switch command from explicit control fields.

    Args:
        request: Canonical control request.
        action: Risk transition action.

    Returns:
        Typed Risk command.

    Raises:
        TradingError: If explicit scope or reason is absent.
    """
    logger.debug("Building typed Risk kill-switch command")
    if request.scope_level is None or request.control_reason is None:
        raise TradingError("INVALID_REQUEST", "Switch scope and reason are required")
    return KillSwitchCommand(
        action=action,  # type: ignore[arg-type]
        scope_level=request.scope_level,
        portfolio_id=request.portfolio_id,
        strategy_id=request.strategy_id,
        symbol=request.symbol,
        reason=request.control_reason,
        requested_at=request.system_time,
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
    )


async def trigger_kill_switch(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Request one scoped Risk-owned kill-switch activation.

    Args:
        request: Canonical activation request.
        deps: Explicit action dependencies.

    Returns:
        Risk transition evidence.
    """
    logger.warning("Requesting Risk kill-switch activation")
    require_action(request, "trigger_kill_switch")
    state = await deps.kill_switch_transition(
        _kill_switch_command(request, "activate"), _policy(request, deps)
    )
    return _control_envelope(request, {"kill_switch": state.model_dump(mode="json")})


async def clear_kill_switch(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Request Risk-authorized clearance without overriding active parents.

    Args:
        request: Canonical clearance request.
        deps: Explicit action dependencies.

    Returns:
        Risk transition evidence.

    Raises:
        TradingError: If an applicable parent scope remains active.
    """
    logger.warning("Requesting Risk kill-switch clearance")
    require_action(request, "clear_kill_switch")
    levels = {"global": 0, "portfolio": 1, "strategy": 2, "symbol": 3}
    if request.scope_level is None:
        raise TradingError("INVALID_REQUEST", "Switch scope is required")
    target_level = levels[request.scope_level]
    states = deps.kill_switch_state_source(request)
    if any(
        levels[state.scope_level] < target_level and state.state != "inactive"
        for state in states
    ):
        raise TradingError("KILL_SWITCH_ACTIVE", "Active parent blocks clearance")
    state = await deps.kill_switch_transition(
        _kill_switch_command(request, "clear"), _policy(request, deps)
    )
    return _control_envelope(request, {"kill_switch": state.model_dump(mode="json")})


__all__ = [
    "clear_kill_switch",
    "pause_strategy",
    "resume_strategy",
    "sync_positions",
    "trigger_kill_switch",
]
