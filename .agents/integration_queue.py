#!/usr/bin/env python3
"""Serialized integration primitives for reviewed parallel Task drafts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast, override


class IntegrationError(RuntimeError):
    """Raised when reviewed-draft integration cannot proceed safely."""


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
        raise IntegrationError(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def _safe_component(value: str) -> str:
    component = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    if not component:
        raise IntegrationError(f"Unsafe integration identifier: {value!r}")
    return component


def changed_paths(repo: Path, baseline: str, head: str) -> set[str]:
    """Return paths changed between two commits."""
    output = _git(repo, "diff", "--name-only", f"{baseline}..{head}")
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line}


def refresh_overlap(
    repo: Path,
    *,
    draft_baseline: str,
    integration_baseline: str,
    draft_paths: set[str],
) -> set[str]:
    """Return draft paths also changed on main since draft dispatch."""
    upstream = changed_paths(repo, draft_baseline, integration_baseline)
    return upstream & {path.replace("\\", "/") for path in draft_paths}


@dataclass(frozen=True, slots=True)
class QueueItem:
    """One reviewed draft waiting for serialized integration."""

    entry: str
    task_run_id: str
    lane: str
    dependency_criticality: int = 0


def queue_key(item: QueueItem) -> tuple[int, list[tuple[int, int | str]], str]:
    """Return deterministic criticality-descending, Task-ID ordering."""
    parts: list[tuple[int, int | str]] = []
    for component in re.split(r"([0-9]+)", item.entry):
        if not component:
            continue
        parts.append((0, int(component)) if component.isdigit() else (1, component))
    return (-item.dependency_criticality, parts, item.task_run_id)


def order_queue(items: list[QueueItem]) -> list[QueueItem]:
    """Return a deterministic integration queue."""
    return sorted(items, key=queue_key)


class IntegrationLock(AbstractContextManager["IntegrationLock"]):
    """Exclusive, non-stealing lock for one Goal integration transaction."""

    def __init__(self, path: Path, owner: str) -> None:
        self._path = path
        self._owner = owner
        self._held = False

    @override
    def __enter__(self) -> IntegrationLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "owner": self._owner,
                "pid": os.getpid(),
                "created_at": dt.datetime.now(tz=dt.UTC).isoformat(),
            },
            sort_keys=True,
        )
        try:
            descriptor = os.open(
                self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
            )
        except FileExistsError as exc:
            raise IntegrationError(
                f"Integration lock is already held: {self._path}"
            ) from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
        self._held = True
        return self

    @override
    def __exit__(self, *_args: object) -> None:
        if self._held:
            try:
                payload = json.loads(self._path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise IntegrationError(
                    "Integration lock identity became unreadable."
                ) from exc
            if payload.get("owner") != self._owner:
                raise IntegrationError("Integration lock ownership changed.")
            self._path.unlink()
            self._held = False


def archive_draft(
    primary_repo: Path,
    lane_repo: Path,
    *,
    goal_run_id: str,
    task_run_id: str,
    approved_paths: list[str],
    coordination_paths: list[str],
) -> dict[str, Any]:
    """Archive exact reviewed draft bytes and return immutable evidence."""
    archive_dir = (
        primary_repo
        / ".agents"
        / "goals"
        / _safe_component(goal_run_id)
        / "integration"
        / _safe_component(task_run_id)
    )
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / "reviewed-draft.zip"
    if archive_path.exists():
        raise IntegrationError(f"Draft archive already exists: {archive_path}")
    selected = sorted(set(approved_paths) | set(coordination_paths))
    manifest: dict[str, Any] = {
        "task_run_id": task_run_id,
        "head": _git(lane_repo, "rev-parse", "HEAD"),
        "branch": _git(lane_repo, "branch", "--show-current"),
        "paths": {},
    }
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for relative in selected:
            path = lane_repo / relative
            if path.is_file():
                data = path.read_bytes()
                bundle.writestr(f"files/{relative}", data)
                manifest["paths"][relative] = {
                    "kind": "file",
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            elif path.exists():
                raise IntegrationError(f"Draft archive path is not a file: {relative}")
            else:
                manifest["paths"][relative] = {"kind": "absent"}
        patch = _git(lane_repo, "diff", "--binary", "HEAD", "--", *approved_paths)
        bundle.writestr("draft.patch", patch.encode("utf-8"))
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        bundle.writestr("manifest.json", manifest_bytes)
    archive_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    evidence = {
        "archive": str(archive_path.relative_to(primary_repo)).replace("\\", "/"),
        "archive_sha256": archive_hash,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        **manifest,
    }
    (archive_dir / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return evidence


def refresh_archived_draft(
    lane_repo: Path,
    *,
    archive_path: Path,
    archive_sha256: str,
    integration_baseline: str,
    refreshed_branch: str,
    replay_implementation: bool = True,
) -> dict[str, Any]:
    """Replay one verified archive onto a fresh branch above current main.

    The archive is created by :func:`archive_draft`. This operation cleans only
    the archive's explicit paths, preserves the old branch ref, and performs no
    rebase, cherry-pick, merge, or conflict resolution.
    """
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != archive_sha256:
        raise IntegrationError("Reviewed-draft archive hash mismatch.")
    with zipfile.ZipFile(archive_path, "r") as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        paths = manifest.get("paths")
        if not isinstance(paths, dict):
            raise IntegrationError("Reviewed-draft archive manifest is invalid.")
        selected = sorted(str(path) for path in paths)
        unexpected = set(_git(lane_repo, "status", "--porcelain").splitlines())
        if not selected and unexpected:
            raise IntegrationError("Draft has changes but no archived paths.")
        for relative in selected:
            target = (lane_repo / relative).resolve()
            try:
                target.relative_to(lane_repo.resolve())
            except ValueError as exc:
                raise IntegrationError("Archive path escaped lane worktree.") from exc
            tracked = (
                subprocess.run(
                    [
                        shutil.which("git") or "git",
                        "ls-files",
                        "--error-unmatch",
                        "--",
                        relative,
                    ],
                    cwd=lane_repo,
                    capture_output=True,
                    check=False,
                ).returncode
                == 0
            )
            if tracked:
                _git(
                    lane_repo,
                    "restore",
                    "--source=HEAD",
                    "--staged",
                    "--worktree",
                    "--",
                    relative,
                )
            elif target.is_file():
                target.unlink()
            elif target.exists():
                raise IntegrationError(f"Cannot clean non-file draft path: {relative}")
        if _git(lane_repo, "status", "--porcelain"):
            raise IntegrationError(
                "Lane contains mutations outside the verified archive; refresh stopped."
            )
        _git(lane_repo, "switch", "--detach", integration_baseline)
        _git(lane_repo, "switch", "-c", refreshed_branch, integration_baseline)
        coordination_prefix = ".agents/task/"
        for relative, facts in cast("dict[str, dict[str, str]]", paths).items():
            if not replay_implementation and not relative.startswith(
                coordination_prefix
            ):
                continue
            target = (lane_repo / relative).resolve()
            if facts.get("kind") == "absent":
                if target.is_file():
                    target.unlink()
                continue
            member = f"files/{relative}"
            data = bundle.read(member)
            if hashlib.sha256(data).hexdigest() != facts.get("sha256"):
                raise IntegrationError(f"Archived file hash mismatch: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return {
        "integration_baseline": integration_baseline,
        "refreshed_branch": refreshed_branch,
        "implementation_replayed": replay_implementation,
        "worktree_head": _git(lane_repo, "rev-parse", "HEAD"),
        "worktree_status_sha256": hashlib.sha256(
            _git(lane_repo, "status", "--porcelain=v1", "-z").encode("utf-8")
        ).hexdigest(),
    }
