"""Unit coverage for multi-site economic calendar scraping.

Network access is injected, so these tests exercise concurrency, cleaning,
validation, projection, persistence, and serialization deterministically without
contacting any external site.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from app.services.data.contracts import DataError
from app.services.data.economic_calendar.scraper import (
    CALENDAR_SITES,
    ScrapeOptions,
    ScrapeResult,
    scrape_economic_calendar,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_START = datetime(2026, 1, 1, tzinfo=UTC)
_END = datetime(2026, 1, 8, tzinfo=UTC)


def _row(**overrides: object) -> dict[str, object]:
    """Return one raw provider row with optional overrides."""
    row: dict[str, object] = {
        "timestamp": "2026-01-02T12:30:00Z",
        "title": "Non-Farm Employment Change",
        "country": "USD",
        "impact": "High",
        "actual": "216K",
        "forecast": "1.5%",
        "previous": "-",
    }
    row.update(overrides)
    return row


class _FakeTransport:
    """Deterministic transport returning canned rows per site."""

    def __init__(
        self,
        rows: Mapping[str, Sequence[Mapping[str, object]]],
        *,
        failing: frozenset[str] = frozenset(),
    ) -> None:
        self._rows = rows
        self._failing = failing
        self.max_concurrent = 0
        self._active = 0
        self._lock = asyncio.Lock()

    async def fetch_site(
        self, site: str, _start: datetime, _end: datetime
    ) -> Sequence[Mapping[str, object]]:
        """Return canned rows, tracking observed concurrency."""
        async with self._lock:
            self._active += 1
            self.max_concurrent = max(self.max_concurrent, self._active)
        await asyncio.sleep(0)
        try:
            if site in self._failing:
                raise TimeoutError(site)
            return self._rows.get(site, [])
        finally:
            async with self._lock:
                self._active -= 1


def _options(**overrides: object) -> ScrapeOptions:
    """Return a bounded scrape declaration."""
    values: dict[str, object] = {"start": _START, "end": _END}
    values.update(overrides)
    return ScrapeOptions(**values)  # type: ignore[arg-type]


def test_window_must_be_ordered_and_aware() -> None:
    """An invalid window never reaches a transport."""
    with pytest.raises(DataError):
        ScrapeOptions(start=_END, end=_START)
    with pytest.raises(DataError):
        ScrapeOptions(start=datetime(2026, 1, 1), end=_END)  # noqa: DTZ001


def test_unknown_site_is_rejected() -> None:
    """Only the four supported portals may be requested."""
    with pytest.raises(DataError):
        _options(sites=("unknown_site",))


def test_concurrency_limit_is_respected() -> None:
    """Site fetches never exceed the declared parallelism."""
    transport = _FakeTransport({site: [_row()] for site in CALENDAR_SITES})

    scrape_economic_calendar(_options(max_parallel_tasks=2), transport)

    assert transport.max_concurrent <= 2


def test_invalid_records_are_filtered() -> None:
    """Rows missing mandatory evidence are discarded, not defaulted."""
    transport = _FakeTransport(
        {
            "forexfactory": [
                _row(),
                _row(title=""),
                _row(country=""),
                _row(impact="unknown"),
                _row(timestamp=None),
            ]
        }
    )

    result = scrape_economic_calendar(_options(sites=("forexfactory",)), transport)

    assert len(result.events) == 1


def test_duplicate_events_are_removed() -> None:
    """Repeated site/time/title rows collapse to one event."""
    transport = _FakeTransport({"forexfactory": [_row(), _row(), _row()]})

    result = scrape_economic_calendar(_options(sites=("forexfactory",)), transport)

    assert len(result.events) == 1


def test_numeric_suffixes_are_parsed_exactly() -> None:
    """Thousands suffixes and percentages become exact decimals."""
    transport = _FakeTransport({"forexfactory": [_row()]})

    result = scrape_economic_calendar(_options(sites=("forexfactory",)), transport)
    event = result.events[0]

    assert event.actual == Decimal(216_000)
    assert event.forecast == Decimal("1.5")
    assert event.previous is None


def test_failing_site_is_recorded_without_failing_the_scrape() -> None:
    """One unreachable portal never discards the others' evidence."""
    transport = _FakeTransport(
        {"forexfactory": [_row()]},
        failing=frozenset({"cryptocraft"}),
    )

    result = scrape_economic_calendar(
        _options(sites=("forexfactory", "cryptocraft")), transport
    )

    assert len(result.events) == 1
    assert result.skipped["cryptocraft"] == "NETWORK_ERROR"


def test_total_failure_is_reported() -> None:
    """A scrape with no reachable site fails rather than returning silence."""
    transport = _FakeTransport({}, failing=frozenset(CALENDAR_SITES))

    with pytest.raises(DataError) as error:
        scrape_economic_calendar(_options(), transport)

    assert error.value.code == "NETWORK_ERROR"


def test_to_dataframe_returns_valid_structure() -> None:
    """The projection carries the fixed calendar column contract."""
    transport = _FakeTransport({"forexfactory": [_row()]})
    result = scrape_economic_calendar(_options(sites=("forexfactory",)), transport)

    frame = result.to_dataframe()

    assert list(frame.columns) == [
        "site",
        "timestamp",
        "title",
        "country",
        "impact",
        "actual",
        "forecast",
        "previous",
    ]
    assert len(frame) == 1


def test_empty_result_still_has_columns() -> None:
    """An empty scrape yields a typed empty frame, not a malformed one."""
    transport = _FakeTransport({"forexfactory": []})
    result = scrape_economic_calendar(_options(sites=("forexfactory",)), transport)

    assert result.to_dataframe().empty
    assert len(result.to_dataframe().columns) == 8


def test_save_skips_empty_dataframes(tmp_path: Path) -> None:
    """Sites with no events are skipped rather than written as empty files."""
    transport = _FakeTransport({"forexfactory": [_row()], "metalsmine": []})
    result = scrape_economic_calendar(
        _options(sites=("forexfactory", "metalsmine")), transport
    )

    result.save(tmp_path)
    written = tuple(tmp_path.glob("*.csv"))

    assert len(written) == 1
    assert written[0].name.startswith("forexfactory_")
    assert written[0].exists()


def test_save_rejects_unsupported_format(tmp_path: Path) -> None:
    """An unsupported artifact format fails before any write."""
    transport = _FakeTransport({"forexfactory": [_row()]})
    result = scrape_economic_calendar(_options(sites=("forexfactory",)), transport)

    with pytest.raises(DataError):
        result.save(tmp_path, "xlsx")


def test_pickle_roundtrip() -> None:
    """A locally produced payload rebuilds an equivalent result."""
    transport = _FakeTransport({"forexfactory": [_row()]})
    result = scrape_economic_calendar(_options(sites=("forexfactory",)), transport)

    restored = ScrapeResult.deserialize(result.serialize())

    assert restored.events == result.events
    assert restored.sites == result.sites


def test_deserialize_rejects_a_foreign_payload() -> None:
    """A payload that is not a scrape result fails closed."""
    import pickle

    with pytest.raises(DataError):
        ScrapeResult.deserialize(pickle.dumps({"not": "a result"}))
