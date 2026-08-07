"""Simulator-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/services/simulator/persistence/`` per the canonical migration-definition
location recorded in ``docs/ARCHITECTURE.md``.
"""

from app.services.simulator.migrations.definitions import (
    SIMULATION_MIGRATIONS as SIMULATION_MIGRATIONS,
)
from app.services.simulator.migrations.definitions import (
    run_simulator_migrations as run_simulator_migrations,
)

__all__ = ["SIMULATION_MIGRATIONS", "run_simulator_migrations"]
