"""Unit tests for authorized Trading portfolio rebalance execution."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256

import pytest
from app.services.risk import (
    create_allocation_risk_decision,
    create_portfolio_budget_execution_verdict,
    create_strategy_operational_eligibility_decision,
    get_decision_state,
)
from app.services.trading.actions import execute_portfolio_rebalance
from app.services.trading.contracts import (
    PortfolioRebalanceExecutionRequest,
    TradingError,
)
from app.services.trading.state import (
    TradingProjection,
    create_execution_position,
    create_execution_position_store,
    set_execution_position,
)
from app.utils import canonical_json
from pydantic import ValidationError

from tests.trading.unit.actions.test_dependencies import (
    NOW,
    MemoryStore,
    dependencies,
)

# Private type-only aliases; Risk exposes functions, not contract classes.
AllocationRiskDecision = object
PortfolioBudgetExecutionVerdict = object
StrategyOperationalEligibilityDecision = object


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


def rebalance_data() -> dict[str, object]:
    """Build complete canonical reduce-only rebalance material."""
    data: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "trading.portfolio_rebalance_execution_request.v1",
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "plan_id": "plan-001",
        "plan_version": "v1",
        "portfolio_id": "portfolio-001",
        "allocation_version": "allocation-v1",
        "allocation_decision_id": "allocation-001",
        "eligibility_decision_ids": ("eligibility-001",),
        "actions": (
            {
                "action_id": "req-44444444-4444-4444-8444-444444444444",
                "component_id": "strategy-001",
                "eligibility_decision_id": "eligibility-001",
                "action": "reduce_exposure",
                "reduce_only": True,
                "current_exposure": "0.60",
                "target_exposure": "0.50",
                "reduction_amount": "0.10",
            },
        ),
        "route": "sim",
        "approval_token_ref": "token-001",
        "canonical_material_version": "v1",
        "valid_from": NOW - timedelta(minutes=1),
        "valid_until": NOW + timedelta(minutes=5),
    }
    data["canonical_hash"] = sha256(canonical_json(data).encode()).hexdigest()
    return data


def rebalance_request() -> PortfolioRebalanceExecutionRequest:
    """Return the validated receiver-owned rebalance request."""
    return PortfolioRebalanceExecutionRequest.model_validate(rebalance_data())


def allocation() -> AllocationRiskDecision:
    """Build current active Risk allocation authority."""
    return create_allocation_risk_decision(
        decision_id="allocation-001",
        portfolio_id="portfolio-001",
        reviewed_version="allocation-v1",
        state=get_decision_state("APPROVE"),
        capped_weights={"strategy-001": Decimal("0.5")},
        risk_budget_projection={"strategy-001": Decimal(5000)},
        conditions=(),
        policy_version="policy-v1",
        evidence_refs={"snapshot": "snapshot-001"},
        issued_at=NOW - timedelta(minutes=2),
        expires_at=NOW + timedelta(minutes=5),
        active=True,
        predecessor_version=None,
        audit_ref="audit-allocation-001",
    )


def budget(item: PortfolioRebalanceExecutionRequest) -> PortfolioBudgetExecutionVerdict:
    """Build exact plan-bound Risk execution budget authority."""
    return create_portfolio_budget_execution_verdict(
        verdict_id="budget-001",
        allocation_decision_id=item.allocation_decision_id,
        portfolio_id=item.portfolio_id,
        allocation_version=item.allocation_version,
        plan_id=item.plan_id,
        plan_hash=item.canonical_hash,
        budget_unit="USD",
        allowed=True,
        reasons=(),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        request_id=item.request_id,
        workflow_id=item.workflow_id,
        correlation_id=item.correlation_id,
    )


def eligibility() -> StrategyOperationalEligibilityDecision:
    """Build current approved strategy eligibility authority."""
    return create_strategy_operational_eligibility_decision(
        decision_id="eligibility-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        scope={"portfolio_id": "portfolio-001"},
        state=get_decision_state("APPROVE"),
        conditions=(),
        policy_version="policy-v1",
        evidence_refs={"review": "review-001"},
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        suspended=False,
        audit_ref="audit-eligibility-001",
    )


def rebalance_dependencies(item: PortfolioRebalanceExecutionRequest):
    """Build dependencies containing current state and exact Risk authorities."""
    store = MemoryStore()
    store.projection = TradingProjection(
        route="sim",
        tenant_id="account-001",
        authority_id="simulation",
        version=1,
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )
    store.execution_positions = create_execution_position_store()
    set_execution_position(
        store.execution_positions,
        create_execution_position(
            position_id="position-001",
            account_id="account-001",
            symbol="EURUSD",
            broker_position_id="position-001",
            state="OPEN",
            quantity=Decimal("2.00"),
            average_entry_price=Decimal("1.10"),
            source_sequence=1,
            version=1,
        ),
    )
    return replace(
        dependencies(store=store),
        allocation_decision_source=lambda value: allocation(),
        budget_verdict_source=lambda value: budget(item),
        eligibility_source=lambda value: (eligibility(),),
    )


def test_rebalance_cannot_open_to_match_weight() -> None:
    """The receiver-owned contract rejects weight-seeking open actions."""
    data = rebalance_data()
    action = dict(data["actions"][0])
    action["action"] = "submit_order"
    action["reduce_only"] = False
    data["actions"] = (action,)
    data["canonical_hash"] = sha256(canonical_json(data).encode()).hexdigest()
    with pytest.raises(ValidationError, match="reduce-only"):
        PortfolioRebalanceExecutionRequest.model_validate(data)


@pytest.mark.anyio
async def test_rebalance_executes_complete_approved_reduction() -> None:
    """An exact authorized plan uses the ordinary reduction path."""
    item = rebalance_request()
    outcome = await execute_portfolio_rebalance(item, rebalance_dependencies(item))
    assert outcome.status == "success"
    assert (
        outcome.data["outcomes"][0]["action_id"]
        == "req-44444444-4444-4444-8444-444444444444"
    )


@pytest.mark.anyio
async def test_rebalance_preserves_prior_outcomes_and_marks_remaining_skipped() -> None:
    """A later child failure retains earlier truth and identifies unattempted work."""
    data = rebalance_data()
    first = dict(data["actions"][0])
    second = {
        **first,
        "action_id": "req-55555555-5555-4555-8555-555555555555",
    }
    third = {
        **first,
        "action_id": "req-66666666-6666-4666-8666-666666666666",
    }
    data["actions"] = (first, second, third)
    del data["canonical_hash"]
    data["canonical_hash"] = sha256(canonical_json(data).encode()).hexdigest()
    item = PortfolioRebalanceExecutionRequest.model_validate(data)
    deps = rebalance_dependencies(item)
    resolver = deps.rebalance_action_resolver

    def fail_second(parent, action):
        """Fail the second child before dispatch while leaving later work untouched."""
        if action["action_id"] == second["action_id"]:
            raise TradingError("SCOPE_MISMATCH", "Injected child resolution failure")
        return resolver(parent, action)

    outcome = await execute_portfolio_rebalance(
        item,
        replace(deps, rebalance_action_resolver=fail_second),
    )

    assert outcome.status == "success"
    assert outcome.metadata.extensions["legacy_status"] == "partial"
    assert [entry["status"] for entry in outcome.data["outcomes"]] == [
        "sent",
        "error",
        "skipped",
    ]
