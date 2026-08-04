"""UI/API-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/api/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.api.migrations.definitions import (
    get_api_migration_steps,
    run_api_migrations,
)

__all__ = ["get_api_migration_steps", "run_api_migrations"]
