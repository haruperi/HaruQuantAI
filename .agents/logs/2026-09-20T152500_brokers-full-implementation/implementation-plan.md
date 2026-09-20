# Implementation Plan: Full Implementation of Brokers Domain Features

> **Task ID:** `FEAT-BROKERS-FULL-DOMAIN-IMPLEMENTATION`
> **Iteration:** `1`
> **Branch:** `backend`
> **Baseline Commit:** `2abbf62`

---

### User Review Required

> [!IMPORTANT]
> **Strict Separation of Concerns Invariant (`FR-BROKERS-005`):**
> Every connector in `brokers` (`D-BROKERS`) is strictly a **transport connector**. It handles remote authentication, connection sessions, protocol negotiation, and streaming raw byte chunks/records.
> **Zero data manipulation, compression, bar aggregation, resampling, or dataset file/database storage** is performed inside `brokers`. Raw payloads are streamed directly to consumers (`data.imports@1` in `D-DATA`).
>
> **SQX Connection Parity vs Custom cTrader:**
> - **Dukascopy (`dukascopy.py`)**: Replicates SQX `DataSourceDukascopy` (HTTP bi5 hourly chunk acquisition and `dukascopy.csv` instrument mapping).
> - **SQ Equity (`sq_equity.py`)**: Replicates SQX `DataSourceSQEquityData` (REST client for SQ Equity server exchanges, lookups, updates with license verification).
> - **SQ Futures (`sq_futures.py`)**: Replicates SQX `DataSourceSQFuturesData` (REST client for SQ Futures server).
> - **Darwinex (`darwinex.py`)**: Replicates SQX `DataSourceDarwinex` (Tick server transport connector with `darwinex.csv` metadata).
> - **Crypto (`crypto_adapter.py`)**: Replicates SQX `DataSourceCrypto` / `CryptoExchangeBinance` (REST/WS transport connector for Binance Spot/Futures and CCXT-compatible exchanges).
> - **Yahoo (`yahoo.py`)**: Replicates SQX `DataSourceYahoo` (HTTP GET with session cookie/crumb to Yahoo Finance v8 chart API).
> - **MetaTrader 5 (`mt5_adapter.py`)**: Replicates SQX `DataSourceMt5Api` / `mt5api.py` (MT5 Python IPC bridge extracting `trade_calc_mode`, `point_value`, `spread`, and quotes).
> - **cTrader (`ctrader_adapter.py`)**: Custom modern implementation (cTrader Open API 2.0 TCP/WebSocket Protobuf transport).
> - **Catalog (`catalog.py`)**: Replicates SQX `BrokerManager` / `BROKER` SQLite table (pre-seeded system brokers, `POSTFIX` mapping, server timezones).
> - **Reconciliation (`reconciliation.py`) & Fencing (`isolation_fencing.py`)**: Reconnect sync and fail-closed uncertainty fencing.
>
> **Multi-Phase Delivery Strategy:**
> To ensure deterministic verification, high test coverage (>80%), and clean-room rigor across 11 features, execution will follow 5 sequential phases.

### Open Questions

> [!NOTE]
> - **Q1:** For offline execution testing when external networks or MT5 terminals are unavailable, all connectors will include an offline mock/loopback mode with deterministic canned responses. Does this match your testing requirements? (Recommended: Yes).

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal**:
  Implement the complete `brokers` domain (`D-BROKERS`) specified in [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md). Provide production-grade, typed, single-file modular monolith features for all 11 registered capabilities, matching StrategyQuant X connection methods while preserving strict transport-only boundaries.
- **Ratified Requirements**:
  - `FR-BROKERS-001`: Capability discovery prevents unsupported connection semantics from transmission.
  - `FR-BROKERS-002`: Reversible symbol translation (prefix/postfix, broker server naming).
  - `FR-BROKERS-003`: Duplicate submission / intent idempotency.
  - `FR-BROKERS-004`: Negative authorization for live profiles in test/mock modes.
  - `FR-BROKERS-005`: Pure transport connection boundary: connectors emit raw chunks/events with zero internal data compression, bar aggregation, storage, or resampling.
  - `FR-BROKERS-006`: Zero-plaintext credential persistence: all secrets are resolved via OS secret provider and never committed to SQLite, files, logs, or UI reads.
  - `FR-BROKERS-007`: Broker server timezone and session timing resolution (`MT_TIMEZONE`).
- **Usage Evidence**:
  - Standalone, deterministic offline scenario in `tests/examples/03_brokers.py` exercising profile catalog discovery, symbol postfix translation, feed connector acquisition across all 7 providers, cTrader/MT5 transport sessions, fail-closed fencing, and state reconciliation.

## 2. Files Read (Audit Trail)

- [app/services/brokers/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/README.md) — Domain specification, 11 feature registries, and NFRs.
- [app/services/data/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/data/README.md) — Data ingestion and dataset storage boundaries.
- [app/registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py) — Application feature factory registration and profile configuration.
- [app/services/persistence/workspace.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/workspace.py) — Architectural blueprint for domain persistence modules.
- `SQX_REFERENCE_ROOT/user/data/data.db` — `BROKER` schema and 11 pre-seeded brokers (`XTB`, `RoboForex`, `Dukascopy`, `Darwinex`, `ICMarkets`, `Pepperstone`, `OANDA`, `FTMO`, `The5ers`, `Monevis`, `Darwinex Zero`).
- `SQX_REFERENCE_ROOT/internal/python/scripts/mt5api.py` — MT5 Python bridge calculation modes, tick size, point value, spread, and quote streaming.
- `SQX_REFERENCE_ROOT/internal/plugins/DataSource*` — `DataSourceDukascopy`, `DataSourceSQEquityData`, `DataSourceSQFuturesData`, `DataSourceDarwinex`, `DataSourceCrypto`, `DataSourceYahoo`, `DataSourceMt5Api`.

## 3. Proposed Changes & Implementation Order

### Phase 1: Shared Contracts & Persistence Boundary

- `[NEW]` [app/contracts/brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/contracts/brokers.py):
  - Typed DTOs: `BrokerProfile`, `BrokerConnectionConfig`, `RawTransportChunk`, `ConnectionHealth`, `ReconciliationReport`.
  - Service Protocols: `BrokerCatalogService`, `BrokerFeedConnector`, `BrokerTradingAdapter`, `BrokerReconciliationService`, `BrokerFencingService`, `BrokerPersistenceService`.
  - Capability Tokens: `BROKER_CATALOG`, `BROKER_MT5`, `BROKER_CTRADER`, `BROKER_DUKASCOPY`, `BROKER_EQUITY`, `BROKER_FUTURES`, `BROKER_DARWINEX`, `BROKER_CRYPTO`, `BROKER_YAHOO`, `BROKER_RECONCILIATION`, `BROKER_FENCING`, `BROKER_PERSISTENCE`.
  - Domain Errors: `BrokerError`, `BrokerConnectionError`, `BrokerAuthenticationError`, `BrokerFencedError`, `BrokerReconciliationError`.
- `[NEW]` [app/services/persistence/brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/persistence/brokers.py):
  - SQLite schema for namespace `brokers.v1`: `broker_profiles`, `broker_connections`, `broker_instrument_overrides`.
  - Pre-seeding of the 11 SQX system brokers with accurate default post-fixes and timezones.
  - Zero plaintext credential storage; connection records link only to OS secret keys.
  - Persistence service implementation, `SPEC`, and zero-argument factory `feature()`.
- `[NEW]` `tests/services/brokers/persistence/test_brokers_persistence.py`:
  - Validates schema initialization, pre-seeded system brokers, custom CRUD, transaction rollback, and connection config storage against isolated `tmp_path` SQLite.

### Phase 2: Catalog, Reconciliation & Fencing

- `[NEW]` [app/services/brokers/catalog.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/catalog.py):
  - `BrokerCatalog` service implementing `brokers.catalog@1`.
  - Reversible symbol resolution (`resolve_broker_symbol("EURUSD", broker_id) -> "EURUSD_roboforex"` and inverse).
  - Server timezone resolution (`get_broker_timezone`).
  - System profile deletion protection.
- `[NEW]` [app/services/brokers/isolation_fencing.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/isolation_fencing.py):
  - `BrokerFencingService` implementing `brokers.fencing@1`.
  - Fail-closed state tracker; trips on threshold errors/disconnects, intercepts commands, enforces reset gating.
- `[NEW]` [app/services/brokers/reconciliation.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/reconciliation.py):
  - `BrokerReconciler` implementing `brokers.reconciliation@1`.
  - Multi-entity reconciliation: balances, positions, and active orders against provider snapshots.
- `[NEW]` Unit tests in `tests/services/brokers/catalog/`, `isolation_fencing/`, and `reconciliation/`.

### Phase 3: Trading Execution Adapters (MT5 & cTrader)

- `[NEW]` [app/services/brokers/mt5_adapter.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/mt5_adapter.py):
  - `Mt5Adapter` implementing `brokers.mt5@1`.
  - Replicates SQX `mt5api.py` calculation rules: Forex (`calc_mode=0`), CFD (`calc_mode=2`), Futures (`calc_mode=1/33`), point values, tick sizes, spread translation.
  - Session lifecycle, quote streaming, and command submission with deterministic offline mock fallback.
- `[NEW]` [app/services/brokers/ctrader_adapter.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/ctrader_adapter.py):
  - `CTraderAdapter` implementing `brokers.ctrader@1`.
  - cTrader Open API 2.0 transport connection (application/account authorization handshake, symbol list discovery, quote and trendbar streaming).
  - Deterministic offline mock protocol harness.
- `[NEW]` Unit tests in `tests/services/brokers/mt5/` and `ctrader/`.

### Phase 4: Data Manager External Feed Transport Connectors

- `[NEW]` [app/services/brokers/dukascopy.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/dukascopy.py):
  - `DukascopyFeedService` implementing `brokers.dukascopy@1`.
  - Replicates SQX `DataSourceDukascopy`: hourly `.bi5` binary tick chunk acquisition via HTTP streaming, `dukascopy.csv` symbol mapping. Pure transport streaming directly to caller.
- `[NEW]` [app/services/brokers/sq_equity.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/sq_equity.py):
  - `SQEquityFeedService` implementing `brokers.equity@1`.
  - Replicates SQX `DataSourceSQEquityData`: REST transport for exchanges, ticker lookup, and raw historical stock data streaming.
- `[NEW]` [app/services/brokers/sq_futures.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/sq_futures.py):
  - `SQFuturesFeedService` implementing `brokers.futures@1`.
  - Replicates SQX `DataSourceSQFuturesData`: REST transport for futures exchanges and raw continuous contract data streaming.
- `[NEW]` [app/services/brokers/darwinex.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/darwinex.py):
  - `DarwinexFeedService` implementing `brokers.darwinex@1`.
  - Replicates SQX `DataSourceDarwinex`: Darwinex tick data transport connector with `darwinex.csv` instrument mapping.
- `[NEW]` [app/services/brokers/crypto_adapter.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/crypto_adapter.py):
  - `CryptoBrokerService` implementing `brokers.crypto@1`.
  - Replicates SQX `DataSourceCrypto` / `CryptoExchangeBinance`: REST/WebSocket connector for Binance Spot/Futures and CCXT-compatible market streams.
- `[NEW]` [app/services/brokers/yahoo.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/brokers/yahoo.py):
  - `YahooFeedService` implementing `brokers.yahoo@1`.
  - Replicates SQX `DataSourceYahoo`: Cookie/crumb session acquisition and Yahoo Finance v8 chart JSON streaming.
- `[NEW]` Unit tests in `tests/services/brokers/<feature>/` for each of the 6 data source connectors.

### Phase 5: Registration, Consolidated Example & Full Qualification

- `[MODIFY]` [app/registry.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/registry.py):
  - Register all 12 feature factories (persistence + 11 service features) in `FEATURES`.
  - Add `"brokers"` profile to `PROFILES` and include all broker features in `"all"`.
- `[NEW]` [tests/examples/03_brokers.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/03_brokers.py):
  - Self-contained, realistic offline example exercising:
    1. Initializing broker persistence and discovering pre-seeded system profiles.
    2. Reversible symbol mapping with broker postfixes (`_roboforex`, `_dukascopy`).
    3. Feed connector streaming across Dukascopy, SQ Equity, SQ Futures, Darwinex, Crypto, and Yahoo.
    4. MT5 and cTrader session simulation.
    5. Disconnect detection, fail-closed isolation fencing, and automated state reconciliation.
- Verification & Qualification:
  - Run `uv run python scripts/architecture_check.py`.
  - Run change-scoped unit tests: `uv run pytest --no-cov tests/services/brokers/`.
  - Run example: `uv run python tests/examples/03_brokers.py`.
  - Run full suite: `uv run python scripts/ci_check.py`.

---

## 4. Dependencies and Contracts

- **Kernel Consumed:**
  - `app.kernel.context.FeatureContext`
  - `app.kernel.feature.FeatureSpec`
  - `app.kernel.logging.get_logger`
- **Public Domain Contracts (`app/contracts/brokers.py`):**
  - Exports: `BrokerCatalogService`, `BrokerFeedConnector`, `BrokerTradingAdapter`, `BrokerReconciliationService`, `BrokerFencingService`, `BrokerPersistenceService`.
  - Capability Tokens: `brokers.catalog@1`, `brokers.mt5@1`, `brokers.ctrader@1`, `brokers.dukascopy@1`, `brokers.equity@1`, `brokers.futures@1`, `brokers.darwinex@1`, `brokers.crypto@1`, `brokers.yahoo@1`, `brokers.reconciliation@1`, `brokers.fencing@1`, `persistence.brokers@1`.
- **Database Boundary:**
  - SQLite metadata exclusively in `app/services/persistence/brokers.py`. Feature modules never execute raw SQL or acquire raw connection objects.

---

## 5. Blockers, Risks, and Trade-offs

- **Risk:** Network dependencies in tests causing non-deterministic test failures.
  - **Mitigation:** Strict separation between transport protocol logic and underlying network sockets. Every connector supports a mock/loopback transport for tests and offline runs with zero live network calls.
- **Risk:** Bloating memory with raw tick/bar streams.
  - **Mitigation:** Pure streaming generator/iterator protocol (`AsyncIterator[RawTransportChunk]`) enabling zero-copy, chunked hand-off to consumer ingestion pipelines.

---

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope**:
  - Full implementation of all 11 broker service features + 1 persistence feature.
  - Public contract definitions in `app/contracts/brokers.py`.
  - Persistence schemas, migrations, and pre-seeded system brokers in `app/services/persistence/brokers.py`.
  - Complete unit, lifecycle, and removal test suites for each feature.
  - Consolidated usage example `tests/examples/03_brokers.py`.
  - Registration in `app/registry.py`.
- **Out of Scope / Non-Goals**:
  - Writing parquet market datasets or saving tick databases (owned by `D-DATA`).
  - Signal generation or order sizing logic (owned by `D-TRADING`).
  - Strategy backtesting matching engine (owned by `D-SIMULATOR`).

---

## 7. Verification Plan

### Automated Unit & Feature Tests
```bash
uv run pytest --no-cov tests/services/brokers/ -v
```

### Architectural Invariant Check
```bash
uv run python scripts/architecture_check.py
```

### Offline Usage Evidence Run
```bash
uv run python tests/examples/03_brokers.py
```

### Full Candidate CI Qualification
```bash
uv run python scripts/ci_check.py
```

---

## 8. Rollback & Contingency

To revert all changes:
```bash
git checkout 2abbf62 -- app/registry.py
git clean -fd app/contracts/brokers.py app/services/persistence/brokers.py app/services/brokers/ tests/services/brokers/ tests/examples/03_brokers.py
```

```text
ALLOWED_WRITE_PATHS:
- app/contracts/brokers.py
- app/services/persistence/brokers.py
- app/services/brokers/catalog.py
- app/services/brokers/mt5_adapter.py
- app/services/brokers/ctrader_adapter.py
- app/services/brokers/dukascopy.py
- app/services/brokers/sq_equity.py
- app/services/brokers/sq_futures.py
- app/services/brokers/darwinex.py
- app/services/brokers/crypto_adapter.py
- app/services/brokers/yahoo.py
- app/services/brokers/reconciliation.py
- app/services/brokers/isolation_fencing.py
- app/registry.py
- tests/services/brokers/
- tests/examples/03_brokers.py
- .agents/logs/2026-09-20T152500_brokers-full-implementation/
END_ALLOWED_WRITE_PATHS:
```
