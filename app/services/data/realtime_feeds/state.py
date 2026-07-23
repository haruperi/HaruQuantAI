"""The single registry of live internal feed state.

``feeds/runtime.py`` split three ways in ``CAP-DATA-026`` Phase 8, and ``_ACTIVE_FEEDS``
had to end up in exactly one of them. Letting each module declare its own would have
produced two registries: ingestion writing to one while status read the other, so a feed
receiving events would report as idle. That failure is silent — nothing raises, the
numbers are simply wrong — which is the same shape as the duplicated settings
``ContextVar`` Phase 3 uncovered.

Hosting the registry below every module that touches it makes a second copy impossible
by construction. ``tests/data/unit/test_feed_state_single_owner.py`` asserts that only
this module declares it.

Nothing outside ``feeds`` imports this module.
"""

from __future__ import annotations

import collections
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING

from app.services.data.contracts import DataError
from app.services.data.persistence.transactions import execute_transaction
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.realtime_feeds.contracts import (
        FeedConfig,
        RawFeedEvent,
    )


class ActiveFeed:
    """In-memory active feed runtime state tracker."""

    def __init__(self, config: FeedConfig, created_at: datetime) -> None:
        """Execute one private DATA operation."""
        logger.debug("Running DATA function: __init__")
        self.config = config
        self.buffer: collections.deque[RawFeedEvent] = collections.deque(
            maxlen=config.buffer_capacity
        )
        self.state: str = "starting"
        self.heartbeat_at: datetime | None = None
        self.last_event_at: datetime | None = None
        self.dropped_count: int = 0
        self.gap_count: int = 0
        self.reconnect_count: int = 0
        self.breaker_state: str = "closed"
        self.breaker_opened_at: datetime | None = None
        self.drift_ms: int | None = None
        self.last_error: str | None = None
        self.created_at = created_at
        self.updated_at = created_at


# In-memory registry of active feeds
_ACTIVE_FEEDS: dict[str, ActiveFeed] = {}


def _restore_active_feed(
    config: FeedConfig,
    row: Mapping[str, None | bool | int | float | str],
    now: datetime,
) -> ActiveFeed:
    """Restore persisted feed controls without inventing volatile buffer contents."""
    logger.info("Restoring persisted controls for feed %s", config.feed_id)
    expected = {
        "source_id": config.source_id,
        "symbol": config.symbol,
        "data_kind": config.data_kind,
        "timeframe": config.timeframe,
        "source_capability": config.source_capability,
        "buffer_capacity": config.buffer_capacity,
        "overflow_policy": config.overflow_policy,
        "heartbeat_timeout_seconds": config.heartbeat_timeout_seconds,
    }
    if any(row[key] != value for key, value in expected.items()):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"operation": "feed_restore"},
            request_id=config.request_id,
        )
    active = ActiveFeed(config, now)
    active.state = str(row["state"])
    active.heartbeat_at = (
        datetime.fromisoformat(str(row["heartbeat_at"]))
        if row["heartbeat_at"] is not None
        else None
    )
    active.last_event_at = (
        datetime.fromisoformat(str(row["last_event_at"]))
        if row["last_event_at"] is not None
        else None
    )
    active.dropped_count = int(str(row["dropped_count"]))
    active.gap_count = int(str(row["gap_count"]))
    active.reconnect_count = int(str(row["reconnect_count"]))
    active.breaker_state = str(row["breaker_state"])
    active.breaker_opened_at = (
        datetime.fromisoformat(str(row["breaker_opened_at"]))
        if row["breaker_opened_at"] is not None
        else None
    )
    active.drift_ms = int(str(row["drift_ms"])) if row["drift_ms"] is not None else None
    active.last_error = (
        str(row["last_error"]) if row["last_error"] is not None else None
    )
    if int(str(row["buffer_depth"])) > 0:
        active.state = "blocked"
        active.last_error = "STATE_RECOVERY_FAILED"
    active.updated_at = now
    return active


def _clear_active_feeds() -> None:
    """Clear in-memory active feeds dictionary. (Used primarily for test isolation)."""
    logger.info("Clearing all in-memory active feeds")
    _ACTIVE_FEEDS.clear()


def _persist_feed_status(active: ActiveFeed, request_id: str) -> None:
    """Save/update current feed status to the SQLite database."""
    logger.debug("Running DATA function: _persist_feed_status")
    from app.services.data.persistence.contracts import (
        StatementPlan,
        TransactionRequest,
    )

    update_sql = (
        "UPDATE data_feeds SET "
        "  state = ?, "
        "  heartbeat_at = ?, "
        "  last_event_at = ?, "
        "  buffer_depth = ?, "
        "  dropped_count = ?, "
        "  gap_count = ?, "
        "  reconnect_count = ?, "
        "  breaker_state = ?, "
        "  breaker_opened_at = ?, "
        "  drift_ms = ?, "
        "  last_error = ?, "
        "  updated_at = ? "
        "WHERE feed_id = ?"
    )

    hb_str = (
        active.heartbeat_at.isoformat().replace("+00:00", "Z")
        if active.heartbeat_at
        else None
    )
    evt_str = (
        active.last_event_at.isoformat().replace("+00:00", "Z")
        if active.last_event_at
        else None
    )
    upd_str = active.updated_at.isoformat().replace("+00:00", "Z")
    breaker_opened_str = (
        active.breaker_opened_at.isoformat().replace("+00:00", "Z")
        if active.breaker_opened_at is not None
        else None
    )

    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(update_sql,),
                parameter_sets=(
                    (
                        active.state,
                        hb_str,
                        evt_str,
                        len(active.buffer),
                        active.dropped_count,
                        active.gap_count,
                        active.reconnect_count,
                        active.breaker_state,
                        breaker_opened_str,
                        active.drift_ms,
                        active.last_error,
                        upd_str,
                        active.config.feed_id,
                    ),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )


__all__ = [
    "ActiveFeed",
]
