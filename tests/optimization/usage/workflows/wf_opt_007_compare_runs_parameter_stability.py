"""WF-OPT-007: compare genuine optimization runs and parameter stability."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.composition.logging import flush_logging
from app.services.optimization import (
    calculate_parameter_stability,
    compare_optimization_runs,
    dump_optimization_value,
    run_parameter_sweep,
)
from tests.optimization.usage._support import (
    genuine_execution_bundle,
    search_request,
)

WORKFLOW_ID = "WF-OPT-007"
STAGES = (
    "Receive two bounded searches over the same genuine MT5 evidence.",
    "Execute both searches through the real Simulator and Analytics adapter.",
    "Compare versioned OptimizationResult metric evidence.",
    "Calculate stability from the observed winning parameter sets.",
    "Return comparison and stability evidence without promotion authority.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute two genuine bounded searches and compare their evidence."""
    print(f"{WORKFLOW_ID} — Compare Optimization Runs and Parameter Stability")
    print("INPUT BOUNDARY — two bounded requests plus genuine MT5 market evidence")

    # Stage 1 — Receive two bounded searches over the same genuine MT5 evidence.
    _stage(1)
    dataset, _, adapter = genuine_execution_bundle()
    grid_request = search_request(dataset)
    random_request = search_request(
        dataset,
        method="random",
        candidate_count=2,
        seed=19,
        request_id="req-dddddddd-dddd-4ddd-8ddd-dddddddddddd",
        workflow_id="wf-eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
        correlation_id="cor-ffffffff-ffff-4fff-8fff-ffffffffffff",
    )

    # Stage 2 — Execute both searches through the real Simulator and Analytics adapter.
    _stage(2)
    first_response = asyncio.run(run_parameter_sweep(grid_request, adapter))
    second_response = asyncio.run(run_parameter_sweep(random_request, adapter))
    if first_response.data is None or second_response.data is None:
        raise RuntimeError(
            f"Optimization comparison inputs failed: "
            f"{first_response.error}, {second_response.error}"
        )
    runs = (first_response.data, second_response.data)

    # Stage 3 — Compare versioned OptimizationResult metric evidence.
    _stage(3)
    comparison_response = compare_optimization_runs(runs)
    if comparison_response.data is None:
        raise RuntimeError(f"Comparison failed: {comparison_response.error}")

    # Stage 4 — Calculate stability from the observed winning parameter sets.
    _stage(4)
    winning_parameters = tuple(
        result.ranked_candidates[0] for result in runs if result.ranked_candidates
    )
    stability_response = calculate_parameter_stability(winning_parameters)
    if stability_response.data is None:
        raise RuntimeError(f"Stability calculation failed: {stability_response.error}")

    # Stage 5 — Return comparison and stability evidence without promotion authority.
    _stage(5)
    print(
        "OUTPUT BOUNDARY — genuine comparison evidence:",
        {
            "mt5_rows": len(dataset.records),
            "run_ids": tuple(result.search_id for result in runs),
            "comparison": dump_optimization_value(comparison_response.data),
            "stability": dump_optimization_value(stability_response.data),
        },
    )


if __name__ == "__main__":
    main()
    flush_logging()
