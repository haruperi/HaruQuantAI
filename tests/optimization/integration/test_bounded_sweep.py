"""Integration evidence for bounded Simulation-adapter search."""

# ruff: noqa: INP001

from app.services.optimization.search import run_bounded_search
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_search_contracts import search_request


def test_bounded_sweep_uses_simulation_adapter() -> None:
    """Search packages every candidate through the execution port."""
    summary = run_bounded_search(search_request(), FakeAdapter())
    assert summary.candidates
    assert all(item.evidence for item in summary.candidates)
