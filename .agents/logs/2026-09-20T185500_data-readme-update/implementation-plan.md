# Implementation Plan: Data Domain Specification & SQX Reference Alignment

> **Task ID:** `TASK-DATA-README-SPEC-ALIGNMENT`
> **Iteration:** `1`
> **Branch:** `backend`
> **Baseline Commit:** `f5997332ff8530412eaad9f8c19a808f15e957ea`

---

### User Review Required

> [!IMPORTANT]
> **Scope Refinements Approved by Owner (Iteration 1):**
> 1. **Rename Feature:** `FEAT-DATA-CALENDARS` $\to$ `FEAT-DATA-SESSIONS` (`sessions.py`), providing `data.sessions@1`.
> 2. **Deferred Features:** Dropped `FEAT-DATA-ECONOMICNEWS`, `FEAT-DATA-CONVERSIONS`, and `FEAT-DATA-SYNTHETIC` for now.
> 3. **Custom Data:** Skipped for now.
> 4. **Exporters Added:** Expanded `FEAT-DATA-IMPORTS` $\to$ `FEAT-DATA-IMPORTS-EXPORTS` (`imports_exports.py`), providing `data.imports_exports@1` (covering CSV, MT4 HST/FXT, and MT5 export formats).
> 5. **Timezone Cloning:** Integrated whole-dataset timezone transformation / cloning (`CloneToTimezoneJob`) under `FEAT-DATA-RESAMPLING` (`resampling.py`).
> 6. **Descriptive FR IDs:** Replaced numeric indices (`FR-DATA-001`) with descriptive 1–2 word identifiers (e.g. `FR-DATA-INSTRUMENT_SPECS`, `FR-DATA-SESSION_WINDOWS`, `FR-DATA-QUALITY_ANOMALIES`).

### Open Questions

> [!NOTE]
> - NONE. All scope boundaries, donor mappings, and naming conventions have been aligned with owner instructions.

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**:
  Update [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) to serve as the authoritative single source of truth for the Data domain (`D-DATA`), codifying cohesive features backed by StrategyQuant X reference donors, complete symbol and configuration tables, and descriptive functional requirements.
- **Ratified Requirements**:
  - `FR-DATA-INSTRUMENT_SPECS`: Validation of contract size, tick size, tick step, point value, lot step, min/max volume.
  - `FR-DATA-BROKER_ALIASES`: Canonical resolution and reversible mapping of broker-specific symbol aliases.
  - `FR-DATA-SESSION_WINDOWS`: Daily/weekly trading session filtering, weekend cuts, and maintenance exclusion.
  - `FR-DATA-TIMEZONE_DST`: Timezone resolution and DST offset transitions without silent or ambiguous time shifts.
  - `FR-DATA-IMPORT_DELIMITERS`: Automatic delimiter, datetime format, and column header detection with strict row error bounds.
  - `FR-DATA-EXPORT_FORMATS`: Configurable tabular CSV export and external platform formats (MT4 HST/FXT, MT5).
  - `FR-DATA-DATASET_IMMUTABILITY`: Content-addressable dataset versions; identical raw bytes and normalized config produce the exact same dataset identity.
  - `FR-DATA-PROVENANCE_LINEAGE`: Published dataset manifests carry full acquisition provenance, configuration, and repair lineage; partial datasets are never published.
  - `FR-DATA-QUALITY_ANOMALIES`: Exhaustive anomaly taxonomy detecting Gaps, High Problems, Low Problems, Spikes, and Crossed Quotes.
  - `FR-DATA-DATA_REPAIR`: Explicit user-configured repair policies (drop, interpolate, clamp); original raw data is never mutated in-place.
  - `FR-DATA-DETERMINISTIC_RESAMPLING`: Resampling is deterministic, session-aligned, and invariant across chunk/batch processing boundaries.
  - `FR-DATA-TIMEZONE_CLONING`: Whole-dataset projection and bar re-alignment into target timezones (e.g. UTC to broker server time GMT+2/+3 with US DST shifts).
  - `FR-DATA-UNIVERSE_CONSTITUENTS`: Point-in-time constituent membership with `date_from` and `date_to` bounds eliminating survivorship bias.
- **Usage Evidence**:
  - Offline example in `tests/examples/04_data.py` exercising instrument lookup, session filtering, tabular import/export, dataset versioning, anomaly detection, resampling, timezone cloning, and universe constituent querying.

## 2. Files Read (Audit Trail)

- [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) — Inspected current data domain specification and feature registry.
- [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) — Inspected data transport boundary (`brokers` emits raw chunks; `data` owns parsing, storage, quality, resampling).
- [docs/PROJECT.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/PROJECT.md) — System requirements, domain index, Parquet storage decision `DEC-DATA-001`.
- [docs/ARCHITECTURE.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/ARCHITECTURE.md) — Modular monolith layout, contracts, and lifecycle invariants.
- `SQX_REFERENCE_ROOT/internal/libs/SQDataLib.jar` — Inspected `InstrumentManager`, `SessionManager`, `Timezones`, `DataImportEngine`, `NewDataFormat`, `BarType`, `TimeBar`, `BasketOfStocksManager`.
- `SQX_REFERENCE_ROOT/internal/libs/SQTradingLib.jar` — Inspected `QualityChecker`, `DataProblemEvaluator` (`GAP`, `LOW_PROBLEM`, `HIGH_PROBLEM`, `SPIKE`).
- `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DataManagerData.jar` — Inspected `CsvExporter`, `MT4ExportJob`, `MT5ExportJob`, `CloneToTimezoneJob`.

## 3. Proposed Changes & Implementation Order

### Data Domain Specification & Registry

- `[MODIFY]` [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md):
  - **Code-aligned layout:** Update module directory tree to physical removal units.
  - **Section 1 (Shared Contracts Table):** Update capability tokens.
  - **Section 2 (Feature Registry):** Update registered features and dependencies.
  - **Section 4 (Configuration & Limits Table):** Add explicit slotted configuration definitions.
  - **Section 4 (Single-File Structure & Symbols Table):** Complete modules, responsibilities, and public symbols.
  - **Section 4 (Functional Requirements):** Enumerate descriptive FRs.
  - **Section 9 (Normative Domain Specification):** Enshrine clean-room boundary, Parquet/Zstd dataset layouts, SQX anomaly classification, and pure transport consumption from `brokers`.

---

# Iteration 2: Market Data Retrieval & Connector Synchronization Feature

> **Task ID:** `FEAT-DATA-MARKET_DATA`
> **Iteration:** `2`
> **Branch:** `backend`
> **Baseline Commit:** `f5997332ff8530412eaad9f8c19a808f15e957ea`

### User Review Required

> [!IMPORTANT]
> **Addition of `FEAT-DATA-MARKET_DATA` (`market_data.py`):**
> Per owner request, we are introducing the unified market data retriever and connector synchronization feature to bridge `D-DATA` with the external provider connectors in `D-BROKERS`.
> - **Purpose:** Provide unified, governed access to market data retrieval, normalization, quality verification, caching, and connector synchronization across providers.
> - **Key Capabilities:**
>   - Construct and dispatch structured `MarketDataRequest` specifications (`source_id`, `symbol`, `data_kind`, `timeframe`, `start`, `end`, `store_data`).
>   - Provide `MarketDataClient` and `fetch_market_data` with transparent caching.
>   - Perform automatic data deduplication, sorting, and quality anomaly checks.
>   - Coordinate idempotent, resumable, and secret-isolated connector synchronization.
>   - Provide async `sync_connectors` implementing `SyncConnectorsCapability`.
> - **Capability Tokens:** `data.market_data@1` and `data.sync@1`.
> - **Owner Module:** `app/services/data/market_data.py`.

### Open Questions

> [!NOTE]
> - NONE. Interface and request contracts are fully aligned with owner guidance.

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**:
  Update [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) to formally register `FEAT-DATA-MARKET_DATA` as the 8th core feature in the Data domain, defining its contract obligations, configuration, workflows, and functional requirements.
- **Ratified Requirements**:
  - `FR-DATA-MARKET_REQUEST`: Construct, validate, and dispatch structured `MarketDataRequest` specifications across registered providers (`source_id`, `symbol`, `data_kind`, `timeframe`, `start`, `end`, `store_data`).
  - `FR-DATA-CACHE_TRANSPARENCY`: Transparent point-in-time caching of fetched bars and ticks avoiding redundant remote downloads.
  - `FR-DATA-CONNECTOR_SYNC`: Idempotent, resumable, and secret-isolated connector synchronization implementing `SyncConnectorsCapability`.
  - `FR-DATA-INGESTION_NORMALIZATION`: Automatic deduplication, monotonic timestamp sorting, and quality anomaly evaluation during stream ingestion.
- **Usage Evidence**:
  - Demonstrating programmatic request dispatch via `build_market_data_request` and `MarketDataClient.fetch_market_data` in `tests/examples/04_data.py`.

## 2. Files Read (Audit Trail)

- [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) — Inspected current 7-module data domain layout and tables.
- [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) — Inspected feed connectors (`brokers.mt5@1`, `brokers.ctrader@1`, `brokers.dukascopy@1`, etc.) consumed by `FEAT-DATA-MARKET_DATA`.

## 3. Proposed Changes & Implementation Order

### Data Domain Specification & Registry

- `[MODIFY]` [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md):
  - **Code-aligned layout:** Add `market_data.py` to the tree (total 8 modules):
    ```text
    app/services/data/
    |-- README.md
    |-- __init__.py
    |-- instruments.py
    |-- sessions.py
    |-- imports_exports.py
    |-- market_data.py
    |-- datasets.py
    |-- quality.py
    |-- resampling.py
    `-- universes.py
    ```
  - **Section 1 (Shared Contracts Table):**
    - Add `data.market_data@1` (`MarketDataClient`)
    - Add `data.sync@1` (`SyncConnectorsCapability`)
  - **Section 2 (Feature Registry):** Add `FEAT-DATA-MARKET_DATA` (`app/services/data/market_data.py`) providing `data.market_data@1` and `data.sync@1`.
  - **Section 3 (Domain Workflows):** Add `WF-DATA-FETCH` and `WF-DATA-SYNC`.
  - **Section 4 (Configuration & Limits Table):** Add `MarketDataConfig`:
    - `schema_version=1`, `cache_enabled=True`, `max_cache_entries=1000`, `request_timeout_s=30.0`, `sync_batch_size=50000`.
  - **Section 4 (Single-File Structure & Symbols Table):** Add `market_data.py` with symbols: `MarketDataClient`, `MarketDataService`, `MarketDataRequest`, `build_market_data_request`.
  - **Section 4 (Functional Requirements Table):** Add:
    - `FR-DATA-MARKET_REQUEST`
    - `FR-DATA-CACHE_TRANSPARENCY`
    - `FR-DATA-CONNECTOR_SYNC`
    - `FR-DATA-INGESTION_NORMALIZATION`
  - **Section 9 (Normative Domain Specification):** Update domain text to cover market data retrieval, transparent caching, and connector synchronization.

### Sequential Implementation Order

1. **Step 1:** Update [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) to integrate `FEAT-DATA-MARKET_DATA`.
2. **Step 2:** Run `scripts/architecture_check.py` to ensure boundary consistency.
3. **Step 3:** Record iteration in `.agents/logs/2026-09-20T185500_data-readme-update/` and prepare walkthrough.

## 4. Dependencies and Contracts

- **Consumes:**
  - `data.instruments@1`, `data.sessions@1`, `data.quality@1`, `data.datasets@1`
  - `brokers.catalog@1`
  - Optional provider connectors: `brokers.mt5@1`, `brokers.ctrader@1`, `brokers.dukascopy@1`, `brokers.equity@1`, `brokers.futures@1`, `brokers.darwinex@1`, `brokers.crypto@1`, `brokers.yahoo@1`
  - `persistence.artifacts@1`
- **Provides:**
  - `data.market_data@1`
  - `data.sync@1`

## 5. Blockers, Risks, and Trade-offs

- **Risk:** Remote provider connection timeouts or incomplete chunks during downloads.
- **Mitigation:** Circuit fencing and transport timeouts are handled in `D-BROKERS`; `market_data.py` operates behind configured timeouts, deduplication, and transparent caching with quarantined partial files.

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope:**
  - Registering `FEAT-DATA-MARKET_DATA` in [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md), including config, symbols, workflows, and FRs.
- **Out of Scope / Non-Goals:**
  - Writing Python source code in this step (reserved for subsequent implementation tasks).

## 7. Verification Plan

### Automated Tests

```bash
uv run python scripts/architecture_check.py
```

## 8. Rollback & Contingency

To revert changes, restore `app/services/data/README.md` from git:
```bash
git checkout HEAD -- app/services/data/README.md
```

```text
ALLOWED_WRITE_PATHS:
- app/services/data/README.md
- .agents/logs/2026-09-20T185500_data-readme-update/implementation-plan.md
- .agents/logs/2026-09-20T185500_data-readme-update/walkthrough.md
END_ALLOWED_WRITE_PATHS:
```
