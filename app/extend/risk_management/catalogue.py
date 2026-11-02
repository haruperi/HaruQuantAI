"""Catalog registry and descriptors for StrategyQuant risk management methods.

Description:
    Provides metadata, parameter specifications, and factory lookup for
    StrategyQuant risk management method definitions matching donor classes
    in SQ.RiskManagement and com.strategyquant.tradinglib.riskmanagement.

Purpose:
    FEAT-RISK-MANAGEMENT: StrategyQuant donor-faithful risk management methods.

Key Capabilities:
    - FR-risk-management-catalogue: Descriptors for risk methods.

Python API Usage:
    from app.extend.risk_management.catalogue import (
        create_risk_management_method,
        list_risk_management_methods,
    )
    methods = list_risk_management_methods()
    rm = create_risk_management_method("AllowAllTrades")

CLI Usage:
    python -m app.cli risk-management list
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.extend.risk_management.allow_all_trades import AllowAllTrades
from app.extend.risk_management.base import RiskManagementMethod

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RiskManagementDescriptor:
    """Metadata descriptor for a risk management method snippet."""

    class_name: str
    display_name: str
    category: str
    sort_order: int
    donor_source: str
    description: str
    parameters: tuple[dict[str, Any], ...]


RISK_MANAGEMENT_CATALOGUE: dict[str, RiskManagementDescriptor] = {
    "AllowAllTrades": RiskManagementDescriptor(
        class_name="AllowAllTrades",
        display_name="Allow all trades",
        category="RiskManagement",
        sort_order=100,
        donor_source="SQ.RiskManagement.AllowAllTrades",
        description="Every trade will be allowed.",
        parameters=(),
    ),
}

_CONSTRUCTORS: dict[str, type[RiskManagementMethod]] = {
    "AllowAllTrades": AllowAllTrades,
    "Allow all trades": AllowAllTrades,
}


def get_risk_management_method(name: str) -> type[RiskManagementMethod]:
    """Look up a risk management method class by name.

    Args:
        name: Class name or display name.

    Returns:
        RiskManagementMethod subclass.

    Raises:
        KeyError: If method name is not found in registry.
    """
    cls = _CONSTRUCTORS.get(name)
    if cls is None:
        logger.error(
            "FR-risk-management-catalogue: unknown risk management method %s", name
        )
        raise KeyError(f"Unknown risk management method: {name}")
    logger.debug("FR-risk-management-catalogue: resolved %s -> %s", name, cls.__name__)
    return cls


def list_risk_management_methods() -> list[RiskManagementDescriptor]:
    """Return all risk management method descriptors sorted by sort_order.

    Returns:
        List of risk management method descriptors.
    """
    return sorted(RISK_MANAGEMENT_CATALOGUE.values(), key=lambda d: d.sort_order)


def create_risk_management_method(name: str, **kwargs: Any) -> RiskManagementMethod:
    """Instantiate a risk management method by name.

    Args:
        name: Name or alias of the risk management method.
        **kwargs: Arguments passed to class constructor.

    Returns:
        Instantiated RiskManagementMethod instance.

    Raises:
        KeyError: If risk management method name is not registered.
    """
    cls = get_risk_management_method(name)
    instance = cls(**kwargs)
    logger.debug(
        "FR-risk-management-catalogue: created instance of %s with params=%s",
        cls.__name__,
        kwargs,
    )
    return instance
