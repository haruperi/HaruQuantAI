"""Supported Optimization robustness API."""

from app.services.optimization.robustness.assessment import assess_strategy_robustness
from app.services.optimization.robustness.barrier import (
    FirstPassageReport,
    JointFirstPassageReport,
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
)
from app.services.optimization.robustness.contracts import (
    ExecutionStressRequest,
    MonteCarloMethod,
    MonteCarloRequest,
    MonteCarloResult,
)
from app.services.optimization.robustness.monte_carlo import (
    calculate_confidence_intervals,
    calculate_probability_of_ruin,
    run_monte_carlo,
    run_parametric_simulation,
)
from app.services.optimization.robustness.stress import apply_execution_cost_stress

__all__ = [
    "ExecutionStressRequest",
    "FirstPassageReport",
    "JointFirstPassageReport",
    "MonteCarloMethod",
    "MonteCarloRequest",
    "MonteCarloResult",
    "apply_execution_cost_stress",
    "assess_strategy_robustness",
    "calculate_confidence_intervals",
    "calculate_probability_of_ruin",
    "estimate_drawdown_mode_sensitivity",
    "estimate_first_passage",
    "estimate_joint_first_passage",
    "run_monte_carlo",
    "run_parametric_simulation",
]
