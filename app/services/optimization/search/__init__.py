"""Public Optimization bounded-search feature API."""

from app.services.optimization.search.contracts import (
    CandidateResult,
    CandidateState,
    SearchMethod,
    SearchRequest,
    SearchSummary,
)
from app.services.optimization.search.grid import iter_grid_candidates
from app.services.optimization.search.random import sample_random_candidates
from app.services.optimization.search.sweep import (
    CheckpointCallback,
    run_bounded_search,
    select_top_candidates,
)

__all__ = [
    "CandidateResult",
    "CandidateState",
    "CheckpointCallback",
    "SearchMethod",
    "SearchRequest",
    "SearchSummary",
    "iter_grid_candidates",
    "run_bounded_search",
    "sample_random_candidates",
    "select_top_candidates",
]
