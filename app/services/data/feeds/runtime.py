"""Internal feed runtime management: start, ingest, overflow, and reconnect."""

from __future__ import annotations

import collections
import hashlib
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.services.data.contracts import FeedEventResult, FeedStatus
from app.services.data.contracts.errors import DataError
from app.services.data.storage.database import execute_transaction
from app.utils import Clock, logger, utc_now

if TYPE_CHECKING:
    from app.services.data.contracts import FeedConfig, RawFeedEvent


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


def start_internal_feed(
    config: FeedConfig,
    *,
    clock: Clock | None = None,
) -> FeedStatus:
    """Start one internal feed for a declared live-capable staging/production source.

    Args:
        config: Configuration details of the feed.
        clock: Optional injected UTC clock.

    Returns:
        The initial FeedStatus.
    """
    logger.info("Starting internal feed %s", config.feed_id)

    # 1. Resolve source descriptor
    from app.services.data.sources.registry import get_source_descriptor

    descriptor = get_source_descriptor(config.source_id)

    # 2. Validate readiness and capability
    if descriptor.readiness not in ("staging", "production"):
        raise DataError(
            "POLICY_BLOCKED",
            safe_details={"source_id": config.source_id},
            request_id=config.request_id,
        )

    if config.source_capability not in descriptor.capabilities:
        raise DataError(
            "POLICY_BLOCKED",
            safe_details={"source_id": config.source_id},
            request_id=config.request_id,
        )

    # Ensure database is bootstrapped

    # Check if feed already registered
    if config.feed_id in _ACTIVE_FEEDS:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"feed_id": config.feed_id},
            request_id=config.request_id,
        )

    # Check database for existing feed
    from app.services.data.contracts import StatementPlan, TransactionRequest

    query_sql = (
        "SELECT feed_id, source_id, symbol, data_kind, timeframe, "
        "source_capability, buffer_capacity, overflow_policy, "
        "heartbeat_timeout_seconds, state, heartbeat_at, last_event_at, "
        "buffer_depth, dropped_count, gap_count, reconnect_count, "
        "breaker_state, breaker_opened_at, drift_ms, last_error "
        "FROM data_feeds WHERE feed_id = ?"
    )
    res = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(query_sql,),
                parameter_sets=((config.feed_id,),),
                max_rows=1,
            ),
            request_id=config.request_id,
        )
    )
    if res.rows:
        active = _restore_active_feed(config, res.rows[0], utc_now(clock))
        _ACTIVE_FEEDS[config.feed_id] = active
        _persist_feed_status(active, config.request_id)
        return FeedStatus(
            feed_id=config.feed_id,
            source_id=config.source_id,
            symbol=config.symbol,
            data_kind=config.data_kind,
            state=active.state,  # type: ignore[arg-type]
            heartbeat_at=active.heartbeat_at,
            last_event_at=active.last_event_at,
            buffer_depth=0,
            buffer_capacity=config.buffer_capacity,
            dropped_count=active.dropped_count,
            gap_count=active.gap_count,
            reconnect_count=active.reconnect_count,
            breaker_state=active.breaker_state,  # type: ignore[arg-type]
            drift_ms=active.drift_ms,
            last_error=active.last_error,
            request_id=config.request_id,
        )

    now = utc_now(clock)
    now_str = now.isoformat().replace("+00:00", "Z")

    import json

    policy = config.reconnect_policy
    reconnect_json = json.dumps(
        {
            "max_retries": policy.max_retries,
            "initial_backoff_seconds": policy.initial_backoff_seconds,
            "max_backoff_seconds": policy.max_backoff_seconds,
            "jitter_seconds": policy.jitter_seconds,
            "circuit_cooldown_seconds": policy.circuit_cooldown_seconds,
        }
    )

    # Persist initial state
    insert_sql = (
        "INSERT INTO data_feeds ("
        "  feed_id, source_id, symbol, data_kind, timeframe, source_capability, "
        "  buffer_capacity, overflow_policy, heartbeat_timeout_seconds, "
        "  reconnect_policy_json, state, heartbeat_at, last_event_at, "
        "  buffer_depth, dropped_count, gap_count, reconnect_count, "
        "  breaker_state, drift_ms, last_error, request_id, created_at, "
        "  updated_at"
        ") VALUES ("
        "  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 0, 0, 0, 0, 'closed', "
        "  NULL, NULL, ?, ?, ?"
        ")"
    )
    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(insert_sql,),
                parameter_sets=(
                    (
                        config.feed_id,
                        config.source_id,
                        config.symbol,
                        config.data_kind,
                        config.timeframe,
                        config.source_capability,
                        config.buffer_capacity,
                        config.overflow_policy,
                        config.heartbeat_timeout_seconds,
                        reconnect_json,
                        "starting",
                        config.request_id,
                        now_str,
                        now_str,
                    ),
                ),
                max_rows=1,
            ),
            request_id=config.request_id,
        )
    )

    # Register in-memory
    active = ActiveFeed(config, now)
    _ACTIVE_FEEDS[config.feed_id] = active

    return FeedStatus(
        feed_id=config.feed_id,
        source_id=config.source_id,
        symbol=config.symbol,
        data_kind=config.data_kind,
        state="starting",
        heartbeat_at=None,
        last_event_at=None,
        buffer_depth=0,
        buffer_capacity=config.buffer_capacity,
        dropped_count=0,
        gap_count=0,
        reconnect_count=0,
        breaker_state="closed",
        drift_ms=None,
        last_error=None,
        request_id=config.request_id,
    )


def ingest_feed_event(feed_id: str, event: RawFeedEvent) -> FeedEventResult:
    """Normalize events, update heartbeat, check overflow, and record gaps/drops.

    Args:
        feed_id: Bounded feed ID.
        event: Raw feed event.

    Returns:
        The FeedEventResult outcome.
    """
    logger.info("Ingesting event sequence %d for feed %s", event.sequence, feed_id)

    # 1. Fetch active feed
    if feed_id not in _ACTIVE_FEEDS:
        raise DataError(
            "DATA_NOT_FOUND",
            safe_details={"feed_id": feed_id},
            request_id=event.request_id,
        )

    if event.feed_id != feed_id:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "feed_id"},
            request_id=event.request_id,
        )

    active = _ACTIVE_FEEDS[feed_id]

    # 2. Check if feed is in a terminated/failed/blocked state
    if active.state in ("failed", "blocked"):
        raise DataError(
            "POLICY_BLOCKED",
            safe_details={"feed_id": feed_id, "state": active.state},
            request_id=event.request_id,
        )

    # Transition from starting to running on first event
    if active.state == "starting":
        active.state = "running"

    # 3. Heartbeat check
    # Check if elapsed time since last heartbeat exceeds timeout
    now = event.received_at
    if active.heartbeat_at is not None:
        elapsed = (event.received_at - active.heartbeat_at).total_seconds()
        if elapsed > active.config.heartbeat_timeout_seconds:
            active.state = "failed"
            active.last_error = "FEED_HEARTBEAT_TIMEOUT"
            active.updated_at = now
            _persist_feed_status(active, event.request_id)
            raise DataError(
                "FEED_HEARTBEAT_TIMEOUT",
                safe_details={"elapsed_seconds": elapsed},
                request_id=event.request_id,
            )

    # Update heartbeat & last event times
    active.heartbeat_at = event.received_at
    active.last_event_at = event.event_timestamp
    active.drift_ms = int(
        (event.received_at - event.event_timestamp).total_seconds() * 1000
    )

    # 4. Enforce overflow
    buffer_depth = len(active.buffer)
    if buffer_depth >= active.config.buffer_capacity:
        return _handle_overflow(active, event, now)

    # Simply append
    active.buffer.append(event)
    active.updated_at = now
    _persist_feed_status(active, event.request_id)

    return FeedEventResult(
        feed_id=feed_id,
        sequence=event.sequence,
        accepted=True,
        buffer_depth=len(active.buffer),
        gap_recorded=False,
        dropped_count=0,
        request_id=event.request_id,
    )


def _handle_overflow(
    active: ActiveFeed, event: RawFeedEvent, now: datetime
) -> FeedEventResult:
    """Handle buffer overflow state according to config policy.

    Args:
        active: Active feed runtime state tracker.
        event: Raw feed event.
        now: Current timestamp.

    Returns:
        The FeedEventResult if accepted/rejected.
    """
    logger.debug("Running DATA function: _handle_overflow")
    policy = active.config.overflow_policy
    feed_id = active.config.feed_id

    if policy == "halt":
        active.state = "failed"
        active.last_error = "BUFFER_OVERFLOW"
        active.updated_at = now
        _persist_feed_status(active, event.request_id)
        raise DataError(
            "BUFFER_OVERFLOW",
            safe_details={"overflow_policy": "halt"},
            request_id=event.request_id,
        )

    if policy == "backpressure":
        raise DataError(
            "BUFFER_OVERFLOW",
            safe_details={"overflow_policy": "backpressure"},
            request_id=event.request_id,
        )

    # ``drop_and_reconcile`` rejects the new event, records a gap, and requires
    # the caller to reconcile before governed consumption resumes.
    active.dropped_count += 1
    active.gap_count += 1
    active.state = "blocked"
    active.last_error = "DATA_DROPPED"
    active.updated_at = now
    _persist_feed_status(active, event.request_id)
    return FeedEventResult(
        feed_id=feed_id,
        sequence=event.sequence,
        accepted=False,
        buffer_depth=len(active.buffer),
        gap_recorded=True,
        dropped_count=1,
        request_id=event.request_id,
    )


def _reconnect_delay_seconds(active: ActiveFeed) -> int:
    """Return deterministic bounded exponential backoff plus bounded jitter."""
    logger.debug("Calculating deterministic feed reconnect delay")
    policy = active.config.reconnect_policy
    exponent = max(0, active.reconnect_count)
    base = min(
        policy.max_backoff_seconds,
        policy.initial_backoff_seconds * (2**exponent),
    )
    if policy.jitter_seconds == 0:
        return int(base)
    material = f"{active.config.feed_id}:{active.reconnect_count}".encode()
    jitter = int.from_bytes(hashlib.sha256(material).digest()[:8], "big") % (
        policy.jitter_seconds + 1
    )
    return int(min(policy.max_backoff_seconds, base + jitter))


def reconnect_feed(
    feed_id: str,
    request_id: str,
    *,
    reconnect: Callable[[], bool],
    wait: Callable[[int], None],
    clock: Clock | None = None,
) -> None:
    """Attempt reconnecting the feed using reconnect policy parameters.

    Args:
        feed_id: Bounded feed ID.
        request_id: Operation request ID.
        reconnect: Injected single reconnect attempt.
        wait: Injected delay boundary receiving deterministic seconds.
        clock: Optional injected UTC clock.

    Raises:
        DataError: If connection circuit-breaker is open.
    """
    logger.info("Triggering reconnect attempt for feed %s", feed_id)
    if feed_id not in _ACTIVE_FEEDS:
        raise DataError(
            "DATA_NOT_FOUND",
            safe_details={"feed_id": feed_id},
            request_id=request_id,
        )

    active = _ACTIVE_FEEDS[feed_id]

    now = utc_now(clock)
    if active.breaker_state == "open":
        opened_at = active.breaker_opened_at
        cooldown = timedelta(
            seconds=active.config.reconnect_policy.circuit_cooldown_seconds
        )
        if opened_at is None or now - opened_at < cooldown:
            raise DataError(
                "CIRCUIT_BREAKER_OPEN",
                safe_details={"feed_id": feed_id},
                request_id=request_id,
            )
        active.breaker_state = "half_open"

    delay_seconds = _reconnect_delay_seconds(active)
    wait(delay_seconds)
    active.reconnect_count += 1

    if active.reconnect_count > active.config.reconnect_policy.max_retries:
        active.breaker_state = "open"
        active.breaker_opened_at = now
        active.state = "blocked"
        active.last_error = "RECONNECT_EXHAUSTED"
        active.updated_at = now
        _persist_feed_status(active, request_id)
        raise DataError(
            "POLICY_BLOCKED",
            safe_details={"feed_id": feed_id},
            request_id=request_id,
        )
    try:
        connected = reconnect()
    except Exception:  # noqa: BLE001 - injected provider boundary.
        logger.error("Injected feed reconnect failed")
        connected = False
    if not connected:
        active.state = "failed"
        active.last_error = "SOURCE_UNAVAILABLE"
        active.updated_at = now
        _persist_feed_status(active, request_id)
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "feed_reconnect"},
            request_id=request_id,
        )
    active.state = "running"
    active.breaker_state = "closed"
    active.breaker_opened_at = None
    active.last_error = None
    active.updated_at = now
    _persist_feed_status(active, request_id)


def reconcile_feed_gap(
    feed_id: str,
    request_id: str,
    *,
    reconcile: Callable[[], bool],
    clock: Clock | None = None,
) -> None:
    """Unblock a dropped feed only after injected reconciliation succeeds."""
    logger.info("Reconciling recorded gap for feed %s", feed_id)
    active = _ACTIVE_FEEDS.get(feed_id)
    if active is None:
        raise DataError(
            "DATA_NOT_FOUND",
            safe_details={"feed_id": feed_id},
            request_id=request_id,
        )
    if active.last_error != "DATA_DROPPED" or active.gap_count <= 0:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"operation": "feed_reconciliation"},
            request_id=request_id,
        )
    try:
        reconciled = reconcile()
    except Exception:  # noqa: BLE001 - injected provider boundary.
        logger.error("Injected feed reconciliation failed")
        reconciled = False
    if not reconciled:
        raise DataError(
            "STATE_RECOVERY_FAILED",
            safe_details={"operation": "feed_reconciliation"},
            request_id=request_id,
        )
    active.state = "running"
    active.last_error = None
    active.updated_at = utc_now(clock)
    _persist_feed_status(active, request_id)


def _persist_feed_status(active: ActiveFeed, request_id: str) -> None:
    """Save/update current feed status to the SQLite database."""
    logger.debug("Running DATA function: _persist_feed_status")
    from app.services.data.contracts import StatementPlan, TransactionRequest

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
    "ingest_feed_event",
    "reconcile_feed_gap",
    "reconnect_feed",
    "start_internal_feed",
]
