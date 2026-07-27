"""Coverage expansion tests for Binance transport operations."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.adapter_runtime.circuit_breaker import _CircuitState
from app.services.brokers.binance_session.transport import _BinanceTransport
from app.services.brokers.contracts.protocols import (
    _CircuitOpenError,
    _RateLimitedError,
)
from pydantic import SecretStr


def _config(**overrides: object) -> BrokerConnectionConfig:
    values: dict[str, object] = {
        "broker_id": BrokerId.BINANCE_SPOT,
        "environment": BrokerEnvironment.TESTNET,
        "provider_enabled": True,
        "connect_timeout_sec": 1,
        "request_timeout_sec": 1,
        "transport_reconnect_max_attempts": 0,
        "stream_buffer_size": 2,
        "circuit_failure_threshold": 2,
        "circuit_recovery_timeout_sec": 1000,
        "circuit_half_open_max_calls": 1,
        "account_reference": "acc-1",
        "credentials": {
            "api_key": SecretStr("key-123"),
            "api_secret": SecretStr("sec-456"),
        },
    }
    values.update(overrides)
    return BrokerConnectionConfig(**values)  # type: ignore[arg-type]


def test_binance_transport_connect_success() -> None:
    """Verify connect initializes AsyncClient and probes ping & server_time."""
    transport = _BinanceTransport(_config())

    mock_client = MagicMock()
    mock_client.ping = AsyncMock(return_value={})
    mock_client.get_server_time = AsyncMock(return_value={"serverTime": 1700000000000})

    mock_module = MagicMock()
    mock_module.AsyncClient.create = AsyncMock(return_value=mock_client)

    async def run_test() -> None:
        with patch("importlib.import_module", return_value=mock_module):
            res = await transport.connect()
            assert res is True
            assert transport._client is mock_client

    asyncio.run(run_test())


def test_binance_transport_call_guard_checks() -> None:
    """Verify call checks client connection, rate limits, and circuit breaker state."""

    async def run_test() -> None:
        # Unconnected client
        transport = _BinanceTransport(_config())
        with pytest.raises(ConnectionError, match="Binance client is not connected"):
            await transport.call("ping")

        # Rate limited
        transport._client = MagicMock()
        transport._client.ping = AsyncMock(return_value={})
        transport._used_weight = 6000
        with pytest.raises(
            _RateLimitedError, match="Binance request-weight limit exhausted"
        ):
            await transport.call("ping")

        # Circuit open
        transport._used_weight = 0
        transport._circuit._state = _CircuitState.OPEN
        transport._circuit._opened_at = time.monotonic()
        with pytest.raises(
            _CircuitOpenError, match="Binance transport circuit is open"
        ):
            await transport.call("ping")

    asyncio.run(run_test())


def test_binance_transport_call_execution_and_errors() -> None:
    """
    Verify call executes method, records latency, updates weight, and handles errors.
    """
    latencies: list[float] = []

    def latency_sink(val: float) -> None:
        latencies.append(val)

    transport = _BinanceTransport(_config(), latency_sink=latency_sink)
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(return_value={"result": "ok"})
    mock_client.response.headers = {"X-MBX-USED-WEIGHT-1M": "150"}
    transport._client = mock_client

    async def run_test() -> None:
        res = await transport.call("ping")
        assert res == {"result": "ok"}
        assert transport._used_weight == 150
        assert len(latencies) == 1

        # Test call failure
        mock_client.ping.side_effect = OSError("connection reset")
        with pytest.raises(OSError, match="connection reset"):
            await transport.call("ping")

    asyncio.run(run_test())


def test_binance_transport_stream_guard_checks() -> None:
    """Verify stream checks connection state and circuit breaker before yielding."""

    async def run_test() -> None:
        transport = _BinanceTransport(_config())

        # Unconnected
        with pytest.raises(ConnectionError, match="Binance client is not connected"):
            async for _ in transport.stream("symbol_ticker_socket", symbol="BTCUSDT"):
                pass

        # Circuit open
        transport._client = MagicMock()
        transport._circuit._state = _CircuitState.OPEN
        transport._circuit._opened_at = time.monotonic()
        with pytest.raises(_CircuitOpenError, match="Binance stream circuit is open"):
            async for _ in transport.stream("symbol_ticker_socket", symbol="BTCUSDT"):
                pass

    asyncio.run(run_test())


def test_binance_transport_close() -> None:
    """Verify close releases client connection and socket manager."""
    transport = _BinanceTransport(_config())
    mock_client = MagicMock()
    mock_client.close_connection = AsyncMock()
    transport._client = mock_client
    transport._socket_manager = MagicMock()

    async def run_test() -> None:
        await transport.close()
        mock_client.close_connection.assert_called_once()
        assert transport._client is None
        assert transport._socket_manager is None

    asyncio.run(run_test())
