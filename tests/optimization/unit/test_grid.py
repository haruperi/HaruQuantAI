"""Tests for bounded grid generation."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.search import iter_grid_candidates
from tests.optimization.unit.test_constraints import _space


def test_iter_grid_candidates_is_lazy_and_bounded() -> None:
    """Grid candidates retain deterministic product order."""
    candidates = tuple(
        iter_grid_candidates(
            _space(), max_candidates=10, max_expansion=10, max_constraints=5
        )
    )
    assert candidates[0] == {"enabled": False}
    assert candidates[-1] == {"enabled": True, "period": 3}


def test_grid_generator_fails_before_returning_partial_results() -> None:
    """A valid-candidate cap breach raises before callers receive a tuple."""
    with pytest.raises(ValueError, match="configured cap"):
        tuple(
            iter_grid_candidates(
                _space(), max_candidates=2, max_expansion=10, max_constraints=5
            )
        )
