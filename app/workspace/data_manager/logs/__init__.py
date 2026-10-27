"""Data Manager activity logs package.

Description:
    Provides structured activity history, active task tracking, and
    event-bus progress delivery for the Data Manager workspace.
"""

from __future__ import annotations

import httpx

from app.host.settings import SettingsManager

from ._cli import (
    register_log_commands,
    run_log_command,
)
from ._helpers import (
    run_logged_task,
)
from .feature import Logs
from .http import register_log_routes

__all__ = [
    "Logs",
    "SettingsManager",
    "httpx",
    "register_log_commands",
    "register_log_routes",
    "run_log_command",
    "run_logged_task",
]
