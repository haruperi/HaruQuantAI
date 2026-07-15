# DATA Domain — Pre-Build Implementation-Readiness Audit

> **Scope:** Read-only audit of `app/services/data` readiness before the next build cycle.
> **Auditor role:** Reporting only — no files created, modified, or deleted.
> **Date:** 2026-07-15
> **Verdict:** **GO** for the next bounded feature (`storage/migrations.py`, `FR-DATA-015`). No hard blocker; two low-severity documentation-hygiene issues are recorded in the Gemini handoff.

Authoritative sources read: `AGENTS.md`; `docs/PROJECT.md`; `docs/ARCHITECTURE.md`; `docs/CHANGELOG.md`; `app/services/data/README.md`; upstream READMEs `app/utils/README.md`, `app/services/brokers/README.md`. Existing code inspected: `app/services/data/contracts/*` (13 files), `app/services/data/storage/{database.py,locking.py,__init__.py}`, `app/services/data/__init__.py`, `tests/data/**`.

---

## 1. Ownership and prohibited responsibilities

**Owns:** historical + real-time market-data acquisition/normalization/provenance/quality/availability/alignment; historical market+account tables, local CSV/Parquet datasets, cache, source policy, job/checkpoint state, feed status, durable audit storage; shared SQLite connections, path-scoped write locking, and migration execution (other domains keep their own tables/migrations); normalization of raw broker/provider reads into `MarketDataset`, `AccountStateSnapshot`, `MarketContextEvidence`, `FXConversionEvidence`; source capability/readiness/licensing/fallback/rate-limit/timeout/breaker/promotion policy; deterministic resampling/alignment/tick-aggregation/synthetic generation; bounded update jobs/backfills and minimal internal feed lifecycle.

**Prohibited (does NOT own):** strategy/indicator/risk/sizing/order/dispatch/reconciliation/simulated-fill decisions; broker connections/adapters/sessions/credentials (Brokers owns these; secrets resolved by Utils and injected via `BrokerConnectionConfig`); **Data never invokes any `BrokerAdapter` mutation — all broker access is read-only through `MarketDataProvider`/`AccountProvider`/`CalculationProvider`**; other domains' tables/schemas/migrations; public streaming subscriptions, automatic feed-gap backfill, historical calendar reconstruction, TSDB selection, unapproved source promotion; raw DataFrames/SDK objects/sockets/credentials/DB sessions crossing the public API; silent fallback, stale-cache use, gap repair, interpolation, hidden migration, or precision coercion. (README §1; ARCHITECTURE "Data Domain Contract Boundary"; NFR-DATA-006.)

## 2. Owned and consumed contracts (owner / version)

**Owned (defined here; names/versions/owners verified consistent with `docs/PROJECT.md` lines 731–734, 768):**

| Contract | Version | Owner | Schema ID | Key consumers |
|---|---|---|---|---|
| `MarketDataset` | v1 | Data | `data.market_dataset.v1` | Indicators, Strategy, Trading, Simulation, Analytics, Optimization, Research, Portfolio, UI/API |
| `AccountStateSnapshot` | v1 | Data | `data.account_state_snapshot.v1` | Strategy, Risk, Trading, Portfolio |
| `MarketContextEvidence` | v1 | Data | `data.market_context_evidence.v1` | Risk (interpreter); Trading (carrier only), UI/API (views) |
| `FXConversionEvidence` | v1 | Data | `data.fx_conversion_evidence.v1` | Risk, Simulation, Analytics, Portfolio |
| `AuditEventQuery` / `AuditEventPage` | v1 | Data | (namespaced) | UI/API, Risk |

**Consumed (referenced, never redefined):** `AuthContext` v1 (Utils) ✔ exported by `app/utils/__init__.py`; `AuditEvent` v1 (Utils) ✔; `BrokerAdapter` read traits v1 (Brokers) ✔ `MarketDataProvider`/`AccountProvider`/`CalculationProvider`/`BrokerAdapter` present in `app/services/brokers/contracts/protocols.py`; `BrokerResult`/`BrokerError` v1 (Brokers); `BrokerConnectionEvent`/subscription DTOs v1 (Brokers). All upstream dependencies exist and are importable.

## 3. Section 4 feature (module) implementation order

Lowest → highest dependency (README §2 manifest; §2 module dependency diagram):

1. `contracts/` — **Completed**
2. `storage/` — **Partial** (database + locking done; migrations/datasets/cache/audit/exports remain)
3. `sources/` — Missing
4. `access/` — Missing
5. `processing/` — Missing
6. `jobs/` — Missing
7. `feeds/` — Missing
8. `public_api/` (+ package-root `__init__`) — Missing

## 4. File order within every feature + 5. Exact FR-per-file assignment

Authoritative file-to-requirement manifest (README §2). Status column reflects on-disk verification.

| Order | File | FR(s) | Status |
|---:|---|---|---|
| 1 | `contracts/errors.py` | 012/013 | Completed |
| 2 | `contracts/records.py` | 001–003 | Completed |
| 3 | `contracts/sources.py` | 010/011 | Completed |
| 4 | `contracts/market.py` | 004–007 | Completed |
| 5 | `contracts/broker.py` | 008 (009 removed) | Completed |
| 6 | `contracts/market_context.py` | 075/076 | Completed |
| 7 | `contracts/fx.py` | 078/079 | Completed |
| 8 | `contracts/audit.py` | 087/088 | Completed |
| 9 | `contracts/storage.py` | 089 | Completed |
| 10 | `contracts/reference.py` | 090 | Completed |
| 11 | `contracts/jobs.py` | 091 | Completed |
| 12 | `contracts/feeds.py` | 092 | Completed |
| 13 | `contracts/__init__.py` | 093 | Completed |
| 14 | `storage/database.py` | 014 | Completed |
| 15 | `storage/locking.py` | 016 | Completed |
| **16** | **`storage/migrations.py`** | **015** | **Missing → NEXT** |
| 17 | `storage/datasets.py` | 017/018 | Missing |
| 18 | `storage/cache.py` | 019/020 | Missing |
| 19 | `storage/audit.py` | 021/077 | Missing |
| 20 | `storage/__init__.py` | 094 | Missing (empty marker) |
| 21 | `sources/protocol.py` | 022–024 | Missing |
| 22 | `sources/registry.py` | 025 | Missing |
| 23 | `sources/identity.py` | 095 | Missing |
| 24 | `sources/policy.py` | 026/027 | Missing |
| 25 | `sources/broker.py` | 028 (029 removed) | Missing |
| 26 | `sources/local.py` | 096 | Missing |
| 27 | `sources/external.py` | 097 | Missing |
| 28 | `sources/__init__.py` | 098 | Missing |
| 29 | `access/historical.py` | 030 | Missing |
| 30 | `access/reference.py` | 031–033 | Missing |
| 31 | `access/sessions.py` | 034/035 | Missing |
| 32 | `access/account.py` | 099 | Missing |
| 33 | `access/market_context.py` | 085 | Missing |
| 34 | `access/fx.py` | 086 | Missing |
| 35 | `access/__init__.py` | 100 | Missing |
| 36 | `processing/timeframes.py` | 101 | Missing |
| 37 | `processing/tabular.py` | 080–083 | Missing |
| 38 | `processing/transforms.py` | 036–038 | Missing |
| 39 | `processing/synthetic.py` | 039 (040 retired) | Missing |
| 40 | `processing/__init__.py` | 102 | Missing |
| 41 | `jobs/models.py` | 103 | Missing |
| 42 | `jobs/backfill.py` | 041–043, 084 | Missing |
| 43 | `jobs/scheduler.py` | 044/045 | Missing |
| 44 | `jobs/__init__.py` | 104 | Missing |
| 45 | `feeds/models.py` | 105 | Missing |
| 46 | `feeds/runtime.py` | 046/047 | Missing |
| 47 | `feeds/status.py` | 048 | Missing |
| 48 | `feeds/__init__.py` | 106 | Missing |
| 49 | `public_api/retrieval.py` | 049–057 | Missing |
| 50 | `public_api/storage.py` | 058/059/070 | Missing |
| 51 | `public_api/processing.py` | 060–064 | Missing |
| 52 | `public_api/jobs.py` | 065–069 | Missing |
| 53 | `public_api/feeds.py` | 071 | Missing |
| 54 | `public_api/__init__.py` | 072 | Missing |
| 55 | `app/services/data/__init__.py` | 073 (074 unused) | Missing (empty marker) |

Removed/retired/unused (must stay absent as active code): `FR-DATA-009`, `FR-DATA-029` (removed), `FR-DATA-040` (retired → Research), `FR-DATA-074` (intentionally unused).

## 6. Existing files — reusable / non-conforming / obsolete / missing

- **Reusable / conforming (in final structure, verified present):** all 13 `contracts/*` files; `storage/database.py`; `storage/locking.py`; `storage/__init__.py` and `app/services/data/__init__.py` as intentional empty structural markers; completed tests under `tests/data/{unit,integration,usage}`.
- **Non-conforming:** none found. On-disk file set matches the manifest exactly; no stray/legacy files (`_common.py`, `DataGateway`, duplicate caches, `TicksGenerator`, facade/aliases) exist — the CAP-DATA-020 cleanup is already satisfied in the tree.
- **Obsolete:** none.
- **Missing (expected, per manifest):** `storage/migrations.py`, `storage/datasets.py`, `storage/cache.py`, `storage/audit.py`, and every file in `sources/`, `access/`, `processing/`, `jobs/`, `feeds/`, `public_api/`; the storage and package-root `__init__.py` remain empty markers until their export FRs (094 / 073).

The migration contracts the next feature needs are present and complete: `MigrationStep(domain, migration_id, checksum, statements)`, `MigrationRequest(domain, steps, request_id)` (ordered, unique, ownership-checked), `MigrationResult(domain, applied_ids, skipped_ids, request_id)` in `contracts/storage.py:134-207`, and are exported by `contracts/__init__.py`. The `data_migration_ledger` invariants are specified (README §4.2 persisted-state manifest: unique `(domain, migration_id)`, immutable checksum + applied-at). **No guessing is required to build `FR-DATA-015`.**

## 7. Tests and usage examples required per feature

Locations (README §7): `tests/data/unit/` (every public symbol + failure path), `tests/data/integration/` (`WF-DATA-*` collaborations/boundaries), `tests/data/usage/` (one runnable `test_usage_*` per `FR-DATA-*`). Coverage gate ≥ 80% branch; ruff + `ruff format --check` + strict mypy must pass (`uv run ... app/services/data`).

Per-feature required tests:
- **contracts/ (done):** `test_usage_contracts.py`, `test_usage_market_context.py`, `test_usage_fx.py`; unit `test_records/errors/source_contracts/market_contracts/broker_contracts/market_context/fx_contracts/audit_contracts/storage_contracts/reference_contracts/job_contracts/feed_contracts/import_boundaries`.
- **storage/:** usage all in `tests/data/usage/test_usage_storage.py` (`FR-014–021, 077, 094`); unit `test_migrations.py` (015), `test_datasets.py` (017/018), `test_cache.py` (019/020), `test_audit_storage.py` (021/077), `test_storage_imports.py` (094); integration `test_local_dataset.py` (WF-003).
- **sources/:** usage `test_usage_sources.py`; unit `test_source_protocol/registry/policy/identity/local_source/external_source/broker_source/source_imports`; integration `test_source_promotion.py` (WF-011), `test_broker_boundary.py` (WF-013).
- **access/:** usage `test_usage_access.py` (+ market_context/fx); unit `test_historical_access/reference_access/sessions/account_access/market_context_access/fx_access/access_imports`; integration `test_historical_retrieval.py` (WF-001), `test_market_context_boundary.py` (WF-014), `test_fx_conversion_evidence.py` (WF-015), `test_simulation_boundary.py` (WF-012).
- **processing/:** usage `test_usage_processing.py`; unit `test_timeframes/tabular/transforms/synthetic/processing_imports`; integration `test_processing.py` (WF-004).
- **jobs/:** usage `test_usage_jobs.py`; unit `test_backfill/scheduler/job_models/job_imports`; integration `test_backfill.py` (WF-007).
- **feeds/:** usage `test_usage_feeds.py`; unit `test_feed_runtime/feed_status/feed_models/feed_imports`; integration `test_feed_runtime.py` (WF-008).
- **public_api/:** usage `test_usage_api.py` (`FR-049–073`); unit `test_public_api.py`, plus package-root/public-api export tests.

## 8. Section 3 workflows completable only after multiple features

Every `WF-DATA-*` is cross-cutting; none is satisfiable by a single feature. Earliest completion points:

- `WF-DATA-003` Local load/save → after `storage/{locking,datasets}` + `public_api/storage`.
- `WF-DATA-011` Source readiness/promotion → after `sources/policy` (+ `storage`).
- `WF-DATA-013` Account snapshot → after `sources/broker` + `access/account` + Brokers read traits (present).
- `WF-DATA-001/002` Historical retrieval → after `sources` (protocol/registry/policy/adapters) + `storage/cache` + `access/historical` + `public_api/retrieval`.
- `WF-DATA-009` Symbol discovery/metadata/availability → after `sources` + `access/reference` + `public_api/retrieval`.
- `WF-DATA-010` Hours/sessions/volume → after `access/sessions` + `public_api/retrieval`.
- `WF-DATA-004` Resample/align/aggregate → after `processing/{timeframes,tabular,transforms}` + `public_api/processing`.
- `WF-DATA-005` Synthetic → after `processing/{timeframes,synthetic}` + `public_api/processing`.
- `WF-DATA-014` Market-context evidence → after `access/market_context` (depends on historical/reference/sessions).
- `WF-DATA-015` FX evidence → after `access/fx` (depends on historical/reference).
- `WF-DATA-007` Update job/backfill → after `jobs/*` (which depend on access + processing + storage + sources).
- `WF-DATA-008` Internal feed/status → after `feeds/*` + `sources` + `storage`.
- `WF-DATA-012` Simulation boundary → after `access/historical` (validates Data returns canonical data only).

## 9. Contradictions between the DATA README and `docs/PROJECT.md`

No contradiction on any **governed field**: contract name, version, owner, and consumer set match between README §1 and `docs/PROJECT.md` (lines 731–734, 768). Two low-severity documentation-hygiene inconsistencies were found (see handoff `ISSUE-001`, `ISSUE-002`). Neither forces a build guess.

## 10. Recommended sequence of bounded implementation tasks

One independently testable feature per approved cycle, in manifest order (AGENTS §3; README §8):

1. **`storage/migrations.py` (`FR-DATA-015`)** — next. `run_domain_migrations(MigrationRequest) -> MigrationResult`; acquire the shared write lock, validate ownership/order/checksums, apply domain-owned steps exactly once, maintain immutable `data_migration_ledger`. Raises `SCHEMA_MIGRATION_FAILED` / `CONCURRENT_WRITE_LOCKED`.
2. `storage/datasets.py` (`FR-DATA-017/018`).
3. `storage/cache.py` (`FR-DATA-019/020`).
4. `storage/audit.py` (`FR-DATA-021/077`).
5. `storage/__init__.py` (`FR-DATA-094`) — storage export gate.
6. `sources/` in file order: `protocol` → `registry` → `identity` → `policy` → `broker` → `local` → `external` → `__init__` (`FR-DATA-022–028, 095–098`).
7. `access/` in file order: `historical` → `reference` → `sessions` → `account` → `market_context` → `fx` → `__init__` (`FR-DATA-030–035, 085/086, 099/100`).
8. `processing/`: `timeframes` → `tabular` → `transforms` → `synthetic` → `__init__` (`FR-DATA-101, 080–083, 036–039, 102`).
9. `jobs/`: `models` → `backfill` → `scheduler` → `__init__` (`FR-DATA-103, 041–043/084, 044/045, 104`).
10. `feeds/`: `models` → `runtime` → `status` → `__init__` (`FR-DATA-105, 046/047, 048, 106`).
11. `public_api/`: `retrieval` → `storage` → `processing` → `jobs` → `feeds` → `__init__` (`FR-DATA-049–071, 072`).
12. `app/services/data/__init__.py` (`FR-DATA-073`) — package-root export gate.

Each cycle: update README status first → implement smallest slice → add `test_usage_*` + unit (+ integration when a workflow closes) → run targeted `ruff`/`ruff format --check`/`mypy`/`pytest` for the touched files → run the Data completion gate for the slice → mark `Completed` only after verification.

---

## GEMINI HANDOFF REPORT

> Paste everything below directly into the build agent. It is self-contained. The DATA domain is **cleared to build** — the next feature is `storage/migrations.py` (`FR-DATA-015`). The two items below are **low-severity documentation-hygiene fixes** to apply as a docs-only change; they do not block coding `FR-DATA-015` and must not alter any code.

### Context you need
- Repo: HaruQuantAI. Governance authority order: Owner → `AGENTS.md` → `docs/PROJECT.md` → `docs/ARCHITECTURE.md` → `docs/CHANGELOG.md`.
- Update docs before code (AGENTS §6). Decision hygiene: statuses across authoritative docs must not diverge (AGENTS §6). Wait for the exact phrase `APPROVED: EXECUTE` before modifying any file (AGENTS §2/§3). These are documentation-only edits; do not touch `app/services/data/**/*.py`.

### ISSUE-001 — Owned-contract status token diverges across authoritative docs
- **Severity:** Low (documentation hygiene; not a build blocker).
- **What is wrong, with evidence:** In `app/services/data/README.md` §1 "Shared contracts → Owned by this domain" (lines 67–73), the Status column reads `Missing` for `MarketDataset`, `AccountStateSnapshot`, `MarketContextEvidence`, `FXConversionEvidence`, and `AuditEventQuery`/`AuditEventPage`. But those contract types are implemented and verified — README §4.1 marks every `contracts/*` file `Completed`, the §7 "Section 4.1 completion evidence" checklist is all `[X]`, and `docs/PROJECT.md` (lines 731–734, 768) registers all five as `Partial`. Per the README's own status definitions (§3), `Missing` = "Not implemented or not verified", which is false for these contract types. So three authoritative locations disagree: README §1 = `Missing`, README §4.1 = `Completed`, PROJECT.md = `Partial`.
- **Correct recommendation:** Align README §1 with `docs/PROJECT.md`. Set the Status column for all five owned-contract rows to `Partial` (contract type defined and tested; producing operations and cross-domain consumers not yet built). Do not change name/version/owner/counterparty/purpose — those already match and are correct.
- **Exact steps:**
  1. Edit `app/services/data/README.md` §1 table (lines 67–73). In each of the five owned-contract rows, change the leading `| Missing |` cell to `| Partial |`. Change nothing else in those rows.
  2. Do not edit §4.1 (`Completed` there is correct — it describes the contract files) and do not edit `docs/PROJECT.md` (already `Partial`).
  3. Record the change in `docs/CHANGELOG.md` under `[Unreleased] → Changed` as a documentation-only status reconciliation (no implementation status advanced).
  4. **Validation:** `grep -nE '\| (Missing|Partial) \| \`MarketDataset\`' app/services/data/README.md` and confirm all five rows read `Partial`; confirm they match `docs/PROJECT.md` lines 731–734 and 768. No code, so no tests run; confirm `git diff` touches only `README.md` and `CHANGELOG.md`.

### ISSUE-002 — Module dependency diagram omits the `sources → jobs` edge
- **Severity:** Low (documentation hygiene; acyclic build order is unaffected).
- **What is wrong, with evidence:** `app/services/data/README.md` §2 "Module dependency diagram" (lines 252–280) lists edges `S-->J` and `A-->J` and `P-->J` into `jobs`, but has no `R-->J` (sources→jobs) edge. However the file-dependency table for `jobs/scheduler.py` (line 1274) declares its Local dependencies as `backfill.py, storage, sources`, and `jobs/backfill.py` (line 1273) declares `access, processing, storage, contracts`. So `jobs` really does depend on `sources`, but the module-level diagram does not show it. (The manifest order already places `sources` (21–28) before `jobs` (41–44), so no cycle exists.)
- **Correct recommendation:** Add the missing `R --> J` edge to the module dependency diagram so it matches the file-dependency tables. Purely a diagram correction.
- **Exact steps:**
  1. Edit `app/services/data/README.md` §2 module dependency `mermaid` block (around lines 263–279). Add a line `    R --> J` alongside the existing `S --> J`, `A --> J`, `P --> J` edges.
  2. Confirm no edge introduces a cycle: allowed order is `C → S → R → A → P → J → F → API`; `R --> J` is forward-only. Leave all other edges unchanged.
  3. Record in `docs/CHANGELOG.md` `[Unreleased] → Changed` as a documentation-only diagram correction.
  4. **Validation:** re-read the diagram and the file tables at lines 1273–1274; confirm the diagram now reflects `sources → jobs`. Confirm `git diff` touches only `README.md` and `CHANGELOG.md`.

### After the two docs fixes — proceed to build `FR-DATA-015`
- **Feature:** `app/services/data/storage/migrations.py`, export `run_domain_migrations(request: MigrationRequest) -> MigrationResult`.
- **Spec:** README §4.2 (`FR-DATA-015` row line 1021; persisted-state manifest line 1006; module flow + rules). Dependencies already present: `storage/database.py` (`execute_transaction`), `storage/locking.py` (`acquire_write_lock`), `contracts/errors.py` (`DataError`, manifest), and `contracts/storage.py` migration contracts (`MigrationStep`/`MigrationRequest`/`MigrationResult`, lines 134–207, exported by `contracts/__init__.py`).
- **Behavior:** acquire the shared path-scoped write lock; validate ownership/order/checksums; apply each domain-owned `MigrationStep` exactly once inside bounded transactions; maintain the immutable `data_migration_ledger` (unique `(domain, migration_id)`, immutable checksum + applied-at evidence); idempotently skip already-applied steps; reject any modification to an applied step. Import performs no env read, connection, filesystem mutation, or schema work.
- **Errors:** `DataError[SCHEMA_MIGRATION_FAILED | CONCURRENT_WRITE_LOCKED]` (plus the executor's redacted `DB_*`/`DATABASE_ERROR` mappings). No raw SQL/paths/exception text crosses the boundary.
- **Tests:** add `tests/data/unit/test_migrations.py::test_run_domain_migrations_rejects_modified_applied_step()` and `tests/data/usage/test_usage_storage.py::test_usage_migrations_run_domain_migrations()`; keep `storage/__init__.py` an empty marker until `FR-DATA-094`.
- **Gate:** `uv run ruff check app/services/data`; `uv run ruff format --check app/services/data`; `uv run mypy app/services/data`; `uv run pytest tests/data/unit/test_migrations.py tests/data/usage/test_usage_storage.py`; then the Data slice completion gate (≥ 80% branch coverage on the new file). Update README `FR-DATA-015` status to `Completed` with file:line evidence and add a `CHANGELOG.md` `ADD-*` entry only after verification passes.
- **Rollback:** revert the new `migrations.py` and its two test additions; docs edits revert via `git checkout -- app/services/data/README.md docs/CHANGELOG.md`.
