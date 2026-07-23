"""Audit-query authorization boundary."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.utils import AuthContext


def may_query_audit(context: AuthContext) -> bool:
    """Return whether the authenticated principal has audit-read permission."""
    return "data.audit.read" in context.permissions


__all__ = ["may_query_audit"]
