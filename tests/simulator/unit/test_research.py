"""Unit tests for the isolated fast-research path."""
# ruff: noqa: INP001

from pathlib import Path

from app.services.simulator.run import run_fast_research
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)


def test_fast_research_cannot_claim_canonical(tmp_path: Path) -> None:
    """Return the distinct non-canonical result without official evidence."""
    dataset = _dataset("req-88888888-8888-4888-8888-888888888888")
    request = _request(
        dataset,
        runtime_profile="fast_research",
        canonical=False,
        suffix="8",
    )
    result = run_fast_research(
        request,
        _auth(request),
        FakeDependencies(tmp_path, dataset),  # type: ignore[arg-type]
    )
    assert result.canonical is False
    assert "fills" not in type(result).model_fields
    assert "artifact_manifest_ref" not in type(result).model_fields
