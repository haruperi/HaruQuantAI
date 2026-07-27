"""Executable Optimization search usage example.

Demonstrates candidate generation, grid search, random sampling, and bounded
search execution.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization.search import (
    CandidateResult,
    SearchMethod,
    iter_grid_candidates,
    run_bounded_search,
    sample_random_candidates,
    select_top_candidates,
)
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_constraints import _space
from tests.optimization.unit.test_search_contracts import search_request


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_search() -> None:
    """Demonstrate optimization search methods."""
    _header("Demonstrate optimization search methods.")
    print("Optimization Example 3: Search Methods and Execution")

    # 1. Search method enum & request
    req = search_request()
    print(
        f"Search Method: {SearchMethod.GRID.value}, "
        f"max candidates: {req.max_candidates}"
    )

    # 2. Grid candidate iteration
    space = _space()
    grid_candidates = list(
        iter_grid_candidates(
            space, max_candidates=10, max_expansion=10, max_constraints=5
        )
    )
    print(f"Generated {len(grid_candidates)} grid candidate parameter combinations.")

    # 3. Random candidate sampling
    random_candidates = sample_random_candidates(
        space, candidate_count=2, seed=3, max_expansion=10, max_constraints=5
    )
    print(f"Sampled {len(random_candidates)} random candidates.")

    # 4. Candidate result model
    cand_res = CandidateResult(
        candidate_hash="a" * 64,
        executable_parameters={"period": 2},
        state="rejected",
        reason_code="CONSTRAINT_REJECTED",
    )
    print(f"CandidateResult status: {cand_res.state}, reason: {cand_res.reason_code}")

    # 5. Run bounded search with adapter
    summary = run_bounded_search(req, FakeAdapter())
    print(
        f"Bounded search ID: {summary.search_id}, "
        f"best candidate: {summary.best_candidate_hash[:8]}..."
    )

    top_candidates = select_top_candidates(summary, 1)
    print(f"Top selected candidates count: {len(top_candidates)}")


def main() -> None:
    """Run Optimization search usage example."""
    example_search()


if __name__ == "__main__":
    main()
