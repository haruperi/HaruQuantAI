"""Tests for Optimization Monte Carlo behavior."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.optimization.robustness import (
    calculate_confidence_intervals,
    calculate_probability_of_ruin,
    run_monte_carlo,
    run_parametric_simulation,
)
from tests.optimization.unit.test_robustness_contracts import monte_carlo_request


def test_run_monte_carlo_repeats_with_same_seed() -> None:
    """Identical seeded requests reproduce every path summary."""
    request = monte_carlo_request()
    assert run_monte_carlo(request, max_simulations=10) == run_monte_carlo(
        request, max_simulations=10
    )


def test_calculate_probability_of_ruin_known_fixture() -> None:
    """Empirical ruin probability counts values at or below the threshold."""
    assert (
        calculate_probability_of_ruin(
            (Decimal(10), Decimal(5), Decimal(2)),
            ruin_threshold=Decimal(5),
        )
        == 2 / 3
    )


def test_calculate_confidence_intervals_known_fixture() -> None:
    """Type-seven interpolation returns the known central interval."""
    assert calculate_confidence_intervals(
        tuple(Decimal(index) for index in range(1, 6)), confidence_level=0.8
    ) == (Decimal("1.4"), Decimal("4.6"))


def test_parametric_simulation_handles_all_win_and_all_loss() -> None:
    """All-win and all-loss assumptions compound in opposite directions."""
    common = {
        "reward_risk": Decimal(1),
        "risk_per_trade": Decimal("0.1"),
        "trade_count": 2,
        "simulations": 1,
        "initial_balance": Decimal(100),
        "seed": 7,
        "max_simulations": 2,
    }
    winners = run_parametric_simulation(win_rate=Decimal(1), **common)
    losers = run_parametric_simulation(win_rate=Decimal(0), **common)
    assert winners.final_equity == (Decimal("121.00"),)
    assert losers.final_equity == (Decimal("81.00"),)
