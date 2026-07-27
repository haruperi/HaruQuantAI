"""Shared, non-workflow infrastructure for Portfolio workflow examples."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import MarketDataset, get_market_data
from app.services.portfolio import (
    ActivePortfolioAllocation,
    PortfolioConstructionRequest,
    PortfolioConstructionResult,
)
from app.services.portfolio.config import PortfolioSettings, RebalanceSchedule
from app.services.portfolio.contracts import PortfolioComponentWeight
from app.services.portfolio.orchestration import (
    ConstructionEvidenceInputs,
    PortfolioWorkflowDependencies,
    PortfolioWorkflowService,
)
from app.services.portfolio.state import PortfolioRepository
from app.services.simulator import PortfolioBacktestRequestV1
from app.utils import AuditEvent
from tests.data.usage.workflows._support import market_request
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

_DATASET_ENV = "HARU_WORKFLOW_MARKET_DATASET"
NOW = datetime.now(UTC).replace(microsecond=0)


def live_market_dataset() -> MarketDataset:
    """Return genuine bounded MT5 evidence, reusing runner-captured evidence."""
    captured = os.environ.get(_DATASET_ENV)
    if captured:
        return MarketDataset.model_validate_json(
            Path(captured).read_text(encoding="utf-8")
        )
    return get_market_data(market_request("bars", timeframe="M1", limit=20))


def settings() -> PortfolioSettings:
    """Return explicit bounded simulation-only Portfolio policy."""
    return PortfolioSettings(
        portfolio_weight_sum_tolerance=Decimal("0.00000001"),
        portfolio_min_weight=Decimal(0),
        portfolio_max_weight=Decimal(1),
        portfolio_max_strategies=10,
        portfolio_min_evidence_observations=1,
        portfolio_max_evidence_age_seconds=31_536_000,
        portfolio_allocation_decision_ttl_seconds=900,
        portfolio_activation_approval_policy={
            "simulation": "automatic_within_policy",
            "paper": "explicit_human",
            "live": "explicit_human",
        },
        portfolio_rebalance_drift_threshold=Decimal("0.05"),
        portfolio_rebalance_schedule=RebalanceSchedule(
            anchor_at=NOW,
            interval_seconds=3600,
        ),
    )


def construction_result() -> PortfolioConstructionResult:
    """Return one immutable simulation allocation candidate."""
    weights = tuple(
        PortfolioComponentWeight(
            component_id=f"component-{suffix}",
            strategy_id=f"strategy-{suffix}",
            strategy_version="1.0.0",
            capital_weight=Decimal("0.5"),
            proposed_risk_budget_weight=Decimal("0.5"),
        )
        for suffix in ("a", "b")
    )
    return PortfolioConstructionResult(
        result_id="portfolio-result-1",
        portfolio_id="portfolio-alpha",
        portfolio_version="version-1",
        scope={"environment": "simulation", "tenant": "owner"},
        status="constructed",
        component_weights=weights,
        method="equal",
        config_hash="a" * 64,
        evidence_hash="b" * 64,
        strategy_lineage_hash="c" * 64,
        canonical_hash="d" * 64,
        created_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def active_allocation() -> ActivePortfolioAllocation:
    """Return one current simulation allocation derived from the candidate."""
    candidate = construction_result()
    return ActivePortfolioAllocation(
        allocation_id="allocation-1",
        portfolio_id=candidate.portfolio_id,
        allocation_version="allocation-version-1",
        scope=candidate.scope,
        construction_result_id=candidate.result_id,
        construction_result_hash=candidate.canonical_hash,
        component_weights=candidate.component_weights,
        simulation_result_id="simulation-result-1",
        simulation_result_hash="e" * 64,
        risk_decision_id="risk-decision-1",
        risk_budget_projection_ref="risk-projection-1",
        activated_at=NOW,
        expires_at=NOW + timedelta(days=1),
        idempotency_key="activation-idempotency-1",
        canonical_hash="f" * 64,
        request_id=candidate.request_id,
        workflow_id=candidate.workflow_id,
        correlation_id=candidate.correlation_id,
        audit_ref="audit-1",
    )


def construction_workflow() -> tuple[
    PortfolioWorkflowService,
    PortfolioConstructionRequest,
    FakePortfolioStore,
    MarketDataset,
]:
    """Build the complete Portfolio service boundary over genuine MT5 evidence."""
    market = live_market_dataset()
    refs, decisions, account, _placeholder, analytics, fx = _owner_bundle(NOW)
    request_data: dict[str, Any] = {
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "causation_id": None,
        "portfolio_id": "portfolio-alpha",
        "portfolio_version": "version-1",
        "scope": {"environment": "simulation", "tenant": "owner"},
        "components": tuple(
            {
                "component_id": f"component-{suffix}",
                "strategy_id": f"strategy-{suffix}",
                "strategy_version": "1.0.0",
                "registry_record_hash": suffix * 64,
                "eligibility_decision_id": f"eligibility-{suffix}",
            }
            for suffix in ("a", "b")
        ),
        "method": "equal",
        "fixed_weights": (),
        "evidence": {
            "account_snapshot_id": account.request_id,
            "account_snapshot_hash": "a" * 64,
            "account_snapshot_as_of": account.snapshot_at,
            "market_dataset_id": market.request_id,
            "market_dataset_hash": "b" * 64,
            "market_dataset_as_of": market.end,
            "analytics_evidence_id": analytics.evidence_id,
            "analytics_evidence_hash": "c" * 64,
            "analytics_evidence_as_of": analytics.measurement_end,
            "fx_evidence_ids": ("fx-1",),
            "fx_evidence_hashes": ("d" * 64,),
        },
        "measurement_start": market.start,
        "measurement_end": market.end,
        "base_currency": "USD",
        "runtime_profile": "simulation",
        "execution_route": "sim",
        "simulation_policy_version": "simulation-policy-1",
        "requested_at": NOW,
    }
    request = PortfolioConstructionRequest(
        **_request_data_with_fx(request_data),
    )

    def strategy_source(_request: PortfolioConstructionRequest):
        return refs

    def eligibility_source(_request: PortfolioConstructionRequest):
        return decisions

    def evidence_source(_request: PortfolioConstructionRequest):
        return ConstructionEvidenceInputs(
            account,
            market,
            analytics,
            fx,
            {"component-a": Decimal("0.1"), "component-b": Decimal("0.2")},
            {"component-a": 30, "component-b": 30},
        )

    def simulation_runner(
        receiver_request: PortfolioBacktestRequestV1,
    ):
        candidate = store.constructions[receiver_request.construction_result_id]
        return _simulation(candidate, NOW)

    def risk_reviewer(receiver_request):
        candidate = next(
            result
            for result in store.constructions.values()
            if result.portfolio_version == receiver_request.portfolio_version
        )
        return _risk_decision(candidate, NOW)

    def audit_persist(event: AuditEvent) -> str:
        return event.event_id

    patcher = __import__("pytest").MonkeyPatch()
    _patch_digest(patcher)
    store = FakePortfolioStore()
    service = PortfolioWorkflowService(
        settings(),
        PortfolioRepository(store),
        PortfolioWorkflowDependencies(
            strategy_reference_source=strategy_source,
            eligibility_decision_source=eligibility_source,
            construction_evidence_source=evidence_source,
            simulation_runner=simulation_runner,
            risk_reviewer=risk_reviewer,
            risk_budget_activator=_activator,
            kill_switch_source=lambda _scope: (_inactive_kill_switch(NOW),),
            trading_executor=_unused,
            trading_execution_source=_unused,
            analytics_measurer=_unused,
            audit_persister=audit_persist,
            clock=lambda: NOW,
        ),
    )
    return service, request, store, market


def simulation_request(
    candidate: PortfolioConstructionResult,
) -> PortfolioBacktestRequestV1:
    """Build the receiver-owned Simulation request bound to one candidate."""
    return PortfolioBacktestRequestV1.model_construct(
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


__all__ = [
    "NOW",
    "_DATASET_ENV",
    "active_allocation",
    "construction_result",
    "construction_workflow",
    "live_market_dataset",
    "settings",
    "simulation_request",
]
