"""Identity-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, and remain local to Identity.
"""

from app.services.api.identity.migrations.definitions import (
    get_identity_migration_steps,
)

__all__ = ("get_identity_migration_steps",)
