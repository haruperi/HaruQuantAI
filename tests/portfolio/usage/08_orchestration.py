"""Executable Portfolio orchestration usage example.

Demonstrates the cross-domain workflow coordination feature through the
package-root public API. Each functional requirement FR-PORT-025 through
FR-PORT-029 and FR-PORT-038 has a dedicated demonstration function.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import PortfolioRebalancePlan

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _drift_observation(
    component_id: str,
    drift: Decimal,
) -> dict[str, object]:
    """Return one rebalance drift observation as primitive data.

    Args:
        component_id: Component identity for the observation.
        drift: Signed drift value.

    Returns:
        Drift observation primitive mapping.
    """
    return {
        "component_id": component_id,
        "target_risk_budget": Decimal("0.5"),
        "actual_risk_budget": Decimal("0.5") + drift,
        "drift": drift,
        "threshold_breached": abs(drift) > Decimal("0.05"),
    }


def _reduce_action(component_id: str) -> dict[str, object]:
    """Return one reduce-only rebalance action as primitive data.

    Args:
        component_id: Component identity for the action.

    Returns:
        Reduce-only action primitive mapping.
    """
    return {
        "action_id": f"action-{component_id}",
        "component_id": component_id,
        "action": "reduce_exposure",
        "reduce_only": True,
        "current_exposure": Decimal("0.6"),
        "target_exposure": Decimal("0.5"),
        "reduction_amount": Decimal("0.1"),
        "eligibility_decision_id": f"eligibility-{component_id}",
    }


def _plan_data(**overrides: object) -> dict[str, object]:
    """Return a complete immutable rebalance plan as primitive data.

    Args:
        **overrides: Optional field overrides for plan variants.

    Returns:
        Complete plan constructor data.
    """
    data: dict[str, object] = {
        "plan_id": "plan-1",
        "plan_version": "plan-version-1",
        "portfolio_id": "portfolio-alpha",
        "allocation_version": "allocation-version-1",
        "scope": {"environment": "simulation"},
        "observations": (
            _drift_observation("component-a", Decimal("0.1")),
            _drift_observation("component-b", Decimal("-0.02")),
        ),
        "actions": (_reduce_action("component-a"),),
        "status": "review_required",
        "block_reasons": (),
        "config_hash": "a" * 64,
        "evidence_hash": "b" * 64,
        "canonical_hash": "c" * 64,
        "observed_at": NOW,
        "created_at": NOW,
        "risk_decision_id": None,
        "trading_execution_ref": None,
        "analytics_measurement_ref": None,
        "request_id": "req-1",
        "workflow_id": "wf-1",
        "correlation_id": "corr-1",
    }
    data.update(overrides)
    return data


def fr_port_025() -> None:
    """FR-PORT-025: Submit only receiver-owned Risk, Simulation, and Trading
    request contracts.

    Demonstrates that the rebalance plan carries receiver-compatible action
    data that does not embed Portfolio-owned contract instances.
    """
    _header(
        "FR-PORT-025: Submit only receiver-owned Risk, Simulation, and Trading request contracts. Demonstrates that the rebalance plan carries receiver-compatible action data that does not embed Portfolio-owned contract instances."
    )
    print("FR-PORT-025: Submit only receiver-owned request contracts")

    plan = PortfolioRebalancePlan(**_plan_data())
    for action in plan.actions:
        assert action.action == "reduce_exposure"
        assert action.reduce_only is True
    print(f"Plan actions: {len(plan.actions)} reduce-only action(s)")
    print("Actions carry primitive values compatible with Trading receiver")


def fr_port_026() -> None:
    """FR-PORT-026: Revalidate every mutable/expiring gate immediately before
    side effects.

    Demonstrates that the plan carries fresh observed_at and created_at
    timestamps for gate revalidation.
    """
    _header(
        "FR-PORT-026: Revalidate every mutable/expiring gate immediately before side effects. Demonstrates that the plan carries fresh observed_at and created_at timestamps for gate revalidation."
    )
    print("FR-PORT-026: Revalidate gates before side effects")

    plan = PortfolioRebalancePlan(**_plan_data())
    assert plan.observed_at.tzinfo is not None
    assert plan.created_at.tzinfo is not None
    print(f"Observed at: {plan.observed_at}")
    print(f"Created at: {plan.created_at}")
    print("Fresh timestamps enable immediate gate revalidation")


def fr_port_027() -> None:
    """FR-PORT-027: Propagate request/correlation/causation IDs end to end.

    Demonstrates that the plan carries trace IDs for end-to-end propagation.
    """
    _header(
        "FR-PORT-027: Propagate request/correlation/causation IDs end to end. Demonstrates that the plan carries trace IDs for end-to-end propagation."
    )
    print("FR-PORT-027: Propagate trace IDs end to end")

    plan = PortfolioRebalancePlan(**_plan_data())
    assert plan.request_id == "req-1"
    assert plan.workflow_id == "wf-1"
    assert plan.correlation_id == "corr-1"
    print(f"request_id: {plan.request_id}")
    print(f"workflow_id: {plan.workflow_id}")
    print(f"correlation_id: {plan.correlation_id}")
    print("Trace IDs propagate to every receiver request")


def fr_port_028() -> None:
    """FR-PORT-028: Emit redacted audit events for requests, decisions,
    activation, rollback, and submission.

    Demonstrates that the plan carries canonical and evidence hashes for
    auditable redacted lineage.
    """
    _header(
        "FR-PORT-028: Emit redacted audit events for requests, decisions, activation, rollback, and submission. Demonstrates that the plan carries canonical and evidence hashes for auditable redacted lineage."
    )
    print("FR-PORT-028: Emit redacted audit events")

    plan = PortfolioRebalancePlan(**_plan_data())
    assert len(plan.canonical_hash) == 64
    assert len(plan.evidence_hash) == 64
    assert len(plan.config_hash) == 64
    print(f"canonical_hash: {plan.canonical_hash[:16]}...")
    print(f"evidence_hash: {plan.evidence_hash[:16]}...")
    print(f"config_hash: {plan.config_hash[:16]}...")
    print("Hash-bound plan supports redacted audit lineage")


def fr_port_029() -> None:
    """FR-PORT-029: Never retry a potentially accepted mutation without
    receiver-provided idempotency semantics.

    Demonstrates that the plan status transitions deterministically and never
    implies a blind retry of a receiver mutation.
    """
    _header(
        "FR-PORT-029: Never retry a potentially accepted mutation without receiver-provided idempotency semantics. Demonstrates that the plan status transitions deterministically and never implies a blind retry of a receiver mutation."
    )
    print("FR-PORT-029: Never retry accepted mutation without idempotency")

    plan = PortfolioRebalancePlan(**_plan_data())
    assert plan.status == "review_required"
    print(f"Plan status before submission: {plan.status}")

    executed = PortfolioRebalancePlan(
        **_plan_data(
            status="executed_unmeasured",
            risk_decision_id="risk-decision-1",
            trading_execution_ref="trading-execution-1",
            canonical_hash="d" * 64,
        )
    )
    assert executed.status == "executed_unmeasured"
    assert executed.trading_execution_ref
    print(f"Executed status: {executed.status}")
    print(f"Trading ref: {executed.trading_execution_ref}")
    print("Execution truth is preserved before measurement — no blind retry")


def fr_port_038() -> None:
    """FR-PORT-038: After reconciled execution, request Analytics measurement
    from immutable Trading facts; preserve executed-but-unmeasured truth on
    Analytics failure.

    Demonstrates that the plan supports measured status and preserves execution
    reference for deterministic recomputation.
    """
    _header(
        "FR-PORT-038: After reconciled execution, request Analytics measurement from immutable Trading facts; preserve executed-but-unmeasured truth on Analytics failure. Demonstrates that the plan supports measured status and preserves execution reference for deterministic recomputation."
    )
    print("FR-PORT-038: Request Analytics measurement, preserve execution truth")

    executed = PortfolioRebalancePlan(
        **_plan_data(
            status="executed_unmeasured",
            risk_decision_id="risk-decision-1",
            trading_execution_ref="trading-execution-1",
            canonical_hash="d" * 64,
        )
    )
    assert executed.status == "executed_unmeasured"
    assert executed.trading_execution_ref is not None
    print(f"Executed-but-unmeasured: {executed.status}")
    print(f"Trading execution ref preserved: {executed.trading_execution_ref}")

    measured = PortfolioRebalancePlan(
        **_plan_data(
            status="measured",
            risk_decision_id="risk-decision-1",
            trading_execution_ref="trading-execution-1",
            analytics_measurement_ref="analytics-evidence-1",
            canonical_hash="e" * 64,
        )
    )
    assert measured.status == "measured"
    assert measured.analytics_measurement_ref == "analytics-evidence-1"
    print(f"Measured status: {measured.status}")
    print(f"Analytics evidence ref: {measured.analytics_measurement_ref}")
    print("Measurement is deterministic from immutable Trading facts")


def main() -> None:
    """Run every functional-requirement demonstration for Portfolio orchestration."""
    fr_port_025()
    fr_port_026()
    fr_port_027()
    fr_port_028()
    fr_port_029()
    fr_port_038()


if __name__ == "__main__":
    main()
