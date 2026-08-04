"""Integration test for Simulation/Risk-reviewed Portfolio activation."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from app.services.portfolio import (
    create_portfolio_handle,
    create_portfolio_value,
    execute_portfolio_handle_operation,
    validate_construction_evidence,
)
from app.services.simulator import (
    calculate_portfolio_backtest_config_hash,
    calculate_simulation_backtest_config_hash,
    create_simulation_value,
    dump_simulation_value,
    unwrap_simulation_response,
)
from app.utils import get_logger

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

AuditEvent = Any
PortfolioBacktestRequestV1 = Any
PortfolioConstructionRequest = Any
PortfolioConstructionResult = Any
PortfolioSettings = Any
logger = get_logger(__name__)


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
    request = create_portfolio_value("PortfolioConstructionRequest", **request_data)
    candidate = create_portfolio_value(
        "PortfolioConstructionResult",
        **{
            **construction_result.model_dump(mode="python"),
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
        },
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
    component_requests = []
    for index, row in enumerate(candidate.component_weights, start=1):
        request_fields = {
            "request_id": f"req-11111111-1111-4111-8111-11111111111{index}",
            "workflow_id": candidate.workflow_id,
            "correlation_id": candidate.correlation_id,
            "strategy_id": f"strategy-{row.component_id}",
            "strategy_version": "1.0.0",
            "strategy_config_ref": f"strategy-config-{row.component_id}",
            "strategy_config_hash": "1" * 64,
            "data_ref": "market-dataset-1",
            "data_version": "v1",
            "data_hash": "2" * 64,
            "tick_generation_ref": "tick-generation-1",
            "tick_generation_version": "v1",
            "tick_generation_hash": "3" * 64,
            "execution_profile_ref": "execution-profile-1",
            "execution_profile_version": "v1",
            "execution_profile_hash": "4" * 64,
            "risk_policy_ref": "risk-policy-1",
            "risk_policy_version": "v1",
            "risk_policy_hash": "5" * 64,
            "symbol": "EURUSD",
            "timeframe": "M1",
            "start": portfolio_now - timedelta(minutes=1),
            "end": portfolio_now,
            "parameters": {},
            "initial_balance": Decimal(1000) * row.capital_weight,
            "account_currency": "USD",
            "asset_class": "FX",
            "seed": index,
            "runtime_profile": "simulation",
            "execution_route": "sim",
            "canonical": True,
        }
        request_fields["config_hash"] = unwrap_simulation_response(
            calculate_simulation_backtest_config_hash(request_fields),
            operation="calculate simulation backtest config hash",
        )
        component_requests.append(
            {
                "component_id": row.component_id,
                "capital_weight": row.capital_weight,
                "risk_budget": row.proposed_risk_budget_weight,
                "risk_decision_id": f"eligibility-{row.component_id}",
                "metrics_ref": f"analytics-{row.component_id}",
                "backtest_request": create_simulation_value(
                    "SimulationBacktestRequestV1",
                    **request_fields,
                ),
            }
        )
    portfolio_request_fields = {
        "request_id": candidate.request_id,
        "workflow_id": candidate.workflow_id,
        "correlation_id": candidate.correlation_id,
        "portfolio_id": candidate.portfolio_id,
        "construction_result_id": candidate.result_id,
        "construction_version": candidate.portfolio_version,
        "components": tuple(component_requests),
        "measurement_start": portfolio_now - timedelta(minutes=1),
        "measurement_end": portfolio_now,
        "base_currency": "USD",
        "fx_evidence_ids": ("req-11111111-1111-4111-8111-111111111114",),
        "fx_evidence_versions": ("v1",),
        "fx_evidence_hashes": ("d" * 64,),
        "execution_profile_version": "v1",
        "risk_policy_version": "risk-policy-1",
        "seed": 7,
        "initial_balance": Decimal(1000),
        "runtime_profile": "simulation",
        "execution_route": "sim",
    }
    hash_fields = {
        **portfolio_request_fields,
        "components": tuple(
            {
                **component,
                "backtest_request": dump_simulation_value(
                    component["backtest_request"]
                ),
            }
            for component in component_requests
        ),
    }
    portfolio_request_fields["config_hash"] = unwrap_simulation_response(
        calculate_portfolio_backtest_config_hash(hash_fields),
        operation="calculate portfolio backtest config hash",
    )
    simulation_request = create_simulation_value(
        "PortfolioBacktestRequestV1",
        **portfolio_request_fields,
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
        return create_portfolio_value(
            "ConstructionEvidenceInputs",
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

    repository = create_portfolio_handle("PortfolioRepository", FakePortfolioStore())
    dependencies = create_portfolio_handle(
        "PortfolioWorkflowDependencies",
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
    )
    service = create_portfolio_handle(
        "PortfolioWorkflowService",
        portfolio_settings,
        repository,
        dependencies,
    )
    review = execute_portfolio_handle_operation(
        service,
        "coordinate_review",
        candidate,
        simulation_request,
        evidence,
    )
    active = execute_portfolio_handle_operation(
        service,
        "activate",
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
