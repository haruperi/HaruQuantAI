"""Navigation metadata for Home workspace."""

from app.core.lib.errors import JSONValue
from app.core.lib.responses import StandardResponse


class HomeNavigation:
    """Provider for Home workspace navigation metadata."""

    def __init__(self) -> None:
        """Initialize HomeNavigation."""

    def get(self, *, request_id: str) -> StandardResponse[dict[str, JSONValue]]:
        """Return Home workspace navigation metadata.

        Args:
            request_id: Non-empty request identifier.

        Returns:
            StandardResponse containing navigation metadata.
        """
        payload: dict[str, JSONValue] = {
            "app_code": "HOME",
            "title": "Getting started",
            "order": 0,
            "section": 0,
            "icon": "home",
        }
        return StandardResponse(
            request_id=request_id,
            data=payload,
            revision=None,
        )
