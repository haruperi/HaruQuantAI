"""Public focused Risk reporting API."""

from app.services.risk.reporting.reports import generate_risk_report

__all__ = ["generate_risk_report"]
