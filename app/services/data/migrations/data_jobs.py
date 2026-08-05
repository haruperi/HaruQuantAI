"""Immutable Data Jobs environment migration."""

from __future__ import annotations

import hashlib

from app.services.data.persistence.contracts import MigrationStep

_STATEMENTS = ("ALTER TABLE data_update_jobs ADD COLUMN environment TEXT",)

DATA_JOBS_ENVIRONMENT_MIGRATION_STEP = MigrationStep(
    domain="data",
    migration_id="008_data_jobs_environment",
    checksum=hashlib.sha256(
        "\n-- statement --\n".join(_STATEMENTS).encode("utf-8")
    ).hexdigest(),
    statements=_STATEMENTS,
)

__all__ = ["DATA_JOBS_ENVIRONMENT_MIGRATION_STEP"]
