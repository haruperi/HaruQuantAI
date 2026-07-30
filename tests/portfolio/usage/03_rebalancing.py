"""Executable Portfolio rebalancing usage example.

Demonstrates the drift and rebalance planning feature through the package-root
public API. Each functional requirement FR-PORT-020 through FR-PORT-024 has a
dedicated demonstration function.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import (
    assess_common_mode_exposure,
    create_portfolio_value,
    get_portfolio_value_field,
    measure_cross_account_correlation,
)

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


def _base_plan_data(**overrides: object) -> dict[str, object]:
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


def fr_port_020() -> None:
    """FR-PORT-020: Bind drift to an active allocation version and fresh
    actual-exposure evidence.

    Demonstrates that the rebalance plan carries an explicit allocation_version
    and observed_at timestamp binding it to its target.
    """
    _header(
        "FR-PORT-020: Bind drift to an active allocation version and fresh actual-exposure evidence. Demonstrates that the rebalance plan carries an explicit allocation_version and observed_at timestamp binding it to its target."
    )
    print("FR-PORT-020: Bind drift to active allocation version and fresh evidence")

    plan = create_portfolio_value("PortfolioRebalancePlan", **_base_plan_data())
    assert plan.allocation_version == "allocation-version-1"
    assert plan.observed_at.tzinfo is not None
    print(f"Bound to allocation_version: {plan.allocation_version}")
    print(f"Observed at UTC: {plan.observed_at}")


def fr_port_021() -> None:
    """FR-PORT-021: Route every plan through Risk review before Trading
    submission.

    Demonstrates that the plan starts in review_required status before Risk
    approval.
    """
    _header(
        "FR-PORT-021: Route every plan through Risk review before Trading submission. Demonstrates that the plan starts in review_required status before Risk approval."
    )
    print("FR-PORT-021: Route every plan through Risk review")

    plan = create_portfolio_value("PortfolioRebalancePlan", **_base_plan_data())
    assert plan.status == "review_required"
    print(f"Initial plan status: {plan.status}")
    print("Plan requires Risk review before Trading submission")


def fr_port_022() -> None:
    """FR-PORT-022: Make existing over-budget correction reduce-only unless a
    separately authorized risk increase exists.

    Demonstrates that every rebalance action is reduce-only.
    """
    _header(
        "FR-PORT-022: Make existing over-budget correction reduce-only unless a separately authorized risk increase exists. Demonstrates that every rebalance action is reduce-only."
    )
    print("FR-PORT-022: Make over-budget correction reduce-only")

    plan = create_portfolio_value("PortfolioRebalancePlan", **_base_plan_data())
    for action in plan.actions:
        assert action.reduce_only is True
        assert action.action == "reduce_exposure"
    print(f"All {len(plan.actions)} action(s) are reduce_only=True")


def fr_port_023() -> None:
    """FR-PORT-023: Never open solely to match target weights.

    Demonstrates that negative drift (under-target exposure) does not produce
    an action.
    """
    _header(
        "FR-PORT-023: Never open solely to match target weights. Demonstrates that negative drift (under-target exposure) does not produce an action."
    )
    print("FR-PORT-023: Never open solely to match target weights")

    plan = create_portfolio_value("PortfolioRebalancePlan", **_base_plan_data())
    action_ids = {a.component_id for a in plan.actions}
    for obs in plan.observations:
        if obs.drift < 0:
            assert obs.component_id not in action_ids
            print(
                f"  {obs.component_id}: under-target drift={obs.drift} "
                f"produces no action"
            )
    print("Under-target exposure does not create opening actions")


def fr_port_024() -> None:
    """FR-PORT-024: Block planning/submission on kill switch, expiry, stale
    evidence, or target-version change.

    Demonstrates that a blocked plan carries deterministic block reasons.
    """
    _header(
        "FR-PORT-024: Block planning/submission on kill switch, expiry, stale evidence, or target-version change. Demonstrates that a blocked plan carries deterministic block reasons."
    )
    print("FR-PORT-024: Block planning on kill switch or stale evidence")

    plan = create_portfolio_value(
        "PortfolioRebalancePlan",
        **_base_plan_data(
            status="blocked",
            block_reasons=("KILL_SWITCH_ACTIVE",),
            actions=(),
        ),
    )
    assert plan.status == "blocked"
    assert "KILL_SWITCH_ACTIVE" in plan.block_reasons
    print(f"Blocked status: {plan.status}")
    print(f"Block reasons: {', '.join(plan.block_reasons)}")


def fr_port_039() -> None:
    """FR-PORT-039: Measure rolling cross-account correlation."""
    _header("FR-PORT-039: Cross-account return and decision correlation")
    report = measure_cross_account_correlation(
        {
            "account-a": (Decimal("0.01"), Decimal("0.02"), Decimal("0.03")),
            "account-b": (Decimal("0.011"), Decimal("0.019"), Decimal("0.029")),
        },
        {
            "account-a": (Decimal(1), Decimal(1), Decimal(0)),
            "account-b": (Decimal(1), Decimal(1), Decimal(0)),
        },
        {"account-a": "broker-a", "account-b": "broker-b"},
        window=3,
        alert_threshold=Decimal("0.60"),
    )
    print(
        "Return correlation:",
        dict(get_portfolio_value_field(report, "return_correlation")),
    )
    print(
        "Decision correlation:",
        dict(get_portfolio_value_field(report, "decision_correlation")),
    )
    print("Alert pairs:", get_portfolio_value_field(report, "alert_pairs"))


def fr_port_040() -> None:
    """FR-PORT-040: Report common-mode loss-at-stop exposure."""
    _header("FR-PORT-040: Common-mode loss-at-stop exposure")
    report = assess_common_mode_exposure(
        {
            "account-a": {"equity_index": Decimal(80), "usd": Decimal(20)},
            "account-b": {"equity_index": Decimal(70)},
        },
        {"account-a": Decimal(50), "account-b": Decimal(100)},
        {"equity_index": Decimal(1), "usd": Decimal("0.5")},
        software_dependencies={
            "account-a": ("engine-v1",),
            "account-b": ("engine-v1",),
        },
        signal_dependencies={"account-a": ("signal-x",), "account-b": ("signal-x",)},
    )
    print(
        "Aggregate loss-at-stop by factor:",
        dict(get_portfolio_value_field(report, "aggregate_loss_at_stop_by_factor")),
    )
    print(
        "Breached accounts:",
        dict(get_portfolio_value_field(report, "breached_accounts")),
    )
    print(
        "Shared software:",
        dict(get_portfolio_value_field(report, "software_dependencies")),
    )
    print(
        "Shared signals:",
        dict(get_portfolio_value_field(report, "signal_dependencies")),
    )


def main() -> None:
    """Run every functional-requirement demonstration for Portfolio rebalancing."""
    fr_port_020()
    fr_port_021()
    fr_port_022()
    fr_port_023()
    fr_port_024()
    fr_port_039()
    fr_port_040()


if __name__ == "__main__":
    main()
