"""Negative workflow integration for governed portfolio rebalance execution."""

# ruff: noqa: PLR0915
from dataclasses import replace
from datetime import timedelta

import pytest
from app.services.risk import get_decision_state
from app.services.trading import (
    create_portfolio_rebalance_execution_request,
    execute_portfolio_rebalance,
    validate_budget_authority,
)
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
    missing_result = await execute_portfolio_rebalance(item, missing)
    assert missing_result.status == "error"
    assert missing_result.error is not None
    assert missing_result.error.code == "PERMISSION_DENIED"

    expired_data = rebalance_allocation().model_dump(mode="python")
    expired_data["expires_at"] = NOW - timedelta(seconds=1)
    expired = type(rebalance_allocation()).model_validate(expired_data)
    expired_deps = replace(
        rebalance_dependencies(item),
        allocation_decision_source=lambda _request: expired,
        simulation_dispatch=counted_dispatch,
    )
    expired_result = await execute_portfolio_rebalance(item, expired_deps)
    assert expired_result.status == "error"
    assert expired_result.error is not None
    assert expired_result.error.code == "BUDGET_BLOCKED"

    rejected_data = rebalance_allocation().model_dump(mode="python")
    rejected_data["state"] = get_decision_state("REJECT")
    rejected_data["active"] = False
    rejected = type(rebalance_allocation()).model_validate(rejected_data)
    rejected_deps = replace(
        rebalance_dependencies(item),
        allocation_decision_source=lambda _request: rejected,
        simulation_dispatch=counted_dispatch,
    )
    rejected_result = await execute_portfolio_rebalance(item, rejected_deps)
    assert rejected_result.status == "error"
    assert rejected_result.error is not None
    assert rejected_result.error.code == "BUDGET_BLOCKED"
    assert dispatch_calls == 0
    assert missing.broker_adapter is None

    budget_data = rebalance_budget(item).model_dump(mode="python")
    budget_data.update({"plan_id": "wrong-plan", "plan_hash": "b" * 64})
    mismatched_budget = type(rebalance_budget(item)).model_validate(budget_data)
    budget_result = validate_budget_authority(
        item,
        rebalance_allocation(),
        mismatched_budget,
        now=NOW,
    )
    assert budget_result.status == "error"
    assert budget_result.error is not None
    assert budget_result.error.code == "BUDGET_BLOCKED"

    open_data = rebalance_data()
    open_action = dict(open_data["actions"][0])
    open_action.update({"action": "submit_order", "reduce_only": False})
    open_data["actions"] = (open_action,)
    with pytest.raises(ValidationError, match="reduce-only"):
        create_portfolio_rebalance_execution_request(**open_data)
    assert {action["action"] for action in item.actions} == {"reduce_exposure"}

    tampered = item.model_dump(mode="python")
    tampered["canonical_hash"] = "0" * 64
    with pytest.raises(ValidationError, match="canonical_hash"):
        create_portfolio_rebalance_execution_request(**tampered)
    assert canonical_json(item.model_dump(mode="json"))
