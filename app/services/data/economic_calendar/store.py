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
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.transactions import _execute_transaction_raw
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

_REFRESH_NEXT_7_DAYS: Final[int] = 7
_REFRESH_NEXT_24_HOURS: Final[int] = 24

_UPSERT_SQL = """
INSERT INTO data_economic_events (
    provider, provider_event_id, name, category, country, currency,
    scheduled_at, original_scheduled_at, actual, forecast, previous,
    revised_previous, actual_raw, forecast_raw, previous_raw, unit, source,
    source_url, impact, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (provider, provider_event_id) DO UPDATE SET
    name = excluded.name,
    category = excluded.category,
    country = excluded.country,
    currency = excluded.currency,
    scheduled_at = excluded.scheduled_at,
    original_scheduled_at = data_economic_events.original_scheduled_at,
    actual = excluded.actual,
    forecast = excluded.forecast,
    previous = excluded.previous,
    revised_previous = excluded.revised_previous,
    actual_raw = excluded.actual_raw,
    forecast_raw = excluded.forecast_raw,
    previous_raw = excluded.previous_raw,
    unit = excluded.unit,
    source = excluded.source,
    source_url = excluded.source_url,
    impact = excluded.impact,
    updated_at = excluded.updated_at
""".strip()

# Query rows in scheduled_at order. The optional currency/country/impact
# clauses are appended deterministically below.
_QUERY_SQL_BASE = (
    "SELECT provider, provider_event_id, name, category, country, currency, "
    "scheduled_at, original_scheduled_at, actual, forecast, previous, "
    "revised_previous, actual_raw, forecast_raw, previous_raw, unit, source, "
    "source_url, impact, updated_at "
    "FROM data_economic_events "
    "WHERE scheduled_at >= ? AND scheduled_at < ?"
)


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


def _dec(value: str | None) -> Decimal | None:
    """Re-parse one stored Decimal text exactly."""
    if value is None:
        return None
    return Decimal(value)


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


def _to_row(event: EconomicEvent) -> tuple[str | int | None, ...]:
    """Pack one `EconomicEvent` for the upsert parameter set."""
    return (
        event.provider,
        event.id,
        event.name,
        event.category,
        event.country,
        event.currency,
        _iso(event.scheduled_at),
        _iso(event.scheduled_at),
        str(event.actual) if event.actual is not None else None,
        str(event.forecast) if event.forecast is not None else None,
        str(event.previous) if event.previous is not None else None,
        str(event.revised_previous) if event.revised_previous is not None else None,
        event.actual_raw,
        event.forecast_raw,
        event.previous_raw,
        event.unit,
        event.source,
        event.source_url,
        int(event.impact),
        _iso(event.updated_at),
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
        provider_event_id = _required_text(row, "provider_event_id")
        return EconomicEvent(
            id=provider_event_id,
            provider=provider,
            name=_required_text(row, "name"),
            category=None if row.get("category") is None else str(row["category"]),
            country=None if row.get("country") is None else str(row["country"]),
            currency=None if row.get("currency") is None else str(row["currency"]),
            scheduled_at=_required_dt(row, "scheduled_at"),
            impact=EventImpact(int(_required_text(row, "impact"))),
            actual=_dec(_opt_str(row, "actual")),
            forecast=_dec(_opt_str(row, "forecast")),
            previous=_dec(_opt_str(row, "previous")),
            revised_previous=(
                None
                if row.get("revised_previous") is None
                else Decimal(str(row["revised_previous"]))
            ),
            actual_raw=_opt_str(row, "actual_raw"),
            forecast_raw=_opt_str(row, "forecast_raw"),
            previous_raw=_opt_str(row, "previous_raw"),
            unit=_opt_str(row, "unit"),
            source=_opt_str(row, "source"),
            source_url=_opt_str(row, "source_url"),
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
        parameter_sets = tuple(_to_row(event) for event in events)
        statements = tuple(_UPSERT_SQL for _ in events)
        logger.info("Upserting %d economic events", len(events))
        _execute_transaction_raw(
            TransactionRequest(
                plan=StatementPlan(
                    statements=statements,
                    parameter_sets=parameter_sets,
                    max_rows=max(1, len(events)),
                ),
                request_id=request_id,
            )
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

        clauses: list[str] = []
        params: list[int | float | str | bytes | None] = [_iso(start), _iso(end)]
        if currencies:
            placeholders = ", ".join("?" for _ in currencies)
            clauses.append(f"currency IN ({placeholders})")
            params.extend(currencies)
        if countries:
            placeholders = ", ".join("?" for _ in countries)
            clauses.append(f"country IN ({placeholders})")
            params.extend(countries)
        if minimum_impact is not None:
            clauses.append("impact >= ?")
            params.append(int(minimum_impact))
        if provider is not None:
            clauses.append("provider = ?")
            params.append(provider)
        sql = _QUERY_SQL_BASE
        if clauses:
            sql = f"{sql} AND {' AND '.join(clauses)}"
        sql = f"{sql} ORDER BY scheduled_at ASC"

        logger.debug("Querying stored economic events")
        result = _execute_transaction_raw(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(sql,),
                    parameter_sets=(tuple(params),),
                    max_rows=100_000,
                ),
                request_id=request_id or generate_id("req"),
            )
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


__all__ = ["EconomicEventStore", "from_row"]
