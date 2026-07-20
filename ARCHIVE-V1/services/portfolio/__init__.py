"""Expose Portfolio Department service classes and tool functions.

Purpose:
    Expose Portfolio Department service classes and tool functions.

Classes:
    None.

Functions:
    __getattr__: Internal helper function defined by this module.

Notes:
    External-facing exports are collected in app/services/portfolio/__init__.py;
    private underscore helpers remain implementation details.
"""

from importlib import import_module
from typing import Any

from app.services.utils.standard import (
    standardize_domain_exports,
    standardize_tool_callable,
)

_SERVICE_EXPORTS = {
    "AllocationService": "allocation_service",
    "CostService": "cost_service",
    "IncidentService": "incident_service",
    "PortfolioAuditService": "audit_service",
    "PortfolioKillSwitch": "kill_switch",
    "LifecycleService": "lifecycle_service",
    "ReportingService": "reporting_service",
}


def __getattr__(name: str) -> Any:
    """Load optional portfolio service classes only when requested."""
    module_name = _SERVICE_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(name)
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    if callable(value) and not isinstance(value, type):
        value = standardize_tool_callable(
            value,
            tool_name=name,
            tool_category="portfolio",
        )
    globals()[name] = value
    return value


# standard_tools.py tools
from .standard_tools import (
    admit_strategy_to_portfolio,
    build_portfolio_risk_snapshot,
    build_risk_decision_package,
    calculate_correlation_adjusted_size,
    calculate_cost_adjusted_size,
    calculate_currency_exposure,
    calculate_fixed_fractional_size,
    calculate_margin_aware_size,
    calculate_margin_usage,
    calculate_max_safe_position_size,
    calculate_portfolio_correlation,
    calculate_portfolio_cvar,
    calculate_portfolio_returns,
    calculate_portfolio_var,
    calculate_portfolio_volatility,
    calculate_risk_contribution,
    calculate_risk_parity_weights,
    calculate_volatility_adjusted_size,
    demote_strategy_to_paper,
    detect_strategy_overlap,
    detect_symbol_cluster_risk,
    get_open_orders,
    get_open_positions,
    get_portfolio_equity_curve,
    get_strategy_allocations,
    promote_strategy_to_live_candidate,
    promote_strategy_to_paper,
    propose_strategy_allocation,
    rebalance_strategy_allocations,
    retire_strategy,
    suspend_strategy,
    update_strategy_status,
    validate_allocation_proposal,
)

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
    "suspend_strategy",
    "update_strategy_status",
    "validate_allocation_proposal",
]


standardize_domain_exports(globals(), __all__, tool_category="portfolio")
