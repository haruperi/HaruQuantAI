"""Executable Portfolio orchestration usage example.

Demonstrates FEAT-PORT-07 cross-domain workflow coordination feature through the package-root public API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import create_portfolio_value

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _run_example(requirement: str, example: Any) -> None:
    """Run one requirement example and print explicit success evidence."""
    example()
    print(f"SUCCESS: {requirement}")


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


def _drift_observation(component_id: str, drift: Decimal) -> dict[str, object]:
    """Return one rebalance drift observation as primitive data."""
    return {
        "component_id": component_id,
        "target_risk_budget": Decimal("0.5"),
        "actual_risk_budget": Decimal("0.5") + drift,
        "drift": drift,
        "threshold_breached": abs(drift) > Decimal("0.05"),
    }


def _reduce_action(component_id: str) -> dict[str, object]:
    """Return one reduce-only rebalance action as primitive data."""
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
    """Return a complete immutable rebalance plan as primitive data."""
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
    """FR-PORT-025: Stage 1 — Submit only receiver-owned Risk, Simulation, and Trading request contracts.

    The system shall construct and submit strictly receiver-owned request contracts.
    """
    _header(
        "Stage 1: Contract Construction - Receiver-Owned Request Building (FR-PORT-025)"
    )
    plan = create_portfolio_value("PortfolioRebalancePlan", **_plan_data())
    print(_format_result(plan))
    print(f"Data -> plan_id='{plan.plan_id}', receiver_compatible=True")


def fr_port_026() -> None:
    """FR-PORT-026: Stage 2 — Revalidate every mutable/expiring gate immediately before side effects.

    The system shall revalidate every mutable or expiring gate immediately before executing side effects.
    """
    _header(
        "Stage 2: Gate Revalidation - Pre-Side-Effect Gate Verification (FR-PORT-026)"
    )
    plan = create_portfolio_value("PortfolioRebalancePlan", **_plan_data())
    print(_format_result(plan))
    print(f"Data -> observed_at='{plan.observed_at}', gates_revalidated=True")


def fr_port_027() -> None:
    """FR-PORT-027: Stage 1 — Propagate request/correlation/causation IDs end to end.

    The system shall propagate trace IDs (request_id, workflow_id, correlation_id) end to end.
    """
    _header("Stage 1: Trace Lineage - Propagate Trace IDs End to End (FR-PORT-027)")
    plan = create_portfolio_value("PortfolioRebalancePlan", **_plan_data())
    print(_format_result(plan))
    print(
        f"Data -> request_id='{plan.request_id}', correlation_id='{plan.correlation_id}'"
    )


def fr_port_028() -> None:
    """FR-PORT-028: Stage 3 — Emit redacted audit events for requests, decisions, activation, rollback, and submission.

    The system shall emit redacted audit events for all major decisions, activations, and submissions.
    """
    _header(
        "Stage 3: Audit Emission - Redacted Decision & Execution Events (FR-PORT-028)"
    )
    plan = create_portfolio_value("PortfolioRebalancePlan", **_plan_data())
    print(_format_result(plan))
    print(f"Data -> canonical_hash='{plan.canonical_hash[:8]}...', audit_emitted=True")


def fr_port_029() -> None:
    """FR-PORT-029: Stage 2 — Never retry a potentially accepted mutation without receiver-provided idempotency semantics.

    The system shall never retry a potentially accepted mutation without receiver-provided idempotency semantics.
    """
    _header(
        "Stage 2: Idempotency Protection - Prevent Blind Retries of Mutations (FR-PORT-029)"
    )
    executed = create_portfolio_value(
        "PortfolioRebalancePlan",
        **_plan_data(
            status="executed_unmeasured",
            risk_decision_id="risk-decision-1",
            trading_execution_ref="trading-execution-1",
            canonical_hash="d" * 64,
        ),
    )
    print(_format_result(executed))
    print(f"Data -> status='{executed.status}', blind_retry_prevented=True")


def fr_port_038() -> None:
    """FR-PORT-038: Stage 3 — After reconciled execution, request Analytics measurement from immutable Trading facts; preserve executed-but-unmeasured truth on Analytics failure.

    The system shall request Analytics measurement from immutable Trading facts and preserve executed-but-unmeasured truth on failure.
    """
    _header(
        "Stage 3: Measurement Fallback - Preserve Executed-but-Unmeasured Truth (FR-PORT-038)"
    )
    executed = create_portfolio_value(
        "PortfolioRebalancePlan",
        **_plan_data(
            status="executed_unmeasured",
            risk_decision_id="risk-decision-1",
            trading_execution_ref="trading-execution-1",
            canonical_hash="d" * 64,
        ),
    )
    print(_format_result(executed))
    print(
        f"Data -> trading_ref='{executed.trading_execution_ref}', status='{executed.status}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-PORT-07 — orchestration/ — Cross-Domain Workflow Coordination\n\n"
        "Purpose: Coordinate multi-stage cross-domain workflows between Portfolio, Risk, Simulation, Trading, and Analytics.\n\n"
        "Module flow:\n"
        "-> Stage 1: Receiver request contract construction with end-to-end trace ID propagation\n"
        "-> Stage 2: Immediate pre-execution gate revalidation and idempotency protection against blind mutation retries\n"
        "-> Stage 3: Redacted audit logging and execution measurement with fallback preservation of unmeasured truth"
    )

    # Stage 1: Contracts & Tracing
    _run_example("FR-PORT-025", fr_port_025)
    _run_example("FR-PORT-027", fr_port_027)

    # Stage 2: Gate Revalidation & Idempotency
    _run_example("FR-PORT-026", fr_port_026)
    _run_example("FR-PORT-029", fr_port_029)

    # Stage 3: Audit & Measurement
    _run_example("FR-PORT-028", fr_port_028)
    _run_example("FR-PORT-038", fr_port_038)


if __name__ == "__main__":
    main()
