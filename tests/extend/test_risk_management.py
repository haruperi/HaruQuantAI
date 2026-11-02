"""Tests for StrategyQuant-compatible risk management methods.

Description:
    Validates the RiskManagementMethod base class, AllowAllTrades snippet,
    catalogue registry, serialization, and error handling with full branch coverage.

Purpose:
    FEAT-RISK-MANAGEMENT: StrategyQuant donor-faithful risk management methods.

Key Capabilities:
    - FR-risk-management-base: Risk management method base contract.
    - FR-risk-management-allow-all: Unconditional order approval policy.
    - FR-risk-management-catalogue: Catalog registry and descriptors.

Python API Usage:
    pytest tests/extend/test_risk_management.py

CLI Usage:
    python -m pytest tests/extend/test_risk_management.py -v
"""

from __future__ import annotations

from typing import Any, override

import app.extend.risk_management as rm_pkg
import pytest
from app.extend.risk_management.allow_all_trades import AllowAllTrades
from app.extend.risk_management.base import RiskManagementMethod
from app.extend.risk_management.catalogue import (
    RISK_MANAGEMENT_CATALOGUE,
    create_risk_management_method,
    get_risk_management_method,
    list_risk_management_methods,
)


class _DummyRejectRiskMethod(RiskManagementMethod):
    """Test stub for rejecting risk management method."""

    @override
    def verify_order(
        self, order: Any = None, trader: Any = None, **kwargs: Any
    ) -> bool:
        return False


class _DummyApproveRiskMethod(RiskManagementMethod):
    """Test stub for approving risk management method inheriting base verifyOrder."""

    @override
    def verify_order(
        self, order: Any = None, trader: Any = None, **kwargs: Any
    ) -> bool:
        return True


def test_base_risk_management_method_defaults_and_accessors() -> None:
    """Verify base method attributes, getters, setters, and serialization."""
    method = _DummyRejectRiskMethod(equity=50000.0, decimals=4)
    assert method.get_equity() == 50000.0
    assert method.get_decimals() == 4
    assert method.name == "RiskManagementMethod"

    method.set_name("Custom Risk Filter")
    assert method.name == "Custom Risk Filter"

    serialized = method.to_dict()
    assert serialized["name"] == "Custom Risk Filter"
    assert serialized["display"] == "Risk Management Method"
    assert serialized["equity"] == 50000.0
    assert serialized["decimals"] == 4
    assert serialized["category"] == "RiskManagement"
    assert serialized["parameters"] == {}


def test_base_risk_management_method_verify_order_rejection() -> None:
    """Verify verifyOrder raises ValueError when verify_order returns False."""
    rejector = _DummyRejectRiskMethod(name="Rejector")
    assert rejector.verify_order() is False

    with pytest.raises(
        ValueError, match="Order rejected by risk management method: Rejector"
    ):
        rejector.verifyOrder(trader="MockTrader", order="MockOrder")


def test_base_risk_management_method_verify_order_approval() -> None:
    """Verify base verifyOrder passes when verify_order returns True."""
    approver = _DummyApproveRiskMethod(name="Approver")
    assert approver.verify_order() is True
    approver.verifyOrder(trader="Trader1", order="Order1")


def test_allow_all_trades_attributes() -> None:
    """Verify AllowAllTrades snippet metadata matching donor ClassConfig and Help."""
    rm = AllowAllTrades()
    assert rm.name == "Allow all trades"
    assert rm.display == "Allow all trades"
    assert rm.help == "Every trade will be allowed."
    assert rm.category == "RiskManagement"
    assert rm.sort_order == 100
    assert rm.get_equity() == 0.0
    assert rm.get_decimals() == 2


def test_allow_all_trades_verify_order_approves_unconditionally() -> None:
    """Verify that AllowAllTrades permits all orders under both API contracts."""
    rm = AllowAllTrades()

    # Generic pythonic verify_order
    assert rm.verify_order() is True
    assert rm.verify_order(order={"symbol": "EURUSD", "volume": 1.0}) is True
    assert (
        rm.verify_order(
            order={"symbol": "GBPUSD", "volume": 5.0},
            trader={"account_id": "test_acc"},
            extra_param=True,
        )
        is True
    )

    # Donor Java parity verifyOrder (no-op, does not raise)
    rm.verifyOrder(trader="Trader1", order="Order1")


def test_catalogue_registry_and_lookup() -> None:
    """Verify catalogue contains AllowAllTrades and resolves by name and display name."""
    assert "AllowAllTrades" in RISK_MANAGEMENT_CATALOGUE
    descriptor = RISK_MANAGEMENT_CATALOGUE["AllowAllTrades"]
    assert descriptor.class_name == "AllowAllTrades"
    assert descriptor.display_name == "Allow all trades"
    assert descriptor.category == "RiskManagement"
    assert descriptor.donor_source == "SQ.RiskManagement.AllowAllTrades"
    assert descriptor.description == "Every trade will be allowed."
    assert descriptor.parameters == ()

    # Lookup by class name
    cls1 = get_risk_management_method("AllowAllTrades")
    assert cls1 is AllowAllTrades

    # Lookup by display name
    cls2 = get_risk_management_method("Allow all trades")
    assert cls2 is AllowAllTrades

    # Unknown lookup raises KeyError
    with pytest.raises(KeyError, match="Unknown risk management method: NonExistent"):
        get_risk_management_method("NonExistent")


def test_catalogue_list_and_create() -> None:
    """Verify list_risk_management_methods and create_risk_management_method."""
    methods = list_risk_management_methods()
    assert len(methods) >= 1
    assert any(m.class_name == "AllowAllTrades" for m in methods)

    instance = create_risk_management_method("AllowAllTrades", equity=25000.0)
    assert isinstance(instance, AllowAllTrades)
    assert instance.get_equity() == 25000.0

    with pytest.raises(KeyError, match="Unknown risk management method: InvalidRM"):
        create_risk_management_method("InvalidRM")


def test_package_exports() -> None:
    """Verify package __all__ exports."""
    expected_exports = {
        "AllowAllTrades",
        "RISK_MANAGEMENT_CATALOGUE",
        "RiskManagementDescriptor",
        "RiskManagementMethod",
        "create_risk_management_method",
        "get_risk_management_method",
        "list_risk_management_methods",
    }
    assert set(rm_pkg.__all__) == expected_exports
