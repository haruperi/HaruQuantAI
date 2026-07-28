"""WF-OPT-SEC: run bounded walk-forward validation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization.execution import execute_candidate
from app.services.optimization.search import run_bounded_search
from app.services.optimization.validation import (
    build_time_series_splits,
    run_walk_forward_validation,
)
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_execution_contracts import execution_request
from tests.optimization.unit.test_validation_contracts import walk_forward_request
from tests.optimization.usage.workflows._support import (
    live_market_dataset,
    live_search_request,
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
    adapter = FakeAdapter()
    request = walk_forward_request().model_copy(
        update={"search": live_search_request(live_market_dataset())}
    )

    # Stage 2 — Build rolling or expanding UTC folds with purge and effective embargo.
    _stage(2)
    folds = build_time_series_splits(request)

    # Stage 3 — Run bounded train-window search and execute a candidate out of sample.
    _stage(3)
    search = run_bounded_search(request.search, adapter)
    candidate = execute_candidate(
        execution_request(),
        adapter,
        deterministic_only=True,
    )

    # Stage 4 — Run walk-forward validation and return fold and aggregate degradation evidence.
    _stage(4)
    result = run_walk_forward_validation(request, adapter)
    print("Search/candidate:", search.search_id, candidate.candidate_hash)
    print("OUTPUT BOUNDARY — typed walk-forward evidence:", len(folds), result.status)


if __name__ == "__main__":
    main()
