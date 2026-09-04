#!/usr/bin/env python3
"""Deterministic Goal supervision above the existing HaruQuantAI Task workflow."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_task import build_task_spec, is_entry_complete, parse_entries
from runtime_policy import RuntimePolicy, scope_fingerprint
from task_api import (
    apply_planner_blocker_resolution,
    prepare_task_run,
    resume_task_run,
)
from workflow_protocol import OrchestratorError, _git_ok
from workflow_runtime import (
    _ensure_runtime_policy_unchanged,
    _entry_gate,
    _load_state,
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
) -> dict[str, Any]:
    """Advance a Goal until completion or the active child requires external action."""
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
