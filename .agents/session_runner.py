#!/usr/bin/env python3
"""Persist and resume one native CLI conversation per workflow role and run."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

AGENTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENTS_DIR.parent
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
POINTER_RE = re.compile(
    r"^Read and follow the instructions in (?P<path>.+) exactly\. "
    r"Perform the full task described there now\.$"
)
SESSION_SCHEMA_VERSION = 1
SUPPORTED_ROLES = frozenset({"PLANNER", "EXECUTOR", "REVIEWER"})


class SessionContinuityError(RuntimeError):
    """Fail-closed role-session continuity error."""


@dataclass(frozen=True, slots=True)
class PromptIdentity:
    """Runtime identity extracted from the current next-agent prompt."""

    run_id: str
    role: str
    iteration: int
    prompt_path: Path


@dataclass(frozen=True, slots=True)
class VendorResult:
    """One vendor CLI invocation result."""

    returncode: int
    stdout: str
    stderr: str


def _resolve_prompt_path(pointer: str) -> Path:
    direct = Path(pointer)
    if direct.is_file():
        return direct.resolve()
    match = POINTER_RE.match(pointer)
    if not match:
        raise SessionContinuityError("Session runner received an invalid prompt pointer.")
    path = Path(match.group("path"))
    if not path.is_absolute():
        path = REPO_ROOT / path
    path = path.resolve()
    if not path.is_file():
        raise SessionContinuityError(f"Prompt file does not exist: {path}")
    return path


def _parse_prompt_identity(pointer: str) -> PromptIdentity:
    path = _resolve_prompt_path(pointer)
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("+++\n"):
        raise SessionContinuityError("Prompt lacks TOML front matter.")
    marker = raw.find("\n+++\n", 4)
    if marker < 0:
        raise SessionContinuityError("Prompt front matter is not closed.")
    try:
        metadata = tomllib.loads(raw[4:marker])
    except tomllib.TOMLDecodeError as exc:
        raise SessionContinuityError(f"Prompt front matter is invalid: {exc}") from exc
    run_id = str(metadata.get("run_id", ""))
    role = str(metadata.get("target_role", "")).upper()
    try:
        iteration = int(metadata.get("iteration", 0))
    except (TypeError, ValueError) as exc:
        raise SessionContinuityError("Prompt iteration is invalid.") from exc
    if not RUN_ID_RE.fullmatch(run_id):
        raise SessionContinuityError(f"Unsafe workflow run id: {run_id!r}")
    if role not in SUPPORTED_ROLES:
        raise SessionContinuityError(f"Unsupported target role: {role!r}")
    if iteration < 1:
        raise SessionContinuityError("Prompt iteration must be positive.")
    return PromptIdentity(run_id=run_id, role=role, iteration=iteration, prompt_path=path)


def _session_state_path(run_id: str) -> Path:
    if not RUN_ID_RE.fullmatch(run_id):
        raise SessionContinuityError(f"Unsafe workflow run id: {run_id!r}")
    return REPO_ROOT / ".agents" / "runs" / run_id / "role-sessions.json"


def _empty_ledger() -> dict[str, Any]:
    return {"schema_version": SESSION_SCHEMA_VERSION, "sessions": {}}


def _load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_ledger()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SessionContinuityError("Role-session ledger must be a JSON object.")
    if int(payload.get("schema_version", 0)) != SESSION_SCHEMA_VERSION:
        raise SessionContinuityError("Unsupported role-session ledger schema.")
    sessions = payload.get("sessions")
    if not isinstance(sessions, dict):
        raise SessionContinuityError("Role-session ledger has invalid sessions data.")
    return cast("dict[str, Any]", payload)


def _save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _existing_record(ledger: dict[str, Any], role: str) -> dict[str, Any] | None:
    sessions = cast("dict[str, Any]", ledger["sessions"])
    record = sessions.get(role)
    if record is None:
        return None
    if not isinstance(record, dict):
        raise SessionContinuityError(f"Invalid stored session record for {role}.")
    return cast("dict[str, Any]", record)


def _validate_record_identity(
    record: dict[str, Any], *, brand: str, model: str, provider: str, effort: str
) -> str:
    expected = {
        "brand": brand,
        "model": model,
        "provider": provider,
        "effort": effort,
    }
    for key, value in expected.items():
        if str(record.get(key, "")) != value:
            raise SessionContinuityError(
                f"Stored role session {key}={record.get(key)!r}; expected {value!r}. "
                "Role transport identity cannot change during a workflow run."
            )
    session_id = str(record.get("session_id", ""))
    if not session_id:
        raise SessionContinuityError("Stored role session has no session id.")
    return session_id


def _record_session(
    ledger: dict[str, Any],
    identity: PromptIdentity,
    *,
    brand: str,
    model: str,
    provider: str,
    effort: str,
    session_id: str,
) -> None:
    if not session_id:
        raise SessionContinuityError("Vendor returned an empty session id.")
    sessions = cast("dict[str, Any]", ledger["sessions"])
    existing = _existing_record(ledger, identity.role)
    if existing is not None:
        old_id = _validate_record_identity(
            existing, brand=brand, model=model, provider=provider, effort=effort
        )
        if old_id != session_id:
            raise SessionContinuityError(
                f"{identity.role} resume returned session {session_id!r}; "
                f"expected exact stored session {old_id!r}."
            )
        if identity.iteration < int(existing.get("last_iteration", 0)):
            raise SessionContinuityError("Role session iteration moved backwards.")
        existing["last_iteration"] = identity.iteration
        return
    for other_role, value in sessions.items():
        if isinstance(value, dict) and str(value.get("session_id", "")) == session_id:
            raise SessionContinuityError(
                f"Cross-role session collision: {identity.role} and {other_role} "
                f"would share {session_id!r}."
            )
    sessions[identity.role] = {
        "brand": brand,
        "model": model,
        "provider": provider,
        "effort": effort,
        "session_id": session_id,
        "created_iteration": identity.iteration,
        "last_iteration": identity.iteration,
    }


def _build_codex_command(
    pointer: str, model: str, effort: str, session_id: str | None
) -> list[str]:
    if session_id:
        return [
            "codex",
            "exec",
            "--json",
            "-c",
            'sandbox_mode="danger-full-access"',
            "resume",
            session_id,
            pointer,
        ]
    return [
        "codex",
        "exec",
        "--json",
        "--sandbox",
        "danger-full-access",
        "-m",
        model,
        "-c",
        f"model_reasoning_effort={effort}",
        pointer,
    ]


def _build_agy_command(
    pointer: str,
    model: str,
    effort: str,
    print_timeout: str,
    session_id: str | None,
) -> list[str]:
    command = [
        "agy",
        "--dangerously-skip-permissions",
        "--model",
        model,
        "--effort",
        effort,
        "--print-timeout",
        print_timeout,
        "--output-format",
        "json",
    ]
    if session_id:
        command.extend(["--conversation", session_id])
    command.extend(["-p", pointer])
    return command


def _build_cline_command(
    pointer: str,
    model: str,
    effort: str,
    provider: str,
    session_id: str | None,
) -> list[str]:
    command = [
        "cline",
        "--json",
        "-P",
        provider,
        "-m",
        model,
        "--thinking",
        effort,
    ]
    if session_id:
        command.extend(["--id", session_id])
    command.append(pointer)
    return command


def build_vendor_command(
    *,
    brand: str,
    pointer: str,
    model: str,
    effort: str,
    provider: str,
    print_timeout: str,
    session_id: str | None,
) -> list[str]:
    """Build a deterministic first-turn or exact-id resume command."""
    if brand == "codex":
        return _build_codex_command(pointer, model, effort, session_id)
    if brand == "agy":
        return _build_agy_command(pointer, model, effort, print_timeout, session_id)
    if brand == "cline":
        if not provider:
            raise SessionContinuityError("Cline session adapter requires a provider id.")
        return _build_cline_command(pointer, model, effort, provider, session_id)
    raise SessionContinuityError(
        f"Native role-session continuity is not implemented for {brand!r}."
    )


def _run_vendor(command: list[str]) -> VendorResult:
    executable = shutil.which(command[0])
    if executable is None:
        raise SessionContinuityError(f"Agent CLI {command[0]!r} is not on PATH.")
    command = [executable, *command[1:]]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return VendorResult(completed.returncode, completed.stdout, completed.stderr)


def _json_objects(stdout: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    stripped = stdout.strip()
    if not stripped:
        return objects
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        objects.append(cast("dict[str, Any]", parsed))
        return objects
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            objects.append(cast("dict[str, Any]", value))
    return objects


def _find_key(value: Any, keys: frozenset[str]) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and isinstance(item, str) and item:
                return item
        for item in value.values():
            found = _find_key(item, keys)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_key(item, keys)
            if found:
                return found
    return None


def extract_session_id(brand: str, stdout: str) -> str:
    """Extract the native session identity from machine-readable CLI output."""
    objects = _json_objects(stdout)
    if brand == "codex":
        for item in objects:
            if item.get("type") == "thread.started":
                thread_id = item.get("thread_id")
                if isinstance(thread_id, str) and thread_id:
                    return thread_id
        raise SessionContinuityError("Codex output contained no thread.started id.")
    if brand == "agy":
        found = _find_key(objects, frozenset({"conversation_id"}))
        if found:
            return found
        raise SessionContinuityError("AGY output contained no conversation_id.")
    if brand == "cline":
        found = _find_key(objects, frozenset({"sessionId", "session_id"}))
        if found:
            return found
        raise SessionContinuityError("Cline output contained no session id.")
    raise SessionContinuityError(f"Unsupported session adapter: {brand!r}")


def probe_adapter(brand: str) -> tuple[bool, str]:
    """Perform a non-conversational static capability probe for doctor output."""
    executable = shutil.which(brand)
    if executable is None:
        return False, f"{brand} CLI is not on PATH"
    if brand == "codex":
        command = [executable, "exec", "resume", "--help"]
        expected = "resume"
    elif brand == "agy":
        command = [executable, "--help"]
        expected = "--conversation"
    elif brand == "cline":
        command = [executable, "--help"]
        expected = "--id"
    else:
        return False, f"native role-session continuity is not implemented for {brand}"
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    if completed.returncode != 0 or expected not in output:
        return False, f"{brand} CLI does not expose expected resume capability {expected}"
    return True, f"{brand} exact-id resume capability declared; runtime verifies returned id"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", required=True, choices=("codex", "agy", "cline"))
    parser.add_argument("--role", required=True, choices=("planner", "executor", "reviewer"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--provider", default="")
    parser.add_argument("--print-timeout", default="110m")
    parser.add_argument("prompt", nargs="?")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.prompt:
        raise SessionContinuityError("Session runner requires the current prompt pointer.")
    identity = _parse_prompt_identity(str(args.prompt))
    requested_role = str(args.role).upper()
    if identity.role != requested_role:
        raise SessionContinuityError(
            f"Prompt targets {identity.role}, but session runner is configured for {requested_role}."
        )
    path = _session_state_path(identity.run_id)
    ledger = _load_ledger(path)
    existing = _existing_record(ledger, identity.role)
    session_id: str | None = None
    if existing is not None:
        session_id = _validate_record_identity(
            existing,
            brand=str(args.brand),
            model=str(args.model),
            provider=str(args.provider),
            effort=str(args.effort),
        )
    command = build_vendor_command(
        brand=str(args.brand),
        pointer=str(args.prompt),
        model=str(args.model),
        effort=str(args.effort),
        provider=str(args.provider),
        print_timeout=str(args.print_timeout),
        session_id=session_id,
    )
    result = _run_vendor(command)
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")
    if result.returncode != 0:
        if session_id and str(args.brand) == "cline":
            sys.stderr.write(
                "Cline native headless --id resume failed. The workflow will not replay "
                "transcripts or silently create a fresh Reviewer session.\n"
            )
        return result.returncode
    returned_id = extract_session_id(str(args.brand), result.stdout)
    if session_id is not None and returned_id != session_id:
        raise SessionContinuityError(
            f"Resume identity mismatch: requested {session_id!r}, got {returned_id!r}."
        )
    _record_session(
        ledger,
        identity,
        brand=str(args.brand),
        model=str(args.model),
        provider=str(args.provider),
        effort=str(args.effort),
        session_id=returned_id,
    )
    _save_ledger(path, ledger)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SessionContinuityError as exc:
        print(f"[SESSION FAIL] {exc}", file=sys.stderr)
        sys.exit(2)
