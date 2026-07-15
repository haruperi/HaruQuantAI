"""MT5 adapter tests using an injected fake transport."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.mt5.adapter import MT5BrokerAdapter
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
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
        account_reference="12345",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    """Mark every operation available for adapter-body unit testing.

    The real registry catalogue keeps every non-connection capability
    ``UNAVAILABLE`` until credential-gated release evidence is recorded
    (see ``registry/catalogue.py``). Unit tests exercise the adapter's own
    method bodies directly, so they assert availability locally instead of
    depending on that release gate.
    """
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


class _FakeTransport:
    def __init__(self, *, verified: bool = True) -> None:
        self._verified = verified
        self.closed = False

    async def connect(self) -> bool:
        return self._verified

    def _responses(self) -> dict[str, object]:
        now = datetime(2026, 1, 1, tzinfo=UTC).timestamp()
        return {
            "account_info": {"login": 12345, "server": "Demo-Server"},
            "terminal_info": {} if self._verified else None,
            "version": "5.0.0",
            "symbols_get": (
                {
                    "name": "EURUSD",
                    "digits": 5,
                    "volume_step": 0.01,
                    "volume_min": 0.01,
                    "volume_max": 100,
                },
            ),
            "symbol_select": True,
            "symbol_info_tick": {
                "time": now,
                "bid": 1.1,
                "ask": 1.1002,
                "last": 1.1001,
            },
            "copy_ticks_range": ({"time": now, "bid": 1.1, "ask": 1.1002},),
            "positions_get": (
                {
                    "ticket": 1,
                    "symbol": "EURUSD",
                    "type": 0,
                    "volume": 1,
                    "price_open": 1.1,
                    "price_current": 1.2,
                    "profit": 100,
                    "time_update": now,
                },
            ),
        }

    async def call(self, name: str, *args: object, **kwargs: object) -> object:
        del args, kwargs
        return self._responses().get(name)

    async def close(self) -> None:
        self.closed = True


def test_adapter_rejects_mismatched_account_reference() -> None:
    """The declared account reference must match the resolved login."""
    bad = BrokerConnectionConfig(
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
        account_reference="99999",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )
    with pytest.raises(ValueError, match="account_reference must match login"):
        MT5BrokerAdapter(bad, _capabilities())


def test_adapter_connect_verifies_account_and_server() -> None:
    """A successful transport verification transitions to a ready session."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=True)
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.is_success
        status = await adapter.is_connected()
        assert status.data is True

    asyncio.run(exercise())


def test_adapter_connect_fails_closed_on_account_mismatch() -> None:
    """A transport that cannot verify identity fails the connection closed."""

    class _MismatchedTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            del args, kwargs
            if name == "account_info":
                return {"login": 1, "server": "Other-Server"}
            if name == "terminal_info":
                return {}
            return None

    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_MismatchedTransport()
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CONNECTION_FAILED

    asyncio.run(exercise())


def test_adapter_get_symbol_info_not_found_is_structured() -> None:
    """A missing symbol returns the exact canonical not-found error."""

    class _EmptyTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbol_info":
                return None
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=_EmptyTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbol_info("UNKNOWN")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND

    asyncio.run(exercise())


def test_adapter_disconnect_releases_transport() -> None:
    """Disconnecting the adapter releases the owned transport handle."""
    transport = _FakeTransport(verified=True)
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        await adapter.disconnect()

    asyncio.run(exercise())
    assert transport.closed


def test_adapter_get_symbols_and_ping() -> None:
    """Symbols map genuine values and ping succeeds on a verified terminal."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=True)
    )

    async def exercise() -> None:
        await adapter.connect()
        symbols = await adapter.get_symbols(limit=5)
        assert symbols.data is not None
        assert symbols.data.items[0].provider_symbol == "EURUSD"
        ping = await adapter.ping()
        assert ping.is_success

    asyncio.run(exercise())


def test_adapter_select_symbol_reports_not_found() -> None:
    """A rejected symbol selection returns the exact not-found error."""

    class _RejectingTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbol_select":
                return False
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_RejectingTransport()
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.select_symbol("UNKNOWN")
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND

    asyncio.run(exercise())


def test_adapter_get_quote_and_ticks() -> None:
    """Quotes and ticks map genuine terminal values."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=True)
    )

    async def exercise() -> None:
        await adapter.connect()
        quote = await adapter.get_quote("EURUSD")
        assert quote.data is not None
        assert str(quote.data.bid) == "1.1"
        ticks = await adapter.get_ticks(
            "EURUSD",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            limit=10,
        )
        assert ticks.data is not None
        assert len(ticks.data.items) == 1

    asyncio.run(exercise())


def test_adapter_get_positions_maps_open_state() -> None:
    """Positions map genuine terminal position state."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=True)
    )

    async def exercise() -> None:
        await adapter.connect()
        positions = await adapter.get_positions(limit=10)
        assert positions.data is not None
        assert positions.data.items[0].side == "LONG"

    asyncio.run(exercise())


def test_adapter_get_platform_info_reports_terminal_version() -> None:
    """Platform info exposes the redacted terminal version and environment."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=True)
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_platform_info()
        assert result.data is not None
        assert result.data.api_or_terminal_version == "5.0.0"
        assert result.data.observed_at.tzinfo is UTC

    asyncio.run(exercise())


def test_adapter_rejects_non_live_or_demo_env() -> None:
    """MT5BrokerAdapter raises ValueError for invalid environment types."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="12345",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )
    with pytest.raises(ValueError, match="MT5 requires LIVE or DEMO"):
        MT5BrokerAdapter(bad, _capabilities())


def test_adapter_rejects_endpoint_override() -> None:
    """MT5BrokerAdapter raises ValueError when an endpoint override is specified."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        endpoint="http://localhost:5000",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="12345",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )
    with pytest.raises(ValueError, match="MT5 does not accept endpoint override"):
        MT5BrokerAdapter(bad, _capabilities())


def test_adapter_rejects_missing_credentials() -> None:
    """MT5BrokerAdapter raises ValueError when required credentials are missing."""
    bad = BrokerConnectionConfig(
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
        account_reference="12345",
        credentials=None,
    )
    msg = "MT5 resolved login, password, and server are required"
    with pytest.raises(ValueError, match=msg):
        MT5BrokerAdapter(bad, _capabilities())


def test_adapter_connect_handles_transport_exception() -> None:
    """A transport connection exception transitions to failed and fails closed."""

    class _FailingTransport(_FakeTransport):
        async def connect(self) -> bool:
            raise ConnectionError("failed to connect")

    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_FailingTransport()
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CONNECTION_FAILED

    asyncio.run(exercise())


def test_adapter_connect_fails_if_initialized_is_false() -> None:
    """A transport reporting initialized is False transitions to failed connection."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=False)
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success

    asyncio.run(exercise())


def test_adapter_ping_unsupported_if_terminal_none() -> None:
    """PING returns unsupported when terminal_info response is missing."""

    class _NoTerminalTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "terminal_info":
                return None
            return await super().call(name, *args, **kwargs)

    transport = _NoTerminalTransport()
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.ping()
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())


def test_adapter_get_symbols_invalid_limit() -> None:
    """Retrieving symbols with an invalid limit raises ValueError."""
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        with pytest.raises(ValueError, match="positive symbol limit is required"):
            await adapter.get_symbols(limit=0)

    asyncio.run(exercise())


def test_adapter_get_ticks_invalid_parameters() -> None:
    """Retrieving ticks with missing or invalid parameters raises ValueError."""
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        msg = "tick start, end, and positive limit are required"
        with pytest.raises(ValueError, match=msg):
            await adapter.get_ticks("EURUSD", start=None, end=None, limit=0)

    asyncio.run(exercise())


def test_adapter_get_account_info_not_found() -> None:
    """A missing account payload returns the exact canonical account-not-found error."""

    class _NoAccountTransport(_FakeTransport):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.allow_account = True

        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "account_info" and not self.allow_account:
                return None
            return await super().call(name, *args, **kwargs)

    transport = _NoAccountTransport()
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        transport.allow_account = False
        result = await adapter.get_account_info()
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND

    asyncio.run(exercise())


def test_adapter_get_positions_invalid_limit() -> None:
    """Retrieving positions with an invalid limit raises ValueError."""
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        with pytest.raises(ValueError, match="positive position limit is required"):
            await adapter.get_positions(limit=0)

    asyncio.run(exercise())


def test_adapter_get_symbol_info_success() -> None:
    """Successfully retrieving symbol info returns a valid mapped BrokerSymbolInfo."""

    class _SymbolTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbol_info":
                return {
                    "name": "EURUSD",
                    "digits": 5,
                    "volume_step": 0.01,
                    "volume_min": 0.01,
                    "volume_max": 100,
                }
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=_SymbolTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbol_info("EURUSD")
        assert result.is_success
        assert result.data is not None
        assert result.data.provider_symbol == "EURUSD"

    asyncio.run(exercise())


def test_adapter_get_quote_not_found() -> None:
    """A missing tick returns symbol not found error."""

    class _NoQuoteTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbol_info_tick":
                return None
            return await super().call(name, *args, **kwargs)

    transport = _NoQuoteTransport()
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_quote("EURUSD")
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND

    asyncio.run(exercise())
