#!/usr/bin/env python3
"""Cross-brand Planner/Executor/Reviewer orchestrator for HaruQuantAI.

Drives the AGENTS.md three-role handoff state machine by launching each
role's coding agent non-interactively (any CLI brand: claude, codex, agy, ...).
The task journals in docs/dev/task/ are the shared memory between agents;
machine coordination uses a mandatory three-line block that each agent
writes at the end of its journal entry:

    STOPPED : <PLANNER|EXECUTOR|REVIEWER>
    ACTIVATING : <PLANNER|EXECUTOR|REVIEWER|NONE>
    HANDOFF : <PENDING_APPROVAL|APPROVED_EXECUTE|READY_FOR_REVIEW|
               CHANGES_REQUESTED|ACCEPTED|BLOCKED>

Exactly one agent runs at a time.

Subcommands:
    start      Run a new task through the full state machine.
    resume     Continue an interrupted run from its saved state.
    doctor     Validate configs, templates, CLIs, and repository gates.
    self-test  Exercise the whole state machine with stub agents (no real
               agent CLI calls, no cost).

Usage examples:
    python .agents/orchestrator.py doctor
    python .agents/orchestrator.py start --task-file .agents/task.example.toml
    python .agents/orchestrator.py resume
    python .agents/orchestrator.py self-test
"""

# pylint: disable=too-many-lines,too-many-arguments,too-many-locals

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, cast

AGENTS_DIR = Path(__file__).resolve().parent

VALID_HANDOFFS = {
    "PENDING_APPROVAL",
    "APPROVED_EXECUTE",
    "READY_FOR_REVIEW",
    "CHANGES_REQUESTED",
    "ACCEPTED",
    "BLOCKED",
}

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

# Whitespace around the colon is optional, and leading/trailing markdown
# decoration (fences, bold, backticks, headers, quote markers) is tolerated
# so `**STOPPED** : \`PLANNER\`` parses the same as `STOPPED : PLANNER`.
BLOCK_LINE_RES = {
    "stopped": re.compile(r"^[>\s#`*_-]*STOPPED[\s`*_-]*:\s*(.+?)\s*$", re.IGNORECASE),
    "activating": re.compile(
        r"^[>\s#`*_-]*ACTIVATING[\s`*_-]*:\s*(.+?)\s*$", re.IGNORECASE
    ),
    "handoff": re.compile(r"^[>\s#`*_-]*HANDOFF[\s`*_-]*:\s*(.+?)\s*$", re.IGNORECASE),
}

NEXT_NOTES_RE = re.compile(r"^\s*NEXT AGENT NOTES\s*:\s?(.*)$", re.IGNORECASE)

MAX_CMD_PREVIEW = 6
EXPECTED_SELF_TEST_ITERATION = 3
BLOCK_FIELD_COUNT = 3
MIN_SELF_TEST_LOG_FILES = 16
DEFAULT_TAIL_LINES = 30


class OrchestratorError(RuntimeError):
    """Fatal orchestration error; run state is saved before raising."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def load_toml(path: Path) -> dict[str, Any]:
    """Load and parse a TOML file from disk.

    Args:
        path: File path to the TOML document.

    Returns:
        Dictionary representing the parsed TOML document.
    """
    with path.open("rb") as fh:
        data: dict[str, Any] = tomllib.load(fh)
        return data


def assemble_config(repo_override: str | None = None) -> dict[str, Any]:
    """Load orchestrator.toml plus the three role TOMLs into one config map.

    Args:
        repo_override: Optional path string overriding the repository root.

    Returns:
        Consolidated orchestration configuration mapping.
    """
    orch = load_toml(AGENTS_DIR / "orchestrator.toml")
    run_cfg: dict[str, Any] = orch.get("run", {})
    paths: dict[str, Any] = orch.get("paths", {})

    default_repo = str(AGENTS_DIR.parent)
    repo = Path(repo_override or run_cfg.get("repo_path", default_repo)).resolve()
    journals = {
        "planner": repo / paths.get("planner_journal", "docs/dev/task/planner.md"),
        "executor": repo / paths.get("executor_journal", "docs/dev/task/executor.md"),
        "reviewer": repo / paths.get("reviewer_journal", "docs/dev/task/reviewer.md"),
    }
    templates = {
        "planner": repo / ".agents/templates/planner.md",
        "planner_approval": repo / ".agents/templates/planner_approval.md",
        "executor": repo / ".agents/templates/executor.md",
        "reviewer": repo / ".agents/templates/reviewer.md",
    }
    roles: dict[str, dict[str, Any]] = {}
    roles_cfg: dict[str, Any] = orch.get("roles", {})
    for role, filename in roles_cfg.items():
        role_cfg = load_toml(AGENTS_DIR / str(filename))
        role_cfg["template_path"] = (repo / str(role_cfg["template"])).resolve()
        if "approval_command" in role_cfg:
            role_cfg["approval_command"] = list(role_cfg["approval_command"])
        roles[role] = role_cfg

    return {
        "repo": repo,
        "main_branch": run_cfg.get("main_branch", "main"),
        "max_iterations": int(run_cfg.get("max_iterations", 5)),
        "timeout": int(run_cfg.get("invocation_timeout_seconds", 3600)),
        "journals": journals,
        "templates": templates,
        "logs_dir": (repo / paths.get("logs_dir", ".agents/logs")).resolve(),
        "runs_dir": (repo / paths.get("runs_dir", ".agents/runs")).resolve(),
        "roles": roles,
    }


# ---------------------------------------------------------------------------
# Prompt composition and agent invocation
# ---------------------------------------------------------------------------


def compose_prompt(template_path: Path, fields: dict[str, Any]) -> str:
    """Fill {{placeholder}} fields; refuse to run with any placeholder left.

    Args:
        template_path: Path to the markdown template file.
        fields: Mapping of placeholder keys to replacement values.

    Returns:
        Rendered prompt string.

    Raises:
        OrchestratorError: If unfilled placeholders remain in the prompt.
    """
    text = template_path.read_text(encoding="utf-8")
    for key, value in fields.items():
        text = text.replace("{{" + key + "}}", str(value))
    leftover = sorted(set(re.findall(r"\{\{\w+\}\}", text)))
    if leftover:
        msg = f"Template {template_path} has unfilled placeholders: {leftover}"
        raise OrchestratorError(msg)
    return text


def _build_agent_cmd(
    role_cfg: dict[str, Any],
    prompt: str,
    prompt_file: Path,
    *,
    approval: bool,
) -> tuple[list[str], str | None]:
    """Build the command line and optional stdin string for the agent.

    Args:
        role_cfg: Configuration dictionary for the agent role.
        prompt: Composed prompt string.
        prompt_file: Destination file path for file-based prompt delivery.
        approval: Whether this is an approval-recording invocation.

    Returns:
        Tuple of (command_args_list, stdin_text).
    """
    command = list(role_cfg.get("approval_command", []) if approval else [])
    if not command:
        command = list(role_cfg["command"])
    delivery = role_cfg.get("prompt_delivery", "file")
    model_args = list(role_cfg.get("model_args", []))

    stdin_text: str | None = None
    if delivery == "stdin":
        stdin_text = prompt
        cmd = command + model_args
    elif delivery == "arg":
        arg = prompt
        cmd = [arg if tok == "{prompt}" else tok for tok in command]
        if "{prompt}" not in command:
            cmd = cmd + model_args + [arg]
    else:  # "file"
        prompt_file.write_text(prompt, encoding="utf-8")
        arg = (
            f"Read and follow the instructions in {prompt_file} exactly. "
            "Perform the full task described there now."
        )
        cmd = [arg if tok == "{prompt}" else tok for tok in command]
        if "{prompt}" not in command:
            cmd = cmd + model_args + [arg]
    return cmd, stdin_text


def run_agent(
    role_cfg: dict[str, Any],
    prompt: str,
    cwd: Path,
    logs_dir: Path,
    tag: str,
    *,
    timeout: int,
    approval: bool = False,
) -> tuple[int, str, Path]:
    """Run one headless agent invocation; return (exit_code, stdout, log_path).

    Prompt delivery defaults to "file": the composed prompt is written under
    logs_dir and the agent receives a short pointer argument. This avoids
    passing megabyte prompts through argv, which is fragile on Windows where
    npm CLIs are .cmd shims re-parsed by cmd.exe.

    Args:
        role_cfg: Configuration dictionary for the agent role.
        prompt: Composed prompt string.
        cwd: Working directory for the process.
        logs_dir: Directory for writing run logs and prompt files.
        tag: Identifier tag used in log file naming.
        timeout: Maximum seconds before process is killed.
        approval: Whether this invocation is for approval recording.

    Returns:
        Tuple of (exit_code, stdout_content, log_file_path).

    Raises:
        OrchestratorError: If the CLI executable is missing or times out.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    now_utc = _dt.datetime.now(tz=_dt.UTC)
    stamp = now_utc.strftime("%Y%m%d-%H%M%S")
    prompt_file = logs_dir / f"{stamp}-{tag}-prompt.md"

    cmd, stdin_text = _build_agent_cmd(role_cfg, prompt, prompt_file, approval=approval)

    exe = shutil.which(cmd[0])
    if exe is None:
        cmd_str = role_cfg.get("command")
        msg = f"Agent CLI '{cmd[0]}' not found on PATH (role command: {cmd_str})"
        raise OrchestratorError(msg)
    cmd[0] = exe

    preview_tokens = " ".join(cmd[:MAX_CMD_PREVIEW])
    ellipsis_suffix = " ..." if len(cmd) > MAX_CMD_PREVIEW else ""
    print(f"    launching: {preview_tokens}{ellipsis_suffix}")
    try:
        proc = subprocess.run(  # noqa: S603
            cmd,
            cwd=str(cwd),
            input=stdin_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        code = proc.returncode
        out = proc.stdout or ""
        err = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        raw_out: Any = exc.stdout
        out = (
            raw_out.decode("utf-8", errors="replace")
            if isinstance(raw_out, bytes)
            else (raw_out or "")
        )
        raw_err: Any = exc.stderr
        err = (
            raw_err.decode("utf-8", errors="replace")
            if isinstance(raw_err, bytes)
            else (raw_err or "")
        )

        _write_log(
            logs_dir,
            stamp,
            tag,
            cmd,
            -1,
            out=out,
            err=err,
            note=f"TIMED OUT after {timeout}s",
        )
        timeout_msg = f"Agent invocation '{tag}' timed out after {timeout}s"
        raise OrchestratorError(timeout_msg) from exc

    log_path = _write_log(logs_dir, stamp, tag, cmd, code, out=out, err=err)
    if code != 0:
        print(f"[warn] agent exited with code {code}; see {log_path}")
    return code, out, log_path


def _write_log(
    logs_dir: Path,
    stamp: str,
    tag: str,
    cmd: list[str],
    code: int,
    *,
    out: str,
    err: str,
    note: str = "",
) -> Path:
    """Write process invocation output to a log file.

    Args:
        logs_dir: Target directory for log output.
        stamp: Timestamp string.
        tag: Identifier tag for the invocation.
        cmd: Executed command arguments.
        code: Return code of the process.
        out: Captured standard output.
        err: Captured standard error.
        note: Optional note (e.g. timeout indicator).

    Returns:
        Path to the created log file.
    """
    log_path = logs_dir / f"{stamp}-{tag}.log"
    body = (
        f"command: {cmd!r}\nexit_code: {code}\n{note}\n"
        f"{'=' * 20} stdout {'=' * 20}\n{out}\n"
        f"{'=' * 20} stderr {'=' * 20}\n{err}\n"
    )
    log_path.write_text(body, encoding="utf-8")
    return log_path


def print_log_tail(log_path: Path, lines: int = DEFAULT_TAIL_LINES) -> None:
    """Print the final lines of a log file to standard output.

    Args:
        log_path: Path to the log file.
        lines: Maximum number of trailing lines to print.
    """
    try:
        content = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    print(f"--- tail of {log_path} ---")
    for line in content[-lines:]:
        print(f"  {line}")


# ---------------------------------------------------------------------------
# Handoff markers and git state
# ---------------------------------------------------------------------------


def parse_handoff_block(lines: list[str]) -> dict[str, str] | None:
    """Parse the nearest STOPPED/ACTIVATING/HANDOFF triple from a line list.

    Scans backwards so earlier iterations' blocks are ignored.

    Args:
        lines: Lines of a journal or agent final answer.

    Returns:
        Mapping with 'stopped', 'activating', and 'handoff' keys converted to
        uppercase if all three lines are found, otherwise None.
    """
    block: dict[str, str] = {}
    for line in reversed(lines):
        for key, rx in BLOCK_LINE_RES.items():
            if key in block:
                continue
            match = rx.match(line)
            if match:
                value = match.group(1).strip("*`_ .;:\"'").upper()
                if value:
                    block[key] = value
        if len(block) == BLOCK_FIELD_COUNT:
            return block
    return None


def latest_handoff_block(journal: Path) -> dict[str, str] | None:
    """Read the most recent handoff block from a journal file.

    Args:
        journal: Path to the markdown journal file.

    Returns:
        Handoff block mapping if found, otherwise None.
    """
    if not journal.exists():
        return None
    lines = journal.read_text(encoding="utf-8", errors="replace").splitlines()
    return parse_handoff_block(lines)


def latest_handoff(journal: Path) -> str | None:
    """Return the most recent HANDOFF status value in a journal, if any.

    Args:
        journal: Path to the markdown journal file.

    Returns:
        The status string if found, otherwise None.
    """
    block = latest_handoff_block(journal)
    return block["handoff"] if block else None


def parse_next_notes(lines: list[str]) -> str:
    """Extract the last NEXT AGENT NOTES section, ending at the STOPPED line.

    Args:
        lines: Lines of a journal or agent final answer.

    Returns:
        The notes text (possibly multiline), or an empty string when absent.
    """
    start: int | None = None
    for idx in range(len(lines) - 1, -1, -1):
        if NEXT_NOTES_RE.match(lines[idx]):
            start = idx
            break
    if start is None:
        return ""
    first = NEXT_NOTES_RE.match(lines[start])
    if first is None:
        return ""
    first_value = first.group(1).strip()
    collected: list[str] = [first_value] if first_value else []
    for line in lines[start + 1 :]:
        if BLOCK_LINE_RES["stopped"].match(line):
            break
        collected.append(line.rstrip())
    while collected and not collected[-1].strip():
        collected.pop()
    return "\n".join(collected).strip()


def capture_notes(state: dict[str, Any], journal: Path, from_role: str) -> None:
    """Scrape NEXT AGENT NOTES from a journal into the run state.

    The notes are injected into the next agent's prompt; they never carry
    prompt authority, which stays with the orchestrator templates.

    Args:
        state: Mutable orchestrator state mapping.
        journal: Path to the role journal just written.
        from_role: Role that wrote the notes (e.g. 'EXECUTOR').
    """
    if not journal.exists():
        return
    lines = journal.read_text(encoding="utf-8", errors="replace").splitlines()
    notes = parse_next_notes(lines)
    if notes:
        state["handoff_notes"] = {"from": from_role, "notes": notes}


def stdout_handoff_block(stdout: str) -> dict[str, str] | None:
    """Fallback handoff block parsed from the agent's final answer.

    Args:
        stdout: Process standard output string.

    Returns:
        Handoff block mapping if found, otherwise None.
    """
    return parse_handoff_block(stdout.splitlines())


def resolve_handoff(
    journal: Path,
    stdout: str,
    allowed: set[str],
    role_name: str,
    *,
    log_path: Path,
    stopped_expected: str,
    activating_expected: str,
) -> dict[str, str] | None:
    """Validate the journal handoff block; accept a stdout block as fallback.

    Routing decisions follow HANDOFF; STOPPED must identify the role that
    just ran (catches role confusion); ACTIVATING is tracked and only warned
    about on mismatch so a redundant field cannot hard-block the pipeline.

    Args:
        journal: Path to the role journal file.
        stdout: Process standard output string.
        allowed: Set of permissible HANDOFF status strings.
        role_name: Role display name for messages.
        log_path: Path to the invocation log file for diagnostics.
        stopped_expected: Expected STOPPED value (e.g. 'EXECUTOR').
        activating_expected: Expected ACTIVATING value (e.g. 'REVIEWER').

    Returns:
        The validated handoff block if valid, otherwise None.
    """
    block = latest_handoff_block(journal)
    if block and block["stopped"] == stopped_expected and block["handoff"] in allowed:
        _warn_activating_mismatch(block, activating_expected, role_name)
        return block
    alt = stdout_handoff_block(stdout)
    if alt and alt["stopped"] == stopped_expected and alt["handoff"] in allowed:
        print(
            f"[warn] {role_name} did not write a valid handoff block to its "
            "journal; accepted the stdout block. Fix prompt compliance "
            "before real runs."
        )
        _warn_activating_mismatch(alt, activating_expected, role_name)
        return alt
    found = block or alt
    sorted_allowed = sorted(allowed)
    print(
        f"[FAIL] expected STOPPED {stopped_expected} with HANDOFF one of "
        f"{sorted_allowed} from {role_name}; found {found}"
    )
    print_log_tail(log_path)
    return None


def _warn_activating_mismatch(
    block: dict[str, str], activating_expected: str, role_name: str
) -> None:
    """Warn when the agent's ACTIVATING line disagrees with the router plan.

    Args:
        block: Validated handoff block mapping.
        activating_expected: Expected ACTIVATING value.
        role_name: Role display name for messages.
    """
    if block["activating"] != activating_expected:
        print(
            f"[warn] {role_name} wrote ACTIVATING {block['activating']}; "
            f"expected {activating_expected}. Routing follows HANDOFF."
        )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Execute a git command in the repository without raising.

    Args:
        repo: Root path of the git repository.
        *args: Command line arguments to git.

    Returns:
        CompletedProcess instance capturing the result.
    """
    git_exe = shutil.which("git") or "git"
    return subprocess.run(  # noqa: S603
        [git_exe, *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def porcelain_outside_agents(repo: Path) -> list[str]:
    """Return porcelain status lines excluding untracked .agents/ entries.

    Args:
        repo: Root path of the git repository.

    Returns:
        List of porcelain status line strings.
    """
    out = git(repo, "status", "--porcelain").stdout.splitlines()
    return [line for line in out if not line.startswith("?? .agents/")]


def entry_gate(cfg: dict[str, Any]) -> str:
    """Verify idle repository state; return the main baseline commit.

    Args:
        cfg: Consolidated orchestration configuration mapping.

    Returns:
        The 40-character baseline commit hash string.

    Raises:
        OrchestratorError: If the repo is dirty, on the wrong branch, or has
            non-empty journals.
    """
    repo: Path = cfg["repo"]
    if not (repo / ".git").exists():
        msg = f"{repo} is not a git repository"
        raise OrchestratorError(msg)
    branch = git(repo, "branch", "--show-current").stdout.strip()
    if branch != cfg["main_branch"]:
        msg = f"Repository must be on '{cfg['main_branch']}' (currently {branch!r})."
        raise OrchestratorError(msg)
    dirty = porcelain_outside_agents(repo)
    if dirty:
        dirty_list = "\n  ".join(dirty)
        msg = (
            "main must be clean before starting a task "
            f"(untracked .agents/ is ignored):\n  {dirty_list}"
        )
        raise OrchestratorError(msg)
    for journal in cfg["journals"].values():
        if not journal.exists():
            msg = f"Missing journal: {journal}"
            raise OrchestratorError(msg)
        if journal.stat().st_size != 0:
            msg = f"Journal {journal} is not empty; an active task may exist."
            raise OrchestratorError(msg)
    baseline = git(repo, "rev-parse", "HEAD").stdout.strip()
    print(f"[ok] entry gate passed; baseline {baseline[:12]}")
    return baseline


# ---------------------------------------------------------------------------
# Run state
# ---------------------------------------------------------------------------


def save_state(runs_dir: Path, state: dict[str, Any]) -> Path:
    """Serialize the orchestrator run state dictionary to JSON on disk.

    Args:
        runs_dir: Target directory for run state files.
        state: State dictionary to serialize.

    Returns:
        Path to the written JSON file.
    """
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{state['run_id']}.json"
    path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return path


def load_run(runs_dir: Path, run_id: str | None) -> dict[str, Any]:
    """Load a saved run state from disk by ID or most recent file.

    Args:
        runs_dir: Target directory holding saved run state JSON files.
        run_id: Optional run ID to load; if None, loads the latest run.

    Returns:
        State dictionary loaded from disk.

    Raises:
        OrchestratorError: If no run state exists or file is invalid JSON.
    """
    if run_id:
        path = runs_dir / f"{run_id}.json"
        if not path.exists():
            msg = f"No saved run {run_id!r} in {runs_dir}"
            raise OrchestratorError(msg)
        raw_data: Any = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw_data, dict):
            msg = f"Saved run state in {path} is not a valid object"
            raise OrchestratorError(msg)
        data: dict[str, Any] = cast("dict[str, Any]", raw_data)
        return data

    runs = sorted(p for p in runs_dir.glob("*.json") if p.is_file())
    if not runs:
        msg = f"No saved runs in {runs_dir}"
        raise OrchestratorError(msg)
    raw_data = json.loads(runs[-1].read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        msg = f"Saved run state in {runs[-1]} is not a valid object"
        raise OrchestratorError(msg)
    data = cast("dict[str, Any]", raw_data)
    return data


def record(
    state: dict[str, Any],
    phase: str,
    block: dict[str, str] | None,
    log_path: Path,
) -> None:
    """Append a step execution entry to the run state history.

    Args:
        state: Mutable orchestrator state mapping.
        phase: Current workflow phase name.
        block: Resolved handoff block (stopped/activating/handoff), if any.
        log_path: Path to the log file for this invocation.
    """
    now_utc = _dt.datetime.now(tz=_dt.UTC)
    state["history"].append(
        {
            "time": now_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "phase": phase,
            "iteration": state["iteration"],
            "stopped": (block or {}).get("stopped"),
            "activating": (block or {}).get("activating"),
            "handoff": (block or {}).get("handoff"),
            "log": str(log_path),
        }
    )


# ---------------------------------------------------------------------------
# Prompt fields
# ---------------------------------------------------------------------------


def build_fields(
    task: dict[str, Any], state: dict[str, Any], cfg: dict[str, Any]
) -> dict[str, Any]:
    """Construct the replacement fields dictionary for template rendering.

    Args:
        task: Task definition dictionary.
        state: Active run state mapping.
        cfg: Consolidated orchestration configuration mapping.

    Returns:
        Mapping of placeholder keys to string values.
    """
    branch_val = state.get("branch") or "(created by the Planner)"
    base_val = state.get("baseline") or "(recorded by the Planner)"
    notes_val = cast("dict[str, Any]", state.get("handoff_notes") or {})
    notes_txt = (
        f"From {notes_val.get('from', 'UNKNOWN')}: {notes_val.get('notes', '')}"
        if notes_val.get("notes")
        else "None"
    )
    return {
        "repo_path": str(cfg["repo"]),
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
        "branch": branch_val,
        "baseline_commit": base_val,
        "blocker_ledger": blocker_ledger_text(state),
        "handoff_notes": notes_txt,
        "correction_context": correction_text(state),
    }


def correction_text(state: dict[str, Any]) -> str:
    """Generate correction/blocker context instructions for iteration > 1.

    A blocker raised by the previous iteration turns the current dry run into
    a minimal blocker-resolution plan; the original task scope is explicitly
    suspended and resumes in the following dry run.

    Args:
        state: Active run state mapping.

    Returns:
        Formatted context text, or empty string for iteration 1.
    """
    iteration = state["iteration"]
    if iteration <= 1:
        return ""
    blockers: list[dict[str, Any]] = state.get("blockers", [])
    pending = [
        b
        for b in blockers
        if b.get("status") == "OPEN" and b.get("iteration") == iteration - 1
    ]
    parts: list[str] = []
    if pending:
        pending_txt = "; ".join(
            f"{b['raised_by']} at iteration {b['iteration']}"
            + (f": {b['description']}" if b.get("description") else "")
            for b in pending
        )
        parts.append(
            f"This is a BLOCKER-RESOLUTION dry run (Dry Run {iteration}). The "
            f"previous iteration was blocked — {pending_txt}. Plan ONLY the "
            "minimal scope needed to resolve the blocker(s). The ORIGINAL task "
            "scope is suspended and continues in the next dry run after this "
            "resolution is implemented; do not expand into it here."
        )
    else:
        parts.append(
            f"This is correction iteration {iteration} of the ORIGINAL task. "
            f"The previous iteration ended with: "
            f"{state.get('last_event', 'unknown')}."
        )
        last_event = state.get("last_event", "")
        if last_event.startswith("Reviewer"):
            parts.append(
                "Address every required correction recorded in "
                "`docs/dev/task/reviewer.md` for the latest review before "
                "re-planning."
            )
        elif last_event.startswith("owner rejected"):
            parts.append(
                "Incorporate the owner direction below into the revised dry run."
            )
    resolved = [b for b in blockers if b.get("status") == "RESOLVED"]
    if resolved:
        ledger = "; ".join(
            f"{b['raised_by']} blocker from iteration {b['iteration']} "
            f"resolved by Dry Run {b.get('resolved_by')}"
            for b in resolved
        )
        parts.append(f"Blocker ledger (already resolved): {ledger}.")
    parts.append(
        "Read the complete journal history in docs/dev/task/, explicitly "
        "inventory every retained changed and untracked path, state whether "
        "each is retained, changed, or rolled back, and append the complete "
        f"`Dry Run {iteration}` per AGENTS.md."
    )
    feedback = state.get("owner_feedback", "").strip()
    if feedback:
        parts.append(f"Owner direction for this dry run: {feedback}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Owner approval gate
# ---------------------------------------------------------------------------


def _collect_rejection_feedback() -> str:
    """Prompt the owner interactively for dry run correction feedback.

    Returns:
        Multiline feedback string entered by the user.
    """
    print("Enter planning feedback (finish with a line containing only '.'):")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def request_approval(auto_approve: bool) -> tuple[bool, str]:
    """Prompt the owner to approve, reject, or abort a planned dry run.

    Args:
        auto_approve: If True, bypass the owner gate automatically.

    Returns:
        Tuple of (approved_bool, owner_feedback_for_next_dry_run).

    Raises:
        KeyboardInterrupt: If the user chooses to abort execution.
    """
    if auto_approve:
        print("[warn] --auto-approve: bypassing the owner approval gate.")
        return True, ""
    print("\nOwner approval required. Options:")
    print("  APPROVED: EXECUTE   authorize this dry run")
    print("  reject              send back to the Planner with feedback")
    abort_msg = "  abort               stop the orchestrator (state saved, resumable)\n"
    print(abort_msg)
    while True:
        try:
            answer = input("Approve Dry Run? > ").strip()
        except EOFError:
            answer = "abort"
        if answer == "APPROVED: EXECUTE":
            return True, ""
        lowered = answer.lower()
        if lowered in ("reject", "r"):
            feedback = _collect_rejection_feedback()
            return False, feedback
        if lowered in ("abort", "a"):
            raise KeyboardInterrupt
        print("Unrecognized input; type APPROVED: EXECUTE, reject, or abort.")


def _record_blocker(state: dict[str, Any], raised_by: str, *, auto: bool) -> None:
    """Record an OPEN blocker in the run state and update ``last_event``.

    Args:
        state: Mutable orchestrator state mapping.
        raised_by: Role that raised the blocker ('PLANNER' or 'EXECUTOR').
        auto: When True, skip the interactive one-line description prompt.
    """
    description = ""
    if not auto:
        try:
            description = input(
                "Describe the blocker in one line (Enter to skip): "
            ).strip()
        except EOFError:
            description = ""
    now_utc = _dt.datetime.now(tz=_dt.UTC)
    state.setdefault("blockers", []).append(
        {
            "iteration": state["iteration"],
            "raised_by": raised_by,
            "description": description,
            "status": "OPEN",
            "time": now_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        }
    )
    detail = f": {description}" if description else ""
    state["last_event"] = (
        f"{raised_by.title()} iteration {state['iteration']} BLOCKED{detail}"
    )


def blocker_ledger_text(state: dict[str, Any]) -> str:
    """Format the blocker ledger for prompt templates.

    Args:
        state: Active run state mapping.

    Returns:
        Human-readable ledger string, or 'None' when no blockers exist.
    """
    blockers: list[dict[str, Any]] = state.get("blockers", [])
    if not blockers:
        return "None"
    entries: list[str] = []
    for b in blockers:
        entry = f"{b['raised_by']} iteration {b['iteration']} ({b['status']}"
        if b.get("resolved_by"):
            entry += f", resolved by Dry Run {b['resolved_by']}"
        if b.get("description"):
            entry += f": {b['description']}"
        entries.append(entry + ")")
    return "; ".join(entries)


# ---------------------------------------------------------------------------
# State-machine router
# ---------------------------------------------------------------------------


def banner(title: str) -> None:
    """Print a prominent section header banner to standard output.

    Args:
        title: Banner title text.
    """
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def _handle_plan_phase(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    self_test: bool,
) -> bool:
    """Execute the Planner dry-run phase.

    Args:
        cfg: Consolidated orchestration configuration mapping.
        state: Mutable orchestrator state mapping.
        self_test: Whether running in self-test sandbox mode.

    Returns:
        True if the router loop should continue, False to stop.

    Raises:
        OrchestratorError: If planning fails or branch is unexpected.
    """
    it = state["iteration"]
    banner(f"PLANNER — Dry Run {it}")
    fields = build_fields(state["task"], state, cfg)
    prompt = compose_prompt(cfg["templates"]["planner"], fields)
    tag = f"{state['run_id']}-planner-dry-run-{it}"
    _, out, log = run_agent(
        cfg["roles"]["planner"],
        prompt,
        cfg["repo"],
        cfg["logs_dir"],
        tag,
        timeout=cfg["timeout"],
    )
    block = resolve_handoff(
        cfg["journals"]["planner"],
        out,
        {"PENDING_APPROVAL", "BLOCKED"},
        "Planner",
        log_path=log,
        stopped_expected="PLANNER",
        activating_expected="PLANNER",
    )
    record(state, "plan", block, log)
    marker = block["handoff"] if block else None
    if marker is None:
        state["status"] = "FAILED"
        save_state(cfg["runs_dir"], state)
        msg = "Planner produced no valid handoff block; stopping (fail closed)."
        raise OrchestratorError(msg)
    capture_notes(state, cfg["journals"]["planner"], "PLANNER")
    if marker == "BLOCKED":
        _record_blocker(state, "PLANNER", auto=self_test)
        state["status"] = "PLANNER_BLOCKED"
        state["phase"] = "done"
        save_state(cfg["runs_dir"], state)
        banner("Planner BLOCKED — owner decision required")
        print("See docs/dev/task/planner.md for evidence and required action.")
        print("Fix the cause, then: python .agents/orchestrator.py resume")
        return True

    if not self_test:
        branch = git(cfg["repo"], "branch", "--show-current").stdout.strip()
        if branch in ("", cfg["main_branch"]):
            state["status"] = "FAILED"
            save_state(cfg["runs_dir"], state)
            msg = (
                "Planner reported PENDING_APPROVAL but repository is still on "
                f"{branch!r}; expected the new task branch."
            )
            raise OrchestratorError(msg)
        state["branch"] = branch
    elif not state.get("branch"):
        state["branch"] = "feature/feat-demo-demo-task"

    state["phase"] = "approve"
    save_state(cfg["runs_dir"], state)
    return True


def _handle_approve_phase(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    auto_approve: bool,
) -> None:
    """Execute the Owner approval phase.

    Args:
        cfg: Consolidated orchestration configuration mapping.
        state: Mutable orchestrator state mapping.
        auto_approve: Whether to auto-approve without interactive prompt.
    """
    it = state["iteration"]
    banner(f"OWNER GATE — approve Dry Run {it}")
    approved, feedback = request_approval(auto_approve)
    if approved:
        state["phase"] = "approval_record"
    else:
        state["last_event"] = f"owner rejected Dry Run {it}"
        state["owner_feedback"] = feedback
        state["iteration"] = it + 1
        state["phase"] = "plan"
    save_state(cfg["runs_dir"], state)


def _handle_approval_record_phase(
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    """Execute the Planner approval recording phase.

    Args:
        cfg: Consolidated orchestration configuration mapping.
        state: Mutable orchestrator state mapping.

    Raises:
        OrchestratorError: If recording approval fails.
    """
    it = state["iteration"]
    banner(f"PLANNER — record approval for Dry Run {it}")
    fields = build_fields(state["task"], state, cfg)
    approval_fields = {
        "repo_path": fields["repo_path"],
        "branch": state["branch"],
        "task_id": fields["task_id"],
        "iteration": it,
        "baseline_commit": state.get("baseline") or fields["baseline_commit"],
        "handoff_notes": fields["handoff_notes"],
    }
    prompt = compose_prompt(cfg["templates"]["planner_approval"], approval_fields)
    tag = f"{state['run_id']}-planner-approval-{it}"
    _, out, log = run_agent(
        cfg["roles"]["planner"],
        prompt,
        cfg["repo"],
        cfg["logs_dir"],
        tag,
        timeout=cfg["timeout"],
        approval=True,
    )
    block = resolve_handoff(
        cfg["journals"]["planner"],
        out,
        {"APPROVED_EXECUTE", "BLOCKED"},
        "Planner (approval)",
        log_path=log,
        stopped_expected="PLANNER",
        activating_expected="EXECUTOR",
    )
    record(state, "approval_record", block, log)
    marker = block["handoff"] if block else None
    if marker != "APPROVED_EXECUTE":
        state["status"] = "FAILED"
        save_state(cfg["runs_dir"], state)
        msg = "Planner failed to record the approval; stopping (fail closed)."
        raise OrchestratorError(msg)
    capture_notes(state, cfg["journals"]["planner"], "PLANNER")
    state["phase"] = "executor"
    save_state(cfg["runs_dir"], state)


def _handle_executor_phase(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    self_test: bool,
) -> None:
    """Execute the Executor implementation phase.

    Args:
        cfg: Consolidated orchestration configuration mapping.
        state: Mutable orchestrator state mapping.
        self_test: Whether running in self-test sandbox mode.

    Raises:
        OrchestratorError: If execution yields no valid marker.
    """
    it = state["iteration"]
    banner(f"EXECUTOR — implement Dry Run {it}")
    fields = build_fields(state["task"], state, cfg)
    prompt = compose_prompt(cfg["templates"]["executor"], fields)
    tag = f"{state['run_id']}-executor-{it}"
    _, out, log = run_agent(
        cfg["roles"]["executor"],
        prompt,
        cfg["repo"],
        cfg["logs_dir"],
        tag,
        timeout=cfg["timeout"],
    )
    block = resolve_handoff(
        cfg["journals"]["executor"],
        out,
        {"READY_FOR_REVIEW", "BLOCKED"},
        "Executor",
        log_path=log,
        stopped_expected="EXECUTOR",
        activating_expected="REVIEWER",
    )
    record(state, "executor", block, log)
    marker = block["handoff"] if block else None
    if marker is None:
        state["status"] = "FAILED"
        save_state(cfg["runs_dir"], state)
        msg = "Executor produced no valid handoff block; stopping (fail closed)."
        raise OrchestratorError(msg)
    capture_notes(state, cfg["journals"]["executor"], "EXECUTOR")
    if marker == "BLOCKED":
        _record_blocker(state, "EXECUTOR", auto=self_test)
        state["owner_feedback"] = ""
        state["iteration"] = it + 1
        state["phase"] = "plan"
    else:
        for blocker in state.get("blockers", []):
            if blocker["status"] == "OPEN":
                blocker["status"] = "RESOLVED"
                blocker["resolved_by"] = it
        state["phase"] = "reviewer"
    save_state(cfg["runs_dir"], state)


def _handle_reviewer_phase(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    self_test: bool,
) -> bool:
    """Execute the Reviewer evaluation phase.

    Args:
        cfg: Consolidated orchestration configuration mapping.
        state: Mutable orchestrator state mapping.
        self_test: Whether running in self-test sandbox mode.

    Returns:
        True if routing should continue, False if ACCEPTED or terminal.

    Raises:
        OrchestratorError: If review yields no valid marker.
    """
    it = state["iteration"]
    banner(f"REVIEWER — review Dry Run {it} / Report {it}")
    fields = build_fields(state["task"], state, cfg)
    prompt = compose_prompt(cfg["templates"]["reviewer"], fields)
    tag = f"{state['run_id']}-reviewer-{it}"
    _, out, log = run_agent(
        cfg["roles"]["reviewer"],
        prompt,
        cfg["repo"],
        cfg["logs_dir"],
        tag,
        timeout=cfg["timeout"],
    )
    block = resolve_handoff(
        cfg["journals"]["reviewer"],
        out,
        {"ACCEPTED", "CHANGES_REQUESTED"},
        "Reviewer",
        log_path=log,
        stopped_expected="REVIEWER",
        activating_expected="NONE",
    )
    record(state, "reviewer", block, log)
    marker = block["handoff"] if block else None
    if marker is None:
        state["status"] = "FAILED"
        save_state(cfg["runs_dir"], state)
        msg = "Reviewer produced no valid handoff block; stopping (fail closed)."
        raise OrchestratorError(msg)
    capture_notes(state, cfg["journals"]["reviewer"], "REVIEWER")
    if marker == "CHANGES_REQUESTED":
        state["last_event"] = f"Reviewer Review {it} CHANGES_REQUESTED"
        state["owner_feedback"] = ""
        state["iteration"] = it + 1
        state["phase"] = "plan"
        save_state(cfg["runs_dir"], state)
        return True

    state["status"] = "ACCEPTED"
    state["handoff_notes"] = None
    state["phase"] = "done"
    save_state(cfg["runs_dir"], state)
    banner("REVIEWER ACCEPTED — verifying close-out")
    _verify_close_out(cfg, self_test=self_test)
    return False


def _verify_close_out(cfg: dict[str, Any], *, self_test: bool) -> None:
    """Verify git and journal state after Reviewer acceptance.

    Args:
        cfg: Consolidated orchestration configuration mapping.
        self_test: Whether running in self-test sandbox mode.
    """
    if self_test:
        print("    (self-test mode: git close-out checks skipped)")
        return
    repo = cfg["repo"]
    journals = cfg["journals"]
    branch = git(repo, "branch", "--show-current").stdout.strip()
    dirty = porcelain_outside_agents(repo)
    empty_journals = all(journals[name].stat().st_size == 0 for name in journals)
    print(f"    branch: {branch} (expected {cfg['main_branch']})")
    print(f"    main dirty entries outside .agents/: {len(dirty)}")
    print(f"    journals emptied: {empty_journals}")
    if branch == cfg["main_branch"] and not dirty and empty_journals:
        last = git(repo, "log", "-1", "--format=%h %s").stdout.strip()
        print(f"[ok] close-out verified; main HEAD: {last}")
    else:
        print("[warn] close-out state unexpected; inspect manually.")


def router(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    auto_approve: bool = False,
    self_test: bool = False,
) -> dict[str, Any]:
    """Run phases until ACCEPTED, a stop condition, or owner interruption.

    Args:
        cfg: Consolidated orchestration configuration mapping.
        state: Mutable orchestrator state mapping.
        auto_approve: If True, bypass the owner gate.
        self_test: If True, operate in self-test stub mode.

    Returns:
        Final state dictionary upon completion or stop condition.

    Raises:
        OrchestratorError: If an unrecognized phase or fatal condition occurs.
    """
    while True:
        if state["iteration"] > cfg["max_iterations"]:
            state["status"] = "MAX_ITERATIONS"
            save_state(cfg["runs_dir"], state)
            banner(f"Stopped: exceeded max iterations ({cfg['max_iterations']})")
            return state

        phase = state["phase"]
        if phase == "plan":
            _handle_plan_phase(cfg, state, self_test=self_test)
        elif phase == "approve":
            _handle_approve_phase(cfg, state, auto_approve=auto_approve)
        elif phase == "approval_record":
            _handle_approval_record_phase(cfg, state)
        elif phase == "executor":
            _handle_executor_phase(cfg, state, self_test=self_test)
        elif phase == "reviewer":
            should_continue = _handle_reviewer_phase(cfg, state, self_test=self_test)
            if not should_continue:
                return state
        elif phase == "done":
            return state
        else:
            msg = f"Unknown phase {phase!r} in saved state."
            raise OrchestratorError(msg)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


TASK_REQUIRED = ("task_id", "task_slug", "task_request")


def collect_task(args: argparse.Namespace) -> dict[str, str]:
    """Extract and validate task definition fields from CLI arguments or TOML.

    Args:
        args: Parsed command line arguments namespace.

    Returns:
        Dictionary of validated task fields.

    Raises:
        OrchestratorError: If required fields are missing or slug is invalid.
    """
    if args.task_file:
        task: dict[str, str] = load_toml(Path(args.task_file).resolve())
    else:
        task = {
            key: str(getattr(args, key))
            for key in (
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
            if getattr(args, key, None) is not None
        }
    missing = [key for key in TASK_REQUIRED if not task.get(key)]
    if missing:
        msg = f"Task fields missing: {missing}"
        raise OrchestratorError(msg)
    if not SLUG_RE.match(task["task_slug"]):
        msg = (
            f"task_slug {task['task_slug']!r} must be lowercase "
            "filesystem-safe (letters, digits, '.', '_', '-')."
        )
        raise OrchestratorError(msg)
    return task


def cmd_start(args: argparse.Namespace) -> int:
    """Execute the 'start' subcommand to begin a new task workflow.

    Args:
        args: Parsed command line arguments namespace.

    Returns:
        Exit code: 0 on success, 130 on interrupt, 1 on failure.
    """
    cfg = assemble_config(args.repo)
    if args.max_iterations:
        cfg["max_iterations"] = args.max_iterations
    task = collect_task(args)
    baseline = entry_gate(cfg)

    now_utc = _dt.datetime.now(tz=_dt.UTC)
    stamp = now_utc.strftime("%Y%m%d-%H%M%S")
    state: dict[str, Any] = {
        "run_id": f"{stamp}-{task['task_slug']}",
        "task": task,
        "iteration": 1,
        "phase": "plan",
        "status": "RUNNING",
        "baseline": baseline,
        "branch": None,
        "last_event": "",
        "owner_feedback": "",
        "blockers": [],
        "handoff_notes": None,
        "history": [],
    }
    path = save_state(cfg["runs_dir"], state)
    print(f"[ok] run {state['run_id']} started; state: {path}")
    try:
        router(cfg, state, auto_approve=args.auto_approve)
    except KeyboardInterrupt:
        state["status"] = "INTERRUPTED"
        save_state(cfg["runs_dir"], state)
        print("\n[interrupted] Run state saved; resume with:")
        print(f"  python .agents/orchestrator.py resume --run-id {state['run_id']}")
        return 130
    return 0 if state.get("status") == "ACCEPTED" else 1


def cmd_resume(args: argparse.Namespace) -> int:
    """Execute the 'resume' subcommand to continue an interrupted task.

    Args:
        args: Parsed command line arguments namespace.

    Returns:
        Exit code: 0 on success, 130 on interrupt, 1 on failure.
    """
    cfg = assemble_config(args.repo)
    if args.max_iterations:
        cfg["max_iterations"] = args.max_iterations
    run_id_val = getattr(args, "run_id", None)
    run_id: str | None = str(run_id_val) if run_id_val is not None else None
    state: dict[str, Any] = load_run(cfg["runs_dir"], run_id)
    print(
        f"[ok] resuming run {state['run_id']} at phase {state['phase']!r}, "
        f"iteration {state['iteration']}, status {state['status']}"
    )
    if state["phase"] == "done" and state.get("status") == "PLANNER_BLOCKED":
        state["iteration"] = int(state["iteration"]) + 1
        state["status"] = "RUNNING"
        state["phase"] = "plan"
        print(
            "[ok] planner blocker on record; resuming with a blocker dry run "
            f"at iteration {state['iteration']}."
        )
    elif state["phase"] == "done":
        print("Run already finished; nothing to do.")
        return 0
    state["status"] = "RUNNING"
    try:
        router(cfg, state, auto_approve=args.auto_approve)
    except KeyboardInterrupt:
        state["status"] = "INTERRUPTED"
        save_state(cfg["runs_dir"], state)
        print("\n[interrupted] Run state saved; resume again with:")
        print(f"  python .agents/orchestrator.py resume --run-id {state['run_id']}")
        return 130
    return 0 if state.get("status") == "ACCEPTED" else 1


def _doctor_check_roles(cfg: dict[str, Any]) -> bool:
    """Validate configured roles, CLIs, and templates for doctor subcommand.

    Args:
        cfg: Consolidated orchestration configuration mapping.

    Returns:
        True if all role validations pass, False otherwise.
    """
    ok = True
    for role in ("planner", "executor", "reviewer"):
        configured = role in cfg["roles"]
        print(f"[{'ok' if configured else 'FAIL'}] role configured: {role}")
        if not configured:
            ok = False

    roles_dict: dict[str, dict[str, Any]] = cfg["roles"]
    for role, role_cfg in roles_dict.items():
        for cmd_key in ("command", "approval_command"):
            command_val: Any = role_cfg.get(cmd_key)
            if not command_val or not isinstance(command_val, (list, tuple)):
                continue
            cmd_token: str = cast("str", command_val[0])
            exe: str | None = shutil.which(cmd_token)
            available: bool = exe is not None
            print(
                f"[{'ok' if available else 'FAIL'}] "
                f"{role}.{cmd_key} CLI '{cmd_token}' on PATH"
            )
            if not available:
                ok = False
        template: Path | None = role_cfg.get("template_path")
        if template:
            exists = template.exists()
            print(f"[{'ok' if exists else 'FAIL'}] {role} template: {template}")
            if not exists:
                ok = False
    return ok


def _doctor_check_repo(cfg: dict[str, Any]) -> bool:
    """Validate git repository and journal state for doctor subcommand.

    Args:
        cfg: Consolidated orchestration configuration mapping.

    Returns:
        True if repository checks pass, False otherwise.
    """
    git_found = shutil.which("git") is not None
    print(f"[{'ok' if git_found else 'FAIL'}] git on PATH")
    if not git_found:
        return False

    repo: Path = cfg["repo"]
    if not (repo / ".git").exists():
        print(f"[FAIL] repo not a git repository: {repo}")
        return False

    branch = git(repo, "branch", "--show-current").stdout.strip()
    dirty = porcelain_outside_agents(repo)
    dirty_count = len(dirty)
    print(f"[info] repo branch: {branch}; dirty outside .agents/: {dirty_count}")
    journals_dict: dict[str, Path] = cfg["journals"]
    for name, journal in journals_dict.items():
        size = journal.stat().st_size if journal.exists() else -1
        print(f"[info] journal {name}: {size} bytes ({journal})")
    return True


def cmd_doctor(args: argparse.Namespace) -> int:
    """Execute the 'doctor' subcommand to validate configurations and tools.

    Args:
        args: Parsed command line arguments namespace.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    py_ver = sys.version.split()[0]
    print(f"[ok] python {py_ver} at {sys.executable}")
    try:
        cfg = assemble_config(args.repo)
    except (OrchestratorError, tomllib.TOMLDecodeError, OSError) as exc:
        print(f"[FAIL] config load: {exc}")
        return 1
    print(f"[ok] config loaded; repo: {cfg['repo']}")

    ok = True
    templates_dict: dict[str, Path] = cfg["templates"]
    for name, path in templates_dict.items():
        exists = path.exists()
        print(f"[{'ok' if exists else 'FAIL'}] template {name}: {path}")
        if not exists:
            ok = False

    if not _doctor_check_roles(cfg):
        ok = False
    if not _doctor_check_repo(cfg):
        ok = False
    return 0 if ok else 1


def cmd_self_test(_args: argparse.Namespace) -> int:
    """Drive the real router/templates against stub agents in a temp dir.

    Args:
        _args: Parsed command line arguments namespace (unused).

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    agents_dir = AGENTS_DIR
    cfg = assemble_config()
    tmp = Path(tempfile.mkdtemp(prefix="hq-orch-self_test-"))
    journals = {
        "planner": tmp / "docs/dev/task/planner.md",
        "executor": tmp / "docs/dev/task/executor.md",
        "reviewer": tmp / "docs/dev/task/reviewer.md",
    }
    for journal in journals.values():
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.write_bytes(b"")

    stub = agents_dir / "tests" / "stub_agent.py"

    def stub_role(role: str, extra: list[str] | None = None) -> dict[str, Any]:
        command = [
            sys.executable,
            str(stub),
            "--role",
            role,
            "--journal",
            str(journals[role]),
        ] + (extra or [])
        return {"command": command, "prompt_delivery": "file"}

    approval_cmd = stub_role("planner", ["--mode", "approval"])["command"]
    test_cfg: dict[str, Any] = {
        "repo": tmp,
        "main_branch": "main",
        "max_iterations": 3,
        "timeout": 120,
        "journals": journals,
        "templates": cfg["templates"],
        "logs_dir": tmp / "logs",
        "runs_dir": tmp / "runs",
        "roles": {
            "planner": {
                **stub_role("planner"),
                "approval_command": approval_cmd,
            },
            "executor": stub_role("executor"),
            "reviewer": stub_role("reviewer"),
        },
    }
    state: dict[str, Any] = {
        "run_id": "self_test-demo",
        "task": {
            "task_kind": "feature",
            "task_id": "FEAT-DEMO",
            "task_slug": "demo-task",
            "task_name": "Demo Task",
            "task_request": "Self-test task.",
            "additional_context": "None",
            "exclusions": "None",
            "owner_execution_notes": "None",
            "review_focus": "None",
        },
        "iteration": 1,
        "phase": "plan",
        "status": "RUNNING",
        "baseline": "0" * 40,
        "branch": None,
        "last_event": "",
        "owner_feedback": "",
        "blockers": [],
        "handoff_notes": None,
        "history": [],
    }

    print(f"[self-test] sandbox: {tmp}")
    try:
        result = router(test_cfg, state, auto_approve=True, self_test=True)
    finally:
        pass

    planner_text = journals["planner"].read_text(encoding="utf-8")
    executor_text = journals["executor"].read_text(encoding="utf-8")
    log_files = list((tmp / "logs").glob("*"))
    reviewer_block = latest_handoff_block(journals["reviewer"])
    rev_ok = reviewer_block is not None and reviewer_block["handoff"] == "ACCEPTED"
    rev_activating_ok = (
        reviewer_block is not None and reviewer_block["activating"] == "NONE"
    )
    logs_path = tmp / "logs"

    def _prompt_has(path: Path | None, needle: str) -> bool:
        return path is not None and needle in path.read_text(encoding="utf-8")

    exec1_prompt = next(iter(logs_path.glob("*executor-1-prompt.md")), None)
    rev2_prompt = next(iter(logs_path.glob("*reviewer-2-prompt.md")), None)
    plan2_prompt = next(iter(logs_path.glob("*planner-dry-run-2-prompt.md")), None)
    dry_runs_ok = all(f"Dry Run {n}" in planner_text for n in (1, 2, 3))
    reports_ok = all(f"Report {n}" in executor_text for n in (1, 2, 3))
    blockers: list[dict[str, Any]] = result.get("blockers", [])
    expected_resolved_iteration = 2
    blocker_ok = (
        len(blockers) == 1
        and blockers[0].get("raised_by") == "EXECUTOR"
        and blockers[0].get("status") == "RESOLVED"
        and blockers[0].get("resolved_by") == expected_resolved_iteration
    )
    assertions: list[tuple[str, bool]] = [
        ("final status ACCEPTED", result.get("status") == "ACCEPTED"),
        (
            "iterations advanced to 3 (blocker + changes-requested loops)",
            result.get("iteration") == EXPECTED_SELF_TEST_ITERATION,
        ),
        ("planner journal has Dry Runs 1-3", dry_runs_ok),
        (
            "planner journal has APPROVED: EXECUTE record",
            "APPROVED: EXECUTE" in planner_text,
        ),
        (
            "planner journal has APPROVED_EXECUTE handoff block",
            "HANDOFF : APPROVED_EXECUTE" in planner_text,
        ),
        (
            "planner journal routes approval to EXECUTOR",
            "ACTIVATING : EXECUTOR" in planner_text,
        ),
        ("executor journal has Reports 1-3", reports_ok),
        (
            "blocker recorded (EXECUTOR it1) and resolved by Dry Run 2",
            blocker_ok,
        ),
        ("reviewer journal ends ACCEPTED", rev_ok),
        ("reviewer journal activates NONE on acceptance", rev_activating_ok),
        (
            "planner notes reached the executor prompt",
            _prompt_has(exec1_prompt, "From PLANNER:"),
        ),
        (
            "executor notes reached the reviewer prompt",
            _prompt_has(rev2_prompt, "From EXECUTOR:"),
        ),
        (
            "blocked-executor notes reached the planner prompt",
            _prompt_has(plan2_prompt, "From EXECUTOR:"),
        ),
        (
            "handoff notes cleared on acceptance",
            not result.get("handoff_notes"),
        ),
        (
            "prompt+log files written per invocation",
            len(log_files) >= MIN_SELF_TEST_LOG_FILES,
        ),
    ]
    failed: list[str] = [name for name, passed in assertions if not passed]
    for name, passed in assertions:
        print(f"[{'ok' if passed else 'FAIL'}] {name}")
    shutil.rmtree(tmp, ignore_errors=True)
    if failed or result.get("status") != "ACCEPTED":
        print(f"SELF-TEST FAILED: {failed}")
        return 1
    print("SELF-TEST PASSED")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Register common CLI flags across subcommands.

    Args:
        parser: Subcommand parser instance.
    """
    parser.add_argument("--repo", help="override repository path")
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="DANGEROUS: skip the owner APPROVED: EXECUTE gate",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        help="override max iterations from orchestrator.toml",
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct the command line arguments parser for the orchestrator.

    Returns:
        Configured ArgumentParser instance.
    """
    doc_summary = __doc__.splitlines()[0] if __doc__ else "Agent orchestrator"
    parser = argparse.ArgumentParser(description=doc_summary)
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="run a new task through the state machine")
    p_start.add_argument(
        "--task-file",
        help="TOML file with task fields (see task.example.toml)",
    )
    p_start.add_argument("--task-kind", default=None)
    p_start.add_argument("--task-id", default=None)
    p_start.add_argument("--task-slug", default=None)
    p_start.add_argument("--task-name", default=None)
    p_start.add_argument("--task-request", default=None)
    p_start.add_argument(
        "--additional-context", dest="additional_context", default=None
    )
    p_start.add_argument("--exclusions", default=None)
    p_start.add_argument(
        "--owner-execution-notes", dest="owner_execution_notes", default=None
    )
    p_start.add_argument("--review-focus", dest="review_focus", default=None)
    p_start.add_argument(
        "--implementation-file",
        dest="implementation_file",
        default=None,
        help="implementation tracker file whose entry this task completes",
    )
    p_start.add_argument(
        "--implementation-entry",
        dest="implementation_entry",
        default=None,
        help="tracker entry id (e.g. '1.1' or 'T.1')",
    )
    _add_common_args(p_start)
    p_start.set_defaults(func=cmd_start)

    p_resume = sub.add_parser("resume", help="continue a saved run")
    p_resume.add_argument("--run-id", default=None, help="run id (default: latest)")
    _add_common_args(p_resume)
    p_resume.set_defaults(func=cmd_resume)

    p_doctor = sub.add_parser("doctor", help="validate configuration and environment")
    p_doctor.add_argument("--repo", help="override repository path")
    p_doctor.set_defaults(func=cmd_doctor, auto_approve=False, max_iterations=0)

    p_test = sub.add_parser("self-test", help="run stub-agent end-to-end test")
    p_test.set_defaults(
        func=cmd_self_test, repo=None, auto_approve=False, max_iterations=0
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the orchestrator script.

    Args:
        argv: Optional list of command line argument strings.

    Returns:
        Process exit code integer.
    """
    args = build_parser().parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        # Agent output may contain characters outside the console codepage.
        stream_obj = cast("Any", stream)
        with contextlib.suppress(OSError, ValueError):
            if hasattr(stream_obj, "reconfigure"):
                stream_obj.reconfigure(errors="replace")
    try:
        return int(args.func(args))
    except OrchestratorError as exc:
        print(f"\n[FAIL] {exc}")
        print("Run state is saved under .agents/runs; fix the cause and 'resume'.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
