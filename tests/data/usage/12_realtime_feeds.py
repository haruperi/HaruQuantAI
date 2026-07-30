"""Demonstrate FEAT-DATA-12 real-time feed lifecycle and observability operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_settings,
    build_feed_config,
    build_feed_status_request,
    build_market_data_request,
    build_raw_feed_event,
    build_reconnect_policy,
    data_settings_context,
    get_tick_data,
    ingest_feed_event,
    read_feed_status,
    reconcile_feed_gap,
    reconnect_feed,
    run_data_migrations,
    start_internal_feed,
    unwrap_data_response,
)
from app.utils import generate_id


def _error_code(error: BaseException) -> str:
    """Return a safe public-boundary error identifier."""
    return str(getattr(error, "code", type(error).__name__))


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _demonstrate_feature() -> None:
    """Exercise feed configuration, starting, ingestion, status, and reconnection."""
    with TemporaryDirectory(prefix="usage-feeds-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            try:
                _demonstrate_feed_operations()
            except Exception as error:  # noqa: BLE001 - domain classes stay private.
                print(
                    "Genuine feed evidence unavailable:",
                    _error_code(error),
                    "(no injected fallback used)",
                )


def _demonstrate_feed_operations() -> None:
    """Run the feed lifecycle operations inside an active context."""
    req_id = generate_id("req")
    feed_id = "usage-feed-eurusd"
    tick = _get_genuine_tick()

    policy = build_reconnect_policy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        jitter_seconds=1,
        circuit_cooldown_seconds=30,
    )
    config = build_feed_config(
        feed_id=feed_id,
        source_id="mt5",
        symbol="EURUSD",
        data_kind="tick",
        timeframe=None,
        source_capability="ticks",
        buffer_capacity=1,
        overflow_policy="drop_and_reconcile",
        heartbeat_timeout_seconds=30,
        reconnect_policy=policy,
        request_id=req_id,
    )
    print(
        "FeedConfig from genuine MT5 tick:",
        config.feed_id,
        config.symbol,
        tick.timestamp.isoformat(),
        str(tick.bid),
        str(tick.ask),
    )

    try:
        st = start_internal_feed(config)
        print("start_internal_feed:", st.feed_id, st.state)
    except Exception as err:  # noqa: BLE001 - domain error classes stay internal.
        print("start_internal_feed handled:", _error_code(err))

    event = build_raw_feed_event(
        feed_id=feed_id,
        sequence=1,
        event_timestamp=tick.timestamp,
        received_at=tick.available_at,
        payload={"bid": str(tick.bid), "ask": str(tick.ask)},
        request_id=req_id,
    )
    try:
        res = ingest_feed_event(feed_id, event)
        print("ingest_feed_event:", res.accepted)
    except Exception as err:  # noqa: BLE001 - domain error classes stay internal.
        print("ingest_feed_event handled:", _error_code(err))

    status_req = build_feed_status_request(feed_id=feed_id, request_id=req_id)
    try:
        st_read = read_feed_status(status_req)
        print("read_feed_status:", st_read.feed_id, st_read.state)
    except Exception as err:  # noqa: BLE001 - domain error classes stay internal.
        print("read_feed_status handled:", _error_code(err))

    try:
        reconnect_feed(
            feed_id=feed_id,
            reconnect=_provider_probe,
            wait=lambda _s: None,
            request_id=req_id,
        )
        print("reconnect_feed: succeeded")
    except Exception as err:  # noqa: BLE001 - domain error classes stay internal.
        print("reconnect_feed handled:", _error_code(err))

    overflow = ingest_feed_event(
        feed_id,
        build_raw_feed_event(
            feed_id=feed_id,
            sequence=2,
            event_timestamp=tick.timestamp,
            received_at=tick.available_at,
            payload={"bid": str(tick.bid), "ask": str(tick.ask)},
            request_id=req_id,
        ),
    )
    print(
        "Overflow evidence:",
        f"accepted={overflow.accepted}",
        f"gap_recorded={overflow.gap_recorded}",
        f"dropped={overflow.dropped_count}",
    )

    try:
        reconcile_feed_gap(
            feed_id=feed_id,
            reconcile=_provider_probe,
            request_id=req_id,
        )
        print("reconcile_feed_gap: succeeded")
    except Exception as err:  # noqa: BLE001 - domain error classes stay internal.
        print("reconcile_feed_gap handled:", _error_code(err))


def _get_genuine_tick() -> Any:
    """Retrieve one bounded genuine MT5 tick through the public Data API."""
    end = datetime.now(UTC)
    response = get_tick_data(
        build_market_data_request(
            source_id="mt5",
            symbol="EURUSD",
            data_kind="ticks",
            timeframe=None,
            start=end - timedelta(days=5),
            end=end,
            limit=1,
            use_cache=False,
            quality_failure_behavior="warn",
            workflow_context="research",
            precision_policy="decimal_string",
            stale_cache_policy="refresh",
            fallback_sources=(),
            request_id=generate_id("req"),
        )
    )
    tick_dataset = unwrap_data_response(
        response,
        operation="data.usage.get_tick_data",
        request_id=response.metadata.request_id,
    )
    return tick_dataset.records[-1]


def _provider_probe() -> bool:
    """Confirm reconciliation/reconnection against a fresh provider read."""
    _get_genuine_tick()
    return True


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
