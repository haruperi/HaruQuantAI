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
    from app.services import simulator
    with patch("app.utils.settings.settings.active_broker", "simulator"):
        module = get_broker_module()
        assert module == simulator


def test_get_active_broker_name_import_error() -> None:
    # Force ImportError on app.utils settings lookup
    with patch.dict("sys.modules", {"app.utils": None, "app.core.config": None}):
        assert get_active_broker_name() == "mt5"
