# 00 — High-Level Domain Relationship Map

> **AUTHORITATIVE — target schema model.** Canonical for cross-domain schema
> structure and the target table/column model. Current-state feature registries remain
> in each owning package `README.md`; executable schema remains in the owning domain's
> migration definitions. Divergences are recorded in
> [05_reconciliation.md](05_reconciliation.md). See [README.md](README.md) for the full
> authority statement.
**Target engine:** SQLite **3.37.0+** — the binding requirement is `STRICT` tables
(3.37.0). Generated columns need 3.31, `json_valid` 3.9, partial indexes 3.8,
`WITHOUT ROWID` 3.8.2, so `STRICT` sets the floor. Verified: the full DDL executes on
SQLite 3.37.2.
**Design basis:** `docs/ARCHITECTURE.md` L645–651 (Data Models & Schema Management).

---

## 0. Storage tiers — SQLite is not the data store

**No bulk numeric series is stored in SQLite.** The database holds system state and a
catalog of what exists elsewhere. Three tiers:

| Tier | Holds | Medium |
|---|---|---|
| **Broker (MT5)** | Live and historical market data, on demand | Remote API. Default source. Nothing persisted. |
| **Parquet** | Ranges pinned for reproducibility: bars, ticks, indicator outputs, research features, equity-curve points | Content-addressed `artifact-{sha256}`, flat layout, atomic temp-then-rename |
| **Sidecar manifest** | The authoritative record of each artifact — `StorageManifest` JSON written beside the file | One `.json` per artifact |
| **SQLite** | System state, decisions, orders, configuration — and a **rebuildable index** over the sidecar manifests | Single file + WAL |

Consequences that shape everything below:

- `data_ticks` and `data_candles` **do not exist as tables.** Their replacements are
  `data_datasets` (logical dataset registry) and `data_partition_files` (per-file
  manifest with SHA-256 and min/max timestamps).
- No `FOREIGN KEY` can point at a price row, because there are no price rows. Joins
  against market data happen in pandas/Arrow after a catalog-driven file selection.
- **The sidecar manifest is authoritative; the SQLite catalog is a derived index (D8).**
  `data_datasets` and `data_partition_files` may be dropped and rebuilt by rescanning
  the artifact tree. The reverse is not true — a lost sidecar is unrecoverable. That
  asymmetry is the reason for the ordering: a corrupt index is a rebuild, a corrupt
  manifest is data loss.
- Integrity between catalog and file is therefore checkable rather than assumed:
  `content_hash` + `verify_state` on `data_partition_files` are compared against the
  sidecar and the bytes, and an unverifiable partition fails closed rather than being
  read.
- Four domains that would otherwise hold 10⁷–10⁹ rows now hold hundreds:
  Data, Indicators, Research, Analytics.

---

## 1. Ownership model

The database is a **single SQLite file**, logically partitioned into 14 owner
namespaces. There is no shared mutable table: every table has exactly one owning
domain, and cross-domain reads occur through the owning domain's public API — never
through a foreign schema's tables directly.

| # | Domain | Prefix | Persists | Write pattern |
|---|--------|--------|----------|---------------|
| 1 | Utils | `util_` ¹ | **Nothing — stateless by design.** Prefix reserved, unused | — |
| 2 | Brokers | `broker_` ¹ | Symbol mapping only — stateless by design (D10) | Bitemporal reference |
| 3 | Data | `data_` | Symbols, sessions, providers, **Parquet catalog** | Catalog upsert |
| 4 | Indicators | `indicator_` ¹ | **Nothing — stateless by design.** Historical prefix reserved, unused | — |
| 5 | Strategy | `strategy_` | Definitions, versions, configs, checkpoints | Versioned immutable |
| 6 | Risk | `risk_` | Limits, policies, decisions, kill switches | **Hash-chained append** |
| 7 | Trading | `trading_` | Orders, fills, positions, transitions | **Event-sourced** |
| 8 | Simulator | `sim_` ² | Backtest runs, latency/slippage models; journal is JSONL, not a table | Append + projection |
| 9 | Analytics | `analytics_` ¹ (historical) | **Nothing — read-only by design.** | — |
| 10 | Optimization | `optimization_` | Jobs, trials, hyperparameter states | Append + checkpoint |
| 11 | Research | `research_` | Studies, artifacts, feature defs, regimes | Append + content-addressed |
| 12 | Portfolio | `portfolio_` | Allocations, cash, rebalances | Versioned + outbox |
| 13 | Agentic | `agentic_` | Agents, traces, tools, LLM costs, memory | **Append-only, high volume** |
| 14 | UI-API | `api_` | Accounts, RBAC, API keys, sessions, scoped user/system settings, audit | Versioned upsert + append audit |

¹ **Ratified (D1).** `util_`, `broker_`, `indicator_`, and `analytics_` follow the
singular-full-word convention of the existing prefixes and are recorded in
`docs/ARCHITECTURE.md`.

² **Resolved (D2).** `sim_` is canonical. The `simulation_runs` form in
`app/services/simulator/state/migrations.py` has never been applied to a database, so
aligning it is a code edit and a checksum recompute, not a ledger event.

---

## 2. Dependency direction

Arrows point from dependent to dependency. **The graph is acyclic.** No domain may
declare a foreign key into a domain that transitively depends on it.

```
                        ┌──────────────┐
                        │  1. Utils    │  (settings, logging, flags)
                        └──────┬───────┘
                               │  every domain reads; none writes back
   ┌───────────────────────────┼───────────────────────────┐
   │                           │                           │
┌──▼──────────┐         ┌──────▼──────┐            ┌───────▼──────┐
│ 2. Brokers  │────────▶│  3. Data    │◀───────────│  14. UI-API  │
│ symbol map  │  feeds  │  catalog    │            │ auth / RBAC  │
└──┬──────────┘         └──────┬──────┘            └───────┬──────┘
   │                           │                           │
   │                    ┌──────▼───────┐                   │
   │                    │4. Indicators │                   │
   │                    │ stateless calc│                  │
   │                    └──────┬───────┘                   │
   │                           │                           │
   │                    ┌──────▼───────┐                   │
   │                    │ 5. Strategy  │                   │
   │                    │  signals     │                   │
   │                    └──────┬───────┘                   │
   │                           │                           │
   │                    ┌──────▼───────┐                   │
   │                    │  6. Risk     │  ◀── approval gate │
   │                    │  admission   │      (mandatory)   │
   │                    └──────┬───────┘                   │
   │                           │                           │
   └───────────────────▶┌──────▼───────┐                   │
        execution        │ 7. Trading   │                   │
                         │ orders/fills │                   │
                         └──┬────────┬──┘                   │
                            │        │                      │
              ┌─────────────▼──┐  ┌──▼─────────────┐        │
              │ 8. Simulator   │  │ 12. Portfolio  │        │
              │ (mirrors 7)    │  │ allocation     │        │
              └─────────┬──────┘  └──┬─────────────┘        │
                        │            │                      │
                     ┌──▼────────────▼──┐                   │
                     │  9. Analytics    │                   │
                     │  metrics / PnL   │                   │
                     └──┬────────────┬──┘                   │
                        │            │                      │
        ┌───────────────▼──┐    ┌────▼──────────┐           │
        │ 10. Optimization │    │ 11. Research  │           │
        │ param search     │    │ features/regimes│         │
        └───────────────┬──┘    └────┬──────────┘           │
                        │            │                      │
                     ┌──▼────────────▼──┐                   │
                     │  13. Agentic     │◀──────────────────┘
                     │  AI orchestration│   governed tool calls only
                     └──────────────────┘
```

### Layer summary

| Layer | Domains | Role |
|---|---|---|
| **L0 Foundation** | Utils | Cross-cutting. Depended on by all; depends on none. |
| **L1 Ingress** | Brokers, Data | External world → canonical storage. |
| **L2 Derivation** | Indicators | Deterministic transforms of L1. Fully recomputable. |
| **L3 Decision** | Strategy, Risk | Intent generation and mandatory admission control. |
| **L4 Execution** | Trading, Simulator | Live and simulated order lifecycle. Simulator mirrors Trading's shape exactly. |
| **L5 Aggregation** | Portfolio, Analytics | Position rollup and performance measurement. |
| **L6 Search** | Optimization, Research | Offline exploration over L5 outputs. |
| **L7 Orchestration** | Agentic | Reads everything through governed tools; writes only its own namespace. |
| **Perimeter** | UI-API | Authentication, RBAC, audit. Writes only `api_*`. |

### Indicators persistence history

Indicators owns no target or live database tables. Migration
`001_indicator_schema_v1` historically introduced `indicator_definitions`,
`indicator_param_sets`, and `indicator_materializations`; immutable migration
`002_remove_unused_indicator_support_schema` retired them after verifying that
all three were empty. Indicator identity and provenance cross domain boundaries
through versioned contracts and immutable value references, not database foreign
keys.

---

## 3. Key cross-domain relationships

Cross-domain foreign keys are declared **only where the child cannot be meaningfully
interpreted without the parent**. Everywhere else, the reference is a soft key
(`TEXT` id with no `REFERENCES` clause) so a domain can be archived independently.

### 3.1 Hard foreign keys (enforced, `ON DELETE RESTRICT`)

| Child | → Parent | Cardinality | Reason |
|---|---|---|---|
| `data_partition_files.dataset_id` | `data_datasets.dataset_id` | N:1 | A file without its dataset has no schema and no semantics. |
| `data_datasets.symbol_id` | `data_symbols.symbol_id` | N:1 | A price dataset without its instrument spec is uninterpretable. |
| `data_fetch_log.dataset_id` | `data_datasets.dataset_id` | N:1 | Materialisation must name where it landed. |
| `research_feature_materializations.feature_id` | `research_features.feature_id` | N:1 | Same. |
| `strategy_configs.version_id` | `strategy_versions.version_id` | N:1 | Config binds to exactly one code version. |
| `optimization_trials.job_id` | `optimization_jobs.job_id` | N:1 | Trials are scoped to a job. |
| `agentic_trace_spans.trace_id` | `agentic_traces.trace_id` | N:1 | Span tree integrity. |
| `api_api_keys.account_id` | `api_accounts.account_id` | N:1 | Credential must have an owner. |
| `api_role_bindings.role_id` | `api_roles.role_id` | N:1 | RBAC integrity. |

### 3.2 Soft references (no FK constraint; validated in application code)

| From | → To | Why soft |
|---|---|---|
| `trading_orders.strategy_version_id` | `strategy_versions` | Orders must survive strategy retirement for audit. |
| `trading_orders.risk_decision_id` | `risk_eligibility_decisions` | Risk records are hash-chained and may be archived separately. |
| `trading_orders.broker_account_id` | broker account identifier | Brokers persists no account table (D10); the id is an opaque provider value carried for audit. |
| Historical `analytics_metric_values.*` | any L4/L5 source | Retired; Analytics now computes from supplied versioned evidence. |
| `portfolio_cash_balances.account_id` | broker account identifier | Same — an opaque provider value, not a foreign key. |
| `agentic_llm_calls.agent_id` | `agentic_agents` | Cost records must survive agent deletion for billing. |
| `sim_*` → `data_*`, `strategy_*` | — | Simulation runs pin content hashes, not live rows. |
| `research_feature_materializations.dataset_id` | `data_datasets` | Same guard. |
| Historical `analytics_equity_curves.dataset_id` | `data_datasets` | Retired with the empty Analytics derived store. |
| `data_datasets.producer_ref` | Indicators contract identity / `research_features` | Same guard, inverted: Data must not reference downstream domains. |

**Design rule:** if the child is an immutable audit or financial record, the parent
reference is **always soft**. Deleting a strategy must never cascade into deleting
evidence that money moved.

---

## 4. The Risk gate

`Risk` is the only mandatory chokepoint in the graph.

```
strategy_signals ──▶ risk_eligibility_decisions ──▶ trading_orders
                            │
                            ├─▶ risk_limit_checks       (one row per limit evaluated)
                            ├─▶ risk_kill_switch_states (deny-by-default on trip)
                            └─▶ risk_audit_records      (hash-chained, append-only)
```

Schema-level enforcement:

- `trading_orders.risk_decision_id` is `NOT NULL`. An order row cannot physically
  exist without naming a risk decision.
- `trading_orders.runtime_profile` carries a `CHECK` constraint; combined with a
  partial unique index, `live` rows are structurally rejected unless the matching
  decision is present and unexpired.
- `risk_audit_records` chains `previous_hash` → `record_hash`, so a deleted or
  edited decision breaks the chain and is detectable.

This mirrors `app/services/risk/migrations/definitions.py` and is intentionally
unchanged from it.

---

## 5. Simulator ≡ Trading shape parity

`sim_*` execution tables are **column-for-column mirrors** of their `trading_*`
counterparts, differing only in prefix and the addition of `run_id`.

| Trading | Simulator |
|---|---|
| `trading_orders` | `sim_orders` (+ `run_id`) |
| `trading_positions` | `sim_positions` (+ `run_id`) |

**Rationale:** Analytics computes performance metrics from one shape. If backtest and
live rows diverge structurally, every metric needs two implementations and the two
drift apart — which is precisely how backtest overfitting hides. Parity is a
correctness control, not convenience.

---

## 6. Where the volume went

### 6.1 Series moved out of SQLite entirely

Each is now a Parquet dataset registered in `data_datasets` with one
`data_partition_files` row per `year=YYYY/month=MM` file.

| Former table | Domain | Est. rows/yr | Now | Catalog row |
|---|---|---|---|---|
| `data_ticks` | Data | 10⁹+ | Parquet, monthly | `data_datasets` (kind `tick`) |
| `data_candles` | Data | 10⁷–10⁸ | Parquet, monthly | `data_datasets` (kind `candle`) |
| `ind_outputs` | Indicators | 10⁸ | Recomputed on demand or stored by a consuming owner | No Indicators-owned catalogue table |
| `research_feature_values` | Research | 10⁸ | Parquet | `research_feature_materializations` |
| Analytics equity-curve points | Analytics | 10⁶ | Upstream supplied artifact/evidence | No Analytics table |

**Order of magnitude.** Ten symbols × ten years of M1 bars is ~37M SQLite rows, versus
~1,200 catalog rows plus 150–400 MB of Parquet. The catalog fits comfortably in page
cache; the bars never enter the database at all.

### 6.2 Series that remain in SQLite

These are system records, not market data. They stay because they are queried
relationally, written transactionally alongside other state, and are orders of
magnitude smaller.

| Table | Domain | Est. rows/yr | Retention |
|---|---|---|---|
| `trading_events` | Trading | 10⁶ | Never purged (regulatory) |
| `agentic_trace_spans` | Agentic | 10⁷ | TTL 12 months |
| `api_audit_log` | UI-API | 10⁶ | Never purged |

`agentic_trace_spans` is the one worth watching. If it becomes a size problem it
follows the same route out — append-only, time-ordered, never joined, which is exactly
the Parquet profile. Application logs and metrics are already outside the database
(rotating files), so they are not listed here at all.

---

## 7. Extensibility surface

Every domain that accepts user-defined configuration exposes exactly one
`*_json TEXT` column guarded by `CHECK(json_valid(...))`, per `ARCHITECTURE.md` L647:

| Table | Column | Holds |
|---|---|---|
| `broker_symbol_map` | — | Brokers holds no JSON payload; execution tuning lives in typed settings |
| `data_datasets` | `arrow_schema_json` | Parquet column names, Arrow types, nullability |
| `strategy_configs` | `inputs_json` | Strategy parameters |
| `risk_policies` | `rules_json` | Limit rule tree |
| `optimization_jobs` | `search_space_json` | Grid/genetic bounds |
| `research_features` | `spec_json` | Feature transform definition |
| `agentic_agents` | `manifest_json` | Role manifest, tool grants |

Hot keys are surfaced as indexed `GENERATED ALWAYS AS (json_extract(...)) VIRTUAL`
columns rather than being queried through `json_extract` at read time.

---

## 8. Universal conventions

Applied to every table in this proposal without exception.

| Concern | Rule |
|---|---|
| Identity | `TEXT` UUIDv7 for entities; monotonic `INTEGER` for append-only event logs. |
| Timestamps | ISO-8601 UTC `TEXT` (`2026-08-03T14:22:05.123456Z`). Lexicographic sort = chronological sort. |
| Audit | `created_at TEXT NOT NULL` and `updated_at TEXT NOT NULL` on **every** table with mutable state. No bulk-row tables remain in SQLite, so there is no volume-driven exemption. **Two exceptions**, both code-authoritative tables transcribed verbatim from live migrations and both stamping epoch nanoseconds instead: `data_migration_ledger` (`applied_at_ns`) and `data_write_locks` (`acquired_at_ns`, `expires_at_ns`). This model must not diverge from either. |
| Traceability | `request_id` and/or `correlation_id` on any table whose rows record a decision, a side-effecting mutation, an external interaction, or an audit event — 21 tables. Deliberately **not** on reference, configuration, or derived-output tables, where the identifiers would be noise. |
| Parquet refs | A table pointing at a materialised dataset carries `dataset_id` (soft ref to `data_datasets`), the `*_hash` of its inputs, a covered range, and a `state` in `building/ready/stale/invalidated/failed`. |
| Lifecycle | `state TEXT NOT NULL` + `CHECK (state IN (...))` on every stateful entity. |
| Booleans | `INTEGER NOT NULL CHECK (col IN (0,1))` per `ARCHITECTURE.md` L647. |
| Money | `TEXT` holding a `decimal.Decimal` string. **Never `REAL`.** Per `ARCHITECTURE.md` L648. |
| JSON | `TEXT` + `CHECK(json_valid(col))`, `*_json` suffix. |
| Normalise vs. payload | **The hybrid rule (D9).** A field becomes a typed column only if it is (i) filtered or joined on, (ii) enforceable by a `CHECK`, or (iii) part of a unique key. Everything else stays in one `*_json` payload. Hot inner keys are exposed as indexed `GENERATED ALWAYS AS (json_extract(...)) VIRTUAL` columns rather than promoted to real columns. This keeps constraint enforcement where it earns its cost, without requiring an additive migration for every new parameter under the immutable ledger. |
| Migration location | **`app/services/<domain>/migrations/` (D12).** One migration package per domain, aggregating that domain's schema definitions. Migrations are schema evolution, not CRUD, and stay outside the `persistence/` package. |
| Strictness | `STRICT` on all tables (matches `trading_*` and `agentic_*` precedent). |
| Soft delete | `deleted_at TEXT` (nullable) on config tables. Never on financial records. |

---

## 9. Next

- [01_entity_specs_core.md](01_entity_specs_core.md) — Utils, Brokers, Data, Indicators
- [02_entity_specs_execution.md](02_entity_specs_execution.md) — Strategy, Risk, Trading, Simulator
- [03_entity_specs_intelligence.md](03_entity_specs_intelligence.md) — Analytics, Optimization, Research, Portfolio, Agentic, UI-API
- [04_indexing_and_performance.md](04_indexing_and_performance.md) — Indexes, PRAGMAs, partitioning
