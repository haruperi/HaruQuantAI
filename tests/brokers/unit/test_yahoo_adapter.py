"""Yahoo adapter tests using an injected fake transport."""

import asyncio
from datetime import UTC, datetime

import pytest
from app.services.brokers.yahoo._legacy_types import (
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.yahoo.adapter import YahooBrokerAdapter


def _config(**overrides: object) -> BrokerConnectionConfig:
    values: dict[str, object] = {
        "broker_id": BrokerId.YAHOO,
        "environment": BrokerEnvironment.SANDBOX,
        "provider_enabled": True,
        "connect_timeout_sec": 1,
        "request_timeout_sec": 1,
        "transport_reconnect_max_attempts": 0,
        "stream_buffer_size": 2,
        "circuit_failure_threshold": 2,
        "circuit_recovery_timeout_sec": 1,
        "circuit_half_open_max_calls": 1,
    }
    values.update(overrides)
    return BrokerConnectionConfig(**values)  # type: ignore[arg-type]


class _FakeTransport:
    def __init__(self, *, fails: bool = False, table: object | None = None) -> None:
        self._fails = fails
        self._table = table
        self.requested_symbols: list[str] = []
        self.requested_timeframes: list[str] = []

    async def history(
        self, *, symbol: str, timeframe: str, start: object, end: object
    ) -> object:
        del start, end
        self.requested_symbols.append(symbol)
        self.requested_timeframes.append(timeframe)
        if self._fails:
            raise ConnectionError("unreachable")
        return self._table if self._table is not None else object()


class _Table:
    """Minimal yfinance-shaped history table."""

    def iterrows(self) -> object:
        """Return one genuine-shaped provider row."""
        return iter(
            (
                (
                    datetime(2026, 6, 1, 12, tzinfo=UTC),
                    {
                        "Open": 100,
                        "High": 101,
                        "Low": 99,
                        "Close": 100.5,
                        "Volume": 1000,
                    },
                ),
            )
        )


def test_adapter_rejects_non_sandbox_environment() -> None:
    """Yahoo accepts only the SANDBOX environment."""
    with pytest.raises(ValueError, match="sandbox-only"):
        YahooBrokerAdapter(_config(environment=BrokerEnvironment.DEMO))


def test_adapter_connect_without_probe_symbol_never_calls_transport() -> None:
    """No hidden default probe symbol is ever assumed."""
    transport = _FakeTransport()
    adapter = YahooBrokerAdapter(_config(), transport=transport)

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status != "success"
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CONFIGURATION_INVALID.value

    asyncio.run(exercise())
    assert transport.requested_symbols == []


def test_adapter_connect_with_probe_symbol_verifies_via_transport() -> None:
    """A configured probe symbol is used for a genuine verification call."""
    transport = _FakeTransport()
    adapter = YahooBrokerAdapter(_config(probe_symbol="AAPL"), transport=transport)

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status == "success"

    asyncio.run(exercise())
    assert transport.requested_symbols == ["AAPL"]
    assert transport.requested_timeframes == ["1d"]


def test_adapter_connect_fails_closed_when_probe_fails() -> None:
    """A failed probe never reports a successful connection."""
    transport = _FakeTransport(fails=True)
    adapter = YahooBrokerAdapter(_config(probe_symbol="AAPL"), transport=transport)

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status != "success"

    asyncio.run(exercise())


def test_adapter_get_historical_bars_requires_positive_limit() -> None:
    """A missing or non-positive limit is rejected before any transport call."""
    adapter = YahooBrokerAdapter(_config(), transport=_FakeTransport())
    adapter._state = BrokerConnectionState.READY

    async def exercise() -> None:
        result = await adapter.get_historical_bars("AAPL", "1d", limit=0)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID.value

    asyncio.run(exercise())


def test_adapter_maps_canonical_h1_to_yfinance_interval() -> None:
    """Canonical H1 requests use provider 1h while preserving request provenance."""
    transport = _FakeTransport(table=_Table())
    adapter = YahooBrokerAdapter(_config(), transport=transport)
    adapter._state = BrokerConnectionState.READY

    async def exercise() -> None:
        result = await adapter.get_historical_bars("AAPL", "H1", limit=1)
        assert result.data is not None
        bar = result.data.items[0]
        assert bar.provider_timeframe == "1h"
        assert bar.requested_timeframe == "H1"

    asyncio.run(exercise())
    assert transport.requested_timeframes == ["1h"]


def test_adapter_platform_info_is_explicitly_research_only() -> None:
    """Platform metadata exposes the provider and research-only posture."""
    adapter = YahooBrokerAdapter(_config(), transport=_FakeTransport())
    adapter._ENFORCE_DECLARED_AVAILABILITY = False
    adapter._state = BrokerConnectionState.READY

    async def exercise() -> None:
        result = await adapter.get_platform_info()
        assert result.data is not None
        assert result.data.provider_name == "Yahoo Finance"
        assert result.data.endpoint_metadata["research_only"] is True

    asyncio.run(exercise())
