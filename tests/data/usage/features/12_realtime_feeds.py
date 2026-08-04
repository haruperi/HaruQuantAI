# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-12 real-time feed lifecycle and observability operations."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_feed_config,
    build_feed_status_request,
    build_market_stream_request,
    build_raw_feed_event,
    build_reconnect_policy,
    data_settings_context,
    ingest_feed_event,
    read_feed_status,
    run_data_migrations,
    start_internal_feed,
    stream_market_data,
)
from app.utils import generate_id


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_data_046() -> None:
    """FR-DATA-046: Stage 1 — Configure feed policy, buffer limits, and start internal streaming feed."""
    _header(
        "Stage 1: Feed Configuration & Lifecycle Management - Start Internal Feed (FR-DATA-046)"
    )
    req_id = generate_id("req")
    feed_id = "usage-feed-eurusd"

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
    print(_format_result(config))
    try:
        st_res = start_internal_feed(config)
        print(_format_result(st_res))
        if st_res.status == "success" and st_res.data:
            print(
                f"Data -> FeedStatus(feed_id={st_res.data.feed_id}, state={st_res.data.state})"
            )
    except Exception as err:
        code = getattr(err, "code", type(err).__name__)
        print(f"Data -> FeedStatus(error={code})")


def fr_data_047() -> None:
    """FR-DATA-047: Stage 2 — Ingest raw feed events, handle buffer overflow, and perform gap reconciliation."""
    _header(
        "Stage 2: Event Ingestion, Buffer Overflow & Gap Reconciliation - Feed Event Ingestion (FR-DATA-047)"
    )
    req_id = generate_id("req")
    feed_id = "usage-feed-eurusd"
    now = datetime.now(UTC)

    event = build_raw_feed_event(
        feed_id=feed_id,
        sequence=1,
        event_timestamp=now,
        received_at=now,
        payload={"bid": "1.0850", "ask": "1.0852"},
        request_id=req_id,
    )
    print(_format_result(event))
    try:
        res = ingest_feed_event(feed_id, event)
        print(_format_result(res))
        if res.status == "success" and res.data:
            print(
                f"Data -> FeedEventResult(accepted={res.data.accepted}, gap_recorded={res.data.gap_recorded})"
            )
    except Exception as err:
        code = getattr(err, "code", type(err).__name__)
        print(f"Data -> FeedEventResult(error={code})")


def fr_data_048() -> None:
    """FR-DATA-048: Stage 3 — Read feed status observability metrics and execute transport reconnection."""
    _header(
        "Stage 3: Feed Status Observability & Transport Reconnection - Read Status & Reconnect (FR-DATA-048)"
    )
    req_id = generate_id("req")
    feed_id = "usage-feed-eurusd"
    status_req = build_feed_status_request(feed_id=feed_id, request_id=req_id)
    try:
        st_read = read_feed_status(status_req)
        print(_format_result(st_read))
        if st_read.status == "success" and st_read.data:
            print(f"Data -> FeedStatus(state={st_read.data.state})")
    except Exception as err:
        code = getattr(err, "code", type(err).__name__)
        print(f"Data -> FeedStatus(error={code})")


def fr_data_154_157() -> None:
    """FR-DATA-154..157: Build both MT5 stream modes through Data's API."""
    _header("Stage 4: Data-Owned MT5 Tick and Closed-Bar Streams")

    async def demonstrate() -> None:
        """Construct both streams without opening a live provider in usage CI."""
        for mode, timeframe in (("ticks", "M1"), ("bars", "H1")):
            request = build_market_stream_request(
                source_id="mt5",
                symbol="EURUSD",
                mode=mode,
                timeframe=timeframe,
                request_id=generate_id("req"),
            )
            print(_format_result(request))
            stream = stream_market_data(request)
            await cast("AsyncGenerator[object]", stream).aclose()
            print(f"Data -> MarketStream(mode={mode}, timeframe={timeframe})")

    asyncio.run(demonstrate())


def main() -> None:
    """Execute every functional-requirement demonstration."""
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
            print("=" * 80)
            print("FEATURE: FEAT-DATA-12 - Realtime Feeds and Streaming")
            print(
                "PURPOSE: Configure feeds, ingest events, reconcile gaps, and monitor feed status"
            )
            print(
                "MODULE FLOW: Stage 1 (Feed Config & Lifecycle) -> Stage 2 (Event Ingestion & Gap Reconciliation) -> Stage 3 (Status Observability & Reconnection)"
            )
            print("=" * 80)

            fr_data_046()
            fr_data_047()
            fr_data_048()
            fr_data_154_157()


if __name__ == "__main__":
    main()
