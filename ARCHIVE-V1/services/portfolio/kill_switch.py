"""Portfolio kill switch with fail-closed live execution controls.

Purpose:
    Portfolio kill switch with fail-closed live execution controls.

Classes:
    PortfolioKillSwitch: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in app/services/portfolio/__init__.py;
    private underscore helpers remain implementation details.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agentic.agents._shared.persistence import utc_stamp, write_json_artifact


class PortfolioKillSwitch:
    """Public class for kill_switch.PortfolioKillSwitch."""

    def __init__(self) -> None:
        """Internal function for kill_switch.__init__."""
        self.state = "healthy"
        self.trigger_reason: str | None = None
        self.triggered_at: str | None = None

    def evaluate(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Public function for kill_switch.evaluate."""
        triggers = [
            name
            for name, active in {
                "critical_audit_failure": snapshot.get("critical_audit_failure"),
                "risk_governor_unavailable": snapshot.get(
                    "risk_governor_available", True
                )
                is False,
                "audit_logging_unavailable": snapshot.get(
                    "audit_logging_available", True
                )
                is False,
                "broker_heartbeat_failed": snapshot.get("broker_heartbeat") == "failed",
                "daily_loss_limit": float(snapshot.get("daily_loss", 0.0))
                >= float(snapshot.get("max_daily_loss", 0.03)),
                "weekly_loss_limit": float(snapshot.get("weekly_loss", 0.0))
                >= float(snapshot.get("max_weekly_loss", 0.06)),
                "account_drawdown_limit": float(snapshot.get("account_drawdown", 0.0))
                >= float(snapshot.get("max_account_drawdown", 0.12)),
                "strategy_drawdown_limit": float(snapshot.get("strategy_drawdown", 0.0))
                >= float(snapshot.get("max_strategy_drawdown", 0.08)),
                "spread_spike": float(snapshot.get("spread", 0.0))
                > float(snapshot.get("max_spread", 2.0)),
                "slippage_spike": float(snapshot.get("slippage", 0.0))
                > float(snapshot.get("max_slippage", 1.0)),
                "repeated_order_failure": int(
                    snapshot.get("repeated_order_failures", 0)
                )
                >= int(snapshot.get("max_repeated_order_failures", 3)),
            }.items()
            if active
        ]
        return (
            self.trigger(";".join(triggers))
            if triggers
            else {
                "state": self.state,
                "triggered": self.state != "healthy",
                "reason": self.trigger_reason,
            }
        )

    def trigger(self, reason: str) -> dict[str, Any]:
        """Public function for kill_switch.trigger."""
        self.state, self.trigger_reason, self.triggered_at = (
            "triggered",
            reason,
            datetime.now(UTC).isoformat(),
        )
        payload = {
            "state": self.state,
            "triggered": True,
            "reason": reason,
            "triggered_at": self.triggered_at,
            "resume_allowed": False,
            "disable_new_orders": True,
            "close_positions_policy": "optional_manual_approval",
            "incident_report": {
                "severity": "critical",
                "trigger": reason,
                "required_action": "manual_review",
            },
        }
        payload["audit_uri"] = write_json_artifact(
            "data/logs/portfolio", f"kill-switch-{utc_stamp()}.json", payload
        )
        return payload

    def resume(self, *, approval_id: str | None = None) -> dict[str, Any]:
        """Public function for kill_switch.resume."""
        if not approval_id:
            return {
                "state": self.state,
                "status": "blocked",
                "reason": "resume_requires_approval",
            }
        self.state, self.trigger_reason, self.triggered_at = "healthy", None, None
        return {"state": self.state, "status": "resumed", "approval_id": approval_id}
