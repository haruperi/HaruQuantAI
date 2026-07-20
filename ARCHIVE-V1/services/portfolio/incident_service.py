"""Portfolio incident reporting service.

Purpose:
    Portfolio incident reporting service.

Classes:
    IncidentService: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in app/services/portfolio/__init__.py;
    private underscore helpers remain implementation details.
"""

from typing import Any

from app.agentic.agents._shared.persistence import utc_stamp, write_json_artifact
from app.agentic.agents.portfolio.shared.contracts import IncidentReport


class IncidentService:
    """Public class for incident_service.IncidentService."""

    def create_incident(self, **kwargs: Any) -> IncidentReport:
        """Public function for incident_service.create_incident."""
        report = IncidentReport(**kwargs)
        report.audit_ref = write_json_artifact(
            "data/logs/portfolio",
            f"incident-{utc_stamp()}.json",
            report.model_dump() if hasattr(report, "model_dump") else report.dict(),
        )
        return report
