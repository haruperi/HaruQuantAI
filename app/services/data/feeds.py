"""Real-time feed observability: bounded buffers, heartbeats, and reconnects.

Extracted from `scheduler.py` after characterization tests (Phase 2.0) proved
current feed behavior. Owns the in-memory/persisted active-feed state, bounded
buffer overflow policy, heartbeat timeout detection, and reconnect policy
modeling. `get_feed_status` remains the single read-only feed observability
surface: it never returns raw sockets, SDK objects, clients, or
credential-bearing connection strings.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from app.services.data.storage import db_helper
from app.utils.errors import DataError, ValidationError, trading_retry_delay
from app.utils.logger import logger

# In-memory active feed state.
ACTIVE_FEEDS: dict[str, dict[str, Any]] = {}

OverflowPolicy = Literal["halt", "drop_and_reconcile", "backpressure"]

DEFAULT_FEED_BUFFER_CAPACITY: int = 10000
"""Default maximum in-flight event count before an overflow policy triggers."""

DEFAULT_HEARTBEAT_TIMEOUT_SECONDS: float = 30.0
"""Default duration after which a feed's last heartbeat is considered stale."""


@dataclass(frozen=True, slots=True)
class ReconnectPolicy:
    """Deterministic reconnect/backoff policy for a real-time feed.

    Attributes:
        max_retries: Maximum reconnect attempts before giving up.
        base_backoff_seconds: Initial backoff delay before exponential growth.
        max_backoff_seconds: Maximum backoff delay.
        jitter_ratio: Fractional randomized jitter applied to the delay.
        circuit_breaker_cooldown_seconds: Cooldown before a half-open retry.
    """

    max_retries: int = 5
    base_backoff_seconds: float = 0.5
    max_backoff_seconds: float = 30.0
    jitter_ratio: float = 0.2
    circuit_breaker_cooldown_seconds: float = 60.0


DEFAULT_RECONNECT_POLICY: ReconnectPolicy = ReconnectPolicy()


def compute_reconnect_delay(
    attempt: int,
    policy: ReconnectPolicy = DEFAULT_RECONNECT_POLICY,
) -> float:
    """Compute the exponential backoff delay with jitter for a reconnect attempt.

    Args:
        attempt: Zero-based reconnect attempt number.
        policy: Reconnect policy governing backoff bounds.

    Returns:
        float: Delay in seconds before the next reconnect attempt.

    Raises:
        ValidationError: If `attempt` exceeds `policy.max_retries`.
    """
    if attempt >= policy.max_retries:
        err_msg = (
            f"Reconnect attempt {attempt} exceeds max_retries={policy.max_retries}."
        )
        logger.error(err_msg)
        raise ValidationError(err_msg, code="FEED_RECONCILIATION_FAILED")
    delay = trading_retry_delay(
        attempt,
        base_seconds=policy.base_backoff_seconds,
        max_seconds=policy.max_backoff_seconds,
        jitter_ratio=policy.jitter_ratio,
    )
    logger.debug(f"compute_reconnect_delay: attempt={attempt} delay={delay:.3f}s")
    return delay


def check_feed_buffer_capacity(
    feed: dict[str, Any],
    capacity: int = DEFAULT_FEED_BUFFER_CAPACITY,
) -> bool:
    """Return whether a feed's buffer depth is within the bounded capacity.

    Args:
        feed: Feed state mapping containing `buffer_depth`.
        capacity: Maximum permitted buffer depth.

    Returns:
        bool: True when the feed is within capacity, False when it has
        overflowed.
    """
    depth = int(feed.get("buffer_depth", 0))
    within_capacity = depth <= capacity
    logger.debug(
        f"check_feed_buffer_capacity: depth={depth} capacity={capacity} "
        f"within_capacity={within_capacity}"
    )
    return within_capacity


def check_feed_heartbeat_timeout(
    feed: dict[str, Any],
    timeout_seconds: float = DEFAULT_HEARTBEAT_TIMEOUT_SECONDS,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a feed's last heartbeat has exceeded the timeout threshold.

    Args:
        feed: Feed state mapping containing `last_heartbeat`.
        timeout_seconds: Maximum allowed silence duration.
        now: Optional deterministic current time for tests.

    Returns:
        bool: True when the feed heartbeat has timed out.
    """
    last_heartbeat = feed.get("last_heartbeat")
    if not last_heartbeat:
        return True
    current = now or datetime.now(UTC)
    try:
        last_dt = datetime.fromisoformat(last_heartbeat)
    except (TypeError, ValueError):
        return True
    elapsed = (current - last_dt).total_seconds()
    timed_out = elapsed > timeout_seconds
    logger.debug(
        f"check_feed_heartbeat_timeout: elapsed={elapsed:.1f}s "
        f"threshold={timeout_seconds}s timed_out={timed_out}"
    )
    return timed_out


def record_feed_heartbeat(
    feed_id: str, *, request_id: str | None = None
) -> dict[str, Any]:
    """Record a fresh heartbeat timestamp for an existing feed.

    Args:
        feed_id: Identifier of the feed being renewed.
        request_id: Optional tracking identifier.

    Returns:
        dict[str, Any]: Updated feed state.

    Raises:
        ValidationError: If the feed does not exist.
    """
    feed = ACTIVE_FEEDS.get(feed_id)
    if not feed:
        err_msg = f"Feed {feed_id} not found."
        raise ValidationError(err_msg, code="DATA_NOT_FOUND")

    now_str = datetime.now(UTC).isoformat()
    feed["last_heartbeat"] = now_str
    feed["updated_at"] = now_str
    ACTIVE_FEEDS[feed_id] = feed

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                "UPDATE feed_state SET last_heartbeat = ?, updated_at = ? "
                "WHERE feed_id = ?;",
                (now_str, now_str, feed_id),
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(
            f"Failed to persist heartbeat renewal for {feed_id}: {e}",
            extra={"request_id": request_id},
        )
    logger.debug(
        f"record_feed_heartbeat: feed_id={feed_id}", extra={"request_id": request_id}
    )
    return feed


def register_mock_feed(
    feed_id: str,
    source: str,
    symbol: str,
    data_kind: str,
    state: str = "connected",
    buffer_depth: int = 0,
    dropped_count: int = 0,
    gap_count: int = 0,
    reconnect_count: int = 0,
    circuit_breaker_state: str = "closed",
    last_error: str | None = None,
) -> None:
    """Register/update active feed in-memory and SQLite DB."""
    now_str = datetime.now(UTC).isoformat()
    feed_data = {
        "feed_id": feed_id,
        "source": source,
        "symbol": symbol,
        "data_kind": data_kind,
        "state": state,
        "last_heartbeat": now_str,
        "last_event": now_str,
        "buffer_depth": buffer_depth,
        "dropped_count": dropped_count,
        "gap_count": gap_count,
        "reconnect_count": reconnect_count,
        "circuit_breaker_state": circuit_breaker_state,
        "last_error": last_error,
        "created_at": now_str,
        "updated_at": now_str,
    }
    ACTIVE_FEEDS[feed_id] = feed_data

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO feed_state (
                    feed_id, source, symbol, data_kind, state, last_heartbeat,
                    last_event, buffer_depth, dropped_count, gap_count,
                    reconnect_count, circuit_breaker_state, last_error,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    feed_id,
                    source,
                    symbol,
                    data_kind,
                    state,
                    now_str,
                    now_str,
                    buffer_depth,
                    dropped_count,
                    gap_count,
                    reconnect_count,
                    circuit_breaker_state,
                    last_error,
                    now_str,
                    now_str,
                ),
            )
    except Exception as e:
        logger.error(f"Failed to persist feed state for {feed_id}: {e}")
        err_msg = f"Database sync failure: {e}"
        raise DataError(err_msg) from e


def handle_feed_overflow(
    feed_id: str,
    policy: OverflowPolicy,
) -> dict[str, Any]:
    """Handle a buffer overflow event on an active feed."""
    feed = ACTIVE_FEEDS.get(feed_id)
    if not feed:
        try:
            with db_helper.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM feed_state WHERE feed_id = ?;", (feed_id,)
                )
                row = cursor.fetchone()
                if row:
                    feed = dict(row)
        except Exception as e:
            err_msg = f"Database query error: {e}"
            raise DataError(err_msg) from e

    if not feed:
        err_msg = f"Feed {feed_id} not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    now_str = datetime.now(UTC).isoformat()
    if policy == "halt":
        feed["state"] = "failed"
        feed["last_error"] = "BUFFER_OVERFLOW"
        msg = f"Feed {feed_id} halted due to buffer overflow."
        logger.error(msg)
    elif policy == "drop_and_reconcile":
        feed["dropped_count"] += 1
        feed["gap_count"] += 1
        feed["state"] = "reconciling"
        feed["last_error"] = "BUFFER_OVERFLOW"
        msg = f"Feed {feed_id} overflow: dropping records and entering reconciliation."
        logger.warning(msg)
    elif policy == "backpressure":
        feed["state"] = "connected"
        msg = f"Feed {feed_id} applying backpressure."
        logger.info(msg)
    else:
        err_msg = f"Unsupported overflow policy: {policy}"
        raise ValidationError(err_msg)

    feed["updated_at"] = now_str
    ACTIVE_FEEDS[feed_id] = feed

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                UPDATE feed_state
                SET state = ?, dropped_count = ?, gap_count = ?,
                    last_error = ?, updated_at = ?
                WHERE feed_id = ?;
                """,
                (
                    feed["state"],
                    feed["dropped_count"],
                    feed["gap_count"],
                    feed["last_error"],
                    now_str,
                    feed_id,
                ),
            )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to update database for feed {feed_id} overflow: {e}")

    return {
        "feed_id": feed_id,
        "action": policy,
        "state": feed["state"],
        "dropped_count": feed["dropped_count"],
        "gap_count": feed["gap_count"],
    }


def _filter_in_memory_feeds(
    feed_id: str | None = None,
    source: str | None = None,
    symbol: str | None = None,
    data_kind: str | None = None,
) -> list[dict[str, Any]]:
    """Filter active in-memory feeds based on criteria."""
    matching_feeds = []
    if feed_id:
        if feed_id in ACTIVE_FEEDS:
            matching_feeds.append(ACTIVE_FEEDS[feed_id])
    else:
        for f in ACTIVE_FEEDS.values():
            if source and f["source"].lower() != source.lower():
                continue
            if symbol and f["symbol"].upper() != symbol.upper():
                continue
            if data_kind and f["data_kind"].lower() != data_kind.lower():
                continue
            matching_feeds.append(f)
    return matching_feeds


def _get_feeds_from_db(
    feed_id: str | None = None,
    source: str | None = None,
    symbol: str | None = None,
    data_kind: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve feeds from database matching the given criteria."""
    matching_feeds = []
    try:
        with db_helper.get_connection() as conn:
            if feed_id:
                cursor = conn.execute(
                    "SELECT * FROM feed_state WHERE feed_id = ?;", (feed_id,)
                )
            else:
                query = "SELECT * FROM feed_state WHERE 1=1"
                params = []
                if source:
                    query += " AND LOWER(source) = LOWER(?)"
                    params.append(source)
                if symbol:
                    query += " AND UPPER(symbol) = UPPER(?)"
                    params.append(symbol)
                if data_kind:
                    query += " AND LOWER(data_kind) = LOWER(?)"
                    params.append(data_kind)
                cursor = conn.execute(query, params)

            rows = cursor.fetchall()
            for r in rows:
                matching_feeds.append(
                    {
                        "feed_id": r["feed_id"],
                        "source": r["source"],
                        "symbol": r["symbol"],
                        "data_kind": r["data_kind"],
                        "state": r["state"],
                        "last_heartbeat": r["last_heartbeat"],
                        "last_event": r["last_event"],
                        "buffer_depth": int(r["buffer_depth"]),
                        "dropped_count": int(r["dropped_count"]),
                        "gap_count": int(r["gap_count"]),
                        "reconnect_count": int(r["reconnect_count"]),
                        "circuit_breaker_state": r["circuit_breaker_state"],
                        "last_error": r["last_error"],
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                    }
                )
    except Exception as e:
        logger.error(f"Database error during feed lookup: {e}")
        err_msg = f"Database error checking feeds: {e}"
        raise DataError(err_msg) from e
    return matching_feeds


def _enrich_feed_observability(feed: dict[str, Any]) -> dict[str, Any]:
    """Attach read-only bounded-buffer and heartbeat-timeout diagnostics."""
    enriched = dict(feed)
    enriched["buffer_capacity"] = DEFAULT_FEED_BUFFER_CAPACITY
    enriched["within_buffer_capacity"] = check_feed_buffer_capacity(feed)
    enriched["heartbeat_timeout_seconds"] = DEFAULT_HEARTBEAT_TIMEOUT_SECONDS
    enriched["heartbeat_timed_out"] = check_feed_heartbeat_timeout(feed)
    return enriched


def get_feed_status(
    feed_id: str | None = None,
    source: str | None = None,
    symbol: str | None = None,
    data_kind: str | None = None,
    *,
    request_id: str | None = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Inspect real-time feed health, heartbeats, buffer depth, and circuit states.

    This is the single read-only feed observability surface. It never returns
    raw sockets, SDK objects, clients, or credential-bearing connection
    strings; only bounded, JSON-safe diagnostic fields.
    """
    logger.info(
        f"Retrieving feed status: id={feed_id}, source={source}, symbol={symbol}",
        extra={"request_id": request_id},
    )

    matching_feeds = _filter_in_memory_feeds(
        feed_id=feed_id, source=source, symbol=symbol, data_kind=data_kind
    )

    if not matching_feeds:
        matching_feeds = _get_feeds_from_db(
            feed_id=feed_id, source=source, symbol=symbol, data_kind=data_kind
        )

    if not matching_feeds:
        err_msg = "No matching real-time feeds found."
        logger.error(err_msg, extra={"request_id": request_id})
        raise ValidationError(err_msg, code="DATA_NOT_FOUND")

    enriched_feeds = [_enrich_feed_observability(f) for f in matching_feeds]

    if feed_id:
        return enriched_feeds[0]

    return enriched_feeds
