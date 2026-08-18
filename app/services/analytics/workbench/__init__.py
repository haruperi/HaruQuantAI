"""Analytics workbench feature (FEAT-ANLT-11).

Owns the finite owner-produced workbench projection over one validated
performance report and one canonical Simulation result. All calculations
stay inside Analytics; nothing is persisted.
"""

from app.services.analytics.workbench.projections import (
    WORKBENCH_MAX_POINTS,
    build_workbench_payload,
)

__all__ = ("WORKBENCH_MAX_POINTS", "build_workbench_payload")
