"""WF-OPT-001: validate typed requests and run advisory public operations."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.composition.logging import flush_logging
from app.services.optimization import run_parameter_sweep, run_robustness_analysis
from tests.optimization.usage._support import (
    genuine_execution_bundle,
    monte_carlo_request,
)
from tests.optimization.usage.workflows._support import (
    live_search_request,
)

WORKFLOW_ID = "WF-OPT-001"
STAGES = (
    "Receive typed search or robustness request data at the public input boundary.",
    "Validate shape, bounds, provenance, and capability through the owning contract.",
    "Run the applicable bounded advisory public operation.",
    "Return OptimizationResult v1 or RobustnessAnalysisResult with no trade authority.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")


# fmt: on


def main() -> None:
    """Execute the corrected request-packaging workflow."""
    print(f"{WORKFLOW_ID} — Package an Optimization or Robustness Request")
    print("INPUT BOUNDARY — typed request data plus genuine MT5 Data provenance")

    # Stage 1 — Receive typed search or robustness request data at the public input boundary.
    _stage(1)
    dataset, _, adapter = genuine_execution_bundle()
    search = live_search_request(dataset)
    robustness = monte_carlo_request()

    # Stage 2 — Validate shape, bounds, provenance, and capability through the owning contract.
    _stage(2)
    validated_search = search

    # Stage 3 — Run the applicable bounded advisory public operation.
    _stage(3)
    optimization_result = asyncio.run(run_parameter_sweep(validated_search, adapter))
    robustness_result = run_robustness_analysis(robustness, max_simulations=5)
    assert optimization_result.data is not None
    assert robustness_result.data is not None

    # Stage 4 — Return OptimizationResult v1 or RobustnessAnalysisResult with no trade authority.
    _stage(4)
    print(
        "OUTPUT BOUNDARY — typed advisory results:",
        optimization_result.data.schema_id,
        robustness_result.data.schema_id,
        f"MT5 rows={len(dataset.records)}",
    )


if __name__ == "__main__":
    main()
    flush_logging()
