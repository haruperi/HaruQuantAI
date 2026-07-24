# Real-Time Feed Lifecycle — FEAT-DATA-12

Owns internal feed startup, bounded buffering, heartbeat, reconnection, gap
reconciliation, persisted state, and status evidence.

- Production files: buffer, contracts, heartbeat, reconnection, state, status.
- Requirements: FR-DATA-046–048.
- Usage evidence: `tests/data/usage/12_realtime_feeds.py`.
- Side effects: explicit source reads and Data-owned state writes.
