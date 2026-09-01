"""Focused configuration tests for Broker provider features."""

import pytest

from app.kernel.identity import generate_uuid7
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.yahoo.config import YahooConfig


def _base() -> dict[str, object]:
    return {
        "profile_id": generate_uuid7(),
        "profile_version_id": generate_uuid7(),
        "account_ref": "research",
        "probe_symbol": "EURUSD",
    }


def test_yahoo_is_sandbox_only() -> None:
    values = _base() | {"environment": "LIVE"}
    with pytest.raises(ValueError, match="SANDBOX-only"):
        YahooConfig.from_dict(values)


def test_dukascopy_requires_explicit_probe_symbol() -> None:
    values = _base()
    values.pop("probe_symbol")
    with pytest.raises(ValueError, match="probe_symbol"):
        DukascopyConfig.from_dict(values)


def test_binance_partial_credentials_fail_closed() -> None:
    values = _base() | {
        "provider_kind": "BINANCE_SPOT",
        "environment": "TESTNET",
        "credentials": {"api_key": "key"},
    }
    with pytest.raises(ValueError, match="api_key and api_secret"):
        BinanceConfig.from_dict(values)
