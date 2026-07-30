"""WF-SIM-002: execute Simulation Trader operations without a broker."""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    create_simulation_handle,
    execute_simulation_handle_operation,
    match_order,
    price_order,
    unwrap_simulation_response,
)
from tests.simulator.usage.workflows._support import (
    execution_profile,
    live_tick_dataset,
    workflow_engine,
    workflow_order_intent,
    workflow_tick,
)

WORKFLOW_ID = "WF-SIM-002"
STAGES = (
    "Receive Trading-owned OrderIntent with route sim and approved volume.",
    "Submit the unchanged intent through SimTrader.submit_order().",
    "Price and match it against the current canonical tick.",
    "Execute the tick, mutate only simulated state, and append journal evidence.",
    "Return the simulated receipt and immutable SimTrader.snapshot().",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented SimTrader workflow."""
    print(f"{WORKFLOW_ID} — Simulation Trader Operations")
    print("INPUT BOUNDARY — Trading-owned OrderIntent(route=sim)")
    with tempfile.TemporaryDirectory(prefix="wf-sim-002-") as directory:
        dataset = live_tick_dataset()
        engine = workflow_engine(Path(directory), dataset)
        trader = create_simulation_handle("SimTrader", engine)
        intent = workflow_order_intent(dataset)
        tick = workflow_tick(dataset)

        # Stage 1 — Receive Trading-owned OrderIntent with route sim and approved volume.
        _stage(1)
        assert intent.route.value == "sim"

        # Stage 2 — Submit the unchanged intent through SimTrader.submit_order().
        _stage(2)
        receipt = unwrap_simulation_response(
            asyncio.run(
                execute_simulation_handle_operation(  # type: ignore[arg-type]
                    trader, "submit_order", intent
                )
            ),
            operation="simulation.workflow.wf_sim_002.submit_order",
        )

        # Stage 3 — Price and match it against the current canonical tick.
        _stage(3)
        priced = unwrap_simulation_response(
            price_order(intent, tick, execution_profile()),
            operation="simulation.workflow.wf_sim_002.price_order",
        )
        matched = unwrap_simulation_response(
            match_order(intent, tick, execution_profile()),
            operation="simulation.workflow.wf_sim_002.match_order",
        )

        # Stage 4 — Execute the tick, mutate only simulated state, and append journal evidence.
        _stage(4)
        unwrap_simulation_response(
            execute_simulation_handle_operation(engine, "execute_tick", tick),
            operation="simulation.workflow.wf_sim_002.execute_tick",
        )

        # Stage 5 — Return the simulated receipt and immutable SimTrader.snapshot().
        _stage(5)
        snapshot = unwrap_simulation_response(
            execute_simulation_handle_operation(trader, "snapshot"),
            operation="simulation.workflow.wf_sim_002.snapshot",
        )
        print("Price/match:", priced, matched.status)
        print(
            "OUTPUT BOUNDARY — ExecutionReceipt and snapshot:",
            receipt.status,
            snapshot["engine_version"],
        )


if __name__ == "__main__":
    main()
