"""Safe checksum manifest assembly for completed Simulation artifacts."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from app.services.simulator.errors import SimulationError
from app.services.simulator.reporting.contracts import (
    CANONICAL_ARTIFACT_TYPES,
    ArtifactEntry,
    ArtifactManifest,
)
from app.utils import logger

_MEDIA_TYPES = {
    "journal.jsonl": "application/x-ndjson",
    "result.json": "application/json",
    "report.md": "text/markdown",
}


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


__all__ = ["build_artifact_manifest"]
