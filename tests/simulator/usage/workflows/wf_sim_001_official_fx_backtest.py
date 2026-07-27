"""WF-SIM-001: execute the official FX backtest path."""

from __future__ import annotations

import sys
import tempfile
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import generate_tick_series
from app.services.simulator import (
    build_tick_timeline,
    run_backtest,
    validate_market_data,
    validate_run_inputs,
)
from tests.simulator.unit.test_engine import _engine
from tests.simulator.unit.test_validate import _context
from tests.simulator.usage.workflows._support import (
    authority,
    backtest_request,
    dependencies,
    live_market_dataset,
)

WORKFLOW_ID = "WF-SIM-001"
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
    print("INPUT BOUNDARY — SimulationBacktestRequestV1 and genuine MT5 evidence")
    bars = live_market_dataset()
    input_ticks = generate_tick_series(
        bars,
        model="trading_bar",
        trading_timeframe="M1",
        spread_model="fixed_spread",
        fixed_spread_points=Decimal(2),
        point_value=Decimal("0.00001"),
    )
    request = backtest_request(input_ticks)

    # Stage 1 — Validate authentication, request structure, references, route, and Phase 1 scope.
    _stage(1)
    validate_run_inputs(request.model_dump(mode="python", warnings=False))
    auth = authority(request)

    # Stage 2 — Validate execution-critical Data evidence before creating state.
    _stage(2)
    ticks = generate_tick_series(
        bars,
        model="trading_bar",
        trading_timeframe="M1",
        spread_model="fixed_spread",
        fixed_spread_points=Decimal(2),
        point_value=Decimal("0.00001"),
    )
    validation_context = _context(ticks).model_copy(
        update={"allowed_tick_models": ("trading_bar",)}
    )
    validated = validate_market_data(ticks, validation_context)

    # Stage 3 — Generate canonical ticks and build the ordered execution clock.
    _stage(3)
    timeline = build_tick_timeline(ticks)

    # Stage 4 — Receive approved Strategy, Risk, and Trading intent boundaries.
    _stage(4)
    print("Approved timeline/request:", len(timeline), request.strategy_id)

    # Stage 5 — Execute ticks through the event-driven engine and journal state transitions.
    _stage(5)
    with tempfile.TemporaryDirectory(prefix="wf-sim-001-engine-") as directory:
        engine = _engine(Path(directory), "official")
        receipts = engine.execute_tick(timeline[0])
        print("First-tick receipts:", len(receipts))

    # Stage 6 — Persist canonical reporting artifacts and return SimulationResult.
    _stage(6)
    with tempfile.TemporaryDirectory(prefix="wf-sim-001-run-") as directory:
        result = run_backtest(
            request,
            auth,
            dependencies(Path(directory), input_ticks),
        )
    print("Validated evidence:", validated.data_hash)
    print("OUTPUT BOUNDARY — typed SimulationResult:", result.status)


if __name__ == "__main__":
    main()
