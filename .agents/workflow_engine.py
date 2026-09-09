#!/usr/bin/env python3
"""State-machine phase handlers for the HaruQuantAI agent workflow."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deterministic_closeout import perform_deterministic_closeout
from failure_routing import (
    FailureClass,
    route_failure,
    run_bounded_environment_operation,
)
from ide_transport import IDE_MODES, finish_ide_role, prepare_ide_role
from runtime_policy import RuntimePolicy
from validation_receipts import (
    ValidationReceiptError,
    candidate_fingerprint,
    create_validation_receipt,
    verify_validation_receipt,
)
from workflow_protocol import (
    ALL_COORDINATION_PATHS,
    OrchestratorError,
    ScopeMutationError,
    _ensure_pending_artifact_unchanged,
    _git_ok,
    _resolve_handoff,
    _sha_file,
    _transition_for,
    _validate_activating,
    _verify_approval_chain,
    _worktree_fingerprint,
    validate_next_agent,
)
from workflow_runtime import (
    _activate_task,
    _append_gate_authorization,
    _ensure_runtime_policy_unchanged,
    _gate_authorization,
    _invoke_pending,
    _record,
    _save_state,
    _write_orchestrator_planner_prompt,
)


def _verify_execution_authority(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    """Verify the frozen Planner or prepared-packet authorization chain."""
    if state.get("authority_kind") == "TASK_PACKET":
        packet_path = Path(str(state.get("task_packet_path", "")))
        record_path = Path(str(state.get("execute_authorization_path", "")))
        if not packet_path.is_file() or _sha_file(packet_path) != state.get(
            "approved_authority_hash"
        ):
            raise OrchestratorError("Prepared Task packet is missing or changed.")
        if not record_path.is_file() or _sha_file(record_path) != state.get(
            "execute_authorization_sha256"
        ):
            raise OrchestratorError(
                "Prepared execution authorization is missing or changed."
            )
        return
    _verify_approval_chain(
        journal=cfg["journals"]["planner"],
        iteration=state.get("approval_iteration", state["iteration"]),
        task_id=state["task"]["task_id"],
        baseline=state.get("planning_baseline", state["baseline"]),
        branch=state.get("planning_branch", state["branch"]),
        approved_plan_hash=state.get("approved_plan_hash", ""),
        authorization_source=state.get("execute_authorization_source", "OWNER_MESSAGE"),
        runtime_policy_fingerprint=state.get("runtime_policy_fingerprint", ""),
        scope_fingerprint=state.get("scope_fingerprint", ""),
    )


def _handle_task_activation(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    print("\n=== ORCHESTRATOR — task activation ===")
    _activate_task(cfg, state)


def _handle_planner(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    iteration = state["iteration"]
    print(f"\n=== PLANNER — Dry Run {iteration} ===")
    stdout, log = _invoke_pending(cfg, state, "PLANNER")
    success_handoff = "PENDING_APPROVAL"
    blocked_handoff = "BLOCKED"
    block = _resolve_handoff(
        cfg["journals"]["planner"],
        stdout,
        "PLANNER",
        {success_handoff, blocked_handoff},
    )
    _validate_activating(
        block, _transition_for(cfg["transitions"], "PLANNER", block["handoff"])
    )
    current_branch = _git_ok(cfg["repo"], "branch", "--show-current")
    invalid_main = current_branch == cfg["main_branch"]
    if current_branch != state.get("branch") or invalid_main:
        msg = (
            f"Planner changed task branch state: current={current_branch!r}, "
            f"expected={state.get('branch')!r}."
        )
        raise OrchestratorError(msg)
    state["plan_hash"] = _sha_file(cfg["journals"]["planner"])
    _record(state, "planner", handoff=block["handoff"], log=str(log))
    if block["handoff"] == blocked_handoff:
        validate_next_agent(
            cfg, state, expected_source="PLANNER", expected_handoff=blocked_handoff
        )
        state.setdefault("blockers", []).append(
            {"iteration": iteration, "raised_by": "PLANNER", "status": "OPEN"}
        )
        state["phase"] = "planner_blocked"
    else:
        validate_next_agent(
            cfg, state, expected_source="PLANNER", expected_handoff=success_handoff
        )
        state["phase"] = "approve"
    finish_ide_role(state)
    _save_state(cfg, state)


def _handle_approval(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    approved: bool,
    rejection: str | None,
) -> None:
    _ensure_pending_artifact_unchanged(cfg, state)
    decision, feedback, source = _gate_authorization(
        cfg,
        state,
        gate="APPROVED: EXECUTE",
        owner_message=approved,
        rejection=rejection,
    )
    if decision:
        _append_gate_authorization(cfg, state, source=source)
        state["phase"] = "executor"
        state["next_agent"]["worktree_sha256"] = _worktree_fingerprint(cfg["repo"])
        _record(
            state,
            "execute_authorization",
            handoff="APPROVED_EXECUTE",
            source=source,
            runtime_policy_sha256=state.get("runtime_policy_fingerprint"),
            scope_sha256=state.get("scope_fingerprint"),
        )
    else:
        state["iteration"] += 1
        state["owner_feedback"] = feedback
        state["correction_context"] = (
            "Owner rejected the preceding dry run. Produce a complete revised dry run "
            "that addresses the owner direction without implementing anything."
        )
        rejection_handoff = "OWNER_REJECTED"
        _write_orchestrator_planner_prompt(cfg, state, rejection_handoff)
        state["phase"] = "planner"
        _record(state, "owner_rejection", handoff=rejection_handoff)
    _save_state(cfg, state)


def _handle_executor(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    print(f"\n=== EXECUTOR — Report {state['iteration']} ===")
    _verify_execution_authority(cfg, state)
    correction = state.get("executor_handoff_correction")
    try:
        stdout, log = _invoke_pending(cfg, state, "EXECUTOR")
    except ScopeMutationError as exc:
        if isinstance(correction, dict):
            state["approved_write_paths"] = correction["approved_write_paths"]
        # The Executor process returned successfully and changed the worktree,
        # but deterministic post-role path validation rejected its delta. Keep
        # the implementation intact and persist a first-class recovery state;
        # do not pretend the Executor authored a BLOCKED journal handoff.
        from task_api import record_scope_blocker

        finish_ide_role(state)
        record_scope_blocker(cfg, state, exc)
        return
    if isinstance(correction, dict):
        state["approved_write_paths"] = correction["approved_write_paths"]
        state.pop("executor_handoff_correction", None)
    success_handoff = "READY_FOR_REVIEW"
    blocked_handoffs = {"BLOCKED", "DESIGN_CHANGE"}
    block = _resolve_handoff(
        cfg["journals"]["executor"],
        stdout,
        "EXECUTOR",
        {success_handoff, *blocked_handoffs},
    )
    _validate_activating(
        block, _transition_for(cfg["transitions"], "EXECUTOR", block["handoff"])
    )
    state["executor_report_hash"] = _sha_file(cfg["journals"]["executor"])
    _record(state, "executor", handoff=block["handoff"], log=str(log))
    if block["handoff"] in blocked_handoffs:
        blocked_iteration = state["iteration"]
        state.setdefault("blockers", []).append(
            {"iteration": blocked_iteration, "raised_by": "EXECUTOR", "status": "OPEN"}
        )
        state["iteration"] = blocked_iteration + 1
        validate_next_agent(
            cfg,
            state,
            expected_source="EXECUTOR",
            expected_handoff=block["handoff"],
        )
        state["correction_context"] = (
            "Executor identified a design or authority decision. Plan only the "
            "minimum change needed to resolve it; preserve valid retained work."
            if block["handoff"] == "DESIGN_CHANGE"
            else "This is a blocker-resolution dry run. Plan only the minimum "
            "authority/scope needed to resolve the recorded Executor blocker; "
            "suspend the remaining original scope until that resolution is reviewed."
        )
        state["phase"] = "planner"
    else:
        validate_next_agent(
            cfg, state, expected_source="EXECUTOR", expected_handoff="READY_FOR_REVIEW"
        )
        state["reviewed_head"] = _git_ok(cfg["repo"], "rev-parse", "HEAD")
        state["reviewed_candidate_hash"] = candidate_fingerprint(Path(cfg["repo"]))
        state["integration_validation"] = _run_local_integration_gate(cfg, state)
        state["phase"] = "reviewer"
    finish_ide_role(state)
    _save_state(cfg, state)


def _handle_reviewer(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    print(f"\n=== REVIEWER — Review {state['iteration']} ===")
    _verify_execution_authority(cfg, state)
    stdout, log = _invoke_pending(cfg, state, "REVIEWER")
    block = _resolve_handoff(
        cfg["journals"]["reviewer"],
        stdout,
        "REVIEWER",
        {
            "CHANGES_REQUESTED",
            "IMPLEMENTATION_FIX",
            "DESIGN_CHANGE",
            "PENDING_COMMIT",
        },
    )
    _validate_activating(
        block, _transition_for(cfg["transitions"], "REVIEWER", block["handoff"])
    )
    _record(state, "reviewer", handoff=block["handoff"], log=str(log))
    if block["handoff"] == "IMPLEMENTATION_FIX":
        used = int(state.get("direct_correction_rounds", 0))
        route = route_failure(FailureClass.IMPLEMENTATION_FIX, direct_corrections=used)
        state["iteration"] += 1
        if route.target == "EXECUTOR":
            state["direct_correction_rounds"] = used + 1
            validate_next_agent(
                cfg,
                state,
                expected_source="REVIEWER",
                expected_handoff="IMPLEMENTATION_FIX",
            )
            state["phase"] = "executor"
        else:
            state["correction_context"] = (
                "Two bounded direct implementation corrections were exhausted. "
                "Perform targeted planning for the unresolved Reviewer findings."
            )
            _write_orchestrator_planner_prompt(cfg, state, "CORRECTION_LIMIT_REACHED")
            state["phase"] = "planner"
    elif block["handoff"] in {"CHANGES_REQUESTED", "DESIGN_CHANGE"}:
        state["iteration"] += 1
        validate_next_agent(
            cfg,
            state,
            expected_source="REVIEWER",
            expected_handoff=block["handoff"],
        )
        state["correction_context"] = (
            "Reviewer identified a design, contract, authority or scope decision. "
            "Produce targeted planning that addresses every finding and preserves "
            "valid retained work."
        )
        state["phase"] = "planner"
    else:
        validate_next_agent(
            cfg, state, expected_source="REVIEWER", expected_handoff="PENDING_COMMIT"
        )
        if candidate_fingerprint(Path(cfg["repo"])) != state.get(
            "reviewed_candidate_hash"
        ):
            raise OrchestratorError(
                "Product candidate changed during independent review."
            )
        state["reviewed_head"] = _git_ok(cfg["repo"], "rev-parse", "HEAD")
        state["reviewed_worktree_hash"] = _worktree_fingerprint(cfg["repo"])
        if state.get("parallel_draft") and not state.get("integration_refreshed"):
            state["draft_review"] = {
                "iteration": state["iteration"],
                "baseline": state["baseline"],
                "reviewed_head": state["reviewed_head"],
                "worktree_sha256": state["reviewed_worktree_hash"],
                "reviewer_journal_sha256": _sha_file(cfg["journals"]["reviewer"]),
            }
            state["phase"] = "draft_reviewed"
        else:
            state["phase"] = "commit_gate"
    finish_ide_role(state)
    _save_state(cfg, state)


def _handle_commit_gate(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    approved: bool,
    rejection: str | None,
) -> None:
    _ensure_pending_artifact_unchanged(cfg, state)
    if _git_ok(cfg["repo"], "rev-parse", "HEAD") != state["reviewed_head"]:
        msg = "HEAD changed after independent review."
        raise OrchestratorError(msg)
    if _worktree_fingerprint(cfg["repo"]) != state["reviewed_worktree_hash"]:
        msg = "Working tree changed after independent review."
        raise OrchestratorError(msg)
    decision, feedback, source = _gate_authorization(
        cfg,
        state,
        gate="APPROVED: COMMIT",
        owner_message=approved,
        rejection=rejection,
    )
    if decision:
        validation = state.get("integration_validation")
        if not isinstance(validation, dict):
            state["reviewed_candidate_hash"] = candidate_fingerprint(Path(cfg["repo"]))
            validation = _run_local_integration_gate(cfg, state)
            state["integration_validation"] = validation
        _ensure_local_integration_gate_unchanged(state, Path(cfg["repo"]))
        state["commit_authorized"] = True
        state["commit_authorization_source"] = source
        state["integration_validation"] = validation
        state["phase"] = "closeout"
        _record(
            state,
            "commit_authorization",
            handoff="APPROVED_COMMIT",
            source=source,
            integration_report_sha256=validation["report_sha256"],
            runtime_policy_sha256=state.get("runtime_policy_fingerprint"),
            scope_sha256=state.get("scope_fingerprint"),
        )
    else:
        state["iteration"] += 1
        state["owner_feedback"] = feedback
        state["correction_context"] = (
            "Owner rejected commit authorization after a passed review. "
            "Produce a new dry run that addresses the owner direction; the "
            "previous acceptance no longer authorizes close-out."
        )
        _write_orchestrator_planner_prompt(cfg, state, "COMMIT_REJECTED")
        state["phase"] = "planner"
        _record(state, "commit_rejection", handoff="COMMIT_REJECTED")
    _save_state(cfg, state)


def _execute_integration_command(command: list[str], repo: Path) -> int:
    """Execute the controller-owned integration command and return its status."""
    result = run_bounded_environment_operation(
        lambda: subprocess.run(command, cwd=repo, check=False)
    )
    return result.returncode


def _validate_integration_report(
    report_path: Path,
    *,
    expected_base: str,
    expected_head: str,
) -> dict[str, Any]:
    """Validate a complete successful local integration report.

    Args:
        report_path: Controller-selected report path.
        expected_base: Exact accepted-main commit used as the integration base.
        expected_head: Exact reviewed branch HEAD.

    Returns:
        Parsed validated report.

    Raises:
        OrchestratorError: If the report is missing, malformed, incomplete, stale,
            or contains a failed prerequisite.
    """
    if not report_path.is_file():
        raise OrchestratorError("Local integration gate produced no report.")
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError("Local integration gate report is invalid.") from exc
    if payload.get("schema_version") != 1:
        raise OrchestratorError("Local integration gate report schema is invalid.")
    if payload.get("report_kind") != "diagnostic-not-reusable-validation-receipt":
        raise OrchestratorError("Local integration gate report kind is invalid.")
    if payload.get("explain_only") is not False:
        raise OrchestratorError("Explain-only output cannot satisfy integration.")
    decision = payload.get("decision")
    if not isinstance(decision, dict):
        raise OrchestratorError("Local integration report has no routing decision.")
    candidate = decision.get("candidate")
    if not isinstance(candidate, dict):
        raise OrchestratorError("Local integration report has no candidate identity.")
    if decision.get("requested_profile") != "integration":
        raise OrchestratorError("Local gate did not execute the integration profile.")
    if candidate.get("base_commit") != expected_base:
        raise OrchestratorError("Local integration report has a stale base commit.")
    if candidate.get("head_commit") != expected_head:
        raise OrchestratorError("Local integration report has a stale reviewed HEAD.")
    families = decision.get("selected_families")
    if not isinstance(families, list) or not families:
        raise OrchestratorError(
            "Local integration report selected no validation family."
        )
    steps = payload.get("steps")
    results = payload.get("results")
    if not isinstance(steps, list) or not steps:
        raise OrchestratorError("Local integration report planned no checks.")
    if not isinstance(results, list) or len(results) != len(steps):
        raise OrchestratorError(
            "Local integration report is missing or skipped required checks."
        )
    for step, result in zip(steps, results, strict=True):
        if not isinstance(step, dict) or not isinstance(result, dict):
            raise OrchestratorError("Local integration report entries are malformed.")
        if step.get("step_id") != result.get("step_id"):
            raise OrchestratorError("Local integration result order is inconsistent.")
        if result.get("exit_code") != 0:
            raise OrchestratorError(
                f"Local integration prerequisite failed: {step.get('step_id')}"
            )
    return cast("dict[str, Any]", payload)


def _run_local_integration_gate(
    cfg: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    """Run integration validation against the exact frozen reviewed worktree."""
    repo = Path(cfg["repo"])
    primary_repo = Path(state.get("primary_repo_path", repo))
    baseline = state.get("integration_baseline") or state["baseline"]
    reviewed_head = state["reviewed_head"]
    reviewed_hash = state.get(
        "reviewed_candidate_hash", state.get("reviewed_worktree_hash")
    )
    current_main = _git_ok(primary_repo, "rev-parse", cfg["main_branch"])
    if current_main != baseline:
        raise OrchestratorError(
            "Accepted main changed before local integration validation."
        )
    if _git_ok(repo, "rev-parse", "HEAD") != reviewed_head:
        raise OrchestratorError("Reviewed HEAD changed before local integration.")
    if candidate_fingerprint(repo) != reviewed_hash:
        raise OrchestratorError("Reviewed candidate changed before local integration.")

    report_path = (
        Path(cfg["logs_dir"]) / state["run_id"] / "integration" / "local-gate.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.unlink(missing_ok=True)
    command_prefix = cfg.get(
        "integration_command_prefix", ["uv", "run", "--locked", "python"]
    )
    command = [
        *command_prefix,
        "scripts/ci_check.py",
        "--profile",
        "integration",
        "--base",
        baseline,
        "--head",
        reviewed_head,
        "--reviewed-worktree",
        "--report",
        str(report_path),
        "--log-dir",
        str(report_path.parent / "steps"),
    ]
    exit_code = _execute_integration_command(command, repo)
    if exit_code != 0:
        raise OrchestratorError(
            f"Local integration gate failed with exit code {exit_code}."
        )
    payload = _validate_integration_report(
        report_path,
        expected_base=baseline,
        expected_head=reviewed_head,
    )
    if _git_ok(repo, "rev-parse", "HEAD") != reviewed_head:
        raise OrchestratorError("Integration checks changed the reviewed HEAD.")
    if candidate_fingerprint(repo) != reviewed_hash:
        raise OrchestratorError("Integration checks changed reviewed candidate bytes.")
    decision = payload["decision"]
    receipt_path = report_path.with_name("local-gate-receipt.json")
    authority_hash = str(
        state.get("approved_authority_hash", state.get("approved_plan_hash", ""))
    )
    try:
        receipt_sha = create_validation_receipt(
            repo=repo,
            diagnostic_path=report_path,
            receipt_path=receipt_path,
            worktree_sha256=reviewed_hash,
            authority_sha256=authority_hash,
        )
    except ValidationReceiptError as exc:
        raise OrchestratorError(str(exc)) from exc
    return {
        "status": "PASSED",
        "base_commit": baseline,
        "reviewed_head": reviewed_head,
        "reviewed_worktree_sha256": reviewed_hash,
        "selected_families": decision["selected_families"],
        "report_path": str(report_path),
        "report_sha256": _sha_file(report_path),
        "receipt_path": str(receipt_path),
        "receipt_sha256": receipt_sha,
        "authority_sha256": authority_hash,
    }


def _ensure_local_integration_gate_unchanged(state: dict[str, Any], repo: Path) -> None:
    """Require unchanged successful integration evidence before close-out."""
    evidence = state.get("integration_validation")
    if not isinstance(evidence, dict) or evidence.get("status") != "PASSED":
        raise OrchestratorError("Close-out has no passed local integration gate.")
    if evidence.get("reviewed_head") != state.get("reviewed_head"):
        raise OrchestratorError("Close-out integration evidence has a stale HEAD.")
    candidate_hash = state.get(
        "reviewed_candidate_hash", state.get("reviewed_worktree_hash")
    )
    if evidence.get("reviewed_worktree_sha256") != candidate_hash:
        raise OrchestratorError("Close-out integration evidence has a stale candidate.")
    report_path = Path(str(evidence.get("report_path", "")))
    if not report_path.is_file() or _sha_file(report_path) != evidence.get(
        "report_sha256"
    ):
        raise OrchestratorError("Close-out integration report is missing or changed.")
    if _git_ok(repo, "rev-parse", "HEAD") != state.get("reviewed_head"):
        raise OrchestratorError("HEAD changed after local integration validation.")
    if candidate_fingerprint(repo) != candidate_hash:
        raise OrchestratorError("Candidate changed after local integration validation.")
    try:
        verify_validation_receipt(
            repo=repo,
            receipt_path=Path(str(evidence.get("receipt_path", ""))),
            expected_receipt_sha256=str(evidence.get("receipt_sha256", "")),
            expected_worktree_sha256=str(candidate_hash or ""),
            expected_authority_sha256=str(
                state.get(
                    "approved_authority_hash", state.get("approved_plan_hash", "")
                )
            ),
        )
    except ValidationReceiptError as exc:
        raise OrchestratorError(str(exc)) from exc


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
    state_copy = {k: v for k, v in state.items() if k != "history"}
    state_copy["history_length"] = len(state.get("history", []))
    (archive_dir / "state.json").write_text(
        json.dumps(state_copy, indent=2, default=str),
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
    """Verify the explicit Task merge and post-close-out repository state."""
    repo = Path(state.get("primary_repo_path", cfg["repo"]))
    main_branch = cfg["main_branch"]
    baseline = state.get("integration_baseline") or state["baseline"]
    current_branch = _git_ok(repo, "branch", "--show-current")
    if current_branch != main_branch:
        msg = f"Close-out did not return to {main_branch}: current={current_branch!r}"
        raise OrchestratorError(msg)
    if _git_ok(repo, "status", "--porcelain"):
        msg = "Close-out left main dirty."
        raise OrchestratorError(msg)
    current_head = _git_ok(repo, "rev-parse", "HEAD")
    parent_line = _git_ok(repo, "rev-list", "--parents", "-n", "1", current_head)
    commit_and_parents = parent_line.split()
    if len(commit_and_parents) != 3:
        msg = "Close-out main HEAD must be an explicit two-parent merge commit."
        raise OrchestratorError(msg)
    first_parent, task_commit = commit_and_parents[1:]
    if first_parent != baseline:
        msg = (
            f"Close-out merge first-parent mismatch: expected {baseline[:12]}, "
            f"got {first_parent[:12]}."
        )
        raise OrchestratorError(msg)
    task_parent = _git_ok(repo, "rev-parse", f"{task_commit}^")
    if task_parent != baseline:
        msg = (
            f"Close-out merge second parent {task_commit[:12]} is not the single "
            f"Task commit directly above baseline {baseline[:12]}."
        )
        raise OrchestratorError(msg)
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", task_commit, current_head],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if ancestry.returncode != 0:
        msg = "Close-out Task commit is not an ancestor of the main merge commit."
        raise OrchestratorError(msg)
    merge_tree = _git_ok(repo, "rev-parse", f"{current_head}^{{tree}}")
    task_tree = _git_ok(repo, "rev-parse", f"{task_commit}^{{tree}}")
    if merge_tree != task_tree:
        msg = "Close-out merge tree differs from the exact reviewed Task tree."
        raise OrchestratorError(msg)
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
        msg = f"Close-out committed unexpected paths: {sorted(unexpected)}"
        raise OrchestratorError(msg)
    # Verify task branch is gone
    task_branch = state.get("branch", "")
    if task_branch and _git_ok(repo, "branch", "--list", task_branch):
        msg = f"Task branch {task_branch!r} still exists after close-out."
        raise OrchestratorError(msg)
    # Verify all four task files are empty
    for path in [*cfg["journals"].values(), cfg["next_agent"]]:
        if not path.exists() or path.stat().st_size != 0:
            msg = f"Close-out did not empty active-task file: {path}"
            raise OrchestratorError(msg)


def _handle_closeout(cfg: dict[str, Any], state: dict[str, Any]) -> bool:
    print(f"\n=== CONTROLLER: deterministic close-out {state['iteration']} ===")
    _ensure_local_integration_gate_unchanged(state, Path(cfg["repo"]))
    _archive_closeout_evidence(cfg, state)
    result = perform_deterministic_closeout(cfg, state)
    state["closeout_receipt"] = result
    _record(state, "closeout", handoff="ACCEPTED", **result)
    _verify_closeout_lineage(cfg, state)
    state["status"] = "ACCEPTED"
    state["phase"] = "done"
    state["next_agent"] = None
    _save_state(cfg, state)
    print("[ok] workflow completed and active-task workspace is empty")
    return False


def router(  # noqa: PLR0911
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
    while state["phase"] != "done":
        _ensure_runtime_policy_unchanged(cfg, state)
        raw_limit = state.get("effective_max_iterations")
        effective_limit = int(cfg["max_iterations"] if raw_limit is None else raw_limit)
        if state["iteration"] > effective_limit:
            policy = cfg.get("runtime_policy")
            recovery_available = (
                isinstance(policy, RuntimePolicy)
                and policy.approval_policy == "unattended"
                and policy.recovery.enabled
                and int(state.get("recovery_generation", 0)) == 0
            )
            if recovery_available and isinstance(policy, RuntimePolicy):
                _ensure_runtime_policy_unchanged(cfg, state)
                state["recovery_generation"] = 1
                state["session_generation"] = "recovery-1"
                state["effective_max_iterations"] = (
                    int(cfg["max_iterations"]) + policy.recovery.additional_iterations
                )
                _record(
                    state,
                    "automatic_recovery_activated",
                    model=policy.recovery.model,
                    effort=policy.recovery.effort,
                    generation="recovery-1",
                )
                _save_state(cfg, state)
                continue
            state["status"] = "MAX_ITERATIONS"
            _record(state, "max_iterations_exhausted")
            _save_state(cfg, state)
            return state
        phase = state["phase"]
        if phase == "draft_reviewed":
            print("Parallel Task draft is reviewed and waiting for integration.")
            return state
        if phase == "task_activation":
            _handle_task_activation(cfg, state)
        elif cfg.get("mode") in IDE_MODES and phase in {
            "planner",
            "executor",
            "reviewer",
        }:
            role = phase.upper()
            pending_invocation = state.get("ide_role_invocation")
            if pending_invocation is None:
                if role_complete:
                    msg = (
                        "--role-complete was supplied before an IDE role was prepared."
                    )
                    raise OrchestratorError(msg)
                prepare_ide_role(
                    cfg,
                    state,
                    role,
                )
                return state
            if not role_complete:
                print(
                    f"IDE mode is waiting for {role} completion. Resume with "
                    "--role-complete"
                    + (
                        " --app-agent-id <opaque-id>."
                        if cfg.get("mode") == "delegate"
                        else "."
                    )
                )
                return state
            cfg["_ide_role_completion"] = {"app_agent_id": app_agent_id}
            role_complete = False
            app_agent_id = None
            if phase == "planner":
                _handle_planner(cfg, state)
            elif phase == "executor":
                _handle_executor(cfg, state)
            elif phase == "reviewer":
                _handle_reviewer(cfg, state)
            cfg.pop("_ide_role_completion", None)
        elif cfg.get("mode") == "manual" and phase in {
            "planner",
            "executor",
            "reviewer",
        }:
            print(
                f"Manual mode is waiting for the dedicated {phase.upper()} chat to "
                "consume .agents/task/next-agent.md."
            )
            return state
        elif phase == "planner":
            _handle_planner(cfg, state)
        elif phase == "planner_blocked":
            blocker_info = state.get("blocker_resolution")
            if blocker_info:
                # BLOCKER_RESOLVED: create fresh Planner prompt
                print("Planner blocker resolved. Creating fresh Planner prompt.")
                _record(
                    state,
                    "planner_blocker_resolved",
                    source=blocker_info.get("source", "OWNER_MESSAGE"),
                    evidence_recorded=bool(blocker_info.get("evidence")),
                )
                blocker_handoff = "BLOCKER_RESOLVED"
                _write_orchestrator_planner_prompt(cfg, state, blocker_handoff)
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
            runtime_policy = cfg.get("runtime_policy")
            execute_preauthorized = (
                isinstance(runtime_policy, RuntimePolicy)
                and runtime_policy.can_preauthorize_execute()
            )
            if (
                cfg.get("mode") in IDE_MODES
                and not approved
                and reject_feedback is None
                and not execute_preauthorized
            ):
                print(
                    "IDE mode is waiting for exact owner authorization: "
                    "APPROVED: EXECUTE"
                )
                return state
            _handle_approval(
                cfg,
                state,
                approved=approved,
                rejection=reject_feedback,
            )
            approved = False
            reject_feedback = None
        elif phase == "executor":
            _handle_executor(cfg, state)
        elif phase == "scope_blocked":
            print(
                "Executor scope validation is BLOCKED. Preserve the worktree, "
                "then run:\n"
                "  uv run .agents/orchestrator.py recover-scope-blocker"
            )
            return state
        elif phase == "reviewer":
            _handle_reviewer(cfg, state)
        elif phase == "commit_gate":
            runtime_policy = cfg.get("runtime_policy")
            commit_preauthorized = (
                isinstance(runtime_policy, RuntimePolicy)
                and runtime_policy.can_preauthorize_commit()
            )
            if (
                cfg.get("mode") in IDE_MODES
                and not commit_approved
                and commit_reject_feedback is None
                and not commit_preauthorized
            ):
                print(
                    "IDE mode is waiting for exact owner authorization: "
                    "APPROVED: COMMIT"
                )
                return state
            _handle_commit_gate(
                cfg,
                state,
                approved=commit_approved,
                rejection=commit_reject_feedback,
            )
            commit_approved = False
            commit_reject_feedback = None
        elif phase == "closeout":
            if not _handle_closeout(cfg, state):
                break
        else:
            msg = f"Unknown saved phase: {phase!r}"
            raise OrchestratorError(msg)
    return state


TASK_REQUIRED = ("task_id", "task_slug", "task_request")


__all__ = [
    "TASK_REQUIRED",
    "_archive_closeout_evidence",
    "_handle_approval",
    "_handle_closeout",
    "_handle_commit_gate",
    "_handle_executor",
    "_handle_planner",
    "_handle_reviewer",
    "_handle_task_activation",
    "_verify_closeout_lineage",
    "router",
]
