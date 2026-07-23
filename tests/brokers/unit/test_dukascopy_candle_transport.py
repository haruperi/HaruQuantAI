"""Dukascopy web-chart candle transport tests."""

import asyncio
import json
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Self

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.contracts.protocols import _ProviderResponseError
from app.services.brokers.dukascopy.candle_transport import (
    _DukascopyCandleTransport,
)

_START = datetime(2026, 6, 1, 12, tzinfo=UTC)


def _config(*, retries: int = 0) -> BrokerConnectionConfig:
    """Return one bounded Dukascopy transport configuration."""
    return BrokerConnectionConfig(
        broker_id=BrokerId.DUKASCOPY,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=retries,
        stream_buffer_size=2,
        circuit_failure_threshold=5,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


class _FakeResponse:
    """Minimal context-managed urllib response."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def read(self) -> bytes:
        """Return the recorded response body."""
        return self._payload


def _jsonp(request: object, rows: list[list[object]]) -> _FakeResponse:
    """Build a JSONP response using the callback from one request URL."""
    query = urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)  # type: ignore[attr-defined]
    callback = query["jsonp"][0]
    body = f"{callback}({json.dumps(rows)});".encode()
    return _FakeResponse(body)


def test_transport_maps_web_symbol_and_paginates_without_duplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forward pages map EURUSD to EUR/USD and remove cursor overlap."""
    start_ms = int(_START.timestamp() * 1000)
    calls: list[str] = []

    def _urlopen(request: object, timeout: float) -> _FakeResponse:
        del timeout
        calls.append(request.full_url)  # type: ignore[attr-defined]
        query = urllib.parse.parse_qs(urllib.parse.urlparse(calls[-1]).query)
        cursor = int(query["last_update"][0])
        if cursor == start_ms:
            rows = [
                [start_ms, 1, 2, 0, 1, 10],
                [start_ms + 3_600_000, 2, 3, 1, 2, 11],
            ]
        else:
            rows = [
                [start_ms + 3_600_000, 2, 3, 1, 2, 11],
                [start_ms + 7_200_000, 3, 4, 2, 3, 12],
            ]
        return _jsonp(request, rows)

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    transport = _DukascopyCandleTransport(_config())

    result = asyncio.run(
        transport.get_candles(
            "EURUSD",
            "H1",
            _START,
            _START + timedelta(hours=5),
            3,
        )
    )

    assert len(result.rows) == 3
    assert result.provider_symbol == "EUR/USD"
    assert result.provider_interval == "1HOUR"
    assert result.page_count == 2
    assert result.truncated
    assert "instrument=EUR%2FUSD" in calls[0]


def test_transport_retries_one_transient_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An idempotent page read retries within the configured bound."""
    attempts = 0
    waits: list[float] = []
    start_ms = int(_START.timestamp() * 1000)

    def _urlopen(request: object, timeout: float) -> _FakeResponse:
        nonlocal attempts
        del timeout
        attempts += 1
        if attempts == 1:
            raise OSError("temporary provider failure")
        return _jsonp(request, [[start_ms, 1, 2, 0, 1, 10]])

    async def _wait(delay: float) -> None:
        waits.append(delay)

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    transport = _DukascopyCandleTransport(_config(retries=1), waiter=_wait)

    result = asyncio.run(
        transport.get_candles(
            "EURUSD",
            "H1",
            _START,
            _START + timedelta(hours=1),
            1,
        )
    )

    assert len(result.rows) == 1
    assert attempts == 2
    assert waits == [0.25]


def test_transport_rejects_invalid_jsonp_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A response for another callback cannot be accepted as provider truth."""
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: _FakeResponse(b"wrong_callback([]);"),
    )
    transport = _DukascopyCandleTransport(_config())

    async def _exercise() -> None:
        with pytest.raises(_ProviderResponseError, match="JSONP envelope"):
            await transport.get_candles(
                "EURUSD",
                "H1",
                _START,
                _START + timedelta(hours=1),
                1,
            )

    asyncio.run(_exercise())
