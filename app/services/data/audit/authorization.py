"""Audit-query authorization boundary."""

from typing import Any

type AuthContext = Any


def may_query_audit(context: AuthContext) -> bool:
    """Return whether the authenticated principal has audit-read permission."""
    return "data.audit.read" in context.permissions


__all__ = ["may_query_audit"]
