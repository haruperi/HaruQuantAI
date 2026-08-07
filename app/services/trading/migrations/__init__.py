"""Trading-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/trading/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.trading.migrations.definitions import (
    TRADING_SCHEMA_VERSION as TRADING_SCHEMA_VERSION,
)
from app.services.trading.migrations.definitions import (
    get_trading_migrations,
    run_trading_migrations,
)

__all__ = ["TRADING_SCHEMA_VERSION", "get_trading_migrations", "run_trading_migrations"]
