"""Integration test for the official Optimization boundary."""

# ruff: noqa: INP001
import asyncio

from app.services.optimization import (
    compare_optimization_runs,
    get_official_optimization_tools,
    run_parameter_sweep,
)
from tests.optimization.unit.test_search_contracts import search_request
from tests.optimization.unit.test_sweep import FakeAdapter


def test_public_boundary_runs_and_compares_advisory_results() -> None:
    """Official operations orchestrate existing capabilities end to end."""
    first_response = asyncio.run(run_parameter_sweep(search_request(), FakeAdapter()))
    assert first_response.data is not None
    first = first_response.data
    second = first.model_copy(update={"search_id": "search-two"})
    comparison_response = compare_optimization_runs((first, second))
    assert comparison_response.data is not None
    comparison = comparison_response.data
    assert comparison.search_ids == (first.search_id, second.search_id)
    assert "run_parameter_sweep" in get_official_optimization_tools()
