"""Dukascopy web-chart tick transport tests."""

import asyncio
import json
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Self

import pytest
from app.services.brokers.canonical_contracts import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.canonical_contracts.protocols import _ProviderResponseError
from app.services.brokers.dukascopy.transport import _DukascopyTransport

_START = datetime(2026, 1, 5, 12, tzinfo=UTC)


def _config() -> BrokerConnectionConfig:
    """Return one bounded test configuration."""
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
    """Minimal context-managed response."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> Self:
        """Enter the response context.

        Returns:
            This response.
        """
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Exit the response context.

        Args:
            *exc_info: Context-manager exception details.
        """
        return

    def read(self) -> bytes:
        """Return the response body.

        Returns:
            Recorded response bytes.
        """
        return self._payload


def _response(request: object, rows: list[list[object]]) -> _FakeResponse:
    """Build provider JSONP using the requested callback.

    Args:
        request: Captured urllib request.
        rows: Provider rows to encode.

    Returns:
        Fake provider response.
    """
    query = urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)  # type: ignore[attr-defined]
    callback = query["jsonp"][0]
    return _FakeResponse(f"{callback}({json.dumps(rows)});".encode())


def test_transport_retrieves_bounded_tick_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The legacy-proven web contract returns bounded raw ticks."""
    start_ms = int(_START.timestamp() * 1000)
    captured: dict[str, object] = {}

    def _urlopen(request: object, timeout: float) -> _FakeResponse:
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        captured["headers"] = request.headers  # type: ignore[attr-defined]
        captured["timeout"] = timeout
        return _response(request, [[start_ms, 1.1, 1.2, 2_000_000, 3_000_000]])

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    result = asyncio.run(
        _DukascopyTransport(_config()).get_ticks(
            "EURUSD", _START, _START + timedelta(hours=1), 1
        )
    )
    assert len(result) == 1
    assert "instrument=EUR%2FUSD" in str(captured["url"])
    assert "interval=TICK" in str(captured["url"])
    assert str(captured["headers"]).find("Mozilla") >= 0
    assert captured["timeout"] == 1


def test_transport_rejects_invalid_jsonp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Malformed provider envelopes fail closed."""
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: _FakeResponse(b"wrong([]);"),
    )

    async def _exercise() -> None:
        """Run the failing transport call."""
        with pytest.raises(_ProviderResponseError, match="JSONP envelope"):
            await _DukascopyTransport(_config()).get_ticks(
                "EURUSD", _START, _START + timedelta(hours=1), 1
            )

    asyncio.run(_exercise())


def test_transport_rejects_invalid_bounds() -> None:
    """Invalid caller bounds fail before provider access."""

    async def _exercise() -> None:
        """Run the invalid bounded call."""
        with pytest.raises(ValueError, match="ordered tick range"):
            await _DukascopyTransport(_config()).get_ticks("EURUSD", _START, _START, 0)

    asyncio.run(_exercise())
