# ruff: noqa: D, ANN, S101
"""Unit tests for the app.services.brokers package registry exports."""

import pytest
import app.services.brokers


def test_brokers_registry_lazy_resolution() -> None:
    # Resolve valid clients
    assert app.services.brokers.MT5Client is not None
    assert app.services.brokers.get_mt5_client is not None
    assert app.services.brokers.CTraderClient is not None
    assert app.services.brokers.get_ctrader_client is not None
    assert app.services.brokers.DukascopyClient is not None
    assert app.services.brokers.get_dukascopy_client is not None
    assert app.services.brokers.BinanceClient is not None
    assert app.services.brokers.get_binance_client is not None
    assert app.services.brokers.YahooClient is not None
    assert app.services.brokers.get_yahoo_client is not None


def test_brokers_registry_invalid_getattr() -> None:
    with pytest.raises(AttributeError):
        _ = app.services.brokers.NonExistentBrokerClient
