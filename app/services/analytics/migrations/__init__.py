"""Analytics-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/analytics/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.analytics.migrations.definitions import (
    ANALYTICS_MIGRATIONS as ANALYTICS_MIGRATIONS,
)
from app.services.analytics.migrations.definitions import (
    ANALYTICS_SCHEMA_VERSION as ANALYTICS_SCHEMA_VERSION,
)
from app.services.analytics.migrations.definitions import (
    get_analytics_migrations,
)

__all__ = [
    "ANALYTICS_MIGRATIONS",
    "ANALYTICS_SCHEMA_VERSION",
    "get_analytics_migrations",
]
