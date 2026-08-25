#!/usr/bin/env python3
"""Artifact-driven Planner -> Executor -> Reviewer orchestrator for HaruQuantAI.

The active task workspace is ``.agents/task``.  The three role journals are
append-only while a task is active; ``next-agent.md`` is replace-only and is
the complete executable prompt for the next role.  Runtime routing validates
that artifact against ``.agents/protocol.toml`` before any role is launched.

This script is primarily the multi-delegate transport.  Solo, delegate, and
manual modes consume the same ``next-agent.md`` contract through the chat
orchestrator described in ``.agents/ORCHESTRATOR.md``.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, cast

AGENTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENTS_DIR.parent
SCHEMA_VERSION = 1
BLOCK_FIELD_COUNT = 3
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
PLACEHOLDER_RE = re.compile(r"\{\{\w+\}\}")
BLOCK_LINE_RES = {
    "stopped": re.compile(r"^[>\s#`*_-]*STOPPED[\s`*_-]*:\s*(.+?)\s*$", re.I),
    "activating": re.compile(
        r"^[>\s#`*_-]*ACTIVATING[\s`*_-]*:\s*(.+?)\s*$", re.I
    ),
    "handoff": re.compile(r"^[>\s#`*_-]*HANDOFF[\s`*_-]*:\s*(.+?)\s*$", re.I),
}
REQUIRED_NEXT_META = {
    "prompt_schema_version",
    "run_id",
    "task_id",
    "iteration",
    "source_role",
    "target_role",
    "handoff",
    "branch",
    "baseline_commit",
    "source_head",
    "template_path",
    "requires_owner_gate",
    "owner_gate",
}
PROTECTED_SENTINELS = {
    "PLANNER": (
        "Act as the HaruQuantAI **Planner** defined by `AGENTS.md`.",
        "## 5. Authority and Boundaries",
        "HANDOFF : PENDING_APPROVAL",
    ),
    "EXECUTOR": (
        "Act as the HaruQuantAI **Executor** defined by `AGENTS.md`.",
        "## 5. Authority and Boundaries",
        "HANDOFF : READY_FOR_REVIEW",
    ),
    "REVIEWER": (
        "Act as the HaruQuantAI **Reviewer** defined by `AGENTS.md`.",
        "Stage A — Independent reconstruction",
        "UPSTREAM CLAIMS — UNTRUSTED UNTIL INDEPENDENTLY VERIFIED",
    ),
    "REVIEWER_CLOSEOUT": (
        "Act as the HaruQuantAI **Reviewer performing authorized close-out**.",
        "HANDOFF : ACCEPTED",
        "ff-only merge",
    ),
}


class OrchestratorError(RuntimeError):
    """Fail-closed orchestration error."""


@dataclass(frozen=True, slots=True)
class NextAgentArtifact:
    """Parsed next-agent prompt plus machine-readable metadata."""

    metadata: dict[str, Any]
    body: str
    raw: str


@dataclass(frozen=True, slots=True)
class Transition:
    """One legal workflow transition loaded from protocol.toml."""

    source_role: str
    handoff: str
    target_role: str
    target_template: str | None
    gate: str | None


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return cast("dict[str, Any]", data)


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
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


def _git_ok(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    if result.returncode != 0:
        raise OrchestratorError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _worktree_fingerprint(repo: Path) -> str:
    """Hash staged, unstaged, and untracked state without mutating the repo."""
    digest = hashlib.sha256()
    for label, args in (
        (b"unstaged\0", ("diff", "--binary", "HEAD")),
        (b"staged\0", ("diff", "--cached", "--binary", "HEAD")),
    ):
        digest.update(label)
        digest.update(_git_ok(repo, *args).encode("utf-8", errors="replace"))
    untracked = _git_ok(repo, "ls-files", "--others", "--exclude-standard", "-z")
    for rel in sorted(filter(None, untracked.split("\0"))):
        path = repo / rel
        digest.update(b"untracked\0")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _parse_protocol(path: Path) -> tuple[dict[str, Any], list[Transition]]:
    raw = _load_toml(path)
    if int(raw.get("prompt_schema_version", 0)) != SCHEMA_VERSION:
        raise OrchestratorError(
            f"Unsupported protocol schema {raw.get('prompt_schema_version')!r}; "
            f"expected {SCHEMA_VERSION}."
        )
    transitions: list[Transition] = []
    for item in raw.get("transitions", []):
        transitions.append(
            Transition(
                source_role=str(item["source_role"]).upper(),
                handoff=str(item["handoff"]).upper(),
                target_role=str(item["target_role"]).upper(),
                target_template=(
                    str(item["target_template"]) if item.get("target_template") else None
                ),
                gate=str(item["gate"]) if item.get("gate") else None,
            )
        )
    return raw, transitions


def _transition_for(
    transitions: list[Transition], source: str, handoff: str
) -> Transition:
    matches = [
        transition
        for transition in transitions
        if transition.source_role == source.upper()
        and transition.handoff == handoff.upper()
    ]
    if len(matches) != 1:
        raise OrchestratorError(
            f"Protocol must define exactly one transition for {source}/{handoff}; "
            f"found {len(matches)}."
        )
    return matches[0]


def assemble_config(repo_override: str | None = None) -> dict[str, Any]:
    """Load global wiring, protocol, role CLIs, paths, and templates."""
    orch = _load_toml(AGENTS_DIR / "orchestrator.toml")
    run_cfg = cast("dict[str, Any]", orch.get("run", {}))
    paths_cfg = cast("dict[str, Any]", orch.get("paths", {}))
    repo = Path(repo_override or run_cfg.get("repo_path", REPO_ROOT)).resolve()
    protocol_path = repo / str(paths_cfg.get("protocol", ".agents/protocol.toml"))
    protocol, transitions = _parse_protocol(protocol_path)
    workspace = cast("dict[str, Any]", protocol["task_workspace"])
    journals = {
        "planner": repo / str(workspace["planner_journal"]),
        "executor": repo / str(workspace["executor_journal"]),
        "reviewer": repo / str(workspace["reviewer_journal"]),
    }
    templates = {
        "planner": repo / "docs/templates/prompt/planner.md",
        "executor": repo / "docs/templates/prompt/executor.md",
        "reviewer": repo / "docs/templates/prompt/reviewer.md",
        "reviewer_closeout": repo / "docs/templates/prompt/reviewer-closeout.md",
        "default": repo / "docs/templates/prompt/default.md",
    }
    roles: dict[str, dict[str, Any]] = {}
    for role, filename in cast("dict[str, Any]", orch.get("roles", {})).items():
        role_cfg = _load_toml(AGENTS_DIR / str(filename))
        roles[role] = role_cfg
    return {
        "repo": repo,
        "main_branch": str(run_cfg.get("main_branch", "main")),
        "max_iterations": int(run_cfg.get("max_iterations", 5)),
        "timeout": int(run_cfg.get("invocation_timeout_seconds", 7200)),
        "stream": bool(run_cfg.get("stream_agent_output", True)),
        "heartbeat": int(run_cfg.get("stream_heartbeat_seconds", 60)),
        "retries": int(run_cfg.get("agent_retry_attempts", 1)),
        "protocol": protocol,
        "transitions": transitions,
        "protocol_path": protocol_path,
        "journals": journals,
        "next_agent": repo / str(workspace["next_agent"]),
        "templates": templates,
        "logs_dir": repo / str(paths_cfg.get("logs_dir", ".agents/logs")),
        "runs_dir": repo / str(paths_cfg.get("runs_dir", ".agents/runs")),
        "roles": roles,
    }


def compose_prompt(template_path: Path, fields: dict[str, Any]) -> str:
    text = template_path.read_text(encoding="utf-8")
    for key, value in fields.items():
        text = text.replace("{{" + key + "}}", str(value))
    leftovers = sorted(set(PLACEHOLDER_RE.findall(text)))
    if leftovers:
        raise OrchestratorError(
            f"Template {template_path} has unfilled placeholders: {leftovers}"
        )
    return text


def _escape_toml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _render_next_agent(metadata: dict[str, Any], body: str) -> str:
    ordered = [
        "prompt_schema_version",
        "run_id",
        "task_id",
        "iteration",
        "source_role",
        "target_role",
        "handoff",
        "branch",
        "baseline_commit",
        "source_head",
        "template_path",
        "requires_owner_gate",
        "owner_gate",
    ]
    lines = ["+++"]
    for key in ordered:
        value = metadata[key]
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, int):
            rendered = str(value)
        else:
            rendered = f'"{_escape_toml(str(value))}"'
        lines.append(f"{key} = {rendered}")
    lines.extend(["+++", "", body.rstrip(), ""])
    return "\n".join(lines)


def parse_next_agent(path: Path) -> NextAgentArtifact:
    if not path.exists() or path.stat().st_size == 0:
        raise OrchestratorError(f"Missing/empty next-agent artifact: {path}")
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("+++\n"):
        raise OrchestratorError("next-agent.md must start with TOML front matter (+++).")
    marker = raw.find("\n+++\n", 4)
    if marker < 0:
        raise OrchestratorError("next-agent.md has no closing TOML front matter marker.")
    header = raw[4:marker]
    body = raw[marker + 5 :].lstrip("\n")
    try:
        metadata = cast("dict[str, Any]", tomllib.loads(header))
    except tomllib.TOMLDecodeError as exc:
        raise OrchestratorError(f"Invalid next-agent TOML metadata: {exc}") from exc
    missing = sorted(REQUIRED_NEXT_META - metadata.keys())
    if missing:
        raise OrchestratorError(f"next-agent.md metadata missing fields: {missing}")
    if int(metadata["prompt_schema_version"]) != SCHEMA_VERSION:
        raise OrchestratorError("next-agent.md prompt schema version is unsupported.")
    if PLACEHOLDER_RE.search(body):
        raise OrchestratorError("next-agent.md contains unfilled {{placeholders}}.")
    return NextAgentArtifact(metadata=metadata, body=body, raw=raw)


def _template_key(target_role: str, template_path: str) -> str:
    if target_role == "REVIEWER" and template_path.endswith("reviewer-closeout.md"):
        return "REVIEWER_CLOSEOUT"
    return target_role


def validate_next_agent(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    expected_source: str,
    expected_handoff: str,
) -> NextAgentArtifact:
    artifact = parse_next_agent(cfg["next_agent"])
    meta = artifact.metadata
    transition = _transition_for(cfg["transitions"], expected_source, expected_handoff)
    expected = {
        "run_id": state["run_id"],
        "task_id": state["task"]["task_id"],
        "iteration": state["iteration"],
        "source_role": transition.source_role,
        "target_role": transition.target_role,
        "handoff": transition.handoff,
        "template_path": transition.target_template,
    }
    for key, value in expected.items():
        if value is not None and str(meta.get(key)) != str(value):
            raise OrchestratorError(
                f"next-agent metadata {key}={meta.get(key)!r}; expected {value!r}."
            )
    if str(meta["branch"]) != str(state.get("branch") or meta["branch"]):
        raise OrchestratorError("next-agent branch does not match active run state.")
    if str(meta["baseline_commit"]) != str(state["baseline"]):
        raise OrchestratorError("next-agent baseline commit is stale.")
    current_head = _git_ok(cfg["repo"], "rev-parse", "HEAD")
    if str(meta["source_head"]) != current_head:
        raise OrchestratorError(
            f"next-agent source_head {meta['source_head']} != current HEAD {current_head}."
        )
    gate = transition.gate or ""
    if bool(meta["requires_owner_gate"]) != bool(gate):
        raise OrchestratorError("next-agent owner-gate flag disagrees with protocol.")
    if str(meta["owner_gate"]) != gate:
        raise OrchestratorError("next-agent owner_gate disagrees with protocol.")
    if transition.target_template:
        template_path = cfg["repo"] / transition.target_template
        if not template_path.exists():
            raise OrchestratorError(f"Canonical target template is missing: {template_path}")
        sentinel_key = _template_key(transition.target_role, transition.target_template)
        for sentinel in PROTECTED_SENTINELS.get(sentinel_key, ()):
            if sentinel not in artifact.body:
                raise OrchestratorError(
                    f"next-agent prompt is missing protected {sentinel_key} sentinel: "
                    f"{sentinel!r}"
                )
    state["next_agent"] = {
        "prompt_sha256": _sha_text(artifact.raw),
        "template_sha256": (
            _sha_file(cfg["repo"] / transition.target_template)
            if transition.target_template
            else None
        ),
        "target_role": transition.target_role,
        "handoff": transition.handoff,
        "template_path": transition.target_template,
        "worktree_sha256": _worktree_fingerprint(cfg["repo"]),
    }
    return artifact


def _ensure_pending_artifact_unchanged(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    pending = cast("dict[str, Any]", state.get("next_agent") or {})
    if not pending:
        raise OrchestratorError("Run state has no pending next-agent artifact.")
    current = cfg["next_agent"].read_text(encoding="utf-8")
    if _sha_text(current) != pending.get("prompt_sha256"):
        raise OrchestratorError("next-agent.md changed after it was validated.")
    if _worktree_fingerprint(cfg["repo"]) != pending.get("worktree_sha256"):
        raise OrchestratorError("Working tree changed after next-agent validation.")


def parse_handoff_block(lines: list[str]) -> dict[str, str] | None:
    block: dict[str, str] = {}
    for line in reversed(lines):
        for key, pattern in BLOCK_LINE_RES.items():
            if key in block:
                continue
            match = pattern.match(line)
            if match:
                value = match.group(1).strip("*`_ .;:\"'").upper()
                if value:
                    block[key] = value
        if len(block) == BLOCK_FIELD_COUNT:
            return block
    return None


def latest_handoff_block(journal: Path) -> dict[str, str] | None:
    if not journal.exists():
        return None
    return parse_handoff_block(
        journal.read_text(encoding="utf-8", errors="replace").splitlines()
    )


def _resolve_handoff(
    journal: Path,
    stdout: str,
    role: str,
    allowed: set[str],
) -> dict[str, str]:
    block = latest_handoff_block(journal)
    if not block:
        block = parse_handoff_block(stdout.splitlines())
        if block:
            print(f"[warn] {role} handoff accepted from stdout fallback.")
    if not block:
        raise OrchestratorError(f"{role} produced no handoff block.")
    if block["stopped"] != role.upper() or block["handoff"] not in allowed:
        raise OrchestratorError(f"Invalid {role} handoff: {block}")
    return block


def _validate_activating(block: dict[str, str], transition: Transition) -> None:
    """Fail closed when journal ACTIVATING disagrees with protocol target."""
    expected = transition.target_role
    if block["activating"] != expected:
        raise OrchestratorError(
            f"Handoff ACTIVATING {block['activating']!r}; expected {expected!r} "
            f"for {transition.source_role}/{transition.handoff}."
        )


__all__ = [name for name in globals() if not name.startswith("__")]
