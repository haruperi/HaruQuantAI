"""Portfolio performance reporting service.

Purpose:
    Portfolio performance reporting service.

Classes:
    ReportingService: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in app/services/portfolio/__init__.py;
    private underscore helpers remain implementation details.
"""

from typing import Any

from app.agentic.agents._shared.persistence import utc_stamp, write_json_artifact
from app.agentic.agents.portfolio.shared.contracts import PerformanceReport


class ReportingService:
    """Public class for reporting_service.ReportingService."""

    def generate(self, *, report_type: str, data: dict[str, Any]) -> PerformanceReport:
        """Public function for reporting_service.generate."""
        missing = [
            key
            for key in ["portfolio_pnl", "drawdown", "trade_count"]
            if key not in data
        ]
        status = (
            "incomplete"
            if missing or data.get("audit_gaps") or data.get("execution_logs_missing")
            else "complete"
        )
        decisions = list(data.get("decision_required", []))
        if data.get("critical_audit_findings"):
            decisions.append("critical_audit_or_risk_findings")
        report = PerformanceReport(
            report_type=report_type,
            status=status,
            portfolio_pnl=float(data.get("portfolio_pnl", 0.0)),
            drawdown=float(data.get("drawdown", 0.0)),
            trade_count=int(data.get("trade_count", 0)),
            strategy_health=data.get("strategy_health", {}),
            decision_required=decisions,
            evidence_refs=data.get("evidence_refs", []),
        )
        report.audit_ref = write_json_artifact(
            "app/agentic/audit/reports/portfolio",
            f"{report_type}-report-{utc_stamp()}.json",
            report.model_dump() if hasattr(report, "model_dump") else report.dict(),
        )
        return report
