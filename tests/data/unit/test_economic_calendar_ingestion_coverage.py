"""Focused branch coverage for economic-calendar ingestion decisions."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Self
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts import DataError
from app.services.data.economic_calendar import ingestion


def _csv_row(**updates: object) -> dict[str, object]:
    """Return one valid official weekly CSV row.

    Args:
        **updates: Column overrides applied to the valid row.

    Returns:
        Mutable official-format row mapping.
    """
    row: dict[str, object] = {
        "Title": "CPI",
        "Country": "USD",
        "Date": "08-09-2026",
        "Time": "8:30am",
        "Impact": "High",
        "Forecast": "2.1%",
        "Previous": "2.0%",
        "URL": "https://www.forexfactory.com/calendar/123-cpi/",
    }
    row.update(updates)
    return row


def test_weekly_csv_normalization_preserves_definition_and_duplicate_identity() -> None:
    """Normalize official rows without collapsing repeated releases."""
    events = ingestion._weekly_events((_csv_row(), _csv_row()))

    assert len(events) == 2
    assert events[0].id != events[1].id
    assert events[0].provider_definition_id == "123"
    assert events[0].currency == "USD"
    assert events[0].forecast_raw == "2.1%"
    assert ingestion._weekly_coverage_end((_csv_row(),)) > datetime(
        2026, 8, 9, tzinfo=UTC
    )


@pytest.mark.parametrize(
    ("row", "field"),
    [
        ({"unexpected": "shape"}, "weekly_keys"),
        (_csv_row(URL="http://invalid.example/1"), "URL"),
        (_csv_row(Title=""), "weekly_row"),
    ],
)
def test_weekly_rows_fail_closed(row: dict[str, object], field: str) -> None:
    """Reject malformed weekly shapes, URLs, and required values.

    Args:
        row: Malformed row under test.
        field: Expected safe failure field.
    """
    with pytest.raises(DataError) as error:
        ingestion._weekly_events((row,))
    assert error.value.safe_details == {"field": field}


def test_definition_fetch_retries_and_crawl_classifies_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bound retries and classify discovered versus rejected definitions."""
    attempts: list[str] = []

    def fetch(source_url: str) -> str:
        """Fail twice and then return bounded Markdown.

        Args:
            source_url: Definition URL being fetched.

        Returns:
            Bounded definition Markdown on the third attempt.

        Raises:
            DataError: During the first two attempts.
        """
        attempts.append(source_url)
        if len(attempts) < 3:
            raise DataError("SOURCE_UNAVAILABLE")
        return "definition"

    monkeypatch.setattr(ingestion, "fetch_reader_event_page", fetch)
    monkeypatch.setattr(ingestion.time, "sleep", lambda _seconds: None)
    assert ingestion._fetch_definition_with_retries("https://example.test") == (
        "definition"
    )
    assert len(attempts) == 3

    monkeypatch.setattr(
        ingestion,
        "_fetch_definition_with_retries",
        lambda url: None if url.endswith("/2") else "definition",
    )
    monkeypatch.setattr(
        ingestion,
        "parse_event_definition",
        lambda _markdown, source_url: {"source_url": source_url},
    )
    monkeypatch.setattr(ingestion, "definition_parameters", lambda value, **_: value)
    persisted: list[object] = []
    monkeypatch.setattr(
        ingestion,
        "update_economic_event_definition_record",
        lambda value, **_: persisted.append(value),
    )
    monkeypatch.setattr(
        ingestion,
        "reconcile_economic_event_definition_records",
        lambda **_: SimpleNamespace(affected_rows=4),
    )
    monkeypatch.setattr(ingestion.time, "monotonic", lambda: 1.0)

    result = ingestion._crawl_definitions_raw(1, 2, "req-test")

    assert result == {"discovered": 1, "rejected": 1, "linked": 4}
    assert len(persisted) == 1


def test_population_environment_and_id_range_fail_closed() -> None:
    """Reject production population and invalid definition ranges."""
    with pytest.raises(DataError):
        ingestion._require_non_production("production")
    response = ingestion.crawl_forexfactory_event_definitions(
        environment="dev",
        start_id=0,
        end_id=1,
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"


def test_weekly_fetch_is_bounded_and_rejects_empty_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decode a bounded CSV response and reject an empty source response."""

    class _Response:
        """Minimal context-managed URL response used by the transport test."""

        def __init__(self, payload: bytes) -> None:
            """Store the bounded response payload.

            Args:
                payload: Bytes returned from ``read``.
            """
            self._payload = payload

        def __enter__(self) -> Self:
            """Return this response from the context manager.

            Returns:
                This response instance.
            """
            return self

        def __exit__(self, *_args: object) -> None:
            """Close the synthetic response without resources.

            Args:
                *_args: Context-manager exception information.
            """

        def read(self, _limit: int) -> bytes:
            """Return the configured response bytes.

            Args:
                _limit: Caller-enforced byte ceiling.

            Returns:
                Configured bounded payload.
            """
            return self._payload

    payload = (
        b"Title,Country,Date,Time,Impact,Forecast,Previous,URL\n"
        b"CPI,USD,08-09-2026,8:30am,High,2.1%,2.0%,"
        b"https://www.forexfactory.com/calendar/123-cpi/\n"
    )
    monkeypatch.setattr(
        ingestion.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _Response(payload),
    )
    assert len(ingestion._fetch_weekly_csv()) == 1
    monkeypatch.setattr(
        ingestion.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _Response(b""),
    )
    with pytest.raises(DataError) as error:
        ingestion._fetch_weekly_csv()
    assert error.value.code == "SOURCE_UNAVAILABLE"


def test_history_backfill_processes_bounded_empty_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Advance a bounded backfill interval without inventing absent events."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)
    store = MagicMock()
    store.missing_intervals.return_value = ((start, end),)
    store.upsert.return_value = SimpleNamespace(
        status="success",
        data=0,
        error=None,
    )
    monkeypatch.setattr(ingestion, "EconomicEventStore", lambda: store)

    class _Provider:
        """Provider returning honest empty historical evidence."""

        async def get_events(
            self,
            interval_start: datetime,
            interval_end: datetime,
        ) -> list[object]:
            """Return no events for the requested interval.

            Args:
                interval_start: Inclusive interval start.
                interval_end: Exclusive interval end.

            Returns:
                Empty provider result.
            """
            assert (interval_start, interval_end) == (start, end)
            return []

    response = asyncio.run(
        ingestion.backfill_forexfactory_history(
            start,
            end,
            provider=_Provider(),  # type: ignore[arg-type]
            environment="dev",
        )
    )

    assert response.status == "success"
    assert response.data == {"imported": 0, "rejected": 0}
    store.record_coverage.assert_not_called()
