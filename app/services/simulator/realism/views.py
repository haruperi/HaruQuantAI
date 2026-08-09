"""No-leakage player and venue execution projections."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from types import MappingProxyType


def project_execution_views(
    events: Sequence[Mapping[str, object]], *, as_of: datetime
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    """Separate venue-effective events from player-perceived events.

    Args:
        events: Events carrying aware ``venue_at`` and ``perceived_at`` values.
        as_of: Aware projection timestamp.

    Returns:
        Immutable venue and player projections.

    Raises:
        ValueError: If timing evidence is absent or invalid.
        TypeError: If event timing fields are not datetimes.
    """
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("projection timestamp must be timezone-aware")
    venue: list[Mapping[str, object]] = []
    player: list[Mapping[str, object]] = []
    for event in events:
        venue_at = event.get("venue_at")
        perceived_at = event.get("perceived_at")
        if not isinstance(venue_at, datetime) or not isinstance(perceived_at, datetime):
            raise TypeError("execution view event timing is invalid")
        detached = MappingProxyType(dict(event))
        if venue_at <= as_of:
            venue.append(detached)
        if perceived_at <= as_of:
            player.append(detached)
    return MappingProxyType({"venue": tuple(venue), "player": tuple(player)})


__all__ = ["project_execution_views"]
