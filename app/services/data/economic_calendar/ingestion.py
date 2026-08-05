"""Database population operations for the Economic Calendar."""

from __future__ import annotations

# ruff: noqa: S310 - the weekly URL is a fixed audited HTTPS endpoint.
import csv
import hashlib
import json
import re
import time
import urllib.request
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Final
from zoneinfo import ZoneInfo

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
    run_data_operation_async,
    unwrap_data_response,
)
from app.services.data.economic_calendar.event_urls import (
    definition_parameters,
    parse_event_definition,
)
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.normalization import normalize_calendar_number
from app.services.data.economic_calendar.reader_transport import fetch_reader_event_page
from app.services.data.economic_calendar.store import EconomicEventStore
from app.services.data.persistence import (
    reconcile_economic_event_definition_records,
    update_economic_event_definition_record,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.economic_calendar.providers import EconomicCalendarProvider

_WEEKLY_URL: Final = "https://nfs.faireconomy.media/ff_calendar_thisweek.csv"
_MAX_WEEKLY_BYTES: Final = 2 * 1024 * 1024
_BATCH_SIZE: Final = 500
_HISTORICAL_MAX_ATTEMPTS: Final = 3
_MAX_DEFINITION_ID: Final = 10_000
_EVENT_URL_PATTERN: Final = re.compile(
    r"^https://www\.forexfactory\.com/calendar/(\d+)(?:-[a-z0-9-]+)?/?$"
)
_WEEKLY_TIMEZONE: Final = ZoneInfo("America/New_York")
_CSV_START: Final = datetime(2007, 1, 1, tzinfo=UTC)
_CSV_END: Final = datetime(2024, 8, 1, tzinfo=UTC)
_IMPACTS: Final = {
    "Low Impact Expected": EventImpact.LOW,
    "Medium Impact Expected": EventImpact.MEDIUM,
    "High Impact Expected": EventImpact.HIGH,
    "Non-Economic": EventImpact.LOW,
    "Low": EventImpact.LOW,
    "Medium": EventImpact.MEDIUM,
    "High": EventImpact.HIGH,
    "Holiday": EventImpact.LOW,
}
_UNIT_SUFFIX: Final = {
    "unit_percentage": "%",
    "unit_thousand": "K",
    "unit_million": "M",
    "unit_billion": "B",
    "unit_trillion": "T",
    "unit_none": "",
    "": "",
}
_NON_PRODUCTION_ENVIRONMENTS: Final = frozenset(
    {"dev", "demo", "paper", "sandbox", "testnet"}
)


def _require_non_production(environment: str) -> None:
    """Block every population operation outside an explicit safe environment."""
    if environment not in _NON_PRODUCTION_ENVIRONMENTS:
        raise DataError("PERMISSION_DENIED", safe_details={"field": "environment"})


def _exact(value: str, unit: str) -> str | None:
    """Return an exact CSV value with its declared unit suffix."""
    value = value.strip()
    if not value:
        return None
    if unit not in _UNIT_SUFFIX:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "unit"})
    return f"{value}{_UNIT_SUFFIX[unit]}"


def _csv_event(row: Mapping[str, str]) -> EconomicEvent:
    """Normalize one trusted historical CSV row without inventing values."""
    try:
        scheduled = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=UTC
        )
        impact = _IMPACTS[row["impact"]]
        previous = _exact(row["previous"], row["previous_unit"])
        revised = previous if row["previous_revised"] == "True" else None
        return EconomicEvent(
            id=f"csv:{row['id']}",
            provider="local_csv",
            name=row["event"].strip(),
            category=None,
            country=None,
            currency=row["currency"].strip().upper(),
            scheduled_at=scheduled,
            original_scheduled_at=scheduled,
            impact=impact,
            actual_raw=_exact(row["actual"], row["actual_unit"]),
            forecast_raw=_exact(row["forecast"], row["forecast_unit"]),
            previous_raw=previous,
            revised_previous=(
                None if revised is None else normalize_calendar_number(revised)
            ),
            source="local_csv",
            source_url=None,
            updated_at=scheduled,
        )
    except (KeyError, ValueError) as error:
        raise DataError(
            "VALIDATION_FAILED", safe_details={"field": "csv_row"}
        ) from error


def _import_csv_raw(
    path: Path, *, store: EconomicEventStore, request_id: str
) -> dict[str, int]:
    """Stream the approved historical interval into bounded transactions."""
    if not path.is_file():
        raise DataError("FILE_NOT_FOUND", safe_details={"field": "path"})
    digest = hashlib.sha256()
    with path.open("rb") as binary_stream:
        for chunk in iter(lambda: binary_stream.read(1024 * 1024), b""):
            digest.update(chunk)
    revision = digest.hexdigest()
    imported = 0
    rejected = 0
    batch: list[EconomicEvent] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            try:
                event = _csv_event(row)
            except DataError:
                rejected += 1
                continue
            if not _CSV_START <= event.scheduled_at < _CSV_END:
                continue
            batch.append(event)
            if len(batch) == _BATCH_SIZE:
                unwrap_data_response(
                    store.upsert(batch, request_id=request_id),
                    operation="data.economic_calendar.import_csv",
                    request_id=request_id,
                )
                imported += len(batch)
                batch.clear()
    if batch:
        unwrap_data_response(
            store.upsert(batch, request_id=request_id),
            operation="data.economic_calendar.import_csv",
            request_id=request_id,
        )
        imported += len(batch)
    if imported:
        store.record_coverage(
            _CSV_START,
            _CSV_END,
            provider="local_csv",
            source_revision=revision,
            request_id=request_id,
        )
    return {"imported": imported, "rejected": rejected}


def import_economic_calendar_csv(
    path: Path = Path("data/scrape.csv"),
    *,
    environment: str,
) -> StandardResponse[dict[str, int]]:
    """Populate the governed historical CSV interval transactionally."""
    request_id = generate_id("req")

    def _raw() -> dict[str, int]:
        _require_non_production(environment)
        return _import_csv_raw(
            path,
            store=EconomicEventStore(),
            request_id=request_id,
        )

    return run_data_operation(
        operation="data.economic_calendar.import_csv",
        request_id=request_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def _week_start(value: datetime) -> datetime:
    """Return Sunday 00:00 UTC for the week containing one UTC instant."""
    day_start = value.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return day_start - timedelta(days=(day_start.weekday() + 1) % 7)


def _weekly_coverage_end(rows: Sequence[Mapping[str, object]]) -> datetime:
    """Return the latest source-local week end represented by weekly rows."""
    ends: list[datetime] = []
    for row in rows:
        if "Date" in row:
            value = datetime.strptime(
                f"{row['Date']} {row['Time']}", "%m-%d-%Y %I:%M%p"
            ).replace(tzinfo=_WEEKLY_TIMEZONE)
        else:
            value = datetime.fromisoformat(str(row["date"]))
        local_start = value.replace(hour=0, minute=0, second=0, microsecond=0)
        local_start -= timedelta(days=(local_start.weekday() + 1) % 7)
        ends.append((local_start + timedelta(days=7)).astimezone(UTC))
    return max(ends)


def _weekly_events(rows: Sequence[Mapping[str, object]]) -> list[EconomicEvent]:
    """Validate and normalize official weekly CSV or injected JSON rows."""
    csv_keys = {
        "Title",
        "Country",
        "Date",
        "Time",
        "Impact",
        "Forecast",
        "Previous",
        "URL",
    }
    json_keys = {"title", "country", "date", "impact", "forecast", "previous"}
    counters: Counter[tuple[str, str]] = Counter()
    events: list[EconomicEvent] = []
    for row in rows:
        keys = set(row)
        if keys not in (csv_keys, json_keys):
            raise DataError("VALIDATION_FAILED", safe_details={"field": "weekly_keys"})
        is_csv = keys == csv_keys
        title = str(row["Title" if is_csv else "title"]).strip()
        country = str(row["Country" if is_csv else "country"]).strip().upper()
        if is_csv:
            scheduled = (
                datetime.strptime(f"{row['Date']} {row['Time']}", "%m-%d-%Y %I:%M%p")
                .replace(tzinfo=_WEEKLY_TIMEZONE)
                .astimezone(UTC)
            )
        else:
            scheduled = datetime.fromisoformat(str(row["date"])).astimezone(UTC)
        impact_text = str(row["Impact" if is_csv else "impact"])
        source_url = str(row["URL"]).strip() if is_csv else _WEEKLY_URL
        definition_match = _EVENT_URL_PATTERN.fullmatch(source_url)
        if is_csv and definition_match is None:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "URL"})
        if not title or not country or impact_text not in _IMPACTS:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "weekly_row"})
        series = (title, country)
        ordinal = counters[series]
        counters[series] += 1
        identity = hashlib.sha256(
            (
                f"{_week_start(scheduled).date()}\x1f{title}\x1f{country}\x1f{ordinal}"
            ).encode()
        ).hexdigest()
        events.append(
            EconomicEvent(
                id=f"weekly:{identity}",
                provider="forexfactory",
                name=title,
                category=None,
                country=None,
                currency=None if country == "ALL" else country,
                scheduled_at=scheduled,
                original_scheduled_at=scheduled,
                impact=_IMPACTS[impact_text],
                forecast_raw=str(row["Forecast" if is_csv else "forecast"]).strip()
                or None,
                previous_raw=str(row["Previous" if is_csv else "previous"]).strip()
                or None,
                source="forexfactory",
                source_url=source_url,
                provider_definition_id=(
                    definition_match.group(1) if definition_match is not None else None
                ),
                updated_at=datetime.now(UTC),
            )
        )
    return events


def _fetch_weekly_csv() -> Sequence[Mapping[str, object]]:
    """Fetch the bounded official weekly CSV resource with permanent URLs."""
    request = urllib.request.Request(
        _WEEKLY_URL,
        headers={"Accept": "text/csv", "User-Agent": "HaruQuantAI/1"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = response.read(_MAX_WEEKLY_BYTES + 1)
    if len(payload) > _MAX_WEEKLY_BYTES:
        raise DataError("LIMIT_EXCEEDED")
    text = payload.decode("utf-8-sig")
    rows: list[Mapping[str, object]] = list(csv.DictReader(text.splitlines()))
    if not rows:
        raise DataError("SOURCE_UNAVAILABLE")
    return rows


def sync_current_week_economic_calendar(
    *,
    environment: str,
    rows: Sequence[Mapping[str, object]] | None = None,
) -> StandardResponse[dict[str, int]]:
    """Upsert the current week from explicit rows or the official CSV source."""
    request_id = generate_id("req")

    def _raw() -> dict[str, int]:
        _require_non_production(environment)
        source_rows = rows if rows is not None else _fetch_weekly_csv()
        events = _weekly_events(source_rows)
        if not events:
            raise DataError("SOURCE_UNAVAILABLE")
        store = EconomicEventStore()
        for event in events:
            if event.provider_definition_id is None or event.source_url is None:
                continue
            definition = {
                "provider_definition_id": event.provider_definition_id,
                "country": event.currency or event.country or "ALL",
                "title": event.name,
                "source_url": event.source_url,
                "source_original": None,
                "source_latest": None,
                "measures": None,
                "effect": None,
                "frequency": None,
                "also_called": None,
                "event_type": None,
            }
            update_economic_event_definition_record(
                definition_parameters(definition, request_id=request_id),
                request_id=request_id,
            )
        unwrap_data_response(
            store.upsert(events, request_id=request_id),
            operation="data.economic_calendar.sync_current_week",
            request_id=request_id,
        )
        start = _week_start(datetime.now(UTC))
        coverage_end = max(
            start + timedelta(days=7),
            _weekly_coverage_end(source_rows),
        )
        revision = hashlib.sha256(
            json.dumps(source_rows, sort_keys=True, default=str).encode()
        ).hexdigest()
        store.record_coverage(
            start,
            coverage_end,
            provider="forexfactory",
            source_revision=revision,
            request_id=request_id,
        )
        return {"imported": len(events), "rejected": 0}

    return run_data_operation(
        operation="data.economic_calendar.sync_current_week",
        request_id=request_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def _fetch_definition_with_retries(source_url: str) -> str | None:
    """Fetch one definition with bounded retries."""
    for attempt in range(_HISTORICAL_MAX_ATTEMPTS):
        try:
            return fetch_reader_event_page(source_url)
        except DataError:
            if attempt + 1 < _HISTORICAL_MAX_ATTEMPTS:
                time.sleep(3.0)
    return None


def _crawl_definitions_raw(
    start_id: int, end_id: int, request_id: str
) -> dict[str, int]:
    """Persist one bounded definition-ID interval and reconcile occurrences."""
    discovered = 0
    rejected = 0
    for definition_id in range(start_id, end_id + 1):
        request_started = time.monotonic()
        source_url = f"https://www.forexfactory.com/calendar/{definition_id}"
        markdown = _fetch_definition_with_retries(source_url)
        if markdown is None:
            rejected += 1
        else:
            try:
                definition = parse_event_definition(markdown, source_url)
            except DataError:
                rejected += 1
            else:
                update_economic_event_definition_record(
                    definition_parameters(definition, request_id=request_id),
                    request_id=request_id,
                )
                discovered += 1
        if definition_id < end_id:
            time.sleep(max(0.0, 3.0 - (time.monotonic() - request_started)))
        if definition_id % 25 == 0 or definition_id == end_id:
            logger.info(
                "Economic Calendar definition scan progress: %d/%d",
                definition_id,
                end_id,
            )
    result = reconcile_economic_event_definition_records(request_id=request_id)
    return {
        "discovered": discovered,
        "rejected": rejected,
        "linked": result.affected_rows,
    }


def crawl_forexfactory_event_definitions(
    *, environment: str, start_id: int = 1, end_id: int = 1024
) -> StandardResponse[dict[str, int]]:
    """Discover, persist, and reconcile bounded Forex Factory definitions."""
    request_id = generate_id("req")

    def _raw() -> dict[str, int]:
        _require_non_production(environment)
        if start_id < 1 or end_id < start_id or end_id > _MAX_DEFINITION_ID:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "id_range"})
        return _crawl_definitions_raw(start_id, end_id, request_id)

    return run_data_operation(
        operation="data.economic_calendar.crawl_event_definitions",
        request_id=request_id,
        start_time=data_start_time(),
        raw=_raw,
    )


async def backfill_forexfactory_history(
    start: datetime,
    end: datetime,
    *,
    provider: EconomicCalendarProvider,
    environment: str,
) -> StandardResponse[dict[str, int]]:
    """Acquire historical Forex Factory data in bounded eight-week intervals."""
    request_id = generate_id("req")

    async def _raw() -> dict[str, int]:
        _require_non_production(environment)
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
        store = EconomicEventStore()
        imported = 0
        missing = store.missing_intervals(
            start,
            end,
            request_id=request_id,
        )
        for missing_start, missing_end in missing:
            cursor = missing_start
            while cursor < missing_end:
                interval_end = min(missing_end, cursor + timedelta(weeks=8))
                for attempt in range(1, _HISTORICAL_MAX_ATTEMPTS + 1):
                    try:
                        result = await provider.get_events(cursor, interval_end)
                        break
                    except DataError:
                        if attempt == _HISTORICAL_MAX_ATTEMPTS:
                            raise
                        logger.warning(
                            "Retrying bounded Forex Factory interval after "
                            "provider failure "
                            "(attempt %s of %s)",
                            attempt + 1,
                            _HISTORICAL_MAX_ATTEMPTS,
                        )
                events = (
                    result
                    if isinstance(result, list)
                    else unwrap_data_response(
                        result,
                        operation="data.economic_calendar.backfill_history",
                        request_id=request_id,
                    )
                )
                unwrap_data_response(
                    store.upsert(events, request_id=request_id),
                    operation="data.economic_calendar.backfill_history",
                    request_id=request_id,
                )
                revision = hashlib.sha256(
                    json.dumps(sorted(event.id for event in events)).encode()
                ).hexdigest()
                if events:
                    store.record_coverage(
                        cursor,
                        interval_end,
                        provider="forexfactory",
                        source_revision=revision,
                        request_id=request_id,
                    )
                imported += len(events)
                cursor = interval_end
        return {"imported": imported, "rejected": 0}

    return await run_data_operation_async(
        operation="data.economic_calendar.backfill_history",
        request_id=request_id,
        start_time=data_start_time(),
        raw=_raw,
    )


__all__ = [
    "backfill_forexfactory_history",
    "crawl_forexfactory_event_definitions",
    "import_economic_calendar_csv",
    "sync_current_week_economic_calendar",
]
