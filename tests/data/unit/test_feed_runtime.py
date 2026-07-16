"""Unit tests for feed runtime initialization, event ingestion, and overflow."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.services.data.contracts import (
    FeedConfig,
    RawFeedEvent,
    ReconnectPolicy,
)
from app.services.data.contracts.errors import DataError
from app.services.data.feeds.runtime import (
    _clear_active_feeds,
    ingest_feed_event,
    reconcile_feed_gap,
    reconnect_feed,
    start_internal_feed,
)


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


def test_start_feed_requires_declared_capability(
    feed_test_env: Path, mock_source_descriptor: None
) -> None:
    """Verify starting feed fails if capability does not match."""
    policy = ReconnectPolicy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        jitter_seconds=1,
        circuit_cooldown_seconds=30,
    )
    # Check invalid capability
    config = FeedConfig(
        feed_id="feed-1",
        source_id="live-src",
        symbol="BTC/USD",
        data_kind="ohlcv",
        timeframe="M5",
        source_capability="historical",  # Source only declares "live"
        buffer_capacity=1000,
        overflow_policy="halt",
        heartbeat_timeout_seconds=5,
        reconnect_policy=policy,
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    with pytest.raises(DataError) as exc:
        start_internal_feed(config)
    assert exc.value.args[0] == "POLICY_BLOCKED"


def test_start_feed_requires_staging_or_production(
    feed_test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify starting feed fails if the source readiness is invalid."""
    from app.services.data.contracts.sources import (
        SourceDescriptor,
        SourceLicensePolicy,
    )

    policy = SourceLicensePolicy(
        source_id="test-src",
        status="approved",
        permitted_workflows=("validation", "backtest", "research"),
        export_allowed=True,
        attribution_required=False,
    )
    desc = SourceDescriptor(
        source_id="test-src",
        readiness="disabled",  # Not staging or production
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

    policy_rec = ReconnectPolicy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        jitter_seconds=1,
        circuit_cooldown_seconds=30,
    )
    config = FeedConfig(
        feed_id="feed-2",
        source_id="test-src",
        symbol="BTC/USD",
        data_kind="tick",
        source_capability="live",
        buffer_capacity=1000,
        overflow_policy="halt",
        heartbeat_timeout_seconds=5,
        reconnect_policy=policy_rec,
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    with pytest.raises(DataError) as exc:
        start_internal_feed(config)
    assert exc.value.args[0] == "POLICY_BLOCKED"


def test_overflow_records_gap_without_backfill(
    feed_test_env: Path, mock_source_descriptor: None
) -> None:
    """Verify overflow policies properly record gaps or drop data."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    policy = ReconnectPolicy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        jitter_seconds=1,
        circuit_cooldown_seconds=30,
    )

    # 1. Test "halt" policy
    config_halt = FeedConfig(
        feed_id="feed-halt",
        source_id="live-src",
        symbol="BTC/USD",
        data_kind="ohlcv",
        timeframe="M5",
        source_capability="live",
        buffer_capacity=2,
        overflow_policy="halt",
        heartbeat_timeout_seconds=5,
        reconnect_policy=policy,
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    start_internal_feed(config_halt)

    # Ingest 2 events to fill the buffer
    ev1 = RawFeedEvent(
        feed_id="feed-halt",
        sequence=1,
        event_timestamp=t,
        received_at=t,
        payload={"price": 100.0},
        request_id="req-21229c6e11b8af38e942d0ec3f394d7d9efe9dfc82b7bee5c156549d7742431b",
    )
    ev2 = RawFeedEvent(
        feed_id="feed-halt",
        sequence=2,
        event_timestamp=t + timedelta(seconds=1),
        received_at=t + timedelta(seconds=1),
        payload={"price": 101.0},
        request_id="req-94a3d683309f201aa0cf837b52e9897ead0054d0d8c226beb429dec71a9b16cd",
    )
    ingest_feed_event("feed-halt", ev1)
    ingest_feed_event("feed-halt", ev2)

    # Ingest 3rd event: expect halt (raises BUFFER_OVERFLOW)
    ev3 = RawFeedEvent(
        feed_id="feed-halt",
        sequence=3,
        event_timestamp=t + timedelta(seconds=2),
        received_at=t + timedelta(seconds=2),
        payload={"price": 102.0},
        request_id="req-ae4c6e1a3ab89cd972c7bf6d98ea13a3b6862240a4a4f89823aaed2c9eb3506c",
    )
    with pytest.raises(DataError) as exc:
        ingest_feed_event("feed-halt", ev3)
    assert exc.value.args[0] == "BUFFER_OVERFLOW"

    # 2. Governed drop rejects the new event and records a reconciliation gap.
    config_drop_old = FeedConfig(
        feed_id="feed-drop-old",
        source_id="live-src",
        symbol="BTC/USD",
        data_kind="tick",
        source_capability="live",
        buffer_capacity=2,
        overflow_policy="drop_and_reconcile",
        heartbeat_timeout_seconds=5,
        reconnect_policy=policy,
        request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
    )

    start_internal_feed(config_drop_old)
    ingest_feed_event(
        "feed-drop-old", ev1.model_copy(update={"feed_id": "feed-drop-old"})
    )
    ingest_feed_event(
        "feed-drop-old", ev2.model_copy(update={"feed_id": "feed-drop-old"})
    )

    dropped_old = ingest_feed_event(
        "feed-drop-old", ev3.model_copy(update={"feed_id": "feed-drop-old"})
    )
    assert dropped_old.accepted is False
    assert dropped_old.dropped_count == 1
    assert dropped_old.gap_recorded is True
    reconcile_feed_gap("feed-drop-old", ev3.request_id, reconcile=lambda: True)

    # 3. A second feed follows the same single governed drop policy.
    config_drop_new = FeedConfig(
        feed_id="feed-drop-new",
        source_id="live-src",
        symbol="BTC/USD",
        data_kind="tick",
        source_capability="live",
        buffer_capacity=2,
        overflow_policy="drop_and_reconcile",
        heartbeat_timeout_seconds=5,
        reconnect_policy=policy,
        request_id="req-bc0e142195cb27a6127a29283e0ccdfb3a51449da848f04abee1c1526184084e",
    )

    start_internal_feed(config_drop_new)
    ingest_feed_event(
        "feed-drop-new", ev1.model_copy(update={"feed_id": "feed-drop-new"})
    )
    ingest_feed_event(
        "feed-drop-new", ev2.model_copy(update={"feed_id": "feed-drop-new"})
    )

    dropped_new = ingest_feed_event(
        "feed-drop-new", ev3.model_copy(update={"feed_id": "feed-drop-new"})
    )
    assert dropped_new.accepted is False
    assert dropped_new.dropped_count == 1
    assert dropped_new.gap_recorded is True


def test_reconnect_circuit_breaker(
    feed_test_env: Path, mock_source_descriptor: None
) -> None:
    """Verify reconnect policies transition breaker state on retry exhaustion."""
    policy = ReconnectPolicy(
        max_retries=2,
        initial_backoff_seconds=1,
        max_backoff_seconds=5,
        jitter_seconds=1,
        circuit_cooldown_seconds=10,
    )
    config = FeedConfig(
        feed_id="feed-rec",
        source_id="live-src",
        symbol="BTC/USD",
        data_kind="tick",
        source_capability="live",
        buffer_capacity=1000,
        overflow_policy="halt",
        heartbeat_timeout_seconds=5,
        reconnect_policy=policy,
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    start_internal_feed(config)

    delays: list[int] = []
    # 1st reconnect
    reconnect_feed(
        "feed-rec",
        "req-2f45aa10615b9ab8062575ce00004e1e39c52115438a34947710bde55dbc38f7",
        reconnect=lambda: True,
        wait=delays.append,
    )
    # 2nd reconnect
    reconnect_feed(
        "feed-rec",
        "req-98621c92bd230e6dfa1ed3f8432ac9538a406cf098d28e06098439c8a355fcc6",
        reconnect=lambda: True,
        wait=delays.append,
    )

    # 3rd reconnect should exceed max_retries and block/open the circuit
    with pytest.raises(DataError) as exc:
        reconnect_feed(
            "feed-rec",
            "req-6601eb863f17b44123af560c6b51754b71aeab7860ea641357235a770c90b8eb",
            reconnect=lambda: True,
            wait=delays.append,
        )
    assert exc.value.args[0] == "POLICY_BLOCKED"

    # Subsequent reconnect attempts are immediately blocked
    with pytest.raises(DataError) as exc:
        reconnect_feed(
            "feed-rec",
            "req-58dac794ffbc7224db83fa1524c5a120d14ec3c968689000c949eb46e88bb1b1",
            reconnect=lambda: True,
            wait=delays.append,
        )
    assert exc.value.args[0] == "CIRCUIT_BREAKER_OPEN"

    _clear_active_feeds()
    restored = start_internal_feed(config)
    assert restored.breaker_state == "open"
    with pytest.raises(DataError) as restored_error:
        reconnect_feed(
            "feed-rec",
            "req-17f27d3e8ff1603bb79995497775f33f49436fdba08b178395e2b86f9783c666",
            reconnect=lambda: True,
            wait=delays.append,
        )
    assert restored_error.value.code == "CIRCUIT_BREAKER_OPEN"
