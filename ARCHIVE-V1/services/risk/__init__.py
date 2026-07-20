"""Risk service tool exports.

Purpose:
    Expose the agent-facing risk tool functions from their focused modules.
    Business implementation lives in the source modules, while this initializer
    stays as a readable export surface.

Functions:
    Risk governor tools from governor_tools.py.
    Portfolio analytics tools from portfolio_tools.py.
    Allocation tools from allocation_tools.py.
    Portfolio lifecycle tools from lifecycle_tools.py.
"""

from __future__ import annotations

# allocation_tools.py tools
from app.services.risk.allocation_tools import (
    calculate_correlation_adjusted_size,
    calculate_cost_adjusted_size,
    calculate_fixed_fractional_size,
    calculate_margin_aware_size,
    calculate_max_safe_position_size,
    calculate_risk_parity_weights,
    calculate_volatility_adjusted_size,
    propose_strategy_allocation,
    rebalance_strategy_allocations,
    validate_allocation_proposal,
)

# governor_tools.py tools
from app.services.risk.governor_tools import (
    check_correlation_limit,
    check_currency_exposure_limit,
    check_cvar_limit,
    check_daily_loss_limit,
    check_kill_switch_state,
    check_leverage_limit,
    check_margin_limit,
    check_max_drawdown_limit,
    check_news_blackout,
    check_portfolio_exposure_limit,
    check_slippage_limit,
    check_spread_limit,
    check_strategy_loss_limit,
    check_symbol_exposure_limit,
    check_trade_frequency_limit,
    check_var_limit,
    run_risk_governor_checks,
)

# lifecycle_tools.py tools
from app.services.risk.lifecycle_tools import (
    admit_strategy_to_portfolio,
    build_risk_decision_package,
    demote_strategy_to_paper,
    promote_strategy_to_live_candidate,
    promote_strategy_to_paper,
    retire_strategy,
    suspend_strategy,
    update_strategy_status,
)

# portfolio_tools.py tools
from app.services.risk.portfolio_tools import (
    build_portfolio_risk_snapshot,
    calculate_currency_exposure,
    calculate_margin_usage,
    calculate_portfolio_correlation,
    calculate_portfolio_cvar,
    calculate_portfolio_returns,
    calculate_portfolio_var,
    calculate_portfolio_volatility,
    calculate_risk_contribution,
    detect_strategy_overlap,
    detect_symbol_cluster_risk,
    get_open_orders,
    get_open_positions,
    get_portfolio_equity_curve,
    get_strategy_allocations,
)
from app.services.utils.standard import standardize_domain_exports

__all__ = [
    "admit_strategy_to_portfolio",
    "build_portfolio_risk_snapshot",
    "build_risk_decision_package",
    "calculate_correlation_adjusted_size",
    "calculate_cost_adjusted_size",
    "calculate_currency_exposure",
    "calculate_fixed_fractional_size",
    "calculate_margin_aware_size",
    "calculate_margin_usage",
    "calculate_max_safe_position_size",
    "calculate_portfolio_correlation",
    "calculate_portfolio_cvar",
    "calculate_portfolio_returns",
    "calculate_portfolio_var",
    "calculate_portfolio_volatility",
    "calculate_risk_contribution",
    "calculate_risk_parity_weights",
    "calculate_volatility_adjusted_size",
    "check_correlation_limit",
    "check_currency_exposure_limit",
    "check_cvar_limit",
    "check_daily_loss_limit",
    "check_kill_switch_state",
    "check_leverage_limit",
    "check_margin_limit",
    "check_max_drawdown_limit",
    "check_news_blackout",
    "check_portfolio_exposure_limit",
    "check_slippage_limit",
    "check_spread_limit",
    "check_strategy_loss_limit",
    "check_symbol_exposure_limit",
    "check_trade_frequency_limit",
    "check_var_limit",
    "demote_strategy_to_paper",
    "detect_strategy_overlap",
    "detect_symbol_cluster_risk",
    "get_open_orders",
    "get_open_positions",
    "get_portfolio_equity_curve",
    "get_strategy_allocations",
    "promote_strategy_to_live_candidate",
    "promote_strategy_to_paper",
    "propose_strategy_allocation",
    "rebalance_strategy_allocations",
    "retire_strategy",
    "run_risk_governor_checks",
    "suspend_strategy",
    "update_strategy_status",
    "validate_allocation_proposal",
]


standardize_domain_exports(globals(), __all__, tool_category="risk")
