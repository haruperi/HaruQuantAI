#!/usr/bin/env python3
"""Controller integration for deterministic reviewed-evidence projection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Final

from scripts.project_feature_evidence import (
    ProjectionError,
    apply_outputs,
    build_feature_projection,
    check_outputs,
)

from validation_receipts import (
    ValidationReceiptError,
    candidate_fingerprint,
    verify_validation_receipt,
)

PROJECTION_RECEIPT_SCHEMA: Final[int] = 1
PROJECTION_RECEIPT_KIND: Final[str] = "controller-evidence-projection-receipt"


class EvidenceProjectionError(RuntimeError):
    """Raised when reviewed evidence cannot be projected or verified."""


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceProjectionError(f"Invalid projection JSON: {path}") from exc
    if not isinstance(value, dict):
        raise EvidenceProjectionError(f"Projection JSON must be an object: {path}")
    return value


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def apply_reviewed_projection(
    cfg: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any] | None:
    """Apply feature-local and aggregate evidence after Reviewer PENDING_COMMIT.

    Args:
        cfg: Active workflow configuration.
        state: Active Task state with passed integration evidence.

    Returns:
        Projection receipt state, or ``None`` for non-feature Tasks.

    Raises:
        EvidenceProjectionError: If provenance, scope, or projected bytes fail.
    """
    task = state.get("task", {})
    if str(task.get("task_kind", "feature")).lower() != "feature":
        return None
    # Compatibility and controller self-test Tasks can use feature-shaped
    # identities without a prepared registered-feature packet. Projection is
    # enabled only by the explicit packet authority attached at preparation.
    if not state.get("task_packet_path"):
        return None
    if state.get("parallel_draft") and not state.get("integration_refreshed"):
        return None
    repo = Path(cfg["repo"])
    packet_path = Path(str(state.get("task_packet_path", "")))
    packet = _load_object(packet_path)
    paths = packet.get("paths")
    if not isinstance(paths, dict) or not paths.get("evidence_path"):
        raise EvidenceProjectionError("Task packet has no feature acceptance path.")
    evidence = state.get("integration_validation")
    if not isinstance(evidence, dict) or evidence.get("status") != "PASSED":
        raise EvidenceProjectionError("Evidence projection requires a passed gate.")
    parent_receipt = Path(str(evidence.get("receipt_path", "")))
    pre_hash = str(state.get("reviewed_candidate_hash", ""))
    authority_hash = str(
        state.get("approved_authority_hash", state.get("approved_plan_hash", ""))
    )
    try:
        verify_validation_receipt(
            repo=repo,
            receipt_path=parent_receipt,
            expected_receipt_sha256=str(evidence.get("receipt_sha256", "")),
            expected_worktree_sha256=pre_hash,
            expected_authority_sha256=authority_hash,
        )
    except ValidationReceiptError as exc:
        raise EvidenceProjectionError(str(exc)) from exc

    acceptance_path = repo / str(paths["evidence_path"])
    reviewer_path = Path(cfg["journals"]["reviewer"])
    try:
        outputs = build_feature_projection(
            packet_path=packet_path,
            acceptance_path=acceptance_path,
            reviewer_journal_path=reviewer_path,
            validation_receipt_path=parent_receipt,
            run_id=str(state["run_id"]),
            repo=repo,
        )
    except (OSError, ProjectionError, ValueError) as exc:
        raise EvidenceProjectionError(str(exc)) from exc
    allowed = set(state.get("controller_projection_paths", []))
    unexpected = set(outputs) - allowed
    if unexpected:
        raise EvidenceProjectionError(
            f"Projection output is outside controller authority: {sorted(unexpected)}"
        )
    apply_outputs(outputs, repo=repo)
    drift = check_outputs(outputs, repo=repo)
    if drift:
        raise EvidenceProjectionError(f"Projection is not idempotent: {drift}")
    post_hash = candidate_fingerprint(repo)
    receipt = {
        "schema_version": PROJECTION_RECEIPT_SCHEMA,
        "receipt_kind": PROJECTION_RECEIPT_KIND,
        "producer": "haruquant-workflow-controller",
        "run_id": state["run_id"],
        "parent_validation_receipt": str(parent_receipt),
        "parent_validation_receipt_sha256": evidence["receipt_sha256"],
        "pre_projection_candidate_sha256": pre_hash,
        "post_projection_candidate_sha256": post_hash,
        "reviewer_journal_sha256": _sha_file(reviewer_path),
        "outputs": {
            relative: _sha_bytes(content)
            for relative, content in sorted(outputs.items())
        },
    }
    receipt_path = (
        Path(cfg["logs_dir"])
        / str(state["run_id"])
        / "integration"
        / "evidence-projection-receipt.json"
    )
    raw = _canonical_bytes(receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(raw)
    state["approved_write_paths"] = sorted(
        set(state.get("approved_write_paths", [])) | set(outputs)
    )
    return {
        "status": "APPLIED",
        "receipt_path": str(receipt_path),
        "receipt_sha256": _sha_bytes(raw),
        "pre_projection_candidate_sha256": pre_hash,
        "post_projection_candidate_sha256": post_hash,
        "output_paths": sorted(outputs),
    }


def verify_reviewed_projection(
    *, repo: Path, state: dict[str, Any]
) -> dict[str, Any] | None:
    """Verify derived projection provenance and every resulting repository byte."""
    projection = state.get("evidence_projection")
    if projection is None:
        return None
    if not isinstance(projection, dict) or projection.get("status") != "APPLIED":
        raise EvidenceProjectionError("Projection state is malformed.")
    receipt_path = Path(str(projection.get("receipt_path", "")))
    if not receipt_path.is_file() or _sha_file(receipt_path) != projection.get(
        "receipt_sha256"
    ):
        raise EvidenceProjectionError("Projection receipt is missing or edited.")
    receipt = _load_object(receipt_path)
    if (
        receipt.get("schema_version") != PROJECTION_RECEIPT_SCHEMA
        or receipt.get("receipt_kind") != PROJECTION_RECEIPT_KIND
        or receipt.get("producer") != "haruquant-workflow-controller"
    ):
        raise EvidenceProjectionError("Projection receipt provenance is invalid.")
    evidence = state.get("integration_validation", {})
    parent_path = Path(str(receipt.get("parent_validation_receipt", "")))
    parent_sha = str(receipt.get("parent_validation_receipt_sha256", ""))
    if (
        parent_path != Path(str(evidence.get("receipt_path", "")))
        or parent_sha != evidence.get("receipt_sha256")
        or not parent_path.is_file()
        or _sha_file(parent_path) != parent_sha
    ):
        raise EvidenceProjectionError("Parent validation receipt changed.")
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise EvidenceProjectionError("Projection receipt has no outputs.")
    for relative, expected_hash in outputs.items():
        path = repo / str(relative)
        if not path.is_file() or _sha_file(path) != expected_hash:
            raise EvidenceProjectionError(f"Projected output changed: {relative}")
    post_hash = str(receipt.get("post_projection_candidate_sha256", ""))
    if candidate_fingerprint(repo) != post_hash:
        raise EvidenceProjectionError("Projected candidate changed.")
    return receipt
