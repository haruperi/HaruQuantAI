# Implementation Plan: Data Domain Full Implementation

> **Task ID:** `FEAT-DATA-FULL-IMPLEMENTATION`
> **Iteration:** `1`
> **Branch:** `backend`
> **Baseline Commit:** `22d171fa9e34e569ee80d3cefc8a2aaeececfb53`

---

### User Review Required

> [!IMPORTANT]
> **Complete Greenfield Domain Implementation:**
> We are implementing the complete Data domain (`D-DATA`) covering all 8 ratified features in [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md):
> 1. `FEAT-DATA-INSTRUMENTS` ([instruments.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/instruments.py))
> 2. `FEAT-DATA-SESSIONS` ([sessions.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/sessions.py))
> 3. `FEAT-DATA-IMPORTS-EXPORTS` ([imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/imports_exports.py))
> 4. `FEAT-DATA-MARKET_DATA` ([market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py))
> 5. `FEAT-DATA-DATASETS` ([datasets.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/datasets.py))
> 6. `FEAT-DATA-QUALITY` ([quality.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/quality.py))
> 7. `FEAT-DATA-RESAMPLING` ([resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/resampling.py))
> 8. `FEAT-DATA-UNIVERSES` ([universes.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/universes.py))
>
> **Architectural Invariants Strictly Preserved:**
> - Zero private sibling imports between features; collaboration is mediated strictly via `FeatureContext` and capability tokens in [app/contracts/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/data.py).
> - All schema, parameterized SQL, and transactions are owned by [app/services/persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py) under namespace `data.v1`.
> - Pure standard library kernel compliance (`ARCH-001` through `ARCH-006`).
> - Registration is declarative and explicit in [app/registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py).

### Open Questions

> [!NOTE]
> - NONE. All 8 features, configuration schemas, symbols, and functional requirements are fully defined in the domain README.

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**:
  Implement the Data domain (`D-DATA`) to provide unified quantitative data management: versioned instruments, trading sessions/DST resolution, tabular import/export (CSV, MT4 HST/FXT, MT5), governed market data retrieval (`MarketDataRequest`) with caching and connector sync, immutable Parquet datasets, SQX anomaly quality detection (Gaps, Low/High Problems, Spikes, Crossed Quotes), session-aware resampling & timezone projection, and point-in-time universe constituent tracking.
- **Ratified Requirements**:
  - `FR-DATA-INSTRUMENT_SPECS`: Validation of pip size, point value, tick size, tick step, lot step, min/max volume, commissions, and margin rates.
  - `FR-DATA-BROKER_ALIASES`: Canonical resolution and reversible mapping of broker-specific symbol aliases.
  - `FR-DATA-SESSION_WINDOWS`: Filter out-of-session quotes and mark open/close transitions per schedule.
  - `FR-DATA-TIMEZONE_DST`: Apply timezone offsets and Daylight Saving Time (DST) transitions deterministically.
  - `FR-DATA-IMPORT_DELIMITERS`: Auto-detect delimiters (comma, semicolon, tab), datetime patterns, and header structures.
  - `FR-DATA-EXPORT_FORMATS`: Export normalized datasets to custom tabular CSV and platform formats (MT4 HST/FXT, MT5).
  - `FR-DATA-MARKET_REQUEST`: Dispatch structured `MarketDataRequest` specifications across configured provider feed connectors.
  - `FR-DATA-CACHE_TRANSPARENCY`: Transparent point-in-time caching of fetched bars and ticks avoiding redundant downloads.
  - `FR-DATA-CONNECTOR_SYNC`: Idempotent, resumable connector synchronization implementing `SyncConnectorsCapability`.
  - `FR-DATA-INGESTION_NORMALIZATION`: Automatic deduplication, monotonic timestamp sorting, and quality anomaly evaluation during stream ingestion.
  - `FR-DATA-DATASET_IMMUTABILITY`: Identical source bytes and normalization produce identical content-addressed dataset identities.
  - `FR-DATA-PROVENANCE_LINEAGE`: Manifests record source provider, parser config, hashes, and transformation parents.
  - `FR-DATA-QUALITY_ANOMALIES`: Exhaustively flag data anomalies: Gaps, Low Problems, High Problems, Spikes, and Crossed Quotes.
  - `FR-DATA-DATA_REPAIR`: Explicit user-configured repair policies (drop, interpolate, clamp) without mutating raw sources.
  - `FR-DATA-DETERMINISTIC_RESAMPLING`: Resampling M1/ticks to higher timeframes is deterministic and chunk-invariant.
  - `FR-DATA-TIMEZONE_CLONING`: Project historical bar series from UTC to specified target timezones aligning session opens.
  - `FR-DATA-UNIVERSE_CONSTITUENTS`: Maintain point-in-time constituent membership (`date_from`, `date_to`) eliminating survivorship bias.
- **Usage Evidence**:
  - Offline consolidated scenario in `tests/examples/04_data.py` exercising instrument lookups, session filtering, tabular imports/exports, request-driven market data fetching with cache hits, dataset publishing, quality anomaly scanning & repair, session-aware resampling, timezone cloning, and universe constituent querying.

---

## 2. Files Read (Audit Trail)

- [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) — Single source of truth for the 8 features, configuration classes, symbols, and 17 FRs.
- [app/contracts/brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/brokers.py) — Feed connector protocols and raw chunk contracts consumed by `market_data.py`.
- [app/services/brokers/catalog.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/catalog.py) — Reference for feature structure, slotted config, and lifecycle wiring.
- [app/services/persistence/brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/brokers.py) — Reference for domain-scoped SQLite persistence and pre-seeding.
- [app/registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py) — Explicit application feature factory registry.
- `SQX_REFERENCE_ROOT/internal/libs/SQDataLib.jar` — Inspected `InstrumentManager`, `SessionManager`, `Timezones`, `DataImportEngine`, `NewDataFormat`, `BarType`, `TimeBar`, `BasketOfStocksManager`.
- `SQX_REFERENCE_ROOT/internal/libs/SQTradingLib.jar` — Inspected `QualityChecker`, `DataProblemEvaluator` (`GAP`, `LOW_PROBLEM`, `HIGH_PROBLEM`, `SPIKE`).
- `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DataManagerData.jar` — Inspected `CsvExporter`, `MT4ExportJob`, `MT5ExportJob`, `CloneToTimezoneJob`.

---

## 3. Proposed Changes & Implementation Order

Grouped by component layer, using explicit action tags and clickable links:

### 1. Contracts Layer (`app/contracts/`)

- `[NEW]` [app/contracts/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/data.py):
  - **Capability Keys:** `DATA_INSTRUMENTS`, `DATA_SESSIONS`, `DATA_IMPORTS_EXPORTS`, `DATA_MARKET_DATA`, `DATA_SYNC`, `DATA_DATASETS`, `DATA_QUALITY`, `DATA_RESAMPLING`, `DATA_UNIVERSES`, `DATA_PERSISTENCE`.
  - **DTOs:** `InstrumentDefinition`, `BrokerAlias`, `InstrumentValidationResult`, `SessionWindow`, `TradingSchedule`, `SessionDefinition`, `BarRecord`, `TickRecord`, `DataFormatSpecification`, `ImportResult`, `ExportResult`, `MarketDataRequest`, `build_market_data_request`, `SyncProgress`, `SyncReport`, `DatasetManifest`, `DatasetQuery`, `QualityAnomaly`, `QualityAnomalyType` (GAP, HIGH_PROBLEM, LOW_PROBLEM, SPIKE, CROSSED_QUOTE), `QualityReport`, `RepairPolicy`, `RepairResult`, `ResamplingRequest`, `TimezoneCloningRequest`, `UniverseBasket`, `BasketConstituent`.
  - **Protocols:** `InstrumentCatalog`, `SessionService`, `ImportExportService`, `MarketDataClient`, `SyncConnectorsCapability`, `DatasetService`, `QualityService`, `ResamplingService`, `UniverseManagerService`, `DataPersistenceService`.
  - **Errors:** `DataError`, `InstrumentNotFoundError`, `InvalidInstrumentError`, `SessionNotFoundError`, `TimezoneError`, `ImportParseError`, `ExportWriteError`, `DatasetNotFoundError`, `DatasetImmutableError`, `QualityValidationError`, `ResamplingError`, `UniverseNotFoundError`.

### 2. Persistence Layer (`app/services/persistence/`)

- `[NEW]` [app/services/persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py):
  - Namespace `data.v1` in SQLite WAL mode.
  - Tables: `data_instruments`, `data_instrument_aliases`, `data_sessions`, `data_datasets`, `data_baskets`, `data_basket_constituents`, `data_cache_entries`, `data_quality_reports`.
  - Pre-seeding default FX, CFD, and Crypto instruments (e.g. EURUSD, GBPUSD, USDJPY, BTCUSD, SP500, US30) and standard sessions (24/5 Forex, US Equities 09:30-16:00 EST, 24/7 Crypto).
  - Implements `DataPersistenceService`, slotted `DataPersistenceConfig`, `SPEC` (`persistence.data`), lifecycle, and `feature` factory.

### 3. Service Features Layer (`app/services/data/`)

- `[NEW]` [app/services/data/instruments.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/instruments.py):
  - Implements `InstrumentCatalog` (`FEAT-DATA-INSTRUMENTS`), contract constraints, pip/tick values, alias resolution, `InstrumentCatalogConfig`, `SPEC`, and `feature` factory.
- `[NEW]` [app/services/data/sessions.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/sessions.py):
  - Implements `SessionService` (`FEAT-DATA-SESSIONS`), schedule evaluation, holiday exclusion, timezone/DST translations, `SessionServiceConfig`, `SPEC`, and `feature` factory.
- `[NEW]` [app/services/data/imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/imports_exports.py):
  - Implements `ImportExportService` (`FEAT-DATA-IMPORTS-EXPORTS`), tabular CSV/TXT auto-detection, column mapping, MT4 HST/FXT and MT5 export writers, `ImportExportConfig`, `SPEC`, and `feature` factory.
- `[NEW]` [app/services/data/datasets.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/datasets.py):
  - Implements `DatasetService` (`FEAT-DATA-DATASETS`), immutable dataset manifests, SHA-256 content hashing, Parquet/Zstd storage partitions, `DatasetServiceConfig`, `SPEC`, and `feature` factory.
- `[NEW]` [app/services/data/quality.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/quality.py):
  - Implements `QualityService` (`FEAT-DATA-QUALITY`), SQX anomaly evaluation (`GAP`, `LOW_PROBLEM`, `HIGH_PROBLEM`, `SPIKE`, `CROSSED_QUOTE`), repair ledger reports, `QualityServiceConfig`, `SPEC`, and `feature` factory.
- `[NEW]` [app/services/data/resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/resampling.py):
  - Implements `ResamplingService` (`FEAT-DATA-RESAMPLING`), tick/M1 aggregation to higher timeframes, 4-price tick generation, timezone cloning (`CloneToTimezoneJob`), `ResamplingServiceConfig`, `SPEC`, and `feature` factory.
- `[NEW]` [app/services/data/universes.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/universes.py):
  - Implements `UniverseManagerService` (`FEAT-DATA-UNIVERSES`), basket management, point-in-time constituent membership (`date_from`, `date_to`), `UniverseManagerConfig`, `SPEC`, and `feature` factory.
- `[NEW]` [app/services/data/market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py):
  - Implements `MarketDataClient` & `SyncConnectorsCapability` (`FEAT-DATA-MARKET_DATA`), request validation, transparent caching, provider stream ingestion, deduplication, sorting, sync coordination, `MarketDataConfig`, `SPEC`, and `feature` factory.

### 4. Application Registry (`app/`)

- `[MODIFY]` [app/registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py):
  - Import all 8 data feature factories and `persistence.data`.
  - Register them in `FEATURES` tuple and `PROFILES["all"]`.

### 5. Tests and Verification (`tests/`)

- `[NEW]` [tests/services/data/test_instruments.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_instruments.py)
- `[NEW]` [tests/services/data/test_sessions.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_sessions.py)
- `[NEW]` [tests/services/data/test_imports_exports.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_imports_exports.py)
- `[NEW]` [tests/services/data/test_market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_market_data.py)
- `[NEW]` [tests/services/data/test_datasets.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_datasets.py)
- `[NEW]` [tests/services/data/test_quality.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_quality.py)
- `[NEW]` [tests/services/data/test_resampling.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_resampling.py)
- `[NEW]` [tests/services/data/test_universes.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_universes.py)
- `[NEW]` [tests/services/data/test_persistence.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_persistence.py)
- `[NEW]` [tests/services/data/test_lifecycle.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_lifecycle.py)
- `[NEW]` [tests/services/data/test_removal.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/data/test_removal.py)
- `[NEW]` [tests/examples/04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py)

### 6. Documentation Updates

- `[MODIFY]` [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) (update Status to `Completed`).
- `[MODIFY]` [docs/PROJECT.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/PROJECT.md) (update Data domain product status to `Completed`).

---

### Sequential Implementation Order

1. **Step 1: Contracts Layer** — Write [app/contracts/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/data.py) with all DTOs, protocols, capability tokens, and error types.
2. **Step 2: Persistence Layer** — Write [app/services/persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py) with SQLite tables, migrations, pre-seeded data, and unit tests in `tests/services/data/test_persistence.py`.
3. **Step 3: Core Foundational Features** —
   - Implement `instruments.py` and `sessions.py` with their unit tests (`test_instruments.py`, `test_sessions.py`).
4. **Step 4: Storage, Ingestion & Quality Features** —
   - Implement `datasets.py`, `quality.py`, and `imports_exports.py` with their unit tests (`test_datasets.py`, `test_quality.py`, `test_imports_exports.py`).
5. **Step 5: Resampling, Universes & Market Data Features** —
   - Implement `resampling.py`, `universes.py`, and `market_data.py` with their unit tests (`test_resampling.py`, `test_universes.py`, `test_market_data.py`).
6. **Step 6: Lifecycle, Removal, Registry Wiring & Consolidated Example** —
   - Implement `test_lifecycle.py`, `test_removal.py`.
   - Wire all features in [app/registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py).
   - Author [tests/examples/04_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/04_data.py).
7. **Step 7: Verification & Candidate Gate** —
   - Run focused pytest on changed tests.
   - Run example script `uv run python tests/examples/04_data.py`.
   - Run authoritative CI check: `uv run python scripts/ci_check.py`.
8. **Step 8: Walkthrough & Delivery** —
   - Update domain README and PROJECT.md to `Completed`.
   - Generate walkthrough artifact.

---

## 4. Dependencies and Contracts

- **Kernel Facilities:**
  - `app.kernel.feature.FeatureSpec`
  - `app.kernel.context.FeatureContext`
  - `app.kernel.logging.get_logger`
- **Persistence Dependencies:**
  - `DATABASE_SERVICE` (`persistence.database@1`)
  - `ARTIFACT_STORE` (`persistence.artifacts@1`)
- **Brokers Domain Dependencies:**
  - `BROKER_CATALOG` (`brokers.catalog@1`)
  - Provider feeds: `brokers.mt5@1`, `brokers.ctrader@1`, `brokers.dukascopy@1`, etc. (optional/operation-gated)
- **Exports:**
  - `data.instruments@1`
  - `data.sessions@1`
  - `data.imports_exports@1`
  - `data.market_data@1`
  - `data.sync@1`
  - `data.datasets@1`
  - `data.quality@1`
  - `data.resampling@1`
  - `data.universes@1`
  - `data.persistence@1`

---

## 5. Blockers, Risks, and Trade-offs

- **Risk:** Timezone calculations across DST transitions in standard Python libraries.
  - **Mitigation:** Use standard-library `zoneinfo.ZoneInfo` for deterministic IANA timezone handling without third-party timezone dependencies.
- **Risk:** High memory usage when parsing large CSV files or resampling ticks.
  - **Mitigation:** Chunked batch processing bounded by `batch_size` (50,000 records) and streaming generator interfaces.
- **Risk:** Parquet file creation without external native library lockups.
  - **Mitigation:** Use `pyarrow.parquet` for chunked write operations with Zstandard compression; fall back to structured SQLite storage if PyArrow is absent in minimal environments.

---

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope:**
  - Implementation of [app/contracts/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/data.py).
  - Implementation of [app/services/persistence/data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/data.py).
  - Implementation of all 8 feature modules in `app/services/data/`.
  - Comprehensive unit test suite in `tests/services/data/`.
  - Consolidated usage example in `tests/examples/04_data.py`.
  - Registration in `app/registry.py` and status updates in README / PROJECT.md.
- **Out of Scope / Non-Goals:**
  - Modifying `D-BROKERS` or `D-SIMULATOR` services in this task.
  - Proprietary StrategyQuant X binary byte-copying; all parsers are clean-room implementations.

---

## 7. Verification Plan

### Automated Tests

- Change-scoped tests during development:
  ```powershell
  uv run pytest --no-cov tests/services/data/
  ```

### Usage Evidence Run

- Consolidated usage scenario:
  ```powershell
  uv run python tests/examples/04_data.py
  ```

### Full Quality Pipeline

- Authoritative pre-push qualification gate:
  ```powershell
  uv run python scripts/ci_check.py
  ```

### Manual Verification

- Verify clean working tree (`git status`) and absence of unmanaged side effects.

---

## 8. Rollback & Contingency

To roll back this task, discard all uncommitted files and restore repository state:
```powershell
git reset --hard HEAD
git clean -fd
```

```text
ALLOWED_WRITE_PATHS:
- app/contracts/data.py
- app/services/persistence/data.py
- app/services/data/instruments.py
- app/services/data/sessions.py
- app/services/data/imports_exports.py
- app/services/data/market_data.py
- app/services/data/datasets.py
- app/services/data/quality.py
- app/services/data/resampling.py
- app/services/data/universes.py
- app/services/data/README.md
- app/registry.py
- docs/PROJECT.md
- tests/services/data/
- tests/examples/04_data.py
- .agents/logs/2026-09-20T193500_data-full-implementation/
END_ALLOWED_WRITE_PATHS:
```
