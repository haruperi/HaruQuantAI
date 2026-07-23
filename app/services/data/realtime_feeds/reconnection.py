"""Bounded reconnection with exponential backoff for internal feeds.

Retry is bounded and deliberate: a delay derived from the attempt count, capped, and
exhausted into an open circuit rather than retried forever. Blind retries are forbidden
by ``NFR-DATA-004`` — an unbounded reconnect loop against a failing provider is
indistinguishable from a working feed at the status boundary.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import timedelta

from app.services.data.contracts import DataError
from app.services.data.realtime_feeds.state import (
    _ACTIVE_FEEDS,
    ActiveFeed,
    _persist_feed_status,
)
from app.utils import Clock, logger, utc_now


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


__all__ = [
    "reconnect_feed",
]
