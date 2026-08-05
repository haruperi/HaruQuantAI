"""Unit evidence for the bounded credential-free calendar transport."""

import asyncio
from datetime import UTC, datetime
from typing import Self

import pytest
from app.services.data.contracts import DataError
from app.services.data.economic_calendar.reader_transport import (
    _parse_reader_markdown,
    _ReaderCalendarTransport,
    build_reader_calendar_transport,
)

_MARKDOWN = """Title: Forex Calendar | Forex Factory

| Date | Time | Currency | Impact | Event | Alerts | Detail | Actual | Forecast | Previous | Graph |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sun Mar 16 |
| Sun Mar 16 | 4:30pm | NZD | ![Impact](https://x/ff-impact-yel.png) | BusinessNZ Services Index |  | detail | 49.1 |  | 50.4 | graph |
| 7:01pm | GBP | ![Impact](https://x/ff-impact-red.png) | Rightmove HPI m/m |  | detail | 1.1% | 0.8% | 0.5% ![Revised](https://x/revised.svg) | graph |
| Mon Mar 17 |
| Mon Mar 17 | Day 1 | EUR | ![Impact](https://x/ff-impact-ora.png) | Finance Ministers Meeting |  | detail |  |  |  | graph |
| Jan 10th | USD | ![Impact](https://x/ff-impact-yel.png) | Undated Reference Row |  | detail | 3.8K |  | 8.3K | graph |
"""


def test_reader_markdown_preserves_values_and_converts_page_timezone() -> None:
    """Parse inherited dates and exact values using America/Chicago time."""
    rows = _parse_reader_markdown(_MARKDOWN, year=2025)

    assert len(rows) == 3
    assert rows[0]["timestamp"] == datetime(2025, 3, 16, 21, 30, tzinfo=UTC)
    assert rows[0]["actual"] == "49.1"
    assert rows[0]["forecast"] is None
    assert rows[0]["previous"] == "50.4"
    assert rows[1]["impact"] == "high"
    assert rows[1]["previous"] == "0.5%"
    assert rows[2]["timestamp"] == datetime(2025, 3, 17, 5, tzinfo=UTC)


def test_reader_transport_rejects_invalid_bounds_and_sites() -> None:
    """Fail closed for invalid transport bounds and non-Forex Factory sites."""
    with pytest.raises(DataError):
        _ReaderCalendarTransport(request_timeout_sec=0)
    transport = _ReaderCalendarTransport()
    with pytest.raises(DataError):
        asyncio.run(
            transport.fetch_site(
                "metalsmine",
                datetime(2025, 3, 16, tzinfo=UTC),
                datetime(2025, 3, 17, tzinfo=UTC),
            )
        )


def test_reader_transport_fetches_fixed_host_and_filters_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise the bounded HTTP handoff without contacting the network."""

    class _Response:
        """Minimal fixed-host response context."""

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def geturl(self) -> str:
            return "https://r.jina.ai/http://www.forexfactory.com/calendar"

        def read(self, _limit: int) -> bytes:
            return _MARKDOWN.encode()

    monkeypatch.setattr(
        "app.services.data.economic_calendar.reader_transport.urllib.request.urlopen",
        lambda *_args, **_kwargs: _Response(),
    )
    transport = build_reader_calendar_transport(request_timeout_sec=1)
    rows = asyncio.run(
        transport.fetch_site(
            "forexfactory",
            datetime(2025, 3, 16, tzinfo=UTC),
            datetime(2025, 3, 18, tzinfo=UTC),
        )
    )

    assert len(rows) == 3
