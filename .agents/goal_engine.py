#!/usr/bin/env python3
"""Deterministic Goal supervision above the existing HaruQuantAI Task workflow."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent))
from integration_queue import (
    IntegrationError,
    IntegrationLock,
    archive_draft,
    refresh_archived_draft,
    refresh_overlap,
)
from make_task import build_task_spec, is_entry_complete, parse_entries
from parallel_goal_engine import (
    DEFAULT_LANES,
    ParallelGoalError,
    acquire_child_paths,
    create_parallel_state,
    enqueue_reviewed_draft,
    is_parallel_state,
    load_schedule,
    ready_entries,
    release_child,
    require_lane,
)
from path_leases import release_leases
from runtime_policy import RuntimePolicy, scope_fingerprint
from task_api import (
    _attach_task_packet,
    apply_planner_blocker_resolution,
    prepare_lane_task_run,
    prepare_task_run,
    resume_task_run,
)
from workflow_protocol import (
    SCHEMA_VERSION,
    OrchestratorError,
    _git_ok,
    _render_next_agent,
    _transition_for,
    _worktree_fingerprint,
    assemble_config,
    compose_prompt,
    parse_next_agent,
    validate_next_agent,
)
from workflow_runtime import (
    _build_fields,
    _derive_task_branch,
    _ensure_runtime_policy_unchanged,
    _entry_gate,
    _load_state,
    _save_state,
    _write_orchestrator_planner_prompt,
)
from worktree_manager import (
    WorktreeError,
    create_lane_worktrees,
    prepare_task_branch,
    remove_clean_lane_worktree,
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
CHILD_CONTEXT_LABEL = "Goal-level child context:"
ASSUMPTION_CONTEXT_LABEL = "Goal unattended assumption policy:"
ASSUMPTION_SECTION = "### Assumptions for Human Review"
SOLO_CHILD_CHAT_PRIMARY = "/new"
SOLO_CHILD_CHAT_FALLBACK = "app-native create_thread"
ASSUMPTION_CONTEXT = """The Goal is configured with stop_on_blocked=false under frozen unattended runtime policy. Before emitting BLOCKED, make one bounded attempt to resolve non-critical ambiguity with an educated, reversible assumption grounded in repository evidence. Never assume owner authorization, credentials, external facts, live-action safety, destructive authority, security policy, acceptance evidence, or scope expansion. True protected/external blockers still stop.

Planner and Executor must record every applied assumption under an exact `### Assumptions for Human Review` heading. Reviewer must reconcile them and include that heading in the final accepted review, using `- NONE` only when no assumption was used and no blocker retry occurred. After a blocker retry, record the blocker and outcome even if no assumption was accepted and a human later resolved it. For each assumption record the original blocker, assumption, repository evidence, affected scope, risk, validation, and revisit trigger."""


def load_goal_spec(path: Path) -> dict[str, Any]:
    """Load and validate one runtime Goal specification."""
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except OSError as exc:
        raise OrchestratorError(
            f"Cannot read Goal specification {path}: {exc}"
        ) from exc
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
            raise OrchestratorError(
                "entries selection requires a non-empty entries array."
            )
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
        raise OrchestratorError(
            "execution_order='listed' is valid only for entries selection."
        )
    if not bool(raw.get("skip_completed", True)):
        raise OrchestratorError(
            "Goal v1 requires skip_completed=true; rerunning completed entries is unsupported."
        )
    stop_on_blocked = raw.get("stop_on_blocked", True)
    if not isinstance(stop_on_blocked, bool):
        raise OrchestratorError("stop_on_blocked must be a boolean.")
    if "child_additional_context" in raw:
        child_context = raw["child_additional_context"]
        if not isinstance(child_context, str) or not child_context.strip():
            raise OrchestratorError(
                "child_additional_context must be a non-blank string when supplied."
            )
    parallelism = raw.get("parallelism", 1)
    if not isinstance(parallelism, int) or isinstance(parallelism, bool):
        raise OrchestratorError("parallelism must be an integer.")
    if parallelism not in {1, 3}:
        raise OrchestratorError("parallelism must be either 1 or 3.")
    raw["parallelism"] = parallelism
    if parallelism == 3:
        lanes = raw.get("lane_names", list(DEFAULT_LANES))
        if not isinstance(lanes, list) or not all(isinstance(v, str) for v in lanes):
            raise OrchestratorError("lane_names must be a string array.")
        if tuple(value.strip().lower() for value in lanes) != DEFAULT_LANES:
            raise OrchestratorError(
                "Parallel Goal lanes must be codex, gemini, and zcode in that order."
            )
        schedule = str(
            raw.get(
                "dependency_schedule",
                "docs/dev/evidence/dependency-schedule.json",
            )
        )
        schedule_path = Path(schedule)
        if schedule_path.is_absolute() or ".." in schedule_path.parts:
            raise OrchestratorError(
                "dependency_schedule must be a safe repository-relative path."
            )
        raw["lane_names"] = list(DEFAULT_LANES)
        raw["dependency_schedule"] = schedule
    return raw


def _tracker_path(repo: Path, spec_or_state: dict[str, Any]) -> Path:
    path = (repo / str(spec_or_state["implementation_file"])).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise OrchestratorError(
            "Goal tracker resolves outside the repository."
        ) from exc
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
            raise OrchestratorError(
                f"Goal references unknown tracker entries: {unknown}"
            )
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
            raise OrchestratorError(
                f"Goal phase {prefix!r} contains no tracker entries."
            )
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
    data = json.dumps(state, indent=2, sort_keys=True, default=str) + "\n"
    temporary.write_text(data, encoding="utf-8")
    for attempt in range(5):
        try:
            temporary.replace(path)
            return path
        except PermissionError, OSError:
            if attempt == 4:
                path.write_text(data, encoding="utf-8")
                if temporary.exists():
                    try:
                        temporary.unlink()
                    except OSError:
                        pass
                return path
            import time

            time.sleep(0.05)
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
            raise OrchestratorError(
                f"Cannot validate existing Goal state {path}: {exc}"
            ) from exc
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
    if cfg.get("mode") == "quick-fix":
        raise OrchestratorError("Quick-Fix mode cannot activate or supervise a Goal.")
    raw_stop_on_blocked = spec.get("stop_on_blocked", True)
    if not isinstance(raw_stop_on_blocked, bool):
        raise OrchestratorError("stop_on_blocked must be a boolean.")
    stop_on_blocked = raw_stop_on_blocked
    policy = cfg.get("runtime_policy")
    if not stop_on_blocked and (
        not isinstance(policy, RuntimePolicy) or policy.approval_policy != "unattended"
    ):
        raise OrchestratorError(
            "stop_on_blocked=false requires a frozen unattended runtime policy."
        )
    tracker = _tracker_path(cast("Path", cfg["repo"]), spec)
    resolved = resolve_goal_entries(spec, parse_entries(tracker))
    stamp = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%d-%H%M%S-%f")
    frozen_scope = {"spec": spec, "resolved_entries": resolved}
    state: dict[str, Any] = {
        "goal_run_id": f"{stamp}-{spec['goal_slug']}",
        "goal_id": str(spec["goal_id"]),
        "goal_slug": str(spec["goal_slug"]),
        "goal_name": str(spec["goal_name"]),
        "goal_request": str(spec["goal_request"]),
        "implementation_file": str(spec["implementation_file"]),
        "selection_type": str(spec["selection_type"]),
        "stop_on_blocked": stop_on_blocked,
        "resolved_entries": resolved,
        "completed_entries": [],
        "remaining_entries": list(resolved),
        "active_child": None,
        "child_runs": {},
        "children": [],
        "child_chat_handoff": None,
        "child_chat_handoffs": [],
        "assumption_ledger": [],
        "assumption_reviews": [],
        "status": "RUNNING",
        "blocked_reason": None,
        "history": [],
        "goal_scope": frozen_scope,
        "scope_fingerprint": scope_fingerprint(frozen_scope),
    }
    if isinstance(policy, RuntimePolicy):
        state["runtime_policy_fingerprint"] = policy.fingerprint
        state["runtime_policy_schema_version"] = policy.schema_version
        state["runtime_mode"] = policy.effective_mode
        state["approval_policy"] = policy.approval_policy
    if int(spec.get("parallelism", 1)) == 3:
        if (
            not isinstance(policy, RuntimePolicy)
            or policy.schema_version < 4
            or not policy.parallel.enabled
        ):
            raise OrchestratorError(
                "Parallel Goal activation requires an enabled schema-v4 parallel policy."
            )
        if tuple(policy.parallel.lane_names) != tuple(spec["lane_names"]):
            raise OrchestratorError(
                "Goal lane names differ from the frozen runtime policy."
            )
        schedule = cast("Path", cfg["repo"]) / str(spec["dependency_schedule"])
        try:
            state = create_parallel_state(
                state, lanes=list(spec["lane_names"]), schedule_path=schedule
            )
        except ParallelGoalError as exc:
            raise OrchestratorError(str(exc)) from exc
        state["dependency_schedule"] = str(spec["dependency_schedule"])
    if "child_additional_context" in spec:
        state["child_additional_context"] = spec["child_additional_context"]
    _goal_record(state, "GOAL_ACTIVATED", resolved_entries=list(resolved))
    save_goal_state(cfg, state)
    return state


def _child_spec_paths(
    cfg: dict[str, Any], state: dict[str, Any], entry_id: str
) -> tuple[Path, Path]:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", entry_id).strip("-") or "entry"
    archive = _goals_dir(cfg) / str(state["goal_run_id"]) / "children" / f"{safe}.toml"
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
    context_sections: list[str] = []
    child_context = state.get("child_additional_context")
    if child_context is not None:
        if not isinstance(child_context, str) or not child_context.strip():
            raise OrchestratorError(
                "Frozen Goal child_additional_context is not a non-blank string."
            )
        context_sections.append(f"{CHILD_CONTEXT_LABEL}\n{child_context}")
    if not bool(state.get("stop_on_blocked", True)):
        context_sections.append(f"{ASSUMPTION_CONTEXT_LABEL}\n{ASSUMPTION_CONTEXT}")
    if context_sections:
        task_spec = tomllib.loads(body)
        tracker_context = str(task_spec.get("additional_context", "")).strip()
        goal_context = "\n\n".join(context_sections)
        combined_context = (
            f"{tracker_context}\n\n{goal_context}" if tracker_context else goal_context
        )
        encoded_context = json.dumps(combined_context, ensure_ascii=False)
        body, replacements = re.subn(
            r"^additional_context\s*=.*$",
            lambda _match: f"additional_context = {encoded_context}",
            body,
            count=1,
            flags=re.MULTILINE,
        )
        if replacements != 1:
            raise OrchestratorError(
                "Generated child Task is missing additional_context."
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
        raise OrchestratorError(
            "Goal active child run identity does not match its ledger."
        )
    task = cast("dict[str, Any]", child.get("task") or {})
    if str(task.get("implementation_entry", "")) != entry_id:
        raise OrchestratorError(
            "Goal active child Task targets a different tracker entry."
        )


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


def _latest_assumption_section(text: str) -> str | None:
    """Return the final canonical assumption-review section from a journal."""
    starts = [match.end() for match in re.finditer(re.escape(ASSUMPTION_SECTION), text)]
    if not starts:
        return None
    start = starts[-1]
    tail = text[start:]
    boundary = re.search(r"(?m)^(?:#{1,3}\s|STOPPED\s*:)", tail)
    return tail[: boundary.start() if boundary else None].strip()


def _record_child_assumption_review(
    cfg: dict[str, Any],
    state: dict[str, Any],
    child: dict[str, Any],
    entry_id: str,
) -> None:
    """Persist the accepted Reviewer's assumption section for later human audit."""
    if bool(state.get("stop_on_blocked", True)):
        return
    run_id = str(child["run_id"])
    repo = Path(cfg["repo"])
    logs_dir = Path(cfg.get("logs_dir", repo / ".agents" / "logs"))
    reviewer = logs_dir / run_id / "closeout" / "reviewer.md"
    try:
        journal = reviewer.read_text(encoding="utf-8")
    except OSError as exc:
        raise OrchestratorError(
            f"Accepted unattended child lacks archived Reviewer evidence: {exc}"
        ) from exc
    section = _latest_assumption_section(journal)
    if not section:
        raise OrchestratorError(
            "Accepted unattended child lacks the required Assumptions for Human "
            "Review section."
        )
    normalized = section.strip().lstrip("- ").rstrip(".").casefold()
    has_assumptions = normalized != "none"
    active = cast("dict[str, Any]", state.get("active_child") or {})
    retry_used = bool(active.get("assumption_retry_used"))
    if retry_used and not has_assumptions:
        raise OrchestratorError(
            "Reviewer reported no assumptions after an unattended blocker retry; "
            "the blocker, retry outcome, and any human resolution must be recorded."
        )
    try:
        archive_path = reviewer.relative_to(repo)
    except ValueError:
        archive_path = reviewer
    review = {
        "entry": entry_id,
        "task_run_id": run_id,
        "has_assumptions": has_assumptions,
        "assumption_retry_used": retry_used,
        "section": section,
        "section_sha256": hashlib.sha256(section.encode("utf-8")).hexdigest(),
        "reviewer_archive": str(archive_path).replace("\\", "/"),
    }
    state.setdefault("assumption_reviews", []).append(review)
    if has_assumptions:
        state.setdefault("assumption_ledger", []).append(review)


def _accept_child(
    cfg: dict[str, Any], state: dict[str, Any], child: dict[str, Any]
) -> None:
    active = cast("dict[str, Any]", state["active_child"])
    _verify_active_child_identity(state, active, child)
    entry_id = str(active["entry"])
    _verify_child_acceptance(cfg, state, child, entry_id)
    _record_child_assumption_review(cfg, state, child, entry_id)
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


def _require_solo_child_chat(
    cfg: dict[str, Any], state: dict[str, Any], child: dict[str, Any]
) -> bool:
    """Checkpoint a mandatory fresh-chat boundary between solo Goal children."""
    remaining = cast("list[str]", state.get("remaining_entries", []))
    schema_version = state.get("runtime_policy_schema_version")
    if (
        state.get("runtime_mode") != "solo"
        or (isinstance(schema_version, int) and schema_version < 3)
        or not remaining
    ):
        return False
    if state.get("child_chat_handoff") is not None:
        raise OrchestratorError("A solo child-chat handoff is already pending.")
    completed = cast("list[str]", state.get("completed_entries", []))
    payload = {
        "goal_run_id": str(state["goal_run_id"]),
        "completed_entry": completed[-1],
        "completed_task_run_id": str(child["run_id"]),
        "next_entry": remaining[0],
        "next_child_number": len(completed) + 1,
    }
    handoff = {
        **payload,
        "handoff_id": scope_fingerprint(payload),
        "status": "REQUIRED",
        "primary_action": SOLO_CHILD_CHAT_PRIMARY,
        "fallback_action": SOLO_CHILD_CHAT_FALLBACK,
        "created_at": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
    }
    state["child_chat_handoff"] = handoff
    _goal_record(
        state,
        "NEXT_CHILD_CHAT_REQUIRED",
        handoff_id=handoff["handoff_id"],
        completed_entry=handoff["completed_entry"],
        next_entry=handoff["next_entry"],
        primary_action=SOLO_CHILD_CHAT_PRIMARY,
        fallback_action=SOLO_CHILD_CHAT_FALLBACK,
    )
    save_goal_state(cfg, state)
    return True


def _claim_solo_child_chat(
    cfg: dict[str, Any], state: dict[str, Any], handoff_id: str | None
) -> bool:
    """Claim the exact pending handoff before preparing the next solo child."""
    pending = state.get("child_chat_handoff")
    if pending is None:
        if handoff_id is not None:
            raise OrchestratorError(
                "No solo child-chat handoff is pending; the claim is stale."
            )
        return True
    if not isinstance(pending, dict):
        raise OrchestratorError("Invalid solo child-chat handoff state.")
    if handoff_id is None:
        return False
    if handoff_id != pending.get("handoff_id"):
        raise OrchestratorError("Solo child-chat handoff id does not match.")
    claimed = dict(pending)
    claimed["status"] = "CLAIMED"
    claimed["claimed_at"] = dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds")
    state.setdefault("child_chat_handoffs", []).append(claimed)
    state["child_chat_handoff"] = None
    _goal_record(
        state,
        "NEXT_CHILD_CHAT_CLAIMED",
        handoff_id=handoff_id,
        next_entry=claimed["next_entry"],
    )
    save_goal_state(cfg, state)
    return True


def _apply_unattended_assumption_retry(
    cfg: dict[str, Any],
    state: dict[str, Any],
    active: dict[str, Any],
    child: dict[str, Any],
) -> bool:
    """Give one blocked Planner a deterministic assumption-policy retry."""
    if (
        child.get("phase") != "planner_blocked"
        or bool(state.get("stop_on_blocked", True))
        or bool(active.get("assumption_retry_used"))
    ):
        return False
    if state.get("approval_policy") != "unattended":
        raise OrchestratorError(
            "Unattended assumption retry requires frozen unattended policy."
        )
    evidence = (
        "Frozen Goal stop_on_blocked=false policy authorizes one retry. Resolve only "
        "non-critical ambiguity through an educated, reversible, repository-grounded "
        "assumption and record it under 'Assumptions for Human Review'. Protected or "
        "external blockers must remain BLOCKED."
    )
    apply_planner_blocker_resolution(
        cfg, child, evidence, source="GOAL_ASSUMPTION_POLICY"
    )
    active["assumption_retry_used"] = True
    _goal_record(
        state,
        "CHILD_ASSUMPTION_RETRY",
        entry=active["entry"],
        task_run_id=child["run_id"],
    )
    save_goal_state(cfg, state)
    return True


def accept_recovered_child(
    cfg: dict[str, Any], state: dict[str, Any], child: dict[str, Any]
) -> None:
    """Reconcile one deterministically recovered accepted child without activation."""
    _accept_child(cfg, state, child)


def _parallel_lane_cfg(
    cfg: dict[str, Any], state: dict[str, Any], lane: str
) -> dict[str, Any]:
    """Assemble one lane-local Task configuration from frozen primary policy."""
    record = cast("dict[str, Any]", state["worktrees"])[lane]
    lane_repo = Path(str(record["path"])).resolve()
    primary_policy = cast("Path", cfg["repo"]) / ".agents" / "run-config.toml"
    lane_policy = lane_repo / ".agents" / "run-config.toml"
    lane_policy.parent.mkdir(parents=True, exist_ok=True)
    if not lane_policy.exists():
        shutil.copyfile(primary_policy, lane_policy)
    lane_cfg = assemble_config(str(lane_repo))
    policy = lane_cfg.get("runtime_policy")
    if not isinstance(policy, RuntimePolicy) or policy.fingerprint != state.get(
        "runtime_policy_fingerprint"
    ):
        raise OrchestratorError("Lane runtime policy differs from frozen Goal policy.")
    return lane_cfg


def _parallel_child_spec(
    cfg: dict[str, Any], state: dict[str, Any], entry_id: str, lane_repo: Path
) -> dict[str, Any]:
    """Write one exact child specification to its archive and lane only."""
    entries = _current_tracker_entries(cfg, state)
    entry = entries.get(entry_id)
    if entry is None or is_entry_complete(entry):
        raise OrchestratorError(
            f"Parallel child {entry_id!r} is missing or already complete."
        )
    body, _label, _previews = build_task_spec(
        entry_id, entry, str(state["implementation_file"])
    )
    archive, _unused_primary = _child_spec_paths(cfg, state, entry_id)
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(body, encoding="utf-8")
    current = lane_repo / ".agents" / "task.toml"
    current.write_text(body, encoding="utf-8")
    return {key: str(value) for key, value in tomllib.loads(body).items()}


def _dispatch_parallel_children(  # noqa: PLR0911
    cfg: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    """Fill free lanes with deterministic schedule-ready Goal children."""
    if not is_parallel_state(state):
        raise OrchestratorError("Parallel dispatch requires parallel Goal state.")
    repo = cast("Path", cfg["repo"])
    tracker_entries = _current_tracker_entries(cfg, state)
    accepted = {
        entry for entry, value in tracker_entries.items() if is_entry_complete(value)
    }
    accepted.update(str(value) for value in state.get("completed_entries", []))
    schedule_path = repo / str(state["dependency_schedule"])
    try:
        predecessors, schedule_hash = load_schedule(schedule_path)
    except ParallelGoalError as exc:
        return _block_goal(cfg, state, "DEPENDENCY_SCHEDULE_INVALID", detail=str(exc))
    if schedule_hash != state.get("dependency_schedule_sha256"):
        return _block_goal(cfg, state, "DEPENDENCY_SCHEDULE_CHANGED")
    active = cast("dict[str, dict[str, Any]]", state["active_children"])
    active_entries = {str(child["entry"]) for child in active.values()}
    try:
        ready = ready_entries(
            selected=[str(value) for value in state["resolved_entries"]],
            completed=accepted,
            active=active_entries,
            predecessors=predecessors,
        )
    except ParallelGoalError as exc:
        return _block_goal(cfg, state, "READY_QUEUE_INVALID", detail=str(exc))
    for lane in [str(value) for value in state["lane_names"]]:
        if lane in active or not ready:
            continue
        entry_id = ready.pop(0)
        record = cast("dict[str, Any]", state["worktrees"])[lane]
        lane_repo = Path(str(record["path"])).resolve()
        baseline = _git_ok(repo, "rev-parse", "HEAD")
        if _git_ok(lane_repo, "rev-parse", "HEAD") != baseline:
            return _block_goal(
                cfg, state, "LANE_BASELINE_STALE", lane=lane, entry=entry_id
            )
        task = _parallel_child_spec(cfg, state, entry_id, lane_repo)
        branch = _derive_task_branch(task)
        try:
            prepare_task_branch(lane_repo, branch=branch, baseline=baseline)
            lane_cfg = _parallel_lane_cfg(cfg, state, lane)
            run_id = _child_run_id(state, entry_id, str(task["task_slug"]))
            child = prepare_lane_task_run(
                lane_cfg,
                task,
                run_id=run_id,
                lane=lane,
                branch=branch,
                baseline=baseline,
            )
            child = resume_task_run(lane_cfg, child)
        except (ParallelGoalError, RuntimeError) as exc:
            return _block_goal(
                cfg,
                state,
                "PARALLEL_CHILD_PREPARATION_FAILED",
                lane=lane,
                entry=entry_id,
                detail=str(exc),
            )
        active[lane] = {
            "entry": entry_id,
            "run_id": child["run_id"],
            "task_id": child["task"]["task_id"],
            "branch": branch,
            "baseline": baseline,
            "phase": child["phase"],
            "status": child["status"],
        }
        record.update(
            {
                "head": baseline,
                "branch": branch,
            }
        )
        cast("dict[str, str]", state["child_runs"])[entry_id] = str(child["run_id"])
        _goal_record(
            state,
            "PARALLEL_CHILD_STARTED",
            lane=lane,
            entry=entry_id,
            task_run_id=child["run_id"],
            baseline=baseline,
        )
    if (
        not state.get("remaining_entries")
        and not active
        and not state.get("integration_queue")
    ):
        return _finalize_parallel_goal(cfg, state)
    save_goal_state(cfg, state)
    return state


def _validate_parallel_goal_state(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    """Validate frozen Goal authority before any parallel state transition."""
    _ensure_runtime_policy_unchanged(cfg, state)
    if state.get("scope_fingerprint") and scope_fingerprint(
        state.get("goal_scope", {})
    ) != state.get("scope_fingerprint"):
        raise OrchestratorError("Frozen Goal scope changed after activation.")
    if state.get("status") == "CANCELLED":
        raise OrchestratorError("A CANCELLED Goal cannot be resumed.")
    if state.get("status") == "BLOCKED":
        raise OrchestratorError(
            f"Goal is BLOCKED: {state.get('blocked_reason')}. "
            "Resolve the recorded cause before resuming parallel work."
        )


def _finalize_parallel_goal(  # noqa: PLR0911
    cfg: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    """Accept a reconciled parallel Goal and remove only clean lane worktrees."""
    if state.get("active_children") or state.get("remaining_entries"):
        raise OrchestratorError(
            "Parallel Goal cannot finalize while child work remains."
        )
    if state.get("integration_queue") or state.get("integration_owner"):
        raise OrchestratorError("Parallel Goal cannot finalize during integration.")
    if state.get("path_leases"):
        return _block_goal(cfg, state, "FINAL_PATH_LEASES_REMAIN")
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
    try:
        records = list(cast("dict[str, dict[str, Any]]", state["worktrees"]).values())
        for record in records:
            lane_repo = Path(str(record["path"]))
            if _git_ok(lane_repo, "status", "--porcelain"):
                return _block_goal(
                    cfg,
                    state,
                    "FINAL_WORKTREE_CLEANUP_FAILED",
                    detail=f"Lane worktree is dirty: {lane_repo}",
                )
        for record in records:
            remove_clean_lane_worktree(
                repo, Path(str(record["path"])), str(state["goal_run_id"])
            )
    except WorktreeError as exc:
        return _block_goal(cfg, state, "FINAL_WORKTREE_CLEANUP_FAILED", detail=str(exc))
    state["worktrees"] = {}
    state["status"] = "ACCEPTED"
    state["blocked_reason"] = None
    _goal_record(
        state,
        "GOAL_ACCEPTED",
        completed=len(cast("list[Any]", state["completed_entries"])),
        parallelism=3,
    )
    save_goal_state(cfg, state)
    return state


def _advance_parallel_goal(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    lane: str | None = None,
    approved: bool = False,
    reject_feedback: str | None = None,
    commit_approved: bool = False,
    commit_reject_feedback: str | None = None,
    role_complete: bool = False,
    app_agent_id: str | None = None,
    **_unused: Any,
) -> dict[str, Any]:
    """Advance exactly one selected lane and preserve every other child."""
    _validate_parallel_goal_state(cfg, state)
    if state.get("status") == "ACCEPTED":
        return state
    actions = any(
        (
            approved,
            reject_feedback,
            commit_approved,
            commit_reject_feedback,
            role_complete,
            app_agent_id,
        )
    )
    if not actions:
        return _dispatch_parallel_children(cfg, state)
    try:
        selected_lane = require_lane(state, lane)
    except ParallelGoalError as exc:
        raise OrchestratorError(str(exc)) from exc
    active = cast("dict[str, dict[str, Any]]", state["active_children"])
    lane_state = active.get(selected_lane)
    if lane_state is None:
        raise OrchestratorError(f"Lane {selected_lane!r} has no active child.")
    lane_cfg = _parallel_lane_cfg(cfg, state, selected_lane)
    child = _load_state(lane_cfg, str(lane_state["run_id"]))
    if (commit_approved or commit_reject_feedback) and not child.get(
        "integration_refreshed"
    ):
        raise OrchestratorError(
            "A parallel draft cannot receive a commit decision before serialized "
            "baseline refresh and final review."
        )
    if approved and child.get("phase") == "approve":
        artifact = parse_next_agent(cast("Path", lane_cfg["next_agent"]))
        allowed_raw = artifact.metadata.get("allowed_write_paths", [])
        deferred_raw = artifact.metadata.get("deferred_integration_paths", [])
        if not isinstance(allowed_raw, list) or not isinstance(deferred_raw, list):
            raise OrchestratorError("Planner path authority metadata is invalid.")
        deferred = [str(path) for path in deferred_raw]
        exclusive = [str(path) for path in allowed_raw if str(path) not in deferred]
        try:
            acquire_child_paths(
                state,
                task_run_id=str(child["run_id"]),
                lane=selected_lane,
                exclusive_paths=exclusive,
                deferred_paths=deferred,
            )
        except ParallelGoalError as exc:
            lane_state["phase"] = "LEASE_BLOCKED"
            lane_state["lease_blocker"] = str(exc)
            save_goal_state(cfg, state)
            return state
        child["deferred_integration_paths"] = deferred
    child = resume_task_run(
        lane_cfg,
        child,
        approved=approved,
        reject_feedback=reject_feedback,
        commit_approved=commit_approved,
        commit_reject_feedback=commit_reject_feedback,
        role_complete=role_complete,
        app_agent_id=app_agent_id,
    )
    lane_state["phase"] = child.get("phase")
    lane_state["status"] = child.get("status")
    if child.get("phase") == "draft_reviewed":
        lane_state["phase"] = "DRAFT_REVIEWED"
        lane_state["draft_review"] = child.get("draft_review")
        try:
            enqueue_reviewed_draft(state, lane=selected_lane)
        except ParallelGoalError as exc:
            raise OrchestratorError(str(exc)) from exc
        lane_state["phase"] = "WAITING_INTEGRATION"
    elif child.get("status") == "ACCEPTED":
        entry_id = str(lane_state["entry"])
        tracker = _current_tracker_entries(cfg, state).get(entry_id)
        if tracker is None or not is_entry_complete(tracker):
            return _block_goal(
                cfg,
                state,
                "PARALLEL_CHILD_TRACKER_RECONCILIATION_FAILED",
                lane=selected_lane,
                entry=entry_id,
            )
        accepted_head = _git_ok(cast("Path", cfg["repo"]), "rev-parse", "HEAD")
        state.setdefault("children", []).append(
            {
                "entry": entry_id,
                "task_run_id": child["run_id"],
                "task_id": child["task"]["task_id"],
                "lane": selected_lane,
                "status": "ACCEPTED",
                "baseline": child.get("integration_baseline", child["baseline"]),
                "accepted_head": accepted_head,
            }
        )
        state.setdefault("completed_entries", []).append(entry_id)
        state["remaining_entries"] = [
            value for value in state["remaining_entries"] if value != entry_id
        ]
        state["integration_queue"] = [
            item
            for item in state.get("integration_queue", [])
            if item.get("task_run_id") != child["run_id"]
        ]
        state["integration_owner"] = None
        try:
            release_child(state, lane=selected_lane, accepted=True)
        except ParallelGoalError as exc:
            raise OrchestratorError(str(exc)) from exc
        _goal_record(
            state,
            "PARALLEL_CHILD_ACCEPTED",
            lane=selected_lane,
            entry=entry_id,
            task_run_id=child["run_id"],
            commit=accepted_head,
        )
    save_goal_state(cfg, state)
    return _dispatch_parallel_children(cfg, state)


def integrate_parallel_draft(
    cfg: dict[str, Any], state: dict[str, Any], *, lane: str
) -> dict[str, Any]:
    """Refresh the head reviewed draft and prepare its fresh final review."""
    _validate_parallel_goal_state(cfg, state)
    if state.get("status") == "ACCEPTED":
        return state
    try:
        lane = require_lane(state, lane)
    except ParallelGoalError as exc:
        raise OrchestratorError(str(exc)) from exc
    queue = cast("list[dict[str, Any]]", state.get("integration_queue", []))
    if not queue:
        raise OrchestratorError("Parallel Goal integration queue is empty.")
    if str(queue[0].get("lane")) != lane:
        raise OrchestratorError(
            f"Lane {lane!r} is not the deterministic integration queue head."
        )
    active = cast("dict[str, dict[str, Any]]", state["active_children"])
    lane_state = active.get(lane)
    if lane_state is None or lane_state.get("phase") != "WAITING_INTEGRATION":
        raise OrchestratorError("Lane has no reviewed draft waiting for integration.")
    primary_repo = cast("Path", cfg["repo"])
    if _git_ok(primary_repo, "branch", "--show-current") != str(cfg["main_branch"]):
        raise OrchestratorError(
            "Primary repository must remain on main for integration."
        )
    if _git_ok(primary_repo, "status", "--porcelain"):
        raise OrchestratorError("Primary main must be clean for integration.")
    lane_cfg = _parallel_lane_cfg(cfg, state, lane)
    lane_repo = cast("Path", lane_cfg["repo"])
    child = _load_state(lane_cfg, str(lane_state["run_id"]))
    draft = cast("dict[str, Any]", child.get("draft_review") or {})
    if child.get("phase") != "draft_reviewed" or not draft:
        raise OrchestratorError("Lane Task state lacks reviewed-draft evidence.")
    if _worktree_fingerprint(lane_repo) != draft.get("worktree_sha256"):
        raise OrchestratorError("Reviewed draft changed while waiting for integration.")
    approved = [str(path) for path in child.get("approved_write_paths", [])]
    deferred = [str(path) for path in child.get("deferred_integration_paths", [])]
    integration_baseline = _git_ok(primary_repo, "rev-parse", "HEAD")
    overlap = refresh_overlap(
        primary_repo,
        draft_baseline=str(child["baseline"]),
        integration_baseline=integration_baseline,
        draft_paths=set(approved),
    )
    requires_replan = bool(overlap or deferred)
    lock_path = (
        primary_repo
        / ".agents"
        / "goals"
        / str(state["goal_run_id"])
        / "integration.lock"
    )
    try:
        with IntegrationLock(lock_path, str(child["run_id"])):
            evidence = archive_draft(
                primary_repo,
                lane_repo,
                goal_run_id=str(state["goal_run_id"]),
                task_run_id=str(child["run_id"]),
                approved_paths=approved,
                coordination_paths=[
                    ".agents/task/planner.md",
                    ".agents/task/executor.md",
                    ".agents/task/reviewer.md",
                    ".agents/task/next-agent.md",
                ],
            )
            refresh_number = int(child.get("refresh_number", 0)) + 1
            refreshed_branch = f"{child['branch']}-r{refresh_number}"
            refresh = refresh_archived_draft(
                lane_repo,
                archive_path=primary_repo / str(evidence["archive"]),
                archive_sha256=str(evidence["archive_sha256"]),
                integration_baseline=integration_baseline,
                refreshed_branch=refreshed_branch,
                replay_implementation=not requires_replan,
            )
    except IntegrationError as exc:
        raise OrchestratorError(str(exc)) from exc
    child["planning_baseline"] = child["baseline"]
    child["planning_branch"] = child["branch"]
    child["baseline"] = integration_baseline
    child["integration_baseline"] = integration_baseline
    child["branch"] = refreshed_branch
    child["refresh_number"] = refresh_number
    child["integration_refreshed"] = True
    child["primary_repo_path"] = str(primary_repo)
    child["refresh_evidence"] = {
        "archive_sha256": evidence["archive_sha256"],
        **refresh,
    }
    _attach_task_packet(lane_cfg, child)
    if requires_replan:
        child["iteration"] = int(child["iteration"]) + 1
        child["integration_refreshed"] = False
        child["correction_context"] = (
            "Serialized integration refresh requires a new complete dry run on "
            f"baseline {integration_baseline}. Reconcile upstream overlaps "
            f"{sorted(overlap)} and implement deferred paths {deferred}. The prior "
            "draft is archived evidence only and was not replayed."
        )
        child["phase"] = "planner"
        state["path_leases"] = release_leases(
            cast("dict[str, dict[str, str]]", state.get("path_leases", {})),
            str(child["run_id"]),
        )
        state["integration_queue"] = [
            item
            for item in state.get("integration_queue", [])
            if item.get("task_run_id") != child["run_id"]
        ]
        _write_orchestrator_planner_prompt(lane_cfg, child, "INTEGRATION_REPLAN")
        _save_state(lane_cfg, child)
        lane_state.update(
            {
                "phase": "RECONCILING",
                "branch": refreshed_branch,
                "integration_baseline": integration_baseline,
                "refresh_evidence": child["refresh_evidence"],
            }
        )
        _goal_record(
            state,
            "INTEGRATION_REPLAN_REQUIRED",
            lane=lane,
            entry=lane_state["entry"],
            overlap=sorted(overlap),
            deferred_paths=deferred,
        )
        save_goal_state(cfg, state)
        return state
    child["phase"] = "reviewer"
    transition = _transition_for(
        lane_cfg["transitions"], "ORCHESTRATOR", "BASELINE_REFRESHED"
    )
    body = compose_prompt(
        lane_cfg["templates"]["reviewer"], _build_fields(child, lane_cfg)
    )
    metadata = {
        "prompt_schema_version": SCHEMA_VERSION,
        "run_id": child["run_id"],
        "task_id": child["task"]["task_id"],
        "iteration": child["iteration"],
        "source_role": "ORCHESTRATOR",
        "target_role": "REVIEWER",
        "handoff": "BASELINE_REFRESHED",
        "branch": refreshed_branch,
        "baseline_commit": integration_baseline,
        "source_head": integration_baseline,
        "template_path": transition.target_template,
        "requires_owner_gate": False,
        "owner_gate": "",
    }
    lane_cfg["next_agent"].write_text(
        _render_next_agent(metadata, body), encoding="utf-8"
    )
    validate_next_agent(
        lane_cfg,
        child,
        expected_source="ORCHESTRATOR",
        expected_handoff="BASELINE_REFRESHED",
    )
    _save_state(lane_cfg, child)
    lane_state.update(
        {
            "phase": "FINAL_REVIEW",
            "branch": refreshed_branch,
            "integration_baseline": integration_baseline,
            "refresh_evidence": child["refresh_evidence"],
        }
    )
    state["integration_owner"] = str(child["run_id"])
    save_goal_state(cfg, state)
    return state


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


def advance_goal(  # noqa: PLR0911
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    approved: bool = False,
    reject_feedback: str | None = None,
    commit_approved: bool = False,
    commit_reject_feedback: str | None = None,
    resolve_planner_blocker: str | None = None,
    stop_after_current_child: bool = False,
    claim_child_chat: str | None = None,
    role_complete: bool = False,
    app_agent_id: str | None = None,
    lane: str | None = None,
) -> dict[str, Any]:
    """Advance a Goal until completion or the active child requires external action."""
    if is_parallel_state(state):
        return _advance_parallel_goal(
            cfg,
            state,
            lane=lane,
            approved=approved,
            reject_feedback=reject_feedback,
            commit_approved=commit_approved,
            commit_reject_feedback=commit_reject_feedback,
            role_complete=role_complete,
            app_agent_id=app_agent_id,
        )
    _ensure_runtime_policy_unchanged(cfg, state)
    if state.get("scope_fingerprint") and scope_fingerprint(
        state.get("goal_scope", {})
    ) != state.get("scope_fingerprint"):
        raise OrchestratorError("Frozen Goal scope changed after activation.")
    if state.get("status") == "CANCELLED":
        raise OrchestratorError("A CANCELLED Goal cannot be resumed.")
    if state.get("status") == "ACCEPTED":
        return state
    if state.get("status") == "BLOCKED":
        raise OrchestratorError(
            f"Goal is BLOCKED: {state.get('blocked_reason')}. "
            "Resolve the recorded cause before creating a replacement Goal run."
        )
    if (
        state.get("child_chat_handoff") is not None
        and claim_child_chat is not None
        and any(
            (
                approved,
                reject_feedback,
                commit_approved,
                commit_reject_feedback,
                resolve_planner_blocker,
                role_complete,
                app_agent_id,
            )
        )
    ):
        raise OrchestratorError(
            "A solo child-chat claim cannot relay role completions, owner gates, "
            "feedback, or app-agent identity into the next child."
        )
    if not _claim_solo_child_chat(cfg, state, claim_child_chat):
        return state
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
                    approved=approved,
                    reject_feedback=reject_feedback,
                    commit_approved=commit_approved,
                    commit_reject_feedback=commit_reject_feedback,
                    role_complete=role_complete,
                    app_agent_id=app_agent_id,
                )
                approved = False
                reject_feedback = None
                commit_approved = False
                commit_reject_feedback = None
                role_complete = False
                app_agent_id = None
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
                if _require_solo_child_chat(cfg, state, child):
                    return state
                if stop_after_current_child:
                    return state
                continue
            if child.get("phase") == "planner_blocked":
                if _apply_unattended_assumption_retry(cfg, state, active, child):
                    continue
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
            approved=approved,
            reject_feedback=reject_feedback,
            commit_approved=commit_approved,
            commit_reject_feedback=commit_reject_feedback,
            role_complete=role_complete,
            app_agent_id=app_agent_id,
        )
        approved = False
        reject_feedback = None
        commit_approved = False
        commit_reject_feedback = None
        role_complete = False
        app_agent_id = None
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
            if _require_solo_child_chat(cfg, state, child):
                return state
            continue
        if child.get("phase") == "planner_blocked":
            if _apply_unattended_assumption_retry(cfg, state, active, child):
                continue
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
    policy = cfg.get("runtime_policy")
    if isinstance(policy, RuntimePolicy) and policy.legacy_compatibility:
        raise OrchestratorError(
            "Missing-schema run configuration is continuation-only. Run "
            ".agents/configure.py before starting a new Task or Goal."
        )
    _entry_gate(cfg)
    _ensure_no_running_goal(cfg)
    state = create_goal_state(cfg, spec)
    if is_parallel_state(state):
        baseline = _git_ok(cast("Path", cfg["repo"]), "rev-parse", "HEAD")
        try:
            records = create_lane_worktrees(
                cast("Path", cfg["repo"]),
                goal_run_id=str(state["goal_run_id"]),
                lanes=[str(lane) for lane in state["lane_names"]],
                baseline=baseline,
            )
        except (ParallelGoalError, RuntimeError) as exc:
            return _block_goal(
                cfg, state, "WORKTREE_INITIALIZATION_FAILED", detail=str(exc)
            )
        state["worktrees"] = {
            lane: record.to_dict() for lane, record in records.items()
        }
        _goal_record(state, "PARALLEL_WORKTREES_CREATED", baseline=baseline)
        save_goal_state(cfg, state)
        return _dispatch_parallel_children(cfg, state)
    return advance_goal(cfg, state, **router_args)


def migrate_goal_to_parallel(
    cfg: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    """Explicitly migrate one inactive sequential Goal to three-lane state."""
    if is_parallel_state(state):
        raise OrchestratorError("Goal is already parallel.")
    if state.get("status") != "RUNNING" or state.get("active_child") is not None:
        raise OrchestratorError(
            "Parallel migration requires a RUNNING Goal with no active child."
        )
    policy = cfg.get("runtime_policy")
    if (
        not isinstance(policy, RuntimePolicy)
        or policy.schema_version < 4
        or not policy.parallel.enabled
    ):
        raise OrchestratorError(
            "Parallel migration requires an enabled schema-v4 parallel policy."
        )
    repo = cast("Path", cfg["repo"])
    if _git_ok(repo, "branch", "--show-current") != str(cfg["main_branch"]):
        raise OrchestratorError("Parallel migration requires the primary main branch.")
    if _git_ok(repo, "status", "--porcelain"):
        raise OrchestratorError("Parallel migration requires clean main.")
    for path in [*cfg["journals"].values(), cfg["next_agent"]]:
        if not path.exists() or path.stat().st_size != 0:
            raise OrchestratorError(
                "Parallel migration requires an empty active Task workspace."
            )
    tracker_entries = _current_tracker_entries(cfg, state)
    resolved = [str(value) for value in state["resolved_entries"]]
    missing = [entry for entry in resolved if entry not in tracker_entries]
    if missing:
        raise OrchestratorError(f"Goal tracker entries disappeared: {missing}")
    completed = [
        entry for entry in resolved if is_entry_complete(tracker_entries[entry])
    ]
    recorded_completed = {str(value) for value in state.get("completed_entries", [])}
    if not recorded_completed.issubset(set(completed)):
        raise OrchestratorError(
            "Goal completion ledger contradicts the canonical tracker."
        )
    before = hashlib.sha256(
        json.dumps(state, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    schedule_path = repo / "docs/dev/evidence/dependency-schedule.json"
    migrated = create_parallel_state(
        state,
        lanes=list(policy.parallel.lane_names),
        schedule_path=schedule_path,
    )
    migrated["dependency_schedule"] = "docs/dev/evidence/dependency-schedule.json"
    migrated["completed_entries"] = completed
    migrated["remaining_entries"] = [
        entry for entry in resolved if entry not in set(completed)
    ]
    migrated["runtime_policy_fingerprint"] = policy.fingerprint
    migrated["runtime_policy_schema_version"] = policy.schema_version
    migrated["runtime_mode"] = policy.effective_mode
    baseline = _git_ok(repo, "rev-parse", "HEAD")
    records = create_lane_worktrees(
        repo,
        goal_run_id=str(migrated["goal_run_id"]),
        lanes=list(policy.parallel.lane_names),
        baseline=baseline,
    )
    migrated["worktrees"] = {lane: record.to_dict() for lane, record in records.items()}
    after_payload = {
        "parallelism": 3,
        "completed_entries": completed,
        "remaining_entries": migrated["remaining_entries"],
        "baseline": baseline,
    }
    migrated["migration_ledger"] = [
        {
            "source_state_sha256": before,
            "result_scope_sha256": scope_fingerprint(after_payload),
            "baseline": baseline,
            "reconciled_completed_entries": completed,
            "migrated_at": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
        }
    ]
    _goal_record(migrated, "GOAL_MIGRATED_TO_PARALLEL", baseline=baseline)
    save_goal_state(cfg, migrated)
    return _dispatch_parallel_children(cfg, migrated)


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
    if is_parallel_state(state):
        active_lanes = cast(
            "dict[str, dict[str, Any]]", state.get("active_children", {})
        )
        lines = [
            f"GOAL : {state.get('status', 'UNKNOWN')}",
            f"GOAL_ID : {state.get('goal_id', '')}",
            f"GOAL_RUN_ID : {state.get('goal_run_id', '')}",
            f"PROGRESS : {len(completed)} / {len(resolved)}",
            "MODE : PARALLEL-3",
        ]
        for lane in [str(value) for value in state.get("lane_names", [])]:
            child = active_lanes.get(lane)
            if child:
                lines.append(
                    f"LANE {lane} : {child.get('entry')} / {child.get('phase')}"
                )
            else:
                lines.append(f"LANE {lane} : IDLE")
        queue = cast("list[dict[str, Any]]", state.get("integration_queue", []))
        lines.append(
            "INTEGRATION_QUEUE : "
            + (", ".join(str(item["entry"]) for item in queue) if queue else "EMPTY")
        )
        lines.append("REMAINING : " + (", ".join(remaining) if remaining else "NONE"))
        if state.get("blocked_reason"):
            lines.append(f"BLOCKED_REASON : {state['blocked_reason']}")
        return "\n".join(lines)
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
    assumption_ledger = cast("list[Any]", state.get("assumption_ledger", []))
    lines.append(f"ASSUMPTIONS_FOR_HUMAN_REVIEW : {len(assumption_ledger)}")
    if state.get("blocked_reason"):
        lines.append(f"BLOCKED_REASON : {state['blocked_reason']}")
    handoff = state.get("child_chat_handoff")
    if isinstance(handoff, dict):
        goal_run_id = str(state.get("goal_run_id", ""))
        handoff_id = str(handoff.get("handoff_id", ""))
        resume = (
            "uv run .agents/orchestrator.py goal-resume "
            f"--goal-run-id {goal_run_id} --claim-child-chat {handoff_id}"
        )
        prompt = (
            f"Continue HaruQuantAI Goal {goal_run_id} in this fresh solo child "
            f"Task chat. Repository state is authoritative. Run: {resume}"
        )
        lines.extend(
            [
                "NEXT_CHILD_CHAT : REQUIRED",
                f"NEXT_CHILD : {handoff.get('next_entry', '')}",
                f"CHILD_CHAT_HANDOFF_ID : {handoff_id}",
                f"PRIMARY_NEW_CHAT_ACTION : {SOLO_CHILD_CHAT_PRIMARY}",
                f"AUTOMATIC_FALLBACK : {SOLO_CHILD_CHAT_FALLBACK}",
                f"NEXT_CHAT_PROMPT : {prompt}",
                f"RESUME_COMMAND : {resume}",
            ]
        )
    return "\n".join(lines)


__all__ = [name for name in globals() if not name.startswith("__")]
