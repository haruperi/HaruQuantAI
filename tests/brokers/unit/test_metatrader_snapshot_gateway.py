"""Unit evidence for bounded MT5 TCP gateway lifecycle."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping

from app.services.brokers.metatrader import snapshot_gateway


def test_gateway_start_and_stop_own_the_listener(
    monkeypatch,
) -> None:
    """The public lifecycle binds once and releases the server."""

    class _Server:
        """Minimal asyncio server fixture."""

        def close(self) -> None:
            """Record closure."""

        async def wait_closed(self) -> None:
            """Complete closure."""

    async def fake_start_server(*_args, **_kwargs):
        """Return one inert listener."""
        return _Server()

    async def scenario() -> None:
        await snapshot_gateway.stop_metatrader_snapshot_gateway()
        monkeypatch.setattr(asyncio, "start_server", fake_start_server)
        await snapshot_gateway.start_metatrader_snapshot_gateway(
            host="127.0.0.1",
            port=9001,
            auth_token="test-token",
            source_id="mt5-terminal-1",
            interval_seconds=1,
            symbols=("EURUSD",),
        )
        assert snapshot_gateway.get_metatrader_snapshot_gateway_status()["listening"]
        await snapshot_gateway.stop_metatrader_snapshot_gateway()
        assert not snapshot_gateway.get_metatrader_snapshot_gateway_status()[
            "listening"
        ]

    asyncio.run(scenario())


def test_gateway_reconciles_revisioned_symbol_demand(monkeypatch) -> None:
    """Active consumers produce one acknowledged union and release to empty."""

    class _Writer:
        def __init__(self) -> None:
            self.frames: list[bytes] = []

        def write(self, frame: bytes) -> None:
            self.frames.append(frame)

        async def drain(self) -> None:
            return None

    async def scenario() -> None:
        gateway = snapshot_gateway._SnapshotGateway()
        writer = _Writer()
        gateway.producer = writer  # type: ignore[assignment]
        gateway.source_id = "mt5-terminal-1"
        gateway.runtime_authoritative = True

        acquire = asyncio.create_task(gateway.acquire_symbols(("EURUSD", "XAUUSD")))
        await asyncio.sleep(0)
        command = json.loads(writer.frames[-1])
        await gateway._accept_symbols_applied(
            {
                "revision": command["revision"],
                "symbols": tuple(command["symbols"]),
                "errors": (),
            }
        )
        consumer_id = await acquire
        assert gateway.status()["applied_symbol_count"] == 2

        await gateway.release_symbols(consumer_id)
        assert json.loads(writer.frames[-1])["symbols"] == []
        await gateway._accept_symbols_applied(
            {
                "revision": json.loads(writer.frames[-1])["revision"],
                "symbols": (),
                "errors": (),
            }
        )
        gateway._accept_heartbeat(
            {"revision": gateway.applied_revision, "type": "heartbeat"}
        )
        assert gateway.status()["paused"] is True
        queue: asyncio.Queue[Mapping[str, object] | None] = asyncio.Queue()
        gateway.subscribers.add(queue)
        gateway._accept_heartbeat(
            {"revision": gateway.applied_revision, "type": "heartbeat"}
        )
        assert queue.empty()

    asyncio.run(scenario())


def test_gateway_retains_shared_demand_during_partial_release(monkeypatch) -> None:
    """Releasing one consumer cannot pause symbols required by another."""

    async def scenario() -> None:
        gateway = snapshot_gateway._SnapshotGateway()
        gateway.runtime_authoritative = True
        gateway.symbol_consumers = {
            "first": ("EURUSD",),
            "second": ("EURUSD", "XAUUSD"),
        }
        monkeypatch.setattr(snapshot_gateway, "_SYMBOL_RELEASE_GRACE_SECONDS", 0.0)

        await gateway.release_symbols("first")
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert gateway.desired_symbols == ("EURUSD", "XAUUSD")
        assert "second" in gateway.symbol_consumers

    asyncio.run(scenario())
