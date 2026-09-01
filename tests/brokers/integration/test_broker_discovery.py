"""Registered-broker discovery and capability catalogue workflow test (WF-BRK-010)."""

import sys
from typing import cast

import pytest
from app.services.brokers import (
    get_broker_id,
    get_broker_value_field,
    get_registered_brokers,
)

# Provider SDK roots that registry discovery must never import: the registry
# resolves providers lazily, so enumeration is import-safe.
_SDK_ROOTS = ("MetaTrader5", "ctrader_open_api", "binance", "yfinance")

_EXPECTED_BROKERS = (
    "mt5",
    "ctrader",
    "binance_spot",
    "binance_usd_m_futures",
    "binance_coin_m_futures",
    "dukascopy",
    "yahoo",
    "sim",
)


def _sdk_modules() -> set[str]:
    """Return the names of currently loaded provider SDK modules.

    Returns:
        Loaded module names whose top-level package is a provider SDK.
    """
    return {name for name in sys.modules if name.split(".")[0] in _SDK_ROOTS}


def _registered_brokers() -> tuple[object, ...]:
    """Return the registered broker tuple from the public boundary.

    Returns:
        Opaque registered broker identifiers in stable registry order.
    """
    response = get_registered_brokers()
    assert get_broker_value_field(response, "status") == "success"
    return cast("tuple[object, ...]", get_broker_value_field(response, "data"))


def test_discovery_enumerates_registered_brokers_without_sdk_import() -> None:
    """WF-BRK-010 step 1: enumeration returns the exact registered set lazily."""
    before = _sdk_modules()
    brokers = _registered_brokers()
    broker_ids = tuple(
        str(get_broker_value_field(broker, "value")) for broker in brokers
    )
    assert broker_ids == _EXPECTED_BROKERS
    assert _sdk_modules() == before


def test_discovery_omits_unregistered_identifiers() -> None:
    """WF-BRK-010 failure behavior: unknown IDs are absent and fail closed."""
    brokers = _registered_brokers()
    assert all(
        str(get_broker_value_field(broker, "value")) != "oanda" for broker in brokers
    )
    with pytest.raises(ValueError, match="oanda"):
        get_broker_id("oanda")
