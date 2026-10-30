"""Tests for BrokerRegistry thread-safe registration and lifecycle management."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import override

from app.core.trading.connection.base import TradingClient
from app.workspace.trading.brokers.registry import BrokerRegistry


class DummyClient(TradingClient):
    """Dummy TradingClient for registry testing."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.disconnected = False

    @override
    def disconnect(self) -> None:
        self.disconnected = True
        super().disconnect()


def test_registry_registration_and_lookup() -> None:
    registry = BrokerRegistry()
    client1 = DummyClient("client-1")
    client2 = DummyClient("client-2")

    registry.register("conn-1", client1)
    registry.register("conn-2", client2)

    assert registry.get("conn-1") is client1
    assert registry.get("conn-2") is client2
    assert registry.get("conn-missing") is None

    assert registry.get_trading_client("conn-1") is client1
    assert len(registry.list_connection_ids()) == 2
    assert ("conn-1", client1) in registry.list_active()


def test_registry_replacement_disconnects_previous() -> None:
    registry = BrokerRegistry()
    client1 = DummyClient("client-1")
    client2 = DummyClient("client-2")

    registry.register("conn-1", client1)
    registry.register("conn-1", client2)

    assert client1.disconnected is True
    assert registry.get("conn-1") is client2


def test_registry_removal() -> None:
    registry = BrokerRegistry()
    client = DummyClient("client-1")

    registry.register("conn-1", client)
    removed = registry.remove("conn-1")

    assert removed is client
    assert registry.get("conn-1") is None
    assert registry.remove("nonexistent") is None


def test_registry_close_all() -> None:
    registry = BrokerRegistry()
    c1 = DummyClient("c1")
    c2 = DummyClient("c2")

    registry.register("c1", c1)
    registry.register("c2", c2)

    registry.close_all()
    assert c1.disconnected is True
    assert c2.disconnected is True
    assert len(registry.list_active()) == 0


def test_registry_async_close_all() -> None:
    async def scenario() -> None:
        registry = BrokerRegistry()
        c1 = DummyClient("c1")
        c2 = DummyClient("c2")

        registry.register("c1", c1)
        registry.register("c2", c2)

        await registry.aclose_all()
        assert c1.disconnected is True
        assert c2.disconnected is True
        assert len(registry.list_active()) == 0

    asyncio.run(scenario())


def test_registry_concurrency() -> None:
    registry = BrokerRegistry()

    def worker(idx: int) -> None:
        client = DummyClient(f"client-{idx}")
        registry.register(f"conn-{idx}", client)
        retrieved = registry.get(f"conn-{idx}")
        assert retrieved is client

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(worker, range(50)))

    assert len(registry.list_active()) == 50
    registry.close_all()
    assert len(registry.list_active()) == 0
