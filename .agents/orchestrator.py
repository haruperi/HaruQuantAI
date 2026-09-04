#!/usr/bin/env python3
# pyright: reportPrivateUsage=false
"""CLI for the HaruQuantAI artifact-driven Task and Goal workflows."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal_engine import (
    accept_recovered_child,
    advance_goal,
    cancel_goal,
    format_goal_status,
    load_goal_spec,
    load_goal_state,
    save_goal_state,
    start_goal,
)
from ide_transport import *
from runtime_policy import (
    RecoveryPolicy,
    RolePolicy,
    RuntimePolicy,
    UnattendedPolicy,
    scope_fingerprint,
)
from session_runner import probe_adapter
from task_api import *
from workflow_engine import *
from workflow_protocol import (
    SLUG_RE,
    OrchestratorError,
    _git_ok,
    _load_toml,
    _parse_protocol,
    _transition_for,
    assemble_config,
    parse_next_agent,
)
from workflow_runtime import (
    WorkflowLock,
    _entry_gate,
    _load_state,
    _save_state,
)

AGENTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENTS_DIR.parent


def _require_cli_mode(cfg: dict[str, Any]) -> None:
    """Validate that runtime mode is one of the supported CLI/manual modes."""
    mode = str(cfg.get("mode", "UNCONFIGURED"))
    if mode not in {
        "solo",
        "solo-headless",
        "delegate",
        "delegate-headless",
        "delegate-multi",
        "manual",
        "quick-fix",
    }:
        raise OrchestratorError(
            f"Workflow mode is {mode!r}; run .agents/configure.py first."
        )


def _collect_task(args: argparse.Namespace) -> dict[str, str]:
    if args.task_file:
        path = Path(args.task_file).resolve()
        if not path.exists():
            raise OrchestratorError(f"Task specification not found: {path}")
        task = {key: str(value) for key, value in _load_toml(path).items()}
    else:
        keys = (
            "task_kind",
            "task_id",
            "task_slug",
            "task_name",
            "task_request",
            "additional_context",
            "exclusions",
            "owner_execution_notes",
            "review_focus",
            "implementation_file",
            "implementation_entry",
        )
        task = {
            key: str(getattr(args, key))
            for key in keys
            if getattr(args, key, None) is not None
        }
    missing = [key for key in TASK_REQUIRED if not task.get(key)]
    if missing:
        raise OrchestratorError(f"Missing task fields: {missing}")
    if not SLUG_RE.fullmatch(task["task_slug"]):
        raise OrchestratorError("task_slug must be lowercase filesystem-safe text.")
    return task


def cmd_start(args: argparse.Namespace) -> int:
    """Start a workflow run from a validated clean-main entry gate."""
    cfg = assemble_config(args.repo)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        state = prepare_task_run(cfg, _collect_task(args))
        try:
            resume_task_run(
                cfg,
                state,
                approved=args.approved,
                reject_feedback=args.reject_feedback,
                commit_approved=args.approved_commit,
                commit_reject_feedback=args.reject_commit_feedback,
                role_complete=args.role_complete,
                app_agent_id=args.app_agent_id,
            )
        except KeyboardInterrupt:
            _save_state(cfg, state)
            print("\nStopped by owner; Task run state saved.")
            return 130
        return 0
    finally:
        lock.release()


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume a saved workflow run from its persisted phase."""
    cfg = assemble_config(args.repo)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        state = _load_state(cfg, args.run_id)
        if state.get("status") == "CANCELLED":
            raise OrchestratorError("A CANCELLED Task run cannot be resumed.")
        resolve_blocker = getattr(args, "resolve_planner_blocker", None)
        if resolve_blocker:
            apply_planner_blocker_resolution(cfg, state, resolve_blocker)
            print(f"[ok] Planner blocker resolved: {resolve_blocker}")
        try:
            resume_task_run(
                cfg,
                state,
                approved=args.approved,
                reject_feedback=args.reject_feedback,
                commit_approved=args.approved_commit,
                commit_reject_feedback=args.reject_commit_feedback,
                role_complete=args.role_complete,
                app_agent_id=args.app_agent_id,
            )
        except KeyboardInterrupt:
            _save_state(cfg, state)
            return 130
        return 0
    finally:
        lock.release()


def cmd_cancel(args: argparse.Namespace) -> int:
    """Cancel an active Task run without destroying evidence."""
    cfg = assemble_config(args.repo)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        state = _load_state(cfg, args.run_id)
        if state.get("status") == "ACCEPTED":
            print("[ok] Task already ACCEPTED; nothing to cancel.")
            return 0
        if state.get("status") == "CANCELLED":
            print("[ok] Task already CANCELLED.")
            return 0
        reason = getattr(args, "reason", "") or "Owner-initiated cancellation"
        state["status"] = "CANCELLED"
        state["cancellation"] = {
            "reason": reason,
            "cancelled_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        }
        _save_state(cfg, state)
        print(f"[ok] Task run {state['run_id']} CANCELLED.")
        print(f"     Reason: {reason}")
        print("     Journals, task branch, and role-session evidence preserved.")
        return 0
    finally:
        lock.release()


def _enable_scope_recovery_transition(cfg: dict[str, Any]) -> None:
    """Load the controller's recovery transition for an external target worktree."""
    try:
        _transition_for(cfg["transitions"], "ORCHESTRATOR", "SCOPE_BLOCKED")
    except OrchestratorError:
        _protocol, controller_transitions = _parse_protocol(
            AGENTS_DIR / "protocol.toml"
        )
        recovery = _transition_for(
            controller_transitions, "ORCHESTRATOR", "SCOPE_BLOCKED"
        )
        cfg["transitions"] = [*cfg["transitions"], recovery]


def _enable_executor_handoff_correction_transition(cfg: dict[str, Any]) -> None:
    """Load the controller-only correction transition for an external worktree."""
    try:
        _transition_for(
            cfg["transitions"], "ORCHESTRATOR", "EXECUTOR_HANDOFF_CORRECTION"
        )
    except OrchestratorError:
        _protocol, controller_transitions = _parse_protocol(
            AGENTS_DIR / "protocol.toml"
        )
        correction = _transition_for(
            controller_transitions, "ORCHESTRATOR", "EXECUTOR_HANDOFF_CORRECTION"
        )
        cfg["transitions"] = [*cfg["transitions"], correction]


def _enable_reviewer_handoff_correction_transition(cfg: dict[str, Any]) -> None:
    """Load the controller-only Reviewer correction transition externally."""
    try:
        _transition_for(
            cfg["transitions"], "ORCHESTRATOR", "REVIEWER_HANDOFF_CORRECTION"
        )
    except OrchestratorError:
        _protocol, controller_transitions = _parse_protocol(
            AGENTS_DIR / "protocol.toml"
        )
        correction = _transition_for(
            controller_transitions, "ORCHESTRATOR", "REVIEWER_HANDOFF_CORRECTION"
        )
        cfg["transitions"] = [*cfg["transitions"], correction]


def cmd_recover_scope_blocker(args: argparse.Namespace) -> int:
    """Recover one exact post-Executor scope failure without changing product work."""
    cfg = assemble_config(args.repo)
    _enable_scope_recovery_transition(cfg)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        state = _load_state(cfg, args.run_id)
        recover_scope_blocker(cfg, state)
        print(
            f"[ok] Scope blocker routed to Planner iteration {state['iteration']} "
            f"for Task {state['run_id']}."
        )
        return 0
    finally:
        lock.release()


def cmd_goal_recover_scope_blocker(args: argparse.Namespace) -> int:
    """Recover the active Goal child while preserving frozen Goal progress."""
    cfg = assemble_config(args.repo)
    _enable_scope_recovery_transition(cfg)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        goal = load_goal_state(cfg, args.goal_run_id)
        if goal.get("status") != "RUNNING":
            raise OrchestratorError("Scope recovery requires a RUNNING Goal.")
        active = goal.get("active_child")
        if not isinstance(active, dict) or not active.get("run_id"):
            raise OrchestratorError("Scope recovery requires one active Goal child.")
        before_completed = list(goal.get("completed_entries", []))
        before_remaining = list(goal.get("remaining_entries", []))
        child = _load_state(cfg, str(active["run_id"]))
        recover_scope_blocker(cfg, child)
        if (
            list(goal.get("completed_entries", [])) != before_completed
            or list(goal.get("remaining_entries", [])) != before_remaining
        ):
            raise OrchestratorError("Scope recovery changed frozen Goal progress.")
        active["phase"] = child["phase"]
        active["status"] = child["status"]
        save_goal_state(cfg, goal)
        print(format_goal_status(goal))
        return 0
    finally:
        lock.release()


def cmd_goal_recover_planner_handoff(args: argparse.Namespace) -> int:
    """Recover the active Goal child's already-returned Planner handoff."""
    cfg = assemble_config(args.repo)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        goal = load_goal_state(cfg, args.goal_run_id)
        if (
            goal.get("goal_run_id") != args.goal_run_id
            or goal.get("status") != "RUNNING"
        ):
            raise OrchestratorError(
                "Planner-handoff recovery requires the exact RUNNING Goal."
            )
        active = goal.get("active_child")
        if not isinstance(active, dict) or active.get("run_id") != args.task_run_id:
            raise OrchestratorError(
                "Planner-handoff recovery active child identity mismatch."
            )
        before_completed = list(goal.get("completed_entries", []))
        before_remaining = list(goal.get("remaining_entries", []))
        child = _load_state(cfg, args.task_run_id)
        recover_planner_handoff(
            cfg,
            child,
            expected_run_id=args.task_run_id,
            expected_planner_session_id=args.planner_session_id,
            expected_worktree_fingerprint=args.worktree_fingerprint,
        )
        if (
            list(goal.get("completed_entries", [])) != before_completed
            or list(goal.get("remaining_entries", [])) != before_remaining
        ):
            raise OrchestratorError("Planner-handoff recovery changed Goal progress.")
        active["phase"] = child["phase"]
        active["status"] = child["status"]
        save_goal_state(cfg, goal)
        print(format_goal_status(goal))
        return 0
    finally:
        lock.release()


def cmd_goal_correct_executor_handoff(args: argparse.Namespace) -> int:
    """Materialize an exact same-session Executor handoff correction prompt."""
    cfg = assemble_config(args.repo)
    _enable_executor_handoff_correction_transition(cfg)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        goal = load_goal_state(cfg, args.goal_run_id)
        if (
            goal.get("goal_run_id") != args.goal_run_id
            or goal.get("status") != "RUNNING"
        ):
            raise OrchestratorError(
                "Executor handoff correction requires the exact RUNNING Goal."
            )
        active = goal.get("active_child")
        if not isinstance(active, dict) or active.get("run_id") != args.task_run_id:
            raise OrchestratorError(
                "Executor handoff correction active child mismatch."
            )
        child = _load_state(cfg, args.task_run_id)
        materialize_executor_handoff_correction(
            cfg,
            child,
            expected_run_id=args.task_run_id,
            expected_executor_session_id=args.executor_session_id,
            expected_worktree_fingerprint=args.worktree_fingerprint,
        )
        active["phase"] = child["phase"]
        active["status"] = child["status"]
        save_goal_state(cfg, goal)
        print(format_goal_status(goal))
        return 0
    finally:
        lock.release()


def cmd_goal_correct_reviewer_handoff(args: argparse.Namespace) -> int:
    """Materialize an exact same-session Reviewer handoff correction prompt."""
    cfg = assemble_config(args.repo)
    _enable_reviewer_handoff_correction_transition(cfg)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        goal = load_goal_state(cfg, args.goal_run_id)
        if (
            goal.get("goal_run_id") != args.goal_run_id
            or goal.get("status") != "RUNNING"
        ):
            raise OrchestratorError(
                "Reviewer handoff correction requires the exact RUNNING Goal."
            )
        active = goal.get("active_child")
        if not isinstance(active, dict) or active.get("run_id") != args.task_run_id:
            raise OrchestratorError(
                "Reviewer handoff correction active child mismatch."
            )
        child = _load_state(cfg, args.task_run_id)
        materialize_reviewer_handoff_correction(
            cfg,
            child,
            expected_run_id=args.task_run_id,
            expected_reviewer_session_id=args.reviewer_session_id,
            expected_worktree_fingerprint=args.worktree_fingerprint,
        )
        active["phase"] = child["phase"]
        active["status"] = child["status"]
        save_goal_state(cfg, goal)
        print(format_goal_status(goal))
        return 0
    finally:
        lock.release()


def cmd_goal_recover_max_iterations(args: argparse.Namespace) -> int:
    """Reopen one exact owner-authorized Goal child correction iteration."""
    cfg = assemble_config(args.repo)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        goal = load_goal_state(cfg, args.goal_run_id)
        if (
            goal.get("goal_run_id") != args.goal_run_id
            or goal.get("status") != "BLOCKED"
            or goal.get("blocked_reason") != "CHILD_TERMINAL_FAILURE"
        ):
            raise OrchestratorError("Max-iteration recovery Goal state mismatch.")
        active = goal.get("active_child")
        if (
            not isinstance(active, dict)
            or active.get("run_id") != args.task_run_id
            or active.get("status") != "MAX_ITERATIONS"
        ):
            raise OrchestratorError("Max-iteration recovery active child mismatch.")
        child = _load_state(cfg, args.task_run_id)
        recover_max_iterations(
            cfg,
            child,
            expected_run_id=args.task_run_id,
            expected_iteration=args.iteration,
            expected_worktree_fingerprint=args.worktree_fingerprint,
        )
        goal["status"] = "RUNNING"
        goal["blocked_reason"] = None
        active["phase"] = child["phase"]
        active["status"] = child["status"]
        save_goal_state(cfg, goal)
        print(format_goal_status(goal))
        return 0
    finally:
        lock.release()


def cmd_goal_recover_completed_closeout(args: argparse.Namespace) -> int:
    """Reconcile an exact completed child close-out after terminal transport loss."""
    cfg = assemble_config(args.repo)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        goal = load_goal_state(cfg, args.goal_run_id)
        if (
            goal.get("goal_run_id") != args.goal_run_id
            or goal.get("status") != "RUNNING"
        ):
            raise OrchestratorError("Completed close-out recovery Goal state mismatch.")
        active = goal.get("active_child")
        if not isinstance(active, dict) or active.get("run_id") != args.task_run_id:
            raise OrchestratorError(
                "Completed close-out recovery active child mismatch."
            )
        child = _load_state(cfg, args.task_run_id)
        recover_completed_closeout(
            cfg,
            child,
            expected_run_id=args.task_run_id,
            expected_iteration=args.iteration,
            expected_merge_head=args.merge_head,
        )
        accept_recovered_child(cfg, goal, child)
        print(format_goal_status(goal))
        return 0
    finally:
        lock.release()


def cmd_goal_start(args: argparse.Namespace) -> int:
    """Freeze one Goal and begin its first ordinary child Task."""
    cfg = assemble_config(args.repo)
    path = Path(args.goal_file).resolve()
    if not path.exists():
        raise OrchestratorError(f"Goal specification not found: {path}")
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        try:
            state = start_goal(
                cfg,
                load_goal_spec(path),
                approved=args.approved,
                reject_feedback=args.reject_feedback,
                commit_approved=args.approved_commit,
                commit_reject_feedback=args.reject_commit_feedback,
                role_complete=args.role_complete,
                app_agent_id=args.app_agent_id,
            )
        except KeyboardInterrupt:
            print("\nStopped by owner; Goal and child Task checkpoints were preserved.")
            return 130
        print(format_goal_status(state))
        return 0
    finally:
        lock.release()


def cmd_goal_resume(args: argparse.Namespace) -> int:
    """Resume the active child of a previously frozen Goal."""
    cfg = assemble_config(args.repo)
    _enable_executor_handoff_correction_transition(cfg)
    _enable_reviewer_handoff_correction_transition(cfg)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        state = load_goal_state(cfg, args.goal_run_id)
        try:
            state = advance_goal(
                cfg,
                state,
                approved=args.approved,
                reject_feedback=args.reject_feedback,
                commit_approved=args.approved_commit,
                commit_reject_feedback=args.reject_commit_feedback,
                resolve_planner_blocker=args.resolve_planner_blocker,
                stop_after_current_child=args.stop_after_current_child,
                claim_child_chat=args.claim_child_chat,
                role_complete=args.role_complete,
                app_agent_id=args.app_agent_id,
            )
        except KeyboardInterrupt:
            print("\nStopped by owner; Goal and child Task checkpoints were preserved.")
            return 130
        print(format_goal_status(state))
        return 0
    finally:
        lock.release()


def cmd_goal_status(args: argparse.Namespace) -> int:
    cfg = assemble_config(args.repo)
    print(format_goal_status(load_goal_state(cfg, args.goal_run_id)))
    return 0


def cmd_goal_cancel(args: argparse.Namespace) -> int:
    cfg = assemble_config(args.repo)
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        state = load_goal_state(cfg, args.goal_run_id)
        reason = args.reason or "Owner-initiated Goal cancellation"
        state = cancel_goal(cfg, state, reason)
        print(format_goal_status(state))
        print("Active child Task evidence, if any, was deliberately preserved.")
        return 0
    finally:
        lock.release()


def _doctor_protocol(cfg: dict[str, Any]) -> bool:
    ok = True
    print(f"[ok] protocol schema: {cfg['protocol']['prompt_schema_version']}")
    continuity = cast("dict[str, Any]", cfg.get("session_continuity", {}))
    required_policy = {
        "scope": "workflow-run",
        "same_role_resume": True,
        "new_run_new_sessions": True,
        "reviewer_closeout_reuses_reviewer": True,
        "session_context_is_authority": False,
    }
    for key, expected in required_policy.items():
        if continuity.get(key) != expected:
            print(f"[FAIL] session continuity {key}: {continuity.get(key)!r}")
            ok = False
    if all(continuity.get(key) == value for key, value in required_policy.items()):
        print("[ok] role session continuity policy")
    seen: set[tuple[str, str]] = set()
    for transition in cfg["transitions"]:
        trans_key = (transition.source_role, transition.handoff)
        if trans_key in seen:
            print(f"[FAIL] duplicate transition: {trans_key}")
            ok = False
        seen.add(trans_key)
        if (
            transition.target_template
            and not (cfg["repo"] / transition.target_template).exists()
        ):
            print(f"[FAIL] missing transition template: {transition.target_template}")
            ok = False
    return ok


def cmd_doctor(args: argparse.Namespace) -> int:
    """Validate workflow configuration and active-task artifacts."""
    try:
        cfg = assemble_config(args.repo)
    except (OSError, KeyError, tomllib.TOMLDecodeError, OrchestratorError) as exc:
        print(f"[FAIL] configuration: {exc}")
        return 1
    ok = _doctor_protocol(cfg)
    for name, path in cfg["templates"].items():
        exists = path.exists()
        print(f"[{'ok' if exists else 'FAIL'}] template {name}: {path}")
        ok = ok and exists
    active_files: dict[str, Path] = {
        **cast("dict[str, Path]", cfg["journals"]),
        "next-agent": cast("Path", cfg["next_agent"]),
    }
    for name, path in active_files.items():
        exists = path.exists()
        print(f"[{'ok' if exists else 'FAIL'}] active task file {name}: {path}")
        ok = ok and exists
    for relative in (
        ".agents/goal_engine.py",
        ".agents/task_api.py",
        ".agents/make_goal.py",
        ".agents/goal.example.toml",
    ):
        path = cfg["repo"] / relative
        exists = path.exists()
        print(f"[{'ok' if exists else 'FAIL'}] Goal workflow source: {relative}")
        ok = ok and exists
    for obsolete in (
        cfg["repo"] / ".agents/templates",
        cfg["repo"] / "docs/dev/prompt",
        cfg["repo"] / "docs/dev/task",
    ):
        if obsolete.exists():
            print(f"[FAIL] obsolete workflow path still exists: {obsolete}")
            ok = False
    mode = str(cfg.get("mode", "UNCONFIGURED"))
    if mode == "UNCONFIGURED":
        print("[FAIL] workflow mode: UNCONFIGURED (run .agents/configure.py)")
        ok = False
    else:
        print(f"[ok] workflow mode: {mode}")
    runtime_policy = cfg.get("runtime_policy")
    if (
        isinstance(runtime_policy, RuntimePolicy)
        and runtime_policy.legacy_compatibility
    ):
        active_task = any(
            path.exists() and path.stat().st_size > 0 for path in active_files.values()
        )
        severity = "warn" if active_task else "FAIL"
        print(
            f"[{severity}] run-config.toml uses continuation-only legacy syntax; "
            "run .agents/configure.py before starting a new Task or Goal"
        )
        ok = ok and active_task
    for role, role_cfg in cfg["roles"].items():
        command = cast("list[str]", role_cfg.get("command", []))
        runner_ok = bool(command) and shutil.which(command[0]) is not None
        if mode in {"solo-headless", "delegate-headless", "delegate-multi"}:
            adapter = str(role_cfg.get("session_adapter", ""))
            continuity_required = role_cfg.get("session_continuity") == "required"
            adapter_ok, detail = (
                probe_adapter(adapter) if adapter else (False, "missing adapter")
            )
            print(
                f"[{'ok' if runner_ok else 'FAIL'}] role {role} session runner: "
                f"{command[:1]}"
            )
            print(
                f"[{'ok' if adapter_ok else 'FAIL'}] role {role} session adapter: {detail}"
            )
            ok = ok and runner_ok and continuity_required and adapter_ok
        else:
            print(f"[N/A] role {role} process runner is unused in {mode} mode")
    if mode == "solo":
        print("[ok] IDE solo transport: current chat performs each prepared role")
    elif mode == "quick-fix":
        print("[ok] Quick-Fix: current chat plans and executes directly on clean main")
    elif mode == "delegate":
        print(
            "[ok] IDE delegate transport: controlling chat must expose app-native "
            "subagents and retain exact role handles"
        )
    if cfg["next_agent"].exists() and cfg["next_agent"].stat().st_size:
        try:
            artifact = parse_next_agent(cfg["next_agent"])
            print(
                f"[ok] current next-agent: {artifact.metadata['source_role']} -> "
                f"{artifact.metadata['target_role']} / {artifact.metadata['handoff']}"
            )
        except OrchestratorError as exc:
            print(f"[FAIL] current next-agent: {exc}")
            ok = False
    return 0 if ok else 1


def _init_self_test_repo(tmp: Path, source_cfg: dict[str, Any]) -> dict[str, Any]:
    """Create a temporary repository containing the workflow self-test fixture."""
    (tmp / ".agents/task").mkdir(parents=True)
    (tmp / ".agents/tests").mkdir(parents=True)
    (tmp / "docs/templates/prompt").mkdir(parents=True)
    for name in ("planner.md", "executor.md", "reviewer.md", "next-agent.md"):
        (tmp / ".agents/task" / name).write_bytes(b"")
    for key in ("planner", "executor", "reviewer", "reviewer_closeout", "default"):
        source = source_cfg["templates"][key]
        target_name = (
            "reviewer-closeout.md" if key == "reviewer_closeout" else source.name
        )
        (tmp / "docs/templates/prompt" / target_name).write_text(
            source.read_text(encoding="utf-8"), encoding="utf-8"
        )
    (tmp / ".agents/protocol.toml").write_text(
        source_cfg["protocol_path"].read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp / "AGENTS.md").write_text("# self-test AGENTS\n", encoding="utf-8")
    (tmp / ".gitignore").write_text(".agents/logs/\n.agents/runs/\n", encoding="utf-8")
    (tmp / "demo.txt").write_text("baseline\n", encoding="utf-8")
    _git_ok(tmp, "init", "-b", "main")
    _git_ok(tmp, "config", "user.email", "self-test@example.invalid")
    _git_ok(tmp, "config", "user.name", "HaruQuantAI Self Test")
    _git_ok(tmp, "add", ".")
    _git_ok(tmp, "commit", "--no-verify", "-m", "self-test baseline")
    stub = AGENTS_DIR / "tests" / "stub_agent.py"
    journals = {
        "planner": tmp / ".agents/task/planner.md",
        "executor": tmp / ".agents/task/executor.md",
        "reviewer": tmp / ".agents/task/reviewer.md",
    }
    roles: dict[str, dict[str, Any]] = {}
    for role in ("planner", "executor", "reviewer"):
        roles[role] = {
            "command": [sys.executable, str(stub), "--role", role, "--repo", str(tmp)],
            "prompt_delivery": "file",
        }
    protocol, transitions = _parse_protocol(tmp / ".agents/protocol.toml")
    policy_roles = {
        role: RolePolicy(
            vendor="codex",
            brand="codex",
            model="stub",
            effort="high",
            legacy_command=tuple(config["command"]),
        )
        for role, config in roles.items()
    }
    runtime_policy = RuntimePolicy(
        schema_version=3,
        mode="delegate-multi",
        approval_policy="unattended",
        max_iterations=3,
        roles=policy_roles,
        unattended=UnattendedPolicy(
            allow_execute=True,
            allow_local_commit=True,
            allow_local_merge=True,
        ),
        recovery=RecoveryPolicy(),
    )
    return {
        "repo": tmp,
        "main_branch": "main",
        "max_iterations": 3,
        "timeout": 60,
        "stream": False,
        "heartbeat": 0,
        "retries": 0,
        "protocol": protocol,
        "session_continuity": cast(
            "dict[str, Any]", protocol.get("session_continuity", {})
        ),
        "transitions": transitions,
        "protocol_path": tmp / ".agents/protocol.toml",
        "journals": journals,
        "next_agent": tmp / ".agents/task/next-agent.md",
        "templates": {
            "planner": tmp / "docs/templates/prompt/planner.md",
            "executor": tmp / "docs/templates/prompt/executor.md",
            "reviewer": tmp / "docs/templates/prompt/reviewer.md",
            "reviewer_closeout": tmp / "docs/templates/prompt/reviewer-closeout.md",
            "default": tmp / "docs/templates/prompt/default.md",
        },
        "logs_dir": tmp / ".agents/logs",
        "runs_dir": tmp / ".agents/runs",
        "roles": roles,
        "mode": "delegate-multi",
        "runtime_policy": runtime_policy,
    }


def cmd_self_test(_args: argparse.Namespace) -> int:
    """Run the bounded workflow integration self-test."""
    source_cfg = assemble_config(str(REPO_ROOT))
    tmp = Path(tempfile.mkdtemp(prefix="hq-agent-workflow-v3-"))
    print(f"[self-test] {tmp}")
    try:
        cfg = _init_self_test_repo(tmp, source_cfg)
        baseline = _entry_gate(cfg)
        state = create_task_state(
            {
                "task_kind": "feature",
                "task_id": "FEAT-DEMO",
                "task_slug": "demo",
                "task_name": "Demo",
                "task_request": "Exercise workflow v2.",
                "additional_context": "None",
                "exclusions": "None",
                "owner_execution_notes": "None",
                "review_focus": "Anti-anchoring",
            },
            baseline,
            run_id="self-test",
        )
        policy = cast("RuntimePolicy", cfg["runtime_policy"])
        state["runtime_policy_fingerprint"] = policy.fingerprint
        state["scope_fingerprint"] = scope_fingerprint(state["task"])
        state["effective_max_iterations"] = policy.max_iterations
        result = resume_task_run(cfg, state)
        checks: dict[str, bool] = {
            "status accepted": result.get("status") == "ACCEPTED",
            "reached iteration 3": result.get("iteration") == 3,
            "blocker recorded": any(
                item.get("raised_by") == "EXECUTOR"
                for item in cast("list[dict[str, Any]]", result.get("blockers", []))
            ),
            "owner approval no Planner approval phase": all(
                item.get("phase") != "approval_record"
                for item in cast("list[dict[str, Any]]", result.get("history", []))
            ),
            "task activation recorded": any(
                item.get("phase") == "task_activation"
                for item in cast("list[dict[str, Any]]", result.get("history", []))
            ),
            "all active files empty": all(
                path.stat().st_size == 0
                for path in [*cfg["journals"].values(), cfg["next_agent"]]
            ),
            "main clean": _git_ok(tmp, "status", "--porcelain") == "",
            "returned to main": _git_ok(tmp, "branch", "--show-current") == "main",
            "prompt hashes recorded": any(
                item.get("phase") == "execute_authorization"
                for item in cast("list[dict[str, Any]]", result.get("history", []))
            ),
            "commit contains only approved path": _git_ok(
                tmp, "diff", "--name-only", f"{baseline}..HEAD"
            )
            == "demo.txt",
        }
        failed = [name for name, passed in checks.items() if not passed]
        for name, passed in checks.items():
            print(f"[{'ok' if passed else 'FAIL'}] {name}")
        if failed:
            print(f"SELF-TEST FAILED: {failed}")
            return 1
        print("SELF-TEST PASSED")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=None)
    parser.add_argument("--approved", action="store_true")
    parser.add_argument("--reject-feedback", default=None)
    parser.add_argument("--approved-commit", action="store_true")
    parser.add_argument("--reject-commit-feedback", default=None)
    parser.add_argument("--role-complete", action="store_true")
    parser.add_argument("--app-agent-id", default=None)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for workflow lifecycle commands."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    subs = parser.add_subparsers(dest="command", required=True)

    start = subs.add_parser("start")
    start.add_argument("--task-file", default=None)
    start.add_argument("--task-kind", default=None)
    start.add_argument("--task-id", default=None)
    start.add_argument("--task-slug", default=None)
    start.add_argument("--task-name", default=None)
    start.add_argument("--task-request", default=None)
    start.add_argument("--additional-context", default=None)
    start.add_argument("--exclusions", default=None)
    start.add_argument("--owner-execution-notes", default=None)
    start.add_argument("--review-focus", default=None)
    start.add_argument("--implementation-file", default=None)
    start.add_argument("--implementation-entry", default=None)
    _add_common(start)
    start.set_defaults(func=cmd_start)

    resume = subs.add_parser("resume")
    resume.add_argument("--run-id", default=None)
    resume.add_argument("--resolve-planner-blocker", default=None)
    _add_common(resume)
    resume.set_defaults(func=cmd_resume)

    cancel = subs.add_parser("cancel")
    cancel.add_argument("--run-id", default=None)
    cancel.add_argument("--reason", default=None)
    cancel.add_argument("--repo", default=None)
    cancel.set_defaults(func=cmd_cancel)

    recover_scope = subs.add_parser("recover-scope-blocker")
    recover_scope.add_argument("--run-id", required=True)
    recover_scope.add_argument("--repo", default=None)
    recover_scope.set_defaults(func=cmd_recover_scope_blocker)

    goal_start = subs.add_parser("goal-start")
    goal_start.add_argument("--goal-file", default=".agents/goal.toml")
    _add_common(goal_start)
    goal_start.set_defaults(func=cmd_goal_start)

    goal_resume = subs.add_parser("goal-resume")
    goal_resume.add_argument("--goal-run-id", default=None)
    goal_resume.add_argument("--resolve-planner-blocker", default=None)
    goal_resume.add_argument("--stop-after-current-child", action="store_true")
    goal_resume.add_argument(
        "--claim-child-chat",
        default=None,
        help="claim the exact persisted solo Goal child-chat handoff",
    )
    _add_common(goal_resume)
    goal_resume.set_defaults(func=cmd_goal_resume)

    goal_status = subs.add_parser("goal-status")
    goal_status.add_argument("--goal-run-id", default=None)
    goal_status.add_argument("--repo", default=None)
    goal_status.set_defaults(func=cmd_goal_status)

    goal_cancel = subs.add_parser("goal-cancel")
    goal_cancel.add_argument("--goal-run-id", default=None)
    goal_cancel.add_argument("--reason", default=None)
    goal_cancel.add_argument("--repo", default=None)
    goal_cancel.set_defaults(func=cmd_goal_cancel)

    goal_recover_scope = subs.add_parser("goal-recover-scope-blocker")
    goal_recover_scope.add_argument("--goal-run-id", required=True)
    goal_recover_scope.add_argument("--repo", default=None)
    goal_recover_scope.set_defaults(func=cmd_goal_recover_scope_blocker)

    goal_recover_planner = subs.add_parser("goal-recover-planner-handoff")
    goal_recover_planner.add_argument("--goal-run-id", required=True)
    goal_recover_planner.add_argument("--task-run-id", required=True)
    goal_recover_planner.add_argument("--planner-session-id", required=True)
    goal_recover_planner.add_argument("--worktree-fingerprint", required=True)
    goal_recover_planner.add_argument("--repo", required=True)
    goal_recover_planner.set_defaults(func=cmd_goal_recover_planner_handoff)

    goal_correct_executor = subs.add_parser("goal-correct-executor-handoff")
    goal_correct_executor.add_argument("--goal-run-id", required=True)
    goal_correct_executor.add_argument("--task-run-id", required=True)
    goal_correct_executor.add_argument("--executor-session-id", required=True)
    goal_correct_executor.add_argument("--worktree-fingerprint", required=True)
    goal_correct_executor.add_argument("--repo", required=True)
    goal_correct_executor.set_defaults(func=cmd_goal_correct_executor_handoff)

    goal_correct_reviewer = subs.add_parser("goal-correct-reviewer-handoff")
    goal_correct_reviewer.add_argument("--goal-run-id", required=True)
    goal_correct_reviewer.add_argument("--task-run-id", required=True)
    goal_correct_reviewer.add_argument("--reviewer-session-id", required=True)
    goal_correct_reviewer.add_argument("--worktree-fingerprint", required=True)
    goal_correct_reviewer.add_argument("--repo", required=True)
    goal_correct_reviewer.set_defaults(func=cmd_goal_correct_reviewer_handoff)

    goal_recover_max = subs.add_parser("goal-recover-max-iterations")
    goal_recover_max.add_argument("--goal-run-id", required=True)
    goal_recover_max.add_argument("--task-run-id", required=True)
    goal_recover_max.add_argument("--iteration", type=int, required=True)
    goal_recover_max.add_argument("--worktree-fingerprint", required=True)
    goal_recover_max.add_argument("--repo", required=True)
    goal_recover_max.set_defaults(func=cmd_goal_recover_max_iterations)

    goal_recover_closeout = subs.add_parser("goal-recover-completed-closeout")
    goal_recover_closeout.add_argument("--goal-run-id", required=True)
    goal_recover_closeout.add_argument("--task-run-id", required=True)
    goal_recover_closeout.add_argument("--iteration", type=int, required=True)
    goal_recover_closeout.add_argument("--merge-head", required=True)
    goal_recover_closeout.add_argument("--repo", required=True)
    goal_recover_closeout.set_defaults(func=cmd_goal_recover_completed_closeout)

    doctor = subs.add_parser("doctor")
    doctor.add_argument("--repo", default=None)
    doctor.set_defaults(func=cmd_doctor)

    self_test = subs.add_parser("self-test")
    self_test.set_defaults(func=cmd_self_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and execute the selected workflow command."""
    args = build_parser().parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        stream_obj = cast("Any", stream)
        with contextlib.suppress(OSError, ValueError):
            if hasattr(stream_obj, "reconfigure"):
                stream_obj.reconfigure(errors="replace")
    try:
        return int(args.func(args))
    except OrchestratorError as exc:
        print(f"\n[FAIL] {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
