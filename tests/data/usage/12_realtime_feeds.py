"""Demonstrate FEAT-DATA-12 real-time feed lifecycle and observability operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import DataError
from app.services.data.realtime_feeds import (
    ingest_feed_event,
    read_feed_status,
    reconcile_feed_gap,
    reconnect_feed,
    start_internal_feed,
)
from app.services.data.realtime_feeds.contracts import (
    FeedConfig,
    FeedStatusRequest,
    RawFeedEvent,
    ReconnectPolicy,
)
from app.utils import generate_id

_NOW = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def main() -> None:
    """Exercise feed configuration, starting, ingestion, status, and reconnection."""
    req_id = generate_id("req")
    feed_id = "usage-feed-btc"

    policy = ReconnectPolicy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        jitter_seconds=1,
        circuit_cooldown_seconds=30,
    )

    config = FeedConfig(
        feed_id=feed_id,
        source_id="mt5",
        symbol="BTCUSD",
        data_kind="tick",
        source_capability="realtime_tick",
        buffer_capacity=1_000,
        overflow_policy="drop_and_reconcile",
        heartbeat_timeout_seconds=30,
        reconnect_policy=policy,
        request_id=req_id,
    )

    status_req = FeedStatusRequest(feed_id=feed_id, request_id=req_id)
    print("FeedConfig:", config.feed_id, config.symbol)

    try:
        st = start_internal_feed(config)
        print("start_internal_feed:", st.feed_id, st.state)
    except DataError as err:
        print("start_internal_feed handled:", err.code)

    event = RawFeedEvent(
        feed_id=feed_id,
        sequence=1,
        event_timestamp=_NOW,
        received_at=_NOW,
        payload={"bid": 60000.0, "ask": 60001.0},
        request_id=req_id,
    )

    try:
        res = ingest_feed_event(feed_id, event)
        print("ingest_feed_event:", res.accepted)
    except DataError as err:
        print("ingest_feed_event handled:", err.code)

    try:
        st_read = read_feed_status(status_req)
        print("read_feed_status:", st_read.feed_id, st_read.state)
    except DataError as err:
        print("read_feed_status handled:", err.code)

    try:
        reconnect_feed(
            feed_id,
            req_id,
            reconnect=lambda: True,
            wait=lambda s: None,
        )
        print("reconnect_feed: succeeded")
    except DataError as err:
        print("reconnect_feed handled:", err.code)

    try:
        reconcile_feed_gap(
            feed_id,
            req_id,
            reconcile=lambda: True,
        )
        print("reconcile_feed_gap: succeeded")
    except DataError as err:
        print("reconcile_feed_gap handled:", err.code)


if __name__ == "__main__":
    main()
