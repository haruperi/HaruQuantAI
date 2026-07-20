"""Deterministic order router for guarded live execution.

Classes and functions:
    OrderRouter: Class. Provides OrderRouter behavior for execution workflows.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agentic.agents._shared.persistence import utc_stamp, write_json_artifact


class OrderRouter:
    """Represent OrderRouter behavior in execution service workflows."""

    component_name = "order_router"

    def route_order(
        self,
        *,
        order: dict[str, Any],
        approval_token: dict[str, Any] | None,
        live_config: dict[str, Any],
        broker_status: dict[str, Any],
        kill_switch_status: str,
    ) -> dict[str, Any]:
        """Perform the route_order execution service operation."""
        reasons: list[str] = []
        if not approval_token:
            reasons.append("missing_risk_approval_token")
        elif approval_token.get("decision") not in {
            "approved",
            "approved_with_reduced_size",
        }:
            reasons.append("risk_approval_not_approved")
        elif approval_token.get("expires_at"):
            try:
                if datetime.fromisoformat(
                    str(approval_token["expires_at"])
                ) < datetime.now(UTC):
                    reasons.append("approval_token_expired")
            except ValueError:
                reasons.append("approval_token_invalid_expiry")
            approved_volume = float(
                approval_token.get(
                    "approved_volume", approval_token.get("approved_size", 0.0)
                )
                or 0.0
            )
            requested_volume = float(
                order.get(
                    "requested_volume",
                    order.get("requested_size", order.get("size", 0.0)),
                )
                or 0.0
            )
            if requested_volume > approved_volume:
                reasons.append("mismatched_order_size")
            for field in ("symbol", "side"):
                if (
                    approval_token.get(field)
                    and order.get(field)
                    and str(approval_token[field]) != str(order[field])
                ):
                    reasons.append(f"mismatched_{field}")
        if not live_config.get("global_live_mode", False):
            reasons.append("live_mode_disabled")
        strategy_config = live_config.get("strategies", {}).get(
            order.get("strategy_id"), {}
        )
        if strategy_config.get("state") not in {
            "micro_live",
            "limited_live",
            "normal_live",
            "live",
        }:
            reasons.append("strategy_not_live")
        if kill_switch_status != "healthy":
            reasons.append("kill_switch_not_healthy")
        if broker_status.get("heartbeat") != "healthy":
            reasons.append("broker_heartbeat_failed")
        if order.get("side") not in {"buy", "sell"}:
            reasons.append("mismatched_side")
        result = {
            "status": "rejected" if reasons else "accepted",
            "reasons": reasons,
            "order": order,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        result["audit_uri"] = write_json_artifact(
            "data/logs/execution", f"order-router-{utc_stamp()}.json", result
        )
        return result
