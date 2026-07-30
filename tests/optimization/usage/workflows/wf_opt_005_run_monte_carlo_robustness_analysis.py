"""WF-OPT-005: run Monte Carlo and robustness analysis."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    apply_execution_cost_stress,
    assess_strategy_robustness,
    calculate_confidence_intervals,
    calculate_probability_of_ruin,
    create_optimization_value,
    run_monte_carlo,
)
from app.utils import flush_logging
from tests.optimization.usage._support import monte_carlo_request

WORKFLOW_ID = "WF-OPT-005"
STAGES = (
    "Receive realized outcomes or validated parametric inputs and deterministic seed.",
    "Run the selected bounded Monte Carlo method with deterministic sub-seeds.",
    "Calculate probability of ruin and confidence intervals.",
    "Apply explicit execution-cost stress assumptions.",
    "Assess applicable evidence and return caveated robustness results.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented robustness workflow."""
    print(f"{WORKFLOW_ID} — Run Monte Carlo and Robustness Analysis")
    print("INPUT BOUNDARY — supplied realized outcomes and deterministic seed")

    # Stage 1 — Receive realized outcomes or validated parametric inputs and deterministic seed.
    _stage(1)
    request = monte_carlo_request()
    outcomes = (Decimal(1), Decimal(2), Decimal("-0.5"))

    # Stage 2 — Run the selected bounded Monte Carlo method with deterministic sub-seeds.
    _stage(2)
    monte_carlo = run_monte_carlo(request, max_simulations=5)

    # Stage 3 — Calculate probability of ruin and confidence intervals.
    _stage(3)
    ruin = calculate_probability_of_ruin(outcomes, ruin_threshold=Decimal(1))
    interval = calculate_confidence_intervals(outcomes, confidence_level=0.5)

    # Stage 4 — Apply explicit execution-cost stress assumptions.
    _stage(4)
    stressed = apply_execution_cost_stress(
        ({"pnl": Decimal(2)},),
        create_optimization_value(
            "ExecutionStressRequest", kind="spread", value=Decimal("0.5")
        ),
    )

    # Stage 5 — Assess applicable evidence and return caveated robustness results.
    _stage(5)
    assessment = assess_strategy_robustness(
        monte_carlo=monte_carlo,
        stress_checks=({"name": "spread", "passed": stressed[0]["pnl"] > 0},),
    )
    print(
        "OUTPUT BOUNDARY — Monte Carlo/ruin/CI/stress/assessment:",
        monte_carlo.simulations,
        ruin,
        interval,
        assessment["applicable_check_count"],
    )


if __name__ == "__main__":
    main()
    flush_logging()
