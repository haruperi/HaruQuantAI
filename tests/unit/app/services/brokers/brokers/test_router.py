# ruff: noqa: D, ANN, S101
"""Unit tests for the app.services.brokers.router module."""

import sys
from unittest.mock import MagicMock, patch

from app.services.brokers.router import get_active_broker_name, get_broker_module


def test_get_active_broker_name_defaults() -> None:
    with patch("app.utils.settings.settings.active_broker", "mt5"):
        assert get_active_broker_name() == "mt5"


def test_get_broker_module_mt5() -> None:
    with patch("app.utils.settings.settings.active_broker", "mt5"):
        module = get_broker_module()
        assert module.__name__.endswith("mt5")


def test_get_broker_module_ctrader() -> None:
    with patch("app.utils.settings.settings.active_broker", "ctrader"):
        module = get_broker_module()
        assert module.__name__.endswith("ctrader")


def test_get_broker_module_simulator() -> None:
    # Setup mock simulator module since it does not exist on disk
    mock_sim = MagicMock()
    mock_sim.__name__ = "app.services.simulator"
    sys.modules["app.services.simulator"] = mock_sim

    try:
        with patch("app.utils.settings.settings.active_broker", "simulator"):
            module = get_broker_module()
            assert module == mock_sim
    finally:
        sys.modules.pop("app.services.simulator", None)
