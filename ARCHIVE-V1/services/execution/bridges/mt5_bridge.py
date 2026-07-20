"""MT5 bridge preparation with live mutation methods fail-closed by default.

Classes and functions:
    MT5Bridge: Class. Provides MT5Bridge behavior for execution workflows.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agentic.agents._shared.persistence import utc_stamp, write_json_artifact


class MT5Bridge:
    """Represent MT5Bridge behavior in execution service workflows."""

    def __init__(self, *, live_enabled: bool = False) -> None:
        self.live_enabled = live_enabled
        self.connected = True
        self.last_heartbeat = datetime.now(UTC).isoformat()

    def reconnect(self) -> bool:
        """Perform the reconnect execution service operation."""
        self.connected = True
        self.heartbeat()
        return self.connected

    def heartbeat(self) -> dict[str, Any]:
        """Perform the heartbeat execution service operation."""
        self.last_heartbeat = datetime.now(UTC).isoformat()
        return {
            "status": "healthy" if self.connected else "disconnected",
            "last_heartbeat": self.last_heartbeat,
        }

    def get_account_info(self) -> dict[str, Any]:
        """Perform the get_account_info execution service operation."""
        return {
            "account_id": "paper-mt5",
            "equity": 100000.0,
            "margin_free": 100000.0,
            "live_enabled": self.live_enabled,
        }

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Perform the get_symbol_info execution service operation."""
        return {
            "symbol": symbol,
            "pip_size": 0.0001,
            "tick_size": 0.00001,
            "trade_allowed": self.live_enabled,
        }

    def get_latest_tick(self, symbol: str) -> dict[str, Any]:
        """Perform the get_latest_tick execution service operation."""
        return {
            "symbol": symbol,
            "bid": 1.1,
            "ask": 1.1001,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_open_positions(self) -> list[dict[str, Any]]:
        """Perform the get_open_positions execution service operation."""
        return []

    def get_pending_orders(self) -> list[dict[str, Any]]:
        """Perform the get_pending_orders execution service operation."""
        return []

    def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """Perform the place_order execution service operation."""
        if not self.live_enabled:
            return self._blocked("place_order", order, "live_execution_disabled")
        return self._audit("place_order", {"status": "accepted", "order": order})

    def close_position(self, position_id: str) -> dict[str, Any]:
        """Perform the close_position execution service operation."""
        if not self.live_enabled:
            return self._blocked(
                "close_position",
                {"position_id": position_id},
                "live_execution_disabled",
            )
        return self._audit(
            "close_position", {"status": "accepted", "position_id": position_id}
        )

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """Perform the cancel_order execution service operation."""
        if not self.live_enabled:
            return self._blocked(
                "cancel_order", {"order_id": order_id}, "live_execution_disabled"
            )
        return self._audit("cancel_order", {"status": "accepted", "order_id": order_id})

    def _blocked(
        self, action: str, payload: dict[str, Any], reason: str
    ) -> dict[str, Any]:
        return self._audit(
            action, {"status": "blocked", "reason": reason, "payload": payload}
        )

    def _audit(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload = {
            **payload,
            "bridge": "mt5",
            "action": action,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        payload["audit_uri"] = write_json_artifact(
            "data/logs/execution", f"mt5-{action}-{utc_stamp()}.json", payload
        )
        return payload


__all__ = ["MT5Bridge"]
