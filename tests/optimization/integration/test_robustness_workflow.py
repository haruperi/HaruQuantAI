"""Integration test for the complete robustness workflow."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.optimization.robustness import (
    ExecutionStressRequest,
    apply_execution_cost_stress,
    assess_strategy_robustness,
    run_monte_carlo,
)
from tests.optimization.unit.test_robustness_contracts import monte_carlo_request


def test_robustness_workflow_is_seeded_and_availability_aware() -> None:
    """Seeded paths and explicit stress feed one assessment."""
    monte_carlo = run_monte_carlo(monte_carlo_request(), max_simulations=5)
    stressed = apply_execution_cost_stress(
        ({"pnl": Decimal(3)},),
        ExecutionStressRequest(kind="slippage", value=Decimal(1)),
    )
    assessment = assess_strategy_robustness(
        monte_carlo=monte_carlo,
        stress_checks=({"name": "slippage", "passed": stressed[0]["pnl"] > 0},),
    )
    assert assessment["monte_carlo_available"] is True
    assert assessment["robustness_percentage"] == 100.0
