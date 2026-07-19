"""Unit tests for deterministic reduce-only Portfolio planning."""

# ruff: noqa: INP001

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioRebalancePlan,
)
from app.services.portfolio.rebalancing import RebalancingService
from app.services.risk import (
    AllocationRiskDecision,
    DecisionState,
    KillSwitchState,
    StrategyOperationalEligibilityDecision,
)
from app.utils import logger


class RecordingPlanRepository:
    """Record immutable plans saved by the rebalancing service."""

    def __init__(self) -> None:
        """Initialize without a recorded plan."""
        logger.debug("Initializing recording Portfolio plan repository")
        self.plan: PortfolioRebalancePlan | None = None

    def save_plan(
        self,
        plan: PortfolioRebalancePlan,
        audit_record: object,
    ) -> PortfolioRebalancePlan:
        """Record and return one immutable plan.

        Args:
            plan: Complete immutable plan.
            audit_record: Redacted audit record.

        Returns:
            Supplied plan.
        """
        logger.debug("Recording Portfolio rebalance plan")
        del audit_record
        self.plan = plan
        return plan


def _risk_decision(
    allocation: ActivePortfolioAllocation,
    now: datetime,
) -> AllocationRiskDecision:
    """Build an active Risk target decision for drift tests.

    Args:
        allocation: Active allocation under assessment.
        now: Stable UTC time.

    Returns:
        Active authoritative Risk decision.
    """
    logger.debug("Building active Risk budget decision for Portfolio drift")
    return AllocationRiskDecision(
        decision_id=allocation.risk_decision_id,
        portfolio_id=allocation.portfolio_id,
        reviewed_version=allocation.allocation_version,
        state=DecisionState.APPROVE,
        capped_weights={
            "component-a": Decimal("0.5"),
            "component-b": Decimal("0.5"),
        },
        risk_budget_projection={
            "component-a": Decimal("0.5"),
            "component-b": Decimal("0.5"),
        },
        conditions=(),
        policy_version="risk-policy-1",
        evidence_refs={"allocation": allocation.canonical_hash},
        issued_at=now,
        expires_at=now + timedelta(hours=1),
        active=True,
        predecessor_version=None,
        audit_ref="risk-audit-1",
    )


def _eligibility(now: datetime) -> dict[str, StrategyOperationalEligibilityDecision]:
    """Build current approving eligibility by component.

    Args:
        now: Stable UTC time.

    Returns:
        Component-keyed current Risk eligibility.
    """
    logger.debug("Building current Portfolio rebalance eligibility")
    return {
        f"component-{suffix}": StrategyOperationalEligibilityDecision.model_construct(
            decision_id=f"eligibility-{suffix}",
            state=DecisionState.APPROVE,
            suspended=False,
            expires_at=now + timedelta(hours=1),
        )
        for suffix in ("a", "b")
    }


def _kill_switch(now: datetime, state: str = "inactive") -> KillSwitchState:
    """Build a canonical global Risk kill-switch state.

    Args:
        now: Stable UTC time.
        state: Canonical kill-switch state.

    Returns:
        Canonical kill-switch evidence.
    """
    logger.debug("Building Portfolio rebalance kill-switch evidence")
    return KillSwitchState.model_construct(
        state_id="kill-switch-1",
        scope_level="global",
        scope={},
        state=state,
        reason="test",
        version=1,
        updated_at=now,
    )


def _assess(
    service: RebalancingService,
    allocation: ActivePortfolioAllocation,
    now: datetime,
    exposures: dict[str, Decimal],
    *,
    evidence_as_of: datetime | None = None,
    kill_switch_state: str = "inactive",
) -> PortfolioRebalancePlan:
    """Assess drift with complete explicit owner evidence.

    Args:
        service: Rebalancing service under test.
        allocation: Active allocation under assessment.
        now: Stable UTC time.
        exposures: Actual component Risk-budget exposures.
        evidence_as_of: Optional explicit observation time.
        kill_switch_state: Canonical Risk kill-switch state.

    Returns:
        Persisted immutable plan.
    """
    logger.debug("Assessing Portfolio drift in test helper")
    return service.assess(
        allocation,
        actual_exposures=exposures,
        evidence_as_of=evidence_as_of or now,
        risk_decision=_risk_decision(allocation, now),
        eligibility_decisions=_eligibility(now),
        kill_switches=(_kill_switch(now, kill_switch_state),),
        now=now,
        request_id="req-rebalance-1",
        workflow_id="wf-rebalance-1",
        correlation_id="corr-rebalance-1",
        audit_record={"event_type": "portfolio.rebalance_assessed"},
    )


def test_over_budget_drift_creates_reduce_only_actions(
    active_allocation: ActivePortfolioAllocation,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Verify over-budget exposure produces only deterministic reductions.

    Args:
        active_allocation: Current active allocation.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
    """
    logger.info("Testing reduce-only Portfolio rebalance planning")
    plan = _assess(
        RebalancingService(
            portfolio_settings,
            RecordingPlanRepository(),  # type: ignore[arg-type]
        ),
        active_allocation,
        portfolio_now,
        {"component-a": Decimal("0.6"), "component-b": Decimal("0.4")},
    )

    assert plan.status == "review_required"
    assert len(plan.actions) == 1
    assert plan.actions[0].component_id == "component-a"
    assert plan.actions[0].reduce_only is True
    assert plan.actions[0].reduction_amount == Decimal("0.1")


def test_under_budget_drift_never_opens_exposure(
    active_allocation: ActivePortfolioAllocation,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Verify target matching never creates an opening action.

    Args:
        active_allocation: Current active allocation.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
    """
    logger.info("Testing Portfolio never opens solely to match target")
    plan = _assess(
        RebalancingService(
            portfolio_settings,
            RecordingPlanRepository(),  # type: ignore[arg-type]
        ),
        active_allocation,
        portfolio_now,
        {"component-a": Decimal("0.4"), "component-b": Decimal("0.5")},
    )

    assert plan.status == "blocked"
    assert plan.actions == ()
    assert plan.block_reasons == ("RISK_INCREASE_UNSUPPORTED",)


@pytest.mark.parametrize("blocked_gate", ["stale", "kill_switch", "expired"])
def test_planning_blocks_stale_kill_switch_and_expired_allocation(
    blocked_gate: str,
    active_allocation: ActivePortfolioAllocation,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Verify mutable planning gates block unsafe plans.

    Args:
        blocked_gate: Gate to invalidate.
        active_allocation: Current active allocation.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
    """
    logger.info("Testing Portfolio rebalance fail-closed gates")
    allocation = active_allocation
    evidence_at = portfolio_now
    switch = "inactive"
    if blocked_gate == "stale":
        evidence_at -= timedelta(hours=2)
    elif blocked_gate == "kill_switch":
        switch = "active"
    else:
        allocation = active_allocation.model_copy(update={"expires_at": portfolio_now})
    plan = _assess(
        RebalancingService(
            portfolio_settings,
            RecordingPlanRepository(),  # type: ignore[arg-type]
        ),
        allocation,
        portfolio_now,
        {"component-a": Decimal("0.5"), "component-b": Decimal("0.5")},
        evidence_as_of=evidence_at,
        kill_switch_state=switch,
    )

    assert plan.status == "blocked"
    assert plan.actions == ()
