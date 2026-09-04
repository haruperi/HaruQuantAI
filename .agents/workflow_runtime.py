#!/usr/bin/env python3
"""Process, state, and invocation helpers for the HaruQuantAI agent workflow."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import TracebackType
from typing import IO, Any, TextIO, cast

# Cross-platform file locking
try:
    import fcntl  # Unix

    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False

try:
    import msvcrt  # Windows

    _HAS_MSVCRT = True
except ImportError:
    _HAS_MSVCRT = False

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ide_transport import *
from runtime_policy import RuntimePolicy, load_runtime_policy, scope_fingerprint
from workflow_protocol import (
    SCHEMA_VERSION,
    OrchestratorError,
    _ensure_pending_artifact_unchanged,
    _git,
    _git_ok,
    _normalize_path_list,
    _render_next_agent,
    _transition_for,
    capture_repository_snapshot,
    compose_prompt,
    compute_snapshot_delta,
    parse_next_agent,
    validate_next_agent,
    validate_no_commits,
    validate_role_branch,
    validate_role_mutations,
)

# Phase 9: Concurrency protection
_WORKFLOW_LOCK_FILE = ".agents/workflow.lock"


class WorkflowLock:
    """Cross-process file lock to prevent concurrent orchestrator runs."""

    def __init__(self, repo: Path) -> None:
        self.lock_path = repo / _WORKFLOW_LOCK_FILE
        self.lock_file: TextIO | None = None

    def acquire(self) -> None:
        """Acquire exclusive lock. Raises OrchestratorError if already locked."""
        try:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            self.lock_file = self.lock_path.open("a+", encoding="utf-8")
            self.lock_file.seek(0)
            self.lock_file.write("0")
            self.lock_file.flush()
            self.lock_file.seek(0)

            if _HAS_MSVCRT:
                # Windows: use msvcrt.locking
                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            elif _HAS_FCNTL:
                # Unix: use fcntl
                cast("Any", fcntl).flock(
                    self.lock_file.fileno(),
                    cast("Any", fcntl).LOCK_EX | cast("Any", fcntl).LOCK_NB,
                )
            else:
                raise OrchestratorError(
                    "No supported operating-system file lock is available."
                )

            self.lock_file.seek(0)
            self.lock_file.truncate()
            self.lock_file.write(f"Locked by PID {os.getpid()}\n")
            self.lock_file.flush()
        except OSError as exc:
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            raise OrchestratorError(
                "Another orchestrator instance is already running."
            ) from exc

    def release(self) -> None:
        """Release the lock."""
        if self.lock_file:
            try:
                if _HAS_MSVCRT:
                    try:
                        msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    except OSError:
                        pass
                elif _HAS_FCNTL:
                    cast("Any", fcntl).flock(
                        self.lock_file.fileno(), cast("Any", fcntl).LOCK_UN
                    )

                self.lock_file.close()
                self.lock_file = None
                if self.lock_path.exists():
                    self.lock_path.unlink()
            except OSError:
                pass

    def __enter__(self) -> WorkflowLock:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.release()


def _stream_reader(
    stream: IO[str],
    sink: list[str],
    prefix: str,
    enabled: bool,
    activity: dict[str, float],
) -> None:
    try:
        for raw in stream:
            line = raw.rstrip("\r\n")
            sink.append(line)
            activity["t"] = time.monotonic()
            if enabled and line.strip():
                print(f"    {prefix}{line}", flush=True)
    finally:
        stream.close()


def _run_process(
    cmd: list[str],
    cwd: Path,
    stdin_text: str | None,
    *,
    timeout: int,
    stream: bool,
    heartbeat: int,
) -> tuple[int, str, str]:
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        raise OrchestratorError(f"Failed to launch {cmd[0]!r}: {exc}") from exc
    out: list[str] = []
    err: list[str] = []
    activity = {"t": time.monotonic()}
    threads = [
        threading.Thread(
            target=_stream_reader,
            args=(proc.stdout, out, "| ", stream, activity),
            daemon=True,
        ),
        threading.Thread(
            target=_stream_reader,
            args=(proc.stderr, err, "! ", stream, activity),
            daemon=True,
        ),
    ]
    for thread in threads:
        thread.start()
    if stdin_text is not None and proc.stdin is not None:
        proc.stdin.write(stdin_text)
        proc.stdin.close()
    started = time.monotonic()
    last_beat = started
    try:
        while proc.poll() is None:
            if time.monotonic() - started > timeout:
                proc.kill()
                raise OrchestratorError(f"Agent invocation timed out after {timeout}s.")
            now = time.monotonic()
            if (
                heartbeat > 0
                and now - activity["t"] >= heartbeat
                and now - last_beat >= heartbeat
            ):
                print(f"    [{int(now - started)}s] agent still running...", flush=True)
                last_beat = now
            time.sleep(0.2)
    finally:
        for thread in threads:
            thread.join(timeout=5)
    return proc.returncode or 0, "\n".join(out), "\n".join(err)


def _build_agent_command(
    role_cfg: dict[str, Any], prompt: str, prompt_file: Path, generation: str = "normal"
) -> tuple[list[str], str | None]:
    command = [
        generation if token == "{generation}" else token
        for token in role_cfg["command"]
    ]
    model_args = list(role_cfg.get("model_args", []))
    delivery = str(role_cfg.get("prompt_delivery", "file"))
    stdin_text: str | None = None
    if delivery == "stdin":
        stdin_text = prompt
        cmd = command + model_args
    elif delivery == "arg":
        cmd = [prompt if token == "{prompt}" else token for token in command]
        if "{prompt}" not in command:
            cmd += model_args + [prompt]
    else:
        prompt_file.write_text(prompt, encoding="utf-8")
        pointer = (
            f"Read and follow the instructions in {prompt_file} exactly. "
            "Perform the full task described there now."
        )
        cmd = [pointer if token == "{prompt}" else token for token in command]
        if "{prompt}" not in command:
            cmd += model_args + [pointer]
    return cmd, stdin_text


def run_agent(
    cfg: dict[str, Any],
    role: str,
    prompt: str,
    tag: str,
    *,
    generation: str = "normal",
) -> tuple[str, Path]:
    logs_dir: Path = cfg["logs_dir"]
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%d-%H%M%S")
    prompt_file = logs_dir / f"{stamp}-{tag}-prompt.md"
    policy = cfg.get("runtime_policy")
    if isinstance(policy, RuntimePolicy):
        role_cfg = policy.role_config(role, generation=generation)
    else:
        role_cfg = cast("dict[str, Any]", cfg["roles"][role.lower()])
    cmd, stdin_text = _build_agent_command(
        role_cfg, prompt, prompt_file, generation=generation
    )
    executable = shutil.which(cmd[0])
    if executable is None:
        raise OrchestratorError(f"Agent CLI {cmd[0]!r} is not on PATH.")
    cmd[0] = executable
    attempts = max(1, int(cfg["retries"]) + 1)
    last_error = ""
    for attempt in range(1, attempts + 1):
        if attempt > 1:
            print(f"    retry {attempt}/{attempts} after non-zero exit")
            time.sleep(1)
        attempt_before = capture_repository_snapshot(cfg["repo"])
        head_before = _git_ok(cfg["repo"], "rev-parse", "HEAD")
        branch_before = _git_ok(cfg["repo"], "branch", "--show-current")
        code, stdout, stderr = _run_process(
            cmd,
            cfg["repo"],
            stdin_text,
            timeout=int(cfg["timeout"]),
            stream=bool(cfg["stream"]),
            heartbeat=int(cfg["heartbeat"]),
        )
        log = (
            logs_dir
            / f"{stamp}-{tag}{'-retry' + str(attempt - 1) if attempt > 1 else ''}.log"
        )
        log.write_text(
            f"command: {cmd!r}\nexit_code: {code}\n"
            f"{'=' * 20} stdout {'=' * 20}\n{stdout}\n"
            f"{'=' * 20} stderr {'=' * 20}\n{stderr}\n",
            encoding="utf-8",
        )
        if code == 0:
            return stdout, log
        attempt_after = capture_repository_snapshot(cfg["repo"])
        delta = compute_snapshot_delta(attempt_before, attempt_after)
        mutated = any(delta[kind] for kind in ("created", "modified", "deleted"))
        mutated = mutated or _git_ok(cfg["repo"], "rev-parse", "HEAD") != head_before
        mutated = mutated or (
            _git_ok(cfg["repo"], "branch", "--show-current") != branch_before
        )
        if mutated:
            raise OrchestratorError(
                f"{role} mutated repository state before failing; "
                "automatic retry suppressed."
            )
        last_error = stderr or stdout
    raise OrchestratorError(
        f"{role} agent failed after {attempts} attempt(s): {last_error[-500:]}"
    )


def _save_state(cfg: dict[str, Any], state: dict[str, Any]) -> Path:
    runs_dir: Path = cfg["runs_dir"]
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{state['run_id']}.json"
    path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return path


def _load_state(cfg: dict[str, Any], run_id: str | None) -> dict[str, Any]:
    runs_dir: Path = cfg["runs_dir"]
    if run_id:
        path = runs_dir / f"{run_id}.json"
    else:
        candidates = sorted(runs_dir.glob("*.json"))
        if not candidates:
            raise OrchestratorError("No saved runs found.")
        path = candidates[-1]
    if not path.exists():
        raise OrchestratorError(f"Run state not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OrchestratorError(f"Invalid run state: {path}")
    return cast("dict[str, Any]", data)


def _record(state: dict[str, Any], phase: str, **extra: Any) -> None:
    entry = {
        "time": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
        "phase": phase,
        "iteration": state["iteration"],
        **extra,
    }
    state.setdefault("history", []).append(entry)


def _entry_gate(cfg: dict[str, Any]) -> str:
    repo: Path = cfg["repo"]
    if not (repo / ".git").exists():
        raise OrchestratorError(f"{repo} is not a git repository.")
    branch = _git_ok(repo, "branch", "--show-current")
    if branch != cfg["main_branch"]:
        raise OrchestratorError(
            f"New task must start on {cfg['main_branch']!r}; current branch is {branch!r}."
        )
    dirty = _git_ok(repo, "status", "--porcelain")
    if dirty:
        raise OrchestratorError(f"main must be clean before starting:\n{dirty}")
    active_files = [*cfg["journals"].values(), cfg["next_agent"]]
    for path in active_files:
        if not path.exists():
            raise OrchestratorError(f"Missing active-task file: {path}")
        if path.stat().st_size != 0:
            raise OrchestratorError(f"Active-task file is not empty: {path}")
    return str(_git_ok(repo, "rev-parse", "HEAD"))


def _branch_component(value: str) -> str:
    component = re.sub(r"[^a-z0-9._-]+", "-", value.lower().replace("_", "-"))
    component = component.strip("-.")
    if not component:
        raise OrchestratorError(f"Cannot derive branch component from {value!r}.")
    return str(component)


def _derive_task_branch(task: dict[str, Any]) -> str:
    """Derive the deterministic task branch from validated task metadata."""
    prefix = (
        "feature"
        if str(task.get("task_kind", "feature")).lower() == "feature"
        else "task"
    )
    task_id = _branch_component(str(task["task_id"]))
    slug = _branch_component(str(task["task_slug"]))
    return f"{prefix}/{task_id}-{slug}"


def _build_fields(state: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    task = cast("dict[str, Any]", state["task"])
    return {
        "repo_path": str(cfg["repo"]),
        "run_id": state["run_id"],
        "task_kind": task.get("task_kind", "feature"),
        "task_id": task["task_id"],
        "task_slug": task["task_slug"],
        "task_name": task.get("task_name", task["task_id"]),
        "task_request": task["task_request"],
        "additional_context": task.get("additional_context", "None"),
        "exclusions": task.get("exclusions", "None"),
        "owner_execution_notes": task.get("owner_execution_notes", "None"),
        "review_focus": task.get("review_focus", "None"),
        "implementation_file": task.get("implementation_file", "(none)"),
        "implementation_entry": task.get("implementation_entry", "(none)"),
        "iteration": state["iteration"],
        "branch": state.get("branch") or "(created by orchestrator during activation)",
        "baseline_commit": state["baseline"],
        "correction_context": state.get("correction_context", "None"),
        "owner_feedback": state.get("owner_feedback", "None") or "None",
        "approved_plan_hash": state.get(
            "approved_plan_hash", "(recorded after owner gate)"
        ),
        "executor_report_hash": state.get(
            "executor_report_hash", "(not available yet)"
        ),
        "blocker_ledger": _blocker_ledger(state),
        "handoff_facts": state.get(
            "handoff_facts", "See active journals and repository evidence."
        ),
        "reviewed_worktree_hash": state.get(
            "reviewed_worktree_hash", "(recorded by orchestrator)"
        ),
        "reviewed_head": state.get("reviewed_head", "(recorded by orchestrator)"),
        "commit_authorization_source": state.get(
            "commit_authorization_source", "(not authorized yet)"
        ),
        "runtime_policy_fingerprint": state.get(
            "runtime_policy_fingerprint", "(legacy interactive run)"
        ),
        "scope_fingerprint": state.get("scope_fingerprint", "(legacy Task run)"),
    }


def _blocker_ledger(state: dict[str, Any]) -> str:
    blockers = cast("list[dict[str, Any]]", state.get("blockers", []))
    if not blockers:
        return "None"
    return "; ".join(
        f"{item['raised_by']} iteration {item['iteration']} ({item['status']})"
        for item in blockers
    )


def _activate_task(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    """Create/verify the task branch and materialize the initial Planner artifact."""
    repo: Path = cfg["repo"]
    baseline = str(state["baseline"])
    quick_fix = state.get("runtime_mode") == "quick-fix"
    branch = str(
        state.get("branch")
        or (
            cfg["main_branch"]
            if quick_fix
            else _derive_task_branch(cast("dict[str, Any]", state["task"]))
        )
    )
    current_branch = _git_ok(repo, "branch", "--show-current")
    current_head = _git_ok(repo, "rev-parse", "HEAD")

    if state.get("branch"):
        if current_branch != branch:
            raise OrchestratorError(
                f"Task activation expected branch {branch!r}; current branch is {current_branch!r}."
            )
        if current_head != baseline:
            raise OrchestratorError(
                "Task branch HEAD changed before initial Planner activation."
            )
    elif quick_fix:
        if current_branch != cfg["main_branch"] or current_head != baseline:
            raise OrchestratorError(
                "Quick-Fix activation requires the recorded clean main baseline."
            )
        state["branch"] = branch
        _record(state, "quick_fix_main_selected", branch=branch)
        _save_state(cfg, state)
    else:
        if current_branch != cfg["main_branch"] or current_head != baseline:
            raise OrchestratorError(
                "Task activation must begin from the recorded clean main baseline."
            )
        check = _git(repo, "check-ref-format", "--branch", branch)
        if check.returncode != 0:
            raise OrchestratorError(f"Derived task branch is invalid: {branch!r}.")
        exists = _git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
        if exists.returncode == 0:
            raise OrchestratorError(f"Task branch already exists: {branch!r}.")
        _git_ok(repo, "switch", "-c", branch, baseline)
        state["branch"] = branch
        state["phase"] = "task_activation"
        _record(state, "task_branch_created", branch=branch)
        _save_state(cfg, state)

    activation = "QUICK_FIX_ACTIVATED" if quick_fix else "TASK_ACTIVATED"
    template_key = "quick_fix_planner" if quick_fix else "planner"
    body = compose_prompt(cfg["templates"][template_key], _build_fields(state, cfg))
    transition = _transition_for(cfg["transitions"], "ORCHESTRATOR", activation)
    metadata = {
        "prompt_schema_version": SCHEMA_VERSION,
        "run_id": state["run_id"],
        "task_id": state["task"]["task_id"],
        "iteration": state["iteration"],
        "source_role": "ORCHESTRATOR",
        "target_role": "PLANNER",
        "handoff": activation,
        "branch": branch,
        "baseline_commit": baseline,
        "source_head": _git_ok(repo, "rev-parse", "HEAD"),
        "template_path": transition.target_template
        or str(cfg["templates"][template_key].relative_to(repo)).replace("\\", "/"),
        "requires_owner_gate": False,
        "owner_gate": "",
    }
    cfg["next_agent"].write_text(_render_next_agent(metadata, body), encoding="utf-8")
    validate_next_agent(
        cfg,
        state,
        expected_source="ORCHESTRATOR",
        expected_handoff=activation,
    )
    state["phase"] = "planner"
    _record(state, "task_activation", handoff=activation, branch=branch)
    _save_state(cfg, state)


def _append_gate_authorization(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    source: str,
) -> None:
    journal: Path = cfg["journals"]["planner"]
    plan_hash = state["plan_hash"]
    # Extract approved_write_paths from Planner's next-agent metadata
    next_agent_path = cfg["next_agent"]
    if next_agent_path.exists() and next_agent_path.stat().st_size > 0:
        artifact = parse_next_agent(next_agent_path)
        approved_paths_raw = artifact.metadata.get("allowed_write_paths", [])
        if isinstance(approved_paths_raw, list):
            approved_write_paths = _normalize_path_list(approved_paths_raw)
        else:
            approved_write_paths = []
    else:
        approved_write_paths = []
    state["approved_write_paths"] = approved_write_paths
    # Build a truthful gate record. The protocol label is stable while the
    # source distinguishes an exact owner message from frozen run policy.
    block = (
        f"### Owner Gate — Dry Run {state['iteration']}\n\n"
        "Gate: APPROVED: EXECUTE\n"
        f"Authorization source: {source}\n"
        f"Task ID: {state['task']['task_id']}\n"
        f"Dry Run: {state['iteration']}\n"
        f"Plan SHA-256: {plan_hash}\n"
        f"Main baseline: {state['baseline']}\n"
        f"Task branch: {state['branch']}\n"
    )
    if source == "RUN_PREAUTHORIZATION":
        block += (
            f"Runtime policy SHA-256: {state['runtime_policy_fingerprint']}\n"
            f"Frozen scope SHA-256: {state['scope_fingerprint']}\n"
        )
    if approved_write_paths:
        block += "Approved write paths:\n"
        for path in approved_write_paths:
            block += f"  - {path}\n"
    with journal.open("a", encoding="utf-8") as handle:
        handle.write(block)
    state["approved_plan_hash"] = plan_hash
    state["execute_authorization_source"] = source


def _write_orchestrator_planner_prompt(
    cfg: dict[str, Any], state: dict[str, Any], source_handoff: str
) -> None:
    fields = _build_fields(state, cfg)
    quick_fix = state.get("runtime_mode") == "quick-fix"
    template_key = "quick_fix_planner" if quick_fix else "planner"
    body = compose_prompt(cfg["templates"][template_key], fields)
    transition = _transition_for(cfg["transitions"], "ORCHESTRATOR", source_handoff)
    metadata = {
        "prompt_schema_version": SCHEMA_VERSION,
        "run_id": state["run_id"],
        "task_id": state["task"]["task_id"],
        "iteration": state["iteration"],
        "source_role": "ORCHESTRATOR",
        "target_role": "PLANNER",
        "handoff": source_handoff,
        "branch": state["branch"],
        "baseline_commit": state["baseline"],
        "source_head": _git_ok(cfg["repo"], "rev-parse", "HEAD"),
        "template_path": transition.target_template
        or "docs/templates/prompt/planner.md",
        "requires_owner_gate": False,
        "owner_gate": "",
    }
    cfg["next_agent"].write_text(_render_next_agent(metadata, body), encoding="utf-8")
    validate_next_agent(
        cfg, state, expected_source="ORCHESTRATOR", expected_handoff=source_handoff
    )


def _request_gate(
    exact: str, label: str, scripted: bool, rejection: str | None
) -> tuple[bool, str]:
    if scripted:
        print(f"[gate] relaying exact owner authorization: {exact}")
        return True, ""
    if rejection is not None:
        return False, rejection
    print(f"\n{label} required. Enter exactly `{exact}`, `reject`, or `abort`.")
    while True:
        try:
            answer = input("> ").strip()
        except EOFError:
            answer = "abort"
        if answer == exact:
            return True, ""
        if answer.lower() == "reject":
            feedback = input("Feedback: ").strip()
            return False, feedback
        if answer.lower() == "abort":
            raise KeyboardInterrupt
        print("Unrecognized gate response.")


def _ensure_runtime_policy_unchanged(
    cfg: dict[str, Any], state: dict[str, Any]
) -> None:
    """Fail closed if a versioned runtime policy changes during a frozen run."""
    frozen = state.get("runtime_policy_fingerprint")
    if not frozen:
        return
    runtime_path = cfg.get("runtime_policy_path")
    if runtime_path is None:
        policy = cfg.get("runtime_policy")
        if not isinstance(policy, RuntimePolicy):
            raise OrchestratorError("Frozen run has no runtime policy to verify.")
    else:
        policy = load_runtime_policy(
            Path(runtime_path),
            legacy_roles=cast("dict[str, dict[str, Any]]", cfg.get("legacy_roles", {})),
            default_max_iterations=int(cfg["max_iterations"]),
        )
    if policy.fingerprint != frozen:
        raise OrchestratorError(
            "Runtime policy changed after run activation; start a new Task or restore "
            "the frozen policy before resuming."
        )
    frozen_scope = state.get("scope_fingerprint")
    if (
        frozen_scope
        and "task" in state
        and scope_fingerprint(state["task"]) != frozen_scope
    ):
        raise OrchestratorError("Frozen Task scope changed after run activation.")


def _gate_authorization(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    gate: str,
    owner_message: bool,
    rejection: str | None,
) -> tuple[bool, str, str]:
    """Resolve a gate from an owner message or frozen unattended policy."""
    _ensure_runtime_policy_unchanged(cfg, state)
    if rejection is not None:
        return False, rejection, ""
    if state.get("runtime_mode") == "quick-fix" and not owner_message:
        raise OrchestratorError(
            "Quick-Fix execution requires the exact interactive owner message."
        )
    if owner_message:
        decision, feedback = _request_gate(gate, "Owner authorization", True, None)
        return decision, feedback, "OWNER_MESSAGE"
    policy = cfg.get("runtime_policy")
    permitted = False
    if isinstance(policy, RuntimePolicy):
        permitted = (
            policy.can_preauthorize_execute()
            if gate == "APPROVED: EXECUTE"
            else policy.can_preauthorize_commit()
        )
    if permitted:
        if not state.get("runtime_policy_fingerprint") or not state.get(
            "scope_fingerprint"
        ):
            raise OrchestratorError(
                "Run preauthorization requires frozen runtime-policy and scope hashes."
            )
        print(f"[gate] {gate} satisfied by frozen run preauthorization")
        return True, "", "RUN_PREAUTHORIZATION"
    decision, feedback = _request_gate(
        gate,
        "Execution approval" if gate.endswith("EXECUTE") else "Commit authorization",
        False,
        None,
    )
    return decision, feedback, "OWNER_MESSAGE" if decision else ""


def _invoke_pending(
    cfg: dict[str, Any],
    state: dict[str, Any],
    role: str,
    *,
    authorized_closeout: bool = False,
) -> tuple[str, Path]:
    """Invoke the pending next-agent with snapshot/delta enforcement."""
    _ensure_runtime_policy_unchanged(cfg, state)
    if cfg.get("mode") in IDE_MODES:
        completion = cfg.get("_ide_role_completion")
        if not isinstance(completion, dict):
            raise OrchestratorError(
                "IDE role work must be prepared and explicitly completed."
            )
        return complete_ide_role(
            cfg,
            state,
            role,
            app_agent_id=cast("str | None", completion.get("app_agent_id")),
            authorized_closeout=authorized_closeout,
        )
    if cfg.get("mode") == "manual":
        raise OrchestratorError("Manual mode does not invoke reasoning-role processes.")
    _ensure_pending_artifact_unchanged(cfg, state)
    artifact = parse_next_agent(cfg["next_agent"])
    if str(artifact.metadata["target_role"]).upper() != role.upper():
        raise OrchestratorError(
            f"Pending prompt targets {artifact.metadata['target_role']}, not {role}."
        )
    # Pre-invocation checks: branch and HEAD
    branch = state.get("branch", "")
    baseline_head = _git_ok(cfg["repo"], "rev-parse", "HEAD")
    validate_role_branch(cfg["repo"], branch)
    # Capture pre-invocation snapshot
    snapshot_before = capture_repository_snapshot(cfg["repo"])
    # Run the agent
    result = run_agent(
        cfg,
        role,
        artifact.raw,
        f"{state['run_id']}-{role.lower()}-{state['iteration']}",
        generation=str(state.get("session_generation", "normal")),
    )
    if authorized_closeout:
        return result
    # Post-invocation: check no commits, branch unchanged, mutations authorized
    current_head = _git_ok(cfg["repo"], "rev-parse", "HEAD")
    validate_no_commits(cfg["repo"], baseline_head, current_head)
    validate_role_branch(cfg["repo"], branch)
    snapshot_after = capture_repository_snapshot(cfg["repo"])
    delta = compute_snapshot_delta(snapshot_before, snapshot_after)
    approved_write_paths = state.get("approved_write_paths")
    approved_set = set(approved_write_paths) if approved_write_paths else None
    validate_role_mutations(
        role,
        delta,
        approved_write_paths=approved_set,
    )
    return result


__all__ = [name for name in globals() if not name.startswith("__")]
