"""Approved typed Optimization operations."""

from app.services.optimization.public_api.operations import (
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

_OFFICIAL_OPTIMIZATION_TOOLS = (
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


def get_official_optimization_tools() -> tuple[str, ...]:
    """Return approved Optimization official operation names."""
    return _OFFICIAL_OPTIMIZATION_TOOLS


__all__ = (
    "build_optimization_handoff",
    "calculate_parameter_stability",
    "calculate_robustness_score",
    "compare_optimization_runs",
    "detect_overfit_parameters",
    "get_official_optimization_tools",
    "rank_parameter_sets",
    "run_parameter_sweep",
    "run_robustness_analysis",
    "run_walk_forward_matrix",
    "run_walk_forward_optimization",
)
