"""Tests for bounded-search contracts."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.search import (
    CandidateResult,
    SearchMethod,
    SearchRequest,
    SearchSummary,
)
from pydantic import ValidationError
from tests.optimization.unit.test_constraints import _space
from tests.optimization.unit.test_execution_contracts import execution_context


def search_request(**overrides) -> SearchRequest:
    """Build a valid grid search request."""
    payload = {
        "space": _space(),
        "execution_context": execution_context(),
        "method": "grid",
        "objective": "net_pnl",
        "enabled_objectives": frozenset({"net_pnl"}),
        "max_candidates": 10,
        "max_parameter_space_expansion": 20,
        "max_constraint_count": 5,
        "max_runtime_seconds": 10.0,
        "request_id": "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "workflow_id": "wf-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "correlation_id": "cor-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    }
    payload.update(overrides)
    return SearchRequest.model_validate(payload)


def test_search_request_requires_seed_for_random() -> None:
    """Random search is invalid without reproducibility evidence."""
    with pytest.raises(ValidationError, match="seed"):
        search_request(method="random", candidate_count=2)


def test_candidate_result_requires_failure_reason() -> None:
    """Failed candidates never disappear without a reason code."""
    with pytest.raises(ValidationError, match="reason"):
        CandidateResult(
            candidate_hash="a" * 64,
            executable_parameters={"period": 2},
            state="failed",
        )


def test_search_method_allows_only_grid_and_random() -> None:
    """The initial search catalog excludes speculative optimizers."""
    assert tuple(SearchMethod) == (SearchMethod.GRID, SearchMethod.RANDOM)


def test_search_summary_validates_best_candidate() -> None:
    """A best-candidate reference must identify accepted score evidence."""
    with pytest.raises(ValidationError, match="best candidate"):
        SearchSummary(
            search_id="search-one",
            request_hash="a" * 64,
            method="grid",
            objective="net_pnl",
            candidates=(),
            best_candidate_hash="b" * 64,
            runtime_ms=1.0,
        )
