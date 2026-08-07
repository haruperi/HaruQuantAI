"""Optimization-owned additive schema definitions executed by Data.

Conformed to the authoritative schema model in
``app/services/optimization/README.md``. The step has never been applied to
a database, so the definition is edited in place rather than extended by a
follow-on migration; see ``FR-OPT-070`` and ``FR-OPT-071``.

The model adopts this domain's shape rather than the reverse. A search is
identified by ``search_id`` and its ranked candidates are stored as a payload;
per-trial normalisation is target-only work and is not implied by this schema.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_domain_migrations,
)
from app.utils import get_logger

logger = get_logger(__name__)

_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS optimization_results (
        search_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL,
        reproducibility_hash TEXT NOT NULL,
        result_json TEXT NOT NULL,
        ranked_candidates_json TEXT NOT NULL,
        stored_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""",
    (
        "CREATE INDEX IF NOT EXISTS idx_optimization_results_repro "
        "ON optimization_results(reproducibility_hash)"
    ),
    """CREATE TABLE IF NOT EXISTS optimization_checkpoints (
        search_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL,
        reproducibility_hash TEXT NOT NULL,
        completed_candidate_position INTEGER NOT NULL,
        checkpoint_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL
    ) STRICT""",
)


def get_optimization_migrations() -> tuple[Any, ...]:
    """Return ordered additive Optimization schema definitions.

    Returns:
        One immutable Data migration step owning both Optimization tables.
    """
    logger.info("Building Optimization-owned migration definitions")
    material = "\n-- statement --\n".join(_STATEMENTS).encode("utf-8")
    return (
        build_migration_step(
            domain="optimization",
            migration_id="001_optimization_schema_v1",
            checksum=hashlib.sha256(material).hexdigest(),
            statements=_STATEMENTS,
        ),
    )


def run_optimization_migrations(request_id: str) -> object:
    """Apply the complete Optimization manifest through Data.

    Args:
        request_id: Canonical migration trace identifier.

    Returns:
        Data-owned standard migration response.
    """
    logger.info("Running the complete Optimization migration manifest")
    request = build_migration_request(
        domain="optimization",
        steps=get_optimization_migrations(),
        request_id=request_id,
        complete_manifest=True,
    )
    return run_domain_migrations(request)


__all__ = ["get_optimization_migrations", "run_optimization_migrations"]
