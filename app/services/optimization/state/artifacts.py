"""Traversal-safe deterministic Optimization artifact locations."""

from __future__ import annotations

import re
from pathlib import Path

from app.services.optimization.errors import OptimizationError
from app.utils import logger

_IDENTIFIER = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def build_optimization_artifact_path(
    *,
    artifact_root: Path,
    kind: str,
    search_id: str,
    reproducibility_hash: str,
) -> Path:
    """Build a deterministic JSON path below an approved artifact root.

    Args:
        artifact_root: Approved Optimization artifact root.
        kind: Either ``results`` or ``checkpoints``.
        search_id: Canonical search identity.
        reproducibility_hash: Lowercase SHA-256 evidence identity.

    Returns:
        Normalized artifact path below the approved root.

    Raises:
        OptimizationError: If identifiers or containment are invalid.
    """
    logger.info("Building traversal-safe Optimization artifact path")
    if (
        kind not in {"results", "checkpoints"}
        or _IDENTIFIER.fullmatch(search_id) is None
        or _SHA256.fullmatch(reproducibility_hash) is None
    ):
        raise OptimizationError("OPT_INVALID_REQUEST", "INVALID_ARTIFACT_IDENTITY")
    root = artifact_root.resolve()
    candidate = (root / kind / search_id / f"{reproducibility_hash}.json").resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise OptimizationError("OPT_INVALID_REQUEST", "ARTIFACT_PATH_ESCAPE") from exc
    return candidate


__all__ = ["build_optimization_artifact_path"]
