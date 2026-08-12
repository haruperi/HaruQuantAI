# Market Data — FEAT-DATA-01

Owns governed market, tick, spread, symbol, metadata, availability, and volume
retrieval, plus bounded Level-1, composite snapshot, categorized directory, and
exact-symbol quote evidence. Consumers import functions only from
`app.services.data`.

- Production files: `asset_classifier.py`, `directory_contracts.py`,
  `directory_projection.py`, `level1.py`, `market_directory.py`, `pipeline.py`,
  `requests.py`, `results.py`, `snapshot.py`, `symbol_discovery.py`,
  `symbol_metadata.py`, and `symbol_quotes.py`; `__init__.py` is internal package
  infrastructure.
- Requirements: `FR-DATA-006`–`007`, `030`–`033`, `035`, `039`, `103`–`104`,
  `107`, `190`–`191`, `203`, and `207`–`213`.
- Usage evidence: `tests/data/usage/features/01_market_data.py`.
- Side effects: approved read-only source calls and documented cache access.
- Directory quote projection treats non-positive provider ``last`` values
  as unavailable because MT5 commonly reports ``last=0`` for OTC instruments
  without an exchange last-trade field. Display price preference is the current
  Level-1 bid, then a genuine positive last trade, then the latest D1 close;
  missing quote or OHLC evidence remains ``None``.
