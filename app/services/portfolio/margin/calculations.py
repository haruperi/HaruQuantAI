"""Decimal margin and buying-power policy."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal


def calculate_margin_view(
    *,
    equity: Decimal,
    margin_used: Decimal,
    reserved: Decimal,
    maintenance: Decimal,
    policy_version: str,
) -> Mapping[str, object]:
    """Build PortfolioMarginView v1 from explicit amounts.

    Returns:
        Versioned margin and buying-power evidence.
    """
    available = equity - margin_used - reserved
    leverage = None if equity <= 0 else (margin_used / equity)
    return {
        "schema": "PortfolioMarginView",
        "version": "v1",
        "policy_version": policy_version,
        "margin_used": str(margin_used),
        "available": str(available),
        "reserved": str(reserved),
        "maintenance": str(maintenance),
        "buying_power": str(max(available, Decimal(0))),
        "leverage": None if leverage is None else str(leverage),
        "liquidation_risk": available < maintenance,
    }
