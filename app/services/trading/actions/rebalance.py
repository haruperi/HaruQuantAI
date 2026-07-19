"""Authorized portfolio rebalance execution through ordinary Trading actions."""

from __future__ import annotations

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
    from datetime import datetime

    from app.services.trading.actions.dependencies import TradingDependencies
    from app.services.trading.contracts.models import JsonValue


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


def _validate_resolved_action(
    parent: PortfolioRebalanceExecutionRequest,
    action: dict[str, JsonValue],
    child: TradingRequest,
) -> None:
    """Validate one Trading-owned resolved order against its Portfolio parent.

    Args:
        parent: Authorized immutable plan request.
        action: Complete canonical reduce-only action.
        child: Trading-owned fully governed reduction request.

    Raises:
        TradingError: If the resolved order breaks parent bindings or safety.
    """
    logger.debug("Validating Trading-owned resolved rebalance action")
    if (
        child.request_id != action["action_id"]
        or child.workflow_id != parent.workflow_id
        or child.correlation_id != parent.correlation_id
        or child.causation_id != parent.request_id
        or child.route is not parent.route
        or child.portfolio_id != parent.portfolio_id
        or child.action != "reduce_exposure"
        or child.allocation_decision_id != parent.allocation_decision_id
        or child.eligibility_decision_id != action["eligibility_decision_id"]
        or child.idempotency_key != f"{parent.plan_id}:{action['action_id']}"
        or child.target_broker_position_id is None
        or child.quantity is None
        or child.quantity <= 0
    ):
        raise TradingError(
            "INVALID_REQUEST",
            "Resolved rebalance action conflicts with its parent plan",
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
    outcomes: list[dict[str, JsonValue]] = []
    for raw_action in request.actions:
        action = dict(raw_action)
        child = deps.rebalance_action_resolver(request, action)
        _validate_resolved_action(request, action, child)
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
