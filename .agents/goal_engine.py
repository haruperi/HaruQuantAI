#!/usr/bin/env python3
"""Deterministic Goal supervision above the existing HaruQuantAI Task workflow."""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_task import build_task_spec, is_entry_complete, parse_entries
from task_api import (
    OrchestratorError,
    _entry_gate,
    _git_ok,
    _load_state,
    apply_planner_blocker_resolution,
    prepare_task_run,
    resume_task_run,
)

GOAL_REQUIRED = (
    "goal_id",
    "goal_slug",
    "goal_name",
    "goal_request",
    "implementation_file",
    "selection_type",
)
GOAL_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
GOAL_RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SELECTION_TYPES = frozenset({"entries", "phase", "all_open"})


def load_goal_spec(path: Path) -> dict[str, Any]:
    """Load and validate one runtime Goal specification."""
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except OSError as exc:
        raise OrchestratorError(f"Cannot read Goal specification {path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise OrchestratorError(f"Invalid Goal TOML {path}: {exc}") from exc
    missing = [key for key in GOAL_REQUIRED if not raw.get(key)]
    if missing:
        raise OrchestratorError(f"Goal specification missing fields: {missing}")
    goal_slug = str(raw["goal_slug"])
    if not GOAL_SLUG_RE.fullmatch(goal_slug):
        raise OrchestratorError("goal_slug must be lowercase filesystem-safe text.")
    selection_type = str(raw["selection_type"])
    if selection_type not in SELECTION_TYPES:
        raise OrchestratorError(
            f"Unsupported goal selection_type {selection_type!r}; "
            f"expected one of {sorted(SELECTION_TYPES)}."
        )
    implementation_file = str(raw["implementation_file"])
    impl_path = Path(implementation_file)
    if impl_path.is_absolute() or ".." in impl_path.parts:
        raise OrchestratorError("Goal implementation_file must be repository-relative.")
    if selection_type == "entries":
        values = raw.get("entries")
        if not isinstance(values, list) or not values:
            raise OrchestratorError("entries selection requires a non-empty entries array.")
        normalized = [str(value) for value in values]
        if len(set(normalized)) != len(normalized):
            raise OrchestratorError("Goal entries must not contain duplicates.")
        raw["entries"] = normalized
    elif selection_type == "phase":
        selection = str(raw.get("selection", "")).strip()
        if not selection:
            raise OrchestratorError("phase selection requires a non-empty selection.")
        raw["selection"] = selection
    execution_order = str(raw.get("execution_order", "tracker"))
    if execution_order not in {"tracker", "listed"}:
        raise OrchestratorError("execution_order must be 'tracker' or 'listed'.")
    if execution_order == "listed" and selection_type != "entries":
        raise OrchestratorError("execution_order='listed' is valid only for entries selection.")
    if not bool(raw.get("skip_completed", True)):
        raise OrchestratorError(
            "Goal v1 requires skip_completed=true; rerunning completed entries is unsupported."
        )
    if not bool(raw.get("stop_on_blocked", True)):
        raise OrchestratorError(
            "Goal v1 requires stop_on_blocked=true; automatic child skipping is unsupported."
        )
    return cast("dict[str, Any]", raw)


def _tracker_path(repo: Path, spec_or_state: dict[str, Any]) -> Path:
    path = (repo / str(spec_or_state["implementation_file"])).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise OrchestratorError("Goal tracker resolves outside the repository.") from exc
    if not path.exists():
        raise OrchestratorError(f"Goal implementation tracker not found: {path}")
    return path


def resolve_goal_entries(
    spec: dict[str, Any], tracker_entries: dict[str, dict[str, Any]]
) -> list[str]:
    """Resolve the child list once; the returned order becomes frozen Goal scope."""
    selection_type = str(spec["selection_type"])
    if not bool(spec.get("skip_completed", True)):
        raise OrchestratorError("Goal v1 requires skip_completed=true.")
    execution_order = str(spec.get("execution_order", "tracker"))
    if selection_type == "entries":
        requested = [str(value) for value in cast("list[Any]", spec["entries"])]
        if len(set(requested)) != len(requested):
            raise OrchestratorError("Goal entries must not contain duplicates.")
        unknown = [entry for entry in requested if entry not in tracker_entries]
        if unknown:
            raise OrchestratorError(f"Goal references unknown tracker entries: {unknown}")
        if execution_order == "listed":
            selected = requested
        else:
            requested_set = set(requested)
            selected = [entry for entry in tracker_entries if entry in requested_set]
    elif selection_type == "phase":
        prefix = str(spec["selection"]).rstrip(".")
        selected = [
            entry
            for entry in tracker_entries
            if entry == prefix or entry.startswith(prefix + ".")
        ]
        if not selected:
            raise OrchestratorError(f"Goal phase {prefix!r} contains no tracker entries.")
    elif selection_type == "all_open":
        selected = list(tracker_entries)
    else:
        raise OrchestratorError(f"Unsupported Goal selection_type: {selection_type!r}")
    selected = [
        entry for entry in selected if not is_entry_complete(tracker_entries[entry])
    ]
    if not selected:
        raise OrchestratorError("Goal resolves to zero executable child Tasks.")
    return selected


def _goals_dir(cfg: dict[str, Any]) -> Path:
    return cast("Path", cfg["repo"]) / ".agents" / "goals"


def _goal_state_path(cfg: dict[str, Any], goal_run_id: str) -> Path:
    if not GOAL_RUN_RE.fullmatch(goal_run_id):
        raise OrchestratorError(f"Unsafe Goal run id: {goal_run_id!r}")
    return _goals_dir(cfg) / goal_run_id / "state.json"


def save_goal_state(cfg: dict[str, Any], state: dict[str, Any]) -> Path:
    """Atomically persist Goal state."""
    path = _goal_state_path(cfg, str(state["goal_run_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def load_goal_state(
    cfg: dict[str, Any], goal_run_id: str | None = None
) -> dict[str, Any]:
    """Load an explicit Goal run, or the latest Goal when no id is supplied."""
    root = _goals_dir(cfg)
    if goal_run_id:
        path = _goal_state_path(cfg, goal_run_id)
    else:
        candidates = sorted(root.glob("*/state.json"))
        if not candidates:
            raise OrchestratorError("No saved Goal runs found.")
        path = candidates[-1]
    if not path.exists():
        raise OrchestratorError(f"Goal state not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid Goal state {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise OrchestratorError(f"Invalid Goal state: {path}")
    return cast("dict[str, Any]", payload)


def _ensure_no_running_goal(cfg: dict[str, Any]) -> None:
    """Prevent multiple Goal supervisors from competing for the Task workspace."""
    for path in sorted(_goals_dir(cfg).glob("*/state.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OrchestratorError(f"Cannot validate existing Goal state {path}: {exc}") from exc
        if isinstance(payload, dict) and payload.get("status") == "RUNNING":
            raise OrchestratorError(
                f"Another Goal is still RUNNING: {payload.get('goal_run_id', path.parent.name)}"
            )


def _goal_record(state: dict[str, Any], event: str, **facts: Any) -> None:
    state.setdefault("history", []).append(
        {
            "time": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
            "event": event,
            **facts,
        }
    )


def create_goal_state(cfg: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Resolve a Goal exactly once and persist its frozen child scope."""
    tracker = _tracker_path(cast("Path", cfg["repo"]), spec)
    resolved = resolve_goal_entries(spec, parse_entries(tracker))
    stamp = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%d-%H%M%S-%f")
    state: dict[str, Any] = {
        "goal_run_id": f"{stamp}-{spec['goal_slug']}",
        "goal_id": str(spec["goal_id"]),
        "goal_slug": str(spec["goal_slug"]),
        "goal_name": str(spec["goal_name"]),
        "goal_request": str(spec["goal_request"]),
        "implementation_file": str(spec["implementation_file"]),
        "selection_type": str(spec["selection_type"]),
        "resolved_entries": resolved,
        "completed_entries": [],
        "remaining_entries": list(resolved),
        "active_child": None,
        "child_runs": {},
        "children": [],
        "status": "RUNNING",
        "blocked_reason": None,
        "history": [],
    }
    _goal_record(state, "GOAL_ACTIVATED", resolved_entries=list(resolved))
    save_goal_state(cfg, state)
    return state


def _child_spec_paths(
    cfg: dict[str, Any], state: dict[str, Any], entry_id: str
) -> tuple[Path, Path]:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", entry_id).strip("-") or "entry"
    archive = (
        _goals_dir(cfg)
        / str(state["goal_run_id"])
        / "children"
        / f"{safe}.toml"
    )
    current = cast("Path", cfg["repo"]) / ".agents" / "task.toml"
    return archive, current


def _child_run_id(state: dict[str, Any], entry_id: str, task_slug: str) -> str:
    """Derive an entry-specific Task run id so Goal children never share sessions."""
    safe_entry = re.sub(r"[^A-Za-z0-9._-]+", "-", entry_id).strip("-") or "entry"
    return f"{state['goal_run_id']}-{safe_entry}-{task_slug}"


def _current_tracker_entries(
    cfg: dict[str, Any], state: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    return parse_entries(_tracker_path(cast("Path", cfg["repo"]), state))


def _write_child_spec(
    cfg: dict[str, Any], state: dict[str, Any], entry_id: str
) -> dict[str, Any]:
    tracker_entries = _current_tracker_entries(cfg, state)
    entry = tracker_entries.get(entry_id)
    if entry is None:
        raise OrchestratorError(
            f"Frozen Goal child {entry_id!r} disappeared from the tracker."
        )
    if is_entry_complete(entry):
        raise OrchestratorError(
            f"Frozen Goal child {entry_id!r} became complete before its Task started; "
            "Goal scope changed outside the supervisor."
        )
    body, _label, _previews = build_task_spec(
        entry_id, entry, str(state["implementation_file"])
    )
    archive, current = _child_spec_paths(cfg, state, entry_id)
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(body, encoding="utf-8")
    current.write_text(body, encoding="utf-8")
    parsed = tomllib.loads(body)
    return {key: str(value) for key, value in parsed.items()}


def _block_goal(
    cfg: dict[str, Any], state: dict[str, Any], reason: str, **facts: Any
) -> dict[str, Any]:
    state["status"] = "BLOCKED"
    state["blocked_reason"] = reason
    _goal_record(state, "GOAL_BLOCKED", reason=reason, **facts)
    save_goal_state(cfg, state)
    return state


def _verify_active_child_identity(
    state: dict[str, Any], active: dict[str, Any], child: dict[str, Any]
) -> None:
    """Verify Goal state still points to the exact intended child Task run."""
    entry_id = str(active["entry"])
    run_id = str(active["run_id"])
    recorded = cast("dict[str, str]", state.get("child_runs", {})).get(entry_id)
    if recorded != run_id or str(child.get("run_id")) != run_id:
        raise OrchestratorError("Goal active child run identity does not match its ledger.")
    task = cast("dict[str, Any]", child.get("task") or {})
    if str(task.get("implementation_entry", "")) != entry_id:
        raise OrchestratorError("Goal active child Task targets a different tracker entry.")


def _verify_child_acceptance(
    cfg: dict[str, Any],
    state: dict[str, Any],
    child: dict[str, Any],
    entry_id: str,
) -> None:
    repo = cast("Path", cfg["repo"])
    if child.get("status") != "ACCEPTED" or child.get("phase") != "done":
        raise OrchestratorError("Goal attempted to accept a non-terminal child Task.")
    if _git_ok(repo, "branch", "--show-current") != str(cfg["main_branch"]):
        raise OrchestratorError("Accepted child did not return the repository to main.")
    if _git_ok(repo, "status", "--porcelain"):
        raise OrchestratorError("Accepted child left main dirty.")
    for path in [*cfg["journals"].values(), cfg["next_agent"]]:
        if not path.exists() or path.stat().st_size != 0:
            raise OrchestratorError(
                f"Accepted child left active-task artifact non-empty: {path}"
            )
    tracker_entries = _current_tracker_entries(cfg, state)
    current = tracker_entries.get(entry_id)
    if current is None or not is_entry_complete(current):
        raise OrchestratorError(
            f"Accepted child {entry_id} did not mark its frozen tracker entry complete."
        )


def _accept_child(
    cfg: dict[str, Any], state: dict[str, Any], child: dict[str, Any]
) -> None:
    active = cast("dict[str, Any]", state["active_child"])
    _verify_active_child_identity(state, active, child)
    entry_id = str(active["entry"])
    _verify_child_acceptance(cfg, state, child, entry_id)
    accepted_head = _git_ok(cast("Path", cfg["repo"]), "rev-parse", "HEAD")
    state.setdefault("children", []).append(
        {
            "entry": entry_id,
            "task_run_id": str(child["run_id"]),
            "task_id": str(child["task"]["task_id"]),
            "status": "ACCEPTED",
            "baseline": str(child["baseline"]),
            "accepted_head": accepted_head,
            "commit": accepted_head,
            "started_at": active.get("started_at"),
            "accepted_at": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
        }
    )
    state.setdefault("completed_entries", []).append(entry_id)
    remaining = cast("list[str]", state["remaining_entries"])
    if not remaining or remaining[0] != entry_id:
        raise OrchestratorError("Goal child order no longer matches remaining scope.")
    remaining.pop(0)
    state["active_child"] = None
    _goal_record(
        state,
        "CHILD_ACCEPTED",
        entry=entry_id,
        task_run_id=child["run_id"],
        commit=accepted_head,
    )
    save_goal_state(cfg, state)


def _finalize_goal(cfg: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if state.get("active_child") is not None or state.get("remaining_entries"):
        raise OrchestratorError("Goal cannot finalize while child work remains.")
    tracker_entries = _current_tracker_entries(cfg, state)
    incomplete = [
        entry
        for entry in cast("list[str]", state["resolved_entries"])
        if entry not in tracker_entries or not is_entry_complete(tracker_entries[entry])
    ]
    if incomplete:
        return _block_goal(
            cfg, state, "FINAL_TRACKER_RECONCILIATION_FAILED", entries=incomplete
        )
    repo = cast("Path", cfg["repo"])
    if _git_ok(repo, "branch", "--show-current") != str(cfg["main_branch"]):
        return _block_goal(cfg, state, "FINAL_BRANCH_NOT_MAIN")
    if _git_ok(repo, "status", "--porcelain"):
        return _block_goal(cfg, state, "FINAL_MAIN_DIRTY")
    state["status"] = "ACCEPTED"
    state["blocked_reason"] = None
    _goal_record(
        state,
        "GOAL_ACCEPTED",
        completed=len(cast("list[Any]", state["completed_entries"])),
    )
    save_goal_state(cfg, state)
    return state


def advance_goal(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    auto_approve: bool = False,
    approved: bool = False,
    reject_feedback: str | None = None,
    commit_approved: bool = False,
    commit_reject_feedback: str | None = None,
    resolve_planner_blocker: str | None = None,
) -> dict[str, Any]:
    """Advance a Goal until completion or the active child requires external action."""
    if state.get("status") == "CANCELLED":
        raise OrchestratorError("A CANCELLED Goal cannot be resumed.")
    if state.get("status") == "ACCEPTED":
        return state
    if state.get("status") == "BLOCKED":
        raise OrchestratorError(
            f"Goal is BLOCKED: {state.get('blocked_reason')}. "
            "Resolve the recorded cause before creating a replacement Goal run."
        )
    while True:
        active = cast("dict[str, Any] | None", state.get("active_child"))
        if active is not None:
            child = _load_state(cfg, str(active["run_id"]))
            try:
                _verify_active_child_identity(state, active, child)
            except OrchestratorError as exc:
                return _block_goal(
                    cfg,
                    state,
                    "CHILD_IDENTITY_MISMATCH",
                    entry=active.get("entry"),
                    detail=str(exc),
                )
            if resolve_planner_blocker:
                apply_planner_blocker_resolution(cfg, child, resolve_planner_blocker)
                resolve_planner_blocker = None
            if child.get("status") == "CANCELLED":
                return _block_goal(
                    cfg,
                    state,
                    "CHILD_CANCELLED",
                    entry=active["entry"],
                    task_run_id=child["run_id"],
                )
            if child.get("status") == "MAX_ITERATIONS":
                return _block_goal(
                    cfg,
                    state,
                    "CHILD_MAX_ITERATIONS",
                    entry=active["entry"],
                    task_run_id=child["run_id"],
                )
            if child.get("status") != "ACCEPTED":
                child = resume_task_run(
                    cfg,
                    child,
                    auto_approve=auto_approve,
                    approved=approved,
                    reject_feedback=reject_feedback,
                    commit_approved=commit_approved,
                    commit_reject_feedback=commit_reject_feedback,
                )
                approved = False
                reject_feedback = None
                commit_approved = False
                commit_reject_feedback = None
                active["phase"] = child.get("phase")
                active["status"] = child.get("status")
                save_goal_state(cfg, state)
            if child.get("status") == "ACCEPTED":
                try:
                    _accept_child(cfg, state, child)
                except OrchestratorError as exc:
                    return _block_goal(
                        cfg,
                        state,
                        "CHILD_ACCEPTANCE_RECONCILIATION_FAILED",
                        entry=active["entry"],
                        detail=str(exc),
                    )
                continue
            if child.get("phase") == "planner_blocked":
                return state
            if child.get("status") not in {"RUNNING", None}:
                return _block_goal(
                    cfg,
                    state,
                    "CHILD_TERMINAL_FAILURE",
                    entry=active["entry"],
                    child_status=child.get("status"),
                )
            return state

        remaining = cast("list[str]", state["remaining_entries"])
        if not remaining:
            return _finalize_goal(cfg, state)
        entry_id = remaining[0]
        try:
            task = _write_child_spec(cfg, state, entry_id)
            child = prepare_task_run(
                cfg,
                task,
                run_id=_child_run_id(state, entry_id, str(task["task_slug"])),
            )
        except OrchestratorError as exc:
            return _block_goal(
                cfg,
                state,
                "CHILD_PREPARATION_FAILED",
                entry=entry_id,
                detail=str(exc),
            )
        active = {
            "entry": entry_id,
            "run_id": child["run_id"],
            "task_id": child["task"]["task_id"],
            "baseline": child["baseline"],
            "phase": child["phase"],
            "status": child["status"],
            "started_at": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
        }
        state["active_child"] = active
        cast("dict[str, str]", state["child_runs"])[entry_id] = str(child["run_id"])
        _goal_record(
            state,
            "CHILD_STARTED",
            entry=entry_id,
            task_run_id=child["run_id"],
            baseline=child["baseline"],
        )
        save_goal_state(cfg, state)
        child = resume_task_run(
            cfg,
            child,
            auto_approve=auto_approve,
            approved=approved,
            reject_feedback=reject_feedback,
            commit_approved=commit_approved,
            commit_reject_feedback=commit_reject_feedback,
        )
        approved = False
        reject_feedback = None
        commit_approved = False
        commit_reject_feedback = None
        active["phase"] = child.get("phase")
        active["status"] = child.get("status")
        save_goal_state(cfg, state)
        if child.get("status") == "ACCEPTED":
            try:
                _accept_child(cfg, state, child)
            except OrchestratorError as exc:
                return _block_goal(
                    cfg,
                    state,
                    "CHILD_ACCEPTANCE_RECONCILIATION_FAILED",
                    entry=entry_id,
                    detail=str(exc),
                )
            continue
        if child.get("phase") == "planner_blocked":
            return state
        if child.get("status") == "MAX_ITERATIONS":
            return _block_goal(
                cfg,
                state,
                "CHILD_MAX_ITERATIONS",
                entry=entry_id,
                task_run_id=child["run_id"],
            )
        return state


def start_goal(
    cfg: dict[str, Any], spec: dict[str, Any], **router_args: Any
) -> dict[str, Any]:
    """Validate idle Task state, freeze Goal scope, and begin the first child."""
    _entry_gate(cfg)
    _ensure_no_running_goal(cfg)
    state = create_goal_state(cfg, spec)
    return advance_goal(cfg, state, **router_args)


def cancel_goal(
    cfg: dict[str, Any], state: dict[str, Any], reason: str
) -> dict[str, Any]:
    """Cancel Goal supervision while preserving any active child Task evidence."""
    if state.get("status") == "ACCEPTED":
        raise OrchestratorError("An ACCEPTED Goal cannot be cancelled.")
    if state.get("status") == "CANCELLED":
        return state
    state["status"] = "CANCELLED"
    state["cancellation"] = {
        "reason": reason,
        "cancelled_at": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
    }
    _goal_record(state, "GOAL_CANCELLED", reason=reason)
    save_goal_state(cfg, state)
    return state


def format_goal_status(state: dict[str, Any]) -> str:
    """Render deterministic Goal progress."""
    resolved = cast("list[str]", state.get("resolved_entries", []))
    completed = cast("list[str]", state.get("completed_entries", []))
    remaining = cast("list[str]", state.get("remaining_entries", []))
    active = cast("dict[str, Any] | None", state.get("active_child"))
    lines = [
        f"GOAL : {state.get('status', 'UNKNOWN')}",
        f"GOAL_ID : {state.get('goal_id', '')}",
        f"GOAL_RUN_ID : {state.get('goal_run_id', '')}",
        f"PROGRESS : {len(completed)} / {len(resolved)}",
        "COMPLETED : " + (", ".join(completed) if completed else "NONE"),
    ]
    if active:
        lines.extend(
            [
                f"CURRENT_CHILD : {active.get('entry')}",
                f"CHILD_RUN_ID : {active.get('run_id')}",
                f"CHILD_STATE : {active.get('phase') or active.get('status')}",
            ]
        )
    else:
        lines.append("CURRENT_CHILD : NONE")
    lines.append("REMAINING : " + (", ".join(remaining) if remaining else "NONE"))
    if state.get("blocked_reason"):
        lines.append(f"BLOCKED_REASON : {state['blocked_reason']}")
    return "\n".join(lines)


__all__ = [name for name in globals() if not name.startswith("__")]
