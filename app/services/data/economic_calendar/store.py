"""Persistent economic-event storage for FEAT-DATA-11.

The store owns the calendar-table upsert and read paths declared by section 7
of the design: events are written and refreshed idempotently under the
composite key ``provider + provider_event_id`` and queried by UTC window plus
optional currency/country/impact filters.

Database access is supplied by the shared DATA persistence layer
(``execute_transaction``); the store never opens a connection or bypasses the
approved storage roots.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.normalization import (
    normalize_calendar_number,
)
from app.services.data.persistence import (
    read_economic_calendar_coverage_records,
    read_economic_event_records,
    update_economic_calendar_coverage_record,
    update_economic_event_records,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

_REFRESH_NEXT_7_DAYS: Final[int] = 7
_REFRESH_NEXT_24_HOURS: Final[int] = 24
_CURRENCY_CODE_LENGTH: Final[int] = 3


def _iso(value: datetime | None) -> str | None:
    """Render one aware UTC datetime as ISO text or NULL."""
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    """Re-parse one stored ISO timestamp, returning timezone-aware UTC."""
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _opt_str(row: dict[str, object], key: str) -> str | None:
    """Return one optional row value as a string or None.

    Args:
        row: Column-name -> scalar mapping.
        key: Column name.

    Returns:
        The string value or None.
    """
    value = row.get(key)
    return None if value is None else str(value)


def _exact_value(raw: str | None, numeric: Decimal | None) -> str | None:
    """Prefer exact provider text and fall back to normalized decimal text."""
    return str(numeric) if numeric is not None else raw


def _event_id(event: EconomicEvent) -> str:
    """Return one provider-qualified stable event identity."""
    prefix = f"{event.provider}:"
    return event.id if event.id.startswith(prefix) else f"{prefix}{event.id}"


def _to_row(event: EconomicEvent, *, request_id: str) -> tuple[str | int | None, ...]:
    """Pack one `EconomicEvent` for the upsert parameter set."""
    return (
        _event_id(event),
        event.name,
        event.currency or event.country or "ALL",
        _iso(event.scheduled_at),
        _iso(event.original_scheduled_at or event.scheduled_at),
        int(event.impact),
        _exact_value(event.actual_raw, event.actual),
        _exact_value(event.forecast_raw, event.forecast),
        _exact_value(event.previous_raw, event.previous),
        None if event.revised_previous is None else str(event.revised_previous),
        event.provider,
        event.source_url,
        _iso(event.original_scheduled_at or event.updated_at or event.scheduled_at),
        _iso(event.updated_at or datetime.now(UTC)),
        request_id,
        event.provider_definition_id,
    )


def _required_text(row: dict[str, object], key: str) -> str:
    """Return one required row scalar as text."""
    value = row[key]
    if value is None:
        detail = f"{key} is required"
        raise ValueError(detail)
    return str(value)


def _required_dt(row: dict[str, object], key: str) -> datetime:
    """Return one required stored UTC timestamp."""
    value = _parse_dt(_required_text(row, key))
    if value is None:
        raise ValueError("stored timestamp is required")
    return value


def _from_row_raw(row: dict[str, object]) -> EconomicEvent:
    """Reconstruct one `EconomicEvent` from a stored row mapping.

    Args:
        row: Column-name -> scalar mapping as returned by ``execute_transaction``.

    Returns:
        The normalized economic event.

    Raises:
        DataError: If a stored row is malformed.
    """
    try:
        provider = _required_text(row, "provider")
        stored_id = _required_text(row, "event_id")
        provider_event_id = stored_id.removeprefix(f"{provider}:")
        scope = _required_text(row, "country")
        currency = (
            scope if len(scope) == _CURRENCY_CODE_LENGTH and scope != "ALL" else None
        )
        return EconomicEvent(
            id=provider_event_id,
            provider=provider,
            name=_required_text(row, "title"),
            category=None,
            country=None if currency is not None or scope == "ALL" else scope,
            currency=currency,
            scheduled_at=_required_dt(row, "scheduled_at"),
            original_scheduled_at=_required_dt(row, "original_scheduled_at"),
            impact=EventImpact(int(_required_text(row, "impact"))),
            actual=normalize_calendar_number(_opt_str(row, "actual")),
            forecast=normalize_calendar_number(_opt_str(row, "forecast")),
            previous=normalize_calendar_number(_opt_str(row, "previous")),
            revised_previous=(
                None
                if row.get("revised_previous") is None
                else Decimal(str(row["revised_previous"]))
            ),
            actual_raw=_opt_str(row, "actual"),
            forecast_raw=_opt_str(row, "forecast"),
            previous_raw=_opt_str(row, "previous"),
            unit=None,
            source=provider,
            source_url=_opt_str(row, "source_url"),
            provider_definition_id=_opt_str(row, "provider_definition_id"),
            source_original=_opt_str(row, "source_original"),
            source_latest=_opt_str(row, "source_latest"),
            measures=_opt_str(row, "measures"),
            effect=_opt_str(row, "effect"),
            frequency=_opt_str(row, "frequency"),
            also_called=_opt_str(row, "also_called"),
            event_type=_opt_str(row, "event_type"),
            updated_at=_parse_dt(_opt_str(row, "updated_at")),
        )
    except (KeyError, ValueError, TypeError, ArithmeticError) as error:
        logger.exception("Failed to reconstruct an economic event row")
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={"operation": "economic_event_from_row"},
        ) from error


def from_row(row: dict[str, object]) -> StandardResponse[EconomicEvent]:
    """Reconstruct one `EconomicEvent` from a stored row mapping.

    Args:
        row: Column-name -> scalar mapping as returned by ``execute_transaction``.

    Returns:
        Standard response carrying the normalized economic event.

    Raises:
        (in-band) ``FILE_CORRUPTED`` when a stored row is malformed.
    """
    return run_data_operation(
        operation="data.economic_calendar.from_row",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _from_row_raw(row),
    )


class EconomicEventStore:
    """Idempotent upsert and read access to ``data_economic_events``."""

    def _upsert_raw(self, events: Sequence[EconomicEvent], *, request_id: str) -> int:
        """Insert or refresh events under their composite provider key.

        Raises:
            DataError: If the bounded write transaction fails.
        """
        if not events:
            return 0
        parameter_sets = tuple(
            _to_row(event, request_id=request_id) for event in events
        )
        logger.info("Upserting %d economic events", len(events))
        update_economic_event_records(
            parameter_sets,
            request_id=request_id,
        )
        return len(events)

    def upsert(
        self, events: Sequence[EconomicEvent], *, request_id: str
    ) -> StandardResponse[int]:
        """Insert or refresh events under their composite provider key.

        Args:
            events: Normalized economic events to store.
            request_id: Caller-supplied trace correlation id.

        Returns:
            Standard response carrying the number of events written (each is
            one upsert row).

        Raises:
            (in-band) ``DataError`` codes when the bounded write transaction
                fails.
        """
        return run_data_operation(
            operation="data.economic_calendar.economic_event_store.upsert",
            request_id=request_id,
            start_time=data_start_time(),
            raw=lambda: self._upsert_raw(events, request_id=request_id),
        )

    def _query_raw(
        self,
        start: datetime,
        end: datetime,
        *,
        currencies: Sequence[str] | None = None,
        countries: Sequence[str] | None = None,
        minimum_impact: EventImpact | None = None,
        provider: str | None = None,
        request_id: str | None = None,
    ) -> list[EconomicEvent]:
        """Return stored events for a UTC window under optional filters.

        Raises:
            DataError: If the window is invalid or the read transaction fails.
        """
        if start.tzinfo is None or end.tzinfo is None:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
        if start >= end:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})

        logger.debug("Querying stored economic events")
        result = read_economic_event_records(
            start=str(_iso(start)),
            end=str(_iso(end)),
            currencies=currencies,
            countries=countries,
            minimum_impact=(
                int(minimum_impact) if minimum_impact is not None else None
            ),
            provider=provider,
            request_id=request_id or generate_id("req"),
        )
        return [_from_row_raw(dict(row)) for row in result.rows]

    def query(
        self,
        start: datetime,
        end: datetime,
        *,
        currencies: Sequence[str] | None = None,
        countries: Sequence[str] | None = None,
        minimum_impact: EventImpact | None = None,
        provider: str | None = None,
        request_id: str | None = None,
    ) -> StandardResponse[list[EconomicEvent]]:
        """Return stored events for a UTC window under optional filters.

        Args:
            start: Inclusive aware-UTC window start.
            end: Exclusive aware-UTC window end.
            currencies: Optional currency filter.
            countries: Optional country filter.
            minimum_impact: Optional impact filter.
            provider: Optional provider filter.
            request_id: Optional trace correlation id.

        Returns:
            Standard response carrying the chronologically ordered normalized
            events matching the filters.

        Raises:
            (in-band) ``VALIDATION_FAILED`` when the window is invalid, plus
                ``DataError`` codes when the bounded read transaction fails.
        """
        return run_data_operation(
            operation="data.economic_calendar.economic_event_store.query",
            request_id=request_id,
            start_time=data_start_time(),
            raw=lambda: self._query_raw(
                start,
                end,
                currencies=currencies,
                countries=countries,
                minimum_impact=minimum_impact,
                provider=provider,
                request_id=request_id,
            ),
        )

    def missing_intervals(
        self, start: datetime, end: datetime, *, request_id: str
    ) -> tuple[tuple[datetime, datetime], ...]:
        """Return uncovered portions of one requested UTC window."""
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
        result = read_economic_calendar_coverage_records(
            start=str(_iso(start)), end=str(_iso(end)), request_id=request_id
        )
        intervals = sorted(
            (
                max(start, _required_dt(dict(row), "range_start")),
                min(end, _required_dt(dict(row), "range_end")),
            )
            for row in result.rows
            if row["status"] == "complete"
        )
        missing: list[tuple[datetime, datetime]] = []
        cursor = start
        for covered_start, covered_end in intervals:
            if covered_end <= cursor:
                continue
            if covered_start > cursor:
                missing.append((cursor, covered_start))
            cursor = max(cursor, covered_end)
            if cursor >= end:
                break
        if cursor < end:
            missing.append((cursor, end))
        return tuple(missing)

    def record_coverage(
        self,
        start: datetime,
        end: datetime,
        *,
        provider: str,
        source_revision: str,
        request_id: str,
        complete: bool = True,
        synchronized_at: datetime | None = None,
    ) -> None:
        """Record one coverage interval after its event transaction succeeds."""
        observed = synchronized_at or datetime.now(UTC)
        update_economic_calendar_coverage_record(
            (
                provider,
                str(_iso(start)),
                str(_iso(end)),
                "complete" if complete else "partial",
                source_revision,
                str(_iso(observed)),
                request_id,
            ),
            request_id=request_id,
        )

    def _refresh_windows_raw(
        self, *, now: datetime | None = None
    ) -> tuple[tuple[datetime, datetime], tuple[datetime, datetime]]:
        """Return the next-7-day and next-24-hour refresh windows as UTC bounds.

        Raises:
                    DataError: If `
        ow`` is naive or not UTC.
        """
        observed = now if now is not None else datetime.now(UTC)
        if observed.tzinfo is None or observed.utcoffset() != timedelta(0):
            raise DataError("VALIDATION_FAILED", safe_details={"field": "now"})
        return (
            (observed, observed + timedelta(days=_REFRESH_NEXT_7_DAYS)),
            (observed, observed + timedelta(hours=_REFRESH_NEXT_24_HOURS)),
        )

    def refresh_windows(
        self, *, now: datetime | None = None
    ) -> StandardResponse[tuple[tuple[datetime, datetime], tuple[datetime, datetime]]]:
        """Return the next-7-day and next-24-hour refresh windows as UTC bounds.

                These are advisory refresh windows for the caller (section 7 of the
                design): the next 7 days is refreshed periodically for schedule
                changes while the next 24 hours is refreshed more frequently. The
                store does not schedule its own refresh; callers integrate it with
                their own scheduler (the DATA jobs feature is out of scope here).

        Args:
                    now: Optional observation instant; defaults to UTC now.

        Returns:
                    Standard response carrying ``(seven_day_window,
                    twenty_four_hour_window)`` as ``(start, end)`` UTC datetime pairs.

        Raises:
                    (in-band) ``VALIDATION_FAILED`` when `
        ow`` is naive or not UTC.
        """
        return run_data_operation(
            operation="data.economic_calendar.economic_event_store.refresh_windows",
            request_id=generate_id("req"),
            start_time=data_start_time(),
            raw=lambda: self._refresh_windows_raw(now=now),
        )


def persist_economic_events(
    events: Sequence[EconomicEvent],
    *,
    store: EconomicEventStore,
    request_id: str,
) -> StandardResponse[int]:
    """Persist normalized economic events through the function-only boundary.

    Args:
        events: Normalized events acquired through the provider-neutral API.
        store: Opaque Data-owned event-store handle.
        request_id: Caller-supplied trace correlation ID.

    Returns:
        Standard response carrying the number of rows upserted.

    Raises:
        (in-band) ``DataError`` codes when the transactional write fails.
    """
    return store.upsert(events, request_id=request_id)


__all__ = ["EconomicEventStore", "from_row", "persist_economic_events"]
