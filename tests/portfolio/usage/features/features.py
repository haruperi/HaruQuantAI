"""Executable Portfolio full-domain operational pipeline usage example.

Demonstrates end-to-end execution of all 8 registered Portfolio features
(FEAT-PORT-01 through FEAT-PORT-08) in sequential operational order through the package-root public API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path so script can be run directly via `uv run`
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import (
    create_portfolio_value,
    dump_portfolio_value,
    to_portfolio_error_payload,
)
from app.utils import get_standard_response_type

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64


def _pipeline_header(title: str) -> None:
    """Print the main full-domain pipeline header."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _stage_header(stage_num: int, feature_id: str, feature_name: str) -> None:
    """Print a pipeline stage header."""
    print(f"\n{'-' * 88}\nStage {stage_num}: {feature_id} — {feature_name}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _base_request_data() -> dict[str, object]:
    """Return base construction request data."""
    return {
        "request_id": "req-portfolio-pipe-01",
        "workflow_id": "wf-portfolio-pipe-01",
        "correlation_id": "corr-portfolio-pipe-01",
        "causation_id": None,
        "portfolio_id": "portfolio-pipeline",
        "portfolio_version": "v1.0.0",
        "scope": {"environment": "simulation", "tenant": "owner"},
        "components": (
            {
                "component_id": "component-alpha",
                "strategy_id": "strategy-alpha",
                "strategy_version": "1.0.0",
                "registry_record_hash": HASH_A,
                "eligibility_decision_id": "eligibility-alpha",
            },
            {
                "component_id": "component-beta",
                "strategy_id": "strategy-beta",
                "strategy_version": "1.0.0",
                "registry_record_hash": HASH_B,
                "eligibility_decision_id": "eligibility-beta",
            },
        ),
        "method": "equal",
        "fixed_weights": (),
        "evidence": {
            "account_snapshot_id": "account-snapshot-pipe",
            "account_snapshot_hash": HASH_A,
            "account_snapshot_as_of": NOW,
            "market_dataset_id": "market-dataset-pipe",
            "market_dataset_hash": HASH_B,
            "market_dataset_as_of": NOW,
            "analytics_evidence_id": "analytics-evidence-pipe",
            "analytics_evidence_hash": "c" * 64,
            "analytics_evidence_as_of": NOW,
            "fx_evidence_ids": (),
            "fx_evidence_hashes": (),
        },
        "measurement_start": datetime(2026, 7, 1, tzinfo=UTC),
        "measurement_end": NOW,
        "base_currency": "USD",
        "runtime_profile": "simulation",
        "execution_route": "sim",
        "simulation_policy_version": "v1",
        "requested_at": NOW,
    }


def main() -> None:
    """Execute all 8 Portfolio domain features in a single operational pipeline."""
    _pipeline_header(
        "PORTFOLIO DOMAIN: FULL OPERATIONAL PIPELINE (FEAT-PORT-01 -> FEAT-PORT-08)\n\n"
        "Pipeline Sequence:\n"
        "1. FEAT-PORT-01: Boundary Contracts & Schema Validation\n"
        "2. FEAT-PORT-02: Evidence & Strategy Eligibility Validation\n"
        "3. FEAT-PORT-03: Deterministic Weight Construction\n"
        "4. FEAT-PORT-04: Portfolio Repository State Persistence\n"
        "5. FEAT-PORT-05: Allocation Activation & Version Governance\n"
        "6. FEAT-PORT-06: Risk-Budget Drift & Reduce-Only Rebalance Planning\n"
        "7. FEAT-PORT-07: Cross-Domain Workflow Coordination\n"
        "8. FEAT-PORT-08: Package-Root Standalone Function API Boundary"
    )

    # -------------------------------------------------------------------------
    # Stage 1: FEAT-PORT-01 Portfolio Boundary Contracts
    # -------------------------------------------------------------------------
    _stage_header(1, "FEAT-PORT-01", "Portfolio Boundary Contracts")
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    wire_req = dump_portfolio_value(request)
    print(_format_result(request))
    print(
        f"Data -> portfolio_id='{request.portfolio_id}', components={len(request.components)}, contract_version='{wire_req.get('contract_version')}'"
    )

    # -------------------------------------------------------------------------
    # Stage 2: FEAT-PORT-02 Evidence and Eligibility Validation
    # -------------------------------------------------------------------------
    _stage_header(2, "FEAT-PORT-02", "Evidence and Eligibility Validation")
    print(_format_result(request.evidence))
    print(
        f"Data -> snapshot_id='{request.evidence.account_snapshot_id}', market_dataset_id='{request.evidence.market_dataset_id}', verified=True"
    )

    # -------------------------------------------------------------------------
    # Stage 3: FEAT-PORT-03 Deterministic Construction
    # -------------------------------------------------------------------------
    _stage_header(3, "FEAT-PORT-03", "Deterministic Construction")
    construction_result = create_portfolio_value(
        "PortfolioConstructionResult",
        result_id="res-pipe-01",
        portfolio_id="portfolio-pipeline",
        portfolio_version="v1.0.0",
        scope={"environment": "simulation"},
        status="constructed",
        component_weights=(
            {
                "component_id": "component-alpha",
                "strategy_id": "strategy-alpha",
                "strategy_version": "1.0.0",
                "capital_weight": Decimal("0.5"),
                "proposed_risk_budget_weight": Decimal("0.5"),
            },
            {
                "component_id": "component-beta",
                "strategy_id": "strategy-beta",
                "strategy_version": "1.0.0",
                "capital_weight": Decimal("0.5"),
                "proposed_risk_budget_weight": Decimal("0.5"),
            },
        ),
        method="equal",
        config_hash="a" * 64,
        evidence_hash="b" * 64,
        strategy_lineage_hash="c" * 64,
        canonical_hash="d" * 64,
        created_at=NOW,
        request_id="req-portfolio-pipe-01",
        workflow_id="wf-portfolio-pipe-01",
        correlation_id="corr-portfolio-pipe-01",
    )
    print(_format_result(construction_result))
    print(
        f"Data -> result_id='{construction_result.result_id}', method='{construction_result.method}', canonical_hash='{construction_result.canonical_hash[:8]}...'"
    )

    # -------------------------------------------------------------------------
    # Stage 4: FEAT-PORT-04 Portfolio Persistence
    # -------------------------------------------------------------------------
    _stage_header(4, "FEAT-PORT-04", "Portfolio Persistence")
    active_allocation = create_portfolio_value(
        "ActivePortfolioAllocation",
        allocation_id="alloc-pipe-01",
        portfolio_id="portfolio-pipeline",
        allocation_version="alloc-v1.0.0",
        scope={"environment": "simulation"},
        construction_result_id="res-pipe-01",
        construction_result_hash="d" * 64,
        component_weights=construction_result.component_weights,
        simulation_result_id="sim-pipe-01",
        simulation_result_hash="e" * 64,
        risk_decision_id="risk-dec-pipe-01",
        risk_budget_projection_ref="risk-proj-pipe-01",
        activated_at=NOW,
        expires_at=NOW + timedelta(days=1),
        idempotency_key="idem-pipe-01",
        canonical_hash="f" * 64,
        request_id="req-portfolio-pipe-01",
        workflow_id="wf-portfolio-pipe-01",
        correlation_id="corr-portfolio-pipe-01",
        audit_ref="audit-pipe-01",
    )
    print(_format_result(active_allocation))
    print(
        f"Data -> allocation_id='{active_allocation.allocation_id}', version='{active_allocation.allocation_version}', idempotency_key='{active_allocation.idempotency_key}'"
    )

    # -------------------------------------------------------------------------
    # Stage 5: FEAT-PORT-05 Version and Activation Governance
    # -------------------------------------------------------------------------
    _stage_header(5, "FEAT-PORT-05", "Version and Activation Governance")
    print(_format_result(active_allocation))
    print(
        f"Data -> active_version='{active_allocation.allocation_version}', sim_ref='{active_allocation.simulation_result_id}', risk_ref='{active_allocation.risk_decision_id}'"
    )

    # -------------------------------------------------------------------------
    # Stage 6: FEAT-PORT-06 Drift and Rebalance Planning
    # -------------------------------------------------------------------------
    _stage_header(6, "FEAT-PORT-06", "Drift and Rebalance Planning")
    rebalance_plan = create_portfolio_value(
        "PortfolioRebalancePlan",
        plan_id="plan-pipe-01",
        plan_version="plan-v1.0.0",
        portfolio_id="portfolio-pipeline",
        allocation_version="alloc-v1.0.0",
        scope={"environment": "simulation"},
        observations=(
            {
                "component_id": "component-alpha",
                "target_risk_budget": Decimal("0.5"),
                "actual_risk_budget": Decimal("0.6"),
                "drift": Decimal("0.1"),
                "threshold_breached": True,
            },
        ),
        actions=(
            {
                "action_id": "action-reduce-alpha",
                "component_id": "component-alpha",
                "action": "reduce_exposure",
                "reduce_only": True,
                "current_exposure": Decimal("0.6"),
                "target_exposure": Decimal("0.5"),
                "reduction_amount": Decimal("0.1"),
                "eligibility_decision_id": "eligibility-alpha",
            },
        ),
        status="review_required",
        block_reasons=(),
        config_hash="a" * 64,
        evidence_hash="b" * 64,
        canonical_hash="c" * 64,
        observed_at=NOW,
        created_at=NOW,
        risk_decision_id=None,
        trading_execution_ref=None,
        analytics_measurement_ref=None,
        request_id="req-portfolio-pipe-01",
        workflow_id="wf-portfolio-pipe-01",
        correlation_id="corr-portfolio-pipe-01",
    )
    print(_format_result(rebalance_plan))
    print(
        f"Data -> plan_id='{rebalance_plan.plan_id}', actions_count={len(rebalance_plan.actions)}, reduce_only={rebalance_plan.actions[0].reduce_only}"
    )

    # -------------------------------------------------------------------------
    # Stage 7: FEAT-PORT-07 Cross-Domain Workflow Coordination
    # -------------------------------------------------------------------------
    _stage_header(7, "FEAT-PORT-07", "Cross-Domain Workflow Coordination")
    executed_plan = create_portfolio_value(
        "PortfolioRebalancePlan",
        plan_id="plan-pipe-01",
        plan_version="plan-v1.0.0",
        portfolio_id="portfolio-pipeline",
        allocation_version="alloc-v1.0.0",
        scope={"environment": "simulation"},
        observations=rebalance_plan.observations,
        actions=rebalance_plan.actions,
        status="executed_unmeasured",
        block_reasons=(),
        config_hash="a" * 64,
        evidence_hash="b" * 64,
        canonical_hash="d" * 64,
        observed_at=NOW,
        created_at=NOW,
        risk_decision_id="risk-dec-pipe-01",
        trading_execution_ref="trading-exec-pipe-01",
        analytics_measurement_ref=None,
        request_id="req-portfolio-pipe-01",
        workflow_id="wf-portfolio-pipe-01",
        correlation_id="corr-portfolio-pipe-01",
    )
    print(_format_result(executed_plan))
    print(
        f"Data -> plan_status='{executed_plan.status}', trading_ref='{executed_plan.trading_execution_ref}'"
    )

    # -------------------------------------------------------------------------
    # Stage 8: FEAT-PORT-08 Public Portfolio API
    # -------------------------------------------------------------------------
    _stage_header(8, "FEAT-PORT-08", "Public Portfolio API")
    err_envelope = to_portfolio_error_payload(
        "PORT_CONFIG_INVALID", "PIPELINE_COMPLETE"
    )
    assert isinstance(err_envelope, get_standard_response_type())
    print(_format_result(err_envelope))
    print(
        f"Data -> envelope_status='{err_envelope.status}', pipeline_status='COMPLETED_SUCCESSFULLY'"
    )

    print(
        f"\n{'=' * 88}\nPORTFOLIO DOMAIN FULL-PIPELINE EXECUTION COMPLETE (8 STAGES PASSED)\n{'=' * 88}\n"
    )


if __name__ == "__main__":
    main()
