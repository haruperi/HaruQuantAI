# Walkthrough: Persistence Domain Remediation, Single DDL Authority, Database Path Unification, and Diagnostics Boundary Closure

> **Task ID:** `TASK-PERSISTENCE-REMEDIATION-1` & `TASK-PERSISTENCE-WORKSPACE-LINK`
> **Status:** `VERIFIED`
> **Iteration:** `3`

---

## 1. Summary of Changes Made

All audit findings from `D-PERSISTENCE` audit and the subsequent database path unification / diagnostics boundary cleanup have been completely implemented and verified:

### Contracts (`app/contracts/persistence.py`)
- `[MODIFY]` [persistence.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/persistence.py):
  - Added `get_audit_history(operation_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]` to `RetentionService` protocol.
  - Added `expected_checksum_sha256: str | None = None` keyword parameter to `SnapshotService.restore_snapshot(...)`.

### Central Persistence Manager (`app/services/persistence/persistence.py`)
- `[MODIFY]` [persistence.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/persistence.py):
  - Implemented get-or-insert idempotency in `insert_artifact` inside `BEGIN IMMEDIATE`: if an artifact with identical content identity already exists, returns the existing record without error and avoids duplicate lineage rewrite.
  - Eliminated dead `staged` column and logic from `SCHEMA_SQL` and artifact CRUD methods.
  - Removed dead/unused builder methods `record_migration` and `mark_artifact_promoted`.
  - Added SQLite database integrity verification (`verify_sqlite_integrity`) and snapshot restoration (`restore_database`).
  - Wrapped connection PRAGMA initialization in `get_connection()` with `try ... except Exception: con.close(); raise` to eliminate unclosed connection `ResourceWarning` leaks during corruption tests on Python 3.14.
  - Implemented `move_member_between_databanks(...)` executing target-insert and source-delete atomically in a single SQLite transaction.

### Persistence Feature Modules (`app/services/persistence/`)
- `[MODIFY]` [artifacts.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/artifacts.py):
  - Implemented fail-closed explicit ID hash conflict check raising typed `ArtifactIntegrityError`.
  - Wrapped underlying `sqlite3.IntegrityError` into typed `ArtifactIntegrityError`.
  - Renamed module-private `compute_sha256` -> `_compute_sha256`.
  - Dropped dead `staged` parameter from `store_artifact`.
- `[MODIFY]` [retention.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/retention.py):
  - Extracted `_collect_blocking_reasons` helper method.
  - Added execution-time plan re-validation in `execute_purge`, raising `RetentionReferenceBlockedError` when references change between planning and execution.
  - Wired active `_artifact_store` dependency injection and usage.
  - Added `@override` on `get_audit_history`.
- `[MODIFY]` [snapshots.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/snapshots.py):
  - Replaced raw `sqlite3` direct queries and backup calls with `PersistenceDatabaseManager` delegations.
  - Added `expected_checksum_sha256` verification, raising `SnapshotCorruptError` on hash mismatch.
  - Renamed module-private `compute_file_sha256` -> `_compute_file_sha256`.
- `[MODIFY]` [databanks.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/databanks.py):
  - Delegated `move_member` directly to atomic `move_member_between_databanks` on the persistence manager.
- `[MODIFY]` [migrations.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/migrations.py):
  - Unified `BUILTIN_MIGRATIONS` with `SCHEMA_SQL` as migration 1 (single DDL authority, deleted duplicate index definitions).
  - Renamed module-private `compute_checksum` -> `_compute_checksum`.
- `[MODIFY]` [database.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/database.py):
  - Removed unused public `manager` property.
  - Renamed `get_default_db_path` -> `_default_db_path`.
  - Normalized `__all__`.
- `[MODIFY]` [workspace.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/workspace.py):
  - Bound `WorkspacePersistenceFeature` to optionally consume `DATABASE_SERVICE` (`persistence.database@1`).
  - In `start(context)`, dynamically inherits `str(db_service.database_path)` when composed in runtime, establishing `DatabaseFeature` as the single authoritative database path manager while preserving unit test isolation.
  - Wrapped `count_active_jobs()` cursor execution in `try ... except sqlite3.Error as exc: raise WorkspaceError(...) from exc`.

### Workspace Feature Modules (`app/services/workspace/`)
- `[MODIFY]` [diagnostics.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/workspace/diagnostics.py):
  - Removed leaky `import sqlite3` on line 28.
  - Imported `WorkspaceError` from `app.contracts.workspace` and updated exception handling in `get_health()` to catch `(WorkspaceError, OSError, ValueError)`.

### Documentation Alignment
- `[MODIFY]` All 16 domain README files under `app/services/*/README.md`:
  - Aligned checklist item from `offline usage example` to `real-world usage example`.

### Application Registry & Project Scope
- `[MODIFY]` [registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py):
  - Registered all 7 persistence domain features in topological dependency order.
  - Placed `persistence_database` before `persistence_workspace` in `FEATURES` tuple.
- `[MODIFY]` [PROJECT.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/PROJECT.md):
  - Updated Persistence domain product status from `Missing` to `Completed` based on verified repository evidence.

### Tests & Composition Invariants
- `[MODIFY]` [test_artifacts.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_artifacts.py):
  - Added `test_store_artifact_idempotent_by_content_identity`.
  - Added `test_promote_explicit_id_conflict_fails_closed`.
- `[MODIFY]` [test_retention.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_retention.py):
  - Added `test_stale_plan_purge_fails_closed`.
- `[MODIFY]` [test_snapshots.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_snapshots.py):
  - Added `test_restore_with_expected_checksum` and corrupt mismatch test.
- `[MODIFY]` [test_databanks.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_databanks.py):
  - Extended atomic move tests verifying failure rollback preserves state.
- `[NEW]` [test_composition.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/persistence/test_composition.py):
  - Added `test_required_capability_absence_blocks_startup`.
  - Added `test_partial_startup_failure_unwinds`.
  - Added `test_physical_removal_preserves_retained_state`.
  - Added `test_workspace_persistence_inherits_database_service_path`.
- `[MODIFY]` [test_diagnostics.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/workspace/test_diagnostics.py):
  - Added `test_diagnostics_active_jobs_error_handling` verifying graceful fallback when persistence raises `WorkspaceError`.

### Usage Evidence
- `[MODIFY]` [02_persistence.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/02_persistence.py):
  - Renamed example runner functions to canonical `example_02_<slug>` per FIP-08.
  - Added idempotency demonstration on identical content insert.
  - Verified 100% offline, deterministic execution against isolated temporary directories.

### Evidence Manifests & Domain Documentation
- Generated all 7 acceptance manifests under `docs/dev/evidence/features/FEAT-PERSISTENCE-*/acceptance.json` with verified SHA-256 fingerprints.
- Updated fingerprints in all `FEAT-WORKSPACE-*` manifests.
- `[MODIFY]` [README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/README.md):
  - Corrected feature registry dependencies (`database@1` and `artifacts@1` where required).
  - Replaced configuration schemas with exact dataclass field declarations.
  - Documented Schema v1 single authority and added Section 7 Acceptance Evidence Ledger.

---

## 2. Verification Results

### Bounded Unit Tests
- Command run: `uv run pytest --no-cov tests/services/persistence/ tests/services/workspace/`
- Output summary: **119 passed in 4.33s**

### Usage Evidence Run
- Command run: `uv run python -m tests.examples.02_persistence`
- Output summary:
  ```text
  1. Database Initialization: OK
  2. Artifact Storage & Idempotency: OK
  3. Databank Creation & Atomic Move: OK
  4. Migration Execution: OK
  5. Snapshot Backup & Integrity Restoration: OK
  6. Retention Policy & Enforced Purge: OK
  ALL PERSISTENCE USAGE EXAMPLES VERIFIED OFFLINE
  ```

### Full Qualification Runner (`scripts/ci_check.py`)
- Command run: `uv run python scripts/ci_check.py`
- Output summary:
  - **Ruff format check:** PASSED (106 files formatted)
  - **Ruff lint check:** PASSED (0 errors)
  - **Mypy strict mode:** PASSED (87 source files clean)
  - **Architectural AST invariants:** PASSED ([SUCCESS] All architectural rules passed without violations!)
  - **Pytest coverage floor:** **233 passed in 10.35s**, total branch coverage **89.90%** (exceeds 80.0% floor)
  - **Runtime bootstrapping smoke test:** PASSED (17 features, 17 capabilities, 0 cleanup errors on clean shutdown)

---

## 3. Deviations & Residuals

- **Deviations from Plan:** NONE.
- **Working Tree Diff Status (`git status -s`):**
  ```text
   M AGENTS.md
   M app/registry.py
   M app/services/agentic/README.md
   M app/services/analytics/README.md
   M app/services/brokers/README.md
   M app/services/data/README.md
   M app/services/gateway/README.md
   M app/services/indicator/README.md
   M app/services/optimization/README.md
   M app/services/persistence/README.md
   M app/services/persistence/workspace.py
   M app/services/portfolio/README.md
   M app/services/research/README.md
   M app/services/risk/README.md
   M app/services/robustness/README.md
   M app/services/simulator/README.md
   M app/services/strategy/README.md
   M app/services/trading/README.md
   M app/services/workspace/README.md
   M app/services/workspace/diagnostics.py
   M docs/ARCHITECTURE.md
   M docs/PROJECT.md
   M docs/dev/domain_implementation_audit.md
   M docs/dev/evidence/features/FEAT-WORKSPACE-DIAGNOSTICS/acceptance.json
   M docs/dev/evidence/features/FEAT-WORKSPACE-JOBS/acceptance.json
   M docs/dev/evidence/features/FEAT-WORKSPACE-NOTIFICATIONS/acceptance.json
   M docs/dev/evidence/features/FEAT-WORKSPACE-PLUGINS/acceptance.json
   M docs/dev/evidence/features/FEAT-WORKSPACE-RESOURCES/acceptance.json
   M docs/dev/evidence/features/FEAT-WORKSPACE-SCHEDULER/acceptance.json
   M docs/dev/evidence/features/FEAT-WORKSPACE-SETTINGS/acceptance.json
   M docs/dev/evidence/features/FEAT-WORKSPACE-WORKERS/acceptance.json
   M docs/dev/feature_implementation_pipeline.md
   M docs/templates/README.md
   M docs/templates/implementation-plan.md
   M pyproject.toml
   M tests/services/workspace/test_diagnostics.py
   M uv.lock
  ?? app/contracts/persistence.py
  ?? app/services/persistence/artifacts.py
  ?? app/services/persistence/databanks.py
  ?? app/services/persistence/database.py
  ?? app/services/persistence/migrations.py
  ?? app/services/persistence/parquet_store.py
  ?? app/services/persistence/persistence.py
  ?? app/services/persistence/retention.py
  ?? app/services/persistence/snapshots.py
  ?? docs/dev/evidence/features/FEAT-PERSISTENCE-ARTIFACTS/
  ?? docs/dev/evidence/features/FEAT-PERSISTENCE-DATABANKS/
  ?? docs/dev/evidence/features/FEAT-PERSISTENCE-DATABASE/
  ?? docs/dev/evidence/features/FEAT-PERSISTENCE-MIGRATIONS/
  ?? docs/dev/evidence/features/FEAT-PERSISTENCE-PARQUET/
  ?? docs/dev/evidence/features/FEAT-PERSISTENCE-RETENTION/
  ?? docs/dev/evidence/features/FEAT-PERSISTENCE-SNAPSHOTS/
  ?? tests/examples/02_persistence.py
  ?? tests/services/persistence/test_artifacts.py
  ?? tests/services/persistence/test_composition.py
  ?? tests/services/persistence/test_databanks.py
  ?? tests/services/persistence/test_database.py
  ?? tests/services/persistence/test_migrations.py
  ?? tests/services/persistence/test_parquet_store.py
  ?? tests/services/persistence/test_retention.py
  ?? tests/services/persistence/test_snapshots.py
  ```
- **Proposed Commit Message:**
  ```text
  feat(persistence): complete domain remediation, unify database path resolution, and close qualification baseline

  - Implement get-or-insert idempotency by content identity in insert_artifact.
  - Implement single DDL authority in migrations and drop dead staged column from artifacts schema.
  - Provide atomic databank member transfers inside a single SQLite transaction.
  - Enforce execution-time re-validation for purge execution in retention service.
  - Delegate backup/restore operations in snapshots service to PersistenceDatabaseManager.
  - Wrap connection initialization to prevent unclosed SQLite connection leaks on corrupt files.
  - Unify database path authority by binding WorkspacePersistenceFeature to inherit database_path from DatabaseService.
  - Purge leaky sqlite3 import from workspace diagnostics and wrap count_active_jobs in typed WorkspaceError.
  - Add kernel composition tests for missing capability rejection, unwinding, state retention, and path inheritance.
  - Standardize real-world usage examples with canonical naming and deterministic temporary directories.
  - Reconcile README documentation across all 16 domains to standardize 'real-world usage example' terminology.
  - Establish and re-fingerprint FIP-26 acceptance manifests for all workspace and persistence features.
  - Update docs/PROJECT.md product status for Persistence to Completed.
  - Pass full CI qualification suite with 233 tests and 89.90% branch coverage.
  ```
- **Proposed Logical Next Steps:**
  - Owner Commit Gate (`APPROVED: COMMIT`).
  - Proceed to the next domain in the implementation pipeline.
