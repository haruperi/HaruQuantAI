"""Registered-broker discovery and capability catalogue workflow test (WF-BRK-010)."""

import sys
from collections.abc import Mapping
from typing import cast

import pytest
from app.services.brokers import (
    get_broker_capability_catalogue,
    get_broker_id,
    get_broker_value_field,
    get_registered_brokers,
)

# Provider SDK roots that registry discovery must never import: the registry
# resolves providers lazily, so enumeration and catalogue reads are import-safe.
_SDK_ROOTS = ("MetaTrader5", "ctrader_open_api", "binance", "yfinance")

_EXPECTED_BROKERS = (
    "mt5",
    "ctrader",
    "binance_spot",
    "binance_usd_m_futures",
    "binance_coin_m_futures",
    "dukascopy",
    "yahoo",
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


def _capability_catalogue() -> Mapping[object, tuple[object, ...]]:
    """Return the capability catalogue from the public boundary.

    Returns:
        Declared opaque capability tuples keyed by broker identifier.
    """
    response = get_broker_capability_catalogue()
    assert get_broker_value_field(response, "status") == "success"
    return cast(
        "Mapping[object, tuple[object, ...]]",
        get_broker_value_field(response, "data"),
    )


def test_discovery_enumerates_registered_brokers_without_sdk_import() -> None:
    """WF-BRK-010 step 1: enumeration returns the exact registered set lazily."""
    before = _sdk_modules()
    brokers = _registered_brokers()
    broker_ids = tuple(
        str(get_broker_value_field(broker, "value")) for broker in brokers
    )
    assert broker_ids == _EXPECTED_BROKERS
    assert _sdk_modules() == before


def test_discovery_catalogue_covers_every_registered_broker() -> None:
    """WF-BRK-010 step 2: the catalogue declares capabilities per broker lazily."""
    before = _sdk_modules()
    catalogue = _capability_catalogue()
    broker_ids = {str(get_broker_value_field(broker, "value")) for broker in catalogue}
    assert broker_ids == set(_EXPECTED_BROKERS)
    for capabilities in catalogue.values():
        assert capabilities
    assert _sdk_modules() == before


def test_discovery_reports_unreleased_capability_unavailable() -> None:
    """WF-BRK-010 failure behavior: unreleased writes stay visibly unavailable."""
    catalogue = _capability_catalogue()
    mt5_capabilities = catalogue[get_broker_id("mt5")]
    modify_order = next(
        capability
        for capability in mt5_capabilities
        if get_broker_value_field(capability, "capability") == "modify_order"
    )
    assert (
        get_broker_value_field(modify_order, "implementation_status") == "IMPLEMENTED"
    )
    assert get_broker_value_field(modify_order, "availability") == "UNAVAILABLE"


def test_discovery_omits_unregistered_identifiers() -> None:
    """WF-BRK-010 failure behavior: unknown IDs are absent and fail closed."""
    brokers = _registered_brokers()
    catalogue = _capability_catalogue()
    assert all(
        str(get_broker_value_field(broker, "value")) != "oanda" for broker in brokers
    )
    assert all(
        str(get_broker_value_field(broker, "value")) != "oanda" for broker in catalogue
    )
    with pytest.raises(ValueError, match="oanda"):
        get_broker_id("oanda")
