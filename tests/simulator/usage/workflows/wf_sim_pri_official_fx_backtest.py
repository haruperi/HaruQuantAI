"""WF-SIM-PRI: execute the official FX backtest path."""

from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.serialization import canonical_digest
from app.services.simulator import (
    build_tick_timeline,
    create_simulation_value,
    dump_simulation_value,
    run_backtest_async,
    unwrap_simulation_response,
    validate_market_data,
    validate_run_inputs,
)
from tests.simulator.usage.workflows._support import (
    authority,
    backtest_request,
    dependencies,
    live_tick_dataset,
)

WORKFLOW_ID = "WF-SIM-PRI"
STAGES = (
    "Validate authentication, request structure, references, route, and Phase 1 scope.",
    "Validate execution-critical Data evidence before creating state.",
    "Generate canonical ticks and build the ordered execution clock.",
    "Receive approved Strategy, Risk, and Trading intent boundaries.",
    "Execute ticks through the event-driven engine and journal state transitions.",
    "Persist canonical reporting artifacts and return SimulationResult.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented official-backtest workflow."""
    print(f"{WORKFLOW_ID} — Official FX Backtest")
    print("INPUT BOUNDARY — SimulationBacktestRequest and genuine MT5 evidence")
    input_ticks = live_tick_dataset()
    request = backtest_request(input_ticks)

    # Stage 1 — Validate authentication, request structure, references, route, and Phase 1 scope.
    _stage(1)
    unwrap_simulation_response(
        validate_run_inputs(dump_simulation_value(request)),
        operation="simulation.workflow.wf_sim_001.validate_run_inputs",
    )
    auth = authority(request)

    # Stage 2 — Validate execution-critical Data evidence before creating state.
    _stage(2)
    ticks = input_ticks
    validation_context = create_simulation_value(
        "MarketDataValidationContext",
        expected_data_hash=canonical_digest(
            ticks.model_dump(mode="python", warnings=False)
        ),
        requested_start=ticks.start,
        requested_end=ticks.end,
        evaluated_at=ticks.available_at,
        maximum_staleness=timedelta(0),
        allowed_tick_models=("trading_bar",),
    )
    validated = unwrap_simulation_response(
        validate_market_data(ticks, validation_context),
        operation="simulation.workflow.wf_sim_001.validate_market_data",
    )

    # Stage 3 — Generate canonical ticks and build the ordered execution clock.
    _stage(3)
    timeline = unwrap_simulation_response(
        build_tick_timeline(ticks),
        operation="simulation.workflow.wf_sim_001.build_tick_timeline",
    )

    # Stage 4 — Receive approved Strategy, Risk, and Trading intent boundaries.
    _stage(4)
    print(
        "Approved timeline evidence:",
        tuple(dump_simulation_value(tick) for tick in timeline[:3]),
    )

    # Stage 5 — Execute ticks through the event-driven engine and journal state transitions.
    _stage(5)
    print("Execution clock ready:", len(timeline), "observed ticks")

    # Stage 6 — Persist canonical reporting artifacts and return SimulationResult.
    _stage(6)
    with tempfile.TemporaryDirectory(prefix="wf-sim-001-run-") as directory:
        result = unwrap_simulation_response(
            asyncio.run(
                run_backtest_async(
                    request,
                    auth,
                    dependencies(Path(directory), input_ticks),
                )
            ),
            operation="simulation.workflow.wf_sim_001.run_backtest",
        )
    print("Validated evidence:", dump_simulation_value(validated))
    print("OUTPUT BOUNDARY — SimulationResult:", dump_simulation_value(result))


if __name__ == "__main__":
    main()
