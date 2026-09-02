"""Feature lifecycle mount implementation for Sessions and Calendars."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.catalogue.capabilities import DEFINE_SESSIONS_CAPABILITY
from app.services.catalogue.session_calendar.config import SessionCalendarConfig
from app.services.catalogue.session_calendar.manifest import SPEC
from app.services.catalogue.session_calendar.session_calendar import (
    SessionCalendarService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class SessionCalendarFeature:
    """Composable feature package providing Sessions and Calendars capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: SessionCalendarService | None = None

    @property
    def service(self) -> SessionCalendarService | None:
        """Return the underlying session calendar service instance.

        Returns:
            The session calendar service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the session calendar capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If config database_path is not a valid string or path.
        """
        cfg = SessionCalendarConfig()
        if isinstance(config, dict):
            db_path = config.get("database_path")
            if db_path is not None and not isinstance(db_path, str):
                msg = "database_path must be a string if provided"
                raise TypeError(msg)
            cfg = SessionCalendarConfig(
                database_path=db_path,
                auto_migrate=config.get("auto_migrate", True),
            )
        elif isinstance(config, SessionCalendarConfig):
            cfg = config

        self._service = SessionCalendarService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(DEFINE_SESSIONS_CAPABILITY, self._service)
        context.register_callback(self._service.close)


def feature() -> SessionCalendarFeature:
    """Factory function for discovery via entry points.

    Returns:
        New SessionCalendarFeature instance.
    """
    return SessionCalendarFeature()
