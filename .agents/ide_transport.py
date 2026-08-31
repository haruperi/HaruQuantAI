#!/usr/bin/env python3
"""Deterministic role boundaries for IDE-native workflow modes."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, cast

from workflow_protocol import (
    OrchestratorError,
    _ensure_pending_artifact_unchanged,
    _git_ok,
    capture_repository_snapshot,
    compute_snapshot_delta,
    validate_no_commits,
    validate_role_branch,
    validate_role_mutations,
)

IDE_MODES = frozenset({"solo", "delegate"})
APP_HANDLE_SCHEMA_VERSION = 1


def _save_run_state(cfg: dict[str, Any], state: dict[str, Any]) -> Path:
    runs_dir = Path(cfg["runs_dir"])
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{state['run_id']}.json"
    path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return path


def _record_event(state: dict[str, Any], phase: str, **extra: Any) -> None:
    entry = {
        "time": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
        "phase": phase,
        "iteration": state["iteration"],
        **extra,
    }
    state.setdefault("history", []).append(entry)


def _handle_path(cfg: dict[str, Any], state: dict[str, Any]) -> Path:
    return Path(cfg["runs_dir"]) / str(state["run_id"]) / "app-agent-handles.json"


def _load_handles(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": APP_HANDLE_SCHEMA_VERSION, "agents": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"Invalid app-agent handle ledger: {exc}") from exc
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != APP_HANDLE_SCHEMA_VERSION
        or not isinstance(value.get("agents"), dict)
    ):
        raise OrchestratorError("App-agent handle ledger has an invalid schema.")
    return cast("dict[str, Any]", value)


def _save_handles(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _bind_delegate_handle(
    cfg: dict[str, Any],
    state: dict[str, Any],
    role: str,
    agent_id: str | None,
) -> str:
    if not agent_id or not agent_id.strip():
        raise OrchestratorError(
            "Delegate mode requires --app-agent-id for every completed role turn."
        )
    normalized = agent_id.strip()
    path = _handle_path(cfg, state)
    ledger = _load_handles(path)
    agents = cast("dict[str, Any]", ledger["agents"])
    existing = agents.get(role)
    if existing is not None:
        if not isinstance(existing, dict) or existing.get("agent_id") != normalized:
            raise OrchestratorError(
                f"Delegate {role} handle changed during the active Task run."
            )
        previous = int(existing.get("last_iteration", 0))
        if int(state["iteration"]) < previous:
            raise OrchestratorError("Delegate role iteration moved backwards.")
        existing["last_iteration"] = int(state["iteration"])
    else:
        collisions = [
            other
            for other, record in agents.items()
            if isinstance(record, dict) and record.get("agent_id") == normalized
        ]
        if collisions:
            raise OrchestratorError(
                f"Delegate app-agent handle is already bound to {collisions[0]}."
            )
        agents[role] = {
            "agent_id": normalized,
            "created_iteration": int(state["iteration"]),
            "last_iteration": int(state["iteration"]),
        }
    _save_handles(path, ledger)
    return normalized


def expected_delegate_handle(
    cfg: dict[str, Any], state: dict[str, Any], role: str
) -> str | None:
    """Return the previously bound app-agent handle for one role, if any."""
    ledger = _load_handles(_handle_path(cfg, state))
    record = cast("dict[str, Any]", ledger["agents"]).get(role)
    if not isinstance(record, dict):
        return None
    value = record.get("agent_id")
    return str(value) if value else None


def prepare_ide_role(
    cfg: dict[str, Any],
    state: dict[str, Any],
    role: str,
    *,
    authorized_closeout: bool = False,
) -> None:
    """Freeze the pre-role repository boundary and expose the validated prompt."""
    mode = str(cfg.get("mode", ""))
    if mode not in IDE_MODES:
        raise OrchestratorError(f"Mode {mode!r} is not IDE-native.")
    if state.get("ide_role_invocation") is not None:
        raise OrchestratorError("An IDE role invocation is already pending completion.")
    _ensure_pending_artifact_unchanged(cfg, state)
    pending = cast("dict[str, Any]", state["next_agent"])
    if str(pending.get("target_role", "")).upper() != role.upper():
        raise OrchestratorError(
            f"Pending prompt targets {pending.get('target_role')!r}, not {role!r}."
        )
    repo = Path(cfg["repo"])
    branch = str(state.get("branch", ""))
    validate_role_branch(repo, branch)
    state["ide_role_invocation"] = {
        "mode": mode,
        "role": role.upper(),
        "iteration": int(state["iteration"]),
        "branch": branch,
        "head": _git_ok(repo, "rev-parse", "HEAD"),
        "snapshot": capture_repository_snapshot(repo),
        "prompt_sha256": pending["prompt_sha256"],
        "authorized_closeout": authorized_closeout,
    }
    _record_event(
        state,
        "ide_role_prepared",
        role=role.upper(),
        mode=mode,
        authorized_closeout=authorized_closeout,
    )
    _save_run_state(cfg, state)
    expected = (
        expected_delegate_handle(cfg, state, role.upper())
        if mode == "delegate"
        else None
    )
    action = "perform in this IDE chat"
    if mode == "delegate":
        action = (
            f"resume app agent {expected}"
            if expected
            else "spawn and retain a new inspectable app-native role agent"
        )
    print(
        "[ROLE_READY] "
        f"run_id={state['run_id']} role={role.upper()} iteration={state['iteration']} "
        f"mode={mode} action={action} prompt={cfg['next_agent']}"
    )


def complete_ide_role(
    cfg: dict[str, Any],
    state: dict[str, Any],
    role: str,
    *,
    app_agent_id: str | None,
    authorized_closeout: bool = False,
) -> tuple[str, Path]:
    """Validate one completed IDE role turn and return an audit-log path."""
    invocation = state.get("ide_role_invocation")
    if not isinstance(invocation, dict):
        raise OrchestratorError("No prepared IDE role invocation awaits completion.")
    mode = str(cfg.get("mode", ""))
    if (
        invocation.get("mode") != mode
        or invocation.get("role") != role.upper()
        or int(invocation.get("iteration", 0)) != int(state["iteration"])
        or bool(invocation.get("authorized_closeout")) != authorized_closeout
    ):
        raise OrchestratorError(
            "IDE role completion identity does not match preparation."
        )
    if mode == "delegate":
        bound_id = _bind_delegate_handle(cfg, state, role.upper(), app_agent_id)
    else:
        if app_agent_id:
            raise OrchestratorError("Solo mode does not accept an app-agent handle.")
        bound_id = ""

    repo = Path(cfg["repo"])
    if not authorized_closeout:
        current_head = _git_ok(repo, "rev-parse", "HEAD")
        validate_no_commits(repo, str(invocation["head"]), current_head)
        validate_role_branch(repo, str(invocation["branch"]))
        delta = compute_snapshot_delta(
            cast("dict[str, str]", invocation["snapshot"]),
            capture_repository_snapshot(repo),
        )
        approved = state.get("approved_write_paths")
        validate_role_mutations(
            role,
            delta,
            approved_write_paths=set(approved) if approved else None,
        )

    logs_dir = Path(cfg["logs_dir"])
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%d-%H%M%S")
    log = logs_dir / (
        f"{stamp}-{state['run_id']}-{role.lower()}-{state['iteration']}-ide.log"
    )
    log.write_text(
        "\n".join(
            (
                f"mode: {mode}",
                f"role: {role.upper()}",
                f"iteration: {state['iteration']}",
                f"app_agent_id: {bound_id or '(inline)'}",
                f"authorized_closeout: {authorized_closeout}",
                "result: deterministic boundary validation passed",
                "",
            )
        ),
        encoding="utf-8",
    )
    stdout = (
        "STOPPED : REVIEWER\nACTIVATING : NONE\nHANDOFF : ACCEPTED\n"
        if authorized_closeout
        else ""
    )
    return stdout, log


def finish_ide_role(state: dict[str, Any]) -> None:
    """Clear a prepared IDE invocation only after its handoff is accepted."""
    state.pop("ide_role_invocation", None)


__all__ = [
    "IDE_MODES",
    "complete_ide_role",
    "expected_delegate_handle",
    "finish_ide_role",
    "prepare_ide_role",
]
