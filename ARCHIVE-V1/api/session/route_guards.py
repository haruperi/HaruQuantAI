"""Shared auth/session guards for simulator routes.

Purpose:
    Shared auth/session guards for simulator routes.

Classes:
    None.

Functions:
    get_owned_session_record: Public function defined by this module.
    get_running_session: Public function defined by this module.

Notes:
    External-facing exports are collected in the owning package __init__.py.
    private underscore helpers remain implementation details unless preserved for API compatibility.
"""

from __future__ import annotations

from typing import Any

from .session_coordinator import SessionCoordinator
from .session_runtime import SimulatorSession


def get_owned_session_record(
    *,
    coordinator: SessionCoordinator[SimulatorSession],
    session_id: int,
    user_id: int,
) -> dict[str, Any]:
    """Public function for route_guards.get_owned_session_record."""
    return coordinator.get_owned_metadata(session_id, user_id).as_record()


def get_running_session(
    *,
    coordinator: SessionCoordinator[SimulatorSession],
    session_id: int,
) -> SimulatorSession:
    """Public function for route_guards.get_running_session."""
    return coordinator.require_runtime(session_id)
