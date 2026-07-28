"""Workflow integration test for isolated non-canonical fast research."""
# ruff: noqa: INP001

from pathlib import Path

from app.services.simulator import run_fast_research, unwrap_simulation_response
from app.utils import logger
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)


def test_fast_research_cannot_produce_canonical_evidence(tmp_path: Path) -> None:
    """Return disclosed observations without fills, journal, or artifacts."""
    logger.info("Testing WF-SIM-007 isolated fast research")
    dataset = _dataset("req-11111111-1111-4111-8111-111111111111")
    request = _request(
        dataset,
        runtime_profile="fast_research",
        canonical=False,
        suffix="1",
    )
    dependencies = FakeDependencies(tmp_path, dataset)
    result = unwrap_simulation_response(
        run_fast_research(request, _auth(request), dependencies),
        operation="test.fast_research.run_fast_research",
    )
    assert result.canonical is False
    assert result.observations
    assert not tuple(dependencies.artifact_root.rglob("*"))
