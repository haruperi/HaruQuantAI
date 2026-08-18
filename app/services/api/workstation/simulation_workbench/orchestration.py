"""Simulation Workbench orchestration composition (FEAT-API-27).

Stage: contracts and persistence (P0-T05 to P0-T07) complete; the gateway
composition (completion sink wiring, registry, route handlers) is added by
the P0-T08 task. This module currently owns only the feature's public
composition entry points that later stages build on.
"""

from __future__ import annotations

from app.services.api.workstation.simulation_workbench.migrations import (
    get_simulation_workbench_migration_steps,
)


def build_simulation_workbench_source() -> object:
    """Build the Simulation Workbench composition source bundle.

    Returns:
        Opaque composition source consumed by the application factory.
    """
    return {
        "migration_steps": get_simulation_workbench_migration_steps(),
    }


__all__ = ("build_simulation_workbench_source",)
