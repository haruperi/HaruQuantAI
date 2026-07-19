"""Integration tests for complete Portfolio construction coordination."""

# ruff: noqa: INP001

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import PortfolioConstructionRequest
from app.services.portfolio.orchestration import (
    ConstructionEvidenceInputs,
    PortfolioWorkflowDependencies,
    PortfolioWorkflowService,
)
from app.services.portfolio.state import PortfolioRepository
from app.utils import AuditEvent, logger
from tests.portfolio.unit.test_allocation import _activator, _inactive_kill_switch
from tests.portfolio.unit.test_evidence import (
    _owner_bundle,
    _patch_digest,
    _request_data_with_fx,
)
from tests.portfolio.unit.test_repository import FakePortfolioStore
from tests.portfolio.unit.test_workflows import _unused


def test_construction_workflow_validates_builds_persists_and_audits(
    construction_request_data: dict[str, Any],
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WF-PORT-001/002 retain exact owner lineage through persistence."""
    logger.info("Testing complete Portfolio construction workflow")
    _patch_digest(monkeypatch)
    request_data = _request_data_with_fx(construction_request_data)
    request_data.update(
        {
            "request_id": "req-" + "1" * 64,
            "workflow_id": "wf-" + "2" * 64,
            "correlation_id": "cor-" + "3" * 64,
        }
    )
    request = PortfolioConstructionRequest(**request_data)
    refs, decisions, account, market, analytics, fx = _owner_bundle(portfolio_now)

    def strategy_source(_request: PortfolioConstructionRequest):
        """Return exact Strategy references for this construction.

        Args:
            _request: Construction command.

        Returns:
            Component-keyed Strategy references.
        """
        logger.debug("Resolving integration Strategy references")
        return refs

    def eligibility_source(_request: PortfolioConstructionRequest):
        """Return exact Risk eligibility for this construction.

        Args:
            _request: Construction command.

        Returns:
            Decision-ID-keyed Risk eligibility.
        """
        logger.debug("Resolving integration Risk eligibility")
        return decisions

    def evidence_source(_request: PortfolioConstructionRequest):
        """Return exact Data and Analytics construction evidence.

        Args:
            _request: Construction command.

        Returns:
            Complete owner evidence input bundle.
        """
        logger.debug("Resolving integration construction evidence")
        return ConstructionEvidenceInputs(
            account_snapshot=account,
            market_dataset=market,
            analytics_evidence=analytics,
            fx_evidence=fx,
            component_volatilities={
                "component-a": Decimal("0.1"),
                "component-b": Decimal("0.2"),
            },
            component_observations={"component-a": 30, "component-b": 30},
        )

    def audit_persist(event: AuditEvent) -> str:
        """Persist and return one complete audit event identity.

        Args:
            event: Redacted Utils audit event.

        Returns:
            Exact event identity.
        """
        logger.debug("Persisting construction integration audit")
        return event.event_id

    def kill_switch_source(_scope):
        """Return current inactive Risk kill-switch evidence.

        Args:
            _scope: Governed Portfolio scope.

        Returns:
            One inactive Risk switch.
        """
        logger.debug("Resolving construction integration kill switch")
        return (_inactive_kill_switch(portfolio_now),)

    def clock() -> datetime:
        """Return the stable integration workflow time.

        Returns:
            Stable aware UTC time.
        """
        logger.debug("Reading construction integration clock")
        return portfolio_now

    store = FakePortfolioStore()
    service = PortfolioWorkflowService(
        portfolio_settings,
        PortfolioRepository(store),
        PortfolioWorkflowDependencies(
            strategy_reference_source=strategy_source,
            eligibility_decision_source=eligibility_source,
            construction_evidence_source=evidence_source,
            simulation_runner=_unused,
            risk_reviewer=_unused,
            risk_budget_activator=_activator,
            kill_switch_source=kill_switch_source,
            trading_executor=_unused,
            trading_execution_source=_unused,
            analytics_measurer=_unused,
            audit_persister=audit_persist,
            clock=clock,
        ),
    )
    result, evidence = service.construct(request)
    assert store.constructions[result.result_id] is result
    assert evidence.request is request
    assert result.component_weights[0].capital_weight == Decimal("0.5")
