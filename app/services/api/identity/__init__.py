"""Public UI/API authorization dependencies."""

from app.services.api.identity.authorization import (
    require_auth_context,
    require_human_permission,
)

__all__ = ("require_auth_context", "require_human_permission")
