"""Behavioral coverage for bounded DATA feed lifecycle state."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from app.services.data.contracts import DataError
from app.services.data.realtime_feeds import buffer, reconnection, status
from app.services.data.realtime_feeds.contracts import (
    FeedConfig,
    FeedStatusRequest,
    RawFeedEvent,
    ReconnectPolicy,
)
from app.services.data.realtime_feeds.heartbeat import (
    heartbeat_expired,
    touch_heartbeat,
)
from app.services.data.realtime_feeds.state import _ACTIVE_FEEDS, ActiveFeed
from app.services.data.sources import registry
from app.utils import generate_id

_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


class _FixedClock:
    """Return one deterministic aware UTC instant."""

    def __init__(self, current: datetime) -> None:
        """Store the instant returned by ``now``."""
        self._current = current

    def now(self) -> datetime:
        """Return the configured instant."""
        return self._current


def _config(*, policy: str = "drop_and_reconcile", capacity: int = 1) -> FeedConfig:
    """Return one bounded feed configuration."""
    return FeedConfig(
        feed_id=f"feed-{policy}",
        source_id="fixture-live",
        symbol="EURUSD",
        data_kind="tick",
        source_capability="ticks",
        buffer_capacity=capacity,
        overflow_policy=policy,  # type: ignore[arg-type]
        heartbeat_timeout_seconds=10,
        reconnect_policy=ReconnectPolicy(
            max_retries=2,
            initial_backoff_seconds=1,
            max_backoff_seconds=4,
            jitter_seconds=1,
            circuit_cooldown_seconds=30,
        ),
        request_id=generate_id("req"),
    )


def _event(config: FeedConfig, sequence: int, *, seconds: int = 0) -> RawFeedEvent:
    """Return one valid raw event."""
    timestamp = _NOW + timedelta(seconds=seconds)
    return RawFeedEvent(
        feed_id=config.feed_id,
        sequence=sequence,
        event_timestamp=timestamp,
        received_at=timestamp + timedelta(milliseconds=10),
        payload={"bid": 1.1},
        request_id=generate_id("req"),
    )


@pytest.fixture(autouse=True)
def _isolated_feed_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate runtime state and replace persistence with deterministic evidence."""
    _ACTIVE_FEEDS.clear()
    result = SimpleNamespace(rows=(), affected_rows=1, committed=True)
    monkeypatch.setattr(buffer, "execute_transaction", lambda _request: result)
    monkeypatch.setattr(buffer, "_persist_feed_status", lambda *_args: None)
    monkeypatch.setattr(reconnection, "_persist_feed_status", lambda *_args: None)
    monkeypatch.setattr(
        registry,
        "get_source_descriptor",
        lambda _source_id: SimpleNamespace(
            readiness="production",
            capabilities=("ticks",),
        ),
    )
    yield
    _ACTIVE_FEEDS.clear()


def test_start_ingest_status_and_heartbeat() -> None:
    """Start a feed, ingest an event, and report its live health evidence."""
    config = _config(capacity=2)
    started = buffer.start_internal_feed(config)
    accepted = buffer.ingest_feed_event(config.feed_id, _event(config, 1))
    current = status.read_feed_status(
        FeedStatusRequest(feed_id=config.feed_id, request_id=generate_id("req")),
        clock=_FixedClock(_NOW + timedelta(seconds=1)),
    )

    assert started.state == "starting"
    assert accepted.accepted
    assert current.state == "running"
    active = _ACTIVE_FEEDS[config.feed_id]
    touch_heartbeat(active, _NOW)
    assert active.heartbeat_at == _NOW
    assert heartbeat_expired(None, _NOW, timedelta(seconds=1))
    assert not heartbeat_expired(_NOW, _NOW, timedelta(seconds=1))


@pytest.mark.parametrize("policy", ["halt", "backpressure"])
def test_overflow_fail_closed_policies(policy: str) -> None:
    """Halt and backpressure policies reject a full buffer."""
    config = _config(policy=policy)
    buffer.start_internal_feed(config)
    buffer.ingest_feed_event(config.feed_id, _event(config, 1))
    with pytest.raises(DataError) as exc_info:
        buffer.ingest_feed_event(config.feed_id, _event(config, 2, seconds=1))
    assert exc_info.value.code == "BUFFER_OVERFLOW"


def test_drop_reconcile_requires_success() -> None:
    """Record a gap and unblock only after explicit successful reconciliation."""
    config = _config()
    buffer.start_internal_feed(config)
    buffer.ingest_feed_event(config.feed_id, _event(config, 1))
    dropped = buffer.ingest_feed_event(config.feed_id, _event(config, 2, seconds=1))
    assert dropped.gap_recorded
    assert not dropped.accepted

    request_id = generate_id("req")
    with pytest.raises(DataError):
        buffer.reconcile_feed_gap(config.feed_id, request_id, reconcile=lambda: False)
    buffer.reconcile_feed_gap(
        config.feed_id,
        request_id,
        reconcile=lambda: True,
        clock=_FixedClock(_NOW + timedelta(seconds=2)),
    )
    assert _ACTIVE_FEEDS[config.feed_id].state == "running"


def test_ingest_rejects_unknown_mismatch_blocked_and_timeout() -> None:
    """Reject events that lack a valid live lifecycle context."""
    config = _config(capacity=2)
    event = _event(config, 1)
    with pytest.raises(DataError):
        buffer.ingest_feed_event(config.feed_id, event)

    buffer.start_internal_feed(config)
    mismatch = event.model_copy(update={"feed_id": "other"})
    with pytest.raises(DataError):
        buffer.ingest_feed_event(config.feed_id, mismatch)
    active = _ACTIVE_FEEDS[config.feed_id]
    active.state = "blocked"
    active.last_error = "POLICY_BLOCKED"
    with pytest.raises(DataError):
        buffer.ingest_feed_event(config.feed_id, event)
    active.state = "running"
    active.heartbeat_at = _NOW
    with pytest.raises(DataError) as exc_info:
        buffer.ingest_feed_event(config.feed_id, _event(config, 2, seconds=11))
    assert exc_info.value.code == "FEED_HEARTBEAT_TIMEOUT"


def test_reconnect_success_failure_exhaustion_and_open_breaker() -> None:
    """Exercise bounded reconnect state and deterministic delays."""
    config = _config(capacity=2)
    active = ActiveFeed(config, _NOW)
    active.state = "failed"
    _ACTIVE_FEEDS[config.feed_id] = active
    waits: list[int] = []

    reconnection.reconnect_feed(
        config.feed_id,
        generate_id("req"),
        reconnect=lambda: True,
        wait=waits.append,
        clock=_FixedClock(_NOW),
    )
    assert active.state == "running"
    assert waits

    active.state = "failed"
    with pytest.raises(DataError) as exc_info:
        reconnection.reconnect_feed(
            config.feed_id,
            generate_id("req"),
            reconnect=lambda: False,
            wait=lambda _delay: None,
            clock=_FixedClock(_NOW),
        )
    assert exc_info.value.code == "SOURCE_UNAVAILABLE"

    active.reconnect_count = config.reconnect_policy.max_retries
    with pytest.raises(DataError) as exc_info:
        reconnection.reconnect_feed(
            config.feed_id,
            generate_id("req"),
            reconnect=lambda: True,
            wait=lambda _delay: None,
            clock=_FixedClock(_NOW),
        )
    assert exc_info.value.code == "POLICY_BLOCKED"

    with pytest.raises(DataError) as exc_info:
        reconnection.reconnect_feed(
            config.feed_id,
            generate_id("req"),
            reconnect=lambda: True,
            wait=lambda _delay: None,
            clock=_FixedClock(_NOW + timedelta(seconds=1)),
        )
    assert exc_info.value.code == "CIRCUIT_BREAKER_OPEN"


def test_status_database_result_and_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Read persisted status and fail closed when no evidence exists."""
    request = FeedStatusRequest(feed_id="persisted", request_id=generate_id("req"))
    row: dict[str, Any] = {
        "feed_id": "persisted",
        "source_id": "fixture-live",
        "symbol": "EURUSD",
        "data_kind": "tick",
        "state": "running",
        "heartbeat_at": _NOW.isoformat(),
        "last_event_at": _NOW.isoformat(),
        "buffer_depth": 0,
        "buffer_capacity": 2,
        "dropped_count": 0,
        "gap_count": 0,
        "reconnect_count": 0,
        "breaker_state": "closed",
        "drift_ms": 0,
        "last_error": None,
        "heartbeat_timeout_seconds": 10,
    }
    monkeypatch.setattr(
        "app.services.data.persistence.transactions.execute_transaction",
        lambda _transaction: SimpleNamespace(rows=(row,)),
    )
    current = status.read_feed_status(
        request,
        clock=_FixedClock(_NOW + timedelta(seconds=20)),
    )
    assert current.state == "failed"
    assert current.last_error == "FEED_HEARTBEAT_TIMEOUT"

    monkeypatch.setattr(
        "app.services.data.persistence.transactions.execute_transaction",
        lambda _transaction: SimpleNamespace(rows=()),
    )
    with pytest.raises(DataError):
        status.read_feed_status(request)
