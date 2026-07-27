"""WF-DATA-010: combine configured sessions with genuine MT5 volume."""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    MarketHoursRequest,
    VolumeRequest,
    WeeklyScheduleDefinition,
    WeeklyScheduleProvider,
    get_historical_volume,
    get_market_hours,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-010"
STAGES = (
    "Declare an explicit revisioned EURUSD weekly schedule.",
    "Normalize current configured sessions to UTC MarketHours.",
    "Read bounded genuine MT5 historical volume.",
    "Return schedule and volume with separate provenance.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute current sessions and volume evidence."""
    print(f"{WORKFLOW_ID} — Current Hours, Sessions, and Volume")
    print("INPUT BOUNDARY — explicit schedule plus bounded MT5 volume request")

    # Stage 1 — Declare an explicit revisioned EURUSD weekly schedule.
    _stage(1)
    provider = WeeklyScheduleProvider(
        WeeklyScheduleDefinition(
            source_id="configured-mt5",
            symbol="EURUSD",
            timezone="UTC",
            sessions={day: ((time(0), time(23, 59)),) for day in range(5)},
            effective_from=date(2020, 1, 1),
            revision="operator-v1",
        )
    )

    # Stage 2 — Normalize current configured sessions to UTC MarketHours.
    _stage(2)
    hours = get_market_hours(
        MarketHoursRequest(
            source_id="configured-mt5",
            symbol="EURUSD",
            request_id=generate_id("req"),
        ),
        provider,
    )

    # Stage 3 — Read bounded genuine MT5 historical volume.
    _stage(3)
    end = datetime.now(UTC)
    volume = get_historical_volume(
        VolumeRequest(
            source_id="mt5",
            symbol="EURUSD",
            start=end - timedelta(hours=1),
            end=end,
            mode="summary",
            limit=100,
            request_id=generate_id("req"),
        )
    )

    # Stage 4 — Return schedule and volume with separate provenance.
    _stage(4)
    print("Hours and volume:", len(hours.hours), volume.volume_kind, volume.summary)
    print("OUTPUT BOUNDARY — configured UTC MarketHours plus MT5 VolumeResult")


if __name__ == "__main__":
    main()
