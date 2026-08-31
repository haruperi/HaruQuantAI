#!/usr/bin/env python3
"""Reusable Task-run API layered over the existing HaruQuantAI Task engine."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from runtime_policy import RuntimePolicy, scope_fingerprint
from workflow_engine import TASK_REQUIRED, router
from workflow_protocol import (
    ROLE_INTRINSIC_PATHS,
    SLUG_RE,
    OrchestratorError,
    ScopeMutationError,
    _git_ok,
    _normalize_path_list,
    _render_next_agent,
    _resolve_handoff,
    _sha_file,
    _transition_for,
    _worktree_fingerprint,
    compose_prompt,
    latest_handoff_block,
    parse_next_agent,
    validate_next_agent,
)
from workflow_runtime import (
    _build_fields,
    _entry_gate,
    _record,
    _save_state,
    _write_orchestrator_planner_prompt,
)

RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SCOPE_BLOCKER_REASON = (
    "Executor produced repository mutations outside Planner-approved scope."
)
LEGACY_COORDINATION_PATHS = set().union(*ROLE_INTRINSIC_PATHS.values())


def _validate_run_id(run_id: str) -> str:
    """Return a filesystem-safe Task run id or fail closed.

    Args:
        run_id: Candidate Task workflow run identifier.

    Returns:
        The validated identifier unchanged.

    Raises:
        OrchestratorError: If the identifier could escape the runtime state directory.
    """
    if not RUN_ID_RE.fullmatch(run_id):
        raise OrchestratorError(
            "run_id must start with an alphanumeric character and contain only "
            "letters, digits, '.', '_', or '-'."
        )
    return run_id


def create_task_state(
    task: dict[str, Any],
    baseline: str,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Create the canonical initial state for one atomic Task workflow run."""
    missing = [key for key in TASK_REQUIRED if not task.get(key)]
    if missing:
        raise OrchestratorError(f"Missing task fields: {missing}")
    task_slug = str(task["task_slug"])
    if not SLUG_RE.fullmatch(task_slug):
        raise OrchestratorError("task_slug must be lowercase filesystem-safe text.")
    if run_id is None:
        stamp = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%d-%H%M%S")
        run_id = f"{stamp}-{task_slug}"
    run_id = _validate_run_id(run_id)
    return {
        "run_id": run_id,
        "task": task,
        "baseline": baseline,
        "branch": None,
        "iteration": 1,
        "phase": "task_activation",
        "status": "RUNNING",
        "owner_feedback": "",
        "correction_context": "None",
        "blockers": [],
        "history": [],
        "next_agent": None,
        "session_generation": "normal",
        "recovery_generation": 0,
    }


def prepare_task_run(
    cfg: dict[str, Any],
    task: dict[str, Any],
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Pass the clean-main entry gate, create Task state, and persist it."""
    policy = cfg.get("runtime_policy")
    if isinstance(policy, RuntimePolicy) and policy.legacy_compatibility:
        raise OrchestratorError(
            "Missing-schema run configuration is continuation-only. Run "
            ".agents/configure.py before starting a new Task or Goal."
        )
    baseline = _entry_gate(cfg)
    state = create_task_state(task, baseline, run_id=run_id)
    if isinstance(policy, RuntimePolicy):
        state["runtime_policy_fingerprint"] = policy.fingerprint
        state["runtime_policy_schema_version"] = policy.schema_version
        state["runtime_mode"] = policy.effective_mode
        state["approval_policy"] = policy.approval_policy
        state["effective_max_iterations"] = policy.max_iterations
        state["scope_fingerprint"] = scope_fingerprint(task)
    _save_state(cfg, state)
    return state


def resume_task_run(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    approved: bool = False,
    reject_feedback: str | None = None,
    commit_approved: bool = False,
    commit_reject_feedback: str | None = None,
    role_complete: bool = False,
    app_agent_id: str | None = None,
) -> dict[str, Any]:
    """Run the existing Task state machine without changing its semantics."""
    return router(
        cfg,
        state,
        approved=approved,
        reject_feedback=reject_feedback,
        commit_approved=commit_approved,
        commit_reject_feedback=commit_reject_feedback,
        role_complete=role_complete,
        app_agent_id=app_agent_id,
    )


def apply_planner_blocker_resolution(
    cfg: dict[str, Any],
    state: dict[str, Any],
    evidence: str,
    *,
    source: str = "OWNER_MESSAGE",
) -> None:
    """Record truthful evidence that authorizes an active Planner retry."""
    if state.get("phase") != "planner_blocked":
        raise OrchestratorError(
            "Planner blocker resolution is valid only while the Task is planner_blocked."
        )
    if not evidence.strip():
        raise OrchestratorError(
            "Planner blocker resolution evidence must not be empty."
        )
    state["blocker_resolution"] = {
        "evidence": evidence.strip(),
        "source": source,
        "resolved_at": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
    }
    _save_state(cfg, state)


def _current_worktree_paths(repo: Path) -> set[str]:
    """Return changed/untracked paths used to reconstruct a failed role delta."""
    paths: set[str] = set()
    for args in (
        ("diff", "--name-only", "HEAD"),
        ("diff", "--cached", "--name-only", "HEAD"),
        ("ls-files", "--others", "--exclude-standard"),
    ):
        paths.update(filter(None, _git_ok(repo, *args).splitlines()))
    return {path.replace("\\", "/") for path in paths}


def _validate_scope_recovery_sessions(
    cfg: dict[str, Any], state: dict[str, Any]
) -> None:
    """Require the existing P/E ledger and absence of a Reviewer session."""
    ledger_path = (
        Path(cfg["repo"])
        / ".agents"
        / "runs"
        / str(state["run_id"])
        / "role-sessions.json"
    )
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid role-session ledger: {exc}") from exc
    sessions = ledger.get("sessions") if isinstance(ledger, dict) else None
    if not isinstance(sessions, dict):
        raise OrchestratorError("Role-session ledger has invalid sessions data.")
    if set(sessions) != {"PLANNER", "EXECUTOR"}:
        raise OrchestratorError(
            "Scope recovery requires existing Planner/Executor sessions and no Reviewer session."
        )
    ids = [
        str(sessions[role].get("session_id", "")) for role in ("PLANNER", "EXECUTOR")
    ]
    if not all(ids) or len(set(ids)) != 2:
        raise OrchestratorError("Scope recovery role-session identities are invalid.")


def _validate_planner_handoff_sessions(
    cfg: dict[str, Any], state: dict[str, Any], expected_planner_session_id: str
) -> None:
    """Require the exact Planner session and no downstream role sessions."""
    ledger_path = (
        Path(cfg["repo"])
        / ".agents"
        / "runs"
        / str(state["run_id"])
        / "role-sessions.json"
    )
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid role-session ledger: {exc}") from exc
    sessions = ledger.get("sessions") if isinstance(ledger, dict) else None
    if not isinstance(sessions, dict) or set(sessions) != {"PLANNER"}:
        raise OrchestratorError(
            "Planner-handoff recovery requires exactly one Planner session and no "
            "Executor or Reviewer session."
        )
    planner = sessions.get("PLANNER")
    if not isinstance(planner, dict) or str(planner.get("session_id", "")) != str(
        expected_planner_session_id
    ):
        raise OrchestratorError("Planner session identity mismatch.")


def _validate_later_planner_handoff_sessions(
    cfg: dict[str, Any], state: dict[str, Any], expected_planner_session_id: str
) -> None:
    """Require exact established role sessions before a later Planner recovery."""
    ledger_path = (
        Path(cfg["repo"])
        / ".agents"
        / "runs"
        / str(state["run_id"])
        / "role-sessions.json"
    )
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid role-session ledger: {exc}") from exc
    sessions = ledger.get("sessions") if isinstance(ledger, dict) else None
    if not isinstance(sessions, dict) or set(sessions) != {
        "PLANNER",
        "EXECUTOR",
        "REVIEWER",
    }:
        raise OrchestratorError(
            "Later Planner-handoff recovery requires the established P/E/R sessions."
        )
    iteration = int(state["iteration"])
    planner = sessions["PLANNER"]
    if (
        not isinstance(planner, dict)
        or str(planner.get("session_id", "")) != str(expected_planner_session_id)
        or int(planner.get("last_iteration", 0)) != iteration
    ):
        raise OrchestratorError("Planner session identity or iteration mismatch.")
    for role in ("EXECUTOR", "REVIEWER"):
        session = sessions[role]
        if (
            not isinstance(session, dict)
            or int(session.get("last_iteration", 0)) >= iteration
        ):
            raise OrchestratorError(
                f"{role.title()} session is already at or beyond Planner iteration."
            )


def _latest_allowed_write_paths(journal_text: str) -> list[str]:
    """Extract the final canonical Planner path-authority block."""
    matches = re.findall(
        r"(?ms)^ALLOWED_WRITE_PATHS:\s*\n(.*?)^END_ALLOWED_WRITE_PATHS:\s*$",
        journal_text,
    )
    if not matches:
        raise OrchestratorError("Planner journal lacks ALLOWED_WRITE_PATHS authority.")
    raw_paths = [
        line.removeprefix("- ").strip()
        for line in matches[-1].splitlines()
        if line.strip()
    ]
    if not raw_paths or any(
        not line.startswith("- ") for line in matches[-1].splitlines() if line.strip()
    ):
        raise OrchestratorError("Planner ALLOWED_WRITE_PATHS block is malformed.")
    return _normalize_path_list(raw_paths)


def recover_planner_handoff(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    expected_run_id: str,
    expected_planner_session_id: str,
    expected_worktree_fingerprint: str,
) -> None:
    """Adopt an already-returned, validated Planner-to-Executor handoff.

    This recovery exists for the narrow boundary where Planner completed and
    replaced ``next-agent.md``, but deterministic validation failed before the
    Planner history/phase update was persisted.  It validates existing artifacts
    and records that completed boundary without invoking any reasoning role or
    rewriting either artifact.
    """
    repo = Path(cfg["repo"])
    if state.get("status") != "RUNNING" or state.get("phase") != "planner":
        raise OrchestratorError(
            "Planner-handoff recovery requires a RUNNING Task in planner phase."
        )
    if str(state.get("run_id")) != expected_run_id:
        raise OrchestratorError("Planner-handoff recovery Task run identity mismatch.")
    iteration = int(state.get("iteration", 0))
    if iteration < 1:
        raise OrchestratorError("Planner-handoff recovery iteration is invalid.")
    if _git_ok(repo, "branch", "--show-current") != state.get("branch"):
        raise OrchestratorError("Planner-handoff recovery Task branch mismatch.")
    if _git_ok(repo, "rev-parse", "HEAD") != state.get("baseline"):
        raise OrchestratorError(
            "Planner-handoff recovery requires the unchanged Task baseline HEAD."
        )
    current_fingerprint = _worktree_fingerprint(repo)
    if current_fingerprint != expected_worktree_fingerprint:
        raise OrchestratorError(
            "Planner-handoff recovery worktree fingerprint mismatch."
        )
    if iteration == 1:
        changed_paths = {
            path
            for path in _current_worktree_paths(repo)
            if not path.startswith((".agents/runs/", ".agents/goals/", ".agents/logs/"))
            and path != ".agents/workflow.lock"
        }
        planner_paths = set(ROLE_INTRINSIC_PATHS["PLANNER"])
        if changed_paths != planner_paths:
            raise OrchestratorError(
                "Planner-handoff recovery requires exactly the Planner journal and "
                "Executor prompt changes; found: " + ", ".join(sorted(changed_paths))
            )
        _validate_planner_handoff_sessions(cfg, state, expected_planner_session_id)
    else:
        _validate_later_planner_handoff_sessions(
            cfg, state, expected_planner_session_id
        )

    journal = Path(cfg["journals"]["planner"])
    prompt = Path(cfg["next_agent"])
    journal_before = journal.read_bytes()
    prompt_before = prompt.read_bytes()
    if not journal_before or not prompt_before:
        raise OrchestratorError(
            "Planner handoff journal or Executor prompt is missing."
        )
    block = _resolve_handoff(journal, "", "PLANNER", {"PENDING_APPROVAL"})
    if block["handoff"] != "PENDING_APPROVAL":
        raise OrchestratorError("Planner journal lacks the current approval handoff.")

    plan_hash = _sha_file(journal)
    artifact = parse_next_agent(prompt)
    if iteration > 1 and "allowed_write_paths" not in artifact.metadata:
        metadata = dict(artifact.metadata)
        metadata["allowed_write_paths"] = _latest_allowed_write_paths(
            journal_before.decode("utf-8")
        )
        prompt.write_text(_render_next_agent(metadata, artifact.body), encoding="utf-8")
        artifact = parse_next_agent(prompt)
    artifact = validate_next_agent(
        cfg, state, expected_source="PLANNER", expected_handoff="PENDING_APPROVAL"
    )
    prompt_plan_hashes = re.findall(
        r"(?m)^Approved plan hash:\s*`([0-9a-f]{64})`\s*$", artifact.body
    )
    if prompt_plan_hashes != [plan_hash]:
        raise OrchestratorError(
            "Planner journal changed after the Executor handoff was produced."
        )
    if journal.read_bytes() != journal_before:
        raise OrchestratorError("Planner-handoff recovery mutated the Planner journal.")
    if iteration == 1 and prompt.read_bytes() != prompt_before:
        raise OrchestratorError("Planner-handoff recovery mutated role artifacts.")

    state["plan_hash"] = plan_hash
    _record(state, "planner", handoff="PENDING_APPROVAL", recovered=True)
    state["phase"] = "approve"
    _save_state(cfg, state)


def materialize_executor_handoff_correction(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    expected_run_id: str,
    expected_executor_session_id: str,
    expected_worktree_fingerprint: str,
) -> None:
    """Materialize a same-session Executor prompt for a missing terminal handoff."""
    repo = Path(cfg["repo"])
    if state.get("status") != "RUNNING" or state.get("phase") != "executor":
        raise OrchestratorError(
            "Executor handoff correction requires a RUNNING Task in executor phase."
        )
    if state.get("run_id") != expected_run_id or int(state.get("iteration", 0)) < 1:
        raise OrchestratorError("Executor handoff correction Task identity mismatch.")
    if _git_ok(repo, "branch", "--show-current") != state.get("branch"):
        raise OrchestratorError("Executor handoff correction branch mismatch.")
    if _git_ok(repo, "rev-parse", "HEAD") != state.get("baseline"):
        raise OrchestratorError("Executor handoff correction HEAD mismatch.")
    if _worktree_fingerprint(repo) != expected_worktree_fingerprint:
        raise OrchestratorError("Executor handoff correction fingerprint mismatch.")

    ledger_path = repo / ".agents/runs" / expected_run_id / "role-sessions.json"
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid role-session ledger: {exc}") from exc
    sessions = ledger.get("sessions") if isinstance(ledger, dict) else None
    if not isinstance(sessions, dict) or not {"PLANNER", "EXECUTOR"}.issubset(sessions):
        raise OrchestratorError(
            "Executor handoff correction requires Planner and Executor sessions."
        )
    unexpected_roles = set(sessions) - {"PLANNER", "EXECUTOR", "REVIEWER"}
    if unexpected_roles:
        raise OrchestratorError(
            "Executor handoff correction found unknown role sessions."
        )
    reviewer = sessions.get("REVIEWER")
    if reviewer is not None and (
        not isinstance(reviewer, dict)
        or int(state["iteration"]) == 1
        or int(reviewer.get("last_iteration", 0)) >= int(state["iteration"])
    ):
        raise OrchestratorError(
            "Executor handoff correction found a Reviewer session at or beyond "
            "the current iteration."
        )
    executor = sessions.get("EXECUTOR")
    if (
        not isinstance(executor, dict)
        or executor.get("session_id") != expected_executor_session_id
    ):
        raise OrchestratorError("Executor session identity mismatch.")

    journal = Path(cfg["journals"]["executor"])
    if not journal.exists() or journal.stat().st_size == 0:
        raise OrchestratorError("Executor report journal is missing.")
    existing_handoff = latest_handoff_block(journal)
    if existing_handoff is not None and (
        existing_handoff.get("stopped") != "EXECUTOR"
        or existing_handoff.get("activating") != "REVIEWER"
        or existing_handoff.get("handoff") != "READY_FOR_REVIEW"
    ):
        raise OrchestratorError("Executor journal has a conflicting terminal handoff.")

    approved_paths = set(state.get("approved_write_paths", []))
    current_paths = {
        path
        for path in _current_worktree_paths(repo)
        if not path.startswith((".agents/runs/", ".agents/goals/", ".agents/logs/"))
        and path != ".agents/workflow.lock"
    }
    allowed_paths = approved_paths | LEGACY_COORDINATION_PATHS
    unauthorized = sorted(current_paths - allowed_paths)
    # At a later correction iteration, retained work from earlier iterations is
    # necessarily outside the latest correction-only approved path set. It has
    # already passed deterministic mutation validation and an earlier Reviewer
    # invocation. A valid current READY_FOR_REVIEW handoff proves the latest
    # Executor invocation also passed mutation validation before prompt parsing
    # failed. The correction invocation itself remains coordination-only.
    prior_review_complete = reviewer is not None and existing_handoff is not None
    if unauthorized and not prior_review_complete:
        raise OrchestratorError(
            "Executor handoff correction found paths outside approved scope: "
            + ", ".join(unauthorized)
        )

    if existing_handoff is None:
        action = (
            "append a new Executor journal terminal block exactly as: STOPPED : "
            "EXECUTOR; ACTIVATING : REVIEWER; HANDOFF : READY_FOR_REVIEW. Then "
        )
    else:
        action = (
            "preserve the existing valid READY_FOR_REVIEW journal handoff without "
            "appending a duplicate. "
        )
    state["correction_context"] = (
        "HANDOFF-ONLY CORRECTION. Preserve every product and documentation byte. "
        "Re-read current Task state and revalidate changed paths against the approved "
        "Planner scope; "
        + action
        + "replace next-agent.md with the complete canonical TOML-front-matter Reviewer "
        "prompt. Do not rewrite historical evidence or change implementation behavior."
    )
    fields = _build_fields(state, cfg)
    body = compose_prompt(Path(cfg["templates"]["executor"]), fields)
    body += (
        "\n\n## Orchestrator handoff-only correction directive\n\n"
        + state["correction_context"]
        + "\n"
    )
    transition = _transition_for(
        cfg["transitions"], "ORCHESTRATOR", "EXECUTOR_HANDOFF_CORRECTION"
    )
    metadata = {
        "prompt_schema_version": 1,
        "run_id": state["run_id"],
        "task_id": state["task"]["task_id"],
        "iteration": state["iteration"],
        "source_role": "ORCHESTRATOR",
        "target_role": "EXECUTOR",
        "handoff": "EXECUTOR_HANDOFF_CORRECTION",
        "branch": state["branch"],
        "baseline_commit": state["baseline"],
        "source_head": _git_ok(repo, "rev-parse", "HEAD"),
        "template_path": transition.target_template,
        "requires_owner_gate": False,
        "owner_gate": "",
    }
    Path(cfg["next_agent"]).write_text(
        _render_next_agent(metadata, body), encoding="utf-8"
    )
    validate_next_agent(
        cfg,
        state,
        expected_source="ORCHESTRATOR",
        expected_handoff="EXECUTOR_HANDOFF_CORRECTION",
    )
    state["executor_handoff_correction"] = {
        "worktree_sha256": expected_worktree_fingerprint,
        "approved_write_paths": sorted(approved_paths),
        "executor_session_id": expected_executor_session_id,
    }
    state["approved_write_paths"] = []
    _record(state, "executor_handoff_correction_materialized")
    _save_state(cfg, state)


def materialize_reviewer_handoff_correction(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    expected_run_id: str,
    expected_reviewer_session_id: str,
    expected_worktree_fingerprint: str,
) -> None:
    """Materialize a same-session Reviewer prompt for an invalid target prompt."""
    repo = Path(cfg["repo"])
    if state.get("status") != "RUNNING" or state.get("phase") != "reviewer":
        raise OrchestratorError(
            "Reviewer handoff correction requires a RUNNING Task in reviewer phase."
        )
    if state.get("run_id") != expected_run_id or int(state.get("iteration", 0)) < 1:
        raise OrchestratorError("Reviewer handoff correction Task identity mismatch.")
    if _git_ok(repo, "branch", "--show-current") != state.get("branch"):
        raise OrchestratorError("Reviewer handoff correction branch mismatch.")
    if _git_ok(repo, "rev-parse", "HEAD") != state.get("baseline"):
        raise OrchestratorError("Reviewer handoff correction HEAD mismatch.")
    if _worktree_fingerprint(repo) != expected_worktree_fingerprint:
        raise OrchestratorError("Reviewer handoff correction fingerprint mismatch.")

    ledger_path = repo / ".agents/runs" / expected_run_id / "role-sessions.json"
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid role-session ledger: {exc}") from exc
    sessions = ledger.get("sessions") if isinstance(ledger, dict) else None
    if not isinstance(sessions, dict) or set(sessions) != {
        "PLANNER",
        "EXECUTOR",
        "REVIEWER",
    }:
        raise OrchestratorError(
            "Reviewer handoff correction requires exact P/E/R sessions."
        )
    reviewer = sessions["REVIEWER"]
    if (
        not isinstance(reviewer, dict)
        or reviewer.get("session_id") != expected_reviewer_session_id
        or int(reviewer.get("last_iteration", 0)) != int(state["iteration"])
    ):
        raise OrchestratorError("Reviewer session identity or iteration mismatch.")

    journal = Path(cfg["journals"]["reviewer"])
    existing_handoff = latest_handoff_block(journal)
    if existing_handoff is None or (
        existing_handoff.get("stopped") != "REVIEWER"
        or existing_handoff.get("handoff")
        not in {"CHANGES_REQUESTED", "PENDING_COMMIT"}
    ):
        raise OrchestratorError("Reviewer journal lacks a valid terminal handoff.")
    handoff = str(existing_handoff["handoff"])
    target = "PLANNER" if handoff == "CHANGES_REQUESTED" else "REVIEWER"
    next_iteration = (
        int(state["iteration"]) + 1
        if handoff == "CHANGES_REQUESTED"
        else int(state["iteration"])
    )
    state["correction_context"] = (
        "HANDOFF-ONLY CORRECTION. Preserve every implementation and journal byte. "
        f"The existing Reviewer handoff is {handoff}. Replace only next-agent.md with "
        f"the complete canonical {target} prompt for iteration {next_iteration}, including "
        "all protected template sentinels and current worktree metadata."
    )
    fields = _build_fields(state, cfg)
    body = compose_prompt(Path(cfg["templates"]["reviewer"]), fields)
    body += (
        "\n\n## Orchestrator handoff-only correction directive\n\n"
        + state["correction_context"]
        + "\n"
    )
    transition = _transition_for(
        cfg["transitions"], "ORCHESTRATOR", "REVIEWER_HANDOFF_CORRECTION"
    )
    metadata = {
        "prompt_schema_version": 1,
        "run_id": state["run_id"],
        "task_id": state["task"]["task_id"],
        "iteration": state["iteration"],
        "source_role": "ORCHESTRATOR",
        "target_role": "REVIEWER",
        "handoff": "REVIEWER_HANDOFF_CORRECTION",
        "branch": state["branch"],
        "baseline_commit": state["baseline"],
        "source_head": _git_ok(repo, "rev-parse", "HEAD"),
        "template_path": transition.target_template,
        "requires_owner_gate": False,
        "owner_gate": "",
    }
    Path(cfg["next_agent"]).write_text(
        _render_next_agent(metadata, body), encoding="utf-8"
    )
    validate_next_agent(
        cfg,
        state,
        expected_source="ORCHESTRATOR",
        expected_handoff="REVIEWER_HANDOFF_CORRECTION",
    )
    _record(state, "reviewer_handoff_correction_materialized", handoff=handoff)
    _save_state(cfg, state)


def recover_max_iterations(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    expected_run_id: str,
    expected_iteration: int,
    expected_worktree_fingerprint: str,
) -> None:
    """Reopen one owner-authorized exact post-review max-iteration correction."""
    repo = Path(cfg["repo"])
    if (
        state.get("status") != "MAX_ITERATIONS"
        or state.get("phase") != "planner"
        or state.get("run_id") != expected_run_id
        or int(state.get("iteration", 0)) != expected_iteration
    ):
        raise OrchestratorError("Max-iteration recovery Task state mismatch.")
    if expected_iteration != int(cfg["max_iterations"]) + 1:
        raise OrchestratorError(
            "Max-iteration recovery requires exactly one iteration beyond the limit."
        )
    if _git_ok(repo, "branch", "--show-current") != state.get("branch"):
        raise OrchestratorError("Max-iteration recovery branch mismatch.")
    if _git_ok(repo, "rev-parse", "HEAD") != state.get("baseline"):
        raise OrchestratorError("Max-iteration recovery HEAD mismatch.")
    if _worktree_fingerprint(repo) != expected_worktree_fingerprint:
        raise OrchestratorError("Max-iteration recovery fingerprint mismatch.")
    artifact = validate_next_agent(
        cfg,
        state,
        expected_source="REVIEWER",
        expected_handoff="CHANGES_REQUESTED",
    )
    if (
        artifact.metadata.get("target_role") != "PLANNER"
        or int(artifact.metadata.get("iteration", 0)) != expected_iteration
    ):
        raise OrchestratorError("Max-iteration recovery Planner prompt mismatch.")
    ledger_path = repo / ".agents/runs" / expected_run_id / "role-sessions.json"
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid role-session ledger: {exc}") from exc
    sessions = ledger.get("sessions") if isinstance(ledger, dict) else None
    if not isinstance(sessions, dict) or set(sessions) != {
        "PLANNER",
        "EXECUTOR",
        "REVIEWER",
    }:
        raise OrchestratorError("Max-iteration recovery requires exact P/E/R sessions.")
    for role in ("PLANNER", "EXECUTOR", "REVIEWER"):
        session = sessions[role]
        if (
            not isinstance(session, dict)
            or int(session.get("last_iteration", 0)) != expected_iteration - 1
        ):
            raise OrchestratorError(
                f"Max-iteration recovery {role} session continuity mismatch."
            )
    state["status"] = "RUNNING"
    _record(
        state,
        "max_iterations_owner_recovery",
        planner_iteration=expected_iteration,
        previous_limit=int(cfg["max_iterations"]),
    )
    _save_state(cfg, state)


def recover_completed_closeout(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    expected_run_id: str,
    expected_iteration: int,
    expected_merge_head: str,
) -> None:
    """Adopt an exact completed close-out whose terminal transport was lost."""
    if (
        state.get("status") != "RUNNING"
        or state.get("phase") != "closeout"
        or state.get("run_id") != expected_run_id
        or int(state.get("iteration", 0)) != expected_iteration
    ):
        raise OrchestratorError("Completed close-out recovery Task state mismatch.")
    repo = Path(cfg["repo"])
    if _git_ok(repo, "rev-parse", "HEAD") != expected_merge_head:
        raise OrchestratorError("Completed close-out recovery merge HEAD mismatch.")
    from workflow_engine import _verify_closeout_lineage

    _verify_closeout_lineage(cfg, state)
    ledger_path = repo / ".agents/runs" / expected_run_id / "role-sessions.json"
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid role-session ledger: {exc}") from exc
    sessions = ledger.get("sessions") if isinstance(ledger, dict) else None
    reviewer = sessions.get("REVIEWER") if isinstance(sessions, dict) else None
    if (
        not isinstance(reviewer, dict)
        or int(reviewer.get("last_iteration", 0)) != expected_iteration
    ):
        raise OrchestratorError("Completed close-out Reviewer continuity mismatch.")
    state["status"] = "ACCEPTED"
    state["phase"] = "done"
    state["next_agent"] = None
    _record(
        state,
        "closeout",
        handoff="ACCEPTED",
        recovered=True,
        merge_head=expected_merge_head,
    )
    _save_state(cfg, state)


def record_scope_blocker(
    cfg: dict[str, Any], state: dict[str, Any], error: ScopeMutationError
) -> None:
    """Persist structured evidence after post-Executor scope validation fails.

    Control flow: the role process has returned successfully, `_invoke_pending`
    has captured the post-role repository delta, and `validate_role_mutations`
    has rejected paths outside `approved_write_paths`. The pending Executor
    artifact is now stale by design; recovery must replace it explicitly rather
    than weakening normal stale-artifact validation.
    """
    if error.role != "EXECUTOR" or state.get("phase") != "executor":
        raise OrchestratorError("Only an active Executor scope failure is recoverable.")
    evidence = {
        "role": error.role,
        "iteration": int(state["iteration"]),
        "offending_paths": list(error.offending_paths),
        "approved_write_paths": list(state.get("approved_write_paths", [])),
        "reason": SCOPE_BLOCKER_REASON,
        "validation_error": str(error),
        "worktree_sha256": _worktree_fingerprint(Path(cfg["repo"])),
    }
    state["scope_blocker"] = evidence
    state.setdefault("blockers", []).append(
        {
            "iteration": int(state["iteration"]),
            "raised_by": "ORCHESTRATOR",
            "status": "OPEN",
            "reason": SCOPE_BLOCKER_REASON,
            "offending_paths": list(error.offending_paths),
        }
    )
    state["phase"] = "scope_blocked"
    _record(
        state,
        "scope_validation_failed",
        raised_by="ORCHESTRATOR",
        offending_paths=list(error.offending_paths),
        worktree_sha256=evidence["worktree_sha256"],
    )
    _save_state(cfg, state)


def recover_scope_blocker(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    """Route an exact preserved post-Executor scope failure to Planner correction."""
    repo = Path(cfg["repo"])
    if state.get("status") != "RUNNING" or state.get("phase") not in {
        "executor",
        "scope_blocked",
        "planner",
    }:
        raise OrchestratorError(
            "Scope recovery requires an active executor/scope_blocked Task state or "
            "an uninvoked SCOPE_BLOCKED Planner prompt."
        )
    if _git_ok(repo, "branch", "--show-current") != state.get("branch"):
        raise OrchestratorError("Scope recovery Task branch identity mismatch.")
    if _git_ok(repo, "rev-parse", "HEAD") != state.get("baseline"):
        raise OrchestratorError(
            "Scope recovery requires the unchanged Task baseline HEAD."
        )
    _validate_scope_recovery_sessions(cfg, state)

    refreshing_prompt = state.get("phase") == "planner"
    if refreshing_prompt:
        evidence = state.get("scope_blocker")
        artifact = parse_next_agent(Path(cfg["next_agent"]))
        if (
            not isinstance(evidence, dict)
            or artifact.metadata.get("source_role") != "ORCHESTRATOR"
            or artifact.metadata.get("handoff") != "SCOPE_BLOCKED"
            or artifact.metadata.get("target_role") != "PLANNER"
            or int(artifact.metadata.get("iteration", 0)) != int(state["iteration"])
            or int(state["iteration"]) != int(evidence.get("iteration", 0)) + 1
        ):
            raise OrchestratorError(
                "Planner-phase scope recovery is not an exact uninvoked recovery prompt."
            )

    if state.get("phase") == "executor" or refreshing_prompt:
        current = _current_worktree_paths(repo)
        allowed = set(state.get("approved_write_paths", [])) | LEGACY_COORDINATION_PATHS
        offending = sorted(current - allowed)
        if not offending:
            raise OrchestratorError(
                "Legacy Executor state has no reconstructable unauthorized paths."
            )
        if refreshing_prompt:
            evidence = state["scope_blocker"]
            evidence["offending_paths"] = offending
            evidence["validation_error"] = str(
                ScopeMutationError("EXECUTOR", offending)
            )
            evidence["worktree_sha256"] = _worktree_fingerprint(repo)
            state["blockers"][-1]["offending_paths"] = offending
        else:
            record_scope_blocker(cfg, state, ScopeMutationError("EXECUTOR", offending))

    evidence = state.get("scope_blocker")
    if not isinstance(evidence, dict) or not evidence.get("offending_paths"):
        raise OrchestratorError("Scope-blocker evidence is missing or invalid.")
    current_fingerprint = _worktree_fingerprint(repo)
    if current_fingerprint != evidence.get("worktree_sha256"):
        raise OrchestratorError("Preserved scope-blocked worktree fingerprint changed.")

    failed_iteration = int(evidence["iteration"])
    state["iteration"] = failed_iteration + 1
    paths = ", ".join(str(path) for path in evidence["offending_paths"])
    state["correction_context"] = (
        "The ORCHESTRATOR rejected Executor output after deterministic scope validation. "
        f"Unauthorized paths: {paths}. Preserve the existing implementation. Determine "
        "whether each path is necessary; explicitly add a justified path to the revised "
        "approved scope, or direct Executor to revert it. Do not silently authorize paths."
    )
    _write_orchestrator_planner_prompt(cfg, state, "SCOPE_BLOCKED")
    state["phase"] = "planner"
    _record(
        state,
        (
            "scope_blocker_recovery_refreshed"
            if refreshing_prompt
            else "scope_blocker_recovery_materialized"
        ),
        raised_by="ORCHESTRATOR",
        failed_iteration=failed_iteration,
        planner_iteration=state["iteration"],
        offending_paths=list(evidence["offending_paths"]),
    )
    _save_state(cfg, state)


__all__ = [
    "apply_planner_blocker_resolution",
    "create_task_state",
    "materialize_executor_handoff_correction",
    "materialize_reviewer_handoff_correction",
    "prepare_task_run",
    "record_scope_blocker",
    "recover_completed_closeout",
    "recover_max_iterations",
    "recover_planner_handoff",
    "recover_scope_blocker",
    "resume_task_run",
]
