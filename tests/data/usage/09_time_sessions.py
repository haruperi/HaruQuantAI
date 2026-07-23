"""Demonstrate FEAT-DATA-09 time, schedule, and session operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.time_sessions import (
    ScheduleRequest,
    classify_gap,
    get_market_hours,
    get_timeframe_spec,
    get_trading_sessions,
    require_utc,
    validate_resample_target,
)
from app.utils import generate_id

_START = datetime(2026, 6, 1, 0, 0, tzinfo=UTC)
_END = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)


def example_21_market_hours() -> None:
    """Inspect market hours for a given symbol and date using get_market_hours."""
    req_id = generate_id("req")
    request = ScheduleRequest(
        symbol="EURUSD",
        date=_START.date(),
        request_id=req_id,
    )
    hours = get_market_hours(request)
    print(f"Market hours: symbol={hours.symbol} open={hours.is_market_open} session_type={hours.session_type}")


def example_22_trading_sessions() -> None:
    """Inspect trading sessions for a given symbol and date using get_trading_sessions."""
    req_id = generate_id("req")
    request = ScheduleRequest(
        symbol="EURUSD",
        date=_START.date(),
        request_id=req_id,
    )
    schedule = get_trading_sessions(request)
    print(f"Trading sessions: count={len(schedule.sessions)}")


def main() -> None:
    """Run all time and session examples."""
    example_21_market_hours()
    example_22_trading_sessions()

    require_utc(_START)
    spec = get_timeframe_spec("M5")
    print(f"Timeframe spec: key={spec.timeframe_key} seconds={spec.duration_seconds}")

    target_spec = validate_resample_target("M1", "M5")
    print(f"Validated resample target: {target_spec.timeframe_key}")

    gap = classify_gap(_START, _END, timeframe="H1")
    print(f"Gap classification: is_gap={gap.is_gap} expected_bars={gap.expected_bars}")


if __name__ == "__main__":
    main()
