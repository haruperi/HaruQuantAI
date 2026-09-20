# Walkthrough: Brokers Domain Specification & Data Manager Provider Alignment

> **Task ID:** `TASK-BROKERS-README-SPEC-ALIGNMENT`
> **Status:** `COMPLETED`

---

## 1. Summary of Changes Made

Updated [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) to serve as the single source of truth for the `brokers` domain (`D-BROKERS`), incorporating our audit of StrategyQuant X build 144.2953 Data Manager external connections and user-ratified boundary constraints:

- `[MODIFY]` [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md):
  - **Strict Transport-Only Boundary (`DEC-BROKERS-003`, `FR-BROKERS-005`):** Explicitly declared that `brokers` owns *only* remote transport sessions, authentication, and raw payload acquisition streaming. All data persistence, compression, saving, bar aggregation, resampling, and format transformations are strictly excluded from `brokers` and owned by `data` (`D-DATA`).
  - **Data Manager Provider Registry Expansion:** Expanded the feature registry and capability matrix to mirror the exact external connection topology from StrategyQuant X Data Manager:
    - `FEAT-BROKERS-CATALOG` (`catalog.py`): Provider profiles, symbol postfix mapping, and server timezones (`brokers.catalog@1`)
    - `FEAT-BROKERS-MT5` (`mt5_adapter.py`): MetaTrader 5 transport session and quote bridge (`brokers.mt5@1`)
    - `FEAT-BROKERS-CTRADER` (`ctrader_adapter.py`): cTrader Open API transport session (`brokers.ctrader@1`)
    - `FEAT-BROKERS-DUKASCOPY` (`dukascopy.py`): Direct Dukascopy binary tick transport connector (`brokers.dukascopy@1`)
    - `FEAT-BROKERS-EQUITY` (`sq_equity.py`): StrategyQuant Equity data feed transport connector (`brokers.equity@1`)
    - `FEAT-BROKERS-FUTURES` (`sq_futures.py`): StrategyQuant Futures data feed transport connector (`brokers.futures@1`)
    - `FEAT-BROKERS-DARWINEX` (`darwinex.py`): Direct Darwinex tick feed transport connector (`brokers.darwinex@1`)
    - `FEAT-BROKERS-CRYPTO` (`crypto_adapter.py`): Unified crypto exchange connector (Binance/CCXT; `brokers.crypto@1`)
    - `FEAT-BROKERS-YAHOO` (`yahoo.py`): Yahoo Finance daily feed transport connector (`brokers.yahoo@1`)
    - `FEAT-BROKERS-RECONCILIATION` (`reconciliation.py`): Session, order/position, and account reconciliation (`brokers.reconciliation@1`)
    - `FEAT-BROKERS-FENCING` (`isolation_fencing.py`): Fail-closed uncertainty and disconnect fencing (`brokers.fencing@1`)
  - **Domain Workflows:** Added `WF-BROKERS-STREAM` for streaming raw transport chunks to data ingestion (`data.imports@1`) alongside `WF-BROKERS-COMMAND`.
  - **Functional Requirements Suite:** Formalized `FR-BROKERS-001` through `FR-BROKERS-007`, specifically adding:
    - `FR-BROKERS-005`: Pure transport connection boundary (zero internal compression/storage/resampling).
    - `FR-BROKERS-006`: Zero-plaintext credential persistence (strict OS secret provider).
    - `FR-BROKERS-007`: Broker server timezone and session timing resolution (`MT_TIMEZONE`).

---

## 2. Verification Results

### Architectural Boundary Check
```bash
uv run python scripts/architecture_check.py
```
```text
========================================
Running Architectural AST Invariant Check...
Scanning targets: C:\Users\rharu\AppDev\HaruQuantAI-backend\app
========================================
[SUCCESS] All architectural rules passed without violations!
```

### Full Repository Qualification Suite
```bash
uv run python scripts/ci_check.py
```
- **Ruff Format & Lint:** Clean (0 errors across all rule groups).
- **Mypy Strict:** Clean (0 typing issues).
- **Architectural Check:** Clean (0 boundary violations).
- **Pytest Suite:** 233 passed in 11.82s.
- **Coverage Floor:** 89.90% total coverage achieved (exceeding 80.0% floor requirement).
- **Runtime Application Bootstrap & Cleanup:** Clean (0 cleanup errors).

---

## 3. Deviations & Residuals

- **Deviations:** None. Implementation strictly matches the approved implementation plan.
- **Working Tree Diff Status (`git status`):**
  ```text
  modified:   app/services/brokers/README.md
  ```
- **Proposed Commit Message:**
  ```text
  docs(brokers): align domain specification with SQX Data Manager providers

  - Enforce pure transport connection boundary (no data manipulation/storage in D-BROKERS)
  - Register SQX Data Manager provider feed suite (Dukascopy, SQ Equity, SQ Futures, Darwinex, Crypto, Yahoo, MT5, cTrader)
  - Add FR-BROKERS-005 (pure transport), FR-BROKERS-006 (secret facility), and FR-BROKERS-007 (timezone mapping)
  ```
- **Next Logical Step:**
  - Proceed to the first feature implementation in the `brokers` domain, starting with `FEAT-BROKERS-CATALOG` (`app/services/brokers/catalog.py` and `app/contracts/brokers.py`).
