"""Reports package for the Risk Governance Service.

Provides report builders, validation rules, and export controls.
"""

from __future__ import annotations

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
from app.services.risk.observability.metrics import RISK_METRICS_REGISTRY

__all__ = [
    "PortfolioRiskReport",
    "RiskDecisionSummary",
    "RiskReport",
    "RiskReportEvidence",
    "RiskReportOptions",
    "RiskReportBuilder",
    "generate_risk_report",
    "redact_risk_report",
    "ReportRedactionPolicy",
    "build_portfolio_risk_snapshot",
    "build_risk_decision_summary",
    "AuthorizedReportPath",
    "ReportWriteReceipt",
    "validate_report_export_destination",
    "write_risk_report",
    "build_report_write_receipt",
    "RISK_METRICS_REGISTRY",
]
