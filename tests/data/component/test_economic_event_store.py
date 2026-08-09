"""Component tests for the `data_economic_events` SQLite store (FR-DATA-128).

DB configuration follows the same monkeypatch pattern as the DATA
persistence migration tests (see ``test_persistence_migrations.py``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.store import EconomicEventStore
from app.services.data.persistence.contracts import StatementPlan, TransactionRequest
from app.services.data.persistence.migrations import run_data_migrations
from app.services.data.persistence.transactions import execute_transaction
from app.utils import generate_id


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.persistence.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def _configure_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Configure one isolated database for the economic-event store."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///economic_events.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    return tmp_path / "economic_events.sqlite3"


def _apply_migrations(request_id: str) -> None:
    """Apply the canonical DATA migration manifest including 002_economic_events."""
    _unwrap(run_data_migrations(request_id))


def _event(
    *,
    delta: timedelta,
    impact: EventImpact = EventImpact.HIGH,
    currency: str = "USD",
    country: str = "US",
    name: str = "CPI",
    forecast: Decimal | None = Decimal("0.3"),
) -> EconomicEvent:
    """Build one deterministic event at the supplied offset."""
    return EconomicEvent(
        id=f"ff:{name}:{impact.name}:{currency}",
        provider="scrape:forexfactory",
        name=name,
        category=None,
        country=country,
        currency=currency,
        scheduled_at=datetime(2026, 7, 26, 12, tzinfo=UTC) + delta,
        impact=impact,
        forecast=forecast,
        actual=None,
        previous=None,
        revised_previous=None,
        actual_raw=None,
        forecast_raw="0.3%",
        previous_raw=None,
        unit="%",
        source="forexfactory",
        source_url=None,
        updated_at=None,
    )


def test_store_requires_migrated_table(monkeypatch, tmp_path: Path) -> None:
    """Querying before the migration exists fails closed."""
    _configure_db(monkeypatch, tmp_path)
    store = EconomicEventStore()
    with pytest.raises(DataError):
        _unwrap(
            store.query(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 2, 1, tzinfo=UTC),
            )
        )


def test_upsert_inserts_and_returns_count(monkeypatch, tmp_path: Path) -> None:
    """Upsert writes one row per event."""
    _configure_db(monkeypatch, tmp_path)
    _apply_migrations(generate_id("req"))
    store = EconomicEventStore()
    events = [_event(delta=timedelta(minutes=5))]

    count = _unwrap(store.upsert(events, request_id=generate_id("req")))

    assert count == 1
    stored = _unwrap(
        store.query(
            datetime(2026, 7, 26, tzinfo=UTC),
            datetime(2026, 7, 27, tzinfo=UTC),
        )
    )
    assert len(stored) == 1
    assert stored[0].id == events[0].id
    assert stored[0].currency == "USD"
    assert stored[0].forecast == Decimal("0.3")
    assert stored[0].impact is EventImpact.HIGH


def test_upsert_exposes_first_seen_at_for_replay_visibility(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`first_seen_at` survives the upsert/query round-trip (`feature`)."""
    _configure_db(monkeypatch, tmp_path)
    _apply_migrations(generate_id("req"))
    store = EconomicEventStore()
    event = _event(delta=timedelta(minutes=5))

    _unwrap(store.upsert([event], request_id=generate_id("req")))

    stored = _unwrap(
        store.query(
            datetime(2026, 7, 26, tzinfo=UTC),
            datetime(2026, 7, 27, tzinfo=UTC),
        )
    )
    assert len(stored) == 1
    assert stored[0].first_seen_at is not None
    assert stored[0].first_seen_at.tzinfo is not None


def test_upsert_is_idempotent_on_composite_key(monkeypatch, tmp_path: Path) -> None:
    """Re-upserting the same provider/id pair overwrites in place."""
    _configure_db(monkeypatch, tmp_path)
    _apply_migrations(generate_id("req"))
    store = EconomicEventStore()
    original = _event(delta=timedelta(minutes=5), forecast=Decimal("0.3"))

    _unwrap(store.upsert([original], request_id=generate_id("req")))
    revised = _event(
        delta=timedelta(minutes=5),
        forecast=Decimal("0.4"),
    )
    _unwrap(store.upsert([revised], request_id=generate_id("req")))

    stored = _unwrap(
        store.query(
            datetime(2026, 7, 26, tzinfo=UTC),
            datetime(2026, 7, 27, tzinfo=UTC),
        )
    )
    assert len(stored) == 1
    assert stored[0].forecast == Decimal("0.4")


def test_upsert_preserves_original_schedule_when_release_moves(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A stable provider key updates the schedule but retains its first value."""
    _configure_db(monkeypatch, tmp_path)
    _apply_migrations(generate_id("req"))
    store = EconomicEventStore()
    original = _event(delta=timedelta(minutes=5))
    revised = _event(delta=timedelta(minutes=35))

    _unwrap(store.upsert([original], request_id=generate_id("req")))
    _unwrap(store.upsert([revised], request_id=generate_id("req")))

    result = _unwrap(
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "SELECT scheduled_at, original_scheduled_at "
                        "FROM data_economic_events WHERE event_id = ?",
                    ),
                    parameter_sets=((f"{original.provider}:{original.id}",),),
                    max_rows=1,
                ),
                request_id=generate_id("req"),
            )
        )
    )
    row = result.rows[0]
    assert row["scheduled_at"] == revised.scheduled_at.isoformat()
    assert row["original_scheduled_at"] == original.scheduled_at.isoformat()


def test_query_filters_by_currency(monkeypatch, tmp_path: Path) -> None:
    """Currency filter excludes non-matching rows."""
    _configure_db(monkeypatch, tmp_path)
    _apply_migrations(generate_id("req"))
    store = EconomicEventStore()
    usd = _event(delta=timedelta(minutes=5))
    eur = _event(
        delta=timedelta(minutes=5),
        currency="EUR",
        country="DE",
        name="ECB",
    )
    _unwrap(store.upsert([usd, eur], request_id=generate_id("req")))

    usd_only = _unwrap(
        store.query(
            datetime(2026, 7, 26, tzinfo=UTC),
            datetime(2026, 7, 27, tzinfo=UTC),
            currencies=("USD",),
        )
    )
    assert len(usd_only) == 1
    assert usd_only[0].currency == "USD"


def test_query_filters_by_minimum_impact(monkeypatch, tmp_path: Path) -> None:
    """Minimum impact filter excludes lower-ranked events."""
    _configure_db(monkeypatch, tmp_path)
    _apply_migrations(generate_id("req"))
    store = EconomicEventStore()
    high = _event(delta=timedelta(minutes=5), impact=EventImpact.HIGH, name="High")
    low = _event(
        delta=timedelta(minutes=5),
        impact=EventImpact.LOW,
        name="Low",
        forecast=None,
    )
    _unwrap(store.upsert([high, low], request_id=generate_id("req")))

    only_high = _unwrap(
        store.query(
            datetime(2026, 7, 26, tzinfo=UTC),
            datetime(2026, 7, 27, tzinfo=UTC),
            minimum_impact=EventImpact.HIGH,
        )
    )
    assert len(only_high) == 1
    assert only_high[0].impact is EventImpact.HIGH


def test_refresh_windows_return_seven_days_and_one_day_bounds() -> None:
    """Refresh windows return the documented 7-day and 24-hour boundaries."""
    store = EconomicEventStore()
    now = datetime(2026, 7, 26, 12, tzinfo=UTC)
    seven, twenty_four = _unwrap(store.refresh_windows(now=now))
    assert seven[0] == now
    assert seven[1] - seven[0] == timedelta(days=7)
    assert twenty_four[0] == now
    assert twenty_four[1] - twenty_four[0] == timedelta(hours=24)


def test_refresh_windows_reject_naive_now() -> None:
    """Refresh policy never silently interprets a naive observation time."""
    with pytest.raises(DataError):
        _unwrap(
            EconomicEventStore().refresh_windows(
                now=datetime(2026, 7, 26, 12, tzinfo=UTC).replace(tzinfo=None)
            )
        )


def test_query_rejects_naive_window(monkeypatch, tmp_path: Path) -> None:
    """Naive datetimes are rejected by the store."""
    _configure_db(monkeypatch, tmp_path)
    store = EconomicEventStore()
    with pytest.raises(DataError):
        _unwrap(
            store.query(
                datetime(2026, 7, 26, tzinfo=UTC).replace(tzinfo=None),
                datetime(2026, 7, 27, tzinfo=UTC).replace(tzinfo=None),
            )
        )
