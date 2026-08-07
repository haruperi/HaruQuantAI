"""Optimization-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside the domain's
private persistence layer per the canonical migration-definition location
recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.optimization.migrations.definitions import (
    get_optimization_migrations,
    run_optimization_migrations,
)

__all__ = ["get_optimization_migrations", "run_optimization_migrations"]
