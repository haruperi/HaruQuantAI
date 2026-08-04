"""Risk-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/risk/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.risk.migrations.definitions import (
    _RISK_MIGRATION_STEPS as _RISK_MIGRATION_STEPS,
)
from app.services.risk.migrations.definitions import (
    RISK_SCHEMA_VERSION as RISK_SCHEMA_VERSION,
)

__all__: list[str] = []
