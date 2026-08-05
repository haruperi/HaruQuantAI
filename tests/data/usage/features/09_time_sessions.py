"""Demonstrate FEAT-DATA-09 time, schedule, and session operations."""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_active_market_sessions_request,
    build_exchange_session_request,
    build_market_hours_request,
    build_schedule_request,
    build_weekly_holiday,
    build_weekly_schedule_definition,
    build_weekly_schedule_provider,
    classify_gap,
    get_active_market_sessions,
    get_exchange_sessions,
    get_market_hours,
    get_market_hours_dashboard_snapshot,
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


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_data_034() -> None:
    """FR-DATA-034: Stage 1 — Return current configured hours and normalized UTC sessions."""
    _header("Stage 1: Market Hours & Schedule Inspection - Market Hours (FR-DATA-034)")
    req_id = generate_id("req")
    hours_req = build_schedule_request(
        source_id="usage-offline-source",
        symbol="EURUSD",
        view="hours",
        timezone="UTC",
        request_id=req_id,
    )
    hours_res = get_market_hours(hours_req)
    print(_format_result(hours_res))

    sessions_req = build_schedule_request(
        source_id="usage-offline-source",
        symbol="EURUSD",
        view="sessions",
        timezone="UTC",
        request_id=req_id,
    )
    sessions_res = get_trading_sessions(sessions_req)
    print(_format_result(sessions_res))

    require_utc(_START)
    tf_res = get_timeframe_spec("M5")
    print(_format_result(tf_res))

    target_res = validate_resample_target("M1", "M5")
    print(_format_result(target_res))

    gap_res = classify_gap(_START, _END)
    print(_format_result(gap_res))


def fr_data_117_119() -> None:
    """FR-DATA-117, FR-DATA-119: Stage 2 — Return venue-authoritative symbol trading windows as ordered UTC intervals with calendar codes."""
    _header(
        "Stage 2: Venue & Exchange Sessions - Exchange Sessions (FR-DATA-117, FR-DATA-119)"
    )
    req = build_exchange_session_request(
        symbol="IBM",
        calendar_code="XNYS",
        start=date(2026, 7, 6),
        end=date(2026, 7, 6),
        request_id=generate_id("req"),
    )
    res = get_exchange_sessions(req)
    print(_format_result(res))
    if res.status == "success" and res.data:
        print(
            f"Data -> SessionWindow(source={res.data[0].source}, count={len(res.data)})"
        )


def fr_data_118() -> None:
    """FR-DATA-118: Stage 3 — Derive is_open, current_session, and next_session deterministically at the checked UTC instant."""
    _header(
        "Stage 3: Tradability & Open State Resolution - Market Hours State (FR-DATA-118)"
    )
    provider = build_weekly_schedule_provider(
        build_weekly_schedule_definition(
            source_id="configured-demo",
            symbol="EURUSD",
            timezone="UTC",
            sessions={day: ((time(0), time(23, 59)),) for day in range(7)},
            effective_from=date(2020, 1, 1),
            revision="usage-v1",
        )
    )
    res = get_market_hours(
        build_market_hours_request(
            source_id="configured-demo",
            symbol="EURUSD",
            request_id=generate_id("req"),
        ),
        provider,
    )
    print(_format_result(res))
    if res.status == "success" and res.data is not None:
        print(f"Data -> MarketSchedule(is_open={res.data.is_open})")


def fr_data_120() -> None:
    """FR-DATA-120: Stage 4 — Expand explicit timezone, effective range, revision, and holiday overrides for offline schedule providers."""
    _header(
        "Stage 4: Configured Provider Schedule & Holiday Overrides - Weekly Schedule Provider (FR-DATA-120)"
    )
    provider = build_weekly_schedule_provider(
        build_weekly_schedule_definition(
            source_id="configured-demo",
            symbol="EURUSD",
            timezone="Europe/London",
            sessions={0: ((time(8), time(17)),)},
            effective_from=date(2026, 1, 1),
            holidays=(build_weekly_holiday(date=date(2026, 7, 27)),),
            revision="usage-v1",
        )
    )
    res = provider.get_sessions(
        start=datetime(2026, 7, 20, tzinfo=UTC),
        end=datetime(2026, 7, 28, tzinfo=UTC),
    )
    print(_format_result(res))
    if res.status == "success" and res.data is not None:
        print(f"Data -> tuple(sessions={len(res.data)})")


def fr_data_121_122() -> None:
    """FR-DATA-121, FR-DATA-122: Stage 5 — Classify analytical named sessions in regional timezones and keep labels structurally separate from order tradability."""
    _header(
        "Stage 5: Analytical Named Sessions & Isolation - Active Market Sessions (FR-DATA-121, FR-DATA-122)"
    )
    res = get_active_market_sessions(
        build_active_market_sessions_request(
            symbol="EURUSD",
            at=datetime(2026, 7, 20, 13, tzinfo=UTC),
            request_id=generate_id("req"),
        )
    )
    print(_format_result(res))
    if res.status == "success" and res.data is not None:
        result = res.data
        print(f"Data -> ActiveMarketSessions(sessions={list(result.sessions)})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
    print("=" * 80)
    assert get_market_hours_dashboard_snapshot()["status"] == "unavailable"
    print("FEATURE: FEAT-DATA-09 - Time and Session Handling")
    print(
        "PURPOSE: Market hours, venue trading sessions, schedule providers, and analytical session classification"
    )
    print(
        "MODULE FLOW: Stage 1 (Hours & Schedule) -> Stage 2 (Venue & Exchange) -> Stage 3 (Tradability & State) -> Stage 4 (Schedule Provider & Holidays) -> Stage 5 (Analytical Sessions)"
    )
    print("=" * 80)

    fr_data_034()
    fr_data_117_119()
    fr_data_118()
    fr_data_120()
    fr_data_121_122()
    print("SUCCESS: FEAT-DATA-09 completed")


if __name__ == "__main__":
    main()
