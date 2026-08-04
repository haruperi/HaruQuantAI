"""Data-owned immutable schema definitions.

Migrations are schema evolution, not CRUD. Data's migration *runner* — the
ledger, checksum comparison, write-lock acquisition, and step application —
remains in ``app/services/data/persistence/`` under the shared-infrastructure
exemption recorded in ``AGENTS.md`` §1. This package holds Data's own schema
*definitions* only.

**This module re-exports definitions only, never the runtime-store runner.**
``app/services/data/persistence/migrations.py`` imports from this package, so
initialising it must not reach back into the runner. ``migrations.runtime_stores``
imports ``run_domain_migrations``; re-exporting it here would make importing the
runner initialise this package, which would import the runtime-store module,
which would import the half-initialised runner. Import
``app.services.data.migrations.runtime_stores`` directly instead.
"""

from app.services.data.migrations.core import (
    DATA_MIGRATION_STEPS as DATA_MIGRATION_STEPS,
)
from app.services.data.migrations.research_sources import (
    RESEARCH_PROVIDER_MIGRATION_STEP as RESEARCH_PROVIDER_MIGRATION_STEP,
)
from app.services.data.migrations.research_sources import (
    RESEARCH_SOURCE_MIGRATION_STEP as RESEARCH_SOURCE_MIGRATION_STEP,
)

__all__ = [
    "DATA_MIGRATION_STEPS",
    "RESEARCH_PROVIDER_MIGRATION_STEP",
    "RESEARCH_SOURCE_MIGRATION_STEP",
]
