# Real-Time Feed Lifecycle and Market Streaming — FEAT-DATA-12

Owns internal feed startup, bounded buffering, heartbeat, reconnection, gap
reconciliation, persisted state/status evidence, and the canonical MT5 tick and
closed-bar streaming behavior consumed by transport bridges.

- Production files: buffer, contracts, heartbeat, reconnection, state, status,
  `mt5_ticks.py`, `mt5_bars.py`, and `subscriptions.py`.
- Public API: `build_market_stream_request` and `stream_market_data`, plus the
  existing feed lifecycle functions, through `app.services.data` only.
- Requirements: FR-DATA-046–048 and FR-DATA-154–157.
- Usage evidence: `tests/data/usage/features/12_realtime_feeds.py`.
- Side effects: explicit source reads and Data-owned state writes delegated to
  `data.persistence`.
- Boundary: Brokers owns MT5 transport/read DTOs; Data owns polling cadence,
  canonical tick/bar mapping, sequencing, heartbeat, fan-out, resume,
  backpressure, and cleanup. API owns no market-stream business behavior.
