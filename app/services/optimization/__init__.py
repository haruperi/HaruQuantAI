"""Approved public port for the complete Optimization domain."""

from app.services.optimization.public_api import (
    build_optimization_handoff,
    calculate_parameter_stability,
    calculate_robustness_score,
    compare_optimization_runs,
    detect_overfit_parameters,
    rank_parameter_sets,
    run_parameter_sweep,
    run_robustness_analysis,
    run_walk_forward_matrix,
    run_walk_forward_optimization,
)
from app.services.optimization.robustness import (
    FirstPassageReport,
    JointFirstPassageReport,
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
)

OFFICIAL_OPTIMIZATION_TOOLS = (
    "build_optimization_handoff",
    "calculate_parameter_stability",
    "calculate_robustness_score",
    "compare_optimization_runs",
    "detect_overfit_parameters",
    "rank_parameter_sets",
    "run_parameter_sweep",
    "run_robustness_analysis",
    "run_walk_forward_matrix",
    "run_walk_forward_optimization",
)

__all__ = (
    "OFFICIAL_OPTIMIZATION_TOOLS",
    "FirstPassageReport",
    "JointFirstPassageReport",
    "build_optimization_handoff",
    "calculate_parameter_stability",
    "calculate_robustness_score",
    "compare_optimization_runs",
    "detect_overfit_parameters",
    "estimate_drawdown_mode_sensitivity",
    "estimate_first_passage",
    "estimate_joint_first_passage",
    "rank_parameter_sets",
    "run_parameter_sweep",
    "run_robustness_analysis",
    "run_walk_forward_matrix",
    "run_walk_forward_optimization",
)
