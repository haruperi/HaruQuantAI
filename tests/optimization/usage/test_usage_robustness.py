"""Runnable usage evidence for Optimization robustness requirements."""

from decimal import Decimal

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


def test_usage_contracts_monte_carlo_method() -> None:
    """Select an approved Monte Carlo method."""
    assert MonteCarloMethod.BLOCK_BOOTSTRAP.value == "block_bootstrap"


def test_usage_contracts_monte_carlo_request() -> None:
    """Construct a complete seeded request."""
    assert monte_carlo_request().seed == 17


def test_usage_contracts_monte_carlo_result() -> None:
    """Consume immutable reproducible result evidence."""
    result = run_monte_carlo(monte_carlo_request(), max_simulations=10)
    assert isinstance(result, MonteCarloResult)


def test_usage_contracts_execution_stress_request() -> None:
    """Construct an explicit absolute commission stress."""
    request = ExecutionStressRequest(kind="commission", value=Decimal(1))
    assert request.value == Decimal(1)


def test_usage_monte_carlo_run_monte_carlo() -> None:
    """Run a bounded seeded empirical simulation."""
    assert run_monte_carlo(monte_carlo_request(), max_simulations=5).simulations == 5


def test_usage_monte_carlo_calculate_probability_of_ruin() -> None:
    """Calculate empirical ruin evidence in supplied units."""
    assert (
        calculate_probability_of_ruin(
            (Decimal(1), Decimal(2)), ruin_threshold=Decimal(1)
        )
        == 0.5
    )


def test_usage_monte_carlo_calculate_confidence_intervals() -> None:
    """Calculate a caller-selected empirical interval."""
    lower, upper = calculate_confidence_intervals(
        (Decimal(1), Decimal(2)), confidence_level=0.5
    )
    assert lower < upper


def test_usage_monte_carlo_run_parametric_simulation() -> None:
    """Run a bounded parametric scenario."""
    result = run_parametric_simulation(
        win_rate=Decimal("0.5"),
        reward_risk=Decimal(1),
        risk_per_trade=Decimal("0.01"),
        trade_count=2,
        simulations=2,
        initial_balance=Decimal(100),
        seed=3,
        max_simulations=2,
    )
    assert len(result.final_equity) == 2


def test_usage_stress_apply_execution_cost_stress() -> None:
    """Apply an absolute same-unit execution cost."""
    result = apply_execution_cost_stress(
        ({"pnl": Decimal(2)},),
        ExecutionStressRequest(kind="spread", value=Decimal("0.5")),
    )
    assert result[0]["pnl"] == Decimal("1.5")


def test_usage_assessment_assess_strategy_robustness() -> None:
    """Combine only applicable supplied robustness checks."""
    result = assess_strategy_robustness(
        monte_carlo=None,
        stress_checks=({"name": "spread", "passed": True},),
    )
    assert result["applicable_check_count"] == 1
