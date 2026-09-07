#!/usr/bin/env python3
"""Artifact-driven Planner -> Executor -> Reviewer orchestrator for HaruQuantAI.

The active task workspace is ``.agents/task``. The three role journals are
append-only while a task is active; ``next-agent.md`` is replace-only and is
the complete executable prompt for the next role. Runtime routing validates
that artifact against ``.agents/protocol.toml`` before any role is launched.

Schema-v3 runtime policy separates IDE-native, headless, and manual transport
while every mode consumes the same validated ``next-agent.md`` contract.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from runtime_policy import load_runtime_policy

AGENTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENTS_DIR.parent
SCHEMA_VERSION = 1
BLOCK_FIELD_COUNT = 3
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
PLACEHOLDER_RE = re.compile(r"\{\{\w+\}\}")
BLOCK_LINE_RES = {
    "stopped": re.compile(r"^[>\s#`*_-]*STOPPED[\s`*_-]*:\s*(.+?)\s*$", re.IGNORECASE),
    "activating": re.compile(
        r"^[>\s#`*_-]*ACTIVATING[\s`*_-]*:\s*(.+?)\s*$", re.IGNORECASE
    ),
    "handoff": re.compile(r"^[>\s#`*_-]*HANDOFF[\s`*_-]*:\s*(.+?)\s*$", re.IGNORECASE),
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
        "Act as the **HaruQuantAI Principal Software Architect and Implementation Planner**",
        "This prompt defines your complete **Planner-specific role contract**.",
        "HANDOFF : PENDING_APPROVAL",
    ),
    "EXECUTOR": (
        "Act as the **HaruQuantAI Senior Software Implementation Engineer**",
        "This prompt defines your complete **Executor-specific role contract**.",
        "HANDOFF : READY_FOR_REVIEW",
    ),
    "REVIEWER": (
        "Act as the **HaruQuantAI Principal Software Verification and Code Review Engineer**",
        "This prompt defines your complete **Reviewer-specific role contract**.",
        "Stage A — Independent reconstruction",
        "Stage B — Independent verification",
        "Stage C — Dry-run, report, and code reconciliation",
    ),
    "REVIEWER_CLOSEOUT": (
        "Act as the **HaruQuantAI Release Integrity and Change-Control Engineer**",
        "This prompt defines your complete **close-out-specific role contract**.",
        "HANDOFF : ACCEPTED",
        "explicit no-fast-forward merge",
    ),
}


class OrchestratorError(RuntimeError):
    """Fail-closed orchestration error."""


class ScopeMutationError(OrchestratorError):
    """A role changed repository paths outside its deterministic authority."""

    def __init__(self, role: str, offending_paths: list[str]) -> None:
        self.role = role.upper()
        self.offending_paths = tuple(sorted(offending_paths))
        super().__init__(
            f"{self.role} modified unauthorized paths: {list(self.offending_paths)}"
        )


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
    return data


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    git_exe = shutil.which("git") or "git"
    return subprocess.run(
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
                    str(item["target_template"])
                    if item.get("target_template")
                    else None
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
    repo = Path(repo_override or REPO_ROOT).resolve()
    runtime_path = repo / ".agents/run-config.toml"
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
    runtime_policy = load_runtime_policy(
        runtime_path,
        legacy_roles=roles,
        default_max_iterations=int(run_cfg.get("max_iterations", 5)),
    )
    runtime_roles = (
        {
            role: runtime_policy.role_config(role)
            for role in ("planner", "executor", "reviewer")
        }
        if runtime_policy.is_headless
        else {}
    )
    return {
        "repo": repo,
        "main_branch": str(run_cfg.get("main_branch", "main")),
        "max_iterations": runtime_policy.max_iterations,
        "timeout": int(run_cfg.get("invocation_timeout_seconds", 7200)),
        "stream": bool(run_cfg.get("stream_agent_output", True)),
        "heartbeat": int(run_cfg.get("stream_heartbeat_seconds", 60)),
        "retries": int(run_cfg.get("agent_retry_attempts", 1)),
        "mode": runtime_policy.effective_mode,
        "approval_policy": runtime_policy.approval_policy,
        "runtime_policy": runtime_policy,
        "runtime_policy_fingerprint": runtime_policy.fingerprint,
        "runtime_policy_path": runtime_path,
        "legacy_roles": roles,
        "protocol": protocol,
        "session_continuity": cast(
            "dict[str, Any]", protocol.get("session_continuity", {})
        ),
        "transitions": transitions,
        "protocol_path": protocol_path,
        "journals": journals,
        "next_agent": repo / str(workspace["next_agent"]),
        "templates": templates,
        "logs_dir": repo / str(paths_cfg.get("logs_dir", ".agents/logs")),
        "runs_dir": repo / str(paths_cfg.get("runs_dir", ".agents/runs")),
        "roles": runtime_roles,
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
        "allowed_write_paths",
    ]
    lines = ["+++"]
    for key in ordered:
        if key not in metadata:
            continue
        value = metadata[key]
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, int):
            rendered = str(value)
        elif isinstance(value, list):
            rendered = (
                "[" + ", ".join(f'"{_escape_toml(str(item))}"' for item in value) + "]"
            )
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
        raise OrchestratorError(
            "next-agent.md must start with TOML front matter (+++)."
        )
    marker = raw.find("\n+++\n", 4)
    if marker < 0:
        raise OrchestratorError(
            "next-agent.md has no closing TOML front matter marker."
        )
    header = raw[4:marker]
    body = raw[marker + 5 :].lstrip("\n")
    try:
        metadata = tomllib.loads(header)
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
    if (
        expected_source.upper() == "PLANNER"
        and expected_handoff.upper() == "PENDING_APPROVAL"
    ):
        raw_paths = meta.get("allowed_write_paths")
        if not isinstance(raw_paths, list):
            raise OrchestratorError(
                "Planner handoff requires allowed_write_paths metadata."
            )
        metadata_paths = _normalize_path_list([str(item) for item in raw_paths])
        journal_text = cfg["journals"]["planner"].read_text(encoding="utf-8")
        matches = re.findall(
            r"(?ms)^ALLOWED_WRITE_PATHS:\s*$\n(?P<body>.*?)^END_ALLOWED_WRITE_PATHS:\s*$",
            journal_text,
        )
        if not matches:
            raise OrchestratorError("Planner journal lacks a path-authority block.")
        journal_paths = _normalize_path_list(
            [
                line.strip()[2:].strip()
                for line in matches[-1].splitlines()
                if line.strip().startswith("- ")
            ]
        )
        if journal_paths != metadata_paths:
            raise OrchestratorError(
                "Planner journal path authority differs from next-agent metadata."
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
            raise OrchestratorError(
                f"Canonical target template is missing: {template_path}"
            )
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
        "source_head": str(meta["source_head"]),
        "branch": str(meta["branch"]),
        "baseline_commit": str(meta["baseline_commit"]),
        "worktree_sha256": _worktree_fingerprint(cfg["repo"]),
    }
    return artifact


def _ensure_pending_artifact_unchanged(
    cfg: dict[str, Any], state: dict[str, Any]
) -> None:
    """Verify the pending next-agent artifact hasn't been tampered with."""
    pending = cast("dict[str, Any]", state.get("next_agent") or {})
    if not pending:
        raise OrchestratorError("Run state has no pending next-agent artifact.")
    current = cfg["next_agent"].read_text(encoding="utf-8")
    if _sha_text(current) != pending.get("prompt_sha256"):
        raise OrchestratorError("next-agent.md changed after it was validated.")
    if str(pending.get("baseline_commit")) != str(state["baseline"]):
        raise OrchestratorError("Pending artifact baseline contradicts active run.")
    current_branch = _git_ok(cfg["repo"], "branch", "--show-current")
    expected_branch = state.get("branch")
    if expected_branch and current_branch != expected_branch:
        raise OrchestratorError(
            f"Branch changed after validation: {current_branch!r} != {expected_branch!r}"
        )
    current_head = _git_ok(cfg["repo"], "rev-parse", "HEAD")
    expected_head = pending.get("source_head")
    if expected_head and current_head != expected_head:
        raise OrchestratorError(
            f"HEAD changed after validation (possible commit): "
            f"{current_head[:12]} != {expected_head[:12]}"
        )
    template_path = pending.get("template_path")
    if template_path:
        full_path = cfg["repo"] / template_path
        if full_path.exists():
            current_template_sha = _sha_file(full_path)
            if current_template_sha != pending.get("template_sha256"):
                raise OrchestratorError(
                    f"Canonical template changed after validation: {template_path}"
                )
    if _worktree_fingerprint(cfg["repo"]) != pending.get("worktree_sha256"):
        raise OrchestratorError("Working tree changed after next-agent validation.")
    artifact = parse_next_agent(cfg["next_agent"])
    expected_role = pending.get("target_role")
    if (
        expected_role
        and str(artifact.metadata.get("target_role", "")).upper()
        != expected_role.upper()
    ):
        raise OrchestratorError(
            f"Target role changed: {artifact.metadata.get('target_role')!r} "
            f"!= {expected_role!r}"
        )
    transition = _transition_for(
        cfg["transitions"],
        str(artifact.metadata["source_role"]),
        str(artifact.metadata["handoff"]),
    )
    if transition.target_role != str(artifact.metadata["target_role"]).upper():
        raise OrchestratorError("Pending target role no longer matches protocol.")
    if transition.target_template != str(artifact.metadata["template_path"]):
        raise OrchestratorError("Pending template no longer matches protocol.")


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


def _extract_pre_gate_content(journal_content: str, iteration: int) -> str | None:
    """Extract journal content before the owner gate for a specific iteration."""
    gate_marker = f"### Owner Gate — Dry Run {iteration}"
    starts = [
        match.start() for match in re.finditer(re.escape(gate_marker), journal_content)
    ]
    if len(starts) != 1:
        return None
    return journal_content[: starts[0]]


def _verify_approval_chain(
    journal: Path,
    iteration: int,
    task_id: str,
    baseline: str,
    branch: str,
    approved_plan_hash: str,
    authorization_source: str = "OWNER_MESSAGE",
    runtime_policy_fingerprint: str = "",
    scope_fingerprint: str = "",
) -> None:
    """Verify the approval chain for a given iteration."""
    content_bytes = journal.read_bytes()
    gate_marker = f"### Owner Gate — Dry Run {iteration}"
    marker_bytes = gate_marker.encode("utf-8")
    starts = [
        match.start() for match in re.finditer(re.escape(marker_bytes), content_bytes)
    ]
    if len(starts) != 1:
        raise OrchestratorError(
            f"Expected one owner gate for iteration {iteration}; found {len(starts)}."
        )
    computed_hash = hashlib.sha256(content_bytes[: starts[0]]).hexdigest()
    if computed_hash != approved_plan_hash:
        raise OrchestratorError(
            f"Approval chain broken: computed {computed_hash[:16]}... "
            f"!= approved {approved_plan_hash[:16]}..."
        )
    content = content_bytes.decode("utf-8")
    gate_start = content.find(gate_marker)
    next_gate = content.find("### Owner Gate ", gate_start + len(gate_marker))
    gate_block = content[gate_start : next_gate if next_gate >= 0 else None]
    if runtime_policy_fingerprint and "Gate: APPROVED: EXECUTE" not in gate_block:
        raise OrchestratorError("Execute gate label mismatch.")
    if f"Plan SHA-256: {approved_plan_hash}" not in gate_block:
        raise OrchestratorError("Owner gate plan hash mismatch.")
    if f"Task ID: {task_id}" not in gate_block:
        raise OrchestratorError("Owner gate task ID mismatch.")
    if f"Dry Run: {iteration}" not in gate_block:
        raise OrchestratorError("Owner gate iteration mismatch.")
    if f"Main baseline: {baseline}" not in gate_block:
        raise OrchestratorError("Owner gate baseline mismatch.")
    if f"Task branch: {branch}" not in gate_block:
        raise OrchestratorError("Owner gate branch mismatch.")
    authorization_line = f"Authorization source: {authorization_source}"
    if authorization_line not in gate_block and runtime_policy_fingerprint:
        raise OrchestratorError("Gate authorization source mismatch.")
    if authorization_source == "RUN_PREAUTHORIZATION":
        if f"Runtime policy SHA-256: {runtime_policy_fingerprint}" not in gate_block:
            raise OrchestratorError("Gate runtime-policy fingerprint mismatch.")
        if f"Frozen scope SHA-256: {scope_fingerprint}" not in gate_block:
            raise OrchestratorError("Gate frozen-scope fingerprint mismatch.")


_SNAPSHOT_IGNORE_PREFIXES = (
    ".agents/logs/",
    ".agents/runs/",
    ".agents/workflow.lock",
)


def capture_repository_snapshot(repo: Path) -> dict[str, str]:
    """Capture a snapshot of all tracked and relevant untracked files."""
    snapshot: dict[str, str] = {}
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    for line in result.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        full_path = repo / path
        if full_path.is_file():
            try:
                snapshot[path] = _sha_file(full_path)
            except OSError:
                snapshot[path] = "ERROR"
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    for line in untracked.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        if any(path.startswith(prefix) for prefix in _SNAPSHOT_IGNORE_PREFIXES):
            continue
        full_path = repo / path
        if full_path.is_file():
            try:
                snapshot[path] = _sha_file(full_path)
            except OSError:
                snapshot[path] = "ERROR"
    return snapshot


def compute_snapshot_delta(
    before: dict[str, str],
    after: dict[str, str],
) -> dict[str, set[str]]:
    """Compute the delta between two repository snapshots."""
    created = set(after.keys()) - set(before.keys())
    deleted = set(before.keys()) - set(after.keys())
    modified = {
        path
        for path in set(before.keys()) & set(after.keys())
        if before[path] != after[path]
    }
    return {"created": created, "modified": modified, "deleted": deleted}


ROLE_INTRINSIC_PATHS: dict[str, frozenset[str]] = {
    "PLANNER": frozenset({".agents/task/planner.md", ".agents/task/next-agent.md"}),
    "EXECUTOR": frozenset({".agents/task/executor.md", ".agents/task/next-agent.md"}),
    "REVIEWER": frozenset({".agents/task/reviewer.md", ".agents/task/next-agent.md"}),
}

ALL_COORDINATION_PATHS = frozenset(
    {
        ".agents/task/planner.md",
        ".agents/task/executor.md",
        ".agents/task/reviewer.md",
        ".agents/task/next-agent.md",
    }
)


def _normalize_path_list(paths: list[str]) -> list[str]:
    """Normalize and validate a list of repository-relative paths."""
    normalized: set[str] = set()
    for raw in paths:
        path = raw.strip().replace("\\", "/")
        if not path:
            continue
        if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
            raise OrchestratorError(f"Absolute path not allowed: {path}")
        if ".." in path.split("/"):
            raise OrchestratorError(f"Path traversal not allowed: {path}")
        # Reject the Git metadata directory as a path component, not every
        # legitimate repository file whose name begins with ``.git``.  Path
        # separators are normalized above; case-folding keeps the boundary
        # fail-closed on case-insensitive filesystems such as Windows.
        first_component = path.split("/", maxsplit=1)[0]
        if first_component.casefold() == ".git":
            raise OrchestratorError(f".git path not allowed: {path}")
        normalized.add(path)
    return sorted(normalized)


def validate_role_mutations(
    role: str,
    delta: dict[str, set[str]],
    *,
    approved_write_paths: set[str] | None = None,
) -> None:
    """Validate that a role's mutations are within its authorized paths."""
    role_upper = role.upper()
    allowed = set(ROLE_INTRINSIC_PATHS.get(role_upper, frozenset()))
    if role_upper == "EXECUTOR" and approved_write_paths is not None:
        allowed |= approved_write_paths
    all_mutations = delta["created"] | delta["modified"] | delta["deleted"]
    violations = all_mutations - allowed
    if violations:
        raise ScopeMutationError(role, sorted(violations))


def validate_no_commits(
    repo: Path,
    baseline_head: str,
    current_head: str,
) -> None:
    """Verify that HEAD has not changed (no commits were made)."""
    if current_head != baseline_head:
        raise OrchestratorError(
            f"Role made commits: HEAD changed from {baseline_head[:12]} "
            f"to {current_head[:12]}"
        )


def validate_role_branch(repo: Path, expected_branch: str) -> None:
    """Verify that the current branch has not changed."""
    current = _git_ok(repo, "branch", "--show-current")
    if current != expected_branch:
        raise OrchestratorError(
            f"Role changed branch: current={current!r}, expected={expected_branch!r}"
        )


__all__ = [name for name in globals() if not name.startswith("__")]
