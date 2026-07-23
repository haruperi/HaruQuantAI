"""Heartbeat observation for internal feeds.

Heartbeat is an attribute of live feed state, not a separate subsystem: it is touched
when an event arrives and read when status is derived. Phase 8 extracted those two
touch points into named helpers so the intent is legible at the call site, rather than
inventing the ``update_heartbeat`` / ``check_timeout`` public surface the README
proposed — neither had a caller, and one would have duplicated the ingestion path.

A missed heartbeat is evidence, not an action. ``feeds/status.py`` reports expiry;
nothing here mutates a feed in response.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.utils import logger

if TYPE_CHECKING:
    from datetime import datetime, timedelta

    from app.services.data.realtime_feeds.state import ActiveFeed


def touch_heartbeat(active: ActiveFeed, received_at: datetime) -> None:
    """Record that a feed produced an observable event.

    Args:
        active: Live feed state to update.
        received_at: Aware UTC time the event was received.
    """
    logger.debug("Touching heartbeat for feed %s", active.config.feed_id)
    active.heartbeat_at = received_at


def heartbeat_expired(
    heartbeat_at: datetime | None,
    now: datetime,
    threshold: timedelta,
) -> bool:
    """Report whether a feed's last heartbeat is older than its threshold.

    A feed that has never produced an event has no heartbeat, which is reported as
    expired rather than fresh: absence of evidence is not evidence of health.

    Args:
        heartbeat_at: Time of the last observed event, or ``None``.
        now: Aware UTC evaluation time, supplied by the caller.
        threshold: Configured heartbeat timeout.

    Returns:
        ``True`` when the heartbeat is missing or older than the threshold.
    """
    if heartbeat_at is None:
        return True
    return (now - heartbeat_at) > threshold


__all__: list[str] = []
