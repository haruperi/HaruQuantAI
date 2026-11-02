"""Risk management extension snippets package.

Description:
    Provides StrategyQuant-compatible risk management methods for pre-trade
    verification and order permission checks matching SQ.RiskManagement snippets.

Purpose:
    FEAT-RISK-MANAGEMENT: StrategyQuant donor-faithful risk management methods.

Key Capabilities:
    - FR-risk-management-base: Risk management method base contract.
    - FR-risk-management-allow-all: Unconditional order approval policy.
    - FR-risk-management-catalogue: Catalog registry and lookup functions.

Python API Usage:
    from app.extend.risk_management import (
        AllowAllTrades,
        RiskManagementMethod,
        create_risk_management_method,
        get_risk_management_method,
        list_risk_management_methods,
    )

CLI Usage:
    python -m app.cli risk-management list
"""

from __future__ import annotations

from app.extend.risk_management.allow_all_trades import AllowAllTrades
from app.extend.risk_management.base import RiskManagementMethod
from app.extend.risk_management.catalogue import (
    RISK_MANAGEMENT_CATALOGUE,
    RiskManagementDescriptor,
    create_risk_management_method,
    get_risk_management_method,
    list_risk_management_methods,
)

__all__ = [
    "RISK_MANAGEMENT_CATALOGUE",
    "AllowAllTrades",
    "RiskManagementDescriptor",
    "RiskManagementMethod",
    "create_risk_management_method",
    "get_risk_management_method",
    "list_risk_management_methods",
]
