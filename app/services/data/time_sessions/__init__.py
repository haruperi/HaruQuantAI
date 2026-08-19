"""Focused timeframes, UTC validation, market schedules, and gap classification."""

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.data.time_sessions.contracts import (
        ActiveMarketSessions,
        ActiveMarketSessionsRequest,
        ExchangeSessionRequest,
        MarketHours,
        MarketHoursRequest,
        MarketSchedule,
        NamedSessionDefinition,
        ScheduleRequest,
        SessionWindow,
        TradingSession,
        WeeklyHoliday,
        WeeklyScheduleDefinition,
    )
    from app.services.data.time_sessions.exchange_calendar import get_exchange_sessions
    from app.services.data.time_sessions.gaps import GapType, classify_gap
    from app.services.data.time_sessions.market_hours import apply_venue_halt
    from app.services.data.time_sessions.named_sessions import (
        FOREX_NAMED_SESSIONS,
        get_active_market_sessions,
    )
    from app.services.data.time_sessions.schedule import (
        MarketCalendar,
        get_current_schedule,
        get_market_hours,
        get_trading_sessions,
    )
    from app.services.data.time_sessions.timeframes import (
        TIMEFRAME_MANIFEST,
        TimeframeSpec,
        get_timeframe_spec,
        validate_resample_target,
    )
    from app.services.data.time_sessions.utc import require_utc
    from app.services.data.time_sessions.weekly_schedule import WeeklyScheduleProvider

# Public export name to the module and attribute that owns it. Resolved on
# first access so importing this boundary never loads every feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "ActiveMarketSessions": (
        "app.services.data.time_sessions.contracts",
        "ActiveMarketSessions",
    ),
    "ActiveMarketSessionsRequest": (
        "app.services.data.time_sessions.contracts",
        "ActiveMarketSessionsRequest",
    ),
    "ExchangeSessionRequest": (
        "app.services.data.time_sessions.contracts",
        "ExchangeSessionRequest",
    ),
    "FOREX_NAMED_SESSIONS": (
        "app.services.data.time_sessions.named_sessions",
        "FOREX_NAMED_SESSIONS",
    ),
    "GapType": ("app.services.data.time_sessions.gaps", "GapType"),
    "MarketCalendar": ("app.services.data.time_sessions.schedule", "MarketCalendar"),
    "MarketHours": ("app.services.data.time_sessions.contracts", "MarketHours"),
    "MarketHoursRequest": (
        "app.services.data.time_sessions.contracts",
        "MarketHoursRequest",
    ),
    "MarketSchedule": ("app.services.data.time_sessions.contracts", "MarketSchedule"),
    "NamedSessionDefinition": (
        "app.services.data.time_sessions.contracts",
        "NamedSessionDefinition",
    ),
    "ScheduleRequest": ("app.services.data.time_sessions.contracts", "ScheduleRequest"),
    "SessionWindow": ("app.services.data.time_sessions.contracts", "SessionWindow"),
    "TIMEFRAME_MANIFEST": (
        "app.services.data.time_sessions.timeframes",
        "TIMEFRAME_MANIFEST",
    ),
    "TimeframeSpec": ("app.services.data.time_sessions.timeframes", "TimeframeSpec"),
    "TradingSession": ("app.services.data.time_sessions.contracts", "TradingSession"),
    "WeeklyHoliday": ("app.services.data.time_sessions.contracts", "WeeklyHoliday"),
    "WeeklyScheduleDefinition": (
        "app.services.data.time_sessions.contracts",
        "WeeklyScheduleDefinition",
    ),
    "WeeklyScheduleProvider": (
        "app.services.data.time_sessions.weekly_schedule",
        "WeeklyScheduleProvider",
    ),
    "apply_venue_halt": (
        "app.services.data.time_sessions.market_hours",
        "apply_venue_halt",
    ),
    "classify_gap": ("app.services.data.time_sessions.gaps", "classify_gap"),
    "get_active_market_sessions": (
        "app.services.data.time_sessions.named_sessions",
        "get_active_market_sessions",
    ),
    "get_current_schedule": (
        "app.services.data.time_sessions.schedule",
        "get_current_schedule",
    ),
    "get_exchange_sessions": (
        "app.services.data.time_sessions.exchange_calendar",
        "get_exchange_sessions",
    ),
    "get_market_hours": (
        "app.services.data.time_sessions.schedule",
        "get_market_hours",
    ),
    "get_timeframe_spec": (
        "app.services.data.time_sessions.timeframes",
        "get_timeframe_spec",
    ),
    "get_trading_sessions": (
        "app.services.data.time_sessions.schedule",
        "get_trading_sessions",
    ),
    "require_utc": ("app.services.data.time_sessions.utc", "require_utc"),
    "validate_resample_target": (
        "app.services.data.time_sessions.timeframes",
        "validate_resample_target",
    ),
}


def __getattr__(name: str) -> object:
    """Resolve one public export on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


__all__ = [
    "FOREX_NAMED_SESSIONS",
    "TIMEFRAME_MANIFEST",
    "ActiveMarketSessions",
    "ActiveMarketSessionsRequest",
    "ExchangeSessionRequest",
    "GapType",
    "MarketCalendar",
    "MarketHours",
    "MarketHoursRequest",
    "MarketSchedule",
    "NamedSessionDefinition",
    "ScheduleRequest",
    "SessionWindow",
    "TimeframeSpec",
    "TradingSession",
    "WeeklyHoliday",
    "WeeklyScheduleDefinition",
    "WeeklyScheduleProvider",
    "apply_venue_halt",
    "classify_gap",
    "get_active_market_sessions",
    "get_current_schedule",
    "get_exchange_sessions",
    "get_market_hours",
    "get_timeframe_spec",
    "get_trading_sessions",
    "require_utc",
    "validate_resample_target",
]
