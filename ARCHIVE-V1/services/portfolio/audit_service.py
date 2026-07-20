"""Portfolio audit checks for governed execution and lifecycle evidence.

Purpose:
    Portfolio audit checks for governed execution and lifecycle evidence.

Classes:
    PortfolioAuditService: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in app/services/portfolio/__init__.py;
    private underscore helpers remain implementation details.
"""

from __future__ import annotations

from typing import Any

from app.agentic.agents._shared.persistence import utc_stamp, write_json_artifact


class PortfolioAuditService:
    """Public class for audit_service.PortfolioAuditService."""

    def audit(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Public function for audit_service.audit."""
        findings: list[str] = []
        if not snapshot.get("risk_governor_approval"):
            findings.append("missing_risk_governor_approval")
        if snapshot.get("approval_token_matches_order") is False:
            findings.append("approval_token_order_mismatch")
        if snapshot.get("unauthorized_risk_threshold_changes"):
            findings.append("unauthorized_risk_threshold_change")
        if snapshot.get("lifecycle_stage_skipped"):
            findings.append("lifecycle_stage_skipped")
        if snapshot.get("live_strategy_board_approval") is False:
            findings.append("live_strategy_missing_board_approval")
        for field, reason in {
            "evidence_refs": "missing_evidence_refs",
            "execution_logs": "missing_execution_logs",
            "broker_responses": "missing_broker_responses",
        }.items():
            if not snapshot.get(field):
                findings.append(reason)
        if snapshot.get("hidden_failed_tool_calls"):
            findings.append("hidden_failed_tool_calls")
        critical = bool(findings and snapshot.get("severity", "critical") == "critical")
        report = {
            "status": "failed" if findings else "passed",
            "findings": findings,
            "daily_audit_report": True,
            "critical_audit_failure_disables_live_trading": critical,
        }
        report["audit_ref"] = write_json_artifact(
            "data/logs/portfolio", f"audit-{utc_stamp()}.json", report
        )
        return report
