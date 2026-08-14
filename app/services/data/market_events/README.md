# Market Events — FEAT-DATA-10

Owns internal feed startup, bounded buffering, heartbeat, reconnection, gap
reconciliation, persisted state/status evidence, and canonical one-second MT5
TCP snapshots consumed by transport bridges.

- Production files: buffer, contracts, heartbeat, reconnection, state, status,
  `mt5_ticks.py`, retired-live-bar guard `mt5_bars.py`, `mt5_snapshots.py`, and
  `subscriptions.py`.
- Public API: `build_market_stream_request`, `stream_market_data`,
  `build_market_snapshot_stream_request`, and `stream_market_snapshots`, plus
  the existing feed lifecycle functions, through `app.services.data` only.
- Requirements: FR-DATA-046–048, FR-DATA-154–157, and FR-DATA-190–191.
- Usage evidence: `tests/data/usage/features/10_market_events.py`.
- Side effects: explicit source reads and Data-owned state writes delegated to
  `data.persistence`.
- Boundary: Brokers owns the persistent MQL5 TCP receiver and versioned wire
  validation. Data owns symbol filtering, canonical quote mapping, freshness,
  sequencing, heartbeat, fan-out, resume, backpressure, and cleanup. Each
  snapshot stream acquires its exact symbol set through the Brokers public
  boundary and releases it deterministically when the stream closes. Closing
  the final stream therefore permits the Brokers/EA channel to pause tick reads
  immediately while preserving its authenticated control connection. The MT5
  Python package remains available for non-streaming control/history reads but
  is prohibited from live stream producers. API owns no acquisition behavior.
