# Implementation Plan: D-DATA Remediation — Truthful Completion & Integrity

> **Task ID:** `TASK-DATA-REMEDIATION-1`
> **Iteration:** `1`
> **Branch:** `backend`
> **Baseline Commit:** `22d171f404802ef2a42b39c4911d3536ba4223e7` + uncommitted working tree (the audited candidate; see AUDIT below)
> **Audit of Record:** Domain audit executed 2026-09-20 per `docs/dev/domain_implementation_audit.md` — 10 PASS / 7 PARTIAL / 7 FAIL / 2 N/A. This plan remediates every FAIL and PARTIAL finding.

---

### User Review Required

> [!IMPORTANT]
> **DECISION-1 — Fate of the orphan `data_cache_entries` table (destructive).**
> Recommended: **drop the table** via ledger migration `0003_drop_data_cache_entries` (`DROP TABLE IF EXISTS`). It has zero readers/writers; caching is already served by the in-memory cache plus immutable dataset manifests. Dropping a table is a Destructive Action under `AGENTS.md` §4 and requires explicit owner authorization. Alternative (no deletion): implement a write-through on-disk cache index against the table in `MarketDataServiceImpl` — more code, duplicates dataset manifests, not recommended.
>
> **DECISION-2 — MT4 HST/FXT and MT5 binary export scope.**
> Recommended: **implement now** (Iteration 5) from the SQX clean-room donors already inspected in the original plan (`CsvExporter`, `MT4ExportJob`, `MT5ExportJob`), making `FR-DATA-EXPORT_FORMATS` truthful. Alternative: defer to a future task and downgrade `FR-DATA-EXPORT_FORMATS` to `Partial` in the README with a documented closure requirement.
>
> **DECISION-3 — Baseline commit before remediation.**
> The entire D-DATA implementation is uncommitted. Recommended: owner authorizes a **baseline commit of the audited candidate first** (fixing only the fabricated walkthrough block per Iteration 7.4 is part of that commit), so this remediation is a clean, revertable diff on top. If declined, rollback relies on the untracked-file manifest in §8.
>
> **Breaking-change posture:** all contract edits are **additive within the existing `@1` capability majors** (new DTO fields with defaults, new protocol methods, new error subclasses). No capability major bump is required; no consumer signature breaks.

### Open Questions

> [!NOTE]
> - NONE blocking. DECISION-1/2/3 above are the only owner sign-offs; defaults are the recommended options and the plan is written against them.

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**:
  The D-DATA audit found the domain declares `Completed` for scope it does not implement, contains a fail-open fabricated operation (`sync_connectors`), dead/orphan durable state, six silently ignored settings, a fabricated evidence receipt, and zero acceptance manifests. Goal: make every `Completed` claim in `app/services/data/README.md` traceable to real, tested behavior; close all 14 non-PASS audit controls; and produce source-bound acceptance evidence — without expanding the domain boundary or breaking any `@1` contract.
- **Ratified Requirements** (from `app/services/data/README.md` §4, restated as the acceptance targets of this task):
  - `FR-DATA-IMPORT_DELIMITERS` — delimiter/datetime/header **auto-detection** (currently absent).
  - `FR-DATA-EXPORT_FORMATS` — CSV + **MT4 HST/FXT + MT5** export (currently CSV only, `format_name` ignored).
  - `FR-DATA-CONNECTOR_SYNC` — idempotent, resumable sync recording fetched intervals and dedup counts (currently a no-op success receipt).
  - `FR-DATA-INGESTION_NORMALIZATION` — dedup + monotonic sort + **quality evaluation during ingestion** (quality service currently injected but never called).
  - `FR-DATA-DATASET_IMMUTABILITY` — **content-addressed** identity for identical source bytes + parameters (currently uuid4 token).
  - `FR-DATA-QUALITY_ANOMALIES` — SQX anomaly set incl. **tick Crossed Quotes (Bid > Ask)** and **ATR-multiplier** spikes (currently median-range; no tick evaluation).
  - `FR-DATA-DATA_REPAIR` — drop / **interpolate** / **clamp spikes** policies with persisted audit (currently two of four policy fields silently ignored; audit never persisted).
  - `FR-DATA-SESSION_WINDOWS` partial — strict window parsing (currently silent hour clamping).
  - `FIP-05/15/16/20/22/23/26` control closures per the audit report (dead config, orphan tables, fail-closed posture, enforced bounds, README reconciliation, acceptance manifests).
- **Usage Evidence**:
  `tests/examples/04_data.py` extended to demonstrate: auto-detected import, MT4-format export, real sync over a mock connector (honest counts), quality report persistence during fetch, content-addressed re-publish idempotency, and interpolated/clamped repair. All offline, deterministic, secret-safe, `tempfile`-cleaned.

## 2. Files Read (Audit Trail)

- [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) — registry, FRs, config/dependency declarations audited against implementation.
- [app/contracts/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/data.py) — DTOs, protocols, errors, capability tokens; additive-change surface identified.
- [app/services/data/instruments.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/instruments.py), [sessions.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/sessions.py), [imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/imports_exports.py), [market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py), [datasets.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/datasets.py), [quality.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/quality.py), [resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/resampling.py), [universes.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/universes.py) — audited line-by-line; deviations catalogued in the audit report.
- [app/services/persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py) — schema, orphan tables, immutability guard semantics.
- [app/services/persistence/migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py) — `BUILTIN_MIGRATIONS` ledger (v1, v2) and checksum mechanism reused for migration v3.
- [app/registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py) — registration confirmed complete; no changes needed.
- [tests/services/data/](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/) (10 files, 36 tests) — existing coverage map; gaps identified (`market_data.py` 64%).
- [tests/examples/04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py) — real output captured by audit re-run (differs from walkthrough §2 block).
- [.agents/logs/2026-09-20T193500_data-full-implementation/implementation-plan.md + walkthrough.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md) — original task history; fabricated example-output block located in §2.
- [docs/dev/evidence/features/FEAT-PERSISTENCE-DATABASE/acceptance.json](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/evidence/features/FEAT-PERSISTENCE-DATABASE/acceptance.json) — canonical manifest schema (fields, fingerprints, pipeline stages) replicated for the 9 new manifests.
- [docs/templates/implementation-plan.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/templates/implementation-plan.md), [docs/dev/domain_implementation_audit.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/domain_implementation_audit.md) — governing templates.

## 3. Proposed Changes & Implementation Order

### 3.1 Contracts layer — `app/contracts/data.py`

- `[MODIFY]` [app/contracts/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/data.py):
  - **New errors** (additive): `InvalidSessionWindowError(DataError)`; `UnsupportedExportFormatError(DataError)`.
  - **`SyncReport`**: add `intervals: tuple[SyncInterval, ...] = ()` and new DTO `SyncInterval(provider, symbol, start, end, records_fetched, records_deduplicated, dataset_id)` (frozen dataclass, defaulted field keeps construction compatible).
  - **`QualityService` protocol**: add `evaluate_tick_quality(ticks: list[TickRecord]) -> QualityReport` (additive method; SQX Crossed Quotes on ticks).
  - **`RepairPolicy`**: no shape change — `clamp_spikes`, `fill_small_gaps`, `max_fill_gap_bars` become honored (were silently ignored).
  - **`build_market_data_request`**: add `start <= end` validation when both provided (`ValueError`, fail-closed).
  - Docstring truth fixes: cache described as in-memory; `export_dataset` supported formats enumerated; `resample_ticks_to_bars` documented as bid-price OHLC basis.

### 3.2 Persistence layer — `app/services/persistence/data.py`

- `[MODIFY]` [app/services/persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py):
  - Register `data.v1` schema in the authoritative ledger: add migration `0003_data_domain` entry to `BUILTIN_MIGRATIONS` in [app/services/persistence/migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py) carrying the `_SCHEMA_SQL` (idempotent `CREATE TABLE IF NOT EXISTS`) so applied checksums are ledger-tracked (FIP-14).
  - Per DECISION-1: append `DROP TABLE IF EXISTS data_cache_entries;` to migration `0003` (destructive — owner-authorized) and remove the table from `_SCHEMA_SQL`.
  - `save_dataset_manifest`: tighten same-`dataset_id` re-save — permitted only when **all** semantic fields match (row_count, quality_score, lineage, parquet_path, hashes, range); any divergence raises `DatasetImmutableError` (closes the silent same-hash mutation hole).
  - `get_quality_report`: unchanged; becomes production-reachable via Iteration 4 wiring.

### 3.3 Feature modules — `app/services/data/*.py`

- `[MODIFY]` [sessions.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/sessions.py):
  - `_parse_time_str` rewritten strict: regex `^(\d{2}):(\d{2})(?::(\d{2}))?$`; out-of-range hour/minute/second or malformed string raises `InvalidSessionWindowError` (no clamping, no silent relaxation). Config: remove nothing; `SessionConfig` unchanged.
- `[MODIFY]` [market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py):
  - **Real `sync_connectors`**: for each registered connector (filtered by `provider_ids`), for each requested symbol (or connector-advertised default): consult `list_manifests` to skip already-covered ranges (resumability/idempotency), stream via the connector, dedup + sort, persist via `DATA_DATASETS`, and record a `SyncInterval` with genuine counts. Per-provider failures append to `errors` and do not abort siblings (fail-closed per provider, fail-open never). No connectors registered ⇒ empty `providers_synced`, no fabricated "verified" logging.
  - **Cache bound**: `MarketDataConfig.max_cache_items` enforced via `OrderedDict` FIFO eviction (currently dead). Remove `enable_caching`/`max_cache_items` divergence with README by renaming to README names or updating README (Iteration 7 reconciles README to final field names — implementation is authoritative).
  - **Ingestion quality gate**: in `_fetch_bars_from_connector` / `_fetch_ticks_from_connector`, after dedup/sort: when `self._quality_service` is present, evaluate (`evaluate_quality` / `evaluate_tick_quality`), set `BarRecord.anomaly_flags` bitmasks, compute `quality_score` **before** persisting (manifest immutability ordering), and persist the `QualityReport` via `self._persistence.save_quality_report` when persistence is present. Reports carry the resulting `dataset_id`.
- `[MODIFY]` [datasets.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/datasets.py):
  - **Content-addressed identity**: `dataset_id = f"ds_{symbol}_{timeframe}_{content_hash[:16]}"` where `content_hash` is SHA-256 over a deterministic logical serialization of the sorted records plus normalization parameters (symbol, timeframe, data_kind, schema version) — deliberately **not** the Parquet bytes (writer-version stability). Identical inputs ⇒ identical identity; existing manifest with matching id and hash ⇒ return it without rewriting (idempotent publish). Remove the `uuid4` token.
  - Accept the precomputed `quality_score` (from the ingestion gate) as an optional parameter so manifests publish once with their final score.
- `[MODIFY]` [quality.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/quality.py):
  - **ATR spikes**: Wilder ATR (default period 14, new `QualityConfig.atr_period`); spike when `bar_range > atr * spike_multiplier`; fallback to the current median-range heuristic only when fewer than `atr_period + 1` bars exist (documented). Removes dead `default_spike_multiplier` config field (parameter remains authoritative).
  - **Tick quality**: implement `evaluate_tick_quality` — `CROSSED_QUOTE` when `bid > ask`, plus duplicate `(timestamp, sequence)` and non-monotonic ordering.
  - **Repair honored**: `repair_data` implements `clamp_spikes` (clamp High/Low to the ATR-derived spike cutoff, audit entry per bar) and `fill_small_gaps` (linear-interpolated bars for gaps ≤ `max_fill_gap_bars` using the timeframe step, audit entry per filled bar). Raw input list is never mutated (already true).
  - `gap_tolerance_multiplier` retained and now documented in README.
- `[MODIFY]` [imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/imports_exports.py):
  - **Auto-detection**: when `format_spec is None`, sniff delimiter (comma/semicolon/tab by frequency over the first non-empty lines), detect header (first-row numeric-parse probe), and infer datetime pattern against a bounded candidate list (`%Y.%m.%d %H:%M:%S`, `%Y-%m-%d %H:%M:%S`, `%Y/%m/%d %H:%M`, ISO). Explicit `format_spec` bypasses detection (deterministic). Remove dead `max_error_ratio`; `row_errors` cap becomes `ImportExportConfig.max_row_errors: int = 50` (honored, was hardcoded).
  - **`format_name` honored**: `"csv"` supported; anything else raises `UnsupportedExportFormatError` listing supported formats until Iteration 5 adds `"mt4_hst"`, `"mt4_fxt"`, `"mt5"`.
  - **`session_name` honored**: resolve via `DATA_SESSIONS` (optional dependency, already injected); unknown name ⇒ `SessionNotFoundError` fail-closed; detected session violations recorded into the import lineage anomaly counts (with Iteration 4 quality wiring).
  - **Import quality gate**: run `evaluate_quality` on parsed bars when the quality service is present; persist the report; record `quality_report_id` + `anomaly_counts` in the dataset lineage.
- `[MODIFY]` [universes.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/universes.py): remove dead `allow_empty_baskets` config field (no behavior change).
- `[MODIFY]` [instruments.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/instruments.py): no behavioral change; docstring alignment only (README reconciliation covers config table).
- `[MODIFY]` [resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/resampling.py): honor `clone_to_timezone(session=...)` — when provided, re-anchor bucket/session context in the docstring-truthful minimal form (document that cloning preserves instants; session is used only for validation of resulting session alignment) **or** drop the unused parameter from the protocol; decision implemented as: keep parameter, validate bars remain contiguous, document. Bid-only tick bars documented in contract (3.1).

### 3.4 Tests — `tests/services/data/` and `tests/system/integration/`

- `[MODIFY]` all existing data test files — adapt to strict parsing, honored configs, new dataset-id shape; add FR-ID traceability lines to module docstrings.
- `[MODIFY]` [test_market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_market_data.py): tick streaming path (mock `stream_historical_ticks`), `_search_manifests` path, sync success + per-provider failure branch, cache eviction bound, ingestion quality gate + report persistence, idempotent content-addressed re-publish. Target: `market_data.py` ≥ 80% module coverage.
- `[MODIFY]` [test_quality.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_quality.py): ATR spike golden fixtures, fallback heuristic, tick crossed quotes, clamp/interpolate repair with audit assertions.
- `[MODIFY]` [test_imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_imports_exports.py): auto-detection matrix (`,`/`;`/tab × header/no-header × datetime patterns), unsupported-format rejection, session-name resolution and fail-closed unknown.
- `[MODIFY]` [test_persistence.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_persistence.py): tightened immutability guard (same-id/different-field ⇒ `DatasetImmutableError`), migration v3 ledger application, cache-table drop.
- `[NEW]` [tests/services/data/test_mt_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_mt_exports.py) (Iteration 5): MT4 HST/FXT and MT5 binary writers — golden byte fixtures from clean-room specs, round-trip field checks, atomic-write and cleanup-on-failure.
- `[NEW]` [tests/system/integration/test_data_workflows.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/system/integration/test_data_workflows.py): independently owned `WF-DATA-FETCH` evidence — a fake `BrokerFeedConnector` published under a broker capability token in a real `Runtime` (database + persistence.data + data features) → `MarketDataRequest` fetch → assert published manifest, persisted quality report, second fetch served from cache without connector calls, and `WF-DATA-SYNC` interval recording. Offline, `tmp_path`-isolated.

### 3.5 Example — `tests/examples/04_data.py`

- `[MODIFY]`: extend to demonstrate auto-detected import, MT4-format export (post-Iteration 5), real sync over an in-example mock connector with honest counts, quality-report persistence during fetch, content-addressed idempotency, and repaired/clamped/interpolated outcomes. Step [9/9] label changes from "Connector synchronization verified" to a truthful statement of what was synchronized.

### 3.6 Evidence — `docs/dev/evidence/features/`

- `[NEW]` 9 manifests `FEAT-DATA-{INSTRUMENTS,SESSIONS,IMPORTS-EXPORTS,MARKET_DATA,DATASETS,QUALITY,RESAMPLING,UNIVERSES}` and `FEAT-PERSISTENCE-DATA`, each `acceptance.json` following the `FEAT-PERSISTENCE-DATABASE` schema exactly: requirement IDs, capabilities, persistence mapping, test target, usage example anchor, verification command + exit code, `tested_revision` (the post-remediation owner-authorized commit SHA), SHA-256 fingerprints of owner module / contract / README, and pipeline stages (`Interfaces`/`UI` = `NOT_APPLICABLE` with the audit's rationale).

### 3.7 Documentation — README + original walkthrough

- `[MODIFY]` [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md): §1 persisted-state status → `Completed` (post-wiring) with cache-table removal recorded; §2 registry statuses → `Completed` and the Required-capabilities column rewritten to the **actual** `SPEC` sets (`data.persistence@1` etc.); §4 config table rewritten to the final classes/fields/defaults (implementation-authoritative); §4 dependency/SPEC parity pass; §7 test layout rewritten to the flat `tests/services/data/test_<feature>.py` convention actually used; FR statuses `Completed` only where the full chain (operation → oracle → executable evidence → manifest) exists. Normative §9 sentences for auto-detection/MT formats/ATR verified true.
- `[MODIFY]` [.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md): append a correction iteration block that **replaces the fabricated §2 example output** with the genuine output (audit re-run record) and notes the commit-message scope fix.
- `[NEW]` `.agents/logs/2026-09-20T202806_data-remediation-1/walkthrough.md`: this task's walkthrough with real receipts.

### Sequential Implementation Order

1. **Iteration 1 — Safety & authority (FIP-20):** contracts errors + strict time parsing + `format_name`/`session_name`/`start<=end` fail-closed + honored `RepairPolicy` + real `sync_connectors` + cache bound. Focused tests green.
2. **Iteration 2 — Computational integrity (FIP-21):** content-addressed identity + idempotent publish + tightened manifest guard + ATR spikes + tick crossed quotes + bid-basis documentation.
3. **Iteration 3 — Durable state (FIP-14/15/16):** migration `0003` (schema ledger registration + cache-table drop per DECISION-1) + orphan-closure verification.
4. **Iteration 4 — Ingestion quality gate (FIP-02/09):** fetch + import quality evaluation, report persistence, manifest scoring order, session-violation lineage.
5. **Iteration 5 — Deferred FR scope (DECISION-2):** delimiter/datetime/header auto-detection + MT4 HST/FXT + MT5 exporters with golden fixtures.
6. **Iteration 6 — Evidence & tests (FIP-10/11/12):** coverage lift to ≥80% per module, integration workflow tests, example extension, FR-ID traceability.
7. **Iteration 7 — Documentation & receipts (FIP-23/26):** README reconciliation, original-walkthrough correction block, 9 acceptance manifests bound to the owner-authorized commit, this task's walkthrough, final `ci_check.py`.

## 4. Dependencies and Contracts

- **Public contract** `app/contracts/data.py` — additive-only edits within `@1` majors: `SyncInterval` DTO, `SyncReport.intervals`, `QualityService.evaluate_tick_quality`, `InvalidSessionWindowError`, `UnsupportedExportFormatError`, `build_market_data_request` temporal validation. No removed/renamed public symbols; no capability-key changes.
- **Capability keys consumed** (unchanged): `DATA_PERSISTENCE`, `DATA_DATASETS`, `DATA_QUALITY`, `DATA_SESSIONS`, `BROKER_*` feed tokens (optional) — all via `FeatureContext.require/optional`.
- **Persistence boundary**: all SQL stays in `app/services/persistence/data.py`; migration DDL goes to `BUILTIN_MIGRATIONS` in `app/services/persistence/migrations.py` (schema mechanics owner). No feature module touches raw connections.
- **No new third-party dependencies** — binary MT4/MT5 writers use stdlib `struct`; Parquet paths reuse pyarrow. `pyproject.toml` untouched.

## 5. Blockers, Risks, and Trade-offs

- **Migration v3 touches the shared migration ledger** (owned by D-PERSISTENCE). Risk: checksum drift for existing databases. Mitigation: DDL is idemp (`CREATE TABLE IF NOT EXISTS` + `DROP TABLE IF EXISTS`); applied-manifest checksum is computed from source at first run; verified against a fresh tmp DB and the seed pattern used by v1/v2.
- **Content-addressed ids change identity shape** for newly published datasets. Trade-off accepted (FR requires it); existing dev rows are untouched (additive). Parquet-byte instability across pyarrow versions is avoided by hashing logical content, not file bytes.
- **Sync correctness depends on connector contracts** that (per the D-BROKERS audit) are themselves remediation targets. Mitigation: sync consumes only the two documented streaming shapes, degrades to per-provider `errors` entries, and all tests use offline mocks; no real provider qualification is claimed anywhere.
- **MT4/MT5 binary formats** are clean-room reverse-engineered; golden fixtures pin exact bytes. Risk of format drift is bounded by fixture tests; no proprietary blobs are copied (DEC-DATA-002 preserved).
- **Quality-before-persist ordering** is required by the tightened immutability guard; Iteration 4 implements it explicitly. Forgetting the order fails loudly (`DatasetImmutableError`), not silently.
- **Assumption**: owner authorizes DECISION-1 (drop) and DECISION-2 (implement MT formats). If either flips, only Iterations 3/5 and the README status column change; the rest of the plan is invariant.

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope**: everything in §3 — 7 iterations, 9 acceptance manifests, README/walkthrough reconciliation, integration workflow evidence, per-module ≥80% coverage for `app/services/data/*` and `app/services/persistence/data.py`.
- **Out of Scope / Non-Goals**: no new features beyond ratified FRs; no Interfaces/UI dispatch (remain N/A); no real network provider calls or provider qualification claims; no changes to `app/registry.py`, `docs/PROJECT.md` (status stays `Completed` once truthful), `pyproject.toml`, other domains, or the kernel; no benchmark/soak claims; no purge/retention operations beyond the owner-authorized cache-table drop.

## 7. Verification Plan

### Automated Tests

- Per-iteration focused runs (editing cadence, `--no-cov`, explicit paths):
  ```bash
  uv run pytest --no-cov tests/services/data/test_sessions.py tests/services/data/test_quality.py
  uv run pytest --no-cov tests/services/data/test_market_data.py
  uv run pytest --no-cov tests/services/data/test_imports_exports.py tests/services/data/test_mt_exports.py
  uv run pytest --no-cov tests/services/data/test_persistence.py
  uv run pytest --no-cov tests/system/integration/test_data_workflows.py
  uv run pytest --no-cov tests/services/data
  ```
- Acceptance: all green; `market_data.py` and every data module ≥ 80% in the final coverage report.

### Usage Evidence Run

  ```bash
  uv run python -m tests.examples.04_data
  ```
- Acceptance: full offline run; output block captured verbatim into this task's walkthrough; sync step prints genuine counts only.

### Quality Pipeline

  ```bash
  uv run python scripts/ci_check.py
  uv run python scripts/architecture_check.py
  ```
- Acceptance: ruff/mypy strict/architecture clean; full suite green at the ≥80% aggregate floor; runtime composition `cleanup_errors: 0`.

### Manual Verification

- Owner reviews: DECISION-1 authorization (before Iteration 3), the corrected original-walkthrough block (Iteration 7), the 9 acceptance manifests, and the README reconciliation diff before the commit gate.

## 8. Rollback & Contingency

Step-by-step undo:

1. If DECISION-3 accepted (baseline committed): `git revert` / `git checkout <baseline> -- <ALLOWED_WRITE_PATHS>` restores the audited candidate exactly.
2. If not: restore tracked files via `git checkout -- app/registry.py app/services/data/README.md docs/PROJECT.md pyproject.toml uv.lock`; delete untracked paths created/modified by this task per the manifest recorded at Iteration 1 start: `app/contracts/data.py`, `app/services/data/{datasets,imports_exports,instruments,market_data,quality,resampling,sessions,universes}.py`, `app/services/persistence/data.py`, `tests/services/data/`, `tests/system/integration/`, `tests/examples/04_data.py`, `docs/dev/evidence/features/FEAT-DATA-*/`, `.agents/logs/2026-09-20T202806_data-remediation-1/` (⚠ destructive to the uncommitted implementation — baseline commit strongly recommended).
3. Migration v3 rollback: forward-only per domain policy; contingency is `DROP`-only-of-empty-table (no data loss possible — table has no writers). If v3 must be reverted, a forward `0004` recreating the table is the sanctioned path.
4. No active-database mutation is performed by this task's code outside the ledger-governed idempotent DDL; all tests/examples use `tmp_path` isolation.

```text
ALLOWED_WRITE_PATHS:
- app/contracts/data.py
- app/services/data/instruments.py
- app/services/data/sessions.py
- app/services/data/imports_exports.py
- app/services/data/market_data.py
- app/services/data/datasets.py
- app/services/data/quality.py
- app/services/data/resampling.py
- app/services/data/universes.py
- app/services/persistence/data.py
- app/services/persistence/migrations.py
- tests/services/data/
- tests/system/integration/
- tests/examples/04_data.py
- docs/dev/evidence/features/FEAT-DATA-INSTRUMENTS/
- docs/dev/evidence/features/FEAT-DATA-SESSIONS/
- docs/dev/evidence/features/FEAT-DATA-IMPORTS-EXPORTS/
- docs/dev/evidence/features/FEAT-DATA-MARKET_DATA/
- docs/dev/evidence/features/FEAT-DATA-DATASETS/
- docs/dev/evidence/features/FEAT-DATA-QUALITY/
- docs/dev/evidence/features/FEAT-DATA-RESAMPLING/
- docs/dev/evidence/features/FEAT-DATA-UNIVERSES/
- docs/dev/evidence/features/FEAT-PERSISTENCE-DATA/
- app/services/data/README.md
- .agents/logs/2026-09-20T202806_data-remediation-1/
- .agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md
END_ALLOWED_WRITE_PATHS:
```


---

# Implementation Plan: D-DATA Closure Remediation — Evidence, Documentation & Integrity

> **Task ID:** `TASK-DATA-REMEDIATION-1`
> **Iteration:** `2`
> **Branch:** `backend`
> **Baseline Commit:** `22d171f404802ef2a42b39c4911d3536ba4223e7` (uncommitted working tree candidate)
> **Trigger:** Closure Verification Audit — Code remediation verified genuine; 5 evidence/documentation blockers and 3 non-blocking defects remain.

---

### User Review Required

> [!IMPORTANT]
> **DECISION-1 — Persistence Schema Architecture & Migration Deviation Acceptance.**
> **Recommended:** In [data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py), remove `DROP TABLE IF EXISTS data_cache_entries;` from `_SCHEMA_SQL`. Keep `DATA_SCHEMA_SQL` strictly non-destructive (`CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`), executed cleanly during `initialize_schema()`—matching the pattern established by `FEAT-PERSISTENCE-BROKERS` ([brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/brokers.py)). Explicitly accept this domain-level schema management deviation so that [migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py) remains reserved for control-plane persistence migrations and does not break [test_migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_migrations.py).
> *Alternative:* Register `0003_data_schema` in `BUILTIN_MIGRATIONS` in [migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py) and update [test_migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_migrations.py) asserts from 2 to 3.

> [!IMPORTANT]
> **DECISION-2 — Acceptance Manifests Revision Binding Strategy.**
> All 9 acceptance manifests (`FEAT-DATA-*` and `FEAT-PERSISTENCE-DATA`) will be regenerated with:
> 1. Real source fingerprints (`owner_module_sha256`, `public_contract_sha256`, `domain_readme_sha256`).
> 2. `Interfaces: "NOT_APPLICABLE"` under `pipeline_stages`.
> 3. `tested_revision`: Pre-populated with current commit `22d171f404802ef2a42b39c4911d3536ba4223e7` (or explicit staged indicator), with the final commit SHA bound immediately upon owner commit authorization.

> [!NOTE]
> **DECISION-3 — Truthful Connector Synchronization in Offline Usage Evidence.**
> In [04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py), provide a deterministic in-memory `DemoFeedConnector` to `MarketDataFeature`. Step [9/9] will genuinely synchronize 1 registered provider and verify fetched records, replacing the misleading 0-provider print label.

### Open Questions

> [!NOTE]
> - NONE blocking. All requirements and audit findings are concrete and bounded.

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**:
  Resolve the 5 evidence-and-documentation blockers and 3 non-blocking defects identified by the independent closure verification audit:
  1. Fix defective manifests in `docs/dev/evidence/features/` (missing fingerprints, incorrect `Interfaces: PASS`).
  2. Append explicit correction block to the original walkthrough in `.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md`.
  3. Clean up `_SCHEMA_SQL` in [persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py) by removing destructive runtime `DROP TABLE IF EXISTS`.
  4. Correct 3 conflicting rows in [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) (`InstrumentCatalogConfig`, `DatasetConfig`, and `FEAT-DATA-QUALITY` dependencies).
  5. Provide genuine provider synchronization verification in [tests/examples/04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py).
  6. Non-blocking fixes: parenthesize multi-exception syntax in [imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/imports_exports.py#L911), track dedup count in [market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py), and raise [resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/resampling.py) coverage from 74% to $\ge 80\%$.
- **Ratified Requirements**:
  `FR-DATA-DATASET_IMMUTABILITY`, `FR-DATA-PROVENANCE_LINEAGE`, `FR-DATA-IMPORT_DETECTION`, `FR-DATA-EXPORT_FORMATS`, `FR-DATA-INSTRUMENT_METADATA`, `FR-DATA-BROKER_ALIASES`, `FR-DATA-SESSION_WINDOWS`, `FR-DATA-TIMEZONE_PROJECTION`, `FR-DATA-QUALITY_ANOMALY_RULES`, `FR-DATA-REPAIR_POLICIES`, `FR-DATA-RESAMPLE_BARS`, `FR-DATA-SIMULATE_TICKS`, `FR-DATA-DYNAMIC_BASKETS`, `FR-DATA-POINT_IN_TIME_QUERY`, `FR-DATA-MARKET_DATA_REQUEST`, `FR-DATA-TRANSPARENT_CACHE`, `FR-DATA-CONNECTOR_SYNC`.
- **Usage Evidence**:
  [tests/examples/04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py) executing all 9 capabilities with genuine provider synchronization.

---

## 2. Files Read (Audit Trail)

- [quality.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/quality.py) — checked ATR, gap logic, and SPEC requirements (`DATA_PERSISTENCE`).
- [instruments.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/instruments.py) — verified `InstrumentCatalogConfig(strict_validation=True)`.
- [datasets.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/datasets.py) — verified `DatasetConfig(storage_dir="data/datasets")` and absence of compression field.
- [imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/imports_exports.py#L911) — inspected unparenthesized `except` statement.
- [resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/resampling.py) — checked uncovered branches (74% coverage).
- [market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py) — checked `sync_connectors` and `SyncInterval.records_deduplicated`.
- [persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py) — located `DROP TABLE IF EXISTS data_cache_entries` in `_SCHEMA_SQL`.
- [persistence/migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py) — analyzed `BUILTIN_MIGRATIONS` and relationship to persistence domain.
- [persistence/brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/brokers.py) — confirmed domain persistence pattern using self-contained schema initialization.
- [test_migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_migrations.py) — confirmed hardcoded count of built-in migrations (versions 1 and 2).
- [README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) — verified conflicting configuration table cells and `FEAT-DATA-QUALITY` dependencies row.
- [04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py) — verified step [9/9] connector sync demonstration.
- [.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md) — confirmed absence of correction block.
- [docs/dev/evidence/features/FEAT-BROKERS-MT5/acceptance.json](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/evidence/features/FEAT-BROKERS-MT5/acceptance.json) — verified canonical structure for fingerprints and pipeline stages.

---

## 3. Proposed Changes & Implementation Order

### Component: Documentation & Evidence

- `[MODIFY]` [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md):
  - In Section 2 registry: update `FEAT-DATA-QUALITY` dependencies from `None` to `data.persistence@1`.
  - In Section 4 config table:
    - Update `InstrumentCatalogConfig`: `strict_validation: bool = True` (remove nonexistent `cache_size`).
    - Update `DatasetConfig`: `storage_dir: Path | str = "data/datasets"` (remove nonexistent `compression` field and `var/` path).
    - Update `QualityConfig`: `atr_period: int = 14`, `gap_tolerance_multiplier: float = 1.5`.
- `[MODIFY]` [.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md):
  - Append an explicit `### Historical Correction Block` documenting that the initial example run output was fabricated, replacing it with the verified clean-room execution receipts.
- `[MODIFY]` [docs/dev/evidence/features/FEAT-DATA-*/acceptance.json](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/evidence/features/) (8 manifests) & [FEAT-PERSISTENCE-DATA/acceptance.json](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/evidence/features/FEAT-PERSISTENCE-DATA/acceptance.json):
  - Compute and insert real SHA-256 hashes under `"fingerprints"`: `owner_module_sha256`, `public_contract_sha256`, `domain_readme_sha256`.
  - Update `pipeline_stages.Interfaces` from `"PASS"` to `"NOT_APPLICABLE"`.

### Component: Data Domain & Persistence Services

- `[MODIFY]` [app/services/persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py):
  - Remove `DROP TABLE IF EXISTS data_cache_entries;` from `_SCHEMA_SQL` to ensure non-destructive startup.
- `[MODIFY]` [app/services/data/imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/imports_exports.py):
  - Line 911: Replace `except UnsupportedExportFormatError, DatasetNotFoundError:` with standard `except (UnsupportedExportFormatError, DatasetNotFoundError):`.
- `[MODIFY]` [app/services/data/market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py):
  - Line 282: Calculate `dedup_count = len(records) - len(deduped)` and pass to `SyncInterval(..., records_deduplicated=dedup_count)`.

### Component: Tests & Usage Evidence

- `[MODIFY]` [tests/examples/04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py):
  - Define `DemoFeedConnector` and register it with `MarketDataFeature(..., connectors={"demo_provider": DemoFeedConnector()})`.
  - Update Step [9/9] output print to truthfully report verified provider synchronization of `demo_provider` with record count.
- `[MODIFY]` [tests/services/data/test_resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_resampling.py):
  - Add test cases covering empty bar/tick sequences, unsupported timeframes, boundary timestamps, and error handling in `resample_bars`, `resample_ticks`, `generate_4price_ticks`, and `clone_to_timezone` to raise coverage to $\ge 85\%$.

### Sequential Implementation Order

1. **Service & Persistence Code Updates**:
   - Clean up `_SCHEMA_SQL` in [persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py).
   - Parenthesize `except` in [imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/imports_exports.py).
   - Compute `records_deduplicated` in [market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py).
2. **Test & Example Upgrades**:
   - Add tests to [test_resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_resampling.py) and verify coverage $\ge 80\%$.
   - Wire `DemoFeedConnector` into [04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py) and run offline example.
3. **Documentation & Manifests Reconciliation**:
   - Update [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) config and dependency rows.
   - Append correction block to [.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md).
   - Compute SHA-256 fingerprints and update all 9 `acceptance.json` files with `Interfaces: NOT_APPLICABLE`.
4. **Candidate Qualification**:
   - Run full candidate qualification suite: `uv run python scripts/ci_check.py`.

---

## 4. Dependencies and Contracts

- No public contract modifications; existing tokens (`DATA_*`) and DTOs in [app/contracts/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/data.py) are unchanged.
- Persistence boundaries remain strictly confined to [app/services/persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py).

---

## 5. Blockers, Risks, and Trade-offs

- **Blockers**: None.
- **Risks & Mitigation**:
  - *Risk*: Modifying `BUILTIN_MIGRATIONS` in [migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py) would alter the control-plane persistence ledger and break existing tests.
    *Mitigation*: Maintain self-contained domain schema management in `data.py` (matching `brokers.py`), remove the runtime DROP statement, and obtain explicit owner acceptance under Decision 1.
  - *Risk*: Git revision in manifests cannot be the final commit SHA before the commit exists.
    *Mitigation*: Retain current baseline SHA in manifests, then update `tested_revision` to the actual commit SHA upon owner commit authorization.

---

## 6. Scope Boundaries

- **In Scope**:
  - The 5 audit blockers (manifest fingerprints/stages, walkthrough correction block, non-destructive schema SQL, 3 README config/spec rows, example step 9 connector sync).
  - The 3 non-blocking notes (imports_exports exception syntax, market_data dedup count, resampling test coverage).
  - Candidate qualification via `scripts/ci_check.py`.
- **Out of Scope**:
  - Adding new features, altering public protocol signatures, or modifying other domains (`D-WORKSPACE`, `D-BROKERS`, `D-PERSISTENCE`).

---

## 7. Verification Plan

### Automated Tests

```bash
# Verify focused resampling coverage >= 80%
uv run pytest --cov=app.services.data.resampling tests/services/data/test_resampling.py

# Verify all data domain unit tests pass (59+ tests)
uv run pytest --no-cov tests/services/data/
```

### Usage Evidence Run

```bash
# Verify genuine provider sync in offline example
uv run python tests/examples/04_data.py
```

### Quality Pipeline

```bash
# Verify architectural rules, formatting, typing, and full repository test suite
uv run python scripts/ci_check.py
```

---

## 8. Rollback & Contingency

If verification fails or changes are rejected, restore modified files via `git checkout`:

```text
ALLOWED_WRITE_PATHS:
- app/services/persistence/data.py
- app/services/data/imports_exports.py
- app/services/data/market_data.py
- app/services/data/README.md
- tests/examples/04_data.py
- tests/services/data/test_resampling.py
- .agents/logs/2026-09-20T193500_data-full-implementation/walkthrough.md
- .agents/logs/2026-09-20T202806_data-remediation-1/implementation-plan.md
- docs/dev/evidence/features/FEAT-DATA-DATASETS/acceptance.json
- docs/dev/evidence/features/FEAT-DATA-IMPORTS-EXPORTS/acceptance.json
- docs/dev/evidence/features/FEAT-DATA-INSTRUMENTS/acceptance.json
- docs/dev/evidence/features/FEAT-DATA-MARKET_DATA/acceptance.json
- docs/dev/evidence/features/FEAT-DATA-QUALITY/acceptance.json
- docs/dev/evidence/features/FEAT-DATA-RESAMPLING/acceptance.json
- docs/dev/evidence/features/FEAT-DATA-SESSIONS/acceptance.json
- docs/dev/evidence/features/FEAT-DATA-UNIVERSES/acceptance.json
- docs/dev/evidence/features/FEAT-PERSISTENCE-DATA/acceptance.json
END_ALLOWED_WRITE_PATHS:
```
