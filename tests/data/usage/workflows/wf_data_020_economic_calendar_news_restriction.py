"""WF-DATA-020: derive bounded economic-calendar restriction evidence."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_economic_event,
    build_event_impact,
    derive_calendar_state,
    get_calendar_value_field,
    get_symbol_event_profile,
    is_news_restricted_events,
    project_calendar_state,
    project_economic_event,
    unwrap_data_response,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-020"
STAGES = (
    "Admit one bounded provider-neutral UTC calendar event.",
    "Resolve the canonical symbol relevance profile.",
    "Evaluate the deterministic blackout state.",
    "Project bounded provenance and restriction evidence.",
)


def _stage(number: int) -> None:
    """Print one README-aligned stage separator."""
    print(f"\n{'=' * 88}\nStage {number}: {STAGES[number - 1]}\n{'=' * 88}")


def _unwrap(response: object) -> object:
    """Unwrap one successful Data response."""
    return unwrap_data_response(
        response,
        operation="data.workflow.economic_calendar",
        request_id=generate_id("req"),
    )


def main() -> None:
    """Run calendar normalization through the restriction output boundary."""
    print("INPUT BOUNDARY: bounded symbol and provider-neutral UTC event evidence")
    at = datetime(2026, 7, 30, 12, tzinfo=UTC)

    # Stage 1
    _stage(1)
    event = build_economic_event(
        id="forexfactory:us-cpi-20260730",
        provider="scrape:forexfactory",
        name="US CPI",
        category="inflation",
        country="US",
        currency="USD",
        scheduled_at=at + timedelta(minutes=5),
        impact=build_event_impact(3),
        actual=None,
        forecast=None,
        previous=None,
        actual_raw=None,
        forecast_raw=None,
        previous_raw=None,
        unit="percent",
        source="forexfactory",
        source_url="https://www.forexfactory.com/calendar",
        updated_at=at,
    )
    event_projection = project_economic_event(event)

    # Stage 2
    _stage(2)
    profile = _unwrap(get_symbol_event_profile("EURUSD"))
    currencies = tuple(get_calendar_value_field(profile, "currencies"))
    assert "USD" in currencies

    # Stage 3
    _stage(3)
    state = _unwrap(
        derive_calendar_state(
            "EURUSD",
            at,
            events=(event,),
            evidence_ref="forexfactory:us-cpi-20260730",
        )
    )
    restricted = _unwrap(is_news_restricted_events((event,), at))
    assert restricted is True

    # Stage 4
    _stage(4)
    evidence = {
        "event": event_projection,
        "profile_currencies": currencies,
        "calendar_state": project_calendar_state(state),
        "restricted": restricted,
    }
    print(f"OUTPUT BOUNDARY: {evidence}")
    print(f"SUCCESS: {WORKFLOW_ID} completed")


if __name__ == "__main__":
    main()
