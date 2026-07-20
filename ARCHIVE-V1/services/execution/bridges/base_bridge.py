"""Base interface for broker execution bridges.

Classes and functions:
    BaseExecutionBridge: Class. Provides BaseExecutionBridge behavior for execution workflows.
"""

from datetime import UTC, datetime
from typing import Any


class BaseExecutionBridge:
    """Represent BaseExecutionBridge behavior in execution service workflows."""

    bridge_name = "base"

    def __init__(self, *, live_enabled: bool = False) -> None:
        self.live_enabled = live_enabled
        self.connected = True
        self.last_heartbeat = datetime.now(UTC).isoformat()

    def heartbeat(self) -> dict[str, Any]:
        """Perform the heartbeat execution service operation."""
        self.last_heartbeat = datetime.now(UTC).isoformat()
        return {
            "bridge": self.bridge_name,
            "status": "healthy" if self.connected else "disconnected",
            "last_heartbeat": self.last_heartbeat,
        }

    def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """Perform the place_order execution service operation."""
        if not self.live_enabled:
            return {
                "bridge": self.bridge_name,
                "status": "blocked",
                "reason": "live_execution_disabled",
                "order": order,
            }
        return {"bridge": self.bridge_name, "status": "accepted", "order": order}
