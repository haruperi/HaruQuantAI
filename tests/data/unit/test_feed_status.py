"""Unit tests for reading feed status, drift tracking, and heartbeat degradation."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts import (
    FeedConfig,
    FeedStatusRequest,
    RawFeedEvent,
    ReconnectPolicy,
)
from app.services.data.contracts.errors import DataError
from app.services.data.feeds.runtime import (
    _clear_active_feeds,
    ingest_feed_event,
    start_internal_feed,
)
from app.services.data.feeds.status import read_feed_status


@pytest.fixture(autouse=True)
def cleanup_active_feeds() -> Generator[None]:
    """Ensure in-memory active feeds are cleared between tests."""
    _clear_active_feeds()
    yield
    _clear_active_feeds()


@pytest.fixture
def feed_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Setup test environment variables and database tables."""
    db_path = tmp_path / "data_feeds.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.name}")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    from app.services.data.storage.migrations import run_data_migrations

    run_data_migrations(
        "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
    )
    return tmp_path


@pytest.fixture
def mock_source_descriptor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock the sources registry to return a live-capable staging source descriptor."""
    from app.services.data.contracts.sources import (
        SourceDescriptor,
        SourceLicensePolicy,
    )

    policy = SourceLicensePolicy(
        source_id="live-src",
        status="approved",
        permitted_workflows=("validation", "backtest", "research"),
        export_allowed=True,
        attribution_required=False,
    )
    desc = SourceDescriptor(
        source_id="live-src",
        readiness="production",
        capabilities=("live",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="1.0",
        timezone="UTC",
        revision="v1",
        license_policy=policy,
        identity_mapping_revision="v1",
        promotion_evidence=("evidence-1",),
    )

    monkeypatch.setattr(
        "app.services.data.sources.registry.get_source_descriptor",
        lambda _: desc,
    )


def test_status_is_backed_by_real_runtime_state(
    feed_test_env: Path, mock_source_descriptor: None
) -> None:
    """Verify read_feed_status reflects real active in-memory and database states."""
    t = datetime.now(UTC)
    policy = ReconnectPolicy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        jitter_seconds=1,
        circuit_cooldown_seconds=30,
    )
    config = FeedConfig(
        feed_id="feed-status-check",
        source_id="live-src",
        symbol="BTC/USD",
        data_kind="ohlcv",
        timeframe="M5",
        source_capability="live",
        buffer_capacity=100,
        overflow_policy="halt",
        heartbeat_timeout_seconds=5,
        reconnect_policy=policy,
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    # 1. Non-existent feed status fails
    with pytest.raises(DataError) as exc:
        read_feed_status(
            FeedStatusRequest(
                feed_id="non-existent",
                request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
            )
        )
    assert exc.value.args[0] == "DATA_NOT_FOUND"

    # 2. Starting status
    start_internal_feed(config)
    status_start = read_feed_status(
        FeedStatusRequest(
            feed_id="feed-status-check",
            request_id="req-bc0e142195cb27a6127a29283e0ccdfb3a51449da848f04abee1c1526184084e",
        )
    )
    assert status_start.state == "starting"
    assert status_start.buffer_depth == 0
    assert status_start.heartbeat_at is None

    # 3. Running status after ingestion
    ev = RawFeedEvent(
        feed_id="feed-status-check",
        sequence=1,
        event_timestamp=t,
        received_at=t + timedelta(milliseconds=150),
        payload={"price": 100.0},
        request_id="req-21229c6e11b8af38e942d0ec3f394d7d9efe9dfc82b7bee5c156549d7742431b",
    )
    ingest_feed_event("feed-status-check", ev)

    status_run = read_feed_status(
        FeedStatusRequest(
            feed_id="feed-status-check",
            request_id="req-d9c2b1bc8ab6d4617766f0c4dbee6bbbc164c63262325a31ed7b8c8bb2d90bca",
        )
    )
    assert status_run.state == "running"
    assert status_run.buffer_depth == 1
    assert status_run.heartbeat_at == t + timedelta(milliseconds=150)
    assert status_run.last_event_at == t
    assert status_run.drift_ms == 150


def test_heartbeat_timeout_degrades_status_on_read(
    feed_test_env: Path, mock_source_descriptor: None
) -> None:
    """Derive stale failure without mutating runtime or persisted feed state."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    policy = ReconnectPolicy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        jitter_seconds=1,
        circuit_cooldown_seconds=30,
    )
    config = FeedConfig(
        feed_id="feed-timeout",
        source_id="live-src",
        symbol="BTC/USD",
        data_kind="tick",
        source_capability="live",
        buffer_capacity=100,
        overflow_policy="halt",
        heartbeat_timeout_seconds=2,
        reconnect_policy=policy,
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    start_internal_feed(config)

    # Ingest initial event at t
    ev = RawFeedEvent(
        feed_id="feed-timeout",
        sequence=1,
        event_timestamp=t,
        received_at=t,
        payload={"price": 100.0},
        request_id="req-21229c6e11b8af38e942d0ec3f394d7d9efe9dfc82b7bee5c156549d7742431b",
    )
    ingest_feed_event("feed-timeout", ev)

    clock = MagicMock()
    clock.now.return_value = t + timedelta(seconds=5)

    # Read status should detect timeout and degrade feed to failed state
    request = FeedStatusRequest(
        feed_id="feed-timeout",
        request_id=(
            "req-f09e27992d5a69d28ab251d5d941310d46e61e94d556bbb7cd32198ec03aa605"
        ),
    )
    status = read_feed_status(request, clock=clock)
    assert status.state == "failed"
    assert status.last_error == "FEED_HEARTBEAT_TIMEOUT"

    from app.services.data.feeds.runtime import _ACTIVE_FEEDS

    assert _ACTIVE_FEEDS["feed-timeout"].state == "running"
    _clear_active_feeds()
    persisted_status = read_feed_status(
        FeedStatusRequest(
            feed_id="feed-timeout",
            request_id=request.request_id,
        ),
        clock=clock,
    )
    assert persisted_status.state == "failed"
    assert persisted_status.last_error == "FEED_HEARTBEAT_TIMEOUT"
