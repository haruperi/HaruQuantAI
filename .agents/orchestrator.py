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
from session_runner import probe_adapter
from task_api import *
from goal_engine import (
    advance_goal,
    cancel_goal,
    format_goal_status,
    load_goal_spec,
    load_goal_state,
    start_goal,
)

AGENTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENTS_DIR.parent


def _require_cli_mode(cfg: dict[str, Any]) -> None:
    """Require the CLI process-runner transport."""
    mode = str(cfg.get("mode", "UNCONFIGURED"))
    if mode != "multi-delegate":
        if mode == "UNCONFIGURED":
            raise OrchestratorError(
                "Workflow mode is UNCONFIGURED; run .agents/configure.py first."
            )
        raise OrchestratorError(
            f"CLI Task/Goal execution is only available in multi-delegate mode; "
            f"configured mode is {mode!r}. Use its documented chat/manual transport."
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
    _require_cli_mode(cfg)
    if args.max_iterations:
        cfg["max_iterations"] = args.max_iterations
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        state = prepare_task_run(cfg, _collect_task(args))
        try:
            result = resume_task_run(
                cfg,
                state,
                auto_approve=args.auto_approve,
                approved=args.approved,
                reject_feedback=args.reject_feedback,
                commit_approved=args.approved_commit,
                commit_reject_feedback=args.reject_commit_feedback,
            )
        except KeyboardInterrupt:
            _save_state(cfg, state)
            print("\nStopped by owner; Task run state saved.")
            return 130
        return 0 if result.get("status") == "ACCEPTED" else 0
    finally:
        lock.release()


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume a saved workflow run from its persisted phase."""
    cfg = assemble_config(args.repo)
    _require_cli_mode(cfg)
    if args.max_iterations:
        cfg["max_iterations"] = args.max_iterations
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
                auto_approve=args.auto_approve,
                approved=args.approved,
                reject_feedback=args.reject_feedback,
                commit_approved=args.approved_commit,
                commit_reject_feedback=args.reject_commit_feedback,
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


def cmd_goal_start(args: argparse.Namespace) -> int:
    """Freeze one Goal and begin its first ordinary child Task."""
    cfg = assemble_config(args.repo)
    _require_cli_mode(cfg)
    if args.max_iterations:
        cfg["max_iterations"] = args.max_iterations
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
                auto_approve=args.auto_approve,
                approved=args.approved,
                reject_feedback=args.reject_feedback,
                commit_approved=args.approved_commit,
                commit_reject_feedback=args.reject_commit_feedback,
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
    _require_cli_mode(cfg)
    if args.max_iterations:
        cfg["max_iterations"] = args.max_iterations
    lock = WorkflowLock(cfg["repo"])
    lock.acquire()
    try:
        state = load_goal_state(cfg, args.goal_run_id)
        try:
            state = advance_goal(
                cfg,
                state,
                auto_approve=args.auto_approve,
                approved=args.approved,
                reject_feedback=args.reject_feedback,
                commit_approved=args.approved_commit,
                commit_reject_feedback=args.reject_commit_feedback,
                resolve_planner_blocker=args.resolve_planner_blocker,
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
        key = (transition.source_role, transition.handoff)
        if key in seen:
            print(f"[FAIL] duplicate transition: {key}")
            ok = False
        seen.add(key)
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
    for role, role_cfg in cfg["roles"].items():
        command = cast("list[str]", role_cfg.get("command", []))
        runner_ok = bool(command) and shutil.which(command[0]) is not None
        if mode == "multi-delegate":
            adapter = str(role_cfg.get("session_adapter", ""))
            continuity_required = role_cfg.get("session_continuity") == "required"
            adapter_ok, detail = probe_adapter(adapter) if adapter else (False, "missing adapter")
            print(
                f"[{'ok' if runner_ok else 'FAIL'}] role {role} session runner: "
                f"{command[:1]}"
            )
            print(f"[{'ok' if adapter_ok else 'FAIL'}] role {role} session adapter: {detail}")
            ok = ok and runner_ok and continuity_required and adapter_ok
        else:
            print(f"[N/A] role {role} CLI is unused in {mode} mode")
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
        target_name = "reviewer-closeout.md" if key == "reviewer_closeout" else source.name
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
    return {
        "repo": tmp,
        "main_branch": "main",
        "max_iterations": 3,
        "timeout": 60,
        "stream": False,
        "heartbeat": 0,
        "retries": 0,
        "protocol": protocol,
        "session_continuity": cast("dict[str, Any]", protocol.get("session_continuity", {})),
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
    }


def cmd_self_test(_args: argparse.Namespace) -> int:
    """Run the bounded workflow integration self-test."""
    source_cfg = assemble_config(str(REPO_ROOT))
    tmp = Path(tempfile.mkdtemp(prefix="hq-agent-workflow-v2-"))
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
        result = resume_task_run(cfg, state, auto_approve=True)
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
                item.get("phase") == "owner_approval"
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
    parser.add_argument("--auto-approve", action="store_true")
    parser.add_argument("--approved", action="store_true")
    parser.add_argument("--reject-feedback", default=None)
    parser.add_argument("--approved-commit", action="store_true")
    parser.add_argument("--reject-commit-feedback", default=None)
    parser.add_argument("--max-iterations", type=int, default=0)


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

    goal_start = subs.add_parser("goal-start")
    goal_start.add_argument("--goal-file", default=".agents/goal.toml")
    _add_common(goal_start)
    goal_start.set_defaults(func=cmd_goal_start)

    goal_resume = subs.add_parser("goal-resume")
    goal_resume.add_argument("--goal-run-id", default=None)
    goal_resume.add_argument("--resolve-planner-blocker", default=None)
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
