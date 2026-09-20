"""Trading session profiles, weekly schedules, holiday exclusion, and timezones.

Feature:
    FEAT-DATA-SESSIONS

Purpose:
    Provides deterministic trading session evaluation, weekly schedule windows,
    holiday calendar exclusions, and timezone/DST projection matching StrategyQuant X
    session models and ExchangeCalendar.

Invariants:
    * Session evaluation uses the session's configured local timezone.
    * Dates in the holiday exclusion list are excluded regardless of active windows.
    * If multiple session windows exist for a day, any matching window counts as open.
    * Unknown timezone strings raise TimezoneError fail-closed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time
from typing import TYPE_CHECKING, override
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.contracts.data import (
    DATA_PERSISTENCE,
    DATA_SESSIONS,
    DataPersistenceService,
    InvalidSessionWindowError,
    SessionDefinition,
    SessionWindow,
    TimezoneError,
)
from app.contracts.data import (
    SessionService as ISessionService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

# Common financial timezone aliases matching SQX
TZ_ALIASES: dict[str, str] = {
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "GMT": "UTC",
    "UTC": "UTC",
    "EET": "Europe/Athens",
    "EEST": "Europe/Athens",
    "Server GMT+2": "Europe/Athens",
    "Server GMT+3": "Europe/Athens",
    "Tokyo": "Asia/Tokyo",
    "Sydney": "Australia/Sydney",
    "London": "Europe/London",
}

_TIME_PATTERN = re.compile(r"^(\d{2}):(\d{2})(?::(\d{2}))?$")


def _resolve_zoneinfo(tz_name: str) -> ZoneInfo:
    """Retrieve ZoneInfo resolving common financial aliases."""
    mapped = TZ_ALIASES.get(tz_name.strip(), tz_name.strip())
    try:
        return ZoneInfo(mapped)
    except ZoneInfoNotFoundError as exc:
        msg = f"Unknown timezone: {tz_name} (mapped to {mapped})"
        raise TimezoneError(msg) from exc


_MAX_HOURS = 23
_MAX_MINUTES_SECONDS = 59


def _parse_time_str(val: str) -> time:
    """Parse 'HH:MM:SS' or 'HH:MM' string strictly into datetime.time.

    Raises:
        InvalidSessionWindowError: If string is malformed or hours/minutes/seconds
            are out of valid ranges (0-23 for hours, 0-59 for minutes/seconds).
    """
    match = _TIME_PATTERN.match(val.strip())
    if not match:
        msg = f"Malformed session time string '{val}'; expected 'HH:MM' or 'HH:MM:SS'"
        raise InvalidSessionWindowError(msg)
    hours, minutes = int(match.group(1)), int(match.group(2))
    seconds = int(match.group(3)) if match.group(3) is not None else 0
    if (
        hours > _MAX_HOURS
        or minutes > _MAX_MINUTES_SECONDS
        or seconds > _MAX_MINUTES_SECONDS
    ):
        msg = (
            f"Invalid session time values in '{val}': "
            f"hours={hours}, minutes={minutes}, seconds={seconds}"
        )
        raise InvalidSessionWindowError(msg)
    return time(hour=hours, minute=minutes, second=seconds)


@dataclass(slots=True, frozen=True)
class SessionConfig:
    """Configuration for trading session service."""

    default_session_name: str = "24/5 Forex"


class SessionServiceImpl(ISessionService):
    """Concrete implementation of SessionService protocol."""

    def __init__(
        self,
        persistence: DataPersistenceService,
        config: SessionConfig | None = None,
    ) -> None:
        """Initialize session service.

        Args:
            persistence: Persistence service for session storage.
            config: Optional configuration.
        """
        self._persistence = persistence
        self._config = config or SessionConfig()

    @override
    async def get_session(self, name: str) -> SessionDefinition | None:
        """Retrieve session profile by name."""
        return await self._persistence.get_session(name)

    @override
    async def get_default_session(self) -> SessionDefinition:
        """Retrieve the system default trading session profile."""
        sessions = await self._persistence.list_sessions()
        for s in sessions:
            if s.is_default:
                return s
        if sessions:
            return sessions[0]

        # Fallback if unseeded
        return SessionDefinition(
            name=self._config.default_session_name,
            description="Fallback 24/5 Forex default session",
            timezone="UTC",
            windows=[
                SessionWindow(
                    day_of_week=i,
                    open_time="00:00:00",
                    close_time="23:59:59",
                )
                for i in range(5)
            ],
            holidays=[],
            is_default=True,
        )

    @override
    async def save_session(self, session: SessionDefinition) -> SessionDefinition:
        """Persist or update a trading session definition."""
        return await self._persistence.save_session(session)

    @override
    async def list_sessions(self) -> list[SessionDefinition]:
        """List all configured session profiles."""
        return await self._persistence.list_sessions()

    @override
    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert a datetime instant from one timezone to another deterministically."""
        source_tz = _resolve_zoneinfo(from_tz)
        target_tz = _resolve_zoneinfo(to_tz)

        if dt.tzinfo is None:
            localized = dt.replace(tzinfo=source_tz)
        else:
            localized = dt.astimezone(source_tz)

        return localized.astimezone(target_tz)

    @override
    def is_in_session(self, dt: datetime, session: SessionDefinition) -> bool:
        """Determine whether timestamp falls within active session trading hours."""
        session_tz = _resolve_zoneinfo(session.timezone)
        if dt.tzinfo:
            local_dt = dt.astimezone(session_tz)
        else:
            local_dt = dt.replace(tzinfo=session_tz)

        # 1. Holiday Check
        date_str = local_dt.strftime("%Y-%m-%d")
        if date_str in session.holidays:
            return False

        # 2. Window Check
        weekday = local_dt.weekday()  # 0=Monday .. 6=Sunday
        matching_windows = [w for w in session.windows if w.day_of_week == weekday]
        if not matching_windows:
            return False

        cur_time = local_dt.time()
        for w in matching_windows:
            open_t = _parse_time_str(w.open_time)
            close_t = _parse_time_str(w.close_time)
            if open_t <= cur_time <= close_t:
                return True

        return False


SPEC: FeatureSpec = FeatureSpec(
    name="data.sessions",
    provides=frozenset({DATA_SESSIONS}),
    requires=frozenset({DATA_PERSISTENCE}),
    optional=frozenset(),
    description="Trading session schedules, holiday calendars, and timezones.",
)


class SessionFeature:
    """Wire session feature into kernel composition lifecycle."""

    def __init__(self, config: SessionConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional session configuration.
        """
        self._config = config or SessionConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve persistence and provide session service.

        Args:
            context: Lifecycle feature context.
        """
        persistence = context.require(DATA_PERSISTENCE)
        service = SessionServiceImpl(persistence, self._config)
        context.provide(DATA_SESSIONS, service)
        logger.info("data_sessions_feature_started")


def feature() -> SessionFeature:
    """Return an unmounted SessionFeature instance.

    Returns:
        New SessionFeature instance.
    """
    return SessionFeature()


__all__ = [
    "SPEC",
    "TZ_ALIASES",
    "SessionConfig",
    "SessionFeature",
    "SessionServiceImpl",
    "feature",
]
