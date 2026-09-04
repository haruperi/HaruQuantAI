"""Protocol tests for the authenticated MT5 snapshot bridge listener.

Each test binds the listener on an ephemeral localhost port and drives it
with a scripted TCP client speaking the ``haruquant.mt5.snapshot.v2`` line
protocol exactly as the TickBridge EA does.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from app.contracts.data.models import StreamMarketEventsSubscription
from app.services.data.realtime_market_events.config import (
    RealtimeMarketEventsConfig,
)
from app.services.data.realtime_market_events.realtime_market_events import (
    StreamMarketEventsService,
)
from app.services.data.realtime_market_events.snapshot_bridge import (
    PROTOCOL,
    Mt5SnapshotBridgeServer,
    SnapshotBridgeSettings,
)

_TOKEN = "bridge-test-token"


def _settings(
    port: int, symbols: tuple[str, ...] = ("EURUSD", "GBPUSD")
) -> SnapshotBridgeSettings:
    """Build bridge settings bound to an ephemeral localhost port."""
    return SnapshotBridgeSettings(
        host="127.0.0.1",
        port=port,
        source_id="mt5-terminal-1",
        auth_token=_TOKEN,
        symbols=symbols,
    )


def _hello(token: str = _TOKEN, source_id: str = "mt5-terminal-1") -> bytes:
    """Build one EA hello frame."""
    return (
        json.dumps(
            {
                "type": "hello",
                "protocol": PROTOCOL,
                "source_id": source_id,
                "token": token,
                "interval_seconds": 1,
                "symbols": ["EURUSD", "GBPUSD"],
            }
        )
        + "\n"
    ).encode("utf-8")


def _snapshot(sequence: int) -> bytes:
    """Build one EA snapshot frame carrying two quotes."""
    return (
        json.dumps(
            {
                "type": "snapshot",
                "protocol": PROTOCOL,
                "sequence": sequence,
                "revision": 1,
                "quotes": [
                    {
                        "symbol": "EURUSD",
                        "bid": 1.0850,
                        "ask": 1.0852,
                        "last": 1.0851,
                        "volume": 12,
                        "time_msc": 1785531600000,
                        "flags": 6,
                        "digits": 5,
                    },
                    {
                        "symbol": "GBPUSD",
                        "bid": 1.2680,
                        "ask": 1.2682,
                        "last": 0.0,
                        "volume": 4,
                        "time_msc": 1785531600000,
                        "flags": 6,
                        "digits": 5,
                    },
                ],
                "errors": [],
            }
        )
        + "\n"
    ).encode("utf-8")


async def _open_connection(
    port: int,
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Connect one scripted EA client to the listener."""
    return await asyncio.open_connection("127.0.0.1", port)


@pytest.mark.asyncio
async def test_hello_receives_compact_set_symbols_and_snapshots_ingest() -> None:
    """Verify authentication, symbol command framing, and event ingestion."""
    service = StreamMarketEventsService(config=RealtimeMarketEventsConfig())
    server = Mt5SnapshotBridgeServer(service, _settings(port=0))
    await server.start()
    port = server._server.sockets[0].getsockname()[1]
    subscription = service.subscribe_stream_market_events_events(
        StreamMarketEventsSubscription()
    )
    try:
        reader, writer = await _open_connection(port)
        writer.write(_hello())
        await writer.drain()

        command_line = await asyncio.wait_for(reader.readuntil(b"\n"), timeout=2.0)
        command = json.loads(command_line.decode("utf-8"))
        assert command["type"] == "set_symbols"
        assert command["protocol"] == PROTOCOL
        assert command["revision"] == 1
        assert command["symbols"] == ["EURUSD", "GBPUSD"]
        # The EA parses this frame with substring markers; compact JSON is
        # part of the protocol contract.
        assert b'"revision":1' in command_line
        assert b'"symbols":["EURUSD","GBPUSD"]' in command_line

        writer.write(_snapshot(1))
        await writer.drain()

        first = await asyncio.wait_for(anext(subscription), timeout=2.0)
        values = first.payload["values"]
        assert values["symbol"] == "EURUSD"
        assert values["bid"] == "1.085"
        assert values["ask"] == "1.0852"
        assert first.payload["provider"]["provider_id"] == server.provider_id

        second = await asyncio.wait_for(anext(subscription), timeout=2.0)
        assert second.payload["values"]["symbol"] == "GBPUSD"
        assert second.payload["provider_sequence"] == 1
        writer.close()
        await writer.wait_closed()
    finally:
        with contextlib_suppress():
            await subscription.aclose()
        await server.stop()


@pytest.mark.asyncio
async def test_hello_with_wrong_token_is_closed_without_acknowledgement() -> None:
    """Verify authentication fails closed."""
    service = StreamMarketEventsService(config=RealtimeMarketEventsConfig())
    server = Mt5SnapshotBridgeServer(service, _settings(port=0))
    await server.start()
    port = server._server.sockets[0].getsockname()[1]
    try:
        reader, writer = await _open_connection(port)
        writer.write(_hello(token="wrong-token"))
        await writer.drain()
        # The listener closes without ever acknowledging the failed hello.
        remainder = await asyncio.wait_for(reader.read(-1), timeout=2.0)
        assert remainder == b""
        writer.close()
        await writer.wait_closed()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_frames_before_authentication_are_rejected() -> None:
    """Verify snapshots never ingest without a valid hello."""
    service = StreamMarketEventsService(config=RealtimeMarketEventsConfig())
    server = Mt5SnapshotBridgeServer(service, _settings(port=0))
    await server.start()
    port = server._server.sockets[0].getsockname()[1]
    try:
        reader, writer = await _open_connection(port)
        writer.write(_snapshot(1))
        await writer.drain()
        remainder = await asyncio.wait_for(reader.read(-1), timeout=2.0)
        assert remainder == b""
        assert not service._event_buffers
        writer.close()
        await writer.wait_closed()
    finally:
        await server.stop()


def contextlib_suppress() -> Any:
    """Return a context manager suppressing async-close errors in teardown."""
    import contextlib

    return contextlib.suppress(Exception)
