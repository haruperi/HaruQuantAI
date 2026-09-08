#!/usr/bin/env python3
"""Opt-in three-lane Goal scheduling above the sequential Task engine."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

from integration_queue import QueueItem, order_queue
from path_leases import LeaseRequest, PathLeaseError, acquire_leases, release_leases
from worktree_manager import validate_lanes

PARALLEL_STATE_SCHEMA_VERSION = 2
DEFAULT_LANES = ("codex", "gemini", "zcode")


class ParallelGoalError(RuntimeError):
    """Raised when parallel Goal state or scheduling is invalid."""


def load_schedule(path: Path) -> tuple[dict[str, set[str]], str]:
    """Load, validate, and hash the canonical Task predecessor schedule."""
    try:
        data = path.read_bytes()
        payload = json.loads(data)
    except (OSError, json.JSONDecodeError) as exc:
        raise ParallelGoalError(f"Invalid dependency schedule {path}: {exc}") from exc
    if payload.get("dag_properties", {}).get("is_acyclic") is not True:
        raise ParallelGoalError("Dependency schedule must declare an acyclic graph.")
    phases = payload.get("phases")
    constraints = payload.get("schedule_constraints")
    if not isinstance(phases, list) or not isinstance(constraints, list):
        raise ParallelGoalError("Dependency schedule is missing phases or constraints.")
    nodes = {
        str(task)
        for phase in phases
        if isinstance(phase, dict)
        for task in cast("list[Any]", phase.get("tasks", []))
    }
    predecessors: dict[str, set[str]] = {node: set() for node in nodes}
    seen: set[tuple[str, str]] = set()
    for raw in constraints:
        if not isinstance(raw, dict):
            raise ParallelGoalError("Schedule constraints must be objects.")
        task = str(raw.get("task", ""))
        predecessor = str(raw.get("predecessor", ""))
        if task not in nodes or predecessor not in nodes:
            raise ParallelGoalError(
                f"Schedule constraint references an unknown Task: {raw}"
            )
        edge = (task, predecessor)
        if edge in seen:
            raise ParallelGoalError(f"Duplicate schedule constraint: {edge}")
        seen.add(edge)
        predecessors[task].add(predecessor)
    return predecessors, hashlib.sha256(data).hexdigest()


def ready_entries(
    *,
    selected: list[str],
    completed: set[str],
    active: set[str],
    predecessors: dict[str, set[str]],
) -> list[str]:
    """Return selected, incomplete, inactive entries whose predecessors are done."""
    unknown = sorted(set(selected) - set(predecessors))
    if unknown:
        raise ParallelGoalError(f"Selected Tasks absent from schedule: {unknown}")
    return [
        entry
        for entry in selected
        if entry not in completed
        and entry not in active
        and predecessors[entry].issubset(completed)
    ]


def create_parallel_state(
    base_state: dict[str, Any],
    *,
    lanes: list[str],
    schedule_path: Path,
) -> dict[str, Any]:
    """Upgrade a newly created Goal state to opt-in parallel state."""
    normalized = validate_lanes(lanes)
    if len(normalized) != 3:
        raise ParallelGoalError("Parallel Goals require exactly three lanes.")
    _predecessors, schedule_hash = load_schedule(schedule_path)
    state = dict(base_state)
    state.update(
        {
            "goal_state_schema_version": PARALLEL_STATE_SCHEMA_VERSION,
            "parallelism": 3,
            "lane_names": list(normalized),
            "dependency_schedule": str(schedule_path),
            "dependency_schedule_sha256": schedule_hash,
            "active_children": {},
            "integration_queue": [],
            "integration_owner": None,
            "path_leases": {},
            "worktrees": {},
            "migration_ledger": [],
        }
    )
    state.pop("active_child", None)
    return state


def require_lane(state: dict[str, Any], lane: str | None) -> str:
    """Return one valid lane, rejecting ambiguous commands."""
    if lane is None:
        raise ParallelGoalError("Parallel Goal operation requires --lane.")
    normalized = lane.strip().lower()
    lanes = [str(item) for item in state.get("lane_names", [])]
    if normalized not in lanes:
        raise ParallelGoalError(f"Unknown lane {lane!r}; expected one of {lanes}.")
    return normalized


def acquire_child_paths(
    state: dict[str, Any],
    *,
    task_run_id: str,
    lane: str,
    exclusive_paths: list[str],
    deferred_paths: list[str],
) -> None:
    """Acquire one child's leases and persist its deferred path declaration."""
    request = LeaseRequest.build(
        task_run_id=task_run_id,
        lane=require_lane(state, lane),
        exclusive_paths=exclusive_paths,
        deferred_paths=deferred_paths,
    )
    try:
        state["path_leases"] = acquire_leases(
            cast("dict[str, dict[str, str]]", state.get("path_leases", {})), request
        )
    except PathLeaseError as exc:
        raise ParallelGoalError(str(exc)) from exc
    active = cast("dict[str, dict[str, Any]]", state.get("active_children", {}))
    child = active.get(lane)
    if child is None or str(child.get("run_id")) != task_run_id:
        raise ParallelGoalError("Lease owner does not match the active lane child.")
    child["exclusive_paths"] = list(request.exclusive_paths)
    child["deferred_integration_paths"] = list(request.deferred_paths)


def enqueue_reviewed_draft(
    state: dict[str, Any], *, lane: str, dependency_criticality: int = 0
) -> None:
    """Place one reviewed draft into the deterministic integration queue."""
    lane = require_lane(state, lane)
    active = cast("dict[str, dict[str, Any]]", state.get("active_children", {}))
    child = active.get(lane)
    if child is None:
        raise ParallelGoalError(f"Lane {lane!r} has no active child.")
    if child.get("phase") != "DRAFT_REVIEWED":
        raise ParallelGoalError("Only a DRAFT_REVIEWED child can enter integration.")
    item = QueueItem(
        entry=str(child["entry"]),
        task_run_id=str(child["run_id"]),
        lane=lane,
        dependency_criticality=dependency_criticality,
    )
    existing = [
        QueueItem(**raw)
        for raw in cast("list[dict[str, Any]]", state.get("integration_queue", []))
    ]
    if any(queued.task_run_id == item.task_run_id for queued in existing):
        raise ParallelGoalError("Task draft is already queued for integration.")
    ordered = order_queue([*existing, item])
    state["integration_queue"] = [
        {
            "entry": queued.entry,
            "task_run_id": queued.task_run_id,
            "lane": queued.lane,
            "dependency_criticality": queued.dependency_criticality,
        }
        for queued in ordered
    ]


def release_child(state: dict[str, Any], *, lane: str, accepted: bool) -> None:
    """Release an accepted child while preserving failed/cancelled drafts."""
    lane = require_lane(state, lane)
    active = cast("dict[str, dict[str, Any]]", state.get("active_children", {}))
    child = active.get(lane)
    if child is None:
        raise ParallelGoalError(f"Lane {lane!r} has no active child.")
    if not accepted:
        raise ParallelGoalError(
            "Unaccepted child leases and worktree must be preserved."
        )
    run_id = str(child["run_id"])
    state["path_leases"] = release_leases(
        cast("dict[str, dict[str, str]]", state.get("path_leases", {})), run_id
    )
    del active[lane]


def is_parallel_state(state: dict[str, Any]) -> bool:
    """Return whether a Goal state explicitly selects parallel supervision."""
    return int(state.get("parallelism", 1)) == 3
