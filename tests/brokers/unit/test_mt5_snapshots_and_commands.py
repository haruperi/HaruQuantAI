"""Unit tests for MetaTrader snapshot protocol, commands, and gateway configuration."""

from __future__ import annotations

import json

import pytest
from app.services.brokers.metatrader.commands import (
    _provider_ticket,
)
from app.services.brokers.metatrader.snapshot_protocol import (
    build_set_symbols_frame,
    parse_snapshot_frame,
)


def test_snapshot_protocol_parse_and_build() -> None:
    """Verify parse_snapshot_frame and build_set_symbols_frame."""
    # Build symbols frame
    frame = build_set_symbols_frame(revision=1, symbols=("EURUSD", "GBPUSD"))
    assert b"EURUSD" in frame

    # Parse invalid frame
    with pytest.raises(ValueError, match="invalid strict snapshot JSON"):
        parse_snapshot_frame(b"invalid_json")

    with pytest.raises(TypeError, match="protocol message must be an object"):
        parse_snapshot_frame(b"[1, 2, 3]")

    with pytest.raises(ValueError, match="unsupported snapshot protocol"):
        parse_snapshot_frame(b'{"protocol": "v1"}')

    with pytest.raises(ValueError, match="unsupported snapshot message type"):
        parse_snapshot_frame(
            b'{"protocol": "haruquant.mt5.snapshot.v2", "type": "unknown"}'
        )

    # Valid hello message
    hello = {
        "protocol": "haruquant.mt5.snapshot.v2",
        "type": "hello",
        "source_id": "mt5-demo-1",
        "interval_seconds": 5,
        "symbols": ["EURUSD"],
        "token": "valid_token",
    }
    parsed_hello = parse_snapshot_frame(json.dumps(hello).encode("utf-8"))
    assert parsed_hello["type"] == "hello"

    # Valid heartbeat message
    hb = {
        "protocol": "haruquant.mt5.snapshot.v2",
        "type": "heartbeat",
        "revision": 1,
    }
    parsed_hb = parse_snapshot_frame(json.dumps(hb).encode("utf-8"))
    assert parsed_hb["type"] == "heartbeat"


def test_mt5_commands_provider_ticket() -> None:
    """Verify _provider_ticket parses integer tickets and rejects non-integers."""
    assert _provider_ticket("123456") == 123456

    from app.services.brokers.canonical_contracts.protocols import (
        _RequestValidationError,
    )

    with pytest.raises(_RequestValidationError, match="MT5 ticket must be an integer"):
        _provider_ticket("abc_invalid_ticket")
