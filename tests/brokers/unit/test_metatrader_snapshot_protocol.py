"""Unit evidence for the tested MT5 EA wire protocol."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from app.services.brokers.metatrader.snapshot_protocol import (
    build_set_symbols_frame,
    parse_snapshot_frame,
)


def _hello(**updates: object) -> bytes:
    payload: dict[str, object] = {
        "type": "hello",
        "protocol": "haruquant.mt5.snapshot.v2",
        "source_id": "mt5-terminal-1",
        "token": "test-token",
        "interval_seconds": 1,
        "symbols": ["EURUSD"],
    }
    payload.update(updates)
    return json.dumps(payload).encode()


def _snapshot(**updates: object) -> bytes:
    payload: dict[str, object] = {
        "type": "snapshot",
        "protocol": "haruquant.mt5.snapshot.v2",
        "sequence": 7,
        "revision": 3,
        "quotes": [
            {
                "symbol": "EURUSD",
                "bid": 1.1,
                "ask": 1.1002,
                "last": 0,
                "volume": 4,
                "volume_real": 4.0,
                "time_msc": 1786651200000,
                "flags": 6,
                "digits": 5,
            }
        ],
        "errors": [],
    }
    payload.update(updates)
    return json.dumps(payload).encode()


def _book(**updates: object) -> bytes:
    payload: dict[str, object] = {
        "type": "book",
        "protocol": "haruquant.mt5.snapshot.v2",
        "sequence": 3,
        "revision": 3,
        "books": [
            {
                "symbol": "EURUSD",
                "book_depth": 10,
                "bids": [{"price": 1.1000, "volume": 2.5}],
                "asks": [{"price": 1.1002, "volume": 1.0}],
            }
        ],
        "errors": [],
    }
    payload.update(updates)
    return json.dumps(payload).encode()


def test_protocol_accepts_the_tested_ea_hello_and_snapshot() -> None:
    hello = parse_snapshot_frame(_hello())
    snapshot = parse_snapshot_frame(_snapshot())
    assert hello["source_id"] == "mt5-terminal-1"
    quote = snapshot["quotes"][0]  # type: ignore[index]
    assert quote["bid"] == Decimal("1.1")
    assert quote["last"] is None


def test_protocol_builds_commands_and_accepts_applied_acknowledgments() -> None:
    command = json.loads(build_set_symbols_frame(4, ("EURUSD", "XAUUSD")))
    assert command == {
        "type": "set_symbols",
        "protocol": "haruquant.mt5.snapshot.v2",
        "revision": 4,
        "symbols": ["EURUSD", "XAUUSD"],
    }
    applied = parse_snapshot_frame(
        json.dumps(
            {
                "type": "symbols_applied",
                "protocol": "haruquant.mt5.snapshot.v2",
                "revision": 4,
                "symbols": ["EURUSD"],
                "errors": [{"symbol": "XAUUSD", "code": 4302}],
            }
        ).encode()
    )
    assert applied["revision"] == 4
    assert applied["symbols"] == ("EURUSD",)


def test_protocol_accepts_the_tested_ea_book() -> None:
    book = parse_snapshot_frame(_book())
    entry = book["books"][0]  # type: ignore[index]
    assert entry["symbol"] == "EURUSD"
    assert entry["book_depth"] == 10
    assert entry["bids"][0]["price"] == Decimal("1.1")  # type: ignore[index]
    assert entry["asks"][0]["volume"] == Decimal("1.0")  # type: ignore[index]


def test_protocol_accepts_a_book_error_for_an_unsupported_symbol() -> None:
    """A symbol whose MarketBookAdd failed reports an explicit error, no book."""
    book = parse_snapshot_frame(
        _book(books=[], errors=[{"symbol": "EURUSD", "code": 0}])
    )
    assert book["books"] == ()
    assert book["errors"][0]["symbol"] == "EURUSD"  # type: ignore[index]


def test_protocol_accepts_a_genuine_empty_book() -> None:
    """A subscribed symbol with zero resting levels is empty, not an error."""
    book = parse_snapshot_frame(
        _book(books=[{"symbol": "EURUSD", "book_depth": 10, "bids": [], "asks": []}])
    )
    entry = book["books"][0]  # type: ignore[index]
    assert entry["bids"] == ()
    assert entry["asks"] == ()


def test_protocol_accepts_a_bounded_idle_heartbeat() -> None:
    """A paused EA can keep only its authenticated control channel alive."""
    heartbeat = parse_snapshot_frame(
        json.dumps(
            {
                "type": "heartbeat",
                "protocol": "haruquant.mt5.snapshot.v2",
                "revision": 5,
            }
        ).encode()
    )

    assert heartbeat["revision"] == 5


@pytest.mark.parametrize(
    "frame",
    [
        _hello(protocol="wrong"),
        _hello(symbols=["EURUSD", "EURUSD"]),
        _snapshot(sequence=0),
        _snapshot(quotes=[], errors=[{"symbol": "EURUSD", "code": 1}], extra=True),
        _book(sequence=0),
        _book(revision=0),
        _book(
            books=[{"symbol": "EURUSD", "book_depth": 10, "bids": [], "asks": []}],
            errors=[{"symbol": "EURUSD", "code": 0}],
        ),
        _book(
            books=[
                {
                    "symbol": "EURUSD",
                    "book_depth": 10,
                    "bids": [{"price": 0, "volume": 1.0}],
                    "asks": [],
                }
            ]
        ),
        _book(books=[{"symbol": "EURUSD", "book_depth": -1, "bids": [], "asks": []}]),
        json.dumps(
            {
                "type": "heartbeat",
                "protocol": "haruquant.mt5.snapshot.v2",
                "revision": 0,
            }
        ).encode(),
    ],
)
def test_protocol_rejects_invalid_frames(frame: bytes) -> None:
    with pytest.raises((TypeError, ValueError)):
        parse_snapshot_frame(frame)
