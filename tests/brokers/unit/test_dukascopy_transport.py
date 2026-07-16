"""Dukascopy transport tests using a mocked HTTP response."""

import asyncio
import lzma
from datetime import UTC, datetime
from typing import Self

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.dukascopy.transport import _DukascopyTransport


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.DUKASCOPY,
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


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def test_transport_decompresses_bounded_hour_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A retrieved hour file is decompressed and returned verbatim."""
    raw = b"tick-bytes"
    compressed = lzma.compress(raw)
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: _FakeResponse(compressed)
    )
    transport = _DukascopyTransport(_config())

    result = asyncio.run(transport.get_hour("EURUSD", datetime(2026, 1, 1, tzinfo=UTC)))

    assert result == raw


def test_transport_surfaces_malformed_compressed_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-LZMA payload raises rather than returning corrupted bytes."""
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: _FakeResponse(b"not-lzma")
    )
    transport = _DukascopyTransport(_config())

    async def exercise() -> None:
        with pytest.raises(lzma.LZMAError):
            await transport.get_hour("EURUSD", datetime(2026, 1, 1, tzinfo=UTC))

    asyncio.run(exercise())


def test_transport_builds_zero_indexed_month_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dukascopy's zero-indexed month convention is applied to the request URL."""
    captured: dict[str, str] = {}

    def _fake_urlopen(request: object, timeout: float) -> _FakeResponse:
        del timeout
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        return _FakeResponse(lzma.compress(b""))

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    transport = _DukascopyTransport(_config())

    asyncio.run(transport.get_hour("EURUSD", datetime(2026, 3, 15, 9, tzinfo=UTC)))

    assert "/EURUSD/2026/02/15/09h_ticks.bi5" in captured["url"]
