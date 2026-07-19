"""Integration test for the official Optimization boundary."""

# ruff: noqa: INP001

from app.services.optimization.public_api import (
    OFFICIAL_OPTIMIZATION_TOOLS,
    compare_optimization_runs,
    run_parameter_sweep,
)
from tests.optimization.unit.test_search_contracts import search_request
from tests.optimization.unit.test_sweep import FakeAdapter


def test_public_boundary_runs_and_compares_advisory_results() -> None:
    """Official operations orchestrate existing capabilities end to end."""
    first = run_parameter_sweep(search_request(), FakeAdapter())
    second = first.model_copy(update={"search_id": "search-two"})
    comparison = compare_optimization_runs((first, second))
    assert comparison.search_ids == (first.search_id, second.search_id)
    assert "run_parameter_sweep" in OFFICIAL_OPTIMIZATION_TOOLS
