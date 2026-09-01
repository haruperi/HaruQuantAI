"""Safe checksum manifest assembly for completed Simulation artifacts."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

from app.composition.logging import get_logger
from app.services.simulator.errors import SimulationError
from app.services.simulator.reporting.contracts import (
    ANALYTICS_REPORT_ARTIFACT_NAME,
    CANONICAL_ARTIFACT_TYPES,
    ArtifactEntry,
    ArtifactManifest,
)

logger = get_logger(__name__)

_MEDIA_TYPES = {
    "journal.jsonl": "application/x-ndjson",
    "result.json": "application/json",
    "report.md": "text/markdown",
    ANALYTICS_REPORT_ARTIFACT_NAME: "application/json",
}

#: Default artifact root mirroring the API bootstrap's simulation artifact
#: directory; the composition root owns the configured absolute location.
_DEFAULT_ARTIFACT_ROOT = Path("artifacts/simulation")


def _resolve_artifacts(root: Path, paths: Sequence[Path]) -> dict[str, Path]:
    """Resolve and validate the exact canonical artifact sequence.

    Args:
        root: Approved resolved artifact root.
        paths: Candidate artifact paths in canonical order.

    Returns:
        Mapping from canonical name to resolved path.

    Raises:
        OSError: If containment, uniqueness, or completeness fails.
    """
    logger.debug("Resolving canonical Simulation artifact paths")
    resolved_by_name: dict[str, Path] = {}
    for path in paths:
        resolved = path.resolve(strict=True)
        if root != resolved.parent and root not in resolved.parents:
            raise OSError("artifact escaped approved root")
        if resolved.name in resolved_by_name:
            raise OSError("artifact name is duplicated")
        resolved_by_name[resolved.name] = resolved
    if tuple(resolved_by_name) != CANONICAL_ARTIFACT_TYPES:
        raise OSError("canonical artifact order or completeness differs")
    return resolved_by_name


def build_artifact_manifest(
    artifact_root: Path,
    paths: Sequence[Path],
    *,
    created_at: datetime,
) -> ArtifactManifest:
    """Hash completed contained artifacts into a stable acyclic manifest.

    Args:
        artifact_root: Approved artifact root.
        paths: Exact completed canonical artifact paths.
        created_at: Deterministic run evidence timestamp.

    Returns:
        Immutable ordered manifest.

    Raises:
        SimulationError: If containment, completeness, or reading fails.
    """
    logger.info("Building canonical Simulation artifact manifest")
    root = artifact_root.resolve()
    try:
        resolved_by_name = _resolve_artifacts(root, paths)
        entries = tuple(
            ArtifactEntry(
                relative_path=name,
                media_type=_MEDIA_TYPES[name],
                size_bytes=resolved_by_name[name].stat().st_size,
                sha256=sha256(resolved_by_name[name].read_bytes()).hexdigest(),
                created_at=created_at,
            )
            for name in CANONICAL_ARTIFACT_TYPES
        )
    except (OSError, ValueError) as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Artifact manifest assembly failed"
        ) from error
    return ArtifactManifest(artifacts=entries, created_at=created_at)


__all__ = ["attach_analytics_report_artifact", "build_artifact_manifest"]


def attach_analytics_report_artifact(
    run_id: str,
    report_json: str,
    *,
    request_id: str,
) -> Mapping[str, object]:
    """Atomically attach one immutable Analytics report to a completed run.

    The attachment never alters the three canonical manifest entries; the
    report is written beside them as an immutable owner reference. Identical
    bytes are idempotent and different bytes fail closed.

    Args:
        run_id: Completed canonical Simulation run identity.
        report_json: Serialized Analytics performance report JSON text.
        request_id: Trace identifier for the attachment operation.

    Returns:
        Immutable attachment projection with reference, checksum, and size.

    Raises:
        SimulationError: ``SIMULATION_RESULT_NOT_FOUND`` when no completed
            result artifact exists for the run, ``ANALYTICS_REPORT_INVALID``
            when the payload is not JSON, or ``ANALYTICS_REPORT_CONFLICT``
            when different bytes were already attached.
    """
    if not run_id or run_id != run_id.strip() or "/" in run_id or "\\" in run_id:
        raise SimulationError("SIM_INVALID_CONFIG", "Run identity is invalid")
    if not request_id:
        raise SimulationError("SIM_INVALID_CONFIG", "Request identity is invalid")
    try:
        json.loads(report_json)
    except (TypeError, ValueError) as error:
        raise SimulationError(
            "ANALYTICS_REPORT_INVALID", "Report payload is not valid JSON"
        ) from error
    payload = report_json.encode("utf-8")
    digest = sha256(payload).hexdigest()
    root = _DEFAULT_ARTIFACT_ROOT.resolve()
    run_root = (root / run_id).resolve()
    if root not in run_root.parents:
        raise SimulationError("SIM_PERSISTENCE_FAILED", "Run path is unsafe")
    if not (run_root / "result.json").exists():
        raise SimulationError(
            "SIMULATION_RESULT_NOT_FOUND", "Completed Simulation run was not found"
        )
    target = run_root / ANALYTICS_REPORT_ARTIFACT_NAME
    if target.exists():
        if target.read_bytes() == payload:
            logger.info(
                "Analytics report artifact already attached to run %s (%s)",
                run_id,
                digest,
            )
            return MappingProxyType(
                {
                    "run_id": run_id,
                    "artifact_ref": f"{run_id}/{ANALYTICS_REPORT_ARTIFACT_NAME}",
                    "sha256": digest,
                    "size_bytes": len(payload),
                    "status": "already_attached",
                }
            )
        raise SimulationError(
            "ANALYTICS_REPORT_CONFLICT",
            "A different Analytics report is already attached to this run",
        )
    try:
        temporary = run_root / f"{ANALYTICS_REPORT_ARTIFACT_NAME}.tmp"
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
    except OSError as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Analytics report attachment failed"
        ) from error
    logger.info("Attached Analytics report artifact to run %s (%s)", run_id, digest)
    return MappingProxyType(
        {
            "run_id": run_id,
            "artifact_ref": f"{run_id}/{ANALYTICS_REPORT_ARTIFACT_NAME}",
            "sha256": digest,
            "size_bytes": len(payload),
            "status": "attached",
        }
    )
