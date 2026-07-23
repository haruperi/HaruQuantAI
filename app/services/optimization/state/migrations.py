"""Optimization-owned additive schema definitions executed by Data."""

from __future__ import annotations

import hashlib

from app.services.data.persistence.contracts import (
    MigrationStep,
)
from app.services.optimization.state.contracts import OPTIMIZATION_SCHEMA_VERSION
from app.utils import logger

_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS optimization_results (
        search_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL,
        reproducibility_hash TEXT NOT NULL,
        result_json TEXT NOT NULL,
        ranked_candidates_json TEXT NOT NULL,
        stored_at TEXT NOT NULL
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS optimization_checkpoints (
        search_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL,
        reproducibility_hash TEXT NOT NULL,
        completed_candidate_position INTEGER NOT NULL,
        checkpoint_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""",
)


def get_optimization_migrations() -> tuple[MigrationStep, ...]:
    """Return ordered additive Optimization schema definitions.

    Returns:
        One immutable Data migration step owning both Optimization tables.
    """
    logger.info("Building Optimization-owned migration definitions")
    material = "\n-- statement --\n".join(_STATEMENTS).encode("utf-8")
    return (
        MigrationStep(
            domain="optimization",
            migration_id="001_optimization_schema_v1",
            checksum=hashlib.sha256(material).hexdigest(),
            statements=_STATEMENTS,
        ),
    )


__all__ = ["OPTIMIZATION_SCHEMA_VERSION", "get_optimization_migrations"]
