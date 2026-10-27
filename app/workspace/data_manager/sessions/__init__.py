"""Data Manager trading sessions catalog service package.

Description:
    Provides trading session schedules, regular trading hours, and holiday
    calendars for the Data Manager workspace, reading catalog entries from
    the authoritative SQLite database (datamgr_sessions table).
"""

from __future__ import annotations

from ._cli import (
    register_session_commands,
    run_session_command,
)
from ._helpers import (
    MAX_HOLIDAYS,
    MAX_SHIFT_MINUTES,
    MAX_WINDOWS,
    SessionsCLI,
    SessionWindow,
    TradingHoliday,
    TradingSession,
    format_session_table,
    persistence,
)
from .feature import Sessions
from .http import register_session_routes

__all__ = [
    "MAX_HOLIDAYS",
    "MAX_SHIFT_MINUTES",
    "MAX_WINDOWS",
    "SessionWindow",
    "Sessions",
    "SessionsCLI",
    "TradingHoliday",
    "TradingSession",
    "format_session_table",
    "persistence",
    "register_session_commands",
    "register_session_routes",
    "run_session_command",
]
