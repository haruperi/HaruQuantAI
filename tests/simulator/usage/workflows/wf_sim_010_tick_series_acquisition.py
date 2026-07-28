"""WF-SIM-010: acquire real bars, generate ticks, and build timeline."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import build_tick_timeline, unwrap_simulation_response
from tests.simulator.usage.workflows._support import (
    live_market_dataset,
    live_tick_dataset,
)

WORKFLOW_ID = "WF-SIM-010"
STAGES = (
    "Retrieve bounded genuine MT5 bar evidence through Data.get_market_data().",
    "Generate canonical ordered ticks through Data.generate_tick_series().",
    "Validate and convert ticks through Simulator.build_tick_timeline().",
    "Return the Data-owned tick dataset and immutable execution clock.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented tick-acquisition workflow."""
    print(f"{WORKFLOW_ID} — Tick-Series Acquisition")
    print("INPUT BOUNDARY — bounded genuine MT5 MarketDataRequest")

    # Stage 1 — Retrieve bounded genuine MT5 bar evidence through Data.get_market_data().
    _stage(1)
    live_market_dataset()

    # Stage 2 — Generate canonical ordered ticks through Data.generate_tick_series().
    _stage(2)
    ticks = live_tick_dataset()

    # Stage 3 — Validate and convert ticks through Simulator.build_tick_timeline().
    _stage(3)
    timeline = unwrap_simulation_response(
        build_tick_timeline(ticks),
        operation="simulation.workflow.wf_sim_010.build_tick_timeline",
    )

    # Stage 4 — Return the Data-owned tick dataset and immutable execution clock.
    _stage(4)
    print(
        "OUTPUT BOUNDARY — tick MarketDataset and execution clock:",
        ticks.record_count,
        len(timeline),
    )


if __name__ == "__main__":
    main()
