"""Thread-safe in-memory simulator session store.

Purpose:
    Thread-safe in-memory simulator session store.

Classes:
    SimulatorSessionManager: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in the owning package __init__.py.
    private underscore helpers remain implementation details unless preserved for API compatibility.
"""

from __future__ import annotations

from threading import RLock
from typing import Generic, TypeVar

SessionT = TypeVar("SessionT")


class SimulatorSessionManager(Generic[SessionT]):
    """Own in-process simulator sessions behind a small locked API."""

    def __init__(self) -> None:
        """Internal function for session_manager.__init__."""
        self._sessions: dict[int, SessionT] = {}
        self._lock = RLock()

    def get(self, session_id: int) -> SessionT | None:
        """Public function for session_manager.get."""
        with self._lock:
            return self._sessions.get(int(session_id))

    def put(self, session_id: int, session: SessionT) -> None:
        """Public function for session_manager.put."""
        with self._lock:
            self._sessions[int(session_id)] = session

    def remove(self, session_id: int) -> SessionT | None:
        """Public function for session_manager.remove."""
        with self._lock:
            return self._sessions.pop(int(session_id), None)
