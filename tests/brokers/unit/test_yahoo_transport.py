"""Yahoo transport tests using a fake in-process yfinance module."""

import asyncio
import sys
import types

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.yahoo_history.transport import _YahooTransport


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=0.1,
        circuit_half_open_max_calls=1,
    )


def _install_fake_yfinance(monkeypatch: pytest.MonkeyPatch, table: object) -> list[str]:
    requested: list[str] = []

    class _Ticker:
        def __init__(self, symbol: str) -> None:
            requested.append(symbol)

        def history(
            self, *, interval: str, start: object, end: object, timeout: float
        ) -> object:
            del interval, start, end, timeout
            return table

    fake_module = types.SimpleNamespace(Ticker=_Ticker)
    monkeypatch.setitem(sys.modules, "yfinance", fake_module)
    return requested


def test_transport_history_returns_the_public_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The transport returns the exact public table produced by one call."""
    table = object()
    requested = _install_fake_yfinance(monkeypatch, table)
    transport = _YahooTransport(_config())

    result = asyncio.run(
        transport.history(symbol="AAPL", timeframe="1d", start=None, end=None)
    )

    assert result is table
    assert requested == ["AAPL"]


def test_repeated_transport_failures_open_the_circuit_and_stop_provider_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After the failure threshold, further calls never reach the provider SDK."""
    call_count = 0

    class _FailingTicker:
        def __init__(self, symbol: str) -> None:
            del symbol

        def history(
            self, *, interval: str, start: object, end: object, timeout: float
        ) -> object:
            nonlocal call_count
            del interval, start, end, timeout
            call_count += 1
            raise TimeoutError

    monkeypatch.setitem(
        sys.modules, "yfinance", types.SimpleNamespace(Ticker=_FailingTicker)
    )
    transport = _YahooTransport(_config())

    async def exercise() -> None:
        for _ in range(2):
            with pytest.raises(TimeoutError):
                await transport.history(
                    symbol="AAPL", timeframe="1d", start=None, end=None
                )
        assert transport._circuit.state == "open"
        with pytest.raises(ConnectionError, match="CIRCUIT_OPEN"):
            await transport.history(symbol="AAPL", timeframe="1d", start=None, end=None)

    asyncio.run(exercise())
    assert call_count == 2


def test_circuit_recovers_after_timeout_on_next_successful_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A half-open probe that succeeds closes the circuit again."""
    attempt = 0

    class _RecoveringTicker:
        def __init__(self, symbol: str) -> None:
            del symbol

        def history(
            self, *, interval: str, start: object, end: object, timeout: float
        ) -> object:
            nonlocal attempt
            del interval, start, end, timeout
            attempt += 1
            if attempt <= 2:
                raise TimeoutError
            return object()

    monkeypatch.setitem(
        sys.modules, "yfinance", types.SimpleNamespace(Ticker=_RecoveringTicker)
    )
    transport = _YahooTransport(_config())

    async def exercise() -> None:
        for _ in range(2):
            with pytest.raises(TimeoutError):
                await transport.history(
                    symbol="AAPL", timeframe="1d", start=None, end=None
                )
        assert transport._circuit.state == "open"
        await asyncio.sleep(0.11)
        result = await transport.history(
            symbol="AAPL", timeframe="1d", start=None, end=None
        )
        assert result is not None
        assert transport._circuit.state == "closed"

    asyncio.run(exercise())
