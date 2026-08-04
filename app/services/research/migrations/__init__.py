"""Research-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside the domain's
private persistence layer per the canonical migration-definition location
recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.research.migrations.definitions import (
    RESEARCH_MIGRATION_STEPS as RESEARCH_MIGRATION_STEPS,
)
from app.services.research.migrations.definitions import (
    build_research_migration_request,
)

__all__ = ["RESEARCH_MIGRATION_STEPS", "build_research_migration_request"]
