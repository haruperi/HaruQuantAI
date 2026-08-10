"""Map cTrader-authored weekly schedules and holiday closures."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.brokers.canonical_contracts import BrokerTradingSession

_EPOCH_DATE = date(1970, 1, 1)


def _field(value: object, name: str) -> Any:  # noqa: ANN401
    """Read one required provider field.

    Args:
        value: Protobuf message or deterministic dictionary fixture.
        name: Provider field name.

    Returns:
        Required field value.
    """
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def _optional(value: object, name: str) -> Any:  # noqa: ANN401
    """Read one optional provider field.

    Args:
        value: Protobuf message or deterministic dictionary fixture.
        name: Provider field name.

    Returns:
        Field value, or ``None`` when absent.
    """
    if isinstance(value, dict):
        return value.get(name)
    has_field = getattr(value, "HasField", None)
    if callable(has_field):
        try:
            if not has_field(name):
                return None
        except ValueError:
            pass
    return getattr(value, name, None)


def _map_trading_sessions(
    spec: object,
    *,
    symbol: str,
    start: datetime,
    end: datetime,
) -> tuple[BrokerTradingSession, ...]:
    """Map one full cTrader symbol specification into bounded UTC sessions.

    Args:
        spec: Full ``ProtoOASymbol`` or equivalent deterministic fixture.
        symbol: Exact provider symbol name.
        start: Inclusive aware range start.
        end: Exclusive aware range end.

    Returns:
        Provider-authored sessions after broker holiday closures.

    Raises:
        ValueError: If range or provider schedule evidence is invalid.
    """
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise ValueError("cTrader session bounds must be ordered and timezone-aware")
    trading_mode = int(_optional(spec, "tradingMode") or 0)
    if trading_mode != 0:
        return ()
    timezone_name = str(_field(spec, "scheduleTimeZone"))
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise ValueError("cTrader schedule timezone is unavailable") from error
    intervals = tuple(_field(spec, "schedule"))
    if not intervals:
        raise ValueError("cTrader symbol schedule is absent")
    closures = _holiday_closures(
        tuple(_field(spec, "holiday")),
        start=start,
        end=end,
    )
    first_local = start.astimezone(timezone)
    days_since_sunday = (first_local.weekday() + 1) % 7
    sunday = first_local.date() - timedelta(days=days_since_sunday + 7)
    sessions: list[BrokerTradingSession] = []
    while datetime.combine(sunday, time.min, tzinfo=timezone).astimezone(UTC) < end:
        week_start = datetime.combine(sunday, time.min, tzinfo=timezone)
        for index, interval in enumerate(intervals):
            local_open = week_start + timedelta(
                seconds=int(_field(interval, "startSecond"))
            )
            local_close = week_start + timedelta(
                seconds=int(_field(interval, "endSecond"))
            )
            if local_open >= local_close:
                raise ValueError("cTrader schedule interval is unordered")
            segments = _subtract_closures(
                local_open.astimezone(UTC),
                local_close.astimezone(UTC),
                closures,
            )
            for segment_index, (opens_at, closes_at) in enumerate(segments):
                if closes_at <= start or opens_at >= end:
                    continue
                sessions.append(
                    BrokerTradingSession(
                        symbol=symbol,
                        opens_at=max(opens_at, start),
                        closes_at=min(closes_at, end),
                        provider_timezone=timezone_name,
                        provider_metadata={
                            "schedule_index": index,
                            "segment_index": segment_index,
                            "trading_mode": trading_mode,
                        },
                    )
                )
        sunday += timedelta(days=7)
    return tuple(sorted(sessions, key=lambda session: session.opens_at))


def _holiday_closures(
    holidays: tuple[Any, ...],
    *,
    start: datetime,
    end: datetime,
) -> tuple[tuple[datetime, datetime], ...]:
    """Return UTC broker holiday closure intervals relevant to a range.

    Args:
        holidays: Provider holiday messages.
        start: Inclusive aware range start.
        end: Exclusive aware range end.

    Returns:
        Ordered closure intervals.

    Raises:
        ValueError: If a provider holiday timezone is unavailable.
    """
    closures: list[tuple[datetime, datetime]] = []
    years = range(start.year - 1, end.year + 2)
    for holiday in holidays:
        source_day = _EPOCH_DATE + timedelta(days=int(_field(holiday, "holidayDate")))
        recurring = bool(_field(holiday, "isRecurring"))
        days = (
            tuple(
                date(year, source_day.month, source_day.day)
                for year in years
                if _valid_date(year, source_day.month, source_day.day)
            )
            if recurring
            else (source_day,)
        )
        timezone_name = str(_field(holiday, "scheduleTimeZone"))
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as error:
            raise ValueError("cTrader holiday timezone is unavailable") from error
        start_second = _optional(holiday, "startSecond")
        end_second = _optional(holiday, "endSecond")
        if (start_second is None) != (end_second is None):
            raise ValueError("cTrader holiday closure boundaries are incomplete")
        for day in days:
            local_start = datetime.combine(day, time.min, tzinfo=timezone)
            full_day = start_second is None or (
                int(start_second) == 0 and int(end_second) == 0
            )
            if full_day:
                local_end = local_start + timedelta(days=1)
            else:
                local_start += timedelta(seconds=int(start_second))
                local_end = datetime.combine(
                    day, time.min, tzinfo=timezone
                ) + timedelta(seconds=int(end_second))
            if local_start >= local_end:
                raise ValueError("cTrader holiday closure is unordered")
            closure = (local_start.astimezone(UTC), local_end.astimezone(UTC))
            if closure[1] > start and closure[0] < end:
                closures.append(closure)
    return tuple(sorted(closures))


def _valid_date(year: int, month: int, day: int) -> bool:
    """Return whether a recurring holiday exists in one year.

    Args:
        year: Calendar year.
        month: Calendar month.
        day: Calendar day.

    Returns:
        Whether ``date`` accepts the combination.
    """
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _subtract_closures(
    opens_at: datetime,
    closes_at: datetime,
    closures: tuple[tuple[datetime, datetime], ...],
) -> tuple[tuple[datetime, datetime], ...]:
    """Subtract broker closure evidence from one regular session.

    Args:
        opens_at: Regular session opening.
        closes_at: Regular session closing.
        closures: Ordered UTC holiday closures.

    Returns:
        Remaining tradable segments.
    """
    segments = [(opens_at, closes_at)]
    for closure_start, closure_end in closures:
        next_segments: list[tuple[datetime, datetime]] = []
        for segment_start, segment_end in segments:
            if closure_end <= segment_start or closure_start >= segment_end:
                next_segments.append((segment_start, segment_end))
                continue
            if segment_start < closure_start:
                next_segments.append((segment_start, closure_start))
            if closure_end < segment_end:
                next_segments.append((closure_end, segment_end))
        segments = next_segments
    return tuple(segments)


__all__: list[str] = []
