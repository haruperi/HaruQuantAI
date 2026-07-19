"""Runnable usage examples for Optimization search."""

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


def test_usage_contracts_search_request() -> None:
    """Construct a complete bounded request."""
    assert search_request().max_candidates == 10


def test_usage_contracts_search_method() -> None:
    """Select one approved initial search method."""
    assert SearchMethod.GRID.value == "grid"


def test_usage_contracts_candidate_result() -> None:
    """Construct explicit rejected-candidate evidence."""
    result = CandidateResult(
        candidate_hash="a" * 64,
        executable_parameters={"period": 2},
        state="rejected",
        reason_code="CONSTRAINT_REJECTED",
    )
    assert result.state == "rejected"


def test_usage_contracts_search_summary() -> None:
    """Consume completed bounded-search evidence."""
    assert run_bounded_search(search_request(), FakeAdapter()).search_id.startswith(
        "search-"
    )


def test_usage_grid_iter_grid_candidates() -> None:
    """Generate a bounded deterministic grid."""
    assert tuple(
        iter_grid_candidates(
            _space(), max_candidates=10, max_expansion=10, max_constraints=5
        )
    )


def test_usage_random_sample_random_candidates() -> None:
    """Sample unique candidates with an explicit seed."""
    assert (
        len(
            sample_random_candidates(
                _space(),
                candidate_count=2,
                seed=3,
                max_expansion=10,
                max_constraints=5,
            )
        )
        == 2
    )


def test_usage_sweep_run_bounded_search() -> None:
    """Execute one complete bounded sweep."""
    assert run_bounded_search(search_request(), FakeAdapter()).best_candidate_hash


def test_usage_sweep_select_top_candidates() -> None:
    """Select a bounded prefix of canonically ranked candidates."""
    summary = run_bounded_search(search_request(), FakeAdapter())
    assert len(select_top_candidates(summary, 1)) == 1
