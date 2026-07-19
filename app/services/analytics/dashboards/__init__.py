"""Public API for bounded Analytics dashboard projection."""

from app.services.analytics.dashboards.payloads import build_dashboard_payload
from app.services.analytics.dashboards.truncation import truncate_series

__all__ = ["build_dashboard_payload", "truncate_series"]
