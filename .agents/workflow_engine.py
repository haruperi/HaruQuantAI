#!/usr/bin/env python3
"""State-machine phase handlers for the HaruQuantAI agent workflow."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_runtime import *  # noqa: F403,E402


def _handle_task_activation(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    print("\n=== ORCHESTRATOR — task activation ===")
    _activate_task(cfg, state)


def _handle_planner(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    iteration = state["iteration"]
    print(f"\n=== PLANNER — Dry Run {iteration} ===")
    stdout, log = _invoke_pending(cfg, state, "PLANNER")
    block = _resolve_handoff(
        cfg["journals"]["planner"], stdout, "PLANNER", {"PENDING_APPROVAL", "BLOCKED"}
    )
    _validate_activating(
        block, _transition_for(cfg["transitions"], "PLANNER", block["handoff"])
    )
    current_branch = _git_ok(cfg["repo"], "branch", "--show-current")
    if current_branch != state.get("branch") or current_branch == cfg["main_branch"]:
        raise OrchestratorError(
            f"Planner changed task branch state: current={current_branch!r}, expected={state.get('branch')!r}."
        )
    state["plan_hash"] = _sha_file(cfg["journals"]["planner"])
    _record(state, "planner", handoff=block["handoff"], log=str(log))
    if block["handoff"] == "BLOCKED":
        validate_next_agent(cfg, state, expected_source="PLANNER", expected_handoff="BLOCKED")
        state.setdefault("blockers", []).append(
            {"iteration": iteration, "raised_by": "PLANNER", "status": "OPEN"}
        )
        state["phase"] = "planner_blocked"
    else:
        validate_next_agent(
            cfg, state, expected_source="PLANNER", expected_handoff="PENDING_APPROVAL"
        )
        state["phase"] = "approve"
    _save_state(cfg, state)


def _handle_approval(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    approved: bool,
    rejection: str | None,
    auto_approve: bool,
) -> None:
    _ensure_pending_artifact_unchanged(cfg, state)
    decision, feedback = _request_gate(
        "APPROVED: EXECUTE",
        f"Owner approval for Dry Run {state['iteration']}",
        approved or auto_approve,
        rejection,
    )
    if decision:
        _append_owner_approval(cfg, state)
        state["phase"] = "executor"
        state["next_agent"]["worktree_sha256"] = _worktree_fingerprint(cfg["repo"])
        _record(state, "owner_approval", handoff="APPROVED_EXECUTE")
    else:
        state["iteration"] += 1
        state["owner_feedback"] = feedback
        state["correction_context"] = (
            "Owner rejected the preceding dry run. Produce a complete revised dry run "
            "that addresses the owner direction without implementing anything."
        )
        _write_orchestrator_planner_prompt(cfg, state, "OWNER_REJECTED")
        state["phase"] = "planner"
        _record(state, "owner_rejection", handoff="OWNER_REJECTED")
    _save_state(cfg, state)


def _handle_executor(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    print(f"\n=== EXECUTOR — Report {state['iteration']} ===")
    stdout, log = _invoke_pending(cfg, state, "EXECUTOR")
    block = _resolve_handoff(
        cfg["journals"]["executor"], stdout, "EXECUTOR", {"READY_FOR_REVIEW", "BLOCKED"}
    )
    _validate_activating(
        block, _transition_for(cfg["transitions"], "EXECUTOR", block["handoff"])
    )
    state["executor_report_hash"] = _sha_file(cfg["journals"]["executor"])
    _record(state, "executor", handoff=block["handoff"], log=str(log))
    if block["handoff"] == "BLOCKED":
        blocked_iteration = state["iteration"]
        state.setdefault("blockers", []).append(
            {"iteration": blocked_iteration, "raised_by": "EXECUTOR", "status": "OPEN"}
        )
        state["iteration"] = blocked_iteration + 1
        validate_next_agent(cfg, state, expected_source="EXECUTOR", expected_handoff="BLOCKED")
        state["correction_context"] = (
            "This is a blocker-resolution dry run. Plan only the minimum authority/scope "
            "needed to resolve the recorded Executor blocker; suspend the remaining original "
            "scope until that resolution is reviewed."
        )
        state["phase"] = "planner"
    else:
        validate_next_agent(
            cfg, state, expected_source="EXECUTOR", expected_handoff="READY_FOR_REVIEW"
        )
        state["phase"] = "reviewer"
    _save_state(cfg, state)


def _handle_reviewer(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    print(f"\n=== REVIEWER — Review {state['iteration']} ===")
    stdout, log = _invoke_pending(cfg, state, "REVIEWER")
    block = _resolve_handoff(
        cfg["journals"]["reviewer"],
        stdout,
        "REVIEWER",
        {"CHANGES_REQUESTED", "PENDING_COMMIT"},
    )
    _validate_activating(
        block, _transition_for(cfg["transitions"], "REVIEWER", block["handoff"])
    )
    _record(state, "reviewer", handoff=block["handoff"], log=str(log))
    if block["handoff"] == "CHANGES_REQUESTED":
        state["iteration"] += 1
        validate_next_agent(
            cfg, state, expected_source="REVIEWER", expected_handoff="CHANGES_REQUESTED"
        )
        state["correction_context"] = (
            "Reviewer requested changes. Produce the next complete dry run addressing every "
            "review finding while preserving valid retained work and the original task scope."
        )
        state["phase"] = "planner"
    else:
        validate_next_agent(
            cfg, state, expected_source="REVIEWER", expected_handoff="PENDING_COMMIT"
        )
        state["reviewed_head"] = _git_ok(cfg["repo"], "rev-parse", "HEAD")
        state["reviewed_worktree_hash"] = _worktree_fingerprint(cfg["repo"])
        state["phase"] = "commit_gate"
    _save_state(cfg, state)


def _handle_commit_gate(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    approved: bool,
    rejection: str | None,
    auto_approve: bool,
) -> None:
    _ensure_pending_artifact_unchanged(cfg, state)
    if _git_ok(cfg["repo"], "rev-parse", "HEAD") != state["reviewed_head"]:
        raise OrchestratorError("HEAD changed after independent review.")
    if _worktree_fingerprint(cfg["repo"]) != state["reviewed_worktree_hash"]:
        raise OrchestratorError("Working tree changed after independent review.")
    decision, feedback = _request_gate(
        "APPROVED: COMMIT",
        f"Commit authorization for Review {state['iteration']}",
        approved or auto_approve,
        rejection,
    )
    if decision:
        state["commit_authorized"] = True
        state["phase"] = "closeout"
        _record(state, "commit_authorization", handoff="APPROVED_COMMIT")
    else:
        state["iteration"] += 1
        state["owner_feedback"] = feedback
        state["correction_context"] = (
            "Owner rejected commit authorization after a passed review. Produce a new dry run "
            "that addresses the owner direction; the previous acceptance no longer authorizes close-out."
        )
        _write_orchestrator_planner_prompt(cfg, state, "COMMIT_REJECTED")
        state["phase"] = "planner"
        _record(state, "commit_rejection", handoff="COMMIT_REJECTED")
    _save_state(cfg, state)


def _handle_closeout(cfg: dict[str, Any], state: dict[str, Any]) -> bool:
    print(f"\n=== REVIEWER — authorized close-out for Review {state['iteration']} ===")
    stdout, log = _invoke_pending(cfg, state, "REVIEWER")
    block = parse_handoff_block(stdout.splitlines()) or latest_handoff_block(
        cfg["journals"]["reviewer"]
    )
    if not block or block["stopped"] != "REVIEWER":
        raise OrchestratorError("Reviewer close-out produced no valid final handoff.")
    _record(state, "closeout", handoff=block["handoff"], log=str(log))
    if block["handoff"] == "CHANGES_REQUESTED":
        state["iteration"] += 1
        validate_next_agent(
            cfg, state, expected_source="REVIEWER", expected_handoff="CHANGES_REQUESTED"
        )
        state["phase"] = "planner"
        _save_state(cfg, state)
        return True
    if block["handoff"] != "ACCEPTED" or block["activating"] != "NONE":
        raise OrchestratorError(f"Unexpected close-out handoff: {block}")
    for path in [*cfg["journals"].values(), cfg["next_agent"]]:
        if not path.exists() or path.stat().st_size != 0:
            raise OrchestratorError(f"Close-out did not empty active-task file: {path}")
    branch = _git_ok(cfg["repo"], "branch", "--show-current")
    if branch != cfg["main_branch"]:
        raise OrchestratorError("Close-out did not return to main.")
    if _git_ok(cfg["repo"], "status", "--porcelain"):
        raise OrchestratorError("Close-out left main dirty.")
    state["status"] = "ACCEPTED"
    state["phase"] = "done"
    state["next_agent"] = None
    _save_state(cfg, state)
    print("[ok] workflow completed and active-task workspace is empty")
    return False


def router(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    auto_approve: bool = False,
    approved: bool = False,
    reject_feedback: str | None = None,
    commit_approved: bool = False,
    commit_reject_feedback: str | None = None,
) -> dict[str, Any]:
    while state["phase"] != "done":
        if state["iteration"] > cfg["max_iterations"]:
            state["status"] = "MAX_ITERATIONS"
            _save_state(cfg, state)
            return state
        phase = state["phase"]
        if phase == "task_activation":
            _handle_task_activation(cfg, state)
        elif phase == "planner":
            _handle_planner(cfg, state)
        elif phase == "planner_blocked":
            print("Planner is BLOCKED. Resolve the documented cause, then run resume.")
            state["phase"] = "planner"
            _save_state(cfg, state)
            return state
        elif phase == "approve":
            _handle_approval(
                cfg,
                state,
                approved=approved,
                rejection=reject_feedback,
                auto_approve=auto_approve,
            )
            approved = False
            reject_feedback = None
        elif phase == "executor":
            _handle_executor(cfg, state)
        elif phase == "reviewer":
            _handle_reviewer(cfg, state)
        elif phase == "commit_gate":
            _handle_commit_gate(
                cfg,
                state,
                approved=commit_approved,
                rejection=commit_reject_feedback,
                auto_approve=auto_approve,
            )
            commit_approved = False
            commit_reject_feedback = None
        elif phase == "closeout":
            if not _handle_closeout(cfg, state):
                break
        else:
            raise OrchestratorError(f"Unknown saved phase: {phase!r}")
    return state


TASK_REQUIRED = ("task_id", "task_slug", "task_request")


__all__ = [name for name in globals() if not name.startswith("__")]
