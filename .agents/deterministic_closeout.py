#!/usr/bin/env python3
"""Deterministic Task commit, merge, cleanup and final receipt creation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_protocol import OrchestratorError, _git, _git_ok, _sha_file

COORDINATION_PATHS = frozenset(
    {
        ".agents/task/planner.md",
        ".agents/task/executor.md",
        ".agents/task/reviewer.md",
        ".agents/task/next-agent.md",
    }
)


def _changed_paths(repo: Path) -> set[str]:
    """Return tracked and untracked changed paths without mutating the tree."""
    paths: set[str] = set()
    for arguments in (
        ("diff", "--name-only", "HEAD"),
        ("diff", "--cached", "--name-only", "HEAD"),
        ("ls-files", "--others", "--exclude-standard"),
    ):
        paths.update(
            line.strip().replace("\\", "/")
            for line in _git_ok(repo, *arguments).splitlines()
            if line.strip()
        )
    return paths


def _run_required(repo: Path, *arguments: str) -> str:
    result = _git(repo, *arguments)
    if result.returncode != 0:
        raise OrchestratorError(
            f"git {' '.join(arguments)} failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def _write_final_receipt(
    path: Path,
    *,
    state: dict[str, Any],
    task_commit: str,
    merge_commit: str,
    task_tree: str,
) -> str:
    payload = {
        "schema_version": 1,
        "receipt_kind": "deterministic-task-closeout",
        "run_id": state["run_id"],
        "task_id": state["task"]["task_id"],
        "baseline_commit": state.get("integration_baseline") or state["baseline"],
        "task_commit": task_commit,
        "merge_commit": merge_commit,
        "reviewed_tree": task_tree,
        "approved_authority_sha256": state.get("approved_authority_hash"),
        "validation_receipt_sha256": state.get("integration_validation", {}).get(
            "receipt_sha256"
        ),
        "evidence_projection_receipt_sha256": (
            state.get("evidence_projection", {}).get("receipt_sha256")
            if isinstance(state.get("evidence_projection"), dict)
            else None
        ),
        "approved_write_paths": state.get("approved_write_paths", []),
        "non_self_referential": True,
    }
    raw = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw, encoding="utf-8", newline="\n")
    return _sha_file(path)


def perform_deterministic_closeout(
    cfg: dict[str, Any], state: dict[str, Any]
) -> dict[str, str]:
    """Commit and merge the exact reviewed Task without an LLM invocation.

    Args:
        cfg: Assembled workflow configuration.
        state: Frozen, reviewed and commit-authorized Task state.

    Returns:
        Final Git identities and close-out receipt identity.

    Raises:
        OrchestratorError: If any path, Git or lineage precondition differs.
    """
    repo = Path(cfg["repo"])
    primary = Path(state.get("primary_repo_path", repo))
    branch = str(state["branch"])
    baseline = str(state.get("integration_baseline") or state["baseline"])
    approved = {str(path).replace("\\", "/") for path in state["approved_write_paths"]}
    if _git_ok(repo, "branch", "--show-current") != branch:
        raise OrchestratorError("Deterministic close-out is not on the Task branch.")
    if _git_ok(repo, "rev-parse", "HEAD") != state["reviewed_head"]:
        raise OrchestratorError("Task HEAD changed before deterministic close-out.")
    unexpected = _changed_paths(repo) - approved - COORDINATION_PATHS
    if unexpected:
        raise OrchestratorError(
            f"Deterministic close-out found unauthorized paths: {sorted(unexpected)}"
        )
    if approved:
        _run_required(repo, "add", "--all", "--", *sorted(approved))
    staged = {
        line.strip().replace("\\", "/")
        for line in _git_ok(repo, "diff", "--cached", "--name-only").splitlines()
        if line.strip()
    }
    if not staged:
        raise OrchestratorError("Deterministic close-out has no implementation delta.")
    if not staged.issubset(approved):
        raise OrchestratorError("Deterministic close-out staged unauthorized paths.")

    commit_message = str(state.get("commit_message", "")).strip()
    if not commit_message:
        raise OrchestratorError("Deterministic close-out has no commit message.")
    _run_required(repo, "commit", "-m", commit_message)
    task_commit = _git_ok(repo, "rev-parse", "HEAD")
    if _git_ok(repo, "rev-parse", f"{task_commit}^") != baseline:
        raise OrchestratorError("Task commit is not directly above its baseline.")
    task_tree = _git_ok(repo, "rev-parse", f"{task_commit}^{{tree}}")

    for path in [*cfg["journals"].values(), cfg["next_agent"]]:
        Path(path).write_bytes(b"")
    if _git_ok(repo, "status", "--porcelain"):
        raise OrchestratorError("Task branch is dirty after coordination cleanup.")

    if repo.resolve() == primary.resolve():
        _run_required(primary, "switch", cfg["main_branch"])
    elif _git_ok(primary, "branch", "--show-current") != cfg["main_branch"]:
        raise OrchestratorError("Primary repository is not on accepted main.")
    if _git_ok(primary, "rev-parse", cfg["main_branch"]) != baseline:
        raise OrchestratorError("Accepted main moved before deterministic merge.")
    _run_required(
        primary,
        "merge",
        "--no-ff",
        branch,
        "-m",
        f"merge({state['task']['task_id']}): accept reviewed task",
    )
    merge_commit = _git_ok(primary, "rev-parse", "HEAD")
    if repo.resolve() != primary.resolve():
        _run_required(repo, "switch", "--detach", merge_commit)
    _run_required(primary, "branch", "-d", branch)

    receipt_path = (
        Path(cfg["logs_dir"]) / state["run_id"] / "closeout" / "final-receipt.json"
    )
    receipt_sha = _write_final_receipt(
        receipt_path,
        state=state,
        task_commit=task_commit,
        merge_commit=merge_commit,
        task_tree=task_tree,
    )
    return {
        "task_commit": task_commit,
        "merge_commit": merge_commit,
        "receipt_path": str(receipt_path),
        "receipt_sha256": receipt_sha,
    }
