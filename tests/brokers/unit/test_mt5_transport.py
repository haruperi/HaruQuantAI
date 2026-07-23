"""MT5 transport tests using a fake in-process SDK module."""

import asyncio
import sys
import types

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.mt5_account.transport import _MT5Transport
from pydantic import SecretStr


def _config(**credentials: str) -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference=credentials.get("login"),
        credentials={key: SecretStr(value) for key, value in credentials.items()},
    )


def _install_fake_sdk(monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def _record(name: str) -> object:
        def _fn(*args: object, **kwargs: object) -> object:
            calls.append((name, args, kwargs))
            if name == "initialize":
                return True
            if name == "shutdown":
                return None
            return f"{name}-result"

        return _fn

    fake = types.SimpleNamespace(
        initialize=_record("initialize"),
        shutdown=_record("shutdown"),
        account_info=_record("account_info"),
        TIMEFRAME_M1=1,
        calls=calls,
    )
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    return fake


def test_transport_connect_forwards_resolved_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Login/password/server/path credentials are forwarded to ``initialize``."""
    fake = _install_fake_sdk(monkeypatch)
    config = _config(
        login="12345", password="hunter2", server="Demo-Server", terminal_path="C:/mt5"
    )
    transport = _MT5Transport(config)

    result = asyncio.run(transport.connect())

    assert result is True
    name, _args, kwargs = fake.calls[0]
    assert name == "initialize"
    assert kwargs["login"] == 12345
    assert kwargs["password"] == "hunter2"
    assert kwargs["server"] == "Demo-Server"
    assert kwargs["path"] == "C:/mt5"


def test_transport_call_requires_initialized_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling an SDK operation before ``connect`` fails closed."""
    _install_fake_sdk(monkeypatch)
    transport = _MT5Transport(_config(login="1", password="p", server="s"))

    async def exercise() -> None:
        with pytest.raises(ConnectionError, match="not initialized"):
            await transport.call("account_info")

    asyncio.run(exercise())


def test_transport_constant_requires_connected_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SDK constants are available only after the terminal is initialized."""
    _install_fake_sdk(monkeypatch)
    transport = _MT5Transport(_config(login="1", password="p", server="s"))

    with pytest.raises(ConnectionError, match="not initialized"):
        asyncio.run(transport.constant("TIMEFRAME_M1"))

    asyncio.run(transport.connect())
    assert asyncio.run(transport.constant("TIMEFRAME_M1")) == 1


def test_transport_close_releases_and_clears_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Close shuts down the terminal and clears the owned SDK handle."""
    fake = _install_fake_sdk(monkeypatch)
    transport = _MT5Transport(_config(login="1", password="p", server="s"))

    async def exercise() -> None:
        await transport.connect()
        await transport.close()

    asyncio.run(exercise())
    assert any(name == "shutdown" for name, _args, _kwargs in fake.calls)
    with pytest.raises(ConnectionError):
        asyncio.run(transport.call("account_info"))
