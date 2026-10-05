"""Unit tests for the broker registry and resolution system."""

from __future__ import annotations

import pytest
from app.plugin.broker import (
    BaseBroker,
    ctrader,
    darwinex,
    dukascopy,
    get_broker,
    mt5,
    register_broker,
    resolve_broker,
    sq_equity,
    sq_futures,
    yahoo,
)


def test_standard_registered_brokers() -> None:
    """Verify standard brokers are present in the global registry."""
    assert get_broker("mt5") is mt5
    assert get_broker("metatrader") is mt5
    assert get_broker("metatrader5") is mt5
    assert get_broker("yahoo") is yahoo
    assert get_broker("dukascopy") is dukascopy
    assert get_broker("darwinex") is darwinex
    assert get_broker("sq_equity") is sq_equity
    assert get_broker("equity") is sq_equity
    assert get_broker("sq_futures") is sq_futures
    assert get_broker("futures") is sq_futures
    assert get_broker("ctrader") is ctrader


def test_case_insensitive_lookup() -> None:
    """Verify alias lookup is case-insensitive and strips whitespace."""
    assert get_broker("MT5") is mt5
    assert get_broker("  Ctrader  ") is ctrader
    assert get_broker("YAHOO") is yahoo


def test_resolve_broker() -> None:
    """Verify resolve_broker handles None, strings, and BaseBroker instances."""
    # None defaults to MT5
    assert resolve_broker(None) is mt5

    # Instance resolution
    assert resolve_broker(ctrader) is ctrader
    assert resolve_broker(yahoo) is yahoo

    # String alias resolution
    assert resolve_broker("dukascopy") is dukascopy
    assert resolve_broker("darwinex") is darwinex


def test_unregistered_broker_raises_key_error() -> None:
    """Verify resolving unknown alias raises KeyError."""
    with pytest.raises(KeyError) as exc_info:
        get_broker("nonexistent_broker_123")
    assert "is not registered" in str(exc_info.value)


def test_invalid_broker_type_raises_type_error() -> None:
    """Verify passing non-str, non-BaseBroker raises TypeError."""
    with pytest.raises(TypeError) as exc_info:
        resolve_broker(12345)
    assert "Invalid broker parameter" in str(exc_info.value)


def test_custom_broker_registration() -> None:
    """Verify registering a custom broker instance works as expected."""
    custom = BaseBroker(name="CustomBroker")
    register_broker("custom_test", custom)

    assert get_broker("custom_test") is custom
    assert resolve_broker("custom_test") is custom
