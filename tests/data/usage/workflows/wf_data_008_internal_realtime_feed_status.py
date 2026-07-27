"""WF-DATA-008: seed the internal feed with a genuine MT5 tick."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    FeedConfig,
    FeedStatusRequest,
    RawFeedEvent,
    ReconnectPolicy,
    get_tick_data,
    ingest_feed_event,
    read_feed_status,
    run_data_migrations,
    start_internal_feed,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

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


def main() -> None:
    """Execute the current feed harness with genuine provider evidence."""
    print(f"{WORKFLOW_ID} — Internal Real-Time Feed and Status")
    print("INPUT BOUNDARY — genuine MT5 tick enters the internal feed harness")

    # Stage 1 — Retrieve one genuine MT5 tick at the public read boundary.
    _stage(1)
    ticks = get_tick_data(market_request("ticks", timeframe=None, limit=1))
    tick = ticks.records[-1]

    with (
        tempfile.TemporaryDirectory(prefix="wf-data-008-") as directory,
        isolated_runtime(Path(directory)),
    ):
        request_id = generate_id("req")
        run_data_migrations(request_id)

        # Stage 2 — Start the bounded internal feed runtime.
        _stage(2)
        config = FeedConfig(
            feed_id="wf-data-008-mt5",
            source_id="mt5",
            symbol="EURUSD",
            data_kind="tick",
            source_capability="ticks",
            buffer_capacity=8,
            overflow_policy="drop_and_reconcile",
            heartbeat_timeout_seconds=30,
            reconnect_policy=ReconnectPolicy(
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
            RawFeedEvent(
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
            FeedStatusRequest(feed_id=config.feed_id, request_id=generate_id("req"))
        )
        assert accepted.accepted
        print("Feed state:", status.state, status.buffer_depth, status.gap_count)
    print("OUTPUT BOUNDARY — bounded FeedStatus from real MT5-derived evidence")


if __name__ == "__main__":
    main()
