"""Sessions and Calendars service implementation and functional behaviors."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, time, timedelta, timezone, tzinfo
from typing import TYPE_CHECKING, override
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.contracts.catalogue.errors import CatalogueFailure
from app.contracts.catalogue.events import (
    MarketCalendarChanged,
    TradingSessionChanged,
)
from app.contracts.catalogue.models import (
    CalendarEarlyClose,
    DefineSessionsRequest,
    DefineSessionsSuccess,
    EffectiveInterval,
    MarketCalendarVersion,
    TradingInterval,
    TradingSessionDefinition,
)
from app.contracts.catalogue.ports import DefineSessionsCapability
from app.contracts.common.models import ProblemDetails
from app.services.catalogue.session_calendar.config import SessionCalendarConfig

if TYPE_CHECKING:
    from app.kernel.events import EventBus


class _USEasternTz(tzinfo):
    """Fallback US Eastern timezone provider with Daylight Saving Time."""

    @override
    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=-4) if self._is_dst(dt) else timedelta(hours=-5)

    @override
    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=1) if self._is_dst(dt) else timedelta(0)

    @override
    def tzname(self, dt: datetime | None) -> str:
        return "EDT" if self._is_dst(dt) else "EST"

    def _is_dst(self, dt: datetime | None) -> bool:
        if dt is None:
            return False
        march_1 = date(dt.year, 3, 1)
        march_days = (6 - march_1.weekday()) % 7
        dst_start_date = date(dt.year, 3, 1 + march_days + 7)

        nov_1 = date(dt.year, 11, 1)
        nov_days = (6 - nov_1.weekday()) % 7
        dst_end_date = date(dt.year, 11, 1 + nov_days)

        d = dt.date()
        if dst_start_date < d < dst_end_date:
            return True
        if d == dst_start_date:
            return (dt.hour, dt.minute) >= (2, 0)
        if d == dst_end_date:
            return (dt.hour, dt.minute) < (2, 0)
        return False


class _LondonTz(tzinfo):
    """Fallback London timezone provider with British Summer Time."""

    @override
    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=1) if self._is_dst(dt) else timedelta(0)

    @override
    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=1) if self._is_dst(dt) else timedelta(0)

    @override
    def tzname(self, dt: datetime | None) -> str:
        return "BST" if self._is_dst(dt) else "GMT"

    def _is_dst(self, dt: datetime | None) -> bool:
        if dt is None:
            return False
        # Last Sunday in March to last Sunday in October
        march_31 = date(dt.year, 3, 31)
        dst_start = date(dt.year, 3, 31 - (march_31.weekday() + 1) % 7)
        oct_31 = date(dt.year, 10, 31)
        dst_end = date(dt.year, 10, 31 - (oct_31.weekday() + 1) % 7)

        d = dt.date()
        if dst_start < d < dst_end:
            return True
        if d == dst_start:
            return (dt.hour, dt.minute) >= (1, 0)
        if d == dst_end:
            return (dt.hour, dt.minute) < (2, 0)
        return False


class _CentralEuropeTz(tzinfo):
    """Fallback Central European timezone provider (CET/CEST)."""

    @override
    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=2) if self._is_dst(dt) else timedelta(hours=1)

    @override
    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=1) if self._is_dst(dt) else timedelta(0)

    @override
    def tzname(self, dt: datetime | None) -> str:
        return "CEST" if self._is_dst(dt) else "CET"

    def _is_dst(self, dt: datetime | None) -> bool:
        if dt is None:
            return False
        # Last Sunday in March to last Sunday in October
        march_31 = date(dt.year, 3, 31)
        dst_start = date(dt.year, 3, 31 - (march_31.weekday() + 1) % 7)
        oct_31 = date(dt.year, 10, 31)
        dst_end = date(dt.year, 10, 31 - (oct_31.weekday() + 1) % 7)

        d = dt.date()
        if dst_start < d < dst_end:
            return True
        if d == dst_start:
            return (dt.hour, dt.minute) >= (2, 0)
        if d == dst_end:
            return (dt.hour, dt.minute) < (3, 0)
        return False


_FALLBACK_TIMEZONES: dict[str, tzinfo] = {
    "America/New_York": _USEasternTz(),
    "US/Eastern": _USEasternTz(),
    "EST5EDT": _USEasternTz(),
    "America/Toronto": _USEasternTz(),
    "Europe/London": _LondonTz(),
    "GB": _LondonTz(),
    "Europe/Belfast": _LondonTz(),
    "Europe/Berlin": _CentralEuropeTz(),
    "Europe/Paris": _CentralEuropeTz(),
    "Europe/Frankfurt": _CentralEuropeTz(),
    "CET": _CentralEuropeTz(),
    "Europe/Zurich": _CentralEuropeTz(),
    "Europe/Amsterdam": _CentralEuropeTz(),
    "Asia/Tokyo": timezone(timedelta(hours=9), "JST"),
    "Japan": timezone(timedelta(hours=9), "JST"),
    "Asia/Hong_Kong": timezone(timedelta(hours=8), "HKT"),
    "Hongkong": timezone(timedelta(hours=8), "HKT"),
    "Asia/Singapore": timezone(timedelta(hours=8), "SGT"),
    "Singapore": timezone(timedelta(hours=8), "SGT"),
}


def _resolve_timezone(name: str) -> tzinfo:
    """Resolve an IANA timezone name to a tzinfo with Windows fallbacks.

    Args:
        name: IANA timezone identifier.

    Returns:
        tzinfo instance.
    """
    if name in ("UTC", "GMT", "Etc/UTC", "Etc/GMT"):
        return UTC
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError, ModuleNotFoundError, OSError, KeyError:
        pass

    normalized = name.strip()
    return _FALLBACK_TIMEZONES.get(normalized, UTC)


class SessionCalendarService(DefineSessionsCapability):
    """Manage and preview effective trading intervals."""

    def __init__(
        self,
        config: SessionCalendarConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the session calendar service with configuration.

        Args:
            config: Optional configuration dataclass.
            event_bus: Optional kernel event bus for domain event publishing.
        """
        self._config = config or SessionCalendarConfig()
        self._event_bus = event_bus
        self._mem_uri: str | None = None
        self._mem_conn: sqlite3.Connection | None = None
        if self._config.database_path is None:
            self._mem_uri = f"file:mem_{id(self)}?mode=memory&cache=shared"
            self._mem_conn = sqlite3.connect(self._mem_uri, uri=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a configured SQLite connection.

        Returns:
            Configured SQLite database connection.
        """
        if self._config.database_path is not None:
            conn = sqlite3.connect(str(self._config.database_path))
        else:
            conn = sqlite3.connect(self._mem_uri or ":memory:", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema if auto_migrate is enabled."""
        if not self._config.auto_migrate:
            return
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    session_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    raw_json TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_calendars (
                    calendar_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    raw_json TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (calendar_id, version)
                )
                """
            )
            conn.commit()

    @override
    async def define_sessions(
        self,
        request: DefineSessionsRequest,
    ) -> DefineSessionsSuccess | CatalogueFailure:
        """Manage and preview effective trading intervals.

        Args:
            request: Operation-discriminated session and calendar request.

        Returns:
            The stored session or calendar version plus previewed effective
            intervals on success, otherwise a structured catalogue failure.
        """
        match request.operation:
            case "GET":
                return self._handle_get(request)
            case "UPSERT_SESSION":
                return await self._handle_upsert_session(request)
            case "UPSERT_CALENDAR":
                return await self._handle_upsert_calendar(request)
            case "PREVIEW":
                return self._handle_preview(request)

    def _handle_get(
        self,
        request: DefineSessionsRequest,
    ) -> DefineSessionsSuccess | CatalogueFailure:
        """Handle GET operation for trading session definition.

        Args:
            request: Validated GET request.

        Returns:
            DefineSessionsSuccess with session or CatalogueFailure if not found.
        """
        session_id_str = str(request.session_id)
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT raw_json FROM trading_sessions
                WHERE session_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (session_id_str,),
            ).fetchone()
        if row is None:
            refs = (request.session_id,) if request.session_id else ()
            return CatalogueFailure(
                request_id=request.request_id,
                code="CATALOGUE_NOT_FOUND",
                problem=ProblemDetails(
                    type="urn:error:catalogue:not-found",
                    title="Trading Session Not Found",
                    status=404,
                    code="CATALOGUE_NOT_FOUND",
                    detail=f"Trading session '{request.session_id}' not found",
                    request_id=request.request_id,
                ),
                conflicting_refs=refs,
            )
        session_def = TradingSessionDefinition.model_validate_json(row["raw_json"])
        return DefineSessionsSuccess(
            request_id=request.request_id,
            session=session_def,
        )

    async def _handle_upsert_session(
        self,
        request: DefineSessionsRequest,
    ) -> DefineSessionsSuccess | CatalogueFailure:
        """Handle UPSERT_SESSION operation.

        Args:
            request: Validated UPSERT_SESSION request.

        Returns:
            DefineSessionsSuccess containing the stored session.

        Raises:
            ValueError: If request.session is None.
        """
        session = request.session
        if session is None:
            msg = "session is required for UPSERT_SESSION"
            raise ValueError(msg)
        session_id_str = str(session.session_id)
        now_iso = datetime.now(UTC).isoformat()
        raw_json = session.model_dump_json()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO trading_sessions (
                    session_id, version, raw_json, content_hash, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id_str,
                    session.version,
                    raw_json,
                    session.content_hash,
                    now_iso,
                ),
            )
            conn.commit()

        if self._event_bus is not None:
            event = TradingSessionChanged(
                session_id=session.session_id,
                version=session.version,
                content_hash=session.content_hash,
            )
            await self._event_bus.publish(event)

        return DefineSessionsSuccess(
            request_id=request.request_id,
            session=session,
        )

    async def _handle_upsert_calendar(
        self,
        request: DefineSessionsRequest,
    ) -> DefineSessionsSuccess | CatalogueFailure:
        """Handle UPSERT_CALENDAR operation.

        Args:
            request: Validated UPSERT_CALENDAR request.

        Returns:
            DefineSessionsSuccess containing the stored calendar.

        Raises:
            ValueError: If request.calendar is None.
        """
        calendar = request.calendar
        if calendar is None:
            msg = "calendar is required for UPSERT_CALENDAR"
            raise ValueError(msg)
        calendar_id_str = str(calendar.calendar_id)
        now_iso = datetime.now(UTC).isoformat()
        raw_json = calendar.model_dump_json()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO market_calendars (
                    calendar_id, version, raw_json, content_hash, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    calendar_id_str,
                    calendar.version,
                    raw_json,
                    calendar.content_hash,
                    now_iso,
                ),
            )
            conn.commit()

        if self._event_bus is not None:
            event = MarketCalendarChanged(
                calendar_id=calendar.calendar_id,
                version=calendar.version,
                content_hash=calendar.content_hash,
            )
            await self._event_bus.publish(event)

        return DefineSessionsSuccess(
            request_id=request.request_id,
            calendar=calendar,
        )

    def _handle_preview(
        self,
        request: DefineSessionsRequest,
    ) -> DefineSessionsSuccess | CatalogueFailure:
        """Handle PREVIEW operation.

        Args:
            request: Validated PREVIEW request.

        Returns:
            DefineSessionsSuccess with effective intervals or CatalogueFailure.

        Raises:
            ValueError: If from_at or to_at timestamp string is None.
        """
        session_id_str = str(request.session_id)
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT raw_json FROM trading_sessions
                WHERE session_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (session_id_str,),
            ).fetchone()
        if row is None:
            refs = (request.session_id,) if request.session_id else ()
            return CatalogueFailure(
                request_id=request.request_id,
                code="CATALOGUE_NOT_FOUND",
                problem=ProblemDetails(
                    type="urn:error:catalogue:not-found",
                    title="Trading Session Not Found",
                    status=404,
                    code="CATALOGUE_NOT_FOUND",
                    detail=f"Trading session '{request.session_id}' not found",
                    request_id=request.request_id,
                ),
                conflicting_refs=refs,
            )
        session_def = TradingSessionDefinition.model_validate_json(row["raw_json"])
        if request.from_at is None or request.to_at is None:
            msg = "from_at and to_at are required for PREVIEW"
            raise ValueError(msg)
        intervals = self._compute_effective_intervals(
            session=session_def,
            from_at_str=request.from_at,
            to_at_str=request.to_at,
        )
        return DefineSessionsSuccess(
            request_id=request.request_id,
            effective_intervals=tuple(intervals),
        )

    def _generate_day_intervals(
        self,
        current_date: date,
        session: TradingSessionDefinition,
        local_tz: tzinfo,
        early_closes: dict[date, str],
        bounds: tuple[datetime, datetime],
    ) -> list[tuple[datetime, datetime]]:
        """Generate clipped intervals for one active trading date.

        Args:
            current_date: Specific local calendar date.
            session: Stored trading session definition.
            local_tz: Resolved tzinfo provider.
            early_closes: Mapping of date to early close time string.
            bounds: Tuple of (from_dt, to_dt) in UTC.

        Returns:
            List of (open_utc, close_utc) intervals clipped to bounds.
        """
        from_dt, to_dt = bounds
        iso_day = current_date.isoweekday()
        day_intervals: list[tuple[datetime, datetime]] = []
        for interval in session.intervals:
            if interval.day_of_week != iso_day:
                continue

            open_t = time.fromisoformat(interval.open_local)
            close_str = interval.close_local
            if current_date in early_closes:
                close_str = min(close_str, early_closes[current_date])
            close_t = time.fromisoformat(close_str)

            open_dt_local = datetime.combine(current_date, open_t, tzinfo=local_tz)
            if interval.spans_next_day:
                close_dt_local = datetime.combine(
                    current_date + timedelta(days=1), close_t, tzinfo=local_tz
                )
            else:
                close_dt_local = datetime.combine(
                    current_date, close_t, tzinfo=local_tz
                )

            open_utc = open_dt_local.astimezone(UTC)
            close_utc = close_dt_local.astimezone(UTC)
            if close_utc <= open_utc:
                continue

            clipped_start = max(open_utc, from_dt)
            clipped_end = min(close_utc, to_dt)
            if clipped_start < clipped_end:
                day_intervals.append((clipped_start, clipped_end))
        return day_intervals

    def _compute_effective_intervals(
        self,
        session: TradingSessionDefinition,
        from_at_str: str,
        to_at_str: str,
    ) -> list[EffectiveInterval]:
        """Compute effective UTC tradable intervals for date range.

        Args:
            session: Stored trading session definition with calendar.
            from_at_str: Inclusive UTC start timestamp string.
            to_at_str: Exclusive UTC end timestamp string.

        Returns:
            List of effective UTC intervals in chronological order.
        """
        from_dt = datetime.fromisoformat(from_at_str).astimezone(UTC)
        to_dt = datetime.fromisoformat(to_at_str).astimezone(UTC)
        local_tz = _resolve_timezone(session.timezone)

        holidays = set(session.calendar.holiday_dates)
        early_closes = {ec.date: ec.close_local for ec in session.calendar.early_closes}

        start_date = from_dt.astimezone(local_tz).date() - timedelta(days=2)
        end_date = to_dt.astimezone(local_tz).date() + timedelta(days=2)

        raw_intervals: list[tuple[datetime, datetime]] = []
        current_date = start_date
        bounds = (from_dt, to_dt)
        while current_date <= end_date:
            if current_date not in holidays:
                raw_intervals.extend(
                    self._generate_day_intervals(
                        current_date, session, local_tz, early_closes, bounds
                    )
                )
            current_date += timedelta(days=1)

        raw_intervals.sort(key=lambda x: (x[0], x[1]))

        merged: list[tuple[datetime, datetime]] = []
        for start, end in raw_intervals:
            if merged and merged[-1][1] >= start:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        def _format_utc(d: datetime) -> str:
            return d.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        return [
            EffectiveInterval(
                from_at=_format_utc(start),
                to_at=_format_utc(end),
            )
            for start, end in merged
        ]


async def fr_cat_define_trading_sessions(
    service: SessionCalendarService,
    request: DefineSessionsRequest,
) -> DefineSessionsSuccess | CatalogueFailure:
    """Requirement implementation trace for FR-CAT-DEFINE_TRADING_SESSIONS.

    Args:
        service: Bound session calendar service instance.
        request: Session and calendar request.

    Returns:
        Operation result or failure.
    """
    return await service.define_sessions(request)


async def fr_cat_define_market_calendars(
    service: SessionCalendarService,
    request: DefineSessionsRequest,
) -> DefineSessionsSuccess | CatalogueFailure:
    """Requirement implementation trace for FR-CAT-DEFINE_MARKET_CALENDARS.

    Args:
        service: Bound session calendar service instance.
        request: Session and calendar request.

    Returns:
        Operation result or failure.
    """
    return await service.define_sessions(request)


async def fr_cat_preview_trading_intervals(
    service: SessionCalendarService,
    request: DefineSessionsRequest,
) -> DefineSessionsSuccess | CatalogueFailure:
    """Requirement implementation trace for FR-CAT-PREVIEW_TRADING_INTERVALS.

    Args:
        service: Bound session calendar service instance.
        request: Session and calendar request.

    Returns:
        Operation result or failure.
    """
    return await service.define_sessions(request)


async def main() -> None:
    """Executable usage demonstration for FEAT-CAT-DEFINE_SESSIONS.

    Raises:
        TypeError: If scenario response type does not match expectations.
    """
    service = SessionCalendarService()
    req_id = "00000000-0000-7000-8000-000000000001"
    snap_id = "00000000-0000-7000-8000-000000000002"
    cal_id = "00000000-0000-7000-8000-000000000010"
    sess_id = "00000000-0000-7000-8000-000000000020"

    print("=== SCENARIO: FR-CAT-DEFINE_MARKET_CALENDARS ===")
    calendar = MarketCalendarVersion(
        calendar_id=cal_id,
        version=1,
        timezone="America/New_York",
        holiday_dates=(date(2026, 7, 3), date(2026, 12, 25)),
        early_closes=(
            CalendarEarlyClose(date=date(2026, 11, 27), close_local="13:00:00"),
        ),
        content_hash="c" * 64,
    )
    cal_req = DefineSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="UPSERT_CALENDAR",
        calendar=calendar,
    )
    res_cal = await fr_cat_define_market_calendars(service, cal_req)
    if not isinstance(res_cal, DefineSessionsSuccess) or res_cal.calendar is None:
        msg = f"Failed calendar scenario: {res_cal}"
        raise TypeError(msg)
    print(
        f"Stored Market Calendar: {res_cal.calendar.calendar_id} "
        f"v{res_cal.calendar.version}"
    )

    print("\n=== SCENARIO: FR-CAT-DEFINE_TRADING_SESSIONS ===")
    intervals = (
        TradingInterval(day_of_week=1, open_local="09:30:00", close_local="16:00:00"),
        TradingInterval(day_of_week=2, open_local="09:30:00", close_local="16:00:00"),
        TradingInterval(day_of_week=3, open_local="09:30:00", close_local="16:00:00"),
        TradingInterval(day_of_week=4, open_local="09:30:00", close_local="16:00:00"),
        TradingInterval(day_of_week=5, open_local="09:30:00", close_local="16:00:00"),
    )
    session = TradingSessionDefinition(
        session_id=sess_id,
        version=1,
        name="US Equity Regular Trading Hours",
        timezone="America/New_York",
        intervals=intervals,
        calendar=calendar,
        end_of_day_policy="SESSION_CLOSE",
        content_hash="b" * 64,
    )
    sess_req = DefineSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="UPSERT_SESSION",
        session=session,
    )
    res_sess = await fr_cat_define_trading_sessions(service, sess_req)
    if not isinstance(res_sess, DefineSessionsSuccess) or res_sess.session is None:
        msg = f"Failed session scenario: {res_sess}"
        raise TypeError(msg)
    print(
        f"Stored Trading Session: {res_sess.session.name} "
        f"(id={res_sess.session.session_id})"
    )

    print("\n=== SCENARIO: FR-CAT-PREVIEW_TRADING_INTERVALS ===")
    prev_req = DefineSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="PREVIEW",
        session_id=sess_id,
        from_at="2026-10-26T00:00:00.000000Z",
        to_at="2026-11-07T00:00:00.000000Z",
    )
    res_prev = await fr_cat_preview_trading_intervals(service, prev_req)
    if not isinstance(res_prev, DefineSessionsSuccess):
        msg = f"Failed preview scenario: {res_prev}"
        raise TypeError(msg)
    print(
        f"Previewed {len(res_prev.effective_intervals)} effective tradable intervals."
    )
    for idx, iv in enumerate(res_prev.effective_intervals[:3]):
        print(f"  Interval {idx + 1}: {iv.from_at} -> {iv.to_at}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
