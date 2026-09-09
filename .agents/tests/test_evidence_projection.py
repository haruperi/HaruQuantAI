"""Tests for controller-owned reviewed-evidence projection."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "evidence_projection.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("hq_evidence_projection", MODULE_PATH)
assert SPEC
assert SPEC.loader
projection = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = projection
SPEC.loader.exec_module(projection)


def _git(repo: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / ".gitignore").write_text(".agents/\n", encoding="utf-8")
    seed = tmp_path / "seed.txt"
    seed.write_text("seed\n", encoding="utf-8")
    _git(tmp_path, "add", "seed.txt", ".gitignore")
    _git(tmp_path, "commit", "-m", "seed")
    runs = tmp_path / ".agents/runs/run/integration"
    runs.mkdir(parents=True)
    packet = runs.parent / "task-packet.json"
    packet.write_text(
        json.dumps({"paths": {"evidence_path": "docs/acceptance.json"}}),
        encoding="utf-8",
    )
    receipt = runs / "local-gate-receipt.json"
    receipt.write_text('{"receipt": true}\n', encoding="utf-8")
    reviewer = tmp_path / ".agents/task/reviewer.md"
    reviewer.parent.mkdir(parents=True)
    reviewer.write_text("HANDOFF : PENDING_COMMIT\n", encoding="utf-8")
    cfg: dict[str, object] = {
        "repo": tmp_path,
        "runs_dir": tmp_path / ".agents/runs",
        "logs_dir": tmp_path / ".agents/logs",
        "journals": {"reviewer": reviewer},
    }
    parent_hash = projection._sha_file(receipt)
    state: dict[str, object] = {
        "run_id": "run",
        "task": {"task_kind": "feature"},
        "task_packet_path": str(packet),
        "reviewed_candidate_hash": projection.candidate_fingerprint(tmp_path),
        "approved_authority_hash": "authority",
        "approved_write_paths": ["product.py"],
        "controller_projection_paths": ["docs/acceptance.json"],
        "integration_validation": {
            "status": "PASSED",
            "receipt_path": str(receipt),
            "receipt_sha256": parent_hash,
        },
    }
    return cfg, state


def test_projection_is_controller_scoped_and_reusable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Controller applies exact outputs and verifies the derived receipt."""
    cfg, state = _fixture(tmp_path)
    monkeypatch.setattr(projection, "verify_validation_receipt", lambda **_kwargs: {})
    monkeypatch.setattr(
        projection,
        "build_feature_projection",
        lambda **_kwargs: {"docs/acceptance.json": b'{"status":"ACCEPTED"}\n'},
    )

    result = projection.apply_reviewed_projection(cfg, state)
    state["evidence_projection"] = result

    assert result is not None
    assert (tmp_path / "docs/acceptance.json").is_file()
    assert "docs/acceptance.json" in state["approved_write_paths"]
    assert projection.verify_reviewed_projection(repo=tmp_path, state=state)


def test_projection_rejects_output_outside_controller_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A projector cannot expand its own exact output authority."""
    cfg, state = _fixture(tmp_path)
    monkeypatch.setattr(projection, "verify_validation_receipt", lambda **_kwargs: {})
    monkeypatch.setattr(
        projection,
        "build_feature_projection",
        lambda **_kwargs: {"app/unauthorized.py": b"bad\n"},
    )

    with pytest.raises(projection.EvidenceProjectionError, match="outside"):
        projection.apply_reviewed_projection(cfg, state)

    assert not (tmp_path / "app/unauthorized.py").exists()


def test_projection_skips_feature_without_prepared_packet(tmp_path: Path) -> None:
    """A broad feature label alone does not grant projection authority."""
    cfg = {"repo": tmp_path}
    state = {"task": {"task_kind": "feature"}}

    assert projection.apply_reviewed_projection(cfg, state) is None
