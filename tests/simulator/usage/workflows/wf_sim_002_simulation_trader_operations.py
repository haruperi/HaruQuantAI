"""WF-SIM-002: execute Simulation Trader operations without a broker."""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import SimTrader, match_order, price_order
from tests.simulator.unit.test_engine import _engine, _intent, _tick
from tests.simulator.unit.test_pricing import _profile

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
        engine = _engine(Path(directory), "trader")
        trader = SimTrader(engine)
        intent = _intent()
        tick = _tick()

        # Stage 1 — Receive Trading-owned OrderIntent with route sim and approved volume.
        _stage(1)
        assert intent.route.value == "sim"

        # Stage 2 — Submit the unchanged intent through SimTrader.submit_order().
        _stage(2)
        receipt = asyncio.run(trader.submit_order(intent))

        # Stage 3 — Price and match it against the current canonical tick.
        _stage(3)
        priced = price_order(intent, tick, _profile())
        matched = match_order(intent, tick, _profile())

        # Stage 4 — Execute the tick, mutate only simulated state, and append journal evidence.
        _stage(4)
        engine.execute_tick(tick)

        # Stage 5 — Return the simulated receipt and immutable SimTrader.snapshot().
        _stage(5)
        snapshot = trader.snapshot()
        print("Price/match:", priced, matched.status)
        print(
            "OUTPUT BOUNDARY — ExecutionReceipt and snapshot:",
            receipt.status,
            snapshot["engine_version"],
        )


if __name__ == "__main__":
    main()
