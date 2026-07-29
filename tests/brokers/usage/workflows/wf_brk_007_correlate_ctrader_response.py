"""WF-BRK-007: correlate concurrent genuine cTrader responses."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    connect_broker,
    disconnect_broker,
    get_broker_connection_status,
    get_broker_value_field,
)
from tests.brokers.usage._support import create_real_adapter, require_success

WORKFLOW_ID = "WF-BRK-007"
STAGES = (
    "Connect one genuine cTrader demo session generation.",
    "Submit concurrent same-result-type status requests.",
    "Accept only each request's canonical correlated response.",
    "Disconnect without retaining stale-generation state.",
)


async def run() -> None:
    """Execute the public cTrader concurrency boundary."""
    print(f"{WORKFLOW_ID} — Correlate cTrader Response")
    print("INPUT BOUNDARY — cTrader requests in one adapter session generation")
    adapter = create_real_adapter("ctrader")
    try:
        # Stage 1 — Connect one genuine cTrader demo session generation.
        _stage(1)
        require_success("cTrader connect", await connect_broker(adapter))

        # Stage 2 — Submit concurrent same-result-type status requests.
        _stage(2)
        first, second = await asyncio.gather(
            get_broker_connection_status(adapter),
            get_broker_connection_status(adapter),
        )

        # Stage 3 — Accept only each request's canonical correlated response.
        _stage(3)
        require_success("First correlated response", first)
        require_success("Second correlated response", second)
        first_data = get_broker_value_field(first, "data")
        second_data = get_broker_value_field(second, "data")
        assert first_data is not None
        assert second_data is not None
        first_state = get_broker_value_field(
            get_broker_value_field(first_data, "state"), "value"
        )
        second_state = get_broker_value_field(
            get_broker_value_field(second_data, "state"), "value"
        )
        print("Correlated states:", first_state, second_state)
    finally:
        # Stage 4 — Disconnect without retaining stale-generation state.
        _stage(4)
        require_success("cTrader disconnect", await disconnect_broker(adapter))
    print("OUTPUT BOUNDARY — two canonical same-type responses in one session")


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
