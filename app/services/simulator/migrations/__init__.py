"""Simulator-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/simulator/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.simulator.migrations.definitions import (
    SIMULATION_MIGRATIONS as SIMULATION_MIGRATIONS,
)

__all__ = ["SIMULATION_MIGRATIONS"]
