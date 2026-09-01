"""Explicit revisioned weekly schedules for providers without session APIs."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.kernel.identity import generate_id
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.time_sessions.contracts import (
    MarketSchedule,
    SessionWindow,
    TradingSession,
    WeeklyHoliday,
    WeeklyScheduleDefinition,
)


class WeeklyScheduleProvider:
    """Expand one explicit weekly definition without guessing provider hours."""

    def __init__(self, definition: WeeklyScheduleDefinition) -> None:
        """Initialize the provider.

        Args:
            definition: Revisioned configured schedule.
        """
        self._definition = definition

    def _get_sessions_raw(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> tuple[TradingSession, ...]:
        """Expand configured sessions intersecting a bounded UTC range.

        Args:
            start: Inclusive UTC range start.
            end: Exclusive UTC range end.

        Returns:
            Ordered configured sessions.

        Raises:
            DataError: If bounds, effective dates, or timezone are invalid.
        """
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise DataError("INVALID_INPUT", safe_details={"field": "range"})
        try:
            timezone = ZoneInfo(self._definition.timezone)
        except ZoneInfoNotFoundError as error:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "definition.timezone"},
            ) from error
        first = start.astimezone(timezone).date() - timedelta(days=1)
        last = end.astimezone(timezone).date()
        holidays = {item.date: item for item in self._definition.holidays}
        sessions: list[TradingSession] = []
        current = first
        while current <= last:
            sessions.extend(self._sessions_for_date(current, timezone, holidays))
            current += timedelta(days=1)
        return tuple(
            sorted(
                (
                    session
                    for session in sessions
                    if session.closes_at > start and session.opens_at < end
                ),
                key=lambda session: session.opens_at,
            )
        )

    def get_sessions(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> StandardResponse[tuple[TradingSession, ...]]:
        """Expand configured sessions intersecting a bounded UTC range.

        Args:
            start: Inclusive UTC range start.
            end: Exclusive UTC range end.

        Returns:
            Standard response carrying ordered configured sessions.

        Raises:
            (in-band) ``INVALID_INPUT`` if bounds, effective dates, or timezone are
            invalid.
        """
        return run_data_operation(
            operation="data.time_sessions.weekly_schedule_provider.get_sessions",
            request_id=generate_id("req"),
            start_time=data_start_time(),
            raw=lambda: self._get_sessions_raw(start=start, end=end),
        )

    def _get_schedule_raw(
        self,
        *,
        source_id: str,
        symbol: str,
        timezone: str,
        observed_at: datetime,
        request_id: str,
    ) -> MarketSchedule:
        """Return the next seven days as the canonical Data schedule.

        Args:
            source_id: Requested source identifier.
            symbol: Requested exact symbol.
            timezone: Requested display timezone identity.
            observed_at: UTC observation instant.
            request_id: Canonical trace identity.

        Returns:
            Current configured schedule.

        Raises:
            DataError: If the requested identity differs from the definition.
        """
        if (
            source_id != self._definition.source_id
            or symbol != self._definition.symbol
            or timezone != self._definition.timezone
        ):
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "weekly_schedule_identity"},
                request_id=request_id,
            )
        sessions = self._get_sessions_raw(
            start=observed_at,
            end=observed_at + timedelta(days=8),
        )
        windows = tuple(
            SessionWindow(
                label=session.label or f"session-{index}",
                opens_at=session.opens_at,
                closes_at=session.closes_at,
            )
            for index, session in enumerate(sessions, start=1)
        )
        return MarketSchedule(
            source_id=source_id,
            symbol=symbol,
            timezone=timezone,
            hours=windows,
            sessions=windows,
            observed_at=observed_at,
            request_id=request_id,
        )

    def get_schedule(
        self,
        *,
        source_id: str,
        symbol: str,
        timezone: str,
        observed_at: datetime,
        request_id: str,
    ) -> StandardResponse[MarketSchedule]:
        """Return the next seven days as the canonical Data schedule.

        Args:
            source_id: Requested source identifier.
            symbol: Requested exact symbol.
            timezone: Requested display timezone identity.
            observed_at: UTC observation instant.
            request_id: Canonical trace identity.

        Returns:
            Standard response carrying the current configured schedule.

        Raises:
            (in-band) ``INVALID_INPUT`` if the requested identity differs from the
            definition.
        """
        return run_data_operation(
            operation="data.time_sessions.weekly_schedule_provider.get_schedule",
            request_id=request_id,
            start_time=data_start_time(),
            raw=lambda: self._get_schedule_raw(
                source_id=source_id,
                symbol=symbol,
                timezone=timezone,
                observed_at=observed_at,
                request_id=request_id,
            ),
        )

    def _sessions_for_date(
        self,
        day: date,
        timezone: ZoneInfo,
        holidays: dict[date, WeeklyHoliday],
    ) -> list[TradingSession]:
        """Expand one local date under effective-range and holiday rules.

        Args:
            day: Local calendar date.
            timezone: Configured venue timezone.
            holidays: Indexed date overrides.

        Returns:
            Sessions for the date.
        """
        if day < self._definition.effective_from or (
            self._definition.effective_to is not None
            and day > self._definition.effective_to
        ):
            return []
        holiday = holidays.get(day)
        intervals: tuple[tuple[time, time], ...]
        if holiday is not None:
            if holiday.opens_at is None or holiday.closes_at is None:
                return []
            intervals = ((holiday.opens_at, holiday.closes_at),)
        else:
            intervals = self._definition.sessions.get(day.weekday(), ())
        return [
            self._session(day, opens_at, closes_at, timezone, index)
            for index, (opens_at, closes_at) in enumerate(intervals, start=1)
        ]

    def _session(
        self,
        day: date,
        opens_at: time,
        closes_at: time,
        timezone: ZoneInfo,
        index: int,
    ) -> TradingSession:
        """Create one configured session and normalize it to UTC.

        Args:
            day: Local opening date.
            opens_at: Local opening time.
            closes_at: Local closing time.
            timezone: Venue timezone.
            index: Stable daily interval index.

        Returns:
            One normalized session.
        """
        local_open = datetime.combine(day, opens_at, tzinfo=timezone)
        close_day = day if closes_at > opens_at else day + timedelta(days=1)
        local_close = datetime.combine(close_day, closes_at, tzinfo=timezone)
        return TradingSession(
            symbol=self._definition.symbol,
            opens_at=local_open.astimezone(UTC),
            closes_at=local_close.astimezone(UTC),
            source=f"configured:{self._definition.source_id}:{self._definition.revision}",
            label=f"{day.isoformat()}-{index}",
        )


__all__ = ["WeeklyScheduleProvider"]
