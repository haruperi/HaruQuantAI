"""WF-SIM-009: execute and reconcile a portfolio simulation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import run_portfolio_backtest, unwrap_simulation_response
from tests.simulator.usage.workflows._support import (
    dependencies,
    live_tick_dataset,
    portfolio_request,
)

WORKFLOW_ID = "WF-SIM-009"
STAGES = (
    "Receive PortfolioBacktestRequestV1 with immutable candidate and MT5 Data/FX lineage.",
    "Validate component allocations, versions, hashes, range, seed, and config hash.",
    "Execute every component through the ordinary deterministic Simulation path.",
    "Reconcile component and aggregate journals and account evidence.",
    "Return PortfolioSimulationResult v1 without approving or modifying allocation.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented portfolio-backtest workflow."""
    print(f"{WORKFLOW_ID} — Portfolio Backtest")
    print("INPUT BOUNDARY — PortfolioBacktestRequestV1 and genuine MT5 evidence")

    # Stage 1 — Receive PortfolioBacktestRequestV1 with immutable candidate and MT5 Data/FX lineage.
    _stage(1)
    dataset = live_tick_dataset()
    request, auth = portfolio_request(dataset)

    # Stage 2 — Validate component allocations, versions, hashes, range, seed, and config hash.
    _stage(2)
    assert sum(component.capital_weight for component in request.components) == 1

    # Stage 3 — Execute every component through the ordinary deterministic Simulation path.
    _stage(3)
    with tempfile.TemporaryDirectory(prefix="wf-sim-009-") as directory:
        result = unwrap_simulation_response(
            run_portfolio_backtest(
                request,
                auth,
                dependencies(Path(directory), dataset),
            ),
            operation="simulation.workflow.wf_sim_009.run_portfolio_backtest",
        )

    # Stage 4 — Reconcile component and aggregate journals and account evidence.
    _stage(4)
    assert len(result.component_results) == len(request.components)

    # Stage 5 — Return PortfolioSimulationResult v1 without approving or modifying allocation.
    _stage(5)
    print("OUTPUT BOUNDARY — typed PortfolioSimulationResult v1:", result.status)


if __name__ == "__main__":
    main()
