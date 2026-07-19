"""Unit tests for safe Simulation artifact manifests."""
# ruff: noqa: INP001

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.reporting import build_artifact_manifest


def test_manifest_rejects_path_escape(tmp_path: Path) -> None:
    """Reject one artifact outside the approved root."""
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "journal.jsonl"
    outside.write_text("{}\n", encoding="utf-8")
    for name in ("result.json", "report.md"):
        (root / name).write_text("evidence", encoding="utf-8")
    with pytest.raises(SimulationError) as captured:
        build_artifact_manifest(
            root,
            (outside, root / "result.json", root / "report.md"),
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
    assert captured.value.code == "SIM_PERSISTENCE_FAILED"


def test_manifest_hashes_three_canonical_entries(tmp_path: Path) -> None:
    """Hash every non-manifest canonical artifact in stable order."""
    paths = []
    for name in ("journal.jsonl", "result.json", "report.md"):
        path = tmp_path / name
        path.write_text(name, encoding="utf-8")
        paths.append(path)
    manifest = build_artifact_manifest(
        tmp_path,
        paths,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert tuple(entry.relative_path for entry in manifest.artifacts) == (
        "journal.jsonl",
        "result.json",
        "report.md",
    )
