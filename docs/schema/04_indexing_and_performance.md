# 04 — Production Indexing & Performance

> **AUTHORITATIVE — target schema model.** Canonical for cross-domain schema
> structure and the target table/column model. Current-state feature registries remain
> in each owning package `README.md`; executable schema remains in the owning domain's
> migration definitions. Divergences are recorded in
> [05_reconciliation.md](05_reconciliation.md). See [README.md](README.md) for the full
> authority statement.

---

## 1. Connection baseline

Applied on every connection open, before any statement.

```sql
PRAGMA journal_mode   = WAL;          -- readers never block the writer
PRAGMA synchronous    = NORMAL;       -- WAL-safe; FULL costs ~10x on ingest
PRAGMA foreign_keys   = ON;           -- OFF by default in SQLite; must be set per connection
PRAGMA busy_timeout   = 5000;         -- SQLITE_BUSY_TIMEOUT_SECONDS (AGENTS.md §5)
PRAGMA cache_size     = -262144;      -- 256 MB page cache (negative = KiB)
PRAGMA mmap_size      = 1073741824;   -- 1 GB memory-mapped I/O
PRAGMA temp_store     = MEMORY;
PRAGMA wal_autocheckpoint = 4000;     -- ~16 MB at 4 KiB pages
PRAGMA analysis_limit = 1000;         -- bounded ANALYZE
PRAGMA optimize;                      -- on connection CLOSE, not open
```

**Notes that matter.**

- `foreign_keys = ON` is per-connection and defaults **off**. Every `REFERENCES`
  clause in this design is inert on a connection that omits it. This is the single
  most commonly missed line in SQLite deployments.
- `synchronous = NORMAL` under WAL risks losing the last transaction on OS crash,
  not corruption. Because no bulk ingest passes through SQLite any more, there is
  little left to gain from `NORMAL`; use `FULL` on the `trading_*` and `risk_*` write
  path, where a lost fill is a real financial discrepancy rather than a re-fetchable
  row.
- `PRAGMA optimize` belongs on close. Running it on open adds latency to every
  connection for no benefit.

### Per-workload overrides

| Workload | Overrides |
|---|---|
| Catalog write | `synchronous=FULL` — volume is ~1 row per symbol-month, so durability is free |
| Live execution | `synchronous=FULL`, `busy_timeout=30000` |
| Backtest read | `query_only=ON` — bars come from Parquet, so SQLite serves catalog lookups only |
| Migration | `synchronous=FULL`, exclusive write lock (`AGENTS.md` §5) |

---

## 2. Artifact layout (the hypertable substitute)

> **Rewritten in Phase 4A to match `persistence/dataset_writer.py`.** An earlier
> version of this section specified Hive `year=`/`month=` partitioning, `zstd` level 3,
> and `DECIMAL(18,8)` prices. The shipped writer does none of those. Rather than change
> a working write path to match a document, the document now describes what ships — and
> one of the three turns out to be unnecessary anyway.

### 2.1 What the writer does

`save_market_data` writes **one artifact plus one sidecar manifest**, atomically:

```
temp file  →  fsync  →  sha256  →  os.replace()  →  manifest written  →  os.replace()
```

| Property | Value |
|---|---|
| Identity | `artifact-{sha256}` — content-addressed |
| Path | caller-supplied `relative_path`; **no directory partitioning** |
| Format | `parquet` or `csv` |
| Compression | pyarrow default |
| Prices | `Decimal` serialised to `str` |
| Sidecar | `StorageManifest` JSON beside the file |

### 2.2 Why directory partitioning is unnecessary here

Hive `year=`/`month=` layout exists so that a reader **without an index** can prune by
path. `idx_data_files_prune` on `(dataset_id, min_ts_utc, max_ts_utc)` does that job
strictly better: it prunes by the data's actual time range rather than by a filename,
and it works wherever the file sits.

With a catalog, partitioning by directory buys nothing and costs a rename convention
that the writer would have to enforce. The flat content-addressed layout is sufficient.

**What is lost:** an external tool pointed at the artifact tree — DuckDB, a bare
pyarrow dataset — cannot prune without consulting the catalog. That is the price of
this simplification and it is real.

### 2.3 Prices as strings

`Decimal → str` is **safe**: no float precision loss, which is the property that
matters for money (`ARCHITECTURE.md` L648). It costs numeric predicate pushdown on
price columns and some file size, since strings compress less well than a decimal
logical type.

The canonical policy remains decimal strings. A fixed Parquet `DECIMAL(18,8)` would
recover both properties but would also introduce a scale and overflow contract that
the current source and dataset schemas do not define. Native decimal logical types are
therefore excluded until bounded per-field precision and scale metadata is ratified;
this is an accepted predicate-pushdown trade-off, not an open schema-programme item.

### 2.4 Immutability

Content-addressing makes artifacts immutable by construction: a changed byte is a
changed hash, which is a different artifact. There is no `sealed` flag because there is
nothing to seal — an artifact is never rewritten in place. A repair produces a new
artifact and a `data_quality_events` row naming what it superseded.

### 2.5 Retention

| Dataset kind | Retention | Rationale |
|---|---|---|
| `tick`, `candle` | Indefinite | Expensive to re-source; brokers age out history |
| `indicator` | Purge after 6 months | Deterministically recomputable from bars plus `formula_hash` |
| `feature` | Purge on study conclusion | Regenerable from the feature spec |
| `equity_curve` | Retain with the run | Small, and reruns are expensive |

Purging sets `data_datasets.state = 'purged'` and deletes the files; the catalog row
survives so a later reader learns the data *existed* and how to rebuild it, rather than
silently finding nothing.

---

## 3. Market-data read paths

### 3.1 The two-step read

```sql
-- Step 1: which artifacts cover this range?  (SQLite, sub-millisecond)
SELECT f.relative_path, f.content_hash, f.format, f.verify_state
FROM data_partition_files f
JOIN data_datasets d ON d.dataset_id = f.dataset_id
WHERE d.dataset_kind = 'candle'
  AND d.symbol_id = ? AND d.timeframe = ?
  AND d.state = 'ready'
  AND f.max_ts_utc >= ? AND f.min_ts_utc <= ?
ORDER BY f.min_ts_utc;
```

Served by `idx_data_datasets_lookup` then `idx_data_files_prune`. The overlap predicate
is `f.max >= start AND f.min <= end` — standard interval intersection. Writing it as
`f.min_ts_utc BETWEEN ? AND ?` is the common bug: it drops the artifact that *starts*
before the window and extends into it.

```python
# Step 2: read only those artifacts
import pyarrow.dataset as ds
table = ds.dataset(paths, format="parquet").to_table(
    columns=["timestamp", "open", "high", "low", "close", "volume"],
)
```

Column projection still applies. Row-level time filtering happens after load, because
prices and timestamps are strings — see §2.3.

### 3.2 Live read (no catalog, no disk)

```
strategy → app.services.data → MT5 → in-memory records
```

Nothing is written. `data_fetch_log` records `served_from = 'broker'`,
`materialized = 0`. This is the default path for live and paper trading.

### 3.3 Integrity gate before every pinned read

```sql
SELECT COUNT(*) FROM data_partition_files
WHERE dataset_id = ? AND verify_state IN ('hash_mismatch','missing');
```

Non-zero blocks the read. `idx_data_files_bad` is partial and **empty in normal
operation**, so the check costs an empty-B-tree probe. Per `AGENTS.md` §3 Fail-Closed,
an unverifiable artifact is a blocking condition, not a warning.

### 3.4 Coverage question: "do I need to fetch?"

```sql
SELECT MIN(min_ts_utc) AS have_from, MAX(max_ts_utc) AS have_to,
       SUM(row_count) AS rows, COUNT(*) AS artifacts
FROM data_partition_files
WHERE dataset_id = ? AND verify_state <> 'missing';
```

One aggregate over a handful of rows answers what would otherwise need a `MIN`/`MAX`
over every stored bar.

### 3.5 Catalog rebuild

Because the sidecar manifests are authoritative (D8), the catalog is disposable:

```sql
DELETE FROM data_partition_files;
DELETE FROM data_datasets;
-- rescan the artifact tree, reading each StorageManifest sidecar
```

Every column except `verify_state` and `verified_at` is reconstructed from the
manifests; those two are index-local operational state and reset to `unverified`.
**A column that cannot be rebuilt this way must not be added to the catalog** — that
constraint is what keeps D8's guarantee true.

---

## 4. Execution pipeline query paths

Latency-critical. Every one of these must be an index seek.

### 4.1 Open orders for an account

```sql
SELECT * FROM trading_orders
WHERE account_id = ? AND symbol_id = ?
  AND state IN ('pending_new','new','partially_filled','pending_cancel');
```

Served by the partial index `idx_trading_orders_open`. The partial predicate keeps
the index at open-order cardinality (tens of rows) rather than total-order
cardinality (millions). A full index on `state` would be ~1000× larger and mostly
terminal rows nobody queries.

### 4.2 Position lookup

```sql
SELECT * FROM trading_positions
WHERE account_id = ? AND symbol_id = ? AND direction = ? AND state = 'open';
```

`idx_trading_pos_open` is a partial **unique** index — the seek is O(log n) over an
index containing only open positions, and it simultaneously enforces the netting
invariant.

### 4.3 Risk admission check

```sql
SELECT * FROM risk_admission_decisions
WHERE decision_id = ? AND consumed_at IS NULL AND expires_at > ?;
```

PK seek plus two predicate filters. `idx_risk_admission_open` covers the sweep for
expiring unconsumed approvals.

### 4.4 Active policy resolution

```sql
SELECT * FROM risk_policies
WHERE scope_level = ? AND scope_key = ? AND runtime_profile = ? AND state = 'active';
```

`idx_risk_policy_active` is partial unique — one seek, guaranteed at most one row.
The uniqueness is the correctness property; the speed is a side effect.

### 4.5 Kill-switch check (runs before every order)

```sql
SELECT 1 FROM risk_kill_switches
WHERE state = 'tripped'
  AND ((scope_level='global')
    OR (scope_level='account'  AND scope_key = ?)
    OR (scope_level='strategy' AND scope_key = ?)
    OR (scope_level='symbol'   AND scope_key = ?))
LIMIT 1;
```

`idx_risk_kill_tripped` is partial on `state = 'tripped'`. In normal operation that
index is **empty**, so the check costs a single empty-B-tree probe — effectively
free. This is the design goal: the safety check that runs most often should cost
least when nothing is wrong.

### 4.6 Event append (optimistic concurrency)

```sql
INSERT INTO trading_events (event_seq, event_id, scope_key, aggregate_version, ...)
VALUES (NULL, ?, ?, ?, ...);
-- UNIQUE(scope_key, aggregate_version) raises SQLITE_CONSTRAINT on a concurrent writer
```

`event_seq INTEGER PRIMARY KEY` appends at the B-tree's right edge — the cheapest
insert SQLite offers, with no page splits mid-tree.

---

## 5. Full index catalogue

### 5.1 Catalog & time-ordered indexes

No `WITHOUT ROWID` bulk tables remain — the series they held are Parquet. What is left
is the catalog that finds those files, plus the system logs that stay in SQLite.

| Index | Table | Columns | Purpose |
|---|---|---|---|
| `idx_data_files_prune` | `data_partition_files` | `dataset_id, min_ts_utc, max_ts_utc` | **File selection by time range** — the hottest catalog query |
| `idx_data_files_hash` | `data_partition_files` | `content_hash` | Content-addressed lookup; detects duplicate artifacts |
| `idx_data_files_bad` | `data_partition_files` | `dataset_id` partial `verify_state IN ('hash_mismatch','missing')` | Integrity gate; empty when healthy |
| `idx_data_datasets_lookup` | `data_datasets` | `dataset_kind, symbol_id, timeframe` partial `state='ready'` | Dataset resolution |
| `idx_agentic_spans_bucket` | `agentic_trace_spans` | `bucket_month, agent_id` | Trace browse |
| `idx_api_audit_bucket` | `api_audit_log` | `bucket_month, actor_kind` | Audit browse |

`idx_data_files_prune` is the single most important index in the design. Every
market-data read begins with it, and it is what makes the catalog cheaper than a
directory walk.

### 5.2 Partial indexes (hot-subset only)

These carry most of the performance benefit. Each stays small because it indexes only
the rows anyone actually queries.

| Index | Predicate | Purpose |
|---|---|---|
| `idx_trading_orders_open` | `state IN (open states)` | Open-order sweep |
| `idx_trading_pos_open` | `state='open'` | **Unique** — netting invariant |
| `idx_risk_kill_tripped` | `state='tripped'` | Empty when healthy |
| `idx_risk_policy_active` | `state='active'` | **Unique** — one policy per scope |
| `idx_risk_admission_open` | `consumed_at IS NULL AND verdict IN (...)` | Unconsumed approvals |
| `idx_risk_checks_breach` | `passed=0` | Breach analysis |
| `idx_portfolio_alloc_active` | `is_active=1` | **Unique** — one allocation |
| `idx_agentic_ckpt_terminal` | `is_terminal=1` | **Unique** — no resume after terminal |
| `idx_agentic_spans_denied` | `outcome='refused'` | Denial audit |
| `idx_agentic_llm_breach` | `within_ceiling=0` | Budget breach |
| `idx_api_keys_lookup` | `revoked_at IS NULL` | Auth hot path |
| `idx_api_audit_denied` | `outcome='denied'` | Security monitoring |
| `idx_opt_trials_pending` | `state='pending'` | Trial dispatch |
| `idx_sim_runs_active` | `state IN ('queued','running')` | Run scheduler |
| `idx_sim_sessions_expiry` | `status IN ('active','expired')` | Playback-session expiry and cleanup |

Six of these are **unique partial indexes enforcing a business invariant**. That is
their primary job; query acceleration is secondary.

### 5.3 Covering indexes

Where the index alone answers the query, avoiding a table lookup:

```sql
CREATE INDEX idx_analytics_trades_cover
    ON analytics_trade_analysis(strategy_version_id, exit_at DESC, net_pnl_decimal, r_multiple_decimal);

CREATE INDEX idx_trading_fills_cover
    ON trading_fills(order_id, sequence, quantity_decimal, price_decimal, commission_decimal);

CREATE INDEX idx_equity_cover
    ON analytics_equity_curves(scope_level, scope_key, period_end_utc,
                               max_drawdown_percent_decimal, end_equity_decimal);
```

Verify with `EXPLAIN QUERY PLAN` — look for `USING COVERING INDEX`. Without that
phrase the extra columns are pure overhead and should be dropped.

### 5.4 Expression / generated-column indexes

```sql
-- date-truncated grouping without a scan
CREATE INDEX idx_trades_day ON analytics_trade_analysis(
    strategy_version_id, substr(exit_at, 1, 10));
```

The `substr(exit_at,1,10)` index works precisely because timestamps are ISO-8601
text — the first ten characters are the date. Epoch integers would need a
`date(ts,'unixepoch')` expression index instead.

---

## 6. JSON access pattern

**Never** filter on `json_extract` at read time on a large table:

`STORED` would duplicate the value in the table for a marginal gain; `VIRTUAL` plus
an index gives the seek without the duplication.

Promote a JSON key to a generated column when it is filtered or joined on. Leave it
in JSON when it is only ever read as part of the whole payload.

### 6.1 Indicators

Indicators owns no current table or index. The indexes introduced for the
legacy empty support schema by `001_indicator_schema_v1` were removed with
their tables by `002_remove_unused_indicator_support_schema`. Indicator
calculation performance is governed by in-memory vectorized execution and the
budgets documented in the owning Indicators README.

---

## 7. Write-path throughput

### 7.1 Parquet write, then catalog commit

Bulk writes no longer go through SQLite. The ordering is what matters:

```python
# 1. Write and fsync the Parquet file FIRST
manifest = save_market_data(request)      # writes artifact + sidecar atomically

# 2. THEN commit the catalog row in one transaction
conn.execute("BEGIN IMMEDIATE")
conn.execute("INSERT INTO data_partition_files (...) VALUES (...)", (..., manifest.content_hash, ...))
conn.execute("UPDATE data_datasets SET file_count=..., total_rows=..., "
             "max_ts_utc=..., updated_at=? WHERE dataset_id=?", (...))
conn.execute("COMMIT")
```

**Never the reverse.** A catalog row pointing at a file that does not exist is a
fail-closed read on the next query. An orphan file with no catalog row is invisible and
harmless, and a reconciliation sweep reclaims it. Write-then-record makes the failure
mode the recoverable one.

`os.replace` gives atomic visibility — a reader never sees a half-written Parquet at
the final path. Writing directly to `final_path` breaks that guarantee.

### 7.2 Catalog write volume

The catalog receives roughly one row per symbol-month. Ten symbols ingesting M1 bars
generate ~120 catalog inserts per year. At that rate every SQLite write-throughput
concern from the previous design disappears — `synchronous=FULL` everywhere costs
nothing measurable.

The transactions that still matter are `trading_*` and `risk_*`, which were never
bulk paths.

### 7.3 Single-writer discipline

SQLite permits one writer at a time. Under WAL, readers proceed concurrently. The
design assumes:

- One writer process per database file, coordinated by `data_write_locks`
  (`AGENTS.md` §5).
- Unlimited concurrent readers.
- Write batching at the application layer, not lock contention at the SQLite layer.

`busy_timeout` handles incidental contention. It is not a substitute for a
single-writer architecture — relying on it under sustained concurrent writes produces
retry storms.

---

## 8. Statistics and maintenance

```sql
-- Weekly, all tables
PRAGMA analysis_limit = 1000;
PRAGMA optimize;

-- Monthly — now cheap, since the database is state + catalog only
VACUUM;

-- Integrity, before backup
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

`VACUUM` was previously an outage on a multi-GB tick database. With bulk series in
Parquet the SQLite file should stay in the tens-to-hundreds of MB, so `VACUUM`
completes in seconds and can run on a normal maintenance window.

### Catalog rebuild

Because the sidecar manifests are authoritative (D8), the catalog is disposable:

```sql
DELETE FROM data_partition_files;
DELETE FROM data_datasets;
-- then rescan the artifact tree, reading each StorageManifest sidecar
```

A rebuild restores every column except `verify_state` and `verified_at`,
which are index-local operational state and reset to `unverified`. Treat a corrupt
catalog as a rebuild, never as data loss.

### Parquet-side maintenance

The catalog cannot detect drift on its own — it must be checked against the files:

```python
# Periodic sweep: does every catalog row still resolve, and does the hash match?
for row in conn.execute("SELECT file_id, relative_path, content_hash "
                        "FROM data_partition_files"):
    state = ("missing" if not os.path.exists(path)
             else "verified" if sha256_file(path) == row["content_hash"]
             else "hash_mismatch")
    conn.execute("UPDATE data_partition_files SET verify_state=?, verified_at=? "
                 "WHERE file_id=?", (state, now_iso(), row["file_id"]))
```

Every artifact is checked: content-addressing means none is expected to change. A
`hash_mismatch` should raise a `data_quality_events` row at `critical` and block reads
of that dataset until resolved.

Orphan reclamation is the other periodic job: an artifact written but never catalogued
(a crash between the two commits) is invisible to readers and reclaimable by comparing
the artifact tree against `data_partition_files`. `idx_data_files_hash` makes the
reverse check — a catalogued artifact that no longer exists — a single indexed lookup.

`PRAGMA foreign_key_check` is worth running in CI. It catches violations that
accumulated while `foreign_keys` was off on some connection.

---

## 9. Expected performance envelope

Indicative figures for a single-node deployment, NVMe SSD, 16 GB RAM. Measure before
relying on any of them.

| Operation | Scale | Target |
|---|---|---|
| Catalog file selection (SQLite) | ~12 rows | < 0.3 ms |
| Integrity gate (`idx_data_files_bad`) | 0 rows | < 0.05 ms |
| Coverage aggregate | ~120 rows | < 1 ms |
| Bar range read, 1 month Parquet | 43k rows | < 40 ms |
| Bar range read, 1 year Parquet | 370k rows | < 300 ms |
| Tick range read, 1 month Parquet | 10M rows | < 2 s |
| Live bar fetch from MT5 | 1k bars | 20–200 ms (network) |
| Open-order lookup | ~10 rows | < 0.5 ms |
| Kill-switch check | 0 rows | < 0.05 ms |
| Position lookup | 1 row | < 0.2 ms |
| Risk admission write | 1 row | < 2 ms (`synchronous=FULL`) |
| Parquet write, 1 symbol-month M1 | 43k rows | < 500 ms incl. fsync |

Parquet figures assume default compression, column projection to the OHLC columns, and warm
page cache. Cold-cache first reads are roughly 2–3× slower.

### When SQLite stops being the right answer

Migrate to Postgres/TimescaleDB when any of these hold:

1. Sustained concurrent writers > 1 (SQLite is fundamentally single-writer).
2. The **catalog** itself outgrows SQLite — which now needs ~10⁵ datasets to happen,
   since bulk rows left. Parquet volume is no longer a SQLite concern at all.
3. Cross-machine access is required (SQLite over a network filesystem is unsafe —
   file locking is unreliable on NFS/SMB).
4. Sub-millisecond p99 needed on concurrent mixed read/write.

Moving bulk series to Parquet pushes conditions 1 and 2 far out: SQLite now holds
system state and a small catalog, which is the workload it is genuinely best at.
Its zero network hop is a latency *advantage* over Postgres here, not a compromise.

---

## 10. Verification

```sql
-- Every listed index exists
SELECT name, tbl_name, partial FROM sqlite_master WHERE type='index' ORDER BY tbl_name;

-- No table scans on hot paths
EXPLAIN QUERY PLAN SELECT ...;   -- expect SEARCH, never SCAN

-- Index size audit (which indexes are worth their cost)
SELECT name, SUM(pgsize) AS bytes FROM dbstat WHERE name LIKE 'idx_%'
GROUP BY name ORDER BY bytes DESC;

-- Unused indexes: cross-check against query logs before dropping
```

`dbstat` requires the `SQLITE_ENABLE_DBSTAT_VTAB` compile option, present in most
CPython builds. If unavailable, fall back to file-size deltas around index creation.
