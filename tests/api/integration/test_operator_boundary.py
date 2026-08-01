"""Reduced operator HTTP boundary integration evidence."""

from app.services.api import build_api_settings, create_api_app


def test_unsupported_operator_authority_is_absent() -> None:
    """Keep unsupported kill-switch and duplicate readiness routes unregistered."""
    paths = create_api_app(build_api_settings()).openapi()["paths"]
    assert "/api/v1/operator/audit-events" in paths
    assert "/api/v1/operator/events" in paths
    assert "/api/v1/operator/approvals" in paths
    assert "/api/v1/operator/kill-switch" not in paths
    assert "/api/v1/operator/readiness" not in paths
