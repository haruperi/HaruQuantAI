"""Simulation Workbench gateway feature (FEAT-API-27).

Owns the durable principal-scoped Simulation run catalogue, typed
live-session projections, and batch coordination behind
``/api/v1/simulator``. The package root is the sole public import
boundary; composition happens in P0-T08.
"""

from app.services.api.workstation.simulation_workbench.migrations import (
    get_simulation_workbench_migration_steps,
)
from app.services.api.workstation.simulation_workbench.schemas import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_VIEWPORT_BEFORE,
    MAX_BATCH_CONCURRENCY,
    MAX_BATCH_ITEMS,
    MAX_PAGE_SIZE,
    MAX_SEEK_TICKS,
    MAX_STEP_TICKS,
    MAX_TAG_LENGTH,
    MAX_TAGS,
    MAX_TRADE_PAGE_SIZE,
    MAX_VIEWPORT_BEFORE,
    VIEWPORT_AFTER,
    RunCatalogueEntry,
)

__all__ = (
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_VIEWPORT_BEFORE",
    "MAX_BATCH_CONCURRENCY",
    "MAX_BATCH_ITEMS",
    "MAX_PAGE_SIZE",
    "MAX_SEEK_TICKS",
    "MAX_STEP_TICKS",
    "MAX_TAGS",
    "MAX_TAG_LENGTH",
    "MAX_TRADE_PAGE_SIZE",
    "MAX_VIEWPORT_BEFORE",
    "VIEWPORT_AFTER",
    "RunCatalogueEntry",
    "get_simulation_workbench_migration_steps",
)
