"""Expose immutable authentication-context and audit-event contracts.

The feature package validates shared evidence shapes without authenticating a
principal, authorizing an operation, or persisting an audit event.
"""

from app.utils.contracts.audit import AuditEvent
from app.utils.contracts.auth import AuthContext

__all__ = ("AuditEvent", "AuthContext")
