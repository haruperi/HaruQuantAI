"""Brokers-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/brokers/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.brokers.migrations.definitions import (
    BROKER_MIGRATIONS as BROKER_MIGRATIONS,
)
from app.services.brokers.migrations.definitions import (
    BROKER_SCHEMA_VERSION as BROKER_SCHEMA_VERSION,
)
from app.services.brokers.migrations.definitions import (
    get_broker_migrations,
)

__all__ = ["BROKER_MIGRATIONS", "BROKER_SCHEMA_VERSION", "get_broker_migrations"]
