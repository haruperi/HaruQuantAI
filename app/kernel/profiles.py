"""Runtime execution profile definitions for the microkernel.

Traces to: P4-T01, Gate G4
"""

from __future__ import annotations

from enum import StrEnum


class RuntimeProfile(StrEnum):
    """Execution profiles dictating provider readiness requirements."""

    RESEARCH = "research"
    SIMULATION = "simulation"
    DEMO = "demo"
    LIVE = "live"


__all__ = ("RuntimeProfile",)
