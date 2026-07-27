"""Timezone-aware canonical session resolution and tagging for Research."""

from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

import pandas as pd

from app.services.research.contracts import ResearchWarning
from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.research.contracts import SessionConfig

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


_MAX_HOUR_OF_DAY = 23


def _validate_hour(hour: int) -> int:
    """Validate one 0-23 clock hour.

    Args:
        hour: Candidate hour value.

    Returns:
        The validated hour.

    Raises:
        ValidationError: If the hour is not a 0-23 integer.
    """
    logger.debug("Validating Research session hour")
    if not isinstance(hour, int) or isinstance(hour, bool) or hour < 0:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_HOUR_OF_DAY")
    if hour > _MAX_HOUR_OF_DAY:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_HOUR_OF_DAY")
    return hour


def _session_active_at_hour(start: time, end: time, hour: int) -> bool:
    """Report whether one window covers the given hour.

    Windows where ``start >= end`` wrap across midnight.

    Args:
        start: Window start.
        end: Window end.
        hour: 0-23 clock hour.

    Returns:
        Whether the hour is inside the session window.
    """
    start_hour = start.hour
    end_hour = end.hour
    # Cross-midnight window (e.g. 22 -> 1) wraps around.
    if start_hour >= end_hour:
        return hour >= start_hour or hour < end_hour
    return start_hour <= hour < end_hour


def active_sessions_for_hour(hour: int, *, config: SessionConfig) -> tuple[str, ...]:
    """Return every configured session active for a timezone-aware hour.

    Args:
        hour: 0-23 clock hour in the configured timezone.
        config: Canonical session windows and precedence.

    Returns:
        Active session names in documented overlap-precedence order.

    Raises:
        ValidationError: If the hour or session policy is invalid.
    """
    logger.info("Resolving active Research sessions for hour")
    checked = _validate_hour(hour)
    active: list[str] = []
    for name in config.overlap_precedence:
        window = config.windows.get(name)
        if window is None:
            raise ValidationError("RES_CONFIGURATION_INVALID", "MISSING_SESSION_WINDOW")
        start, end = window
        if _session_active_at_hour(start, end, checked):
            active.append(name)
    return tuple(active)


def session_label_for_hour(hour: int, *, config: SessionConfig) -> str:
    """Return the deterministic primary session label for one hour.

    Overlapping sessions resolve to the highest-precedence active name;
    hours with no active session resolve to ``unmatched``.

    Args:
        hour: 0-23 clock hour in the configured timezone.
        config: Canonical session windows and precedence.

    Returns:
        The primary session name, or ``unmatched``.

    Raises:
        ValidationError: If the hour or session policy is invalid.
    """
    logger.debug("Selecting Research primary session label")
    active = active_sessions_for_hour(hour, config=config)
    return active[0] if active else "unmatched"


def session_hours_payload(*, config: SessionConfig) -> Mapping[str, JSONValue]:
    """Return a machine-readable payload describing the session policy.

    Args:
        config: Canonical session windows and precedence.

    Returns:
        Versioned payload of timezone, windows, order, and overlaps.

    Raises:
        ValidationError: If the session policy is invalid.
    """
    logger.debug("Building Research session-hours payload")
    overlaps: list[JSONValue] = []
    names = list(config.windows.keys())
    for left_index in range(len(names)):
        for right_index in range(left_index + 1, len(names)):
            left_name, right_name = names[left_index], names[right_index]
            left_start, left_end = config.windows[left_name]
            right_start, right_end = config.windows[right_name]
            for hour in range(24):
                if _session_active_at_hour(
                    left_start, left_end, hour
                ) and _session_active_at_hour(right_start, right_end, hour):
                    overlaps.append(f"{left_name}+{right_name}")
                    break
    return {
        "schema_version": "v1",
        "timezone": config.timezone,
        "windows": {
            name: [f"{start.hour:02d}:00", f"{end.hour:02d}:00"]
            for name, (start, end) in config.windows.items()
        },
        "overlap_precedence": [str(name) for name in config.overlap_precedence],
        "overlaps": overlaps,
    }


def tag_sessions(
    data: pd.DataFrame, *, config: SessionConfig
) -> tuple[pd.DataFrame, tuple[ResearchWarning, ...]]:
    """Add canonical session labels to a copied timezone-aware frame.

    The input is never mutated; rows keep their original order. Naive
    timestamps and unmatched hours record warnings without raising.

    Args:
        data: Frame with a timezone-aware DatetimeIndex.
        config: Canonical session windows and precedence.

    Returns:
        A copied frame with a ``session`` column and structured warnings.

    Raises:
        ValidationError: If the index is not a DatetimeIndex or is naive.
    """
    logger.info("Tagging Research sessions on frame")
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValidationError("RES_INPUT_INVALID", "DATETIME_INDEX_REQUIRED")
    if data.index.tz is None:
        raise ValidationError("RES_INPUT_INVALID", "NAIVE_INDEX_REJECTED")
    labels: list[str] = []
    warnings: list[ResearchWarning] = []
    unmatched = 0
    for timestamp in data.index:
        hour = timestamp.hour
        label = session_label_for_hour(hour, config=config)
        if label == "unmatched":
            unmatched += 1
        labels.append(label)
    if unmatched:
        warnings.append(
            ResearchWarning(
                "UNMATCHED_SESSION_HOURS",
                "Some rows did not match any configured session",
                "warning",
                "session",
                {"unmatched_count": unmatched},
            )
        )
    tagged = data.copy()
    tagged["session"] = labels
    return tagged, tuple(warnings)


__all__ = (
    "active_sessions_for_hour",
    "session_hours_payload",
    "session_label_for_hour",
    "tag_sessions",
)
