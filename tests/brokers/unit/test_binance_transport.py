"""Binance Spot transport tests using a fake in-process SDK module."""

import asyncio
import sys
import types
from typing import ClassVar

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.binance.transport import _BinanceTransport
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.BINANCE_SPOT,
        environment=BrokerEnvironment.TESTNET,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        credentials={
            "api_key": SecretStr("test-key"),
            "api_secret": SecretStr("test-secret"),
        },
    )


class _FakeClient:
    closed = False
    created_kwargs: ClassVar[dict[str, object]] = {}

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def ping(self) -> dict[str, object]:
        self.calls.append("ping")
        return {}

    async def get_server_time(self) -> dict[str, object]:
        self.calls.append("get_server_time")
        return {"serverTime": 0}

    async def close_connection(self) -> None:
        self.calls.append("close_connection")


def _install_fake_sdk(monkeypatch: pytest.MonkeyPatch) -> type[_FakeClient]:
    async def _create(
        api_key: str | None, api_secret: str | None, *, testnet: bool
    ) -> _FakeClient:
        _FakeClient.created_kwargs = {
            "api_key": api_key,
            "api_secret": api_secret,
            "testnet": testnet,
        }
        return _FakeClient()

    fake_module = types.SimpleNamespace(
        AsyncClient=types.SimpleNamespace(create=_create)
    )
    monkeypatch.setitem(sys.modules, "binance", fake_module)
    return _FakeClient


def test_transport_connect_creates_client_with_resolved_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Connect creates a testnet client using the resolved API key/secret."""
    _install_fake_sdk(monkeypatch)
    transport = _BinanceTransport(_config())

    result = asyncio.run(transport.connect())

    assert result is True
    assert _FakeClient.created_kwargs["api_key"] == "test-key"
    assert _FakeClient.created_kwargs["api_secret"] == "test-secret"
    assert _FakeClient.created_kwargs["testnet"] is True


def test_transport_call_requires_connected_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling before connect fails closed without a client reference."""
    _install_fake_sdk(monkeypatch)
    transport = _BinanceTransport(_config())

    async def exercise() -> None:
        with pytest.raises(ConnectionError, match="not connected"):
            await transport.call("ping")

    asyncio.run(exercise())


def test_transport_close_releases_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Close releases the owned Binance client connection."""
    _install_fake_sdk(monkeypatch)
    transport = _BinanceTransport(_config())

    async def exercise() -> None:
        await transport.connect()
        await transport.close()

    asyncio.run(exercise())
    with pytest.raises(ConnectionError):
        asyncio.run(transport.call("ping"))
