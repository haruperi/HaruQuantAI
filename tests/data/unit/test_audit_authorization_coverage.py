"""Unit tests for audit/authorization.py to reach 100% coverage."""

from unittest.mock import MagicMock

from app.services.data.audit.authorization import may_query_audit


def test_may_query_audit() -> None:
    """Test may_query_audit returns True when permission is present."""
    mock_ctx = MagicMock()
    mock_ctx.permissions = {"data.audit.read", "other.perm"}
    assert may_query_audit(mock_ctx) is True

    mock_ctx.permissions = {"other.perm"}
    assert may_query_audit(mock_ctx) is False
