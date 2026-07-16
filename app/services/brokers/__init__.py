"""Canonical Brokers domain API with lazy provider type resolution."""

# ruff: noqa: ANN401, PLE0604 - PEP 562 resolves a fixed heterogeneous type table.

import importlib
from typing import Any

from app.services.brokers.contracts import *  # noqa: F403
from app.services.brokers.contracts import __all__ as _contract_exports
from app.services.brokers.registry import (
    create_broker_adapter,
    get_broker_capability_catalogue,
    get_registered_brokers,
)

_LAZY_ADAPTERS = {
    "MT5BrokerAdapter": "app.services.brokers.mt5",
    "CTraderBrokerAdapter": "app.services.brokers.ctrader",
    "BinanceBrokerAdapter": "app.services.brokers.binance",
    "DukascopyBrokerAdapter": "app.services.brokers.dukascopy",
    "YahooBrokerAdapter": "app.services.brokers.yahoo",
}

__all__ = (
    *_contract_exports,
    "create_broker_adapter",
    "get_broker_capability_catalogue",
    "get_registered_brokers",
    *_LAZY_ADAPTERS,
)


def __getattr__(name: str) -> Any:
    """Resolve only an approved adapter class and cache the class object.

    Args:
        name: Name of the attribute/adapter class to resolve.

    Returns:
        The resolved adapter class object.

    Raises:
        AttributeError: If the class name is not recognized or found.
    """
    module_name = _LAZY_ADAPTERS.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(importlib.import_module(module_name), name)
    globals()[name] = value
    return value
