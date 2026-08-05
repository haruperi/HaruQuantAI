# 01 — Entity Specs: Core (Utils, Brokers, Data, Indicators)

> **AUTHORITATIVE — target schema model.** Canonical for cross-domain schema
> structure and the target table/column model. Current-state feature registries remain
> in each owning package `README.md`; executable schema remains in the owning domain's
> migration definitions. Divergences are recorded in
> [05_reconciliation.md](05_reconciliation.md). See [README.md](README.md) for the full
> authority statement.

Conventions from [00_domain_relationship_map.md](00_domain_relationship_map.md) §8
apply to every table below. All tables are `STRICT`.

---

## Domain 1 — Utils (`util_`)

### Utils owns no tables — by design

`app/utils/` is the shared utility framework, imported by every domain. Giving it
write-ownership of state would invert the dependency direction of the whole system.
`docs/PROJECT.md` §5 has no Utils row for exactly that reason.

An earlier draft of this model defined seven `util_*` tables. **All are withdrawn.**
Each was either already owned elsewhere or actively harmful:

| Withdrawn | Why it is not needed |
|---|---|
| `util_logs` | `app/utils/logging/logger.py` writes through `_SafeRotatingFileHandler` to rotating files. A database log table would make the logger depend on Data, which depends on the logger — a cycle, and a poor fit for log volume. |
| `util_metrics` | Same dependency inversion. Operational metrics belong outside the transactional store. |
| `util_tasks` | Duplicates `data_update_jobs`, which already carries `next_run_at`, `interval_seconds`, `enabled`, `state`, `last_run_status`, `lease_owner`, `lease_expires_at`, and `recovery_state`. |
| `util_task_runs` | Duplicates `data_backfill_checkpoints`, which already records committed ranges, record counts, content hashes, and publication state per chunk. |
| `util_health_checks` | Health is computed on demand by `app/services/api/health/probes.py`. Storing a current-state snapshot invites serving a stale one. |
| `util_settings` | Bootstrap configuration is resolved from the central JSON/process sources and typed settings objects. Versioned, non-secret user and post-connection system settings share the UI/API-owned `api_settings` table; Utils remains stateless and cannot depend on Data. |
| `util_feature_flags` | No feature-flag mechanism exists in this system. The table described a capability that was never requested. |

Durable cross-domain audit is already `data_audit_events`.

The `util_` prefix stays **ratified but unused** (D1). Reserving it costs nothing and
avoids re-litigating namespace ownership if Utils ever does acquire state.

---

## Domain 2 — Brokers (`broker_`)

> Prefix `broker_` is ratified (D1) and recorded in `docs/ARCHITECTURE.md`.

### Brokers persists almost nothing — by design

`docs/PROJECT.md` §5 records Brokers persisted state as `Completed` by **verified
absence**: *"Brokers is a stateless passthrough; technical session state is in-memory
only and credentials are never persisted."* Decision **D10** upheld that.

An earlier draft of this model defined `broker_providers`, `broker_connections`,
`broker_accounts`, and `broker_connection_events`. All four are **withdrawn**:

| Withdrawn table | Why it is not needed |
|---|---|
| `broker_providers` | Provider capability and rate-limit policy is configuration, not state. It belongs in typed settings or the adapter registry, not in a table. |
| `broker_connections` | Connection and circuit-breaker state is in-memory by design (`_TransportCircuitBreaker`). Persisting it creates a recovery path that can resurrect a stale circuit state across restart. |
| `broker_accounts` | Balance, equity, and margin are **fetched live**. Persisting them creates a staleness and reconciliation problem the current design does not have. |
| `broker_connection_events` | Connection transitions are operational telemetry; they belong in the rotating application log, or in `data_audit_events` when they must be durable. |

**One safety control was lost with them.** `broker_connections` carried
`CHECK (environment <> 'production' OR enabled = 0)`, which made a production
connection structurally unstorable in the enabled state — a schema-level enforcement
of `AGENTS.md` §3 *No Live Action by Default*. That guarantee now rests entirely on
application code and the `ALLOW_LIVE_MUTATIONS` toggle. This is a real reduction in
structural safety, accepted as the price of keeping Brokers stateless.

### `broker_symbol_map`

The single exception, generated from migration step `001_broker_symbol_map_v1`.



```sql
CREATE TABLE broker_symbol_map (
    map_id TEXT PRIMARY KEY,
    provider_code TEXT NOT NULL,
    symbol_id TEXT NOT NULL,
    provider_symbol TEXT NOT NULL,
    contract_size_decimal TEXT NOT NULL DEFAULT '1',
    digits_override INTEGER,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (provider_code, provider_symbol, effective_from),
    UNIQUE (provider_code, symbol_id, effective_from)
) STRICT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_symbol_active ON broker_symbol_map(provider_code, symbol_id) WHERE enabled = 1 AND effective_to IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_symbol_reverse ON broker_symbol_map(provider_code, provider_symbol) WHERE enabled = 1 AND effective_to IS NULL;
```

`effective_from` / `effective_to` make the mapping **bitemporal**. A broker that renames an instrument mid-history must not retroactively rewrite what an earlier backtest traded, so a rename closes the old row and opens a new one.

Both partial unique indexes are enforcement, not optimisation: at most one active mapping per instrument, and at most one per provider symbol. A duplicate active mapping is how an order reaches the wrong instrument.

`provider_code` and `symbol_id` are plain values, not foreign keys. Brokers reaches Data through `app.services.data`, never through its schema.
## Domain 3 — Data (`data_`)

The highest-volume domain. Data also owns shared connection, locking, and migration
infrastructure (`AGENTS.md` §1 Domain Persistence Support).

### The catalog

Seven tables indexing artifacts written by `persistence/dataset_writer.py`. Generated
from migration step `006_data_catalog_v1` so the model cannot drift from the code.

#### `data_symbols`

```sql
CREATE TABLE data_symbols (
    symbol_id TEXT PRIMARY KEY,
    canonical_symbol TEXT NOT NULL UNIQUE,
    asset_class TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    quote_currency TEXT NOT NULL,
    digits INTEGER NOT NULL,
    tick_size_decimal TEXT NOT NULL,
    min_volume_decimal TEXT NOT NULL,
    max_volume_decimal TEXT NOT NULL,
    volume_step_decimal TEXT NOT NULL,
    contract_size_decimal TEXT NOT NULL DEFAULT '1',
    spec_json TEXT NOT NULL DEFAULT '{}',
    state TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
) STRICT;

CREATE INDEX IF NOT EXISTS idx_data_symbols_class ON data_symbols(asset_class, canonical_symbol);
```

Instrument reference data. `state` distinguishes an active instrument from a delisted one, so a backtest over a delisted symbol is a deliberate choice rather than an accident.

#### `data_providers`

```sql
CREATE TABLE data_providers (
    provider_id TEXT PRIMARY KEY,
    provider_code TEXT NOT NULL UNIQUE,
    provider_kind TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    trust_tier TEXT NOT NULL,
    rate_limit INTEGER NOT NULL DEFAULT 0,
    rate_window_seconds INTEGER NOT NULL DEFAULT 1,
    license_json TEXT NOT NULL DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
) STRICT;
```

`priority` and `trust_tier` drive deterministic provider selection when several sources cover one symbol. Without an explicit ordering the same backtest can pull different prices on different days.

#### `data_market_sessions`

```sql
CREATE TABLE data_market_sessions (
    session_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    session_name TEXT NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    open_time_utc TEXT NOT NULL,
    close_time_utc TEXT NOT NULL,
    is_trading INTEGER NOT NULL DEFAULT 1 CHECK (is_trading IN (0, 1)),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (symbol_id, session_name, day_of_week, effective_from)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_data_sessions_active ON data_market_sessions(symbol_id, day_of_week) WHERE effective_to IS NULL;
```

`effective_from` / `effective_to` make session definitions **bitemporal**. A backtest over 2019 must use 2019's session hours; using today's silently trades hours that did not exist.

#### `data_datasets`

```sql
CREATE TABLE data_datasets (
    dataset_id TEXT PRIMARY KEY,
    dataset_kind TEXT NOT NULL,
    owner_domain TEXT NOT NULL,
    symbol_id TEXT,
    timeframe TEXT,
    provider_id TEXT,
    producer_ref TEXT,
    root_path TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    normalization_version TEXT NOT NULL,
    timestamp_semantics TEXT NOT NULL DEFAULT 'bar_open',
    file_count INTEGER NOT NULL DEFAULT 0,
    total_rows INTEGER NOT NULL DEFAULT 0,
    total_bytes INTEGER NOT NULL DEFAULT 0,
    min_ts_utc INTEGER,
    max_ts_utc INTEGER,
    state TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (dataset_kind, symbol_id, timeframe, provider_id, producer_ref)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_data_datasets_lookup ON data_datasets(dataset_kind, symbol_id, timeframe);
```

One row per logical dataset — market data, indicator outputs, research features. `producer_ref` names the producing identity for derived datasets and is deliberately **not** a foreign key: Data must not depend on Indicators or Research.

`timestamp_semantics` is a column because mixing bar-open and bar-close stamps is a lookahead bug that silently inflates results. Declaring it per dataset makes the mismatch detectable at load.

#### `data_partition_files`

```sql
CREATE TABLE data_partition_files (
    file_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL UNIQUE,
    relative_path TEXT NOT NULL,
    format TEXT NOT NULL CHECK (format IN ('parquet', 'csv')),
    content_hash TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    byte_size INTEGER NOT NULL,
    min_ts_utc INTEGER NOT NULL,
    max_ts_utc INTEGER NOT NULL,
    schema_version TEXT NOT NULL,
    normalization_version TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    provenance_json TEXT NOT NULL DEFAULT '{}',
    license_json TEXT NOT NULL DEFAULT '{}',
    verify_state TEXT NOT NULL DEFAULT 'unverified',
    verified_at TEXT,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (dataset_id, relative_path),
    CHECK (max_ts_utc >= min_ts_utc)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_data_files_prune ON data_partition_files(dataset_id, min_ts_utc, max_ts_utc);

CREATE INDEX IF NOT EXISTS idx_data_files_bad ON data_partition_files(dataset_id) WHERE verify_state IN ('hash_mismatch', 'missing');

CREATE INDEX IF NOT EXISTS idx_data_files_hash ON data_partition_files(content_hash);
```

The artifact index. **One row per file written by `dataset_writer.save_market_data`**, populated from the `StorageManifest` that writer returns.

`idx_data_files_prune` on `(dataset_id, min_ts_utc, max_ts_utc)` is the hot path of every pinned read: it selects the files a query needs **without opening any of them**, replacing a directory walk plus N footer reads with one indexed range scan.

`artifact_id` mirrors the writer's `artifact-{sha256}` identity, so a file and its catalog row cannot disagree about which artifact they describe. `content_hash` plus `verify_state` make silent corruption detectable — a truncated write or bit rot changes the hash, and `hash_mismatch` blocks reads of that artifact rather than feeding corrupt prices into a backtest.

#### `data_fetch_log`

```sql
CREATE TABLE data_fetch_log (
    fetch_id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    symbol_id TEXT NOT NULL,
    data_kind TEXT NOT NULL,
    timeframe TEXT,
    range_start_utc INTEGER NOT NULL,
    range_end_utc INTEGER NOT NULL,
    rows_returned INTEGER NOT NULL DEFAULT 0,
    materialized INTEGER NOT NULL DEFAULT 0 CHECK (materialized IN (0, 1)),
    dataset_id TEXT,
    served_from TEXT NOT NULL,
    fetch_latency_ms INTEGER,
    state TEXT NOT NULL,
    error_code TEXT,
    request_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (range_end_utc >= range_start_utc),
    CHECK (materialized = 0 OR dataset_id IS NOT NULL)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_data_fetch_symbol ON data_fetch_log(symbol_id, data_kind, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_data_fetch_source ON data_fetch_log(served_from, started_at DESC);
```

Every broker fetch, materialised or not. `served_from` makes the cache hierarchy measurable: a backtest that believes it read pinned Parquet but actually hit the live broker is not reproducible, and this column is what surfaces that.

The final `CHECK` prevents claiming materialisation without naming the dataset it landed in.

#### `data_quality_events`

```sql
CREATE TABLE data_quality_events (
    event_id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL,
    dataset_id TEXT,
    file_id TEXT,
    fetch_id TEXT,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    ts_range_start INTEGER NOT NULL,
    ts_range_end INTEGER NOT NULL,
    affected_rows INTEGER NOT NULL DEFAULT 0,
    detail_json TEXT NOT NULL DEFAULT '{}',
    detected_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
) STRICT;

CREATE INDEX IF NOT EXISTS idx_data_quality_symbol ON data_quality_events(symbol_id, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_data_quality_severe ON data_quality_events(detected_at DESC) WHERE severity IN ('error', 'critical');
```

Because artifacts are immutable and content-addressed, a repair is a **new artifact**, not an `UPDATE`. The event row records which file was superseded and why; the replacement carries a new `content_hash`. Per `AGENTS.md` §3 "No Invented Data", an interpolated value stays traceable to the event that produced it.
### `data_migration_ledger`

**Code is authoritative for this table.** Transcribed verbatim from
`app/services/data/persistence/migrations.py`. This model does not propose a variant
and must not diverge — per `AGENTS.md` §5 this ledger governs every other migration in
the system, so a mismatch here would invalidate schema evolution everywhere.

```sql
CREATE TABLE data_migration_ledger (
    domain           TEXT NOT NULL,
    migration_id     TEXT NOT NULL,
    checksum         TEXT NOT NULL,
    applied_at_ns    TEXT NOT NULL CHECK (
        length(applied_at_ns) = 19
        AND applied_at_ns NOT GLOB '*[^0-9]*'
    ),
    PRIMARY KEY (domain, migration_id)
) STRICT;
```

An earlier draft of this model invented `step_id`, `sequence`, and `applied_at`. That
was a defect, corrected here: the ledger is keyed by `(domain, migration_id)`, not by a
synthetic step id, and stamps nanoseconds rather than ISO text.

`applied_at_ns` is `TEXT`, not `INTEGER`, and a second correction restores that. Under
`STRICT` an `INTEGER` column is a signed 64-bit value, which holds nanosecond epochs
comfortably — so the shipped choice is not a range workaround. It is a shape guarantee:
the `CHECK` fixes the value at exactly nineteen digits with no other characters, so a
truncated, sign-prefixed, or second-resolution stamp is rejected at write time rather
than silently ordering the ledger wrongly. An `INTEGER` column would accept all three.

Applied steps are immutable; a checksum mismatch blocks database access.

### `data_write_locks`

**Code is authoritative for this table.** Transcribed from
`app/services/data/persistence/locking.py`. Required by `AGENTS.md` §5, which mandates
explicit write-lock acquisition with leases and a strict busy-timeout policy for every
schema change.

```sql
CREATE TABLE data_write_locks (
    lock_name        TEXT    PRIMARY KEY,
    lease_owner      TEXT    NOT NULL,
    lease_token      TEXT    NOT NULL,
    acquired_at_ns   INTEGER NOT NULL,
    expires_at_ns    INTEGER NOT NULL,
    request_id       TEXT    NOT NULL,
    renewed_count    INTEGER NOT NULL DEFAULT 0
) STRICT;

CREATE INDEX idx_data_locks_expiry ON data_write_locks(expires_at_ns);
```

This table was absent from an earlier draft of the model — a correctness gap, since
the single-writer discipline in
[04_indexing_and_performance.md](04_indexing_and_performance.md) §7.3 depends on it.

`lease_token` is what makes lock release safe: a holder whose lease expired cannot
release a lock a second holder has since acquired, because the tokens differ.

---

### Operational and reference tables

Twelve further Data tables ship today, recorded here so the model omits nothing that
exists. Generated from their migration definitions.

#### `data_cache`

```sql
CREATE TABLE data_cache (
    key TEXT PRIMARY KEY,
    dataset_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    source_revision TEXT NOT NULL,
    raw_data_hash TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    normalization_version TEXT NOT NULL,
    request_id TEXT NOT NULL
) STRICT;
```

Versioned response cache. `raw_data_hash` plus `normalization_version` mean an entry is reused only when both the upstream bytes and the transform that shaped them are unchanged.

#### `data_audit_events`

```sql
CREATE TABLE data_audit_events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    domain TEXT NOT NULL,
    action TEXT NOT NULL,
    principal_id TEXT,
    request_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    causation_id TEXT,
    payload_json TEXT NOT NULL
) STRICT;
```

Durable cross-domain audit storage. Emitting domains own their payload fields; Data owns persistence. `causation_id` distinguishes what triggered an event from what it correlates with.

#### `data_source_attempts`

```sql
CREATE TABLE data_source_attempts (
    source_id TEXT NOT NULL,
    timestamp_ns TEXT NOT NULL CHECK ( length(timestamp_ns) = 19 AND timestamp_ns NOT GLOB '*[^0-9]*' ),
    request_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'FAILURE', 'BLOCKED')),
    error_code TEXT,
    PRIMARY KEY (source_id, timestamp_ns)
) STRICT;
```

Append-only attempt log behind the circuit breaker. `status` and `error_code` drive breaker transitions.

#### `data_source_state`

```sql
CREATE TABLE data_source_state (
    source_id TEXT PRIMARY KEY,
    readiness TEXT NOT NULL CHECK ( readiness IN ('disabled', 'staging', 'production') ),
    descriptor_revision TEXT NOT NULL,
    updated_at_ns TEXT NOT NULL CHECK ( length(updated_at_ns) = 19 AND updated_at_ns NOT GLOB '*[^0-9]*' ),
    request_id TEXT NOT NULL
) STRICT;
```

Current readiness per source. `descriptor_revision` pins which capability descriptor the verdict was computed against.

#### `data_update_jobs`

```sql
CREATE TABLE data_update_jobs (
    job_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    symbols_json TEXT NOT NULL,
    timeframes_json TEXT NOT NULL,
    data_kinds_json TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT,
    interval_seconds INTEGER,
    enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
    created_at TEXT NOT NULL,
    request_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK ( state IN ('created', 'running', 'stopped', 'failed', 'blocked') ),
    last_run_status TEXT CHECK ( last_run_status IN ('succeeded', 'failed', 'blocked') ),
    last_checkpoint TEXT,
    last_error TEXT,
    next_run_at TEXT,
    lease_owner TEXT,
    lease_expires_at TEXT,
    recovery_state TEXT NOT NULL CHECK ( recovery_state IN ('clean', 'required', 'recovered', 'blocked') ),
    environment TEXT
) STRICT;
```

Scheduled ingestion with leases. `lease_owner` and `lease_expires_at` prevent two workers claiming one job; `recovery_state` and `last_checkpoint` make an interrupted job resumable. Migration `008_data_jobs_environment` adds nullable `environment`; it is required and constrained by the application contract for exclusive weekly `economic_calendar` jobs and remains null for market-data jobs.

#### `data_backfill_checkpoints`

```sql
CREATE TABLE data_backfill_checkpoints (
    idempotency_key TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    committed_start TEXT NOT NULL,
    committed_end TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    checkpoint TEXT NOT NULL,
    artifact_temp TEXT NOT NULL,
    artifact_final TEXT NOT NULL,
    publication_state TEXT NOT NULL CHECK ( publication_state IN ('prepared', 'committed') ),
    request_id TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;
```

Per-chunk commit record keyed by idempotency key. `committed_start`/`committed_end` plus `content_hash` make a re-run provably a no-op.

#### `data_feeds`

```sql
CREATE TABLE data_feeds (
    feed_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    data_kind TEXT NOT NULL CHECK (data_kind IN ('ohlcv', 'tick', 'spread')),
    timeframe TEXT,
    source_capability TEXT NOT NULL,
    buffer_capacity INTEGER NOT NULL,
    overflow_policy TEXT NOT NULL CHECK ( overflow_policy IN ('halt', 'drop_and_reconcile', 'backpressure') ),
    heartbeat_timeout_seconds INTEGER NOT NULL,
    reconnect_policy_json TEXT NOT NULL,
    state TEXT NOT NULL CHECK ( state IN ('starting', 'running', 'stopped', 'failed', 'blocked') ),
    heartbeat_at TEXT,
    last_event_at TEXT,
    buffer_depth INTEGER NOT NULL,
    dropped_count INTEGER NOT NULL,
    gap_count INTEGER NOT NULL,
    reconnect_count INTEGER NOT NULL,
    breaker_state TEXT NOT NULL CHECK ( breaker_state IN ('closed', 'open', 'half_open') ),
    breaker_opened_at TEXT,
    drift_ms INTEGER,
    last_error TEXT,
    request_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
) STRICT;
```

Streaming feed lifecycle. `dropped_count` and `gap_count` are separate from `reconnect_count`, so a feed that reconnected cleanly is distinguishable from one that lost data.

#### `data_economic_events`

```sql
CREATE TABLE data_economic_events (
    event_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    country TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    original_scheduled_at TEXT NOT NULL,
    impact INTEGER NOT NULL CHECK (impact BETWEEN 1 AND 3),
    actual TEXT,
    forecast TEXT,
    previous TEXT,
    revised_previous TEXT,
    provider TEXT NOT NULL,
    source_url TEXT,
    first_seen_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    request_id TEXT NOT NULL,
    provider_definition_id TEXT
) STRICT;
```

Calendar events use a provider-qualified deterministic `event_id`. Exact provider
values remain strings in `actual`, `forecast`, and `previous`; this preserves suffixes
without parallel raw/normalized columns. `original_scheduled_at` is immutable when a
provider reschedules an event.

#### `data_economic_event_definitions`

```sql
CREATE TABLE data_economic_event_definitions (
    provider TEXT NOT NULL,
    provider_definition_id TEXT NOT NULL,
    country TEXT NOT NULL,
    title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_original TEXT,
    source_latest TEXT,
    measures TEXT,
    effect TEXT,
    frequency TEXT,
    also_called TEXT,
    event_type TEXT,
    first_seen_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_verified_at TEXT NOT NULL,
    request_id TEXT NOT NULL,
    PRIMARY KEY (provider, provider_definition_id),
    UNIQUE (provider, source_url)
) STRICT;
```

Definition-level specifications are normalized away from scheduled occurrences.
Only verified provider text is stored; unavailable values remain null. Occurrences
join through `provider_definition_id`, and reconciliation requires one exact
title/country match.

#### `data_economic_calendar_coverage`

```sql
CREATE TABLE data_economic_calendar_coverage (
    provider TEXT NOT NULL,
    range_start TEXT NOT NULL,
    range_end TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('complete', 'partial')),
    source_revision TEXT NOT NULL,
    synchronized_at TEXT NOT NULL,
    request_id TEXT NOT NULL,
    PRIMARY KEY (provider, range_start, range_end),
    CHECK (range_start < range_end)
) STRICT;
```

Coverage is explicit because an empty event query does not prove missing data. Public
calendar retrieval checks these intervals before any provider request and acquires
only uncovered ranges.

#### `data_research_sources`

```sql
CREATE TABLE data_research_sources (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    asset_scope_json TEXT NOT NULL,
    issuer_scope_json TEXT NOT NULL,
    language TEXT NOT NULL,
    event_at TEXT,
    published_at TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    available_at TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    previous_document_id TEXT,
    original_hash TEXT NOT NULL,
    normalized_hash TEXT NOT NULL,
    original_content BLOB NOT NULL,
    normalized_text TEXT NOT NULL,
    license_id TEXT NOT NULL,
    retention_until TEXT NOT NULL,
    trust_status TEXT NOT NULL,
    manipulation_status TEXT NOT NULL,
    injection_status TEXT NOT NULL,
    currency TEXT,
    unit TEXT,
    provenance_json TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (source_id, external_id, normalized_hash)
) STRICT;
```

Externally sourced documents with their original bytes. `original_hash` proves what arrived and `normalized_hash` what the pipeline made of it, so a normalisation change is detectable without re-fetching. `available_at` is when the document became *knowable* — using `published_at` instead is how look-ahead enters a fundamental strategy.

#### `data_runtime_records`

```sql
CREATE TABLE data_runtime_records (
    namespace TEXT NOT NULL,
    collection_name TEXT NOT NULL,
    record_key TEXT NOT NULL,
    partition_key TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    codec_kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (namespace, collection_name, record_key),
    UNIQUE (namespace, collection_name, partition_key, sequence_number)
) STRICT;
```

Generic keyed runtime store. `revision` carries `CHECK (revision > 0)` and the composite unique key orders records within a partition, so a compare-and-swap write cannot silently reorder history.

#### `data_research_observations`

```sql
CREATE TABLE data_research_observations (
    observation_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    observation_period TEXT NOT NULL,
    value_json TEXT NOT NULL,
    unit TEXT,
    published_at TEXT NOT NULL,
    available_at TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    previous_observation_id TEXT,
    content_hash TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    trust_status TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE ( source_id, series_id, observation_period, content_hash )
) STRICT;
```

Extracted values, kept separate from the source document so a re-extraction produces new observations without rewriting the evidence they came from.

#### `data_verified_research_sources`

```sql
CREATE TABLE data_verified_research_sources (
    source_id TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    external_record_id TEXT NOT NULL,
    fixture_sha256 TEXT NOT NULL,
    environments_json TEXT NOT NULL,
    license_policy TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (source_id, parser_version)
) STRICT;
```

The allow-list of sources cleared for use. Absence is a denial.

---
## Domain 4 — Indicators (`indicator_`)

> Prefix `indicator_` is ratified (D1) and recorded in `docs/ARCHITECTURE.md`.

Generated from migration step `001_indicator_schema_v1`. Computed series are not
stored in the database; `indicator_materializations` records the artifact reference.

### `indicator_definitions`

```sql
CREATE TABLE indicator_definitions (
    definition_id TEXT PRIMARY KEY,
    indicator_code TEXT NOT NULL,
    version TEXT NOT NULL,
    category TEXT NOT NULL,
    formula_hash TEXT NOT NULL,
    param_schema_json TEXT NOT NULL,
    output_names_json TEXT NOT NULL,
    lookback_bars INTEGER NOT NULL,
    is_causal INTEGER NOT NULL DEFAULT 1 CHECK (is_causal IN (0, 1)),
    state TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (indicator_code, version)
) STRICT;

CREATE INDEX idx_indicator_defs_code ON indicator_definitions(indicator_code, version);

CREATE INDEX idx_indicator_defs_lookahead ON indicator_definitions(indicator_code) WHERE is_causal = 0;
```

`formula_hash` is computed over the implementation. If the formula changes the hash changes, forcing a new version and invalidating every materialisation built from it. Without this, a silent formula fix retroactively rewrites backtest history.

`is_causal = 0` marks an indicator that reads future bars — a centred moving average, a zig-zag. Legitimate for research and catastrophic in a live signal path. As a column with its own partial index, Strategy can reject them structurally rather than by convention.

### `indicator_param_sets`

```sql
CREATE TABLE indicator_param_sets (
    param_set_id TEXT PRIMARY KEY,
    definition_id TEXT NOT NULL,
    params_json TEXT NOT NULL,
    params_hash TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    period INTEGER GENERATED ALWAYS AS (json_extract(params_json, '$.period')) VIRTUAL,
    source_field TEXT GENERATED ALWAYS AS (json_extract(params_json, '$.source')) VIRTUAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (definition_id, params_hash)
) STRICT;

CREATE INDEX idx_indicator_params_period ON indicator_param_sets(definition_id, period);
```

The JSON-payload pattern from [00](00_domain_relationship_map.md) §8. `params_json` stays free-form; `period` and `source_field` are extracted into indexed generated columns, so the common query does not pay `json_extract` per row.

### `indicator_materializations`

```sql
CREATE TABLE indicator_materializations (
    materialization_id TEXT PRIMARY KEY,
    definition_id TEXT NOT NULL,
    param_set_id TEXT NOT NULL,
    symbol_id TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    source_dataset_id TEXT,
    source_data_hash TEXT NOT NULL,
    formula_hash TEXT NOT NULL,
    covered_from_utc INTEGER NOT NULL,
    covered_to_utc INTEGER NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL,
    built_at TEXT,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (definition_id, param_set_id, symbol_id, timeframe),
    CHECK (covered_to_utc >= covered_from_utc)
) STRICT;

CREATE INDEX idx_indicator_mat_stale ON indicator_materializations(symbol_id, timeframe) WHERE state IN ('stale', 'invalidated');

CREATE INDEX idx_indicator_mat_lookup ON indicator_materializations(definition_id, param_set_id) WHERE state = 'ready';
```

Computed series live in an artifact; this table holds the reference. Two hashes drive invalidation: `source_data_hash` covers the underlying bars, so a repair that rewrites them makes the derivation provably stale; `formula_hash` is copied at build time, so a formula fix invalidates every materialisation rather than silently changing what a stored series means.

---
## Entity count — this file

| Domain | Tables | Bulk rows in SQLite |
|---|---|---|
| Utils | 0 | none — stateless by design |
| Brokers | 1 | none — stateless by design (D10) |
| Data | 21 | **none — catalog only** |
| Indicators | 3 | **none — catalog only** |
| **Total** | **25** | |

Next: [02_entity_specs_execution.md](02_entity_specs_execution.md)
