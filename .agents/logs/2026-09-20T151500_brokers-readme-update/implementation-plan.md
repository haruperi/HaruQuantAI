# Implementation Plan: Brokers Domain Specification & Data Manager Provider Alignment

> **Task ID:** `TASK-BROKERS-README-SPEC-ALIGNMENT`
> **Iteration:** `1`
> **Branch:** `backend`
> **Baseline Commit:** `fc4f84de7200ec83db2468554b45e4f162be871a`

---

### User Review Required

> [!IMPORTANT]
> **Strict Domain Boundary Separation:**
> Per your guidance, the `brokers` domain (`D-BROKERS`) owns **ONLY** the actual external transport connection, session lifecycle, and raw acquisition streaming.
> **Zero data manipulation** (no compression, tick-to-bar aggregation, resampling, local database dataset storage, cleaning, or caching transformations) is permitted inside `brokers`. All data transformations, storage schemas, and dataset immutability belong strictly to the `data` domain (`D-DATA`).
>
> **Provider Scope Expansion:**
> We are aligning the feature registry with the exact Data Manager "Data sources" connection topology in StrategyQuant X:
> 1. Dukascopy (`FEAT-BROKERS-DUKASCOPY`) — donor: `DataSourceDukascopy`
> 2. StrategyQuant Equity (`FEAT-BROKERS-EQUITY`) — donor: `DataSourceSQEquityData`
> 3. StrategyQuant Futures (`FEAT-BROKERS-FUTURES`) — donor: `DataSourceSQFuturesData`
> 4. Darwinex (`FEAT-BROKERS-DARWINEX`) — donor: `DataSourceDarwinex`
> 5. Crypto Exchanges (`FEAT-BROKERS-CRYPTO`) — donor: `DataSourceCrypto` / `CryptoExchange*`
> 6. Yahoo Finance (`FEAT-BROKERS-YAHOO`) — donor: `DataSourceYahoo`
> 7. MetaTrader 5 (`FEAT-BROKERS-MT5`) — donor: `DataSourceMt5Api` / `mt5api.py`
> 8. cTrader (`FEAT-BROKERS-CTRADER`) — Target modern adapter (`DEC-BROKERS-001`, no SQX donor)
> 9. Broker Catalog & Settings (`FEAT-BROKERS-CATALOG`) — donor: `BrokerManager` / `BROKER` SQLite table
> 10. Connection Reconciliation & Fencing (`FEAT-BROKERS-RECONCILIATION`, `FEAT-BROKERS-FENCING`) — Operational safety invariants

### Open Questions

> [!NOTE]
> - **Q1:** Should `app/contracts/brokers.py` define a generic `BrokerTransportConnection` protocol that emits typed raw chunks/events consumed by `data.imports@1`, or should each provider expose a tailored transport protocol? (Proposed: A unified `BrokerFeedConnector` protocol in `app/contracts/brokers.py` with provider-specific configuration DTOs).

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**:
  Update [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) to serve as the single source of truth for the `brokers` domain (`D-BROKERS`), incorporating our audit of StrategyQuant X build 144.2953 Data Manager external connections.
  The update establishes a strict separation of concerns: `brokers` handles exclusively the remote transport session, authentication, and raw payload acquisition without touching data persistence, compression, or transformation.
- **Ratified Requirements**:
  - `FR-BROKERS-001`: Capability discovery prevents unsupported connection semantics from transmission.
  - `FR-BROKERS-002`: Reversible symbol translation (prefix/postfix, broker server naming).
  - `FR-BROKERS-003`: Duplicate submission / intent idempotency.
  - `FR-BROKERS-004`: Negative authorization for live profiles in test/mock modes.
  - `FR-BROKERS-005`: Pure transport connection boundary — zero data storage, compression, bar aggregation, or mutation inside broker connectors.
  - `FR-BROKERS-006`: Zero-plaintext credential persistence (strict OS secret provider).
  - `FR-BROKERS-007`: Broker server timezone and session timing resolution (`MT_TIMEZONE`).
- **Usage Evidence**:
  - Offline example in `tests/examples/03_brokers.py` demonstrating connection initialization, profile discovery, symbol translation, and raw chunk reception across mocked providers.

## 2. Files Read (Audit Trail)

- [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) — Current state of brokers domain registry and specifications.
- [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) — Boundary definition of `D-DATA` (owns storage, schemas, imports, datasets, resampling).
- [docs/PROJECT.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/PROJECT.md) — System requirements, domain index, cTrader/MT5 target decisions.
- [docs/ARCHITECTURE.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/ARCHITECTURE.md) — Universal structural and runtime constraints.
- `SQX_REFERENCE_ROOT/user/data/data.db` — Inspected `BROKER`, `INSTRUMENTS`, and `SESSIONS` tables for `POSTFIX`, `MT_TIMEZONE`, and `BROKER_ID`.
- `SQX_REFERENCE_ROOT/internal/python/scripts/mt5api.py` — Inspected MT5 Python bridge, symbol metadata calculation, and override resolutions.
- `SQX_REFERENCE_ROOT/internal/plugins/DataSource*` — Inspected `DataSourceDukascopy`, `DataSourceDarwinex`, `DataSourceSQEquityData`, `DataSourceSQFuturesData`, `DataSourceYahoo`, `DataSourceCrypto`, and `DataSourceMt5Api`.

## 3. Proposed Changes & Implementation Order

### Documentation & Domain Registry

- `[MODIFY]` [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md):
  - **Section 1 (Purpose & Boundary):** Formulate strict boundary: owns provider connection, sessions, capability discovery, transport streaming, and connection reconciliation. Explicitly disclaims all data storage, compression, saving, bar resampling, or format transformations.
  - **Section 1 (Shared Contracts Table):** Add capability tokens for `brokers.equity@1`, `brokers.futures@1`, `brokers.darwinex@1`, and `brokers.yahoo@1`.
  - **Section 2 (Feature Registry):**
    - `FEAT-BROKERS-CATALOG` (`catalog.py`): Provider profiles, postfix mapping, server timezones.
    - `FEAT-BROKERS-MT5` (`mt5_adapter.py`): MetaTrader 5 transport session and quote bridge.
    - `FEAT-BROKERS-CTRADER` (`ctrader_adapter.py`): cTrader Open API transport session.
    - `FEAT-BROKERS-DUKASCOPY` (`dukascopy.py`): Direct Dukascopy binary tick transport connector.
    - `FEAT-BROKERS-EQUITY` (`sq_equity.py`): StrategyQuant Equity data feed transport connector.
    - `FEAT-BROKERS-FUTURES` (`sq_futures.py`): StrategyQuant Futures data feed transport connector.
    - `FEAT-BROKERS-DARWINEX` (`darwinex.py`): Direct Darwinex tick feed transport connector.
    - `FEAT-BROKERS-CRYPTO` (`crypto_adapter.py`): Unified crypto exchange connector (Binance/CCXT).
    - `FEAT-BROKERS-YAHOO` (`yahoo.py`): Yahoo Finance daily feed transport connector.
    - `FEAT-BROKERS-RECONCILIATION` (`reconciliation.py`): Session and order/position state reconciliation.
    - `FEAT-BROKERS-FENCING` (`isolation_fencing.py`): Fail-closed uncertainty and disconnect fencing.
  - **Section 4 (Feature Specifications & FRs):** Update configuration, single-file structure, and include `FR-BROKERS-001` through `FR-BROKERS-007`.
  - **Section 9 (Normative Domain Specification):** Enshrine clean-room boundary, credential isolation, and pure transport invariant.

### Sequential Implementation Order

1. **Step 1:** Draft updated [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) adhering to `FIP-01` through `FIP-26`.
2. **Step 2:** Run `scripts/architecture_check.py` to ensure boundary consistency and docstring compliance.
3. **Step 3:** Record task artifact in `.agents/logs/2026-09-20T151500_brokers-readme-update/` and prepare walkthrough.

## 4. Dependencies and Contracts

- Consumes:
  - `app.kernel.logging` (`logger = get_logger(__name__)`)
  - OS secret provider (for credential resolution)
- Emits:
  - `brokers.catalog@1`
  - `brokers.mt5@1`
  - `brokers.ctrader@1`
  - `brokers.dukascopy@1`
  - `brokers.equity@1`
  - `brokers.futures@1`
  - `brokers.darwinex@1`
  - `brokers.crypto@1`
  - `brokers.yahoo@1`
  - `brokers.reconciliation@1`
  - `brokers.fencing@1`
- Persistence Boundary:
  - `app/services/persistence/brokers.py` owns broker profile table schemas (`brokers.v1`), postfix maps, and connection configuration metadata. Zero credentials stored in database.

## 5. Blockers, Risks, and Trade-offs

- **Risk:** Conflating transport acquisition with dataset storage.
  - **Mitigation:** Strict `FR-BROKERS-005` invariant forbidding local file/database storage or transformation inside `brokers`. Hand-off to `D-DATA` occurs via stream callbacks or raw payloads.
- **Risk:** Breaking existing architectural checks.
  - **Mitigation:** Verify with `uv run python scripts/architecture_check.py`.

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope**:
  - Updating [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md).
  - Registering the complete 11-feature suite aligned with SQX Data Manager providers.
  - Specifying `FR-BROKERS-001` through `FR-BROKERS-007`.
- **Out of Scope / Non-Goals**:
  - Implementing the Python service code (deferred to individual feature implementation tasks).
  - Editing `app/services/data/README.md` or any other domain.
  - Direct database modifications.

## 7. Verification Plan

### Automated Tests
- Architecture and boundary verification:
  ```bash
  uv run python scripts/architecture_check.py
  ```

### Manual Verification
- Review [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) line-by-line against user boundary rules and SQX Data Manager donor specifications.

## 8. Rollback & Contingency

To revert:
```bash
git checkout HEAD -- app/services/brokers/README.md
```

```text
ALLOWED_WRITE_PATHS:
- app/services/brokers/README.md
- .agents/logs/2026-09-20T151500_brokers-readme-update/implementation-plan.md
- .agents/logs/2026-09-20T151500_brokers-readme-update/walkthrough.md
END_ALLOWED_WRITE_PATHS:
```
