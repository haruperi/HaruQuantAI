"""Yahoo transport tests using a fake in-process yfinance module."""

import asyncio
import sys
import types

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.yahoo.transport import _YahooTransport


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
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


def _install_fake_yfinance(monkeypatch: pytest.MonkeyPatch, table: object) -> list[str]:
    requested: list[str] = []

    class _Ticker:
        def __init__(self, symbol: str) -> None:
            requested.append(symbol)

        def history(self, *, interval: str, start: object, end: object) -> object:
            del interval, start, end
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


def test_transport_records_circuit_failure_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transport timeout is surfaced and counted by the circuit breaker."""

    class _TimeoutTicker:
        def __init__(self, symbol: str) -> None:
            del symbol

        def history(self, *, interval: str, start: object, end: object) -> object:
            del interval, start, end
            raise TimeoutError

    monkeypatch.setitem(
        sys.modules, "yfinance", types.SimpleNamespace(Ticker=_TimeoutTicker)
    )
    transport = _YahooTransport(_config())

    async def exercise() -> None:
        with pytest.raises(TimeoutError):
            await transport.history(symbol="AAPL", timeframe="1d", start=None, end=None)

    asyncio.run(exercise())
    assert transport._circuit.state == "closed"
