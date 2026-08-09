# Replay Data Package

`FEAT-DATA-19` streams already-retrieved bounded market evidence in deterministic
source order with an explicit per-event `available_at` timestamp and no future
visibility. `stream_replay_events` never assumes a wall-clock "now": its required
`as_of` argument is the fail-closed consumer port standing in for Simulator's
not-yet-built Simulator clock — omitting it is a validation
error, never an inferred boundary.

`build_replay_package`/`parse_replay_package` construct and JSON-round-trip the
bounded declaration of what to replay (source, symbols, data kind, coverage window),
per the cross-domain contract-transport decision (D-1). No new persistence is owned
here; replay composes existing Data retrieval read-only.
