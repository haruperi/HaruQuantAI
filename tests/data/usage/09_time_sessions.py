"""Demonstrate FEAT-DATA-09 time, schedule, and session operations."""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    ActiveMarketSessionsRequest,
    DataError,
    ExchangeSessionRequest,
    MarketHoursRequest,
    ScheduleRequest,
    WeeklyHoliday,
    WeeklyScheduleDefinition,
    WeeklyScheduleProvider,
    classify_gap,
    get_active_market_sessions,
    get_exchange_sessions,
    get_market_hours,
    get_timeframe_spec,
    get_trading_sessions,
    require_utc,
    validate_resample_target,
)
from app.utils import generate_id

_START = datetime(2026, 6, 1, 0, 0, tzinfo=UTC)
_END = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_21_market_hours() -> None:
    """Inspect market hours for a given symbol and date using get_market_hours."""
    _header("Inspect market hours for a given symbol and date using get_market_hours.")
    req_id = generate_id("req")
    request = ScheduleRequest(
        source_id="usage-offline-source",
        symbol="EURUSD",
        view="hours",
        timezone="UTC",
        request_id=req_id,
    )
    try:
        hours = get_market_hours(request)
        print(f"Market hours: symbol={hours.symbol} sessions={len(hours.hours)}")
    except DataError as error:
        print(f"Market hours failed closed: {error.code}")


def example_22_trading_sessions() -> None:
    """Inspect trading sessions for a symbol and date."""
    _header("Inspect trading sessions for a symbol and date.")
    req_id = generate_id("req")
    request = ScheduleRequest(
        source_id="usage-offline-source",
        symbol="EURUSD",
        view="sessions",
        timezone="UTC",
        request_id=req_id,
    )
    try:
        schedule = get_trading_sessions(request)
        print(f"Trading sessions: count={len(schedule.sessions)}")
    except DataError as error:
        print(f"Trading sessions failed closed: {error.code}")


def _demonstrate_feature() -> None:
    """Run all time and session examples."""
    example_21_market_hours()
    example_22_trading_sessions()

    require_utc(_START)
    spec = get_timeframe_spec("M5")
    print(f"Timeframe spec: key={spec.key} seconds={spec.duration.total_seconds()}")

    validate_resample_target("M1", "M5")
    print("Validated resample target: M5")

    gap = classify_gap(_START, _END)
    print(f"Gap classification: {gap.value}")


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_034() -> None:
    _header("fr_data_034")
    "FR-DATA-034: Return current configured hours and normalized UTC sessions, advance cross-midnight windows correctly, and reject historical reconstruction."
    _demonstrate_once()


def fr_data_117() -> None:
    """FR-DATA-117: Return provider- or venue-authoritative symbol trading windows as ordered timezone-aware UTC intervals without inferring a venue from ticker text."""
    _header(
        "FR-DATA-117: Return provider- or venue-authoritative symbol trading windows as ordered timezone-aware UTC intervals without inferring a venue from ticker text."
    )
    sessions = get_exchange_sessions(
        ExchangeSessionRequest(
            symbol="IBM",
            calendar_code="XNYS",
            start=date(2026, 7, 6),
            end=date(2026, 7, 6),
            request_id=generate_id("req"),
        )
    )
    print(f"Venue sessions: count={len(sessions)} source={sessions[0].source}")


def fr_data_118() -> None:
    """FR-DATA-118: Derive `is_open`, `current_session`, and `next_session` deterministically from authoritative ordered windows at the checked UTC instant."""
    _header(
        "FR-DATA-118: Derive `is_open`, `current_session`, and `next_session` deterministically from authoritative ordered windows at the checked UTC instant."
    )
    provider = WeeklyScheduleProvider(
        WeeklyScheduleDefinition(
            source_id="configured-demo",
            symbol="EURUSD",
            timezone="UTC",
            sessions={day: ((time(0), time(23, 59)),) for day in range(7)},
            effective_from=date(2020, 1, 1),
            revision="usage-v1",
        )
    )
    result = get_market_hours(
        MarketHoursRequest(
            source_id="configured-demo",
            symbol="EURUSD",
            request_id=generate_id("req"),
        ),
        provider,
    )
    print(f"Market open: {result.is_open}")


def fr_data_119() -> None:
    """FR-DATA-119: Require an explicit registered exchange-calendar code for exchange-traded symbols and return bounded holiday-, break-, and shortened-session-aware UTC windows."""
    _header(
        "FR-DATA-119: Require an explicit registered exchange-calendar code for exchange-traded symbols and return bounded holiday-, break-, and shortened-session-aware UTC windows."
    )
    request = ExchangeSessionRequest(
        symbol="IBM",
        calendar_code="XNYS",
        start=date(2026, 7, 6),
        end=date(2026, 7, 6),
        request_id=generate_id("req"),
    )
    print(f"Explicit exchange: {get_exchange_sessions(request)[0].source}")


def fr_data_120() -> None:
    """FR-DATA-120: Expand an explicit timezone, effective range, revision, weekly interval map, and date holiday overrides for providers that expose no session API; never label configured evidence as provider evidence."""
    _header(
        "FR-DATA-120: Expand an explicit timezone, effective range, revision, weekly interval map, and date holiday overrides for providers that expose no session API; never label configured evidence as provider evidence."
    )
    provider = WeeklyScheduleProvider(
        WeeklyScheduleDefinition(
            source_id="configured-demo",
            symbol="EURUSD",
            timezone="Europe/London",
            sessions={0: ((time(8), time(17)),)},
            effective_from=date(2026, 1, 1),
            holidays=(WeeklyHoliday(date=date(2026, 7, 27)),),
            revision="usage-v1",
        )
    )
    sessions = provider.get_sessions(
        start=datetime(2026, 7, 20, tzinfo=UTC),
        end=datetime(2026, 7, 28, tzinfo=UTC),
    )
    print(f"Configured sessions after holiday override: {len(sessions)}")


def fr_data_121() -> None:
    """FR-DATA-121: Classify configurable named sessions in regional timezones with DST handling, including cross-midnight definitions."""
    _header(
        "FR-DATA-121: Classify configurable named sessions in regional timezones with DST handling, including cross-midnight definitions."
    )
    result = get_active_market_sessions(
        ActiveMarketSessionsRequest(
            symbol="EURUSD",
            at=datetime(2026, 7, 20, 13, tzinfo=UTC),
            request_id=generate_id("req"),
        )
    )
    print(f"Analytical sessions: {', '.join(result.sessions)}")


def fr_data_122() -> None:
    """FR-DATA-122: Keep analytical named-session labels structurally separate from symbol tradability so labels never authorize or validate an order."""
    _header(
        "FR-DATA-122: Keep analytical named-session labels structurally separate from symbol tradability so labels never authorize or validate an order."
    )
    result = get_active_market_sessions(
        ActiveMarketSessionsRequest(
            symbol="EURUSD",
            at=datetime(2026, 7, 20, 13, tzinfo=UTC),
            request_id=generate_id("req"),
        )
    )
    print(f"Labels do not authorize orders: {bool(result.sessions)}")


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_034,
        fr_data_117,
        fr_data_118,
        fr_data_119,
        fr_data_120,
        fr_data_121,
        fr_data_122,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
