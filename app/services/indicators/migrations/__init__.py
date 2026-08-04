"""Indicators-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/indicators/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.indicators.migrations.definitions import (
    INDICATOR_MIGRATIONS as INDICATOR_MIGRATIONS,
)
from app.services.indicators.migrations.definitions import (
    INDICATOR_SCHEMA_VERSION as INDICATOR_SCHEMA_VERSION,
)
from app.services.indicators.migrations.definitions import (
    get_indicator_migrations,
)

__all__ = [
    "INDICATOR_MIGRATIONS",
    "INDICATOR_SCHEMA_VERSION",
    "get_indicator_migrations",
]
