# Implementation Plan: Persistence Domain Remediation (Post-Audit TASK-PERSISTENCE-REMEDIATION-1)

> **Task ID:** `TASK-PERSISTENCE-REMEDIATION-1`
> **Iteration:** `1`
> **Branch:** `backend`
> **Baseline Commit:** `a99cd758f1972511a74e9122511cfc5aaa3d1833` (plus the uncommitted persistence working tree — the audited candidate this remediation corrects)
> **Audit of record:** Domain Implementation Audit of `D-PERSISTENCE` performed 2026-09-20 against the same revision/working tree (26 controls: 10 PASS, 11 PARTIAL, 3 FAIL, 2 N/A).

Follow-up work on the same task appends a clearly labelled iteration to this
file. Do not create a second plan for the same task run.

---

### User Review Required

> [!IMPORTANT]
> Critical design decisions requiring explicit owner sign-off before execution:
>
> 1. **Schema redefinition without compatibility migrations.** The persistence
>    domain has never been committed or deployed; every database created so far
>    is a throwaway (`tmp_path` test DB or the gitignored `data/` smoke DB).
>    This plan therefore redefines migration v1 and removes the dead `staged`
>    column **without** writing upgrade migrations for interim schemas. Confirm
>    no persistence-domain database outside throwaway paths needs preserving.
> 2. **Additive protocol changes keep capability major `@1`.**
>    `RetentionService.get_audit_history(...)` becomes a public protocol
>    operation and `SnapshotService.restore_snapshot(...)` gains an optional
>    `expected_checksum_sha256` keyword. Both are additive (no consumer or
>    implementer outside this domain exists), so majors stay `1` per FIP-05.
> 3. **`docs/PROJECT.md` status flip is ordered last.** The Persistence row
>    changes `Missing` → `Completed` only after work packages 1–9 are verified,
>    so no authority ever claims completion ahead of evidence.
> 4. **Commit remains owner-gated.** This plan ends at the walkthrough; the Git
>    commit happens only on explicit owner authorization (AGENTS §6).
> 5. **`FR-PERSISTENCE-CONCURRENCY_INSERT` is currently false at runtime**
>    (audit probe: repeated `store_artifact` raises raw
>    `sqlite3.IntegrityError`). WP1 fixes behavior, not just the test.

### Open Questions

> [!NOTE]
> `- NONE` — all audit findings map to a work package below. One accepted
> residual is explicitly scoped out (see §6 Non-Goals: `DatabankCapacityError`
> remains unused; eviction-by-`None` is the documented admission-gate
> semantic).

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**: The 2026-09-20 domain audit found the
  persistence implementation mechanically green (architecture check, 49 owner
  tests, ruff, mypy strict, `ci_check.py` exit 0 at 89.76% coverage) but
  non-conformant on three FAILs and eleven PARTIALs. This task remediates all
  of them in one surgical pass so the domain may truthfully hold `Completed`
  status with a complete evidence chain:
  - `FIP-02` FAIL — `FR-PERSISTENCE-CONCURRENCY_INSERT` disproven at runtime.
  - `FIP-23` FAIL — `docs/PROJECT.md` says `Missing` while README says
    `Completed`; README tables contradict code.
  - `FIP-26` FAIL — no acceptance manifests, no plan/walkthrough trail, no
    Git-linked history.
  - PARTIALs — retention purge trusts stale plans (`FIP-20`), snapshot module
    executes raw SQLite outside the persistence boundary (`FIP-14`), base
    schema bypasses the migration ledger with duplicated index DDL
    (`FIP-14/15`), dead persistence builders and dead schema state (`FIP-16`),
    protocol/public-surface drift (`FIP-13`), example function naming
    (`FIP-08`), missing idempotency/absence/unwind/removal tests
    (`FIP-10/11/18`).
- **Ratified Requirements**: `FR-PERSISTENCE-CONCURRENCY_INSERT`,
  `FR-PERSISTENCE-COPY_MOVE` (atomic move), `FR-PERSISTENCE-SAFE_PURGE`
  (execution-time fail-closed), plus the ARCH-001…006 invariants and the
  FIP-26 evidence obligations recorded in
  [app/services/persistence/README.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/README.md).
  Audit remediation ordering follows §5.7 of
  [docs/dev/domain_implementation_audit.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/domain_implementation_audit.md).
- **Usage Evidence**: `tests/examples/02_persistence.py` remains the
  consolidated offline harness; WP7 renames its per-feature functions to the
  canonical `example_02_<slug>()` shape and the verification run must show all
  7 features, including a repeated-insert idempotency demonstration in the
  artifacts section.

## 2. Files Read (Audit Trail)

All files below were read in full during the 2026-09-20 audit; findings cited
per file:

- [app/services/persistence/README.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/README.md) — registry, FR table, decisions; found dependency-column and config-table drift.
- [app/contracts/persistence.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/persistence.py) — 7 capability tokens @1, protocols, DTOs, error hierarchy (`RetentionReferenceBlockedError` defined but unused).
- [app/services/persistence/persistence.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/persistence.py) — `SCHEMA_SQL`, `PersistenceDatabaseManager`; found dead `record_migration`/`mark_artifact_promoted`, dead `staged` column, eager schema init outside ledger.
- [app/services/persistence/database.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/database.py) — SPEC/lifecycle verified; public `manager` property not in protocol.
- [app/services/persistence/artifacts.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/artifacts.py) — non-idempotent `insert_artifact` path; public `compute_sha256` helper.
- [app/services/persistence/migrations.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py) — checksummed ledger verified fail-closed; duplicate index DDL under second names.
- [app/services/persistence/databanks.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/databanks.py) — `move_member` is copy-then-remove in two transactions.
- [app/services/persistence/retention.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/retention.py) — `execute_purge` trusts plan; unused `_artifact_store`; public `get_audit_history` not in protocol.
- [app/services/persistence/snapshots.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/snapshots.py) — raw `sqlite3` connections + `PRAGMA integrity_check` in feature module; public `compute_file_sha256`.
- [app/services/persistence/parquet_store.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/parquet_store.py) — conformant; no changes planned.
- [app/registry.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py) — all 7 factories registered; profiles verified; no changes needed.
- [app/kernel/feature.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/kernel/feature.py), [app/kernel/bootstrapper.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/kernel/bootstrapper.py), [app/kernel/capability.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/kernel/capability.py) — `FeatureSpec` shape (no `config_keys` field in this kernel), `CapabilityUnavailableError` raised by `Runtime` at bootstrapper.py:212 for unfulfilled requires (used by WP8 tests).
- [tests/services/persistence/](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/) (all 7 files) — tmp_path isolation verified; no idempotency/absence/unwind/removal tests exist.
- [tests/examples/02_persistence.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/02_persistence.py) — offline/temp-clean verified; `run_*` naming deviates from canonical `example_<NN>_<slug>()`.
- [docs/PROJECT.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/docs/PROJECT.md) — line 60: Persistence `Missing` (authority conflict).
- [docs/dev/evidence/features/FEAT-WORKSPACE-SETTINGS/acceptance.json](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/evidence/features/FEAT-WORKSPACE-SETTINGS/acceptance.json) — manifest exemplar whose field set WP9 replicates.
- [docs/dev/evidence/reimplementation.json](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/evidence/reimplementation.json) — `SQX144-EV-000006` resolves (line 789).
- [docs/templates/implementation-plan.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/docs/templates/implementation-plan.md), [docs/templates/walkthrough.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/docs/templates/walkthrough.md) — canonical task templates.
- [pyproject.toml](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/pyproject.toml) — `pyarrow>=18` present; coverage floor 80 with branch measurement; pytest config.

## 3. Proposed Changes & Implementation Order

### Contracts layer

- `[MODIFY]` [app/contracts/persistence.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/persistence.py)
  - Add `get_audit_history(operation_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]` to `RetentionService` (fitted docstring).
  - Add optional keyword `expected_checksum_sha256: str | None = None` to `SnapshotService.restore_snapshot`.
  - No capability token or major changes.

### Domain persistence boundary (`app/services/persistence/persistence.py`)

- `[MODIFY]` persistence.py
  - **Idempotent artifact insert**: `insert_artifact` performs, inside its
    existing `BEGIN IMMEDIATE` transaction, a `SELECT` by `artifact_id`
    first; on hit it returns the existing `ArtifactRecord` unchanged (no
    lineage rewrite); on miss it inserts artifact + lineage as today. The
    `BEGIN IMMEDIATE` write lock serializes concurrent writers, making
    check-then-insert race-free under SQLite's single-writer model.
  - **Remove dead state**: drop the `staged` column from `SCHEMA_SQL`, from
    `insert_artifact`'s signature/body, and from `get_artifact`'s
    `WHERE ... AND staged = 0` filter.
  - **Delete dead builders**: remove `record_migration` and
    `mark_artifact_promoted` (zero callers, grep-verified).
  - **New snapshot mechanics**: add `verify_sqlite_integrity(database_path:
    Path) -> None` (opens connection, `PRAGMA integrity_check`, raises
    `sqlite3.DatabaseError` on non-`ok`) and `restore_database(source_path:
    Path) -> None` (checkpoint → `sqlite3` backup API → checkpoint). These
    absorb the raw-connection work currently in `snapshots.py`.
  - **Atomic member move**: add `move_member_between_databanks(source_project,
    source_databank, target_project, target_databank, artifact_id) ->
    DatabankMemberRecord` executing insert-into-target and
    delete-from-source in one transaction, so
    `FR-PERSISTENCE-COPY_MOVE`'s atomicity claim is real. (Copy stays
    non-destructive and unchanged.)

### Feature modules

- `[MODIFY]` [app/services/persistence/artifacts.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/artifacts.py)
  - `promote_artifact`: after computing `sha256_hash`, when an explicit
    `artifact_id` collides with a cataloged artifact whose hash differs,
    raise typed `ArtifactIntegrityError` (fail-closed identity guard);
    identical content re-promotion now succeeds idempotently via the manager
    change. Wrap any residual `sqlite3.IntegrityError` from the manager into
    typed `ArtifactIntegrityError` (`from exc`).
  - Rename module helper `compute_sha256` → `_compute_sha256` (no external
    importers; grep-verified).
- `[MODIFY]` [app/services/persistence/retention.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/retention.py)
  - Extract `_collect_blocking_reasons(artifact_id, active_refs) ->
    list[str]` shared by `plan_purge` and `execute_purge`; `execute_purge`
    re-validates every eligible ID **at execution time** and raises
    `RetentionReferenceBlockedError` (already defined in the contract,
    previously unused) when a plan has gone stale.
  - Use `self._artifact_store.get_artifact(...)` for existence/size in
    `execute_purge`, making the declared `ARTIFACT_STORE` dependency real;
    drop the unused `_db_service` attribute if nothing else consumes it after
    this change.
- `[MODIFY]` [app/services/persistence/snapshots.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/snapshots.py)
  - Replace direct `sqlite3.connect`/`PRAGMA`/backup usage with the new
    `PersistenceDatabaseManager` methods; remove the `sqlite3` import from
    this feature module. `restore_snapshot` verifies
    `expected_checksum_sha256` (when provided) via the renamed
    `_compute_file_sha256` before restoring.
  - Rename `compute_file_sha256` → `_compute_file_sha256`.
- `[MODIFY]` [app/services/persistence/databanks.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/databanks.py)
  - `move_member` delegates to the new single-transaction manager operation
    (raises the same `DatabankNotFoundError` semantics as `copy_member`).
- `[MODIFY]` [app/services/persistence/migrations.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py)
  - `BUILTIN_MIGRATIONS` becomes `((1, "0001_initial_schema", SCHEMA_SQL),
    (2, "0002_secondary_indexes", <idx_persistence_views_scope +
    idx_persistence_lineage_parent>))`, importing `SCHEMA_SQL` from the
    persistence module — one authoritative DDL source; the old
    duplicate-index v1 SQL is deleted.
  - Rename `compute_checksum` → `_compute_checksum`.
  - Manager bootstrap note: `PersistenceDatabaseManager.__init__` keeps its
    idempotent `CREATE TABLE IF NOT EXISTS` bootstrap so `DatabaseService`
    alone yields a usable schema; the ledger remains the authoritative
    applied record (existing tests asserting pending `[1, 2]` and
    `current_version() == 0` before `apply_all()` remain valid).
- `[MODIFY]` [app/services/persistence/database.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/database.py)
  - Remove the public `manager` property (not in the `DatabaseService`
    protocol; no callers — grep-verified). Rename `get_default_db_path` →
    `_default_db_path` (used only by `DatabaseConfig.default_factory`) and
    drop it from `__all__`.
- No changes: `parquet_store.py`, `app/registry.py`.

### Tests

- `[MODIFY]` [tests/services/persistence/test_artifacts.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_artifacts.py)
  - `test_store_artifact_idempotent_by_content_identity`: same payload twice
    → same `artifact_id`, no exception, exactly one catalog row (assert via
    `get_artifact` + direct count query), replaying with identical
    `parent_ids` is stable.
  - `test_promote_explicit_id_conflict_fails_closed`: explicit `artifact_id`
    reused for different content → `ArtifactIntegrityError`.
- `[MODIFY]` [tests/services/persistence/test_retention.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_retention.py)
  - `test_stale_plan_purge_fails_closed`: build plan for an orphan, then add
    a databank membership for that artifact, then `execute_purge(plan)` →
    `RetentionReferenceBlockedError`, artifact still present, no audit row.
- `[MODIFY]` [tests/services/persistence/test_snapshots.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_snapshots.py)
  - `test_restore_with_expected_checksum`: matching checksum restores;
    mismatched `expected_checksum_sha256` → `SnapshotError` with DB unchanged.
- `[MODIFY]` [tests/services/persistence/test_databanks.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_databanks.py)
  - Extend `test_copy_and_move_member`: after `move_member`, source query
    returns no row and target has it (already covered) — add failure-path
    assertion that a move into a missing target databank leaves the source
    membership intact (single-transaction proof).
- `[NEW]` [tests/services/persistence/test_composition.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_composition.py)
  - `test_required_capability_absence_blocks_startup`: `Runtime` with
    database + databanks (no artifacts) raises `CapabilityUnavailableError`
    at composition (bootstrapper.py:212 semantics).
  - `test_partial_startup_failure_unwinds`: a stub feature whose `start`
    raises after `provide` — exiting the `Runtime` context manager propagates
    the error and previously provided capabilities are withdrawn
    (`require` inside the exited context raises `CapabilityUnavailableError`).
  - `test_physical_removal_preserves_retained_state`: compose the full domain,
    write an artifact + databank row, stop; recompose without
    `ParquetFeature`/`SnapshotsFeature`/`ArtifactsFeature` — unrelated
    features start, and the on-disk artifact payload files and database rows
    remain intact (no implicit purge).

### Example

- `[MODIFY]` [tests/examples/02_persistence.py](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/02_persistence.py)
  - Rename to canonical FIP-08 shape (call sites updated, behavior unchanged):
    `example_02_database`, `example_02_migrations`, `example_02_snapshots`,
    `example_02_artifacts`, `example_02_retention`, `example_02_databanks`,
    `example_02_parquet_store`.
  - In `example_02_artifacts`, add a repeated `store_artifact` of the parent
    payload demonstrating idempotent canonical insertion (prints "already
    cataloged — identical identity returned").

### Documentation and evidence

- `[MODIFY]` [app/services/persistence/README.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/README.md)
  - Registry table: databanks and retention Required capabilities list both
    `persistence.database@1` and `persistence.artifacts@1` (matching SPECs).
  - Replace the representative `schema_version` / `operation_timeout_s` /
    `resource_limit` config table with the real per-module config keys
    (`DatabaseConfig`: `database_path`, `timeout_s`, `busy_timeout_ms`,
    `wal_mode`; `ArtifactConfig`: `artifacts_dir`, `staging_dir`;
    `DatabankConfig`: `default_capacity`; `MigrationConfig`:
    `migrations_dir`, `custom_migrations`; `RetentionConfig`:
    `artifacts_dir`; `SnapshotConfig`: `snapshot_dir`; `ParquetConfig`:
    `market_dir`).
  - Persisted-state wording: schema v1 = ledgered `0001_initial_schema`
    applied by `FEAT-PERSISTENCE-MIGRATIONS` (bootstrap init is idempotent,
    ledger authoritative); drop the "staged quarantining" implication tied to
    the removed column (staging remains filesystem-level).
  - Add the Section-7-style acceptance table linking all seven
    `FEAT-PERSISTENCE-*` manifests, test files, and `example_02_*` names;
    bind `ATW-PERSISTENCE-PUBLISH-001` to
    `FEAT-PERSISTENCE-ARTIFACTS` evidence.
  - Note `move_member` single-transaction atomicity and
    `execute_purge` execution-time re-validation under the corresponding FRs.
- `[MODIFY]` [docs/PROJECT.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/docs/PROJECT.md)
  - Line 60 domain row: Persistence `Missing` → `Completed` — **executed only
    as WP9's final step**, after all verification below is green.
- `[NEW]` `docs/dev/evidence/features/FEAT-PERSISTENCE-{DATABASE,MIGRATIONS,SNAPSHOTS,ARTIFACTS,RETENTION,DATABANKS,PARQUET}/acceptance.json`
  (7 files) — mirror the workspace exemplar's field set exactly:
  `feature_id`, `domain: "D-PERSISTENCE"`, `status: "ACCEPTED"`,
  `requirements` (FR IDs; artifacts also carries
  `ATW-PERSISTENCE-PUBLISH-001`), `verified_at_utc`, `owner_module`,
  `public_contract`, `symbols`, `capabilities`, `persistence`
  (`module: app/services/persistence/persistence.py`,
  `namespace: "persistence.v1"`, feature-relevant `tables`),
  `test_target`, `usage_example:
  "tests/examples/02_persistence.py::example_02_<slug>"`, `verification`
  (bounded command + exit code + flags), `tested_revision` (candidate HEAD
  SHA at verification time; the containing commit is the terminal identity),
  `fingerprints` (sha256 of owner module / contract / domain README at
  verification time), `pipeline_stages`
  (`Interfaces`/`UI`: `NOT_APPLICABLE` with feature-specific reason; others
  `PASS` from real evidence). All values must be computed, never templated.
- `[NEW]` `.agents/logs/2026-09-20T134225_persistence-remediation-1/walkthrough.md`
  — authored after verification per
  [docs/templates/walkthrough.md](file:///C:/Users/rharu/AppDev/HaruQuantAI-backend/docs/templates/walkthrough.md).

### Sequential Implementation Order

1. Contracts (protocol additions) — unblocks feature edits.
2. `persistence.py` (idempotent insert, dead-state/builder removal, snapshot
   mechanics, atomic move).
3. Feature modules in dependency order: `artifacts.py`, `retention.py`,
   `snapshots.py`, `databanks.py`, `migrations.py`, `database.py`.
4. Tests: extend the four existing files, add `test_composition.py`.
5. Example renames + idempotency demonstration.
6. README reconciliation.
7. Full verification (§7) and audit-probe re-run.
8. Evidence manifests + walkthrough (only from actual results).
9. `docs/PROJECT.md` status flip → owner commit gate.

## 4. Dependencies and Contracts

- Public contract changes are additive only; capability tokens and majors
  (`persistence.*@1`) are unchanged; no consumer outside the domain resolves
  these capabilities (grep-verified), so no ripple.
- Cross-feature wiring stays capability-based: databanks/retention resolve
  `DATABASE_SERVICE`/`ARTIFACT_STORE` via `FeatureContext.require` (fail-closed
  `CapabilityUnavailableError` per kernel).
- All SQL, DDL, and raw connections remain in
  `app/services/persistence/persistence.py` (ARCH-006 / Architecture Rule 7);
  after WP3 no feature module imports `sqlite3` except through the manager.
- No changes to `app/registry.py`, kernel, or other domains.

## 5. Blockers, Risks, and Trade-offs

- **Schema redefinition risk** (see User Review §1): mitigated by the
  uncommitted-state assumption; interim local DBs (gitignored `data/`) keep
  their physical shape but nothing reads the removed column.
- **Idempotency semantics**: check-then-insert inside `BEGIN IMMEDIATE` is
  serialized by SQLite's single-writer lock; the returned pre-existing record
  is not mutated (no lineage rewrite on replay) — documented in docstrings.
- **`SCHEMA_SQL` as migration v1** changes ledger checksums relative to any
  DB created from the pre-remediation working tree; such DBs must be deleted
  and recreated (acceptable per the assumption above). Existing migration
  tests' expectations (`pending == [1, 2]`, rollback, checksum tamper) are
  preserved by design.
- **Protocol additions**: additive; if the owner prefers strict
  no-protocol-change, `get_audit_history` can be underscored instead —
  flagged for sign-off.
- **Trade-off accepted**: `execute_purge` fail-closed on stale plans may
  abort a multi-artifact purge that was partially valid; callers re-plan.
  This is the audit-mandated safe direction (`FIP-20`).
- **Non-risk**: coverage — additions are small; the 89.76% aggregate and
  per-module ≥85% margins absorb them; new tests raise coverage.

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope**: WP1 idempotent insertion + typed collision errors; WP2
  execution-time purge re-validation + real artifact dependency; WP3 snapshot
  mechanics into the persistence boundary + optional checksum verify; WP4
  single DDL authority + atomic move + dead code/state removal; WP5
  protocol/hygiene renames; WP6 README/PROJECT reconciliation; WP7 example
  canonical naming; WP8 composition/absence/unwind/removal/idempotency tests;
  WP9 seven acceptance manifests + walkthrough + status flip; owner commit
  preparation.
- **Out of Scope / Non-Goals**: no new features or FRs; no changes to
  `parquet_store.py`, `workspace.py`, gateway, or kernel; no Interfaces/UI
  work (`FIP-24/25` remain N/A); no performance budgets or benchmarks (none
  declared); no change to eviction admission-gate semantics or
  `DatabankCapacityError` (documented residual); no Git operations short of
  the owner-gated commit; no provider/remote/release claims.

## 7. Verification Plan

### Automated Tests

Per-work-package focused commands (editing cadence, `--no-cov`):

```bash
uv run pytest --no-cov tests/services/persistence/test_artifacts.py
uv run pytest --no-cov tests/services/persistence/test_retention.py
uv run pytest --no-cov tests/services/persistence/test_snapshots.py
uv run pytest --no-cov tests/services/persistence/test_databanks.py
uv run pytest --no-cov tests/services/persistence/test_migrations.py
uv run pytest --no-cov tests/services/persistence/test_database.py
uv run pytest --no-cov tests/services/persistence/test_composition.py
uv run pytest --no-cov tests/services/persistence/
```

Audit-probe re-run (must now print `SAME ID: True`, no exception), against a
temp directory:

```bash
uv run python <probe>: store_artifact(payload) twice; assert identical artifact_id
```

### Usage Evidence Run

```bash
uv run python -m tests.examples.02_persistence
```

Must print all seven sections plus the idempotent re-insert line and exit 0.

### Quality Pipeline

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python scripts/architecture_check.py
uv run python scripts/ci_check.py   # full gate: tests + 80% floor + examples + smoke
```

### Manual Verification

- Owner reviews the walkthrough, the seven manifests (spot-check
  fingerprints against `sha256sum` of the named files), and the README /
  PROJECT.md diffs before authorizing the commit (AGENTS §2.5–2.6, §6).

## 8. Rollback & Contingency

All changes live in the uncommitted working tree; rollback is `git checkout --
<paths>` / deleting untracked new files. Because the pre-remediation tree is
itself uncommitted, the safety net is the baseline audit record plus this
plan; if remediation must be abandoned mid-way, restore audited files from
the task's before/after fingerprints captured in the walkthrough. No database
rollback is required: every test and the example operate on `tmp_path` /
`TemporaryDirectory` storage only; the gitignored `data/` smoke database is
disposable. Contingency for a failing WP4 ledger change: revert
`BUILTIN_MIGRATIONS` to index-only migrations and keep bootstrap init (the
audit PARTIAL stands, documented as residual).

```text
ALLOWED_WRITE_PATHS:
- app/contracts/persistence.py
- app/services/persistence/persistence.py
- app/services/persistence/database.py
- app/services/persistence/artifacts.py
- app/services/persistence/databanks.py
- app/services/persistence/migrations.py
- app/services/persistence/retention.py
- app/services/persistence/snapshots.py
- app/services/persistence/README.md
- docs/PROJECT.md
- tests/services/persistence/test_artifacts.py
- tests/services/persistence/test_databanks.py
- tests/services/persistence/test_database.py
- tests/services/persistence/test_migrations.py
- tests/services/persistence/test_parquet_store.py
- tests/services/persistence/test_retention.py
- tests/services/persistence/test_snapshots.py
- tests/services/persistence/test_composition.py
- tests/examples/02_persistence.py
- docs/dev/evidence/features/FEAT-PERSISTENCE-DATABASE/acceptance.json
- docs/dev/evidence/features/FEAT-PERSISTENCE-MIGRATIONS/acceptance.json
- docs/dev/evidence/features/FEAT-PERSISTENCE-SNAPSHOTS/acceptance.json
- docs/dev/evidence/features/FEAT-PERSISTENCE-ARTIFACTS/acceptance.json
- docs/dev/evidence/features/FEAT-PERSISTENCE-RETENTION/acceptance.json
- docs/dev/evidence/features/FEAT-PERSISTENCE-DATABANKS/acceptance.json
- docs/dev/evidence/features/FEAT-PERSISTENCE-PARQUET/acceptance.json
- .agents/logs/2026-09-20T134225_persistence-remediation-1/implementation-plan.md
- .agents/logs/2026-09-20T134225_persistence-remediation-1/walkthrough.md
END_ALLOWED_WRITE_PATHS:
```
