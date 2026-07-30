"""Executable Optimization robustness usage example.

Demonstrates Monte Carlo simulations, execution stress testing, confidence
interval calculation,
probability of ruin, and strategy robustness assessment.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization import (
    apply_execution_cost_stress,
    assess_strategy_robustness,
    calculate_confidence_intervals,
    calculate_probability_of_ruin,
    create_optimization_value,
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
    run_monte_carlo,
    run_parametric_simulation,
)
from app.services.risk import create_firm_mandate
from tests.optimization.usage._support import monte_carlo_request

RETURNS = (Decimal("0.02"), Decimal("-0.01"), Decimal("0.015"), Decimal("-0.005"))


def _mandate(account_id: str = "account-1") -> object:
    """Build a bounded verified mandate through Risk's public API."""
    return create_firm_mandate(
        account_id=account_id,
        mandate_version="2026.07.28-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="evaluation_p1",
        initial_balance=Decimal(1000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash="a" * 64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.1")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.05"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.1"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
    )


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_robustness() -> None:
    """Demonstrate robustness analysis tools."""
    _header("Demonstrate robustness analysis tools.")
    print("Optimization Example 5: Robustness Analysis and Stress Testing")

    # 1. Monte Carlo method
    print(f"Monte Carlo method: {monte_carlo_request().method}")

    # 2. Run Monte Carlo simulation
    req = monte_carlo_request()
    mc_res = run_monte_carlo(req, max_simulations=5)
    print(
        f"Monte Carlo simulation count: {mc_res.simulations}, method: {mc_res.method}"
    )

    # 3. Probability of ruin & confidence intervals
    p_ruin = calculate_probability_of_ruin(
        (Decimal(1), Decimal(2)), ruin_threshold=Decimal(1)
    )
    print(f"Calculated probability of ruin: {p_ruin}")

    lower, upper = calculate_confidence_intervals(
        (Decimal(1), Decimal(2)), confidence_level=0.5
    )
    print(f"Confidence interval 50%: [{lower}, {upper}]")

    # 4. Parametric simulation
    param_res = run_parametric_simulation(
        win_rate=Decimal("0.5"),
        reward_risk=Decimal(1),
        risk_per_trade=Decimal("0.01"),
        trade_count=2,
        simulations=2,
        initial_balance=Decimal(100),
        seed=3,
        max_simulations=2,
    )
    print(
        "Parametric simulation final equity points count: "
        f"{len(param_res.final_equity)}"
    )

    # 5. Execution stress request & stress application
    stress_req = create_optimization_value(
        "ExecutionStressRequest", kind="spread", value=Decimal("0.5")
    )
    stressed_outcomes = apply_execution_cost_stress(({"pnl": Decimal(2)},), stress_req)
    print(f"Stressed PnL after spread stress: {stressed_outcomes[0]['pnl']}")

    # 6. Overall robustness assessment
    assessment = assess_strategy_robustness(
        monte_carlo=None,
        stress_checks=({"name": "spread", "passed": True},),
    )
    print(f"Applicable robustness check count: {assessment['applicable_check_count']}")

    # 7. Prop-firm absorbing-barrier evidence
    first_passage = estimate_first_passage(RETURNS, _mandate(), paths=100, seed=7)
    joint = estimate_joint_first_passage(
        {
            "account-1": RETURNS,
            "account-2": (
                Decimal("0.011"),
                Decimal("-0.004"),
                Decimal("0.018"),
                Decimal("-0.009"),
            ),
        },
        {"account-1": _mandate(), "account-2": _mandate("account-2")},
        paths=100,
        seed=7,
    )
    sensitivity = estimate_drawdown_mode_sensitivity(
        RETURNS, _mandate(), paths=100, seed=7
    )
    print(
        "Barrier evidence:",
        {
            "target_probability": first_passage.probability_target,
            "none_survive_probability": joint.probability_none_survive,
            "drawdown_modes": tuple(sensitivity),
        },
    )


def main() -> None:
    """Run Optimization robustness usage example."""
    example_robustness()


if __name__ == "__main__":
    main()
