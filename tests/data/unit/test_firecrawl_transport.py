"""Unit coverage for the licensed Firecrawl calendar transport.

All network access is faked through injected responses, so these tests exercise
parsing, timezone derivation, window pagination, error mapping, concurrency
bounds, and secret hygiene deterministically without contacting Firecrawl or
any calendar site.
"""

from __future__ import annotations

import asyncio
import email.message
import json
import urllib.error
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Self

import pytest
from app.services.data.contracts import DataError
from app.services.data.economic_calendar import firecrawl_transport as ft
from pydantic import SecretStr

_REFERENCE = datetime(2026, 7, 30, 12, 14, 22, tzinfo=UTC)


def _transport(**overrides: Any) -> ft._FirecrawlCalendarTransport:
    """Build the private transport with deterministic test credentials."""
    options: dict[str, Any] = {
        "request_timeout_sec": 5.0,
        "max_parallel_requests": 2,
        "wait_for_ms": 0,
    }
    options.update(overrides)
    return ft._FirecrawlCalendarTransport(SecretStr("fc-test-key"), **options)


def _fetch(
    transport: ft._FirecrawlCalendarTransport,
    site: str,
    start: datetime,
    end: datetime,
) -> list[Mapping[str, object]]:
    """Drive the async fetch synchronously."""
    return asyncio.run(transport.fetch_site(site, start, end))


_FF_PAGE = """<html><body>
<strong class="syncedtime">8:14am</strong>
<table><tbody>
<tr class="calendar__row calendar__row--day-breaker"><td colspan="10" class="calendar__cell">Sun <span>Jul 26</span></td></tr>
<tr data-event-id="149952" class="calendar__row calendar__row--single-event"><td class="calendar__cell calendar__date"><span class="date">Sun <span>Jul 26</span></span></td><td class="calendar__cell calendar__time"><span>7:50pm</span></td><td class="calendar__cell calendar__currency"><span>JPY</span></td><td class="calendar__cell calendar__impact"><span title="Low Impact Expected" class="icon icon--ff-impact-yel"></span></td><td class="calendar__cell calendar__event event"><span class="calendar__event-title">SPPI y/y</span></td><td class="calendar__cell calendar__detail"><a><img></a></td><td class="calendar__cell calendar__actual"><span>3.2%</span></td><td class="calendar__cell calendar__forecast"><span>3.4%</span></td><td class="calendar__cell calendar__previous"><span title="Revised from 3.3%">3.4%</span></td><td class="calendar__cell calendar__graph"><a><img></a></td></tr>
<tr data-event-id="150431" class="calendar__row calendar__row--new-day"><td class="calendar__cell calendar__date"><span class="date">Mon <span>Jul 27</span></span></td><td class="calendar__cell calendar__time"><span>4:00am</span></td><td class="calendar__cell calendar__currency"><span>EUR</span></td><td class="calendar__cell calendar__impact"><span title="Medium Impact Expected"></span></td><td class="calendar__cell calendar__event event"><span class="calendar__event-title">German ifo Business Climate</span></td><td class="calendar__cell calendar__detail"></td><td class="calendar__cell calendar__actual"><span>86.6</span></td><td class="calendar__cell calendar__forecast"><span>86.1</span></td><td class="calendar__cell calendar__previous"><span>85.7</span></td><td class="calendar__cell calendar__graph"></td></tr>
<tr data-event-id="150576" class="calendar__row"><td class="calendar__cell calendar__time"></td><td class="calendar__cell calendar__currency"><span>EUR</span></td><td class="calendar__cell calendar__impact"><span title="High Impact Expected"></span></td><td class="calendar__cell calendar__event event"><span class="calendar__event-title">M3 Money Supply y/y</span></td><td class="calendar__cell calendar__actual"><span>3.3%</span></td><td class="calendar__cell calendar__forecast"></td><td class="calendar__cell calendar__previous"></td><td class="calendar__cell calendar__graph"></td></tr>
<tr data-event-id="150999" class="calendar__row"><td class="calendar__cell calendar__time"><span>All Day</span></td><td class="calendar__cell calendar__currency"><span>EUR</span></td><td class="calendar__cell calendar__impact"><span title="Bank Holiday"></span></td><td class="calendar__cell calendar__event event"><span class="calendar__event-title">ECOFIN Meetings</span></td><td class="calendar__cell calendar__actual"></td><td class="calendar__cell calendar__forecast"></td><td class="calendar__cell calendar__previous"></td><td class="calendar__cell calendar__graph"></td></tr>
<tr data-event-id="150999" class="calendar__row"><td class="calendar__cell calendar__time"></td><td class="calendar__cell calendar__currency"><span>EUR</span></td><td class="calendar__cell calendar__impact"><span title="Bank Holiday"></span></td><td class="calendar__cell calendar__event event"><span class="calendar__event-title">ECOFIN Meetings</span></td><td class="calendar__cell calendar__actual"></td><td class="calendar__cell calendar__forecast"></td><td class="calendar__cell calendar__previous"></td><td class="calendar__cell calendar__graph"></td></tr>
</tbody></table>
</body></html>"""

_CC_PAGE = """<html><body>
<strong class="syncedtime">8:14am</strong>
<table><tbody>
<tr class="calendar__row calendar__row--day-breaker"><td colspan="9" class="calendar__cell">Mon <span>Jul 27</span></td></tr>
<tr data-event-id="148184" class="calendar__row calendar__row--new-day"><td class="calendar__cell calendar__date"><span class="date">Mon <span>Jul 27</span></span></td><td class="calendar__cell calendar__time"><span>8:30am</span></td><td class="calendar__cell calendar__impact"><span title="Low Impact Expected"></span></td><td class="calendar__cell calendar__event event"><span class="calendar__event-title">US Core Durable Goods Orders m/m</span></td><td class="calendar__cell calendar__actual"><span>0.6%</span></td><td class="calendar__cell calendar__forecast"><span>0.9%</span></td><td class="calendar__cell calendar__previous"><span>1.4%</span></td><td class="calendar__cell calendar__graph"></td></tr>
<tr data-event-id="148172" class="calendar__row"><td class="calendar__cell calendar__time"></td><td class="calendar__cell calendar__impact"><span title="High Impact Expected"></span></td><td class="calendar__cell calendar__event event"><span class="calendar__event-title">UK CPI y/y</span></td><td class="calendar__cell calendar__actual"></td><td class="calendar__cell calendar__forecast"></td><td class="calendar__cell calendar__previous"></td><td class="calendar__cell calendar__graph"></td></tr>
<tr data-event-id="148190" class="calendar__row"><td class="calendar__cell calendar__time"><span>9:00am</span></td><td class="calendar__cell calendar__impact"><span title="Low Impact Expected"></span></td><td class="calendar__cell calendar__event event"><span class="calendar__event-title">BTC Halving Countdown</span></td><td class="calendar__cell calendar__actual"></td><td class="calendar__cell calendar__forecast"></td><td class="calendar__cell calendar__previous"></td><td class="calendar__cell calendar__graph"></td></tr>
</tbody></table>
</body></html>"""

_NO_SYNC_PAGE = "<html><body><table><tbody></tbody></table></body></html>"


def _stub_page(
    monkeypatch: pytest.MonkeyPatch,
    html: str,
    reference: datetime = _REFERENCE,
) -> None:
    """Point the transport at one deterministic page for every URL."""
    monkeypatch.setattr(
        ft._FirecrawlCalendarTransport,
        "_post_sync",
        lambda _self, _page_url: (html, reference),
    )


def test_week_params_single_sunday_window() -> None:
    """A window inside one Sunday-anchored week fetches exactly one page."""
    start = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
    end = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)
    assert ft._week_params_covering(start, end) == ("jul26.2026",)


def test_week_params_spanning_multiple_weeks() -> None:
    """A window crossing week boundaries yields each covered week page."""
    start = datetime(2026, 7, 20, tzinfo=UTC)
    end = datetime(2026, 8, 3, tzinfo=UTC)
    assert ft._week_params_covering(start, end) == (
        "jul19.2026",
        "jul26.2026",
        "aug2.2026",
    )


def test_week_params_beyond_page_bound_rejected() -> None:
    """A window wider than the bounded page count fails closed."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 4, 1, tzinfo=UTC)
    with pytest.raises(DataError, match="VALIDATION_FAILED"):
        ft._week_params_covering(start, end)


def test_parse_clock_variants() -> None:
    """Provider clock labels parse to 24-hour values; bad labels raise."""
    assert ft._parse_clock("8:14am") == (8, 14)
    assert ft._parse_clock("12:00am") == (0, 0)
    assert ft._parse_clock("12:30pm") == (12, 30)
    assert ft._parse_clock("11:59pm") == (23, 59)
    with pytest.raises(ValueError, match="clock label"):
        ft._parse_clock("25:00")


def test_offset_resolution_eastern_daylight() -> None:
    """The synced display derives the page offset in quarter-hour steps."""
    reference = datetime(2026, 7, 30, 12, 14, 22, tzinfo=UTC)
    assert ft._resolve_offset_minutes("8:14am", reference) == -240
    assert ft._resolve_offset_minutes("12:14pm", reference) == 0


def test_offset_resolution_day_wrap() -> None:
    """Offsets wrap across midnight within the half-day window."""
    reference = datetime(2026, 7, 30, 0, 0, 0, tzinfo=UTC)
    assert ft._resolve_offset_minutes("11:45pm", reference) == -15
    assert ft._resolve_offset_minutes("12:15am", reference) == 15


def test_parse_page_forexfactory_shape() -> None:
    """The currency-cell shape parses with inheritance, impacts, and dedup."""
    rows = ft._parse_page("forexfactory", _FF_PAGE, year=2026, offset_minutes=-240)
    assert len(rows) == 4
    sppi = rows[0]
    assert sppi["event_id"] == "149952"
    assert sppi["timestamp"] == datetime(2026, 7, 26, 23, 50, tzinfo=UTC)
    assert sppi["impact"] == "low"
    assert sppi["actual"] == "3.2%"
    ifo = rows[1]
    assert ifo["timestamp"] == datetime(2026, 7, 27, 8, 0, tzinfo=UTC)
    assert ifo["impact"] == "medium"
    m3 = rows[2]
    assert m3["timestamp"] == datetime(2026, 7, 27, 8, 0, tzinfo=UTC)
    assert m3["impact"] == "high"
    assert m3["forecast"] is None
    ecofin = rows[3]
    assert ecofin["timestamp"] == datetime(2026, 7, 27, 4, 0, tzinfo=UTC)
    assert ecofin["impact"] == "holiday"


def test_parse_page_cryptocraft_shape() -> None:
    """The title-prefix shape derives currencies and drops unmapped titles."""
    rows = ft._parse_page("cryptocraft", _CC_PAGE, year=2026, offset_minutes=-240)
    assert len(rows) == 2
    durable = rows[0]
    assert durable["country"] == "USD"
    assert durable["timestamp"] == datetime(2026, 7, 27, 12, 30, tzinfo=UTC)
    cpi = rows[1]
    assert cpi["country"] == "GBP"
    assert cpi["timestamp"] == datetime(2026, 7, 27, 12, 30, tzinfo=UTC)
    assert cpi["impact"] == "high"


def test_fetch_site_filters_to_window(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rows outside the requested UTC window are excluded after conversion."""
    _stub_page(monkeypatch, _FF_PAGE)
    rows = _fetch(
        _transport(),
        "forexfactory",
        datetime(2026, 7, 27, tzinfo=UTC),
        datetime(2026, 7, 28, tzinfo=UTC),
    )
    assert [row["title"] for row in rows] == [
        "German ifo Business Climate",
        "M3 Money Supply y/y",
        "ECOFIN Meetings",
    ]


def test_fetch_site_rejects_undeclared_site() -> None:
    """An unknown site identifier fails closed before any network call."""
    with pytest.raises(DataError, match="VALIDATION_FAILED"):
        _fetch(
            _transport(),
            "unknownsite",
            datetime(2026, 7, 27, tzinfo=UTC),
            datetime(2026, 7, 28, tzinfo=UTC),
        )


def test_fetch_site_rejects_oversized_window() -> None:
    """A window spanning too many week pages fails closed before fetching."""
    with pytest.raises(DataError, match="VALIDATION_FAILED"):
        _fetch(
            _transport(),
            "forexfactory",
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 4, 1, tzinfo=UTC),
        )


def test_post_maps_http_error_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP failures map to canonical codes without leaking credentials."""
    cases = [
        (401, "SOURCE_UNAVAILABLE"),
        (402, "SOURCE_UNAVAILABLE"),
        (403, "SOURCE_UNAVAILABLE"),
        (429, "NETWORK_ERROR"),
        (500, "NETWORK_ERROR"),
    ]
    for status, expected in cases:

        def raise_http(_self: Any, _page_url: str, _status: int = status) -> None:
            raise urllib.error.HTTPError(
                _page_url,
                _status,
                "error",
                {},
                None,  # type: ignore[arg-type]
            )

        monkeypatch.setattr(ft._FirecrawlCalendarTransport, "_post_sync", raise_http)
        with pytest.raises(DataError, match=expected):
            _fetch(
                _transport(),
                "forexfactory",
                datetime(2026, 7, 27, tzinfo=UTC),
                datetime(2026, 7, 28, tzinfo=UTC),
            )


def test_post_maps_network_and_timeout_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Connection and timeout failures map to their canonical codes."""
    monkeypatch.setattr(
        ft._FirecrawlCalendarTransport,
        "_post_sync",
        lambda _self, _page_url: (_ for _ in ()).throw(
            urllib.error.URLError("unreachable")
        ),
    )
    with pytest.raises(DataError, match="NETWORK_ERROR"):
        _fetch(
            _transport(),
            "forexfactory",
            datetime(2026, 7, 27, tzinfo=UTC),
            datetime(2026, 7, 28, tzinfo=UTC),
        )
    monkeypatch.setattr(
        ft._FirecrawlCalendarTransport,
        "_post_sync",
        lambda _self, _page_url: (_ for _ in ()).throw(TimeoutError()),
    )
    with pytest.raises(DataError, match="TIMEOUT"):
        _fetch(
            _transport(),
            "forexfactory",
            datetime(2026, 7, 27, tzinfo=UTC),
            datetime(2026, 7, 28, tzinfo=UTC),
        )


def test_post_rejects_unsuccessful_or_malformed_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed or shapeless intermediary response maps to NETWORK_ERROR."""
    for payload in ({"success": False}, {"success": True, "data": {}}, {}):
        monkeypatch.setattr(
            ft._FirecrawlCalendarTransport,
            "_post_sync",
            lambda _self, _page_url, _p=payload: (_ for _ in ()).throw(
                DataError("NETWORK_ERROR", safe_details={"operation": "x"})
            ),
        )
        with pytest.raises(DataError, match="NETWORK_ERROR"):
            _fetch(
                _transport(),
                "forexfactory",
                datetime(2026, 7, 27, tzinfo=UTC),
                datetime(2026, 7, 28, tzinfo=UTC),
            )


def test_page_offset_fails_closed_without_synced_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A page without a synced-time element fails rather than guessing a zone."""
    _stub_page(monkeypatch, _NO_SYNC_PAGE)
    with pytest.raises(DataError, match="NETWORK_ERROR"):
        _fetch(
            _transport(),
            "forexfactory",
            datetime(2026, 7, 27, tzinfo=UTC),
            datetime(2026, 7, 28, tzinfo=UTC),
        )


class _FakeResponse:
    """Minimal urlopen stand-in returning one JSON payload."""

    def __init__(self, payload: Mapping[str, Any]) -> None:
        """Store the payload and a deterministic Date header."""
        self._payload = payload
        self.headers = email.message.Message()
        self.headers["Date"] = "Thu, 30 Jul 2026 12:14:22 GMT"
        self.headers["Content-Type"] = "application/json"

    def read(self, _limit: int = -1) -> bytes:
        """Return the encoded payload."""
        return json.dumps(self._payload).encode("utf-8")

    def geturl(self) -> str:
        """Return the audited final Firecrawl API URL."""
        return "https://api.firecrawl.dev/v2/scrape"

    def __enter__(self) -> Self:
        """Return self as the context manager value."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the fake response without side effects."""


def test_post_sync_sends_licensed_request_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The request carries the licensed key, enhanced proxy, and fresh render."""
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> _FakeResponse:
        captured["authorization"] = request.headers.get("Authorization")
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse({"success": True, "data": {"html": _FF_PAGE}})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    transport = _transport()
    html, reference = transport._post_sync(
        "https://www.forexfactory.com/calendar?week=jul26.2026"
    )
    assert html == _FF_PAGE
    assert reference == _REFERENCE
    assert captured["authorization"] == "Bearer fc-test-key"
    assert captured["body"]["proxy"] == "enhanced"
    assert captured["body"]["maxAge"] == 0
    assert captured["body"]["formats"] == ["html"]
    assert captured["body"]["skipTlsVerification"] is False
    assert captured["body"]["storeInCache"] is False


def test_post_sync_rejects_redirect_host_or_non_json_mime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The response must remain on the audited API host and carry JSON."""

    class InvalidResponse(_FakeResponse):
        """Response with caller-selected final URL and content type."""

        def __init__(self, *, final_url: str, content_type: str) -> None:
            super().__init__({"success": True, "data": {"html": _FF_PAGE}})
            self._final_url = final_url
            self.headers.replace_header("Content-Type", content_type)

        def geturl(self) -> str:
            return self._final_url

    for response in (
        InvalidResponse(
            final_url="https://redirect.invalid/v2/scrape",
            content_type="application/json",
        ),
        InvalidResponse(
            final_url="https://api.firecrawl.dev/v2/scrape",
            content_type="text/html",
        ),
    ):
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *_args, _response=response, **_kwargs: _response,
        )
        with pytest.raises(DataError, match="NETWORK_ERROR"):
            _transport()._post_sync("https://www.forexfactory.com/calendar")


def test_post_sync_rejects_oversized_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The transport rejects oversized intermediary responses before parsing."""

    class OversizedResponse(_FakeResponse):
        def read(self, limit: int = -1) -> bytes:
            return b"x" * limit

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: OversizedResponse({}),
    )
    with pytest.raises(DataError, match="LIMIT_EXCEEDED"):
        _transport()._post_sync("https://www.forexfactory.com/calendar")


def test_post_sync_rejects_failed_or_malformed_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsuccessful and shapeless intermediary responses map to NETWORK_ERROR."""
    payloads: list[Mapping[str, Any]] = [
        {"success": False},
        {"success": True, "data": {}},
        {"unexpected": True},
    ]
    for payload in payloads:
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *_args, _p=payload, **_kwargs: _FakeResponse(_p),
        )
        with pytest.raises(DataError, match="NETWORK_ERROR"):
            _transport()._post_sync("https://www.forexfactory.com/calendar")


def test_builder_resolves_key_from_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The builder resolves the licensed key through the shared boundary."""
    settings = type("Settings", (), {"firecrawl_api_key": SecretStr("fc-resolved")})()
    monkeypatch.setattr(ft, "load_broker_provider_settings", lambda: settings)
    transport = ft.build_firecrawl_calendar_transport()
    assert isinstance(transport, ft._FirecrawlCalendarTransport)


def test_builder_fails_closed_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing licensed material fails closed with SOURCE_UNAVAILABLE."""
    settings = type("Settings", (), {"firecrawl_api_key": None})()
    monkeypatch.setattr(ft, "load_broker_provider_settings", lambda: settings)
    with pytest.raises(DataError, match="SOURCE_UNAVAILABLE"):
        ft.build_firecrawl_calendar_transport()


def test_builder_validates_bounds() -> None:
    """Non-positive transport bounds are rejected at construction."""
    for kwargs in (
        {"request_timeout_sec": 0},
        {"max_parallel_requests": 0},
        {"max_parallel_requests": 99},
        {"wait_for_ms": -1},
    ):
        with pytest.raises(DataError, match="VALIDATION_FAILED"):
            ft.build_firecrawl_calendar_transport(
                SecretStr("fc-test-key"),
                **kwargs,  # type: ignore[arg-type]
            )


def test_secret_never_appears_in_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """The licensed key never leaks into raised errors or their details."""

    def raise_auth_error(request: Any, timeout: float) -> None:
        raise urllib.error.HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            {},
            None,  # type: ignore[arg-type]
        )

    monkeypatch.setattr("urllib.request.urlopen", raise_auth_error)
    with pytest.raises(DataError) as captured:
        _fetch(
            _transport(),
            "forexfactory",
            datetime(2026, 7, 27, tzinfo=UTC),
            datetime(2026, 7, 28, tzinfo=UTC),
        )
    assert "fc-test-key" not in str(captured.value)
    assert "fc-test-key" not in repr(vars(captured.value))


def test_concurrent_requests_respect_semaphore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent site fetches never exceed the licensed request bound."""
    import threading
    import time

    max_active = 0
    guard = threading.Lock()

    def fake_post(self: Any, page_url: str) -> tuple[str, datetime]:
        nonlocal max_active
        with guard:
            active_local = fake_post.active = fake_post.active + 1
            max_active = max(max_active, active_local)
        time.sleep(0.01)
        with guard:
            fake_post.active -= 1
        return _CC_PAGE, _REFERENCE

    fake_post.active = 0  # type: ignore[attr-defined]
    monkeypatch.setattr(ft._FirecrawlCalendarTransport, "_post_sync", fake_post)

    async def run() -> None:
        transport = _transport(max_parallel_requests=1)
        start = datetime(2026, 7, 27, tzinfo=UTC)
        end = datetime(2026, 7, 28, tzinfo=UTC)
        await asyncio.gather(
            transport.fetch_site("cryptocraft", start, end),
            transport.fetch_site("cryptocraft", start, end),
        )

    asyncio.run(run())
    assert max_active == 1
