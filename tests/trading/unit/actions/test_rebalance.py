"""Unit tests for authorized Trading portfolio rebalance execution."""

# ruff: noqa: ARG005, INP001

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256

import pytest
from app.services.risk.contracts import (
    AllocationRiskDecision,
    DecisionState,
    PortfolioBudgetExecutionVerdict,
    StrategyOperationalEligibilityDecision,
)
from app.services.trading.actions import execute_portfolio_rebalance
from app.services.trading.contracts import PortfolioRebalanceExecutionRequest
from app.services.trading.state import TradingProjection
from app.utils import canonical_json
from pydantic import ValidationError
from tests.trading.unit.actions.test_dependencies import (
    NOW,
    MemoryStore,
    dependencies,
)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


def rebalance_data() -> dict[str, object]:
    """Build complete canonical reduce-only rebalance material."""
    data: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "trading.portfolio_rebalance_execution_request.v1",
        "request_id": "rebalance-request-001",
        "workflow_id": "workflow-001",
        "correlation_id": "correlation-001",
        "plan_id": "plan-001",
        "plan_version": "v1",
        "portfolio_id": "portfolio-001",
        "allocation_version": "allocation-v1",
        "allocation_decision_id": "allocation-001",
        "eligibility_decision_ids": ("eligibility-001",),
        "actions": (
            {
                "action_id": "action-001",
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
    return AllocationRiskDecision(
        decision_id="allocation-001",
        portfolio_id="portfolio-001",
        reviewed_version="allocation-v1",
        state=DecisionState.APPROVE,
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
    return PortfolioBudgetExecutionVerdict(
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
    return StrategyOperationalEligibilityDecision(
        decision_id="eligibility-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        scope={"portfolio_id": "portfolio-001"},
        state=DecisionState.APPROVE,
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
        positions={
            "position-001": {
                "symbol": "EURUSD",
                "broker_position_id": "position-001",
            }
        },
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
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
    assert outcome.data["outcomes"][0]["action_id"] == "action-001"
