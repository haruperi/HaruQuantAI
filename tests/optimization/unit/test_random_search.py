"""Tests for seeded random candidate sampling."""

# ruff: noqa: INP001

from app.services.optimization.search import sample_random_candidates
from tests.optimization.unit.test_constraints import _space


def test_sample_random_candidates_is_seeded() -> None:
    """Identical seed and space produce identical unique samples."""
    arguments = {
        "candidate_count": 2,
        "seed": 17,
        "max_expansion": 10,
        "max_constraints": 5,
    }
    first = sample_random_candidates(_space(), **arguments)
    second = sample_random_candidates(_space(), **arguments)
    assert first == second
    assert len({tuple(item.items()) for item in first}) == 2
