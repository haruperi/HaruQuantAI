"""Unit tests for the fail-closed Trading budget gate."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

import pytest
from app.services.risk.contracts import (
    AllocationRiskDecision,
    DecisionState,
    PortfolioBudgetExecutionVerdict,
)
from app.services.trading.contracts import (
    PortfolioRebalanceExecutionRequest,
    TradingError,
    TradingRoute,
)
from app.services.trading.monitoring import BudgetGate
from app.utils import canonical_json, logger

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _request() -> PortfolioRebalanceExecutionRequest:
    """Build a canonical rebalance request.

    Returns:
        Valid plan-bound execution request.
    """
    logger.debug("Building budget-gate rebalance request")
    data: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "trading.portfolio_rebalance_execution_request.v1",
        "request_id": "request-001",
        "workflow_id": "workflow-001",
        "correlation_id": "correlation-001",
        "plan_id": "plan-001",
        "plan_version": "v1",
        "portfolio_id": "portfolio-001",
        "allocation_version": "allocation-v1",
        "allocation_decision_id": "allocation-decision-001",
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
        "route": TradingRoute.SIM,
        "approval_token_ref": "approval-001",
        "canonical_material_version": "v1",
        "valid_from": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }
    data["canonical_hash"] = sha256(canonical_json(data).encode()).hexdigest()
    return PortfolioRebalanceExecutionRequest.model_validate(data)


def _allocation() -> AllocationRiskDecision:
    """Build current active allocation authority.

    Returns:
        Active Risk allocation decision.
    """
    logger.debug("Building budget-gate allocation decision")
    return AllocationRiskDecision(
        decision_id="allocation-decision-001",
        portfolio_id="portfolio-001",
        reviewed_version="allocation-v1",
        state=DecisionState.APPROVE,
        capped_weights={"strategy-001": Decimal("0.5")},
        risk_budget_projection={"strategy-001": Decimal(5000)},
        conditions=(),
        policy_version="policy-v1",
        evidence_refs={"snapshot": "snapshot-001"},
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        active=True,
        predecessor_version=None,
        audit_ref="audit-001",
    )


def _verdict(
    request: PortfolioRebalanceExecutionRequest,
) -> PortfolioBudgetExecutionVerdict:
    """Build current Risk execution-time budget authority.

    Args:
        request: Exact request to bind.

    Returns:
        Allowed plan-bound budget verdict.
    """
    logger.debug("Building budget-gate execution verdict")
    return PortfolioBudgetExecutionVerdict(
        verdict_id="budget-verdict-001",
        allocation_decision_id="allocation-decision-001",
        portfolio_id=request.portfolio_id,
        allocation_version=request.allocation_version,
        plan_id=request.plan_id,
        plan_hash=request.canonical_hash,
        budget_unit="USD",
        allowed=True,
        reasons=(),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
    )


def test_budget_gate_requires_exact_plan_binding() -> None:
    """Reject a budget verdict bound to a different plan hash."""
    logger.debug("Testing exact budget-gate plan binding")
    request = _request()
    mismatched = _verdict(request).model_copy(update={"plan_hash": "b" * 64})
    with pytest.raises(TradingError, match="BUDGET_BLOCKED"):
        BudgetGate.validate(request, _allocation(), mismatched, now=NOW)


def test_budget_gate_accepts_current_risk_authority() -> None:
    """Accept exact active allocation and execution-time budget authority."""
    logger.debug("Testing current budget authority acceptance")
    request = _request()
    BudgetGate.validate(request, _allocation(), _verdict(request), now=NOW)
