"""Verify release checks through controlled HTTP transports.

Description:
    Qualifies bounded provider results without a production feed or network.
Purpose:
    FEAT-HOME-DASHBOARD: Release comparison and failure qualification.
Key Capabilities:
    - FR-HOME-UPDATES: Assert public checks, logging, caching and input limits.
Python API Usage:
    pytest.main(["tests/unit/workspace/home/test_releases.py", "--no-cov"])
CLI Usage:
    uv run pytest tests/unit/workspace/home/test_releases.py --no-cov
"""

import asyncio
import logging
from typing import Any
from unittest.mock import Mock

import httpx
import pytest
from app.host.transport import ServletConstants
from app.workspace.home import Home
from app.workspace.home._releases import ReleaseFeed


def _payload(**updates: Any) -> dict[str, Any]:
    return {
        "latest_version": "1.1.0",
        "published_at": "2026-10-21T00:00:00Z",
        "changelog": "Original release notes",
        "release_url": "https://example.invalid/releases/1.1.0",
        **updates,
    }


@pytest.mark.parametrize(
    ("latest", "expected"),
    [("1.1.0", True), ("1.0.0", False), ("0.9.0", False), ("1.0.10", True)],
)
def test_release_comparison_cache_and_safe_request(
    latest: str, expected: bool, caplog: pytest.LogCaptureFixture
) -> None:
    requests: list[httpx.Request] = []
    now = [0.0]

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_payload(latest_version=latest))

    feed = ReleaseFeed(
        "https://example.invalid/feed",
        transport=httpx.MockTransport(respond),
        clock=lambda: now[0],
    )
    constants = Mock(spec=ServletConstants)
    constants.get_constants.return_value = {"version": "1.0.0"}
    home = Home(constants, feed)
    caplog.set_level(logging.INFO)
    result = home.check_updates()
    assert result["update_available"] is expected
    result["state"] = "tampered"
    assert home.check_updates()["state"] == "available"
    assert len(requests) == 1
    assert not requests[0].content
    assert "authorization" not in requests[0].headers
    now[0] = 61.0
    assert home.check_updates()["latest_version"] == latest
    assert len(requests) == 2
    assert any(r.__dict__.get("fr_id") == "FR-HOME-UPDATES" for r in caplog.records)


@pytest.mark.parametrize(
    "url",
    [
        None,
        "http://example.invalid/feed",
        "https://user:pass@example.invalid/feed",
        "https://example.invalid/feed?token=secret",
        "https://example.invalid/#fragment",
    ],
)
def test_unavailable_or_unsafe_address_never_sends(url: str | None) -> None:
    handler = Mock()
    result = ReleaseFeed(url, transport=httpx.MockTransport(handler)).check("1.0.0")
    assert result["state"] == ("unavailable" if url is None else "unsupported")
    assert result["update_available"] is None
    handler.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [b"not json", b"{}", b"x" * (256 * 1024 + 1)],
    ids=["invalid-json", "missing-fields", "oversized"],
)
def test_invalid_and_oversized_response(body: bytes) -> None:
    result = ReleaseFeed(
        "https://example.invalid/feed",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=body)
        ),
    ).check("1.0.0")
    assert result["state"] == "unsupported"
    assert result["update_available"] is None


@pytest.mark.parametrize(
    "patch",
    [
        {"latest_version": "1.2.0-beta"},
        {"published_at": "2026-10-21"},
        {"release_url": "javascript:alert(1)"},
    ],
)
def test_unsupported_release_contract(patch: dict[str, Any]) -> None:
    result = ReleaseFeed(
        "https://example.invalid/feed",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=_payload(**patch))
        ),
    ).check("1.0.0")
    assert result["state"] == "unsupported"


@pytest.mark.parametrize("status", [301, 404, 500])
def test_http_failures_are_not_up_to_date(status: int) -> None:
    result = ReleaseFeed(
        "https://example.invalid/feed",
        transport=httpx.MockTransport(lambda request: httpx.Response(status)),
    ).check("1.0.0")
    assert result["state"] == "error"
    assert result["update_available"] is None


def test_network_failure_is_redacted_and_cached(
    caplog: pytest.LogCaptureFixture,
) -> None:
    handler = Mock(side_effect=httpx.ReadTimeout("sensitive-error-details"))
    feed = ReleaseFeed(
        "https://example.invalid/feed", transport=httpx.MockTransport(handler)
    )
    assert feed.check("1.0.0")["state"] == "error"
    assert feed.check("1.0.0")["state"] == "error"
    assert handler.call_count == 1
    assert "sensitive-error-details" not in caplog.text


def test_total_budget_cancels_provider() -> None:
    closed = []

    async def delayed(request: httpx.Request) -> httpx.Response:
        try:
            await asyncio.sleep(30)
        finally:
            closed.append(True)
        return httpx.Response(200, json=_payload())

    assert (
        ReleaseFeed(
            "https://example.invalid/feed", transport=httpx.MockTransport(delayed)
        ).check("1.0.0")["state"]
        == "error"
    )
    assert closed == [True]
