"""Reports package for the Risk Governance Service.

Provides report builders, validation rules, and export controls.
"""

from __future__ import annotations

from app.services.risk.observability.metrics import RISK_METRICS_REGISTRY
from app.services.risk.reports.builder import (
    PortfolioRiskReport,
    ReportRedactionPolicy,
    RiskDecisionSummary,
    RiskReport,
    RiskReportBuilder,
    RiskReportEvidence,
    RiskReportOptions,
    build_portfolio_risk_snapshot,
    build_risk_decision_summary,
    generate_risk_report,
    redact_risk_report,
)
from app.services.risk.reports.exporter import (
    AuthorizedReportPath,
    ReportWriteReceipt,
    build_report_write_receipt,
    validate_report_export_destination,
    write_risk_report,
)

__all__ = [
    "RISK_METRICS_REGISTRY",
    "AuthorizedReportPath",
    "PortfolioRiskReport",
    "ReportRedactionPolicy",
    "ReportWriteReceipt",
    "RiskDecisionSummary",
    "RiskReport",
    "RiskReportBuilder",
    "RiskReportEvidence",
    "RiskReportOptions",
    "build_portfolio_risk_snapshot",
    "build_report_write_receipt",
    "build_risk_decision_summary",
    "generate_risk_report",
    "redact_risk_report",
    "validate_report_export_destination",
    "write_risk_report",
]
