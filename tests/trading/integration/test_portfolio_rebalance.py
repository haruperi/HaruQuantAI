"""Negative workflow integration for governed portfolio rebalance execution."""

# ruff: noqa: INP001

from dataclasses import replace
from datetime import timedelta

import pytest
from app.services.risk.contracts import DecisionState
from app.services.trading.actions import execute_portfolio_rebalance
from app.services.trading.contracts import (
    PortfolioRebalanceExecutionRequest,
    TradingError,
)
from app.services.trading.monitoring import BudgetGate
from app.utils import canonical_json
from pydantic import ValidationError
from tests.trading.conftest import (
    NOW,
    rebalance_allocation,
    rebalance_budget,
    rebalance_data,
    rebalance_dependencies,
    rebalance_request,
)


@pytest.mark.anyio
async def test_rebalance_cannot_bypass_risk_or_open_to_match_weight() -> None:
    """Reject absent Risk, mismatched budget, opening actions, and tampering."""
    item = rebalance_request()
    dispatch_calls = 0

    async def counted_dispatch(intent):
        """Count any forbidden Simulation dispatch attempt."""
        nonlocal dispatch_calls
        dispatch_calls += 1
        raise AssertionError(intent.client_order_id)

    missing = replace(
        rebalance_dependencies(item),
        allocation_decision_source=lambda _request: None,
        simulation_dispatch=counted_dispatch,
    )
    with pytest.raises(TradingError, match="PERMISSION_DENIED"):
        await execute_portfolio_rebalance(item, missing)

    expired_data = rebalance_allocation().model_dump(mode="python")
    expired_data["expires_at"] = NOW - timedelta(seconds=1)
    expired = type(rebalance_allocation()).model_validate(expired_data)
    expired_deps = replace(
        rebalance_dependencies(item),
        allocation_decision_source=lambda _request: expired,
        simulation_dispatch=counted_dispatch,
    )
    with pytest.raises(TradingError, match="BUDGET_BLOCKED"):
        await execute_portfolio_rebalance(item, expired_deps)

    rejected_data = rebalance_allocation().model_dump(mode="python")
    rejected_data["state"] = DecisionState.REJECT
    rejected_data["active"] = False
    rejected = type(rebalance_allocation()).model_validate(rejected_data)
    rejected_deps = replace(
        rebalance_dependencies(item),
        allocation_decision_source=lambda _request: rejected,
        simulation_dispatch=counted_dispatch,
    )
    with pytest.raises(TradingError, match="BUDGET_BLOCKED"):
        await execute_portfolio_rebalance(item, rejected_deps)
    assert dispatch_calls == 0
    assert missing.broker_adapter is None

    budget_data = rebalance_budget(item).model_dump(mode="python")
    budget_data.update({"plan_id": "wrong-plan", "plan_hash": "b" * 64})
    mismatched_budget = type(rebalance_budget(item)).model_validate(budget_data)
    with pytest.raises(TradingError, match="BUDGET_BLOCKED"):
        BudgetGate.validate(
            item,
            rebalance_allocation(),
            mismatched_budget,
            now=NOW,
        )

    open_data = rebalance_data()
    open_action = dict(open_data["actions"][0])
    open_action.update({"action": "submit_order", "reduce_only": False})
    open_data["actions"] = (open_action,)
    with pytest.raises(ValidationError, match="reduce-only"):
        PortfolioRebalanceExecutionRequest.model_validate(open_data)
    assert {action["action"] for action in item.actions} == {"reduce_exposure"}

    tampered = item.model_dump(mode="python")
    tampered["canonical_hash"] = "0" * 64
    with pytest.raises(ValidationError, match="canonical_hash"):
        PortfolioRebalanceExecutionRequest.model_validate(tampered)
    assert canonical_json(item.model_dump(mode="json"))
