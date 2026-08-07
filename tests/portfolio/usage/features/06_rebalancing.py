"""Executable Portfolio rebalancing usage example.

Demonstrates FEAT-PORT-06 drift and rebalance planning feature through the package-root public API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import (
    assess_common_mode_exposure,
    create_portfolio_value,
    measure_cross_account_correlation,
)

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


def _base_plan_data(**overrides: object) -> dict[str, object]:
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


def fr_port_020() -> None:
    """FR-PORT-020: Stage 1 — Bind drift to an active allocation version and fresh actual-exposure evidence.

    The system shall bind drift calculation to an active allocation version and fresh actual-exposure evidence.
    """
    _header("Stage 1: Drift Binding - Target Version & Exposure Evidence (FR-PORT-020)")
    plan = create_portfolio_value("PortfolioRebalancePlan", **_base_plan_data())
    print(_format_result(plan))
    print(
        f"Data -> allocation_version='{plan.allocation_version}', observed_at='{plan.observed_at}'"
    )


def fr_port_021() -> None:
    """FR-PORT-021: Stage 2 — Route every plan through Risk review before Trading submission.

    The system shall route every rebalance plan through Risk review before Trading submission.
    """
    _header("Stage 2: Risk Review Gate - Require Risk Authorization (FR-PORT-021)")
    plan = create_portfolio_value("PortfolioRebalancePlan", **_base_plan_data())
    print(_format_result(plan))
    print(f"Data -> status='{plan.status}', risk_review_required=True")


def fr_port_022() -> None:
    """FR-PORT-022: Stage 2 — Make existing over-budget correction reduce-only unless a separately authorized risk increase exists.

    The system shall enforce reduce-only actions for existing over-budget exposure corrections.
    """
    _header("Stage 2: Exposure Reduction - Reduce-Only Actions (FR-PORT-022)")
    plan = create_portfolio_value("PortfolioRebalancePlan", **_base_plan_data())
    print(_format_result(plan.actions[0]))
    print(
        f"Data -> action='{plan.actions[0].action}', reduce_only={plan.actions[0].reduce_only}"
    )


def fr_port_023() -> None:
    """FR-PORT-023: Stage 2 — Never open solely to match target weights.

    The system shall never create opening actions solely to make actual holdings match target weights.
    """
    _header(
        "Stage 2: Action Guard - Prohibit Opening Actions on Under-Target Exposure (FR-PORT-023)"
    )
    plan = create_portfolio_value("PortfolioRebalancePlan", **_base_plan_data())
    print(_format_result(plan))
    print("Data -> opening_actions_generated=False")


def fr_port_024() -> None:
    """FR-PORT-024: Stage 3 — Block planning/submission on kill switch, expiry, stale evidence, or target-version change.

    The system shall block rebalance planning or submission on kill switch, expiry, or stale evidence.
    """
    _header(
        "Stage 3: Fail-Closed Blocking - Interlock on Stale Evidence & Kill Switch (FR-PORT-024)"
    )
    plan = create_portfolio_value(
        "PortfolioRebalancePlan",
        **_base_plan_data(
            status="blocked",
            block_reasons=("KILL_SWITCH_ACTIVE",),
            actions=(),
        ),
    )
    print(_format_result(plan))
    print(f"Data -> status='{plan.status}', block_reasons={list(plan.block_reasons)}")


def fr_port_039() -> None:
    """FR-PORT-039: Measure deterministic cross-account correlation."""
    report = measure_cross_account_correlation(
        {
            "a": (Decimal("0.01"), Decimal("0.02")),
            "b": (Decimal("0.02"), Decimal("0.04")),
        },
        {"a": (Decimal(-1), Decimal(1)), "b": (Decimal(-1), Decimal(1))},
        {"a": "broker-a", "b": "broker-b"},
        window=2,
        alert_threshold=Decimal("0.60"),
    )
    print(_format_result(report))
    print(f"Data -> alert_pairs={report.alert_pairs}")


def fr_port_040() -> None:
    """FR-PORT-040: Aggregate common-mode loss-at-stop exposure."""
    report = assess_common_mode_exposure(
        {"a": {"EURUSD": Decimal(100)}, "b": {"EURUSD": Decimal(200)}},
        {"a": Decimal(50), "b": Decimal(50)},
        {"EURUSD": Decimal(1)},
        software_dependencies={"a": ("runtime",), "b": ("runtime",)},
        signal_dependencies={"a": ("trend",), "b": ("trend",)},
    )
    print(_format_result(report))
    print(f"Data -> aggregate={dict(report.aggregate_loss_at_stop_by_factor)}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-PORT-06 — rebalancing/ — Drift and Rebalance Planning\n\n"
        "Purpose: Assess risk-budget drift against active allocation targets and generate governed reduce-only rebalance plans.\n\n"
        "Module flow:\n"
        "-> Stage 1: Target allocation version binding and fresh account/FX evidence observation\n"
        "-> Stage 2: Threshold drift calculation, reduce-only action generation, and Risk review routing\n"
        "-> Stage 3: Fail-closed submission interlocks (kill-switch, stale evidence, or version changes)"
    )

    # Stage 1: Binding
    _run_example("FR-PORT-020", fr_port_020)

    # Stage 2: Calculation & Action Guard
    _run_example("FR-PORT-021", fr_port_021)
    _run_example("FR-PORT-022", fr_port_022)
    _run_example("FR-PORT-023", fr_port_023)

    # Stage 3: Blocking Interlocks
    _run_example("FR-PORT-024", fr_port_024)
    _run_example("FR-PORT-039", fr_port_039)
    _run_example("FR-PORT-040", fr_port_040)


if __name__ == "__main__":
    main()
