# Authoritative Database Schema Model

## Authority statement

**This directory is the authoritative cross-domain database schema model.**

Promoted from `docs/dev/schema/` under Dry-Run Plan 2, Phase 0.

### What this directory is canonical for

- **Cross-domain schema structure**: the storage-tier model, the domain dependency
  graph as expressed in foreign keys, prefix ownership, and the universal column
  conventions in [00](00_domain_relationship_map.md) §8.
- **The target table and column model** for all 14 domains.
- **Indexing and performance policy**, including Parquet layout and read paths.
- **The reconciliation record** between target and live schema.

### What this directory is *not* canonical for

Per `AGENTS.md` §1 *Feature Registry Authority*, which is unchanged:

- **Current-state feature registries** remain solely in each owning package
  `README.md` — feature IDs, statuses, module ownership, public API, contracts,
  requirements, usage evidence.
- **Executable schema** remains solely in the owning domain's migration definitions.
  Nothing here is executed.
- **`FEAT-[DOM]-NN` registration** happens in the owning package README, never here.

### Target vs. Current

This model is **normative for new work and aspirational for existing tables.**
59 tables are live under an immutable migration ledger; 19 share a name with a table
defined here, and 13 of those are structurally incompatible.

Per `AGENTS.md` §5 and `ARCHITECTURE.md` L650, applied migration steps are immutable.
Therefore:

- A **new** table must conform to this model.
- An **existing** table that diverges is recorded in
  [05_reconciliation.md](05_reconciliation.md) with an adoption tier. Divergence is a
  documented state, not a defect to be silently migrated away.
- Closing a divergence requires either an additive migration (Tier A) or an explicit
  baseline reset approval (Tier C). **Neither is authorised by this document.**

### Precedence

`Owner` → `AGENTS.md` → `docs/PROJECT.md` → `docs/ARCHITECTURE.md` → **`docs/schema/`**
→ owning package `README.md` (current state) → `migrations.py` (executable truth).

Where this model and a live migration disagree, the migration is what the database
actually contains and this model states what it should become.

---

## Scope and provenance

| | |
|---|---|
| **Requested** | Complete schema for 14 domains, SQLite target |
| **Mode** | Greenfield ideal-state, promoted to authoritative (Dry-Run Plan 2, Phase 0) |
| **Engine strategy** | SQLite-native equivalents for JSONB/hypertables (owner-selected) |
| **Authored** | 2026-08-03 |
| **Approval** | Dry-Run Plan 1 (authored), Dry-Run Plan 2 Phase 0 (promoted) |
| **Entities** | 103 tables across 14 domains |
| **Storage model** | MT5 broker is the runtime source; Parquet is the pinned store; SQLite holds system state + a Parquet catalog. **No bulk series in the database.** |
| **Verified** | All DDL executed against a live SQLite engine; FK targets, index targets, audit columns, prefix ownership, `STRICT` mode, and absence of `REAL` monetary columns all checked programmatically |

---

## Reading order

| Document | Contents |
|---|---|
| [00_domain_relationship_map.md](00_domain_relationship_map.md) | Ownership model, dependency DAG, cross-domain FK policy, universal conventions |
| [01_entity_specs_core.md](01_entity_specs_core.md) | Utils, Brokers, Data, Indicators — 25 tables |
| [02_entity_specs_execution.md](02_entity_specs_execution.md) | Strategy, Risk, Trading, Simulator — 26 tables |
| [03_entity_specs_intelligence.md](03_entity_specs_intelligence.md) | Analytics, Optimization, Research, Portfolio, Agentic, UI-API — 52 tables |
| [04_indexing_and_performance.md](04_indexing_and_performance.md) | PRAGMAs, Parquet layout, catalog-then-file read paths, index catalogue, throughput |
| [05_reconciliation.md](05_reconciliation.md) | **Live vs. proposal diff, adoption tiers, resolution of D4** |

Start with 00 — the conventions in §8 apply to every table in 01–03 and are not
repeated.

---

## How the brief's Postgres-isms were resolved

Three requirements in the original brief do not exist in SQLite. Each was translated
rather than dropped:

| Requested | SQLite reality | Substitute |
|---|---|---|
| `JSONB` columns | No JSONB type. SQLite 3.45+ has `jsonb()` *functions* storing BLOB — not the same thing, not equivalently queryable. | `TEXT` + `CHECK(json_valid(col))`, with hot keys promoted to indexed `GENERATED ALWAYS AS (json_extract(...)) VIRTUAL` columns |
| Hypertables | TimescaleDB only. | **Superseded — see below.** Bulk series left SQLite entirely; content-addressed Parquet artifacts are the store, and `data_partition_files` is the index |
| Time partitioning | No declarative partitioning. | The catalog prunes by recorded time range, which is more precise than a directory name and needs no filesystem access. Directory partitioning proved unnecessary once a catalog existed — see [04](04_indexing_and_performance.md) §2.2 |
| UUID / BigInt PKs | No UUID type. | `TEXT` UUIDv7 (time-sortable, preserves insert locality) for entities; `INTEGER PRIMARY KEY` for append-only event logs |

---

## Storage model

Revised after the initial draft: the database does **not** store market data.

| Tier | Holds | Medium |
|---|---|---|
| **Broker (MT5)** | Live and historical bars/ticks, on demand | Remote API. Default path. Nothing persisted. |
| **Parquet** | Ranges pinned for reproducibility | Content-addressed `artifact-{sha256}`, flat layout, prices as `Decimal` strings |
| **Sidecar manifest** | Authoritative record of each artifact (`StorageManifest` JSON) | One `.json` per artifact |
| **SQLite** | System state, decisions, orders, config — and a rebuildable index over the sidecars | Single file + WAL |

Five bulk tables were removed and replaced by catalog rows:

| Removed | Rows it would have held | Replaced by |
|---|---|---|
| `data_ticks` | 10⁹+/yr | `data_datasets` + `data_partition_files` |
| `data_candles` | 10⁷–10⁸/yr | Same |
| `ind_outputs` | 10⁸/yr | `indicator_materializations` |
| `research_feature_values` | 10⁸/yr | `research_feature_materializations` |
| `analytics_equity_curves` (points) | 10⁶/yr | `analytics_equity_curves` (summary row + `dataset_id`) |

**What this buys.** Ten symbols × ten years of M1 bars: ~37M SQLite rows becomes
~1,200 catalog rows plus 150–400 MB of Parquet. Column projection means a backtest
reading four of nine columns reads 44 % of the bytes.

**What it costs.** No SQL joins against prices, no foreign key from a bar to its
symbol, and catalog/file consistency becomes the application's job. That last one is
why `data_partition_files` carries `content_hash` + `verify_state`, why the write
order is Parquet-then-catalog, and why an unverifiable partition fails closed. DuckDB
covers the ad-hoc SQL gap by querying Parquet directly.

See [00](00_domain_relationship_map.md) §0 for the full storage-tier rules and
[04](04_indexing_and_performance.md) §2–3 for layout, pruning, and read paths.

---

## Resolved conventions

No open decisions remain against this model. Each row below is settled; the outcome is
written into the section named, and the row is retained here only as a pointer.

| # | Decision | Outcome |
|---|---|---|
| D1 | Table prefixes for the four undocumented domains | `util_`, `broker_`, `indicator_`, `analytics_` — the singular-full-word convention already used by `data_`, `api_`, `strategy_`, `risk_`, `trading_`, `portfolio_`, `research_`, `agentic_`. Recorded in `docs/ARCHITECTURE.md`. |
| D2 | `sim_` vs `simulation_` | **`sim_`.** `simulation_runs` was never applied to any database — it exists only as a string in two files — so the rename is a code edit plus a checksum recompute, not a ledger event. |
| D3 | Runtime SQLite version | **Confirmed ≥ 3.37.0 by evidence**, not assumption: 17 of 22 tables in `data/database/haruquant-dev.db` declare `STRICT`, which the engine could not have accepted below 3.37.0. |
| D4 | Adoption scope | Rewrite migration definitions for the **7 never-applied** REBUILD tables to match this model before first apply — zero ledger and zero data risk. The **6 applied** tables (`api_accounts`, `api_sessions`, `strategy_versions`, `strategy_configs`, `strategy_checkpoints`, `data_migration_ledger`) stay divergent and documented in [05](05_reconciliation.md). |
| D8 | Sidecar manifest vs. SQLite catalog | **Sidecar authoritative; catalog is a rebuildable index.** A corrupt catalog is a rescan; a lost sidecar is data loss. Recorded in [00](00_domain_relationship_map.md) §0, [01](01_entity_specs_core.md) Domain 3, and [04](04_indexing_and_performance.md) §8. |
| D9 | Normalised columns vs. `*_json` payload | **Hybrid rule.** Normalise only what is filtered/joined, `CHECK`-enforceable, or part of a unique key. Recorded in [00](00_domain_relationship_map.md) §8. |
| D10 | Brokers and Analytics persistence | Brokers stays stateless (`broker_symbol_map` only); Analytics owns a derived store. Recorded in `docs/PROJECT.md` §5. |
| D12 | Migration-definition location | `app/services/<domain>/migrations/`. Relocation is an import-path refactor, not a checksum risk. |
| D13 | Authority form for `docs/schema/` | Canonical for cross-domain structure and the target model; owning package READMEs stay canonical for current state. `AGENTS.md` §1 unchanged. |
| D14 | Immutable Portfolio definition history | **Split.** `portfolio_definitions` holds identity; `portfolio_definition_versions` holds append-only configuration history. Satisfies `PROJECT.md` §5 without breaking child foreign keys. |

---

## Design controls worth noting

Several constraints in this design encode safety policy in the schema itself, so that
no code path — including a buggy new one — can violate them. They are the parts most
worth reviewing:

| Control | Where | Effect |
|---|---|---|
| ~~Production connections cannot be stored enabled~~ | ~~`broker_connections` CHECK~~ | **WITHDRAWN** under D10. Brokers persists no connection table, so this control now rests on application code and `ALLOW_LIVE_MUTATIONS`. See [01](01_entity_specs_core.md) Domain 2. |
| Orders cannot exist without a risk decision | `trading_orders.risk_decision_id NOT NULL` | The admission gate is unbypassable |
| Kill-switch reset requires a recorded approval | `risk_kill_switch_states` CHECK | `AGENTS.md` §3 "No caller can override" |
| One active allocation per portfolio | `idx_risk_allocation_active` unique partial | No ambiguity about which budget applied |
| One open position per account/symbol/side | `idx_trading_pos_open` unique partial | Netting invariant |
| Agents cannot hold mutating permissions | `agentic_agents.permission_class` CHECK | Classes are unrepresentable, not merely refused |
| Order/kill-switch/deploy tools unregistrable | `agentic_tools` CHECKs | `FEAT-AGT-05` deny-by-default |
| No wildcard scopes | `agentic_tool_grants`, `api_permissions` CHECKs | Absence of a grant is a denial |
| Out-of-sample cannot overlap in-sample | `optimization_jobs` CHECK | Temporal separation of validation data |
| Confirmatory studies must be preregistered | `research_studies` CHECK | Hypothesis fixed before results are known |
| Multiple tests force a correction | `research_hypothesis_tests` CHECK | Prevents uncorrected multiple-comparison claims |
| Money is never `REAL` | All monetary columns `TEXT`; Parquet stores `Decimal` as string | `ARCHITECTURE.md` L648 `decimal.Decimal`. Moving Parquet to a `DECIMAL` logical type is recorded as an open improvement in [04](04_indexing_and_performance.md) §2.3 |
| Unverifiable partition blocks reads | `data_partition_files.verify_state` + `idx_data_files_bad` | `AGENTS.md` §3 Fail-Closed |
| Materialisation must name its dataset | `data_fetch_log` CHECK | No untraceable "we saved it somewhere" |

---

## Verification

Three scripts, each answering a different question. All exit non-zero on failure.

```bash
python docs/schema/verify_schema.py          # is the model internally sound?
python docs/schema/compare_model_to_code.py  # does the code match the model?
python docs/schema/verify_persistence_sql.py # does the SQL match the code?
```

**`verify_schema.py`** executes every `CREATE TABLE` and `CREATE INDEX` in this model
against a live SQLite engine and asserts: all foreign-key targets resolve, all index
targets resolve, audit columns are present, no monetary column is `REAL`, every table
is `STRICT`, and all 14 domain prefixes are distinct. Run it after any edit to docs
01–03.

**`compare_model_to_code.py`** diffs each conformed table's columns between this model
and the migration module that ships it, so model drift is reported rather than
discovered later.

**`verify_persistence_sql.py`** checks that every table named in a persistence SQL
literal has a `CREATE TABLE` somewhere. Nothing else connects those strings to the
migrations: renaming `hq_runtime_records` to `data_runtime_records` updated the
migration but not the ten statements that read the table, each of which would have
failed on first apply for five domains. Run it after renaming any table.
