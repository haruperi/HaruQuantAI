"""Close-out evidence regression tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def test_closeout_archive_preserves_active_evidence(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    cfg["journals"]["planner"].write_text("plan", encoding="utf-8")
    cfg["next_agent"].write_text("prompt", encoding="utf-8")
    state["approved_write_paths"] = ["demo.txt"]
    archive: Path = orc._archive_closeout_evidence(cfg, state)
    assert (archive / "planner.md").read_text(encoding="utf-8") == "plan"
    assert (archive / "next-agent.md").read_text(encoding="utf-8") == "prompt"
    assert cfg["journals"]["planner"].read_text(encoding="utf-8") == "plan"


def _closeout_state(repo: Path, baseline: str) -> dict[str, Any]:
    return {
        "baseline": baseline,
        "branch": "task/already-deleted",
        "approved_write_paths": ["demo.txt"],
    }


def test_closeout_rejects_unexpected_committed_path(
    orc: ModuleType, cfg: dict[str, Any], repo: Path
) -> None:
    baseline = _git(repo, "rev-parse", "HEAD")
    (repo / "demo.txt").write_text("approved\n", encoding="utf-8")
    (repo / "unexpected.txt").write_text("bad\n", encoding="utf-8")
    _git(repo, "add", "demo.txt", "unexpected.txt")
    _git(repo, "commit", "--no-verify", "-m", "one task commit")
    with pytest.raises(orc.OrchestratorError, match="unexpected paths"):
        orc._verify_closeout_lineage(cfg, _closeout_state(repo, baseline))


def test_closeout_rejects_multiple_commits(
    orc: ModuleType, cfg: dict[str, Any], repo: Path
) -> None:
    baseline = _git(repo, "rev-parse", "HEAD")
    (repo / "demo.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "demo.txt")
    _git(repo, "commit", "--no-verify", "-m", "first")
    (repo / "demo.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "add", "demo.txt")
    _git(repo, "commit", "--no-verify", "-m", "second")
    with pytest.raises(orc.OrchestratorError, match="direct child of baseline"):
        orc._verify_closeout_lineage(cfg, _closeout_state(repo, baseline))


def test_closeout_accepts_exact_lineage(
    orc: ModuleType, cfg: dict[str, Any], repo: Path
) -> None:
    baseline = _git(repo, "rev-parse", "HEAD")
    (repo / "demo.txt").write_text("approved\n", encoding="utf-8")
    _git(repo, "add", "demo.txt")
    _git(repo, "commit", "--no-verify", "-m", "one task commit")

    orc._verify_closeout_lineage(cfg, _closeout_state(repo, baseline))


def test_failed_closeout_before_commit_preserves_journals(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for journal in cfg["journals"].values():
        journal.write_text("evidence\n", encoding="utf-8")
    cfg["next_agent"].write_text("closeout prompt\n", encoding="utf-8")

    def fail_gate(*_args: Any, **_kwargs: Any) -> None:
        raise orc.OrchestratorError("simulated final gate failure")

    monkeypatch.setitem(orc._handle_closeout.__globals__, "_invoke_pending", fail_gate)
    with pytest.raises(orc.OrchestratorError, match="final gate failure"):
        orc._handle_closeout(cfg, state)
    for journal in cfg["journals"].values():
        assert journal.read_text(encoding="utf-8") == "evidence\n"
    assert cfg["next_agent"].read_text(encoding="utf-8") == "closeout prompt\n"
