"""Executable Optimization search usage example.

Demonstrates FEAT-OPT-03 candidate generation, grid search, random sampling, and bounded search execution.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

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


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_opt_018() -> None:
    """FR-OPT-018: Stage 1 — Search Method & Request Modeling.

    The system shall model search requests with strategy/data provenance, method, seed, and resource caps.
    """
    _header("Stage 1: Search Request - Model Search Request (FR-OPT-018)")
    dataset, _, _ = genuine_execution_bundle()
    req = search_request(dataset)
    print(_format_result(req))
    print(f"Data -> method='{req.method}', max_candidates={req.max_candidates}")


def fr_opt_019() -> None:
    """FR-OPT-019: Stage 2 — Lazy Grid Candidate Iteration.

    The system shall lazily yield valid grid candidates without materializing the full Cartesian product.
    """
    _header("Stage 2: Grid Search - Iterate Grid Candidates (FR-OPT-019)")
    space = parameter_space()
    grid_candidates = list(
        iter_grid_candidates(
            space, max_candidates=10, max_expansion=10, max_constraints=5
        )
    )
    print(_format_result(grid_candidates))
    print(f"Data -> generated_grid_candidates_count={len(grid_candidates)}")


def fr_opt_020() -> None:
    """FR-OPT-020: Stage 2 — Pseudo-Random Candidate Sampling.

    The system shall generate unique pseudo-random candidates deterministically from a required seed.
    """
    _header("Stage 2: Random Search - Sample Random Candidates (FR-OPT-020)")
    space = parameter_space()
    random_candidates = sample_random_candidates(
        space, candidate_count=2, seed=3, max_expansion=10, max_constraints=5
    )
    print(_format_result(random_candidates))
    print(f"Data -> sampled_random_candidates_count={len(random_candidates)}")


def fr_opt_021() -> None:
    """FR-OPT-021: Stage 3 — Bounded Search Execution.

    The system shall evaluate unique valid candidates through the injected adapter and return a search summary.
    """
    _header("Stage 3: Search Execution - Run Bounded Search (FR-OPT-021)")
    dataset, _, adapter = genuine_execution_bundle()
    req = search_request(dataset)
    summary = run_bounded_search(req, adapter)
    print(_format_result(summary))
    print(
        f"Data -> search_id='{summary.search_id}', best_candidate='{summary.best_candidate_hash[:8]}...'"
    )


def fr_opt_022() -> None:
    """FR-OPT-022: Stage 3 — Top Candidate Selection.

    The system shall return the top N candidates from a deterministic search summary.
    """
    _header("Stage 3: Top Selection - Select Top Candidates (FR-OPT-022)")
    dataset, _, adapter = genuine_execution_bundle()
    req = search_request(dataset)
    summary = run_bounded_search(req, adapter)
    top_candidates = select_top_candidates(summary, 1)
    print(_format_result(top_candidates))
    print(f"Data -> top_candidates_count={len(top_candidates)}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-03 — search/ — Bounded Candidate Search\n\n"
        "Purpose: Model search requests, generate grid and pseudo-random candidates lazily, execute bounded search loops, and select top candidates.\n\n"
        "Module flow:\n"
        "-> Stage 1: Search request payload construction and validation\n"
        "-> Stage 2: Lazy grid candidate iteration and seeded pseudo-random sampling\n"
        "-> Stage 3: Bounded search loop execution and deterministic top candidate selection"
    )

    # Stage 1: Search Request
    fr_opt_018()

    # Stage 2: Candidate Generation
    fr_opt_019()
    fr_opt_020()

    # Stage 3: Execution & Top Selection
    fr_opt_021()
    fr_opt_022()


if __name__ == "__main__":
    main()
