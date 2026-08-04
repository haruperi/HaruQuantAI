# Schema and Persistence Programme — Handover

**Status:** Phases 0–3 complete. Phase 4 partially complete (4A, 4B, 4C, 4E shipped; 4D
not built). Phases 5 and 6 not started.
**Last worked:** 3 August 2026.
**Audience:** the next agent or engineer picking this up cold.

This document is a handover, not an authority. The authoritative sources remain
`AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/schema/`, and each owning
package `README.md`, in that precedence order. Where this document and those disagree,
they win and this document is stale.

---

## 1. What this programme is

The repository had ~59 tables declared across scattered migration modules, an immutable
ledger governing their application, and no single description of the data model. The
programme built that description, promoted it to authoritative, reconciled it against
what actually ships, and then closed the gaps it exposed.

Two constraints shaped everything:

**Storage model.** Market data is *not* stored in the database. It is fetched live from
the broker (MT5 by default) and optionally persisted as Parquet artifacts. The `data_*`
tables are therefore a *catalogue of references*, not the data itself. Anyone who reads
the model expecting bar tables will be confused; there are none by design.

**Uniform Persistence Layout.** Every database operation lives in
`app/services/[DOMAIN]/persistence/` containing exactly `__init__.py`, `create.py`,
`read.py`, `update.py`, `delete.py`. Operations are classified by *business effect*,
not by SQL statement — a read that writes an audit row is a create. `delete.py` exists
even where deletion is prohibited (Strategy's exports nothing). Migration definitions
live *outside* the persistence package, in `app/services/[DOMAIN]/migrations/`.
`app/services/data/persistence/` is exempt from the four-module shape: it owns the
shared connection, transaction, locking, ledger and backup infrastructure.

---

## 2. Where things live

| Path | What it is |
|---|---|
| `docs/schema/README.md` | Authority statement, precedence chain, design-control catalogue, verification instructions |
| `docs/schema/00_domain_relationship_map.md` | Storage tiers (§0), universal conventions (§8) |
| `docs/schema/01_entity_specs_core.md` | Utils (0 tables), Brokers (1), Data (21), Indicators (3) |
| `docs/schema/02_entity_specs_execution.md` | Strategy (7), Risk (10), Trading (7), Simulator (1) |
| `docs/schema/03_entity_specs_intelligence.md` | Analytics (6), Optimization (5), Research (6), Portfolio (9), Agentic (13), UI-API (13) |
| `docs/schema/04_indexing_and_performance.md` | Index strategy; §2 describes the *shipped* Parquet writer |
| `docs/schema/05_reconciliation.md` | Live-vs-model diff, adoption tiers A–D, phase status |
| `docs/schema/verify_schema.py` | 12 checks on the model itself |
| `docs/schema/compare_model_to_code.py` | Column-level model-vs-code diff + list of uncreated model tables |
| `docs/schema/verify_persistence_sql.py` | Every table named in persistence SQL has a creating statement |

Model total: **102 tables**. Tables actually created by some module: **76**. Model
tables no module creates: **26** (listed by the comparison script).

Migration definition modules (32 files) live at `app/services/<domain>/migrations/` for
analytics, api, brokers, data, indicators, optimization, portfolio, research, risk,
simulator, strategy, trading, plus `app/agentic/migrations/`.

Two Data modules create tables *outside* the ledger, necessarily — they bootstrap the
ledger itself: `app/services/data/persistence/migrations.py` (`data_migration_ledger`)
and `.../locking.py` (`data_write_locks`).

---

## 3. Running the checks

```bash
python docs/schema/verify_schema.py          # is the model internally sound?
python docs/schema/compare_model_to_code.py  # does the code match the model?
python docs/schema/verify_persistence_sql.py # does the SQL match the code?
```

All three exit non-zero on failure and all three were green at handover.

A note for anyone working in a sandbox: the project targets **Python 3.14**. A 3.10/3.12
sandbox cannot import `app.*` — `app/services/data/persistence/backup.py` uses a PEP 695
`type` alias, and `app/services/data/persistence/transactions.py` relies on PEP 758
`except A, B:`. Neither is a defect. To exercise schema statements in an older
interpreter, lift the `_*_SCHEMA_STATEMENTS` tuple out with `ast` and inject it under
the expected module name in `sys.modules`, rather than importing the package.

---

## 4. Decisions already made — do not relitigate without the owner

Recorded in `docs/PROJECT.md` §12 as D1–D14. The ones most likely to be re-opened by
mistake:

- **Utils owns no tables.** Seven proposed `util_*` tables were withdrawn. Utils is the
  shared framework; it holds no state. The `util_` prefix stays reserved and unused.
- **Brokers is a stateless passthrough** except for `broker_symbol_map`. Connection and
  circuit state are in memory, balances are fetched live, credentials are never
  persisted. Four other proposed `broker_*` tables were withdrawn.
- **Hybrid normalisation (D9).** Normalise only what is filtered, joined,
  `CHECK`-enforceable, or part of a unique key. Everything else goes in a `*_json`
  payload, with `GENERATED ALWAYS AS (json_extract(...)) VIRTUAL` columns for hot keys.
- **Money is never `REAL`.** All monetary columns are `TEXT` holding `Decimal` strings.
  Parquet stores prices as decimal strings too; moving to a `DECIMAL` logical type is a
  recorded open improvement, not a defect.
- **The model is normative for new work, descriptive for existing tables.** Where a
  shipped table differs, the model was amended to match it unless the difference was a
  real defect. Live Risk shape was adopted over renaming live code.
- **Persistence and schema packages are private support, not registered features.**
  This is the newest decision (3 Aug 2026) and it reversed part of Phase 4 — see §6.

---

## 5. Phase-by-phase record

### Phase 0 — Promote the model to authoritative

Moved `docs/dev/schema` to `docs/schema`. Replaced the "non-authoritative" banner with
an authority statement and a precedence chain: `Owner → AGENTS.md → docs/PROJECT.md →
docs/ARCHITECTURE.md → docs/schema/ → owning package README.md → migrations.py`.
Relocated decisions D1–D9 into `docs/PROJECT.md` §12 so the model holds no decision
ledger of its own (`AGENTS.md` §4 Decision Hygiene). Amended `ARCHITECTURE.md` and
`AGENTS.md` authority routing.

### Phase 1 — Tier D defect fixes

Five model defects corrected: withdrew `sim_timeline_events` (contradicted a documented
live exclusion); replaced the invented `data_migration_ledger` definition with the live
one; added `data_write_locks`; added `request_id`/`correlation_id` to **21** tables (not
all of them — only where a row records a decision, a side-effecting mutation, an
external interaction, or an audit event); reconciled `data_partition_files` with the
live `StorageManifest` contract (adopted 5 fields, rejected 3 as duplicates).

Also resolved D10: Brokers stays stateless (upheld), Analytics gains a derived store
(overturned the earlier "read-only" reading).

### Phase 2 — Hybrid normalisation

Applied D9 across the model. Brought forward what made the live tables better —
`canonical_hash`, `record_hash`, `request_id`, `correlation_id`, `retention_class`,
`injection_status`, workflow-node columns — so the residual live-vs-model differences
reduced to renames and payload-shape preferences.

### Phase 3 — Conform shipped migration definitions

Relocated migration definitions out of persistence packages into
`app/services/<domain>/migrations/` for Trading, Risk, Portfolio, Optimization,
Research, Simulator, API, Agentic and Data, conforming each to the model
column-by-column. Registered `FR-TRD-070`–`073` and `FR-RISK-069`–`072`.

Recorded every shipped table in the model (8 Data tables, 4 API tables,
`strategy_mutations` had all been missing).

### Phase 4 — Build the real gaps

| Sub-phase | Status | What |
|---|---|---|
| 4A | Shipped | Artifact catalogue: 7 tables, migration step `006_data_catalog_v1`, catalogue CRUD in `data/persistence/`. Doc 04 §2–3 rewritten to describe the writer that actually ships |
| 4B | Shipped | `indicator_definitions`, `indicator_param_sets`, `indicator_materializations` with generated columns over `params_json` |
| 4C | Shipped | Six `analytics_*` tables: metric definitions and values, round-trip analysis, PnL attribution, equity-curve summaries, reports |
| 4D | **NOT BUILT** | Trading materialisation — see §7 |
| 4E | Shipped | `broker_symbol_map`, bitemporal, with two partial unique indexes |

### Post-Phase-4 correction (3 August 2026)

Closing Phase 4 surfaced that 4B/4C/4E had registered `FEAT-DATA-18`, `FEAT-INDI-07`,
`FEAT-ANLT-06` and `FEAT-BRK-16` as features whose public API was a list of persistence
functions — but no domain exports those functions, and the Phase 0 decision says
persistence packages are private support. The owner chose to **withdraw the
registrations**.

Done: removed the four `FEAT-*` rows and their `FR-DATA-154`–`160`,
`FR-INDI-036`–`040`, `FR-ANLT-055`–`059`, `FR-BRK-136`–`138` rows; deleted the four
numbered usage programs; converted their evidence into 22 pytest tests at
`tests/{data,indicators,analytics,brokers}/unit/`. Tables, migrations and CRUD modules
are unchanged and still applied — only their status as features changed.

---

## 6. Defects found and fixed — read this before trusting a green check

Every one of these was a check that *passed* while being wrong. They are recorded
because the same shapes will recur.

1. **`hq_runtime_records` rename, half-applied.** Renamed to `data_runtime_records` in
   the migration but not in ten statements across `create.py`, `read.py` and
   `update.py`. Would have failed on first apply for Trading, Risk, Portfolio,
   Simulator and Agentic. Nothing connected a SQL string constant to its `CREATE TABLE`.
   `verify_persistence_sql.py` now does, and is proven against this exact bug.

2. **4D recorded as shipped when it was not.** `compare_model_to_code.py` reported "0
   mismatched" because a table absent from code is a table it never compares. It now
   also lists the 26 model tables no module creates.

3. **Constraint-matcher prefix bug.** `re.match(r"(PRIMARY KEY|UNIQUE|CHECK|...)")`
   matched any column named `check*` — silently hiding 8 columns (`checkpoint_json`,
   `checkpoint_id`, `check_seq`, `check_id`, `checked_at`, `checkpoint_hash`,
   `checksum`) from comparisons. Fixed by requiring `CHECK\s*\(` / `UNIQUE\s*\(`.

4. **Line-based column splitting.** Multi-line column definitions (wrapped `CHECK`,
   `GENERATED ALWAYS AS`) were read as two entries, producing `)` as a column name.
   Fixed with `_split_top_level()`, which splits on top-level commas and strips inline
   `--` comments first.

5. **Index-name extraction consumed `IF NOT EXISTS`.** Two partial unique indexes were
   reported as named `IF`. Display-only, but it survived several runs because a check
   that prints a wrong name still passes.

6. **`FR-DATA-154`–`157` allocated twice** — once for MT5 streaming, once for the
   catalogue. Resolved by the withdrawal.

7. **12 Data tables silently deleted** by a section-replacement regex whose end anchor
   matched too early; table count dropped 102→86 unnoticed. Restored.

8. **Regex insert anchor matched the following table** when `created_at` was the final
   column: 4 tables missed their columns, 3 non-targets gained them, 1 duplicated.

9. **Circular import.** `data/migrations/__init__.py` imported `runtime_stores`, which
   imported `persistence.migrations`, which imported the migrations package. Fixed by
   removing `runtime_stores` from the package `__init__`, with the reason in its
   docstring. Do not re-add it.

10. **Four tests broken by 4B/4E and not noticed** until the withdrawal fixed them:
    `test_usage_scripts_cover_exact_requirements_through_root_api` (40 Completed
    `FR-INDI-*` rows against 35 discoverable functions),
    `test_usage_parity_and_reachability` (asserts exactly 16 broker usage programs),
    `test_brokers_readme_has_one_reconciled_completed_registry` (expects `FEAT-BRK-00`…
    `15`), and `test_registered_feature_directories_match_the_current_package` (broken
    earlier by creating `app/services/data/migrations/`, fixed with a
    `SUPPORT_DIRECTORIES` exclusion).

Two claims I made during the programme were themselves wrong and were retracted: that
`except OSError, ValueError:` was invalid syntax (it is PEP 758, valid on 3.14), and
that Agentic had no `FR-*` requirements (it has 124 under `FR-AGENTIC-`, which my
`FR-[A-Z]{2,4}-` pattern could not match). Check the pattern before concluding absence.

---

## 7. Closure status — **COMPLETED**

### 7.1 Phase 6 — migrate five domains off the runtime store — **COMPLETED**

Trading, Risk, Portfolio, Simulator and Agentic now write their active durable state
directly to domain-owned relational tables while Data retains connection, locking,
statement-plan and transaction execution ownership. No production domain remains on
the generic key-value store `data_runtime_records`.

**Measured cost:** roughly 4,275 lines — 2,055 across five persistence packages, 2,220
across ten runtime adapters, 62 exported functions.

The completed order was Trading → Risk → Portfolio → Simulator → Agentic. Agentic's
workflow, memory-record, lifecycle and operations producers use eight owned tables.
`agentic_evidence_claims` and the four experiment tables still lack production durable
producers and remain honestly Missing/Partial rather than being populated speculatively.

Trading Phase 4D was completed as part of this sequence, preventing a second parallel
persistence mechanism from being introduced.

### 7.2 Phase 5 — API RBAC normalisation — **COMPLETED**

`api-0005` adds `api_roles`, `api_permissions`, `api_role_bindings`, and
`api_role_permissions`, backfills exact legacy authority, and changes account and
session reads to use normalized tables. The immutable baseline JSON columns remain as
unused compatibility fields; new rows store empty arrays there. Backfill and new
registration fail closed if one role name would acquire conflicting permission sets.
The existing account and sessions were preserved rather than rebuilding the baseline.

The other twelve Tier C candidates should **not** be pursued — in every case the live
table is equivalent or better and the migration buys only column naming.

### 7.3 `api-0004` ledger orphan — **COMPLETED**

The development database was backed up through Data's immutable backup contract, the
exact orphan row was removed after checksum and schema verification, and `api-0005`
was applied without deleting the existing account or sessions. `MigrationRequest` now
supports an explicit complete-manifest declaration; such runs fail before schema
mutation when the ledger contains an unknown applied ID.

### 7.4 Smaller items — **COMPLETED**

- **Brokers usage execution:** deliberately manual and credential-gated for genuine
  non-production sessions. Automated parity tests verify every program and workflow;
  ordinary CI never initiates a broker connection or mutation.
- **Schema verifier:** `verify_schema.py` is formatted, typed, resource-safe, and
  Ruff-clean while retaining all twelve checks.
- **Parquet decimal policy:** decimal strings remain canonical and precision-safe.
  Native fixed-scale decimals are explicitly excluded until bounded scale metadata is
  ratified.
- **Non-schema producers:** Agentic evidence claims, Agentic experiment records, and
  Portfolio definition creation remain honest feature-backlog exclusions. Their table
  existence does not authorize invented business records and they are not unfinished
  schema-programme work.

---

## 8. Working agreements that apply to this programme

From `AGENTS.md`, and they are not optional:

- **Dry-run then approval.** Present a plan; wait for `APPROVED: EXECUTE`. Restricted
  commands needing explicit approval: `rm -rf`, `git reset`, `git clean`, `uv add`/`uv
  remove`, `docker compose`, live broker calls, real email/Telegram sends, destructive
  SQL.
- **Fail closed.** If policy is uncertain or evidence is missing, block the action.
- **No live action by default.** Live trading, risk changes and execution-state
  mutations need explicit deterministic approval. Real integration operations only
  against verified non-production targets (`ENVIRONMENT=dev`, demo/paper/sandbox). The
  kill switch is deterministic and cannot be bypassed.
- **No invented data.** Never fabricate backtest results, live performance, or broker
  fills.
- **Credential hygiene.** Logs, exception payloads and test output must never capture
  plain-text credentials, secret keys, JWTs or account passwords. `.env.example` only.
- **Migrations are immutable.** An applied step is never edited. Checksums are SHA-256
  over the ordered statement list; the ledger is keyed `(domain, migration_id)`. Path
  and module name are *not* checksum inputs, so relocating a definitions module is safe;
  changing a statement is not.
- **One feature = one module folder = one usage program.** Usage programs are standalone
  numbered scripts under `tests/<domain>/usage/`, excluded from pytest collection, with
  `main()` and an `if __name__ == "__main__"` guard, verified by direct execution. Unit
  and integration behaviour stays in pytest files outside `usage/`.
- **No deep cross-domain imports.** Consumers outside a domain import only from
  `app.services.[DOMAIN]`. Within a domain's own test tree, deep imports of that
  domain's private modules are used (see the four new schema tests) — but the indicators
  usage-script runner enforces the strict form for *usage programs* specifically.

---

## 9. Programme completion evidence

The programme is complete when the final validation record below is green. Future
feature work must continue to run all three schema checks, and any table rename must
run `verify_persistence_sql.py`; those are permanent maintenance gates rather than
remaining programme tasks.

### Final validation record — 4 August 2026

| Gate | Command or evidence | Result |
|---|---|---|
| Target model integrity | `uv run python docs/schema/verify_schema.py` | **PASS** — all 12 checks; 102 tables and 98 executable indexes |
| Target-to-code comparison | `uv run python docs/schema/compare_model_to_code.py` | **PASS** — 42 executable tables compared, 0 mismatches; 18 explicitly model-only backlog/exclusion tables reported |
| Persistence SQL coverage | `uv run python docs/schema/verify_persistence_sql.py` | **PASS** — all 68 SQL-referenced tables have a creating statement |
| Repository tests, main partition | `uv run pytest --no-cov -q --ignore=tests/optimization/integration/test_usage_scripts.py` | **PASS** — 4,287 passed, 5 explicit live-provider skips |
| Repository tests, Optimization usage partition | `uv run pytest --no-cov tests/optimization/integration/test_usage_scripts.py -q` | **PASS** — 10 passed in 49.95 seconds |
| Corrected-failure regression set | Focused API, Data, Indicators, Simulator, Strategy, Trading, Utils, and system tests | **PASS** — 73 passed, 3 explicit MT5 skips |
| Code quality | Targeted `ruff check`, `ruff format --check`, and `mypy` over changed production and validation files | **PASS** |
| Development database | SQLite integrity, API ledger, normalized RBAC counts, existing identity/session counts | **PASS** — integrity `ok`; no `api-0004` orphan; one `api-0005`; account and five sessions preserved |
| Recovery point | Immutable Data backup manifest `id-edc5184c150002bb414689b9b610b108af2a3f4a674d8ac1e839e0dcdb26a8fd` | **PASS** — manifest and backup database independently reloaded and verified |

The pytest record is deliberately partitioned because repeated whole-repository runs
caused resource-contention timeouts in four Optimization subprocess programs even
though the complete Optimization usage file passes in under 50 seconds in isolation.
The two green partitions cover all 4,297 collected tests. The five skips are explicit
opt-ins for licensed calendar, live research-provider, and genuine MT5 workflow
verification; ordinary CI performs no provider connection.

### Completed-plan evidence

- [x] Normalized API RBAC migration and fail-closed account authority writes — `app/services/api/migrations/definitions.py:298`, `app/services/api/persistence/create.py:58`.
- [x] Complete-manifest orphan detection and authoritative Data/API runs — `app/services/data/persistence/contracts.py:190`, `app/services/data/persistence/migrations.py:287`, `app/services/api/migrations/definitions.py:351`.
- [x] Public-port graph retains deep-import enforcement while classifying mandated persistence delegation as infrastructure — `tests/system/unit/test_public_ports.py:135`.
- [x] Licensed calendar and genuine MT5 workflow execution are explicit opt-ins — `tests/data/integration/test_usage_scripts.py:9`, `tests/indicators/integration/test_workflow_scripts.py:11`.
- [x] Stale migration, public-export, and system-workflow evidence is reconciled with the current owner boundaries — `tests/data/unit/test_economic_calendar_migration.py:65`, `tests/strategy/unit/test_public_api.py:17`, `tests/system/integration/test_optimization.py:119`.

There are no remaining schema-programme implementation items. The 18 model-only
tables and the non-schema producers listed in §7 remain explicit future feature work;
they are not partially implemented schema migrations.

### Fresh development-database rebuild — 4 August 2026

After the programme closed, `data/database/haruquant-dev.db` was reset in one
exclusive transaction and rebuilt solely through the authoritative domain migration
manifests. The rebuilt database contains **84 executable tables** and **25 migration
ledger rows across 13 domains**. `PRAGMA integrity_check` returned `ok`,
`PRAGMA foreign_key_check` returned no rows, every non-infrastructure table was empty,
and repeat execution of the complete Data and API manifests applied no steps. The
remaining 18 target-model tables are the explicit future work identified above, not
missing migrations from this rebuild.

The pre-reset recovery point is immutable Data backup manifest
`id-d97e8bce2c23f1f1a53296bb68ef823ba1e38af97e5a6b0e9328159d26b39571`
with payload SHA-256
`acc0e123be4fee78ba604235dad252f8e3841ecc39c155571374996bcb5990b8`.
An independently hash-verified archive copy is retained under
`data/artifacts/data/database-rebuild/20260804T001200Z/`.

### Unified settings migration — 4 August 2026

Owner-approved migration `api-0006` replaced the user-only table with one
UI/API-owned `api_settings` table for versioned, secret-safe `user` and `system`
documents. The migration copies and count-verifies legacy rows before dropping
`api_user_settings`; immutable steps `api-0001` through `api-0005` remain unchanged.
The final development database still contains **84 tables**, now records **26 ledger
rows**, passes integrity and foreign-key checks, and exposes exactly one settings
table. Its settings rows are empty because the fresh rebuild contained no user
preferences and no system values were invented.

`DataSettings` now consumes the repository's central JSON/process source order, so
API startup reaches the development database without transient shell injection.
Connection-bootstrap paths, lock timeouts, credentials, and encryption material stay
outside `api_settings` because the application needs them before the table is
reachable. The pre-migration recovery point is immutable backup manifest
`id-01ad38f9cea970cfe4b14229193f685c06ec15cda6cb028e1c1bc702ddbc66b7`,
whose database payload SHA-256 is
`f77ce7454572b5ddf13776883439f6ba06c3a2bc480475ce3e403274732c5b77`.
