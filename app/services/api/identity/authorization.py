"""Authenticated principal and permission enforcement."""

from typing import Any

from fastapi import HTTPException, status

from app.utils import get_logger

type AuthContext = Any

logger = get_logger(__name__)


def require_auth_context() -> AuthContext:
    """Fail closed until composition injects a validated authentication context.

    Raises:
        HTTPException: Always when no authentication provider is configured.
    """
    logger.warning("Rejecting request without configured authentication")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="AUTHENTICATION_REQUIRED",
    )


def require_human_permission(auth: AuthContext, permission: str) -> None:
    """Require one authenticated human principal and exact permission.

    Args:
        auth: Validated shared authentication context.
        permission: Exact receiver permission.

    Raises:
        HTTPException: If the principal is not a user or lacks permission.
    """
    logger.debug("Authorizing authenticated API request")
    if auth.principal_type != "USER" or permission not in auth.permissions:
        logger.warning("Rejecting unauthorized API request")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AUTHORIZATION_DENIED",
        )


__all__ = ("require_auth_context", "require_human_permission")
