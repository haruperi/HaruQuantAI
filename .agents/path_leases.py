#!/usr/bin/env python3
"""Deterministic exact-path leases for parallel Goal children."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class PathLeaseError(RuntimeError):
    """Raised when a path lease request is invalid or conflicts."""


def normalize_paths(paths: list[str]) -> tuple[str, ...]:
    """Return sorted, unique, safe repository-relative paths.

    Args:
        paths: Candidate repository-relative paths.

    Returns:
        Normalized exact paths.

    Raises:
        PathLeaseError: If a path is empty, absolute, traverses upward, or targets
            Git metadata.
    """
    result: set[str] = set()
    folded: dict[str, str] = {}
    for raw in paths:
        path = raw.strip().replace("\\", "/")
        if not path:
            raise PathLeaseError("Path leases require non-empty exact paths.")
        parts = path.split("/")
        if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
            raise PathLeaseError(f"Absolute path is not leaseable: {path}")
        if ".." in parts:
            raise PathLeaseError(f"Path traversal is not leaseable: {path}")
        if parts[0].casefold() == ".git":
            raise PathLeaseError(f"Git metadata is not leaseable: {path}")
        if any(character in path for character in "*?[]{}"):
            raise PathLeaseError(f"Glob-like path is not leaseable: {path}")
        prior = folded.get(path.casefold())
        if prior is not None and prior != path:
            raise PathLeaseError(
                f"Case-insensitive path collision: {prior!r} and {path!r}"
            )
        folded[path.casefold()] = path
        result.add(path)
    return tuple(sorted(result))


@dataclass(frozen=True, slots=True)
class LeaseRequest:
    """One child's exact draft and deferred path request."""

    task_run_id: str
    lane: str
    exclusive_paths: tuple[str, ...]
    deferred_paths: tuple[str, ...] = ()

    @classmethod
    def build(
        cls,
        *,
        task_run_id: str,
        lane: str,
        exclusive_paths: list[str],
        deferred_paths: list[str] | None = None,
    ) -> LeaseRequest:
        """Validate and construct one request."""
        exclusive = normalize_paths(exclusive_paths)
        deferred = normalize_paths(deferred_paths or [])
        overlap = set(exclusive) & set(deferred)
        if overlap:
            raise PathLeaseError(
                f"Paths cannot be both exclusive and deferred: {sorted(overlap)}"
            )
        if not task_run_id.strip() or not lane.strip():
            raise PathLeaseError("Lease ownership requires task_run_id and lane.")
        return cls(task_run_id, lane, exclusive, deferred)


def acquire_leases(
    leases: dict[str, dict[str, str]], request: LeaseRequest
) -> dict[str, dict[str, str]]:
    """Return a new lease table containing ``request``.

    Existing leases owned by the same Task are idempotent. Any other owner on an
    exact path fails closed.
    """
    updated = {path: dict(owner) for path, owner in leases.items()}
    conflicts: dict[str, dict[str, str]] = {}
    for path in request.exclusive_paths:
        for leased_path, owner in updated.items():
            overlaps = (
                path == leased_path
                or path.startswith(leased_path.rstrip("/") + "/")
                or leased_path.startswith(path.rstrip("/") + "/")
            )
            if overlaps and owner.get("task_run_id") != request.task_run_id:
                conflicts[leased_path] = owner
    if conflicts:
        detail = ", ".join(
            f"{path} ({owner.get('task_run_id', 'unknown')})"
            for path, owner in sorted(conflicts.items())
        )
        raise PathLeaseError(f"Exclusive path lease conflict: {detail}")
    for path in request.exclusive_paths:
        updated[path] = {
            "task_run_id": request.task_run_id,
            "lane": request.lane,
            "kind": "exclusive",
        }
    return updated


def release_leases(
    leases: dict[str, dict[str, str]], task_run_id: str
) -> dict[str, dict[str, str]]:
    """Return a new table without leases owned by ``task_run_id``."""
    return {
        path: dict(owner)
        for path, owner in leases.items()
        if owner.get("task_run_id") != task_run_id
    }


def request_from_state(child: dict[str, Any]) -> LeaseRequest:
    """Build a lease request from a Task run state."""
    return LeaseRequest.build(
        task_run_id=str(child["run_id"]),
        lane=str(child["lane"]),
        exclusive_paths=[str(path) for path in child.get("approved_write_paths", [])],
        deferred_paths=[
            str(path) for path in child.get("deferred_integration_paths", [])
        ],
    )
