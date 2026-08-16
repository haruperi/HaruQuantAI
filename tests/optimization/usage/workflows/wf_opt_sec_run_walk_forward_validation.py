"""WF-OPT-SEC: run bounded walk-forward validation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    build_time_series_splits,
    execute_candidate,
    run_bounded_search,
    run_walk_forward_validation,
)
from app.utils import flush_logging
from tests.optimization.usage._support import (
    genuine_execution_bundle,
    walk_forward_request,
)

WORKFLOW_ID = "WF-OPT-SEC"
STAGES = (
    "Receive approved WalkForwardRequest, Simulation adapter, and MT5 Data provenance.",
    "Build rolling or expanding UTC folds with purge and effective embargo.",
    "Run bounded train-window search and execute a candidate out of sample.",
    "Run walk-forward validation and return fold and aggregate degradation evidence.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")


# fmt: on


def main() -> None:
    """Execute the documented walk-forward workflow."""
    print(f"{WORKFLOW_ID} — Run Walk-Forward Validation")
    print("INPUT BOUNDARY — WalkForwardRequest and Simulation adapter")

    # Stage 1 — Receive approved WalkForwardRequest, Simulation adapter, and MT5 Data provenance.
    _stage(1)
    dataset, candidate_request, adapter = genuine_execution_bundle()
    request = walk_forward_request(dataset)

    # Stage 2 — Build rolling or expanding UTC folds with purge and effective embargo.
    _stage(2)
    folds = build_time_series_splits(request)

    # Stage 3 — Run bounded train-window search and execute a candidate out of sample.
    _stage(3)
    search = asyncio.run(run_bounded_search(request.search, adapter))
    candidate = asyncio.run(
        execute_candidate(
            candidate_request,
            adapter,
            deterministic_only=True,
        )
    )

    # Stage 4 — Run walk-forward validation and return fold and aggregate degradation evidence.
    _stage(4)
    result = asyncio.run(run_walk_forward_validation(request, adapter))
    print("Search/candidate:", search.search_id, candidate.candidate_hash)
    print("OUTPUT BOUNDARY — typed walk-forward evidence:", len(folds), result.status)


if __name__ == "__main__":
    main()
    flush_logging()
