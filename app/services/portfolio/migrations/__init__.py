"""Portfolio-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/portfolio/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.portfolio.migrations.definitions import (
    PORTFOLIO_MIGRATIONS as PORTFOLIO_MIGRATIONS,
)
from app.services.portfolio.migrations.definitions import (
    get_portfolio_migrations,
)
from app.services.portfolio.migrations.runner import run_portfolio_migrations

__all__ = [
    "PORTFOLIO_MIGRATIONS",
    "get_portfolio_migrations",
    "run_portfolio_migrations",
]
