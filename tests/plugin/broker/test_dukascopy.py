"""Unit tests for DukascopyBroker plugin with mocked responses."""

from __future__ import annotations

import lzma
from unittest.mock import MagicMock

from app.plugin.broker import DukascopyBroker
from app.plugin.broker.dukascopy import _decompress_bi5


def test_dukascopy_connect_success() -> None:
    """Verify DukascopyBroker connect with HTTP 200 head response."""
    broker = DukascopyBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    broker.session.head = MagicMock(return_value=mock_resp)

    res = broker.connect()
    assert res.is_success is True
    assert broker.is_connected().data is True


def test_dukascopy_connect_failure() -> None:
    """Verify DukascopyBroker connect failure."""
    broker = DukascopyBroker()
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    broker.session.head = MagicMock(return_value=mock_resp)

    res = broker.connect()
    assert res.is_success is False
    assert broker.is_connected().data is False


def test_dukascopy_disconnect() -> None:
    """Verify DukascopyBroker disconnect."""
    broker = DukascopyBroker()
    assert broker.disconnect().is_success is True
    assert broker.is_connected().data is False


def test_dukascopy_get_symbol_info() -> None:
    """Verify DukascopyBroker instrument metadata."""
    broker = DukascopyBroker()
    eur = broker.get_symbol_info("EURUSD")
    assert eur.is_success is True
    assert eur.data.name == "EURUSD"
    assert eur.data.digits == 5
    assert eur.data.point == 0.00001

    jpy = broker.get_symbol_info("USDJPY")
    assert jpy.is_success is True
    assert jpy.data.digits == 3


def test_dukascopy_lzma_decompression() -> None:
    """Verify decompression of bi5 payload."""
    raw_bytes = b"sample uncompressed ticks payload data"
    compressed = lzma.compress(raw_bytes, format=lzma.FORMAT_ALONE)

    decomp = _decompress_bi5(compressed)
    assert decomp == raw_bytes


def test_dukascopy_get_symbol_tick() -> None:
    """Verify get_symbol_tick returns valid Tick."""
    broker = DukascopyBroker()
    tick_res = broker.get_symbol_tick("EURUSD")
    assert tick_res.is_success is True
    assert tick_res.data.bid > 0
    assert tick_res.data.ask >= tick_res.data.bid
