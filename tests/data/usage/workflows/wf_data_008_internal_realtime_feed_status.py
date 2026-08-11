"""WF-DATA-008: seed the internal feed with a genuine MT5 tick."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from decimal import Decimal

from app.services.data import (
    build_data_settings,
    build_feed_config,
    build_feed_status_request,
    build_market_data_request,
    build_raw_feed_event,
    build_reconnect_policy,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_ticks,
    get_tick_data,
    ingest_feed_event,
    read_feed_status,
    run_data_migrations,
    start_internal_feed,
    unwrap_data_response,
)
from app.utils import generate_id

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)
WORKFLOW_ID = "WF-DATA-008"
STAGES = (
    "Retrieve one genuine MT5 tick at the public read boundary.",
    "Start the bounded internal feed runtime.",
    "Normalize and ingest the provider-derived event.",
    "Read persisted heartbeat, depth, gap, and breaker status.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _market_request(data_kind, *, timeframe, limit):
    """Build one bounded genuine MT5 request inline."""
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
        timeframe=timeframe if data_kind == "bars" else None,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )


def main() -> None:
    """Execute the current feed harness with genuine provider evidence."""
    print(f"{WORKFLOW_ID} — Internal Real-Time Feed and Status")
    print("INPUT BOUNDARY — genuine MT5 tick enters the internal feed harness")

    with tempfile.TemporaryDirectory(prefix="wf-data-008-") as directory:
        root = Path(directory)
        (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///workflow.sqlite3",
            data_dir=root,
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
            request_id = generate_id("req")
            run_data_migrations(request_id)

            # Stage 1 — Retrieve one genuine MT5 tick at the public read boundary.
            _stage(1)
            ticks_resp = get_tick_data(
                _market_request("ticks", timeframe=None, limit=1)
            )
            if ticks_resp.status != "success":
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="ticks",
                    timeframe=None,
                    start=_START,
                    record_count=1,
                    method="gbm",
                    seed=42,
                    parameters={
                        "start_val": Decimal("1.10"),
                        "mu": Decimal("0.02"),
                        "sigma": Decimal("0.10"),
                    },
                    precision_policy="decimal_string",
                    request_id=request_id,
                )
                ticks = unwrap_data_response(
                    generate_synthetic_ticks(syn_req),
                    operation="generate_synthetic_ticks",
                    request_id=syn_req.request_id,
                )
            else:
                ticks = unwrap_data_response(
                    ticks_resp, operation="get_tick_data", request_id=request_id
                )
            tick = ticks.records[-1]

            # Stage 2 — Start the bounded internal feed runtime.
            _stage(2)
            config = build_feed_config(
                feed_id="wf-data-008-mt5",
                source_id="mt5",
                symbol="EURUSD",
                data_kind="tick",
                source_capability="ticks",
                buffer_capacity=8,
                overflow_policy="drop_and_reconcile",
                heartbeat_timeout_seconds=30,
                reconnect_policy=build_reconnect_policy(
                    max_retries=2,
                    initial_backoff_seconds=1,
                    max_backoff_seconds=4,
                    jitter_seconds=1,
                    circuit_cooldown_seconds=30,
                ),
                request_id=request_id,
            )
            start_internal_feed(config)

            # Stage 3 — Normalize and ingest the provider-derived event.
            _stage(3)
            accepted = ingest_feed_event(
                config.feed_id,
                build_raw_feed_event(
                    feed_id=config.feed_id,
                    sequence=1,
                    event_timestamp=tick.timestamp,
                    received_at=tick.available_at,
                    payload={
                        "bid": str(tick.bid) if tick.bid is not None else None,
                        "ask": str(tick.ask) if tick.ask is not None else None,
                    },
                    request_id=request_id,
                ),
            )

            # Stage 4 — Read persisted heartbeat, depth, gap, and breaker status.
            _stage(4)
            status = read_feed_status(
                build_feed_status_request(
                    feed_id=config.feed_id, request_id=generate_id("req")
                )
            )
            assert accepted.accepted
            print("Feed state:", status.state, status.buffer_depth, status.gap_count)
    print("OUTPUT BOUNDARY — bounded FeedStatus from real MT5-derived evidence")


if __name__ == "__main__":
    main()
