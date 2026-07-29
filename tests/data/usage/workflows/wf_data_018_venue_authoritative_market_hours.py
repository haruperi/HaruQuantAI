"""WF-DATA-018: use an explicit revisioned schedule for MT5 EURUSD."""

from __future__ import annotations

import sys
import tempfile
from datetime import date, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_market_hours_request,
    build_weekly_schedule_definition,
    build_weekly_schedule_provider,
    get_market_data,
    get_market_hours,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

WORKFLOW_ID = "WF-DATA-018"
STAGES = (
    "Confirm the exact MT5 EURUSD symbol with genuine observations.",
    "Select an explicit revisioned weekly definition because MT5 exposes no sessions.",
    "Expand authoritative configured windows with timezone and effective range.",
    "Derive deterministic current and next MarketHours state.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute configured venue-hours evidence without ticker inference."""
    print(f"{WORKFLOW_ID} — Venue-Authoritative Market Hours")
    print("INPUT BOUNDARY — exact MT5 symbol and revisioned weekly definition")

    with (
        tempfile.TemporaryDirectory(prefix="wf-data-018-") as directory,
        isolated_runtime(Path(directory)),
    ):
        request_id = generate_id("req")

        # Stage 1 — Confirm the exact MT5 EURUSD symbol with genuine observations.
        _stage(1)
        evidence_resp = get_market_data(market_request("bars", timeframe="M1", limit=1))
        evidence = unwrap_data_response(
            evidence_resp, operation="get_market_data", request_id=request_id
        )
        assert evidence.symbol == "EURUSD"

        # Stage 2 — Select an explicit revisioned weekly definition because MT5 exposes no sessions.
        _stage(2)
        definition = build_weekly_schedule_definition(
            source_id="configured-mt5",
            symbol="EURUSD",
            timezone="UTC",
            sessions={day: ((time(0), time(23, 59)),) for day in range(5)},
            effective_from=date(2020, 1, 1),
            revision="operator-v1",
        )

        # Stage 3 — Expand authoritative configured windows with timezone and effective range.
        _stage(3)
        provider = build_weekly_schedule_provider(definition)

        # Stage 4 — Derive deterministic current and next MarketHours state.
        _stage(4)
        hours_resp = get_market_hours(
            build_market_hours_request(
                source_id=definition.source_id,
                symbol=definition.symbol,
                request_id=request_id,
            ),
            provider,
        )
        hours = unwrap_data_response(
            hours_resp, operation="get_market_hours", request_id=request_id
        )
        print(
            "Market-hours evidence:",
            hours.is_open,
            hours.current_session,
            hours.next_session,
        )
    print("OUTPUT BOUNDARY — UTC sessions and deterministic MarketHours")


if __name__ == "__main__":
    main()
