# Artifact and Reference Catalog

`FEAT-DATA-18` owns the rebuildable SQLite index over source-authoritative reference
evidence and sidecar-authoritative dataset artifacts. It never grants trading
authority, invents reference metadata, or replaces a missing provider observation.

The feature activates `data_symbols`, `data_providers`, `data_market_sessions`,
`data_datasets`, `data_partition_files`, `data_fetch_log`, and
`data_quality_events`. All mutations execute through Data persistence transactions.
