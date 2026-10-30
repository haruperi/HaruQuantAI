"""Temporary migration bridge to app.core.trading.blocks.runtime_inputs."""

from __future__ import annotations

import sys

from app.core.trading.blocks import runtime_inputs as _implementation
from app.core.trading.blocks.runtime_inputs import *  # noqa: F403
from app.core.trading.blocks.runtime_inputs import (
    bind_profile_signals,
    bind_runtime_inputs,
    execute_bound_signal,
    resolve_decision_price,
    schedule_calendar_session,
)

__all__ = [
    "bind_profile_signals",
    "bind_runtime_inputs",
    "execute_bound_signal",
    "resolve_decision_price",
    "schedule_calendar_session",
]

sys.modules[__name__] = _implementation
