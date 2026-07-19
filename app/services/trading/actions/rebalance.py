"""Authorized portfolio rebalance execution through ordinary Trading actions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from app.services.risk.contracts import DecisionState
from app.services.trading.actions.positions import reduce_exposure
from app.services.trading.contracts import (
    PortfolioRebalanceExecutionRequest,
    StandardTradingEnvelope,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.monitoring import BudgetGate
from app.utils import logger

if TYPE_CHECKING:
    from app.services.trading.actions.dependencies import TradingDependencies
    from app.services.trading.contracts.models import JsonValue
    from app.services.trading.state import TradingProjection


def _text(action: dict[str, JsonValue], field: str) -> str:
    """Read one contract-validated rebalance text field.

    Args:
        action: Complete canonical rebalance action.
        field: Required field name.

    Returns:
        Exact text value.

    Raises:
        TradingError: If runtime material is unexpectedly malformed.
    """
    logger.debug("Reading rebalance text field %s", field)
    value = action.get(field)
    if not isinstance(value, str):
        raise TradingError("INVALID_REQUEST", "Rebalance action text is malformed")
    return value


def _decimal(action: dict[str, JsonValue], field: str) -> Decimal | None:
    """Read one contract-validated rebalance Decimal field.

    Args:
        action: Complete canonical rebalance action.
        field: Optional Decimal field name.

    Returns:
        Exact Decimal or ``None``.
    """
    logger.debug("Reading rebalance Decimal field %s", field)
    value = action.get(field)
    return None if value is None else Decimal(str(value))


def _provider_id(
    request: PortfolioRebalanceExecutionRequest, deps: TradingDependencies
) -> str | None:
    """Resolve provider identity only from injected Broker connection material.

    Args:
        request: Authorized rebalance request.
        deps: Explicit action dependencies.

    Returns:
        Broker provider identity or ``None`` for Simulation.

    Raises:
        TradingError: If a Broker route lacks connection material.
    """
    logger.debug("Resolving rebalance provider from injected connection")
    if request.route.value == "sim":
        return None
    if deps.connection is None:
        raise TradingError("SERVICE_UNAVAILABLE", "Broker connection is absent")
    return deps.connection.broker_id.value


def _position_target(
    projection: TradingProjection | None, symbol: str
) -> tuple[str, int]:
    """Read one broker position identity from Trading-owned state.

    Args:
        projection: Current Trading execution projection.
        symbol: Exact canonical symbol.

    Returns:
        Broker position identity and current projection version.

    Raises:
        TradingError: If state cannot select exactly one position.
    """
    logger.debug("Reading rebalance target position from Trading state")
    if projection is None:
        raise TradingError("RECONCILIATION_REQUIRED", "Trading state is absent")
    matches: list[str] = []
    for identity, facts in projection.positions.items():
        if isinstance(facts, dict) and facts.get("symbol") == symbol:
            target = facts.get("broker_position_id", identity)
            if isinstance(target, str):
                matches.append(target)
    if len(matches) != 1:
        raise TradingError(
            "RECONCILIATION_REQUIRED", "Trading state cannot identify one position"
        )
    return matches[0], projection.version


def _validate_eligibility(
    request: PortfolioRebalanceExecutionRequest,
    deps: TradingDependencies,
    now: datetime,
) -> None:
    """Require every referenced current Risk eligibility decision.

    Args:
        request: Authorized rebalance request.
        deps: Explicit action dependencies.
        now: Current injected time.

    Raises:
        TradingError: If eligibility authority is incomplete or blocking.
    """
    logger.debug("Validating rebalance strategy eligibility authority")
    decisions = deps.eligibility_source(request)
    by_id = {decision.decision_id: decision for decision in decisions}
    if set(by_id) != set(request.eligibility_decision_ids):
        raise TradingError("PERMISSION_DENIED", "Eligibility references mismatch")
    if any(
        decision.state is not DecisionState.APPROVE
        or decision.suspended
        or decision.expires_at <= now
        for decision in decisions
    ):
        raise TradingError("PERMISSION_DENIED", "Strategy eligibility blocks plan")


def _action_request(
    parent: PortfolioRebalanceExecutionRequest,
    action: dict[str, JsonValue],
    deps: TradingDependencies,
    provider_id: str | None,
) -> TradingRequest:
    """Adapt one complete approved reduction into a canonical Trading request.

    Args:
        parent: Authorized immutable plan request.
        action: Complete canonical reduce-only action.
        deps: Explicit action dependencies.
        provider_id: Provider selected from injected connection material.

    Returns:
        Ordinary Risk-approved reduce-exposure request.
    """
    logger.debug("Adapting approved rebalance reduction into Trading request")
    symbol = _text(action, "symbol")
    capability, symbol_info = deps.symbol_capability_source(
        parent.route, provider_id, symbol
    )
    del capability
    authority = provider_id or "simulation"
    projection = deps.store.load_projection(
        (parent.route, _text(action, "account_id"), authority)
    )
    position_id, version = _position_target(projection, symbol)
    expiration_value = action.get("expiration")
    expiration = (
        datetime.fromisoformat(expiration_value)
        if isinstance(expiration_value, str)
        else None
    )
    return TradingRequest(
        request_id=_text(action, "action_id"),
        workflow_id=parent.workflow_id,
        correlation_id=parent.correlation_id,
        causation_id=parent.request_id,
        route=parent.route,
        action="reduce_exposure",
        provider_id=provider_id,
        account_id=_text(action, "account_id"),
        portfolio_id=parent.portfolio_id,
        strategy_id=_text(action, "strategy_id"),
        strategy_version=_text(action, "strategy_version"),
        intent_id=_text(action, "source_intent_id"),
        symbol=symbol,
        side=_text(action, "side"),  # type: ignore[arg-type]
        order_type=_text(action, "order_type"),  # type: ignore[arg-type]
        quantity_unit=symbol_info.quantity_unit,
        quantity=_decimal(action, "approved_volume"),
        price=_decimal(action, "price"),
        stop_price=_decimal(action, "stop_price"),
        stop_loss=_decimal(action, "stop_loss"),
        take_profit=_decimal(action, "take_profit"),
        time_in_force=action.get("time_in_force"),  # type: ignore[arg-type]
        expiration=expiration,
        target_broker_position_id=position_id,
        position_id=position_id,
        expected_version=version,
        risk_decision_id=_text(action, "risk_decision_id"),
        action_policy_verdict_id=_text(action, "action_policy_verdict_id"),
        approval_token_ref=parent.approval_token_ref,
        eligibility_decision_id=_text(action, "eligibility_decision_id"),
        allocation_decision_id=parent.allocation_decision_id,
        idempotency_key=f"{parent.plan_id}:{_text(action, 'action_id')}",
        canonical_material_version=parent.canonical_material_version,
        system_time=deps.clock(),
        valid_until=parent.valid_until,
        instrument_min_quantity=symbol_info.min_quantity,
        instrument_max_quantity=symbol_info.max_quantity,
        instrument_quantity_step=symbol_info.quantity_step,
        instrument_price_tick=symbol_info.price_step,
    )


async def execute_portfolio_rebalance(
    request: PortfolioRebalanceExecutionRequest,
    deps: TradingDependencies,
) -> StandardTradingEnvelope:
    """Execute an authorized immutable reduce-only rebalance plan.

    Args:
        request: Receiver-owned complete rebalance request.
        deps: Explicit action dependencies.

    Returns:
        Ordered child outcomes with partial completion retained.

    Raises:
        TradingError: If authorization, version, budget, eligibility, state, or
            gates fail before child execution.
    """
    logger.info("Executing authorized Trading portfolio rebalance")
    now = deps.clock()
    if not request.valid_from <= now < request.valid_until:
        raise TradingError("STALE_EVIDENCE", "Rebalance validity is inactive")
    allocation = deps.allocation_decision_source(request)
    budget = deps.budget_verdict_source(request)
    if allocation is None or budget is None:
        raise TradingError("PERMISSION_DENIED", "Rebalance budget authority is absent")
    BudgetGate.validate(request, allocation, budget, now=now)
    _validate_eligibility(request, deps, now)
    provider_id = _provider_id(request, deps)
    outcomes: list[dict[str, JsonValue]] = []
    for raw_action in request.actions:
        action = dict(raw_action)
        child = _action_request(request, action, deps, provider_id)
        if any(
            state.state != "inactive" for state in deps.kill_switch_state_source(child)
        ):
            raise TradingError("KILL_SWITCH_ACTIVE", "Kill switch blocks rebalance")
        outcome = await reduce_exposure(child, deps)
        outcomes.append(
            {
                "action_id": child.request_id,
                "status": outcome.status,
                "data": outcome.data,
            }
        )
    partial = any(
        item["status"] in {"partial", "unknown_outcome", "rejected"}
        for item in outcomes
    )
    data = _redacted_envelope_data(
        {"plan_id": request.plan_id, "outcomes": cast("JsonValue", outcomes)}
    )
    return StandardTradingEnvelope(
        status="partial" if partial else "success",
        message="Authorized rebalance actions executed through ordinary Trading gates",
        data=data,
        errors=(),
        warnings=({"code": "PARTIAL_COMPLETION"},) if partial else (),
        audit_metadata={
            "operation": "execute_portfolio_rebalance",
            "request_id": request.request_id,
            "correlation_id": request.correlation_id,
            "redaction_applied": True,
        },
    )


__all__ = ["execute_portfolio_rebalance"]
