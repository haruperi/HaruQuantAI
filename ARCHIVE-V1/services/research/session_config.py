"""Shared Edge Lab session windows and helpers.

Purpose:
    Shared Edge Lab session windows and helpers.

Classes:
    None.

Functions:
    active_sessions_for_hour: Run active sessions for hour processing.
    session_label_for_hour: Run session label for hour processing.
    session_hours_payload: Run session hours payload processing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd
from app.services.utils.logger import logger

EDGE_SESSION_WINDOWS: dict[str, tuple[int, ...]] = {
    "sydney": tuple(range(7)),
    "tokyo": tuple(range(2, 9)),
    "london": tuple(range(10, 17)),
    "ny": tuple(range(15, 22)),
}

EDGE_SESSION_ORDER: tuple[str, ...] = (
    "sydney",
    "tokyo",
    "sydney_tokyo",
    "london",
    "london_ny",
    "ny",
    "gap",
)


def active_sessions_for_hour(
    hour: int,
    session_windows: Mapping[str, Sequence[int]] | None = None,
) -> list[str]:
    """Run active sessions for hour processing."""
    windows = session_windows or EDGE_SESSION_WINDOWS
    active: list[str] = []
    for session_name, hours in windows.items():
        if int(hour) in hours:
            active.append(str(session_name))
    return active


def session_label_for_hour(
    hour: int,
    session_windows: Mapping[str, Sequence[int]] | None = None,
) -> str:
    """Run session label for hour processing."""
    active = active_sessions_for_hour(hour, session_windows=session_windows)
    return "_".join(active) if active else "gap"


def session_hours_payload(
    session_windows: Mapping[str, Sequence[int]] | None = None,
) -> dict[str, list[int]]:
    """Run session hours payload processing."""
    windows = session_windows or EDGE_SESSION_WINDOWS
    return {str(name): [int(hour) for hour in hours] for name, hours in windows.items()}


def tag_sessions(
    df: pd.DataFrame,
    asia_hours: Sequence[int] | None = None,
    london_hours: Sequence[int] | None = None,
    ny_hours: Sequence[int] | None = None,
    off_hours: Sequence[int] | None = None,
) -> pd.DataFrame:
    """Tag each bar with its trading session label."""
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have a DatetimeIndex for session tagging")

    out = df.copy()
    session_windows: Mapping[str, Sequence[int]] | None = None
    if any(
        hours is not None for hours in (asia_hours, london_hours, ny_hours, off_hours)
    ):
        session_windows = {
            "asia": tuple(asia_hours or ()),
            "london": tuple(london_hours or ()),
            "ny": tuple(ny_hours or ()),
            "off": tuple(off_hours or ()),
        }

    out["session"] = [
        session_label_for_hour(int(hour), session_windows=session_windows)
        for hour in out.index.hour
    ]
    logger.debug(f"Session distribution: {out['session'].value_counts().to_dict()}")
    return out
