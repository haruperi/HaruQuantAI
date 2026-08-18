"""Simulation Workbench HTTP route composition (FEAT-API-27).

Stage: the router is declared and mounted by the P0-T10 composition task
together with its handlers; until then it owns no operations so the
route catalogue is unchanged.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/simulator", tags=["simulator-workbench"])

__all__ = ("router",)
