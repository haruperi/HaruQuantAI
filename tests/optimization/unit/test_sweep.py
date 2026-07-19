"""Tests for bounded search orchestration."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.errors import OptimizationError
from app.services.optimization.search import run_bounded_search, select_top_candidates
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_search_contracts import search_request


def test_bounded_sweep_checkpoints_every_candidate() -> None:
    """Every terminal candidate advances the checkpoint callback once."""
    checkpoints = []
    summary = run_bounded_search(
        search_request(),
        FakeAdapter(),
        checkpoint=lambda index, result: checkpoints.append(
            (index, result.candidate_hash)
        ),
    )
    assert len(checkpoints) == len(summary.candidates)
    assert summary.best_candidate_hash is not None


class FailingAdapter:
    """Compatible adapter that fails every candidate deterministically."""

    contract_version = "v1"
    engine_type = "event_driven"
    engine_version = "v1"
    deterministic = True

    def execute(self, request):
        """Raise a controlled candidate execution failure."""
        del request
        raise OptimizationError("OPT_EXECUTION_FAILED", "FIXTURE_FAILURE")


def test_run_bounded_search_preserves_failed_candidates() -> None:
    """Failed executions remain explicit candidate evidence."""
    summary = run_bounded_search(search_request(), FailingAdapter())
    assert summary.best_candidate_hash is None
    assert all(item.state == "failed" for item in summary.candidates)


def test_select_top_candidates_preserves_order() -> None:
    """Top selection preserves canonical score ranking."""
    summary = run_bounded_search(search_request(), FakeAdapter())
    selected = select_top_candidates(summary, 2)
    assert len(selected) == 2
    with pytest.raises(ValueError, match="positive"):
        select_top_candidates(summary, 0)
