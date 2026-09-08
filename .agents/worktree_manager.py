#!/usr/bin/env python3
"""Lifecycle-safe Git worktree management for parallel Goal lanes."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

LANE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class WorktreeError(RuntimeError):
    """Raised when a lane worktree operation cannot be proven safe."""


@dataclass(frozen=True, slots=True)
class WorktreeRecord:
    """Persisted identity of one controller-owned lane worktree."""

    lane: str
    path: str
    head: str
    branch: str | None

    def to_dict(self) -> dict[str, str | None]:
        """Return a JSON-serializable record."""
        return asdict(self)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        [shutil.which("git") or "git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise WorktreeError(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def validate_lanes(lanes: list[str], *, maximum: int = 3) -> tuple[str, ...]:
    """Validate one-to-three unique filesystem-safe lane names."""
    if not lanes or len(lanes) > maximum:
        raise WorktreeError(f"Expected between one and {maximum} lanes.")
    normalized = tuple(lane.strip().lower() for lane in lanes)
    if len(set(normalized)) != len(normalized):
        raise WorktreeError("Lane names must be unique.")
    invalid = [lane for lane in normalized if not LANE_RE.fullmatch(lane)]
    if invalid:
        raise WorktreeError(f"Unsafe lane names: {invalid}")
    return normalized


def worktree_root(repo: Path, goal_run_id: str) -> Path:
    """Return the validated controller-owned root for one Goal."""
    if not RUN_RE.fullmatch(goal_run_id):
        raise WorktreeError(f"Unsafe Goal run id: {goal_run_id!r}")
    root = (repo.resolve() / ".agents" / "worktrees" / goal_run_id).resolve()
    allowed = (repo.resolve() / ".agents" / "worktrees").resolve()
    if root.parent != allowed:
        raise WorktreeError("Worktree root escaped the controller-owned directory.")
    return root


def inspect_worktree(path: Path, lane: str) -> WorktreeRecord:
    """Inspect one existing worktree without changing it."""
    if not path.exists():
        raise WorktreeError(f"Lane worktree does not exist: {path}")
    head = _git(path, "rev-parse", "HEAD")
    branch = _git(path, "branch", "--show-current") or None
    return WorktreeRecord(lane=lane, path=str(path), head=head, branch=branch)


def create_lane_worktrees(
    repo: Path,
    *,
    goal_run_id: str,
    lanes: list[str],
    baseline: str,
) -> dict[str, WorktreeRecord]:
    """Create clean detached worktrees for all lanes or fail before partial reuse.

    Newly created worktrees are removed on a creation failure only when Git proves
    they are clean. Pre-existing paths always fail closed.
    """
    normalized = validate_lanes(lanes)
    root = worktree_root(repo, goal_run_id)
    targets = {lane: root / lane for lane in normalized}
    existing = [str(path) for path in targets.values() if path.exists()]
    if existing:
        raise WorktreeError(f"Lane worktree paths already exist: {existing}")
    _git(repo, "cat-file", "-e", f"{baseline}^{{commit}}")
    root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    try:
        for path in targets.values():
            _git(repo, "worktree", "add", "--detach", str(path), baseline)
            created.append(path)
        return {lane: inspect_worktree(path, lane) for lane, path in targets.items()}
    except WorktreeError:
        for path in reversed(created):
            if _git(path, "status", "--porcelain"):
                continue
            _git(repo, "worktree", "remove", str(path))
        raise


def prepare_task_branch(
    path: Path, *, branch: str, baseline: str, main_branch: str = "main"
) -> WorktreeRecord:
    """Create and check out one Task branch in a clean detached lane."""
    if _git(path, "status", "--porcelain"):
        raise WorktreeError(f"Lane worktree is dirty: {path}")
    current = _git(path, "branch", "--show-current")
    if current:
        raise WorktreeError(
            f"Lane must be detached before assignment; current branch is {current!r}."
        )
    if _git(path, "rev-parse", "HEAD") != baseline:
        raise WorktreeError("Lane HEAD does not match the accepted dispatch baseline.")
    if branch == main_branch:
        raise WorktreeError("A lane Task branch cannot be the main branch.")
    _git(path, "check-ref-format", "--branch", branch)
    exists = subprocess.run(
        [
            shutil.which("git") or "git",
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/heads/{branch}",
        ],
        cwd=path,
        check=False,
    )
    if exists.returncode == 0:
        raise WorktreeError(f"Task branch already exists: {branch}")
    _git(path, "switch", "-c", branch, baseline)
    return inspect_worktree(path, path.name)


def detach_accepted_lane(path: Path, accepted_head: str) -> WorktreeRecord:
    """Return a clean accepted lane to detached reusable state."""
    if _git(path, "status", "--porcelain"):
        raise WorktreeError("Cannot detach a dirty lane worktree.")
    _git(path, "switch", "--detach", accepted_head)
    return inspect_worktree(path, path.name)


def remove_clean_lane_worktree(repo: Path, path: Path, goal_run_id: str) -> None:
    """Remove exactly one clean controller-owned lane worktree."""
    root = worktree_root(repo, goal_run_id)
    resolved = path.resolve()
    if resolved.parent != root:
        raise WorktreeError("Refusing to remove a non-lane worktree path.")
    if _git(resolved, "status", "--porcelain"):
        raise WorktreeError("Refusing to remove a dirty lane worktree.")
    _git(repo, "worktree", "remove", str(resolved))
