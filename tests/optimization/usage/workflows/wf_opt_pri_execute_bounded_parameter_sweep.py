"""WF-OPT-PRI: execute one bounded parameter sweep."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    evaluate_constraints,
    execute_candidate,
    iter_grid_candidates,
    run_bounded_search,
    sample_random_candidates,
    validate_parameter_space,
)
from app.utils import flush_logging
from tests.optimization.usage._support import genuine_execution_bundle
from tests.optimization.usage.workflows._support import (
    live_search_request,
)

WORKFLOW_ID = "WF-OPT-PRI"
STAGES = (
    "Validate the bounded parameter space and genuine MT5 Data provenance.",
    "Yield grid and seeded-random candidates without unbounded materialization.",
    "Record constraint failures before any Simulation adapter call.",
    "Execute one version-compatible candidate through the injected adapter.",
    "Run the bounded search and return deterministic SearchSummary evidence.",
)


def _constraint_passes(
    candidate: dict[str, object],
    constraints: tuple[str, ...],
) -> bool:
    """Return False when an inactive field makes a constraint inapplicable."""
    try:
        return evaluate_constraints(candidate, constraints)
    except ValueError:
        return False


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented bounded-sweep workflow."""
    print(f"{WORKFLOW_ID} — Execute a Bounded Parameter Sweep")
    print(
        "INPUT BOUNDARY — SearchRequest, Strategy/Data provenance, Simulation adapter"
    )
    dataset, candidate_request, adapter = genuine_execution_bundle()
    request = live_search_request(dataset)

    # Stage 1 — Validate the bounded parameter space and genuine MT5 Data provenance.
    _stage(1)
    validate_parameter_space(
        request.space,
        max_expansion=request.max_parameter_space_expansion,
        max_constraints=request.max_constraint_count,
    )

    # Stage 2 — Yield grid and seeded-random candidates without unbounded materialization.
    _stage(2)
    grid = tuple(
        iter_grid_candidates(
            request.space,
            max_candidates=request.max_candidates,
            max_expansion=request.max_parameter_space_expansion,
            max_constraints=request.max_constraint_count,
        )
    )
    random = sample_random_candidates(
        request.space,
        candidate_count=2,
        seed=7,
        max_expansion=request.max_parameter_space_expansion,
        max_constraints=request.max_constraint_count,
    )

    # Stage 3 — Record constraint failures before any Simulation adapter call.
    _stage(3)
    accepted = tuple(
        candidate
        for candidate in grid
        if _constraint_passes(candidate, request.space.constraints)
    )

    # Stage 4 — Execute one version-compatible candidate through the injected adapter.
    _stage(4)
    execution = execute_candidate(
        candidate_request,
        adapter,
        deterministic_only=True,
    )

    # Stage 5 — Run the bounded search and return deterministic SearchSummary evidence.
    _stage(5)
    summary = run_bounded_search(request, adapter)
    print("Generated/accepted/random:", len(grid), len(accepted), len(random))
    print(
        "Execution evidence:",
        execution.candidate_hash,
        execution.simulation_run_id,
        f"MT5 rows={len(dataset.records)}",
    )
    print("OUTPUT BOUNDARY — typed SearchSummary:", summary.search_id)


if __name__ == "__main__":
    main()
    flush_logging()
