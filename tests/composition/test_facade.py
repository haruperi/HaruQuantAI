"""Unit tests for composition facade and capability leasing."""

from __future__ import annotations

import types
from unittest.mock import MagicMock, patch

import pytest
from app.composition.facade import CapabilityLease, lease_capability
from app.kernel.errors import CapabilityUnavailableError


def test_capability_lease_release() -> None:
    """Verify CapabilityLease wraps instance and can be released."""
    lease = CapabilityLease(instance="mock_instance")
    assert lease.instance == "mock_instance"
    lease.release()


def test_lease_capability_rsi_and_williams() -> None:
    """Verify lease_capability succeeds when provider modules are resolved."""
    mock_rsi_mod = types.ModuleType(
        "app.services.indicators.momentum.rsi_default.plugin"
    )
    mock_rsi_mod.create_provider = MagicMock(return_value="rsi_instance")  # type: ignore[attr-defined]

    mock_williams_mod = types.ModuleType(
        "app.services.indicators.momentum.williams_r_default.plugin"
    )
    mock_williams_mod.create_provider = MagicMock(return_value="williams_instance")  # type: ignore[attr-defined]

    with patch.dict(
        "sys.modules",
        {
            "app.services.indicators": types.ModuleType("app.services.indicators"),
            "app.services.indicators.momentum": types.ModuleType(
                "app.services.indicators.momentum"
            ),
            "app.services.indicators.momentum.rsi_default": types.ModuleType(
                "app.services.indicators.momentum.rsi_default"
            ),
            "app.services.indicators.momentum.rsi_default.plugin": mock_rsi_mod,
            "app.services.indicators.momentum.williams_r_default": types.ModuleType(
                "app.services.indicators.momentum.williams_r_default"
            ),
            "app.services.indicators.momentum.williams_r_default.plugin": mock_williams_mod,
        },
    ):
        lease_rsi = lease_capability("indicator.rsi.v1")
        assert isinstance(lease_rsi, CapabilityLease)
        assert lease_rsi.instance == "rsi_instance"

        lease_williams = lease_capability("indicator.williams_r.v1")
        assert isinstance(lease_williams, CapabilityLease)
        assert lease_williams.instance == "williams_instance"


def test_lease_capability_unavailable() -> None:
    """Verify lease_capability raises CapabilityUnavailableError for unknown capabilities."""
    with pytest.raises(CapabilityUnavailableError):
        lease_capability("unknown.capability.v1")
