"""Tests for traversal-safe Optimization artifact paths."""

# ruff: noqa: INP001

from pathlib import Path

import pytest
from app.services.optimization.errors import OptimizationError
from app.services.optimization.state import build_optimization_artifact_path


def test_artifact_path_cannot_escape_root(tmp_path: Path) -> None:
    """Validated identifiers keep result locations beneath the approved root."""
    path = build_optimization_artifact_path(
        artifact_root=tmp_path,
        kind="results",
        search_id="search-one",
        reproducibility_hash="a" * 64,
    )
    assert path.is_relative_to(tmp_path.resolve())
    with pytest.raises(OptimizationError):
        build_optimization_artifact_path(
            artifact_root=tmp_path,
            kind="results",
            search_id="../escape",
            reproducibility_hash="a" * 64,
        )
