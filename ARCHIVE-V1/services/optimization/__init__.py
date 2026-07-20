"""Optimization service tool exports.

Purpose:
    Expose deterministic optimization and robustness tools from focused modules
    without placing implementation logic in this package initializer.

Classes and functions:
    optimization_tools.py tools: Functions. Parameter sweep, walk-forward,
        comparison, stability, overfit, ranking, persistence, and report tools.
    robustness_tools.py tools: Functions. Cost stress, Monte Carlo,
        cross-market/timeframe, out-of-sample, score, and report tools.
"""

from __future__ import annotations

from app.services.utils.standard import standardize_domain_exports

# optimization_tools.py tools
from .optimization_tools import (
    build_optimization_report,
    calculate_parameter_stability,
    compare_optimization_runs,
    detect_overfit_parameters,
    rank_parameter_sets,
    run_parameter_sweep,
    run_walk_forward_matrix,
    run_walk_forward_optimization,
    save_optimization_result,
)

# robustness_tools.py tools
from .robustness_tools import (
    build_robustness_report,
    calculate_robustness_score,
    run_combined_monte_carlo,
    run_commission_stress_test,
    run_cross_market_test,
    run_cross_timeframe_test,
    run_randomize_history_mc,
    run_randomize_parameters_mc,
    run_randomize_trade_order_mc,
    run_resample_trades_mc,
    run_second_oos_test,
    run_skip_trades_mc,
    run_slippage_stress_test,
    run_spread_stress_test,
    run_third_oos_test,
)

__version__ = "1.0.0"


__all__ = [
    # optimization_tools.py tools
    "build_optimization_report",
    "calculate_parameter_stability",
    "compare_optimization_runs",
    "detect_overfit_parameters",
    "rank_parameter_sets",
    "run_parameter_sweep",
    "run_walk_forward_matrix",
    "run_walk_forward_optimization",
    "save_optimization_result",
    # robustness_tools.py tools
    "build_robustness_report",
    "calculate_robustness_score",
    "run_combined_monte_carlo",
    "run_commission_stress_test",
    "run_cross_market_test",
    "run_cross_timeframe_test",
    "run_randomize_history_mc",
    "run_randomize_parameters_mc",
    "run_randomize_trade_order_mc",
    "run_resample_trades_mc",
    "run_second_oos_test",
    "run_skip_trades_mc",
    "run_slippage_stress_test",
    "run_spread_stress_test",
    "run_third_oos_test",
]


standardize_domain_exports(globals(), __all__, tool_category="optimization")
