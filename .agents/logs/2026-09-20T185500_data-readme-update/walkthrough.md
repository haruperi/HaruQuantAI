# Walkthrough: Data Domain Specification & SQX Reference Alignment

> **Task ID:** `TASK-DATA-README-SPEC-ALIGNMENT`
> **Status:** `VERIFIED`

---

## 1. Summary of Changes Made

- `[MODIFY]` [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md):
  - **Iteration 1:**
    - Replaced `FEAT-DATA-CALENDARS` with `FEAT-DATA-SESSIONS` (`sessions.py`), providing `data.sessions@1`.
    - Dropped `FEAT-DATA-ECONOMICNEWS`, `FEAT-DATA-CONVERSIONS`, and `FEAT-DATA-SYNTHETIC` for now. Skipped Custom Data.
    - Expanded `FEAT-DATA-IMPORTS` into `FEAT-DATA-IMPORTS-EXPORTS` (`imports_exports.py`), providing `data.imports_exports@1` (including CSV, MT4 HST/FXT, and MT5 export formats).
    - Integrated whole-dataset timezone transformation / cloning (`CloneToTimezoneJob`) under `FEAT-DATA-RESAMPLING` (`resampling.py`).
  - **Iteration 2:**
    - Registered `FEAT-DATA-MARKET_DATA` ([market_data.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/market_data.py)) for governed market data retrieval, transparent caching, and connector synchronization across providers.
    - Provided capabilities: `data.market_data@1` and `data.sync@1`.
    - Declared public symbols: `MarketDataClient`, `MarketDataService`, `MarketDataRequest`, `build_market_data_request`.
    - Added workflows `WF-DATA-FETCH` and `WF-DATA-SYNC`.
    - Declared slotted configuration `MarketDataConfig`.
    - Added 4 descriptive functional requirements:
      - `FR-DATA-MARKET_REQUEST`
      - `FR-DATA-CACHE_TRANSPARENCY`
      - `FR-DATA-CONNECTOR_SYNC`
      - `FR-DATA-INGESTION_NORMALIZATION`
  - **Completed Domain Tables:** Fully defined slotted configuration classes (`<Feature>Config`), single-file structure, and public symbols for all 8 modules.
  - **Full Functional Requirements Suite (17 Descriptive IDs):**
    - `FR-DATA-INSTRUMENT_SPECS`
    - `FR-DATA-BROKER_ALIASES`
    - `FR-DATA-SESSION_WINDOWS`
    - `FR-DATA-TIMEZONE_DST`
    - `FR-DATA-IMPORT_DELIMITERS`
    - `FR-DATA-EXPORT_FORMATS`
    - `FR-DATA-MARKET_REQUEST`
    - `FR-DATA-CACHE_TRANSPARENCY`
    - `FR-DATA-CONNECTOR_SYNC`
    - `FR-DATA-INGESTION_NORMALIZATION`
    - `FR-DATA-DATASET_IMMUTABILITY`
    - `FR-DATA-PROVENANCE_LINEAGE`
    - `FR-DATA-QUALITY_ANOMALIES`
    - `FR-DATA-DATA_REPAIR`
    - `FR-DATA-DETERMINISTIC_RESAMPLING`
    - `FR-DATA-TIMEZONE_CLONING`
    - `FR-DATA-UNIVERSE_CONSTITUENTS`

---

## 2. Verification Results

### Architectural Checks

```powershell
uv run python scripts/architecture_check.py
```
**Output:**
```text
========================================
Running Architectural AST Invariant Check...
Scanning targets: C:\Users\rharu\AppDev\HaruQuantAI-backend\app
========================================
[SUCCESS] All architectural rules passed without violations!
```

---

## 3. Deviations & Residuals

- **Deviations:** None. All changes strictly adhered to owner directives and approved implementation plan iterations.
- **Working Tree Status (`git status --short`):**
  ```text
  M app/services/data/README.md
  ?? .agents/logs/2026-09-20T185500_data-readme-update/
  ```
- **Proposed Commit Message:**
  ```text
  docs(data): register FEAT-DATA-MARKET_DATA and align data domain specifications with SQX donors

  - Add FEAT-DATA-MARKET_DATA (market_data.py) for governed data retrieval and connector sync
  - Rename calendars feature to sessions.py (FEAT-DATA-SESSIONS)
  - Expand imports to imports_exports.py (FEAT-DATA-IMPORTS-EXPORTS)
  - Integrate timezone cloning under resampling.py (FEAT-DATA-RESAMPLING)
  - Defer economic_news, conversions, and synthetic series
  - Enshrine 17 descriptive functional requirements (FR-DATA-*)
  - Complete slotted configuration and symbol tables for all 8 modules
  ```
- **Logical Next Steps:**
  - Owner review and authorization to commit.
  - Proceed to implement Data domain public contracts in `app/contracts/data.py` and service features sequentially.
