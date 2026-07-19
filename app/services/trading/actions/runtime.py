"""Thin live/paper evaluation-cycle orchestration through public domain APIs."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from hashlib import sha256
from typing import TYPE_CHECKING

from pydantic import ValidationError as PydanticValidationError

from app.services.risk.contracts import DecisionState
from app.services.trading.actions.orders import _execute_request
from app.services.trading.contracts import (
    StandardTradingEnvelope,
    TradingError,
    TradingRequest,
    TradingRoute,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.monitoring import OperationalEvent, emit_runtime_event
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.risk.contracts import RiskDecisionPackage
    from app.services.strategy import TradeIntent
    from app.services.trading.actions.dependencies import TradingDependencies
    from app.services.trading.contracts.models import JsonValue

_ACTION_BY_INTENT = {
    "OPEN": "submit_order",
    "INCREASE": "submit_order",
    "CLOSE": "close_position",
    "REDUCE": "reduce_exposure",
    "MODIFY": "modify_position",
    "CANCEL": "cancel_order",
}


def _required_text(evidence: Mapping[str, JsonValue], field: str) -> str:
    """Read one required immutable orchestration reference.

    Args:
        evidence: JSON-safe workflow facts and references.
        field: Required evidence key.

    Returns:
        Exact trimmed text.

    Raises:
        TradingError: If evidence is absent or malformed.
    """
    logger.debug("Reading runtime evidence reference %s", field)
    value = evidence.get(field)
    if not isinstance(value, str) or not value or value != value.strip():
        raise TradingError("INVALID_REQUEST", f"Runtime evidence requires {field}")
    return value


def _route(deps: TradingDependencies) -> TradingRoute:
    """Read the selected route from the configured live session.

    Args:
        deps: Explicit action dependencies.

    Returns:
        Paper or live route.

    Raises:
        TradingError: If the lifecycle dependency is absent.
    """
    logger.debug("Reading evaluation route from LiveSession")
    if deps.live_session is None:
        raise TradingError("SERVICE_UNAVAILABLE", "Live session is absent")
    return TradingRoute(deps.live_session.config.execution_route)


def _provider_id(deps: TradingDependencies) -> str:
    """Read provider identity from injected Broker connection material.

    Args:
        deps: Explicit action dependencies.

    Returns:
        Exact Broker provider identifier.

    Raises:
        TradingError: If connection material is absent.
    """
    logger.debug("Reading evaluation provider from Broker connection")
    if deps.connection is None:
        raise TradingError("SERVICE_UNAVAILABLE", "Broker connection is absent")
    return deps.connection.broker_id.value


def _state_target(
    request: TradingRequest,
    deps: TradingDependencies,
    intent: TradeIntent,
) -> tuple[str | None, str | None, int | None]:
    """Read modify/cancel/close target identifiers from Trading state.

    Args:
        request: Partially addressed canonical request.
        deps: Explicit action dependencies.
        intent: Immutable Strategy proposal.

    Returns:
        Order target, position target, and projection version.

    Raises:
        TradingError: If exactly one required state target cannot be proven.
    """
    logger.debug("Resolving evaluation target identifiers from Trading state")
    projection = deps.store.load_projection(
        (request.route, request.account_id, request.provider_id or "simulation")
    )
    if intent.intent_type in {"OPEN", "INCREASE"}:
        return None, None, None
    if projection is None:
        raise TradingError("RECONCILIATION_REQUIRED", "Trading projection is absent")
    if intent.intent_type == "CANCEL":
        matches = [
            identity
            for identity, facts in projection.orders.items()
            if isinstance(facts, dict) and facts.get("symbol") == intent.symbol
        ]
        if len(matches) != 1:
            raise TradingError("RECONCILIATION_REQUIRED", "Order target is ambiguous")
        facts = projection.orders[matches[0]]
        target = (
            facts.get("broker_order_id", matches[0])
            if isinstance(facts, dict)
            else matches[0]
        )
        if not isinstance(target, str):
            raise TradingError("RECONCILIATION_REQUIRED", "Order target is malformed")
        return target, None, projection.version
    matches = [
        identity
        for identity, facts in projection.positions.items()
        if isinstance(facts, dict) and facts.get("symbol") == intent.symbol
    ]
    if len(matches) != 1:
        raise TradingError("RECONCILIATION_REQUIRED", "Position target is ambiguous")
    facts = projection.positions[matches[0]]
    target = (
        facts.get("broker_position_id", matches[0])
        if isinstance(facts, dict)
        else matches[0]
    )
    if not isinstance(target, str):
        raise TradingError("RECONCILIATION_REQUIRED", "Position target is malformed")
    return None, target, projection.version


def _approved_request(
    intent: TradeIntent,
    decision: RiskDecisionPackage,
    deps: TradingDependencies,
    evidence: Mapping[str, JsonValue],
) -> TradingRequest:
    """Build one canonical request from immutable Strategy and Risk lineage.

    Args:
        intent: Strategy-owned proposal.
        decision: Risk-owned approval package.
        deps: Explicit action dependencies.
        evidence: Workflow references that carry no approval authority.

    Returns:
        Complete canonical Trading request.

    Raises:
        TradingError: If Risk approval or lineage is incomplete.
    """
    logger.debug("Building canonical request from Strategy/Risk lineage")
    now = deps.clock()
    if (
        decision.state is not DecisionState.APPROVE
        or decision.intent_id != intent.intent_id
        or decision.approved_size is None
        or decision.token is None
        or decision.expires_at <= now
    ):
        raise TradingError("PERMISSION_DENIED", "Risk did not approve TradeIntent")
    route = _route(deps)
    provider_id = _provider_id(deps)
    _, symbol_info = deps.symbol_capability_source(route, provider_id, intent.symbol)
    action = _ACTION_BY_INTENT[intent.intent_type]
    request = TradingRequest(
        request_id=decision.request_id,
        workflow_id=decision.workflow_id,
        correlation_id=decision.correlation_id,
        causation_id=intent.decision_id,
        route=route,
        action=action,  # type: ignore[arg-type]
        provider_id=provider_id,
        account_id=_required_text(evidence, "account_id"),
        portfolio_id=(
            str(evidence["portfolio_id"])
            if isinstance(evidence.get("portfolio_id"), str)
            else None
        ),
        strategy_id=intent.strategy_id,
        strategy_version=intent.strategy_version,
        intent_id=intent.intent_id,
        symbol=intent.symbol,
        side=intent.side,
        order_type=intent.order_type,
        quantity_unit=symbol_info.quantity_unit,
        quantity=decision.approved_size,
        price=intent.limit_price,
        stop_price=intent.stop_price,
        stop_loss=intent.stop_loss,
        take_profit=intent.take_profit,
        time_in_force=intent.time_in_force,
        expiration=intent.expiration,
        risk_decision_id=decision.decision_id,
        action_policy_verdict_id=_required_text(evidence, "action_policy_verdict_id"),
        approval_token_ref=decision.token.token_id,
        eligibility_decision_id=(
            str(evidence["eligibility_decision_id"])
            if isinstance(evidence.get("eligibility_decision_id"), str)
            else None
        ),
        idempotency_key=intent.idempotency_key,
        canonical_material_version=_required_text(
            evidence, "canonical_material_version"
        ),
        system_time=now,
        valid_until=min(decision.expires_at, decision.token.expires_at),
        instrument_min_quantity=symbol_info.min_quantity,
        instrument_max_quantity=symbol_info.max_quantity,
        instrument_quantity_step=symbol_info.quantity_step,
        instrument_price_tick=symbol_info.price_step,
    )
    order_target, position_target, version = _state_target(request, deps, intent)
    material = {
        **request.model_dump(mode="python"),
        "target_broker_order_id": order_target,
        "order_id": order_target,
        "target_broker_position_id": position_target,
        "position_id": position_target,
        "expected_version": version,
    }
    try:
        return TradingRequest.model_validate(material)
    except PydanticValidationError as error:
        raise TradingError(
            "INVALID_REQUEST", "Derived evaluation request is invalid"
        ) from error


def _check_timeout(
    deps: TradingDependencies,
    started_at: datetime,
    evidence: Mapping[str, JsonValue],
) -> None:
    """Emit timeout evidence and block before mutation when the cycle exceeds budget.

    Args:
        deps: Explicit action dependencies.
        started_at: Injected cycle start timestamp.
        evidence: Workflow trace references.

    Raises:
        TradingError: If elapsed time exceeds the configured exact bound.
    """
    logger.debug("Checking Trading evaluation workflow timeout")
    if deps.live_session is None:
        raise TradingError("SERVICE_UNAVAILABLE", "Live session is absent")
    now = deps.clock()
    elapsed = (now - started_at).total_seconds()
    if elapsed <= float(deps.live_session.config.live_workflow_timeout_seconds):
        return
    material = {"started_at": started_at, "observed_at": now}
    digest = sha256(canonical_json(material).encode("utf-8")).hexdigest()
    emit_runtime_event(
        OperationalEvent(
            event_id=f"trd-runtime-{digest}",
            event_type="WORKFLOW_TIMEOUT",
            severity="error",
            occurred_at=now,
            request_id=_required_text(evidence, "request_id"),
            workflow_id=_required_text(evidence, "workflow_id"),
            correlation_id=_required_text(evidence, "correlation_id"),
            facts={"elapsed_seconds": str(elapsed)},
            source_refs={"runtime": "actions.runtime"},
        ),
        deps.event_sink,
    )
    raise TradingError("WORKFLOW_TIMEOUT", "Evaluation cycle exceeded its bound")


async def run_live_evaluation_cycle(
    deps: TradingDependencies,
    evidence: Mapping[str, JsonValue],
) -> StandardTradingEnvelope:
    """Run one Data-to-Indicators-to-Strategy-to-Risk evaluation cycle.

    Args:
        deps: Exact typed public domain ports and execution dependencies.
        evidence: JSON-safe trigger facts and trace references.

    Returns:
        Normal no-action outcome or ordinary gated dispatch outcome.

    Raises:
        TradingError: If upstream evidence, approval, gate, or authority fails.
    """
    logger.info("Running one governed Trading live evaluation cycle")
    started_at = deps.clock()
    dataset = await deps.market_data_source(evidence)
    account = await deps.evaluation_account_source(evidence)
    indicators = await deps.indicator_source(dataset, evidence)
    intent = await deps.strategy_source(dataset, account, indicators, evidence)
    if intent is None:
        data = _redacted_envelope_data({"mutation_performed": False})
        return StandardTradingEnvelope(
            status="success",
            message="Strategy produced a neutral no-action outcome",
            data=data,
            errors=(),
            warnings=(),
            audit_metadata={
                "operation": "run_live_evaluation_cycle",
                "request_id": _required_text(evidence, "request_id"),
                "correlation_id": _required_text(evidence, "correlation_id"),
                "redaction_applied": True,
            },
        )
    decision = await deps.risk_source(intent, account, evidence)
    request = _approved_request(intent, decision, deps, evidence)
    _check_timeout(deps, started_at, evidence)
    return await _execute_request(request, deps, evidence)


__all__ = ["run_live_evaluation_cycle"]
