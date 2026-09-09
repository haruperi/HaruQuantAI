"""Tests for controller-owned close-out without a reasoning invocation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "deterministic_closeout.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("hq_deterministic_closeout", MODULE_PATH)
assert SPEC
assert SPEC.loader
closeout = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = closeout
SPEC.loader.exec_module(closeout)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def _state(repo: Path, baseline: str) -> dict[str, Any]:
    return {
        "run_id": "closeout-test",
        "task": {"task_id": "FEAT-DEMO"},
        "baseline": baseline,
        "branch": "feature/feat-demo-demo",
        "reviewed_head": baseline,
        "approved_write_paths": ["demo.txt"],
        "approved_authority_hash": "authority",
        "commit_message": "feat(test): complete FEAT-DEMO",
        "integration_validation": {"receipt_sha256": "validation"},
        "evidence_projection": {"receipt_sha256": "projection"},
    }


def test_closeout_commits_merges_and_clears_without_agent(
    repo: Path, cfg: dict[str, Any]
) -> None:
    """The controller completes exact Git mechanics without role transport."""
    baseline = _git(repo, "rev-parse", "HEAD")
    _git(repo, "switch", "-c", "feature/feat-demo-demo")
    (repo / "demo.txt").write_text("implemented\n", encoding="utf-8")
    state = _state(repo, baseline)

    result = closeout.perform_deterministic_closeout(cfg, state)

    assert _git(repo, "branch", "--show-current") == "main"
    assert len(_git(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()) == 3
    assert _git(repo, "status", "--porcelain") == ""
    assert not _git(repo, "branch", "--list", state["branch"])
    assert Path(result["receipt_path"]).is_file()
    receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["evidence_projection_receipt_sha256"] == "projection"
    assert all(path.stat().st_size == 0 for path in cfg["journals"].values())


def test_closeout_rejects_unapproved_path_before_staging(
    repo: Path, cfg: dict[str, Any]
) -> None:
    """Unexpected product bytes stop before commit or journal clearing."""
    baseline = _git(repo, "rev-parse", "HEAD")
    _git(repo, "switch", "-c", "feature/feat-demo-demo")
    (repo / "demo.txt").write_text("approved\n", encoding="utf-8")
    (repo / "other.txt").write_text("unapproved\n", encoding="utf-8")
    cfg["journals"]["reviewer"].write_text("review\n", encoding="utf-8")
    state = _state(repo, baseline)

    with pytest.raises(closeout.OrchestratorError, match="unauthorized paths"):
        closeout.perform_deterministic_closeout(cfg, state)

    assert _git(repo, "rev-parse", "HEAD") == baseline
    assert cfg["journals"]["reviewer"].read_text(encoding="utf-8") == "review\n"
