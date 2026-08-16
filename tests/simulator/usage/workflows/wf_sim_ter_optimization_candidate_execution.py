"""WF-SIM-TER: execute one Optimization candidate through Simulation."""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import run_backtest_async, unwrap_simulation_response
from tests.simulator.usage.workflows._support import (
    authority,
    backtest_request,
    dependencies,
    live_tick_dataset,
)

WORKFLOW_ID = "WF-SIM-TER"
STAGES = (
    "Receive the bounded Optimization candidate as SimulationBacktestRequest.",
    "Execute it through the canonical run_backtest_async() path.",
    "Preserve immutable result and provenance without ranking or promotion.",
    "Return SimulationResult to the Optimization adapter boundary.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented Optimization candidate workflow."""
    print(f"{WORKFLOW_ID} — Optimization Candidate Execution")
    print("INPUT BOUNDARY — Optimization candidate plus genuine MT5 provenance")

    # Stage 1 — Receive the bounded Optimization candidate as SimulationBacktestRequest.
    _stage(1)
    dataset = live_tick_dataset()
    request = backtest_request(dataset)

    # Stage 2 — Execute it through the canonical run_backtest_async() path.
    _stage(2)
    with tempfile.TemporaryDirectory(prefix="wf-sim-003-") as directory:
        result = unwrap_simulation_response(
            asyncio.run(
                run_backtest_async(
                    request,
                    authority(request),
                    dependencies(Path(directory), dataset),
                )
            ),
            operation="simulation.workflow.wf_sim_003.run_backtest",
        )

    # Stage 3 — Preserve immutable result and provenance without ranking or promotion.
    _stage(3)
    assert result.config_hash == request.config_hash

    # Stage 4 — Return SimulationResult to the Optimization adapter boundary.
    _stage(4)
    print("OUTPUT BOUNDARY — immutable SimulationResult:", result.run_id, result.status)


if __name__ == "__main__":
    main()
