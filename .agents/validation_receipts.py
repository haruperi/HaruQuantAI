#!/usr/bin/env python3
"""Controller-owned creation and verification of validation receipts."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Final

from workflow_protocol import _git_ok

RECEIPT_SCHEMA_VERSION: Final[int] = 1
POLICY_INPUTS: Final[tuple[str, ...]] = (
    "scripts/ci_check.py",
    "scripts/validation_router.py",
    "pyproject.toml",
    "uv.lock",
    "app/ui/package-lock.json",
    ".agents/protocol.toml",
)


class ValidationReceiptError(RuntimeError):
    """Raised when controller validation evidence is incomplete or stale."""


def candidate_fingerprint(repo: Path) -> str:
    """Hash candidate bytes while excluding role coordination artifacts."""
    digest = hashlib.sha256()
    exclusions = tuple(
        f":(exclude){path}"
        for path in (
            ".agents/task/planner.md",
            ".agents/task/executor.md",
            ".agents/task/reviewer.md",
            ".agents/task/next-agent.md",
        )
    )
    for label, arguments in (
        ("unstaged", ("diff", "--binary", "HEAD", "--", ".", *exclusions)),
        (
            "staged",
            ("diff", "--cached", "--binary", "HEAD", "--", ".", *exclusions),
        ),
    ):
        digest.update(label.encode("ascii") + b"\0")
        digest.update(_git_ok(repo, *arguments).encode("utf-8", errors="replace"))
    untracked = [
        path
        for path in _git_ok(
            repo, "ls-files", "--others", "--exclude-standard"
        ).splitlines()
        if path and not path.replace("\\", "/").startswith(".agents/task/")
    ]
    for relative in sorted(untracked):
        path = repo / relative
        digest.update(b"untracked\0" + relative.encode("utf-8") + b"\0")
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationReceiptError(f"Invalid validation JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValidationReceiptError(f"Validation JSON is not an object: {path}")
    return value


def _input_manifest(repo: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    decision = report.get("decision")
    if not isinstance(decision, dict):
        raise ValidationReceiptError("Diagnostic report has no routing decision.")
    paths = {
        *[str(path) for path in decision.get("changed_paths", [])],
        *POLICY_INPUTS,
        *[str(path) for path in decision.get("python_test_paths", [])],
        *[
            f"app/ui/{path}" if not str(path).startswith("app/ui/") else str(path)
            for path in decision.get("ui_test_paths", [])
        ],
    }
    paths = {path for path in paths if not path.startswith(".agents/task/")}
    manifest: list[dict[str, Any]] = []
    for relative in sorted(paths):
        path = repo / relative
        manifest.append(
            {
                "path": relative.replace("\\", "/"),
                "state": "FILE" if path.is_file() else "MISSING",
                "sha256": _sha_file(path) if path.is_file() else None,
            }
        )
    return manifest


def create_validation_receipt(
    *,
    repo: Path,
    diagnostic_path: Path,
    receipt_path: Path,
    worktree_sha256: str,
    authority_sha256: str,
) -> str:
    """Create a source-bound receipt from one successful runner diagnostic.

    Returns:
        SHA-256 of the canonical receipt bytes.
    """
    report = _load_object(diagnostic_path)
    if report.get("report_kind") != "diagnostic-not-reusable-validation-receipt":
        raise ValidationReceiptError("Unexpected diagnostic report kind.")
    steps = report.get("steps")
    results = report.get("results")
    if not isinstance(steps, list) or not isinstance(results, list) or not steps:
        raise ValidationReceiptError("Diagnostic report has no completed steps.")
    if len(steps) != len(results):
        raise ValidationReceiptError("Diagnostic report skipped validation steps.")
    logs: list[dict[str, str]] = []
    for step, result in zip(steps, results, strict=True):
        if not isinstance(step, dict) or not isinstance(result, dict):
            raise ValidationReceiptError("Diagnostic entries are malformed.")
        if step.get("step_id") != result.get("step_id") or result.get("exit_code") != 0:
            raise ValidationReceiptError(
                "Diagnostic contains failed or mismatched steps."
            )
        log_path = Path(str(result.get("log_path", "")))
        log_hash = str(result.get("log_sha256", ""))
        if not log_path.is_file() or _sha_file(log_path) != log_hash:
            raise ValidationReceiptError("Validation log is missing or changed.")
        logs.append({"path": str(log_path), "sha256": log_hash})
    decision = report["decision"]
    candidate = decision.get("candidate")
    if not isinstance(candidate, dict):
        raise ValidationReceiptError("Diagnostic candidate identity is missing.")
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "receipt_kind": "controller-validation-receipt",
        "producer": "haruquant-workflow-controller",
        "candidate": candidate,
        "reviewed_worktree_sha256": worktree_sha256,
        "authority_sha256": authority_sha256,
        "input_manifest": _input_manifest(repo, report),
        "validation_policy": {
            "requested_profile": decision.get("requested_profile"),
            "selected_families": decision.get("selected_families"),
            "routing_reasons": decision.get("reasons"),
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "steps": steps,
        "results": results,
        "logs": logs,
        "diagnostic_path": str(diagnostic_path),
        "diagnostic_sha256": _sha_file(diagnostic_path),
    }
    raw = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(raw, encoding="utf-8", newline="\n")
    return _sha_bytes(raw.encode("utf-8"))


def verify_validation_receipt(
    *,
    repo: Path,
    receipt_path: Path,
    expected_receipt_sha256: str,
    expected_worktree_sha256: str,
    expected_authority_sha256: str,
) -> dict[str, Any]:
    """Verify controller provenance, exact candidate and every input/log hash."""
    if not receipt_path.is_file() or _sha_file(receipt_path) != expected_receipt_sha256:
        raise ValidationReceiptError("Validation receipt is missing or edited.")
    receipt = _load_object(receipt_path)
    if (
        receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION
        or receipt.get("receipt_kind") != "controller-validation-receipt"
        or receipt.get("producer") != "haruquant-workflow-controller"
    ):
        raise ValidationReceiptError("Validation receipt provenance is invalid.")
    if receipt.get("reviewed_worktree_sha256") != expected_worktree_sha256:
        raise ValidationReceiptError("Validation receipt candidate changed.")
    if receipt.get("authority_sha256") != expected_authority_sha256:
        raise ValidationReceiptError("Validation receipt authority changed.")
    for item in receipt.get("input_manifest", []):
        path = repo / str(item.get("path", ""))
        expected_state = item.get("state")
        if expected_state == "FILE":
            if not path.is_file() or _sha_file(path) != item.get("sha256"):
                raise ValidationReceiptError(f"Validation input changed: {path}")
        elif path.exists():
            raise ValidationReceiptError(f"Validation input appeared: {path}")
    for item in receipt.get("logs", []):
        path = Path(str(item.get("path", "")))
        if not path.is_file() or _sha_file(path) != item.get("sha256"):
            raise ValidationReceiptError("Validation receipt log changed.")
    diagnostic_path = Path(str(receipt.get("diagnostic_path", "")))
    if not diagnostic_path.is_file() or _sha_file(diagnostic_path) != receipt.get(
        "diagnostic_sha256"
    ):
        raise ValidationReceiptError("Validation diagnostic changed.")
    return receipt
