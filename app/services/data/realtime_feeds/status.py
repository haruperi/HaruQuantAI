"""Read persisted/in-memory feed status information."""

from __future__ import annotations

from datetime import datetime

from app.services.data.contracts import DataError
from app.services.data.realtime_feeds.contracts import (
    FeedStatus,
    FeedStatusRequest,
)
from app.utils import Clock, logger, utc_now


def _parse_time(value: object) -> datetime | None:
    """Parse one nullable persisted UTC timestamp."""
    logger.debug("Parsing persisted feed timestamp evidence")
    return None if value is None else datetime.fromisoformat(str(value))


def _effective_health(
    state: str,
    heartbeat_at: datetime | None,
    heartbeat_timeout_seconds: int,
    now: datetime,
    last_error: str | None,
) -> tuple[str, str | None]:
    """Derive stale status without mutating persisted or in-memory runtime state."""
    logger.debug("Deriving effective DATA feed health")
    if state != "running" or heartbeat_at is None:
        return state, last_error
    elapsed = (now - heartbeat_at).total_seconds()
    if elapsed > heartbeat_timeout_seconds:
        return "failed", "FEED_HEARTBEAT_TIMEOUT"
    return state, last_error


def read_feed_status(
    request: FeedStatusRequest,
    *,
    clock: Clock | None = None,
) -> FeedStatus:
    """Read persisted or in-memory feed status without mutation.

    Args:
        request: The feed status request.
        clock: Optional injected UTC clock.

    Returns:
        The current FeedStatus evidence.
    """
    logger.info("Reading persisted status for feed %s", request.feed_id)

    from app.services.data.realtime_feeds.state import _ACTIVE_FEEDS

    if request.feed_id in _ACTIVE_FEEDS:
        active = _ACTIVE_FEEDS[request.feed_id]
        now = utc_now(clock)
        state, last_error = _effective_health(
            active.state,
            active.heartbeat_at,
            active.config.heartbeat_timeout_seconds,
            now,
            active.last_error,
        )

        return FeedStatus(
            feed_id=active.config.feed_id,
            source_id=active.config.source_id,
            symbol=active.config.symbol,
            data_kind=active.config.data_kind,
            state=state,  # type: ignore[arg-type]
            heartbeat_at=active.heartbeat_at,
            last_event_at=active.last_event_at,
            buffer_depth=len(active.buffer),
            buffer_capacity=active.config.buffer_capacity,
            dropped_count=active.dropped_count,
            gap_count=active.gap_count,
            reconnect_count=active.reconnect_count,
            breaker_state=active.breaker_state,  # type: ignore[arg-type]
            drift_ms=active.drift_ms,
            last_error=last_error,
            request_id=request.request_id,
        )

    # Check database
    from app.services.data.persistence.contracts import (
        StatementPlan,
        TransactionRequest,
    )
    from app.services.data.persistence.transactions import execute_transaction

    query_sql = (
        "SELECT feed_id, source_id, symbol, data_kind, state, heartbeat_at, "
        "  last_event_at, buffer_depth, buffer_capacity, dropped_count, "
        "  gap_count, reconnect_count, breaker_state, drift_ms, last_error, "
        "  heartbeat_timeout_seconds "
        "FROM data_feeds WHERE feed_id = ?"
    )
    res = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(query_sql,),
                parameter_sets=((request.feed_id,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )
    if not res.rows:
        raise DataError(
            "DATA_NOT_FOUND",
            safe_details={"message": f"Feed {request.feed_id} was not found"},
            request_id=request.request_id,
        )

    row = res.rows[0]
    heartbeat_at = _parse_time(row["heartbeat_at"])
    state, last_error = _effective_health(
        str(row["state"]),
        heartbeat_at,
        int(str(row["heartbeat_timeout_seconds"])),
        utc_now(clock),
        str(row["last_error"]) if row["last_error"] is not None else None,
    )

    return FeedStatus(
        feed_id=str(row["feed_id"]),
        source_id=str(row["source_id"]),
        symbol=str(row["symbol"]),
        data_kind=row["data_kind"],  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
        heartbeat_at=heartbeat_at,
        last_event_at=_parse_time(row["last_event_at"]),
        buffer_depth=int(row["buffer_depth"]),  # type: ignore[arg-type]
        buffer_capacity=int(row["buffer_capacity"]),  # type: ignore[arg-type]
        dropped_count=int(row["dropped_count"]),  # type: ignore[arg-type]
        gap_count=int(row["gap_count"]),  # type: ignore[arg-type]
        reconnect_count=int(row["reconnect_count"]),  # type: ignore[arg-type]
        breaker_state=row["breaker_state"],  # type: ignore[arg-type]
        drift_ms=int(row["drift_ms"]) if row["drift_ms"] is not None else None,
        last_error=last_error,
        request_id=request.request_id,
    )


__all__ = [
    "get_feed_status",
    "read_feed_status",
]


def get_feed_status(request: FeedStatusRequest) -> FeedStatus:
    """Query live feed buffer metrics, drift, and reconnect status."""
    logger.info("Executing public DATA feed-status query")
    return read_feed_status(request)
