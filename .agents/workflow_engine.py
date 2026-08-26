#!/usr/bin/env python3
"""State-machine phase handlers for the HaruQuantAI agent workflow."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_runtime import *


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
        validate_next_agent(
            cfg, state, expected_source="PLANNER", expected_handoff="BLOCKED"
        )
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
    # Verify approval chain before invoking Executor
    _verify_approval_chain(
        journal=cfg["journals"]["planner"],
        iteration=state["iteration"],
        task_id=state["task"]["task_id"],
        baseline=state["baseline"],
        branch=state["branch"],
        approved_plan_hash=state.get("approved_plan_hash", ""),
    )
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
        validate_next_agent(
            cfg, state, expected_source="EXECUTOR", expected_handoff="BLOCKED"
        )
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
    # Verify approval chain before Reviewer (same chain Executor used)
    _verify_approval_chain(
        journal=cfg["journals"]["planner"],
        iteration=state["iteration"],
        task_id=state["task"]["task_id"],
        baseline=state["baseline"],
        branch=state["branch"],
        approved_plan_hash=state.get("approved_plan_hash", ""),
    )
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


def _archive_closeout_evidence(cfg: dict[str, Any], state: dict[str, Any]) -> Path:
    """Archive journals and authorization evidence before close-out mutation."""
    logs_dir = cfg.get("logs_dir", cfg["repo"] / ".agents" / "logs")
    archive_dir = logs_dir / state["run_id"] / "closeout"
    archive_dir.mkdir(parents=True, exist_ok=True)
    for key, journal_path in cfg["journals"].items():
        if journal_path.exists():
            (archive_dir / f"{key}.md").write_text(
                journal_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
    next_agent = cfg["next_agent"]
    if next_agent.exists():
        (archive_dir / "next-agent.md").write_text(
            next_agent.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    # Archive state summary
    import json as _json

    state_copy = {k: v for k, v in state.items() if k != "history"}
    state_copy["history_length"] = len(state.get("history", []))
    (archive_dir / "state.json").write_text(
        _json.dumps(state_copy, indent=2, default=str),
        encoding="utf-8",
    )
    # Archive reviewed HEAD and worktree fingerprint
    head = _git_ok(cfg["repo"], "rev-parse", "HEAD")
    (archive_dir / "reviewed_head.txt").write_text(head + "\n", encoding="utf-8")
    fp = _worktree_fingerprint(cfg["repo"])
    (archive_dir / "worktree_fingerprint.txt").write_text(fp + "\n", encoding="utf-8")
    print(f"[ok] close-out evidence archived to {archive_dir}")
    return Path(archive_dir)


def _verify_closeout_lineage(
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    """Verify Git lineage after close-out: main is clean, ff-only merge correct."""
    repo = cfg["repo"]
    main_branch = cfg["main_branch"]
    baseline = state["baseline"]
    current_branch = _git_ok(repo, "branch", "--show-current")
    if current_branch != main_branch:
        raise OrchestratorError(
            f"Close-out did not return to {main_branch}: current={current_branch!r}"
        )
    if _git_ok(repo, "status", "--porcelain"):
        raise OrchestratorError("Close-out left main dirty.")
    # Verify main HEAD is exactly one commit ahead of baseline
    current_head = _git_ok(repo, "rev-parse", "HEAD")
    parent = _git_ok(repo, "rev-parse", f"{current_head}^")
    if parent != baseline:
        raise OrchestratorError(
            f"Close-out commit parent mismatch: expected {baseline[:12]}, "
            f"got {parent[:12]}. Task commit must be direct child of baseline."
        )
    # Verify approved changed-path set
    approved_paths = set(state.get("approved_write_paths", []))
    diff_result = subprocess.run(
        ["git", "diff", "--name-only", f"{baseline}..{current_head}"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    committed_paths = {p.strip() for p in diff_result.stdout.splitlines() if p.strip()}
    # Add coordination paths (always allowed)
    allowed = approved_paths | ALL_COORDINATION_PATHS
    unexpected = committed_paths - allowed
    if unexpected:
        raise OrchestratorError(
            f"Close-out committed unexpected paths: {sorted(unexpected)}"
        )
    # Verify task branch is gone
    task_branch = state.get("branch", "")
    if task_branch and _git_ok(repo, "branch", "--list", task_branch):
        raise OrchestratorError(
            f"Task branch {task_branch!r} still exists after close-out."
        )
    # Verify all four task files are empty
    for path in [*cfg["journals"].values(), cfg["next_agent"]]:
        if not path.exists() or path.stat().st_size != 0:
            raise OrchestratorError(f"Close-out did not empty active-task file: {path}")


def _handle_closeout(cfg: dict[str, Any], state: dict[str, Any]) -> bool:
    print(f"\n=== REVIEWER — authorized close-out for Review {state['iteration']} ===")
    _archive_closeout_evidence(cfg, state)
    stdout, log = _invoke_pending(cfg, state, "REVIEWER", authorized_closeout=True)
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
    _verify_closeout_lineage(cfg, state)
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
            blocker_info = state.get("blocker_resolution")
            if blocker_info:
                # BLOCKER_RESOLVED: create fresh Planner prompt
                print("Planner blocker resolved. Creating fresh Planner prompt.")
                _write_orchestrator_planner_prompt(cfg, state, "BLOCKER_RESOLVED")
                state["phase"] = "planner"
                state.pop("blocker_resolution", None)
                _save_state(cfg, state)
            else:
                print(
                    "Planner is BLOCKED. Resolve the documented cause, then run:\n"
                    "  uv run .agents/orchestrator.py resume "
                    '--resolve-planner-blocker "<resolution evidence>"'
                )
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
