"""Bounded transport evidence for FEAT-DATA-16."""

from datetime import UTC, datetime
from typing import Self

import pytest
from app.services.data import retrieve_research_provider_payload


class _Response:
    """Minimal bounded response."""

    def __init__(
        self,
        payload: bytes,
        url: str = "https://api.fiscaldata.treasury.gov/example",
    ) -> None:
        self.payload = payload
        self.url = url
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]

    def geturl(self) -> str:
        return self.url


def test_transport_enforces_host_bounds_and_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retrieve approved bytes and reject unsafe or excessive access."""
    monkeypatch.setattr(
        "app.services.data.sources.research_transport.urlopen",
        lambda *_args, **_kwargs: _Response(b'{"data":[]}'),
    )
    now = datetime(2026, 1, 1, tzinfo=UTC)
    payload = retrieve_research_provider_payload(
        "treasury-test",
        "https://api.fiscaldata.treasury.gov/example",
        allowed_hosts=("api.fiscaldata.treasury.gov",),
        user_agent="HaruQuantAI test@example.invalid",
        now=now,
        rate_limit=1,
    )
    assert payload == b'{"data":[]}'
    with pytest.raises(Exception, match="LIMIT_EXCEEDED"):
        retrieve_research_provider_payload(
            "treasury-test",
            "https://api.fiscaldata.treasury.gov/example",
            allowed_hosts=("api.fiscaldata.treasury.gov",),
            user_agent="HaruQuantAI test@example.invalid",
            now=now,
            rate_limit=1,
        )
    with pytest.raises(Exception, match="INVALID_INPUT"):
        retrieve_research_provider_payload(
            "bad",
            "http://example.test",
            allowed_hosts=("example.test",),
            user_agent="agent",
            now=now,
        )


def test_transport_bounds_failures_and_circuit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject oversized payloads and open a circuit after repeated failures."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.data.sources.research_transport.urlopen",
        lambda *_args, **_kwargs: _Response(b"0123456789", "https://example.test/data"),
    )
    with pytest.raises(Exception, match="LIMIT_EXCEEDED"):
        retrieve_research_provider_payload(
            "oversized-test",
            "https://example.test/data",
            allowed_hosts=("example.test",),
            user_agent="test",
            max_bytes=5,
            now=now,
        )

    def _offline(*_args: object, **_kwargs: object) -> None:
        raise OSError("offline")

    monkeypatch.setattr(
        "app.services.data.sources.research_transport.urlopen",
        _offline,
    )
    for offset in range(3):
        with pytest.raises(Exception, match="SOURCE_UNAVAILABLE"):
            retrieve_research_provider_payload(
                "circuit-test",
                "https://example.test/data",
                allowed_hosts=("example.test",),
                user_agent="test",
                rate_limit=10,
                now=now.replace(second=offset),
            )
    with pytest.raises(Exception, match="CIRCUIT_BREAKER_OPEN"):
        retrieve_research_provider_payload(
            "circuit-test",
            "https://example.test/data",
            allowed_hosts=("example.test",),
            user_agent="test",
            rate_limit=10,
            now=now.replace(second=3),
        )


def test_transport_rejects_unapproved_response_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject redirects and response media outside the approved contract."""
    response = _Response(b"content", "https://unapproved.test/data")
    response.headers = {"Content-Type": "text/html"}
    monkeypatch.setattr(
        "app.services.data.sources.research_transport.urlopen",
        lambda *_args, **_kwargs: response,
    )
    with pytest.raises(Exception, match="INVALID_INPUT"):
        retrieve_research_provider_payload(
            "metadata-test",
            "https://example.test/data",
            allowed_hosts=("example.test",),
            user_agent="test",
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
