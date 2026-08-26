"""Role mutation-authority regression tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _invoke_with_fake_agent(
    orc: ModuleType,
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    role: str,
    action: Any,
    *,
    approved: set[str] | None = None,
) -> None:
    """Invoke one role through the real snapshot/authority boundary."""
    invoke_globals = orc._invoke_pending.__globals__
    monkeypatch.setitem(
        invoke_globals, "_ensure_pending_artifact_unchanged", lambda *_: None
    )
    artifact = SimpleNamespace(metadata={"target_role": role}, raw="prompt")
    monkeypatch.setitem(invoke_globals, "parse_next_agent", lambda *_: artifact)

    def fake_run_agent(*_args: Any, **_kwargs: Any) -> tuple[str, Path]:
        action()
        return "", repo / ".agents/logs/fake.log"

    monkeypatch.setitem(invoke_globals, "run_agent", fake_run_agent)
    state: dict[str, Any] = {
        "branch": "main",
        "run_id": "authority",
        "iteration": 1,
        "approved_write_paths": sorted(approved or set()),
    }
    cfg = {
        "repo": repo,
        "next_agent": repo / ".agents/task/next-agent.md",
    }
    orc._invoke_pending(cfg, state, role)


def test_snapshot_detects_change_to_already_dirty_file(
    orc: ModuleType, repo: Path
) -> None:
    path = repo / "dirty.txt"
    path.write_text("first", encoding="utf-8")
    before = orc.capture_repository_snapshot(repo)
    path.write_text("second", encoding="utf-8")
    delta = orc.compute_snapshot_delta(before, orc.capture_repository_snapshot(repo))
    assert delta["modified"] == {"dirty.txt"}


def test_executor_rejects_unapproved_path(orc: ModuleType) -> None:
    delta = {"created": {"surprise.py"}, "modified": set(), "deleted": set()}
    with pytest.raises(orc.OrchestratorError, match="unauthorized"):
        orc.validate_role_mutations(
            "EXECUTOR", delta, approved_write_paths={"approved.py"}
        )


@pytest.mark.parametrize(
    "path", ["../escape", "/absolute", "C:/absolute", ".git/config"]
)
def test_path_authority_rejects_unsafe_paths(orc: ModuleType, path: str) -> None:
    with pytest.raises(orc.OrchestratorError):
        orc._normalize_path_list([path])


def test_planner_unauthorized_write_fails_integration(
    orc: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mutate() -> None:
        path = repo / "app/unauthorized.py"
        path.parent.mkdir()
        path.write_text("bad\n", encoding="utf-8")

    with pytest.raises(orc.OrchestratorError, match="unauthorized paths"):
        _invoke_with_fake_agent(orc, repo, monkeypatch, "PLANNER", mutate)


def test_executor_unauthorized_write_fails_integration(
    orc: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mutate() -> None:
        (repo / "demo.txt").write_text("approved\n", encoding="utf-8")
        (repo / "surprise.txt").write_text("bad\n", encoding="utf-8")

    with pytest.raises(orc.OrchestratorError, match="unauthorized paths"):
        _invoke_with_fake_agent(
            orc, repo, monkeypatch, "EXECUTOR", mutate, approved={"demo.txt"}
        )


def test_reviewer_implementation_mutation_fails_integration(
    orc: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (repo / "demo.txt").write_text("before\n", encoding="utf-8")

    def mutate() -> None:
        (repo / "demo.txt").write_text("reviewer changed it\n", encoding="utf-8")

    with pytest.raises(orc.OrchestratorError, match="unauthorized paths"):
        _invoke_with_fake_agent(orc, repo, monkeypatch, "REVIEWER", mutate)


def test_clean_role_commit_is_rejected(
    orc: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def commit() -> None:
        journal = repo / ".agents/task/planner.md"
        journal.write_text("plan\n", encoding="utf-8")
        _git(repo, "add", ".agents/task/planner.md")
        _git(repo, "commit", "--no-verify", "-m", "forbidden role commit")

    with pytest.raises(orc.OrchestratorError, match="Role made commits"):
        _invoke_with_fake_agent(orc, repo, monkeypatch, "PLANNER", commit)
