"""Executable Optimization robustness usage example.

Demonstrates Monte Carlo simulations, execution stress testing, confidence interval calculation,
probability of ruin, and strategy robustness assessment.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization.robustness import (
    ExecutionStressRequest,
    MonteCarloMethod,
    MonteCarloResult,
    apply_execution_cost_stress,
    assess_strategy_robustness,
    calculate_confidence_intervals,
    calculate_probability_of_ruin,
    run_monte_carlo,
    run_parametric_simulation,
)
from tests.optimization.unit.test_robustness_contracts import monte_carlo_request


def example_robustness() -> None:
    """Demonstrate robustness analysis tools."""
    print("=" * 80)
    print("Optimization Example 5: Robustness Analysis and Stress Testing")
    print("=" * 80)

    # 1. Monte Carlo method
    print(f"Monte Carlo method: {MonteCarloMethod.BLOCK_BOOTSTRAP.value}")

    # 2. Run Monte Carlo simulation
    req = monte_carlo_request()
    mc_res = run_monte_carlo(req, max_simulations=5)
    print(
        f"Monte Carlo simulation count: {mc_res.simulations}, is MonteCarloResult: {isinstance(mc_res, MonteCarloResult)}"
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
        f"Parametric simulation final equity points count: {len(param_res.final_equity)}"
    )

    # 5. Execution stress request & stress application
    stress_req = ExecutionStressRequest(kind="spread", value=Decimal("0.5"))
    stressed_outcomes = apply_execution_cost_stress(({"pnl": Decimal(2)},), stress_req)
    print(f"Stressed PnL after spread stress: {stressed_outcomes[0]['pnl']}")

    # 6. Overall robustness assessment
    assessment = assess_strategy_robustness(
        monte_carlo=None,
        stress_checks=({"name": "spread", "passed": True},),
    )
    print(f"Applicable robustness check count: {assessment['applicable_check_count']}")


def main() -> None:
    """Run Optimization robustness usage example."""
    example_robustness()


if __name__ == "__main__":
    main()
