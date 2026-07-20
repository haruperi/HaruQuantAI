"""Replay and what-if risk analysis workflows."""

from __future__ import annotations

__all__ = [
    "CockpitStatePayload",
    "HypotheticalOrderAction",
    "ReplayClock",
    "ReplayEngine",
    "ReplayFrame",
    "ReplayRun",
    "TimelinePoint",
    "TimelineReconstructor",
    "WhatIfComparison",
    "WhatIfEngine",
    "apply_hypothetical_actions",
    "build_cockpit_state",
]

_EXPORT_MODULES = {
    "CockpitStatePayload": "cockpit_state",
    "HypotheticalOrderAction": "hypothetical_orders",
    "ReplayClock": "clock",
    "ReplayEngine": "replay_engine",
    "ReplayFrame": "models",
    "ReplayRun": "models",
    "TimelinePoint": "timeline",
    "TimelineReconstructor": "timeline",
    "WhatIfComparison": "models",
    "WhatIfEngine": "what_if_engine",
    "apply_hypothetical_actions": "hypothetical_orders",
    "build_cockpit_state": "cockpit_state",
}


def __getattr__(name: str):
    """Load replay symbols lazily to avoid circular imports."""
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value
