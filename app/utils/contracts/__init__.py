"""Public shared-contract exports."""

from app.utils.contracts.audit import AuditEvent, create_audit_event
from app.utils.contracts.auth import AuthContext, create_auth_context


def get_auth_context_type() -> type[object]:
    """Return the internal canonical authentication-context runtime type.

    Returns:
        The authentication-context class for receiver-side runtime validation.
    """
    return AuthContext


def get_audit_event_type() -> type[object]:
    """Return the internal canonical audit-event runtime type.

    Returns:
        The audit-event class for receiver-side runtime schema validation.
    """
    return AuditEvent


__all__ = [
    "create_audit_event",
    "create_auth_context",
    "get_audit_event_type",
    "get_auth_context_type",
]
