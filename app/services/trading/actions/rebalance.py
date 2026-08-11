"""Authorized portfolio rebalance execution through ordinary Trading actions."""

# ruff: noqa: BLE001 - public boundaries normalize every failure.

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, cast

from app.services.risk import get_decision_state
from app.services.trading.actions._shared import response_data_json
from app.services.trading.actions.positions import reduce_exposure
from app.services.trading.contracts import (
    PortfolioRebalanceExecutionRequest,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.contracts.responses import success_trading_response
from app.services.trading.monitoring.budgets import validate_budget_authority
from app.services.trading.validation.authority import validate_kill_switch_hierarchy
from app.utils import get_logger

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

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
        decision.state is not get_decision_state("APPROVE")
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
        or child.causation_id is not None
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


async def _execute_portfolio_rebalance_value(
    request: PortfolioRebalanceExecutionRequest,
    deps: TradingDependencies,
) -> StandardResponse[dict[str, JsonValue]]:
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
    budget_response = validate_budget_authority(request, allocation, budget, now=now)
    if budget_response.status == "error":
        raise TradingError("BUDGET_BLOCKED", "Rebalance budget authority is blocked")
    _validate_eligibility(request, deps, now)
    outcomes: list[dict[str, JsonValue]] = []
    for raw_action in request.actions:
        action = dict(raw_action)
        action_id = str(action["action_id"])
        try:
            child = deps.rebalance_action_resolver(request, action)
            _validate_resolved_action(request, action, child)
            validate_kill_switch_hierarchy(
                child,
                deps.kill_switch_state_source(child),
                deps.max_staleness_seconds["kill_switch"],
                deps.clock(),
            )
            outcome = await reduce_exposure(child, deps)
            child_status = outcome.metadata.extensions.get("legacy_status")
            if not isinstance(child_status, str):
                child_status = outcome.status
            outcomes.append(
                {
                    "action_id": child.request_id,
                    "status": child_status,
                    "data": response_data_json(outcome.data),
                }
            )
            if outcome.metadata.extensions.get("legacy_status") == "unknown_outcome":
                break
        except TradingError as error:
            outcomes.append(
                {
                    "action_id": action_id,
                    "status": "error",
                    "error_code": error.trading_code,
                }
            )
            break
    completed_ids = {item["action_id"] for item in outcomes}
    outcomes.extend(
        {
            "action_id": str(action["action_id"]),
            "status": "skipped",
            "reason": "prior_action_not_completed",
        }
        for action in request.actions
        if action["action_id"] not in completed_ids
    )
    partial = any(
        item["status"] in {"partial", "unknown_outcome", "rejected", "error", "skipped"}
        for item in outcomes
    )
    data = _redacted_envelope_data(
        {"plan_id": request.plan_id, "outcomes": cast("JsonValue", outcomes)}
    )
    return success_trading_response(
        data,
        operation="trading.execute_portfolio_rebalance",
        message="Authorized rebalance actions executed through ordinary Trading gates",
        risk_level="critical",
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        read_only=False,
        modifies_database=True,
        places_trade=True,
        requires_network=request.route.value in {"paper", "live"},
        legacy_status="partial" if partial else "success",
        extensions={"redaction_applied": True},
    )


async def execute_portfolio_rebalance(
    request: PortfolioRebalanceExecutionRequest,
    deps: TradingDependencies,
) -> StandardResponse[dict[str, JsonValue]]:
    """Execute a portfolio rebalance and return a standard response.

    Args:
        request: Receiver-owned rebalance execution request.
        deps: Active trading runtime dependencies.

    Returns:
        Standard response containing ordered child results or an error.
    """
    try:
        return await _execute_portfolio_rebalance_value(request, deps)
    except Exception as error:
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(error, {"request_id": request.request_id})


__all__ = ["execute_portfolio_rebalance"]
