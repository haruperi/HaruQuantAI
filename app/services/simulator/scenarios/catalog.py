"""Built-in emergency and abnormal-operation scenario templates."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

_EMERGENCY = (
    "flash_crash",
    "api_failure",
    "drawdown_breach",
    "margin_survival",
    "recovery_failure",
)
_ABNORMAL = (
    "bad_tick",
    "feed_disagreement",
    "market_halt",
    "market_gap",
    "margin_change",
    "order_rejection",
    "cancel_fill_race",
    "clock_drift",
    "process_failure",
)


def get_scenario_templates() -> Mapping[str, tuple[str, ...]]:
    """Return immutable supported emergency and abnormal template identities."""
    return MappingProxyType({"emergency": _EMERGENCY, "abnormal": _ABNORMAL})


__all__ = ["get_scenario_templates"]
