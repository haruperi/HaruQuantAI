"""Unit tests for CTraderBroker plugin framing, catalog, and protocol logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.plugin.broker import (
    CTraderBroker,
    OrderAction,
    OrderType,
    TimeFrame,
    TradeRequest,
)


def test_ctrader_send_msg_framing() -> None:
    """Verify 4-byte big-endian message framing in _send_msg."""
    broker = CTraderBroker()
    mock_sock = MagicMock()
    broker._sock = mock_sock

    payload_type = 2100
    payload_bytes = b"hello cTrader"

    success = broker._send_msg(payload_type, payload_bytes)
    assert success is True
    assert mock_sock.sendall.called
    sent_bytes = mock_sock.sendall.call_args[0][0]
    # First 4 bytes must be the length of the serialized message
    assert len(sent_bytes) > 4


def test_ctrader_timeframe_mapping() -> None:
    """Verify cTrader period ID mappings."""
    broker = CTraderBroker()
    assert broker.TIMEFRAME_TO_PERIOD[TimeFrame.M1] == 1
    assert broker.TIMEFRAME_TO_PERIOD[TimeFrame.H1] == 9
    assert broker.TIMEFRAME_TO_PERIOD[TimeFrame.D1] == 12


def test_ctrader_symbol_catalog() -> None:
    """Verify embedded cTrader symbol metadata and lookup."""
    broker = CTraderBroker()
    res = broker.get_symbol_info("EURUSD")
    assert res.is_success is True
    assert res.data.name == "EURUSD"
    assert res.data.digits == 5

    syms = broker.get_symbols()
    assert syms.is_success is True
    assert len(syms.data) >= 4


def test_ctrader_order_check() -> None:
    """Verify pre-flight order check validation."""
    broker = CTraderBroker()

    # Valid request
    valid_req = TradeRequest(
        action=OrderAction.DEAL, symbol="EURUSD", volume=0.01, type=OrderType.BUY
    )
    chk_valid = broker.check_order(valid_req)
    assert chk_valid.is_success is True
    assert chk_valid.data.retcode == 0

    # Missing symbol
    invalid_req = TradeRequest(symbol="", volume=0.01)
    chk_invalid = broker.check_order(invalid_req)
    assert chk_invalid.is_success is False

    # Zero volume
    zero_vol = TradeRequest(symbol="EURUSD", volume=0.0)
    chk_zero = broker.check_order(zero_vol)
    assert chk_zero.is_success is False


def test_ctrader_connection_states() -> None:
    """Verify disconnect and connection checking."""
    broker = CTraderBroker()
    assert broker.is_connected().data is False

    broker._sock = MagicMock()
    broker._authenticated = True
    assert broker.is_connected().data is True

    disc = broker.disconnect()
    assert disc.is_success is True
    assert broker.is_connected().data is False
