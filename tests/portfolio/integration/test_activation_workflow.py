"""Integration test for Simulation/Risk-reviewed Portfolio activation."""

# ruff: noqa: INP001

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import (
    PortfolioConstructionRequest,
    PortfolioConstructionResult,
)
from app.services.portfolio.evidence import validate_construction_evidence
from app.services.portfolio.orchestration import (
    ConstructionEvidenceInputs,
    PortfolioWorkflowDependencies,
    PortfolioWorkflowService,
)
from app.services.portfolio.state import PortfolioRepository
from app.services.simulator import PortfolioBacktestRequestV1
from app.utils import AuditEvent, logger
from tests.portfolio.unit.test_allocation import (
    _activator,
    _inactive_kill_switch,
    _risk_decision,
    _simulation,
)
from tests.portfolio.unit.test_evidence import (
    _owner_bundle,
    _patch_digest,
    _request_data_with_fx,
)
from tests.portfolio.unit.test_repository import FakePortfolioStore
from tests.portfolio.unit.test_workflows import _unused


def test_activation_chain_uses_receiver_owned_simulation_and_risk_contracts(
    construction_request_data: dict[str, Any],
    construction_result: PortfolioConstructionResult,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WF-PORT-003/004 revalidate and activate only after owner approvals."""
    logger.info("Testing complete Portfolio activation integration workflow")
    _patch_digest(monkeypatch)
    request_data = _request_data_with_fx(construction_request_data)
    request_data.update(
        {
            "request_id": "req-11111111-1111-4111-8111-111111111111",
            "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
            "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        }
    )
    request = PortfolioConstructionRequest(**request_data)
    candidate = PortfolioConstructionResult.model_validate(
        {
            **construction_result.model_dump(mode="python"),
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
        }
    )
    refs, decisions, account, market, analytics, fx = _owner_bundle(portfolio_now)
    evidence = validate_construction_evidence(
        request,
        strategy_refs=refs,
        eligibility_decisions=decisions,
        account_snapshot=account,
        market_dataset=market,
        analytics_evidence=analytics,
        fx_evidence=fx,
        component_volatilities={
            "component-a": Decimal("0.1"),
            "component-b": Decimal("0.2"),
        },
        component_observations={"component-a": 30, "component-b": 30},
        now=portfolio_now,
        settings=portfolio_settings,
    )
    simulation_request = PortfolioBacktestRequestV1.model_construct(
        request_id=candidate.request_id,
        workflow_id=candidate.workflow_id,
        correlation_id=candidate.correlation_id,
        portfolio_id=candidate.portfolio_id,
        construction_result_id=candidate.result_id,
        construction_version=candidate.portfolio_version,
        components=tuple(
            SimpleNamespace(
                component_id=row.component_id,
                capital_weight=row.capital_weight,
                risk_budget=row.proposed_risk_budget_weight,
            )
            for row in candidate.component_weights
        ),
        runtime_profile="simulation",
        execution_route="sim",
    )

    def strategy_source(_request: PortfolioConstructionRequest):
        """Return unchanged Strategy references before activation."""
        logger.debug("Re-reading activation Strategy references")
        return refs

    def eligibility_source(_request: PortfolioConstructionRequest):
        """Return unchanged Risk eligibility before activation."""
        logger.debug("Re-reading activation Risk eligibility")
        return decisions

    def evidence_source(_request: PortfolioConstructionRequest):
        """Return complete owner evidence when requested."""
        logger.debug("Resolving activation construction evidence")
        return ConstructionEvidenceInputs(
            account,
            market,
            analytics,
            fx,
            {"component-a": Decimal("0.1"), "component-b": Decimal("0.2")},
            {"component-a": 30, "component-b": 30},
        )

    def simulation_runner(_request: PortfolioBacktestRequestV1):
        """Return a completed Simulation result for the exact candidate."""
        logger.info("Running activation Simulation receiver fake")
        return _simulation(candidate, portfolio_now)

    def risk_reviewer(_request):
        """Return a current inactive Risk approval for activation."""
        logger.info("Running activation Risk review receiver fake")
        return _risk_decision(candidate, portfolio_now)

    def kill_switch_source(_scope):
        """Return current inactive Risk kill-switch evidence."""
        logger.debug("Resolving activation kill-switch evidence")
        return (_inactive_kill_switch(portfolio_now),)

    def audit_persist(event: AuditEvent) -> str:
        """Persist one redacted activation audit identity."""
        logger.debug("Persisting activation integration audit")
        return event.event_id

    def clock() -> datetime:
        """Return stable UTC activation workflow time."""
        logger.debug("Reading activation integration clock")
        return portfolio_now

    service = PortfolioWorkflowService(
        portfolio_settings,
        PortfolioRepository(FakePortfolioStore()),
        PortfolioWorkflowDependencies(
            strategy_reference_source=strategy_source,
            eligibility_decision_source=eligibility_source,
            construction_evidence_source=evidence_source,
            simulation_runner=simulation_runner,
            risk_reviewer=risk_reviewer,
            risk_budget_activator=_activator,
            kill_switch_source=kill_switch_source,
            trading_executor=_unused,
            trading_execution_source=_unused,
            analytics_measurer=_unused,
            audit_persister=audit_persist,
            clock=clock,
        ),
    )
    review = service.coordinate_review(candidate, simulation_request, evidence)
    active = service.activate(
        candidate,
        evidence,
        review,
        approval_attestation=None,
        approval_validation=None,
        expires_at=portfolio_now + timedelta(days=1),
        idempotency_key="activation-integration-1",
        expected_predecessor=None,
        expected_revision=0,
    )
    assert active.risk_decision_id == review.risk_decision.decision_id
    assert active.simulation_result_id == review.simulation.result_id
