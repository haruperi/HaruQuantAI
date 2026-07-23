"""Approved Strategy runtime, timing, and lifecycle enumerations."""

from __future__ import annotations

from enum import StrEnum


class StrategyEnvironment(StrEnum):
    """Approved Strategy execution environments."""

    RESEARCH = "RESEARCH"
    SIMULATION = "SIMULATION"
    PAPER = "PAPER"
    LIVE = "LIVE"


class StrategyTimingPolicy(StrEnum):
    """Supported evidence timing policies."""

    BAR_OPEN_PREVIOUS_CLOSE = "BAR_OPEN_PREVIOUS_CLOSE"
    EVENT_DRIVEN = "EVENT_DRIVEN"


class StrategyLifecycleStatus(StrEnum):
    """Immutable version lifecycle states."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"
    REVOKED = "REVOKED"
