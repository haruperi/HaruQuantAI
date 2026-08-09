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
from app.services.optimization.robustness.risk_sensitivity import (
    evaluate_risk_sensitivity,
    get_risk_sensitivity_contract_version,
    summarize_drawdown_threshold_sensitivity,
)
from app.services.optimization.robustness.stress import apply_execution_cost_stress
from app.services.optimization.robustness.stress_calibration import (
    StressProfileCalibrationPort,
    get_stress_calibration_contract_version,
    resolve_stress_profile_calibration,
)

__all__ = [
    "ExecutionStressRequest",
    "FirstPassageReport",
    "JointFirstPassageReport",
    "MonteCarloMethod",
    "MonteCarloRequest",
    "MonteCarloResult",
    "StressProfileCalibrationPort",
    "apply_execution_cost_stress",
    "assess_strategy_robustness",
    "calculate_confidence_intervals",
    "calculate_probability_of_ruin",
    "estimate_drawdown_mode_sensitivity",
    "estimate_first_passage",
    "estimate_joint_first_passage",
    "evaluate_risk_sensitivity",
    "get_risk_sensitivity_contract_version",
    "get_stress_calibration_contract_version",
    "resolve_stress_profile_calibration",
    "run_monte_carlo",
    "run_parametric_simulation",
    "summarize_drawdown_threshold_sensitivity",
]
