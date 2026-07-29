"""Demonstrate FEAT-DATA-12 real-time feed lifecycle and observability operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_feed_config,
    build_feed_status_request,
    build_raw_feed_event,
    build_reconnect_policy,
    ingest_feed_event,
    read_feed_status,
    reconcile_feed_gap,
    reconnect_feed,
    start_internal_feed,
)
from app.services.data.contracts.errors import DataError
from app.utils import generate_id

_NOW = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _demonstrate_feature() -> None:
    """Exercise feed configuration, starting, ingestion, status, and reconnection."""
    req_id = generate_id("req")
    feed_id = "usage-feed-btc"

    policy = build_reconnect_policy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        backoff_multiplier=2.0,
    )
    config = build_feed_config(
        feed_id=feed_id,
        source_id="mt5",
        symbol="BTCUSD",
        data_kind="ohlcv",
        buffer_size=100,
        reconnect_policy=policy,
        request_id=req_id,
    )
    print("FeedConfig:", config.feed_id, config.symbol)

    try:
        st = start_internal_feed(config)
        print("start_internal_feed:", st.feed_id, st.state)
    except DataError as err:
        print("start_internal_feed handled:", err.code)

    event = build_raw_feed_event(
        feed_id=feed_id,
        sequence_number=1,
        payload={"open": 50000.0, "close": 50100.0},
        received_at=_NOW,
        request_id=req_id,
    )
    try:
        res = ingest_feed_event(feed_id, event)
        print("ingest_feed_event:", res.accepted)
    except DataError as err:
        print("ingest_feed_event handled:", err.code)

    status_req = build_feed_status_request(feed_id=feed_id, request_id=req_id)
    try:
        st_read = read_feed_status(status_req)
        print("read_feed_status:", st_read.feed_id, st_read.state)
    except DataError as err:
        print("read_feed_status handled:", err.code)

    try:
        reconnect_feed(
            feed_id=feed_id,
            reconnect=lambda: True,
            wait=lambda _s: None,
            clock=lambda: _NOW,
            request_id=req_id,
        )
        print("reconnect_feed: succeeded")
    except DataError as err:
        print("reconnect_feed handled:", err.code)

    try:
        reconcile_feed_gap(
            feed_id=feed_id,
            reconcile=lambda: True,
            clock=lambda: _NOW,
            request_id=req_id,
        )
        print("reconcile_feed_gap: succeeded")
    except DataError as err:
        print("reconcile_feed_gap handled:", err.code)


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_046() -> None:
    _header("fr_data_046")
    _demonstrate_once()


def fr_data_047() -> None:
    _header("fr_data_047")
    _demonstrate_once()


def fr_data_048() -> None:
    _header("fr_data_048")
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_046,
        fr_data_047,
        fr_data_048,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
