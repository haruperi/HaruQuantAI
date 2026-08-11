"""Unit tests for Data audit authorization boundary."""

from types import SimpleNamespace

from app.services.data.evidence.audit_authorization import may_query_audit


def test_may_query_audit_returns_true_when_permission_present() -> None:
    """Verify may_query_audit returns True when permission is present."""
    auth = SimpleNamespace(permissions=("data.audit.read",))
    assert may_query_audit(auth) is True  # type: ignore[arg-type]


def test_may_query_audit_returns_false_when_permission_absent() -> None:
    """Verify may_query_audit returns False when permission is absent."""
    auth = SimpleNamespace(permissions=("data.read",))
    assert may_query_audit(auth) is False  # type: ignore[arg-type]
