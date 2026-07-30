"""Executable Optimization search usage example.

Demonstrates candidate generation, grid search, random sampling, and bounded
search execution.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization import (
    iter_grid_candidates,
    run_bounded_search,
    sample_random_candidates,
    select_top_candidates,
)
from tests.optimization.usage._support import (
    genuine_execution_bundle,
    parameter_space,
    search_request,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_search() -> None:
    """Demonstrate optimization search methods."""
    _header("Demonstrate optimization search methods.")
    print("Optimization Example 3: Search Methods and Execution")

    # 1. Search method enum & request
    dataset, _, adapter = genuine_execution_bundle()
    req = search_request(dataset)
    print(f"Search Method: {req.method}, max candidates: {req.max_candidates}")

    # 2. Grid candidate iteration
    space = parameter_space()
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

    # 4. Run bounded search with adapter
    summary = run_bounded_search(req, adapter)
    print(
        f"Bounded search used {dataset.record_count} MT5-derived {dataset.symbol} ticks "
        f"from {dataset.start.isoformat()} to {dataset.end.isoformat()}; "
        f"search ID={summary.search_id}, "
        f"best candidate={summary.best_candidate_hash[:8]}..."
    )

    top_candidates = select_top_candidates(summary, 1)
    print(f"Top selected candidates count: {len(top_candidates)}")


def main() -> None:
    """Run Optimization search usage example."""
    example_search()


if __name__ == "__main__":
    main()
