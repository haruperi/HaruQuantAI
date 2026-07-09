# Phase 2 Data Foundation — Brownfield Upgrade Implementation Plan V2

## 0. Purpose

This document replaces the greenfield-style Phase 2 Data plan with a brownfield upgrade plan for the existing HaruQuantAI repository.

The goal is not to rebuild `app/services/data/` from scratch. The goal is to harden, refactor, and extend the current Data module while preserving its working collaboration with `app/services/brokers/` and protecting downstream imports already used by Strategy, Indicators, Research, Simulator, Trading, UI/API, and Conversation layers.

## 1. Non-Negotiable Brownfield Rules

- [ ] **DATA-UPG-001**: Preserve the existing `app/services/data/` module as the starting point.

  - Do not delete the existing module tree and recreate it from the old Phase 2 architecture diagram.
  - Upgrade by extraction, wrapping, adapter hardening, and test coverage.
  - Treat existing behavior as legacy working capability unless a test proves it unsafe.
- [ ] **DATA-UPG-002**: Preserve current public imports during the upgrade window.

  - Existing exports from `app.services.data` remain importable until an explicit deprecation/migration step is completed.
  - The stricter official AI-tool surface may be introduced through a catalog, but it must not break existing imports in the same sprint.
- [ ] **DATA-UPG-003**: Keep broker connectivity in `app/services/brokers/`.

  - Data may read broker market data through broker client factories.
  - Data must not own login, broker SDK lifecycle, account mutation, order mutation, or live execution policy.
  - Data may normalize and quality-check records returned by broker read calls.
- [ ] **DATA-UPG-004**: Apply the Phase 2 requirements as hardening overlays, not as a replacement file tree.

  - When a requirement already has partial implementation, add tests and close gaps.
  - When a requirement conflicts with current imports, introduce compatibility wrappers first.
  - When a requirement requires a split file, extract from the existing file only after characterization tests exist.
- [ ] **DATA-UPG-005**: No large move-only refactors before tests.

  - First create characterization tests around current behavior.
  - Then add missing contracts and wrappers.
  - Then extract files in small increments.

## 2. Current Repository Baseline

### 2.1 Existing Data package

Current implementation exists under:

```text
app/services/data/
├── __init__.py
├── gateway.py
├── models.py
├── normalization.py
├── scheduler.py
├── sources.py
├── storage.py
├── transforms.py
└── validation.py
```

Current data capabilities already include:

- Gateway retrieval through `get_data`.
- Symbol listing through `list_symbols`.
- Symbol metadata through `get_symbol_metadata`.
- Data availability inspection through `get_data_availability`.
- Real-time feed status through `get_feed_status`.
- Scheduler/job helpers.
- Local CSV/Parquet loading and saving.
- SQLite-backed cache and job/feed state.
- OHLCV/tick/spread Pydantic models.
- Source adapters for `csv`, `parquet`, `synthetic`, `mt5`, `ctrader`, `dukascopy`, `binance`, and `yahoo`.
- Resampling, tick aggregation, multi-timeframe alignment, labels, and deterministic synthetic data generation.

### 2.2 Existing Broker collaboration

Current broker collaboration already exists:

```text
app/services/data/sources.py
  -> BrokerBackedAdapter
  -> _get_mt5_client()
  -> _get_ctrader_client()
  -> _get_dukascopy_client()
  -> _get_binance_client()
  -> _get_yahoo_client()

app/services/brokers/
  -> lazy broker package exports
  -> provider clients
  -> broker router
```

This is the correct direction. The upgrade should formalize this as a read-only provider port instead of replacing it.

### 2.3 Current pain points to fix incrementally

- Importing Data currently initializes SQLite through a module-level `DatabaseHelper()` instance.
- Importing `scheduler.py` performs crash recovery at module load.
- `app.services.data.__all__` currently exposes many support functions, not only official tools.
- Public functions return raw native values instead of a uniform tool envelope.
- Data adapter registry instantiates broker-backed adapters at import time, although broker clients are still lazy inside factories.
- Some errors use broad exceptions or inconsistent error codes.
- Some functions use pandas DataFrames internally and must ensure no raw pandas objects cross official AI-tool boundaries.
- Cache writes use `INSERT OR REPLACE`, which is convenient but does not yet distinguish insert/update/no-op/conflict as required.
- Scheduler currently simulates update loops rather than performing real chunked backfill work.
- Feed status exists, but bounded buffer, heartbeat timeout, gap reconciliation, and overflow policies need hardening.

## 3. Target Upgrade Architecture

The final target should be a hardened version of the current module, not a reset.

### 3.1 Brownfield target tree

```text
app/services/data/
├── __init__.py                  # compatibility public gate; preserves current imports during migration
├── public_api.py                # official AI-tool catalog wrappers and envelope boundary
├── contracts.py                 # request/response contracts, provider ports, official tool DTOs
├── errors.py                    # data error codes and error mapping helpers
├── gateway.py                   # existing gateway, gradually slimmed into orchestration only
├── models.py                    # existing Pydantic record models; extended with metadata/quality models
├── normalization.py             # existing provider/file normalization; extended with quality flags
├── scheduler.py                 # existing job/feed API; import side effects removed
├── sources.py                   # existing source adapters; broker read port formalized
├── storage.py                   # existing SQLite/cache/file I/O; lazy init and idempotency hardened
├── transforms.py                # existing resample/alignment/tick/synthetic/label helpers
├── validation.py                # existing time/limit/license/bars validation
├── feeds.py                     # extracted bounded feed buffer/heartbeat/reconnect logic
├── persistence.py               # extracted repository/idempotency/migration helpers
└── README.md                    # module usage, boundaries, public/private exports, upgrade notes
```

### 3.2 Extraction rule

Only create new files when they reduce risk:

- `public_api.py` is allowed early because it wraps existing functions without moving them.
- `contracts.py` is allowed early because it gives tests stable DTOs and protocols.
- `errors.py` is allowed early because it centralizes deterministic error mapping.
- `feeds.py` should be extracted from `scheduler.py` only after tests cover current feed behavior.
- `persistence.py` should be extracted from `storage.py` only after tests cover current SQLite/cache behavior.

Do not split `gateway.py`, `sources.py`, `storage.py`, or `scheduler.py` into large folder trees in the first upgrade slice.

## 4. Public Boundary Policy

### 4.1 Compatibility exports

During the migration window, keep the current `app.services.data` imports stable.

- [ ] **DATA-UPG-006**: Keep current public imports working:

  - `get_data`
  - `list_symbols`
  - `get_market_hours`
  - `get_symbol_metadata`
  - `get_data_availability`
  - `get_feed_status`
  - scheduler helpers
  - storage helpers
  - transform helpers
  - validation helpers
- [ ] **DATA-UPG-007**: Add an explicit classification table in `__init__.py` or `public_api.py`:

  - `official_tool`
  - `public_support_api`
  - `legacy_public_compatibility`
  - `internal_only`
- [ ] **DATA-UPG-008**: Do not silently remove broad exports to satisfy the older strict three-tool target.

  - First add tests that document existing imports.
  - Then add official tool wrappers.
  - Then deprecate non-official root exports in a later sprint only after downstream modules are migrated.

### 4.2 Official AI-tool surface

The intended official AI-tool surface for Phase 2 should be:

```text
get_data
list_symbols
get_market_hours
get_feed_status
```

`get_feed_status` is included because current code already exposes it and Phase 2 requirements explicitly include read-only feed observability.

All other public functions remain callable support APIs unless explicitly promoted.

## 5. Broker/Data Boundary Contract

### 5.1 Ownership

- Data owns:

  - market data request validation;
  - source selection;
  - read-only market-data calls;
  - normalization into canonical records;
  - data quality flags;
  - caching and persistence of data artifacts;
  - feed observability and source status;
  - local file ingestion.
- Brokers own:

  - SDK imports;
  - terminal/client connection lifecycle;
  - authentication;
  - account/session handling;
  - broker-native request formats;
  - broker-specific read methods;
  - broker mutations and trade submission APIs.
- Trading/Live own:

  - order mutation;
  - live-readiness gates;
  - idempotency for broker mutations;
  - reconciliation of orders/positions/deals;
  - kill-switch enforcement for live mutation.

### 5.2 Data-to-broker rule

Data may call only read methods exposed by broker clients, such as:

- `get_bars(...)`
- `get_ticks(...)`
- symbol metadata or symbol discovery reads
- connection readiness/read-only status

Data must not call:

- `trade(...)`
- order submission
- order modification
- order cancellation
- position close
- account mutation
- live approval or risk bypass methods

### 5.3 Required upgrade task

- [ ] **DATA-UPG-009**: Add a `BrokerMarketDataPort` protocol in `contracts.py`.
  - It should describe only read-only data methods needed by `BrokerBackedAdapter`.
  - `BrokerBackedAdapter` should depend on this protocol instead of unconstrained `Any` clients where practical.
  - Tests should assert no data adapter calls mutation methods.

## 6. Implementation Sequence — Build on Existing Code

### Phase 2.0 — Baseline audit and safety net

Goal: freeze the current working behavior before refactoring.

- [ ] **DATA-UPG-010**: Add characterization tests for `app.services.data.__all__`.

  - Assert current exports remain importable.
  - Assert imports do not require live broker credentials.
  - Mark current broad export behavior as compatibility behavior.
- [ ] **DATA-UPG-011**: Add characterization tests for `get_data` using `source="synthetic"`.

  - OHLCV path.
  - tick path.
  - spread path where available.
  - unsupported data kind.
  - unsupported timeframe.
  - limit enforcement.
  - request ID propagation where observable.
- [ ] **DATA-UPG-012**: Add characterization tests for local file behavior.

  - safe path rejection for `..`;
  - hidden path rejection;
  - unsupported extension rejection;
  - CSV load success;
  - Parquet save/load where optional dependency is available;
  - overwrite rejection;
  - atomic write behavior.
- [ ] **DATA-UPG-013**: Add characterization tests for `sources.py`.

  - source registry contains existing source names;
  - unknown source fails deterministically;
  - broker-backed adapters do not connect at import time;
  - broker client factories are lazy.
- [ ] **DATA-UPG-014**: Add characterization tests for scheduler/feed status.

  - create job;
  - duplicate job rejection;
  - get job status;
  - missing job rejection;
  - registered feed status;
  - missing feed status.
- [ ] **DATA-UPG-015**: Add characterization tests for transforms.

  - resampling;
  - tick aggregation;
  - multi-timeframe no-lookahead alignment;
  - synthetic deterministic seed output;
  - label generation.

Acceptance:

- Existing Data tests pass.
- New characterization tests pass.
- Coverage for `app/services/data` is at least 80% before structural extraction begins.

### Phase 2.1 — Official tool wrappers without breaking imports

Goal: introduce a stable official tool surface while preserving current native APIs.

- [ ] **DATA-UPG-016**: Create `app/services/data/contracts.py`.

  - `DataRequest`
  - `ListSymbolsRequest`
  - `MarketHoursRequest`
  - `FeedStatusRequest`
  - `DataToolMetadata`
  - `DataToolEnvelope` or adapter to the shared HaruQuant envelope
  - `BrokerMarketDataPort`
  - `SourceAdapterPort`
- [ ] **DATA-UPG-017**: Create `app/services/data/errors.py`.

  - Map expected failures to deterministic codes:
    - `VALIDATION_FAILED`
    - `INVALID_INPUT`
    - `UNSUPPORTED_TIMEFRAME`
    - `UNSUPPORTED_OPERATION`
    - `AUTHENTICATION_FAILED`
    - `CREDENTIALS_MISSING`
    - `BROKER_UNAVAILABLE`
    - `SERVICE_UNAVAILABLE`
    - `CIRCUIT_BREAKER_OPEN`
    - `LICENSE_RESTRICTION`
    - `DATA_NOT_FOUND`
    - `DATA_SCHEMA_DRIFT`
    - `BUFFER_OVERFLOW`
    - `DATA_DROPPED`
    - `FEED_HEARTBEAT_TIMEOUT`
    - `FEED_RECONCILIATION_FAILED`
    - `STATE_RECOVERY_FAILED`
    - `DATA_SERIALIZATION_FAILED`
- [ ] **DATA-UPG-018**: Create `app/services/data/public_api.py`.

  - Wrap existing native functions instead of replacing them.
  - Official wrappers return standard envelopes.
  - Native functions keep returning current native values for existing internal callers.
- [ ] **DATA-UPG-019**: Add official wrapper functions:

  - `get_data_tool(...)`
  - `list_symbols_tool(...)`
  - `get_market_hours_tool(...)`
  - `get_feed_status_tool(...)`
- [ ] **DATA-UPG-020**: Update `__init__.py` carefully.

  - Preserve current exports.
  - Add `OFFICIAL_DATA_TOOLS` catalog.
  - Do not remove current exports in this phase.

Acceptance:

- Existing imports still work.
- Official wrappers return envelope-shaped success and error payloads.
- No raw exception reaches the wrapper boundary.
- Official wrapper outputs are JSON-safe.

### Phase 2.2 — Import safety and lazy initialization

Goal: remove side effects from module import without breaking behavior.

- [ ] **DATA-UPG-021**: Make SQLite initialization lazy.

  - Replace eager `db_helper = DatabaseHelper()` with a lazy accessor such as `get_db_helper()`.
  - Keep a compatibility `db_helper` facade only if existing code needs it.
  - Ensure imports do not create files or run migrations unless a function uses persistence.
- [ ] **DATA-UPG-022**: Move scheduler crash recovery out of import time.

  - Remove automatic `recover_crashed_jobs()` execution on module import.
  - Add explicit `recover_data_jobs_on_startup(...)` or `initialize_data_scheduler(...)`.
  - UI/API or app lifespan may call it intentionally.
- [ ] **DATA-UPG-023**: Make adapter registry safer.

  - Keep `ADAPTER_REGISTRY` compatibility.
  - Ensure registry creation does not connect to brokers.
  - Add lazy registration hooks for optional providers.

Acceptance:

- `import app.services.data` performs no database file writes, no migrations, no broker connections, no network calls, and no background tasks.
- Existing function calls still initialize only the required dependencies when invoked.

### Phase 2.3 — Gateway hardening

Goal: harden `gateway.py` in place.

- [ ] **DATA-UPG-024**: Validate `workflow_context` against the approved set.

  - `research`
  - `backtest`
  - `validation`
  - `risk`
  - `execution_bound`
- [ ] **DATA-UPG-025**: Enforce start/end timestamp order.

  - `start_time < end_time` required.
  - Equal or reversed ranges return deterministic validation error.
- [ ] **DATA-UPG-026**: Standardize `data_kind` behavior.

  - `ohlcv`
  - `ticks`
  - `spreads`
  - `volume`
  - Unsupported values fail with deterministic code.
- [ ] **DATA-UPG-027**: Add gateway result metadata.

  - source
  - symbol
  - timeframe
  - data kind
  - record count
  - volume kind
  - schema version
  - normalization version
  - raw hash where available
  - cache status
  - warnings
- [ ] **DATA-UPG-028**: Ensure gateway cache behavior is explicit.

  - `refresh_and_return`
  - `return_stale`
  - `fail`
  - invalid stale behavior rejected.
- [ ] **DATA-UPG-029**: Normalize all official-boundary timestamps to UTC ISO-8601 strings.

Acceptance:

- Gateway tests cover all supported data kinds and failure modes.
- Official wrapper returns metadata consistently.
- Native `get_data` remains compatible.

### Phase 2.4 — Source adapter and broker-read hardening

Goal: keep current adapter model, but make it safer and clearer.

- [ ] **DATA-UPG-030**: Formalize `SourceAdapterProtocol` fields and return behavior.

  - no raw pandas at public boundary;
  - adapter may use pandas internally;
  - adapter returns `list[dict[str, Any]]` records only;
  - adapter failures map to deterministic errors.
- [ ] **DATA-UPG-031**: Harden `BrokerBackedAdapter`.

  - Accept a `BrokerMarketDataPort` factory.
  - Only call read methods.
  - Add timeout/error classification for broker reads.
  - Map connection/auth failures to deterministic error codes.
- [ ] **DATA-UPG-032**: Add broker-read contract tests with fake broker clients.

  - connected client returns bars;
  - disconnected client connects lazily;
  - failed connection trips circuit breaker;
  - unsupported broker result shape fails safely;
  - mutation methods are never called.
- [ ] **DATA-UPG-033**: Preserve the existing source names.

  - `csv`
  - `parquet`
  - `synthetic`
  - `mt5`
  - `ctrader`
  - `dukascopy`
  - `binance`
  - `yahoo`

Acceptance:

- Broker-backed reads continue through `app/services/brokers`.
- Data does not import broker SDKs directly except through broker service modules.
- Optional provider dependencies fail only when their provider is used.

### Phase 2.5 — Storage and persistence hardening

Goal: improve the existing SQLite/file/cache layer without replacing it.

- [ ] **DATA-UPG-034**: Add an explicit persistence contract.

  - cache read/write;
  - job state read/write;
  - feed state read/write;
  - circuit breaker state read/write;
  - license metadata read/write;
  - migration state read/write.
- [ ] **DATA-UPG-035**: Replace silent `INSERT OR REPLACE` where conflicts matter.

  - Distinguish insert, update, no-op duplicate, and conflict.
  - Keep retry-safe cache writes.
  - Never silently overwrite committed source data.
- [ ] **DATA-UPG-036**: Make migrations auditable.

  - migration id;
  - source schema version;
  - target schema version;
  - applied timestamp;
  - rollback guidance where practical.
- [ ] **DATA-UPG-037**: Add connection leak tests.

  - connection close on success;
  - connection close on failure;
  - concurrent reads do not exhaust SQLite connections;
  - busy timeout behavior is deterministic.
- [ ] **DATA-UPG-038**: Add raw-hash and normalization-version propagation.

Acceptance:

- Existing file I/O functions still work.
- SQLite initialization is explicit/lazy.
- Persistence behavior is covered by unit tests.

### Phase 2.6 — Feed observability and real-time state

Goal: upgrade current feed status into a reliable read-only observability surface.

- [ ] **DATA-UPG-039**: Extract feed state helpers to `feeds.py` after tests exist.

  - Keep `scheduler.get_feed_status` compatibility wrapper if needed.
- [ ] **DATA-UPG-040**: Add bounded buffer behavior.

  - capacity;
  - buffer depth;
  - overflow policy;
  - dropped event count;
  - gap count.
- [ ] **DATA-UPG-041**: Add heartbeat timeout detection.

  - last heartbeat timestamp;
  - timeout threshold;
  - `FEED_HEARTBEAT_TIMEOUT` status/error.
- [ ] **DATA-UPG-042**: Add explicit overflow policies.

  - `halt`
  - `drop_and_reconcile`
  - `backpressure`
- [ ] **DATA-UPG-043**: Add reconnect policy data model.

  - max retries;
  - base backoff;
  - max backoff;
  - jitter;
  - circuit breaker cooldown.

Acceptance:

- `get_feed_status` remains read-only.
- No raw sockets, SDK objects, clients, or credential-bearing connection strings are returned.
- Feed status is JSON-safe.

### Phase 2.7 — Data quality, normalization, and lineage

Goal: make existing normalization safer for downstream research/backtest/risk users.

- [ ] **DATA-UPG-044**: Add data quality flags to record metadata.

  - missing field;
  - stale record;
  - partial record;
  - duplicate timestamp;
  - non-monotonic timestamp;
  - out-of-range OHLC;
  - inverted bid/ask;
  - zero or negative prices;
  - NaN/infinity;
  - license restriction;
  - provider revision.
- [ ] **DATA-UPG-045**: Keep gaps visible.

  - Do not silently fill missing bars outside explicit research workflows.
  - Record fill/interpolation decisions in metadata.
- [ ] **DATA-UPG-046**: Add volume kind disclosure.

  - `tick_volume`
  - `real_volume`
  - `broker_volume`
  - `synthetic_volume`
  - `unknown`
- [ ] **DATA-UPG-047**: Add data lineage metadata.

  - source;
  - provider;
  - license/attribution;
  - source revision;
  - raw hash;
  - normalization version;
  - schema version;
  - retrieval timestamp;
  - cache/persistence status.

Acceptance:

- Downstream modules can decide whether a record is safe for research, backtest, validation, risk, or execution-bound workflows.
- Official wrappers expose quality metadata without leaking raw provider objects.

### Phase 2.8 — Transform hardening

Goal: preserve existing transform helpers while making them safer and more deterministic.

- [ ] **DATA-UPG-048**: Add no-lookahead tests for `align_multitimeframe_data`.
- [ ] **DATA-UPG-049**: Add deterministic tests for synthetic generators.
- [ ] **DATA-UPG-050**: Add resampling performance test.

  - 100,000 M1 bars to H1 target should stay under the approved local benchmark threshold.
  - Keep threshold configurable if CI hardware varies.
- [ ] **DATA-UPG-051**: Add transform output schema tests.

  - no raw NumPy scalar leakage;
  - timestamps are JSON-safe;
  - output preserves symbol/timeframe/source fields.

Acceptance:

- Existing transform API remains available.
- Tests prove deterministic output and no-lookahead behavior.

### Phase 2.9 — Documentation and migration notes

Goal: document how the brownfield module works now and how it will evolve.

- [ ] **DATA-UPG-052**: Add or update `app/services/data/README.md`.

  - module ownership;
  - broker boundary;
  - official tools;
  - compatibility exports;
  - native APIs vs tool wrappers;
  - source adapter lifecycle;
  - persistence lifecycle;
  - feed status behavior;
  - examples.
- [ ] **DATA-UPG-053**: Add migration notes for future stricter public boundary.

  - Current broad root exports are compatibility exports.
  - Future official AI-tool exports are cataloged separately.
  - Downstream modules should gradually move to official wrappers or stable support APIs.
- [ ] **DATA-UPG-054**: Add usage examples.

  - `example_01_get_synthetic_ohlcv()`
  - `example_02_list_symbols()`
  - `example_03_get_market_hours()`
  - `example_04_get_feed_status()`
  - `example_05_save_and_load_local_dataset()`
  - `example_06_resample_ohlcv()`
  - `example_07_broker_backed_read_with_fake_client()`

Acceptance:

- README explains that this is an upgrade of the existing module, not a clean-room rebuild.
- Examples run without live broker credentials by default.

## 7. File-by-File Upgrade Map

### 7.1 `app/services/data/__init__.py`

Current role: package export gate.

Upgrade steps:

- Preserve current exports initially.
- Add explicit export classification.
- Add `OFFICIAL_DATA_TOOLS` catalog.
- Add tests preventing accidental export removal.
- Later, after downstream migration, reduce official root tool surface only through a documented deprecation step.

Do not:

- suddenly reduce `__all__` to only three functions;
- import heavy provider SDKs directly;
- trigger database initialization or background recovery through imports.

### 7.2 `app/services/data/gateway.py`

Current role: gateway orchestration, cache routing, source adapter selection, normalization, and native public functions.

Upgrade steps:

- Keep current native functions.
- Add stronger request validation.
- Add deterministic error mapping.
- Add metadata-rich gateway result internally.
- Keep public native return shape stable unless a wrapper is used.
- Move envelope behavior to `public_api.py`, not into the core gateway.

### 7.3 `app/services/data/models.py`

Current role: Pydantic record models for OHLCV, ticks, spreads, symbol metadata, and data availability.

Upgrade steps:

- Add quality metadata models.
- Add lineage/provenance models.
- Add feed/job status models if not extracted elsewhere.
- Keep existing model names stable.

### 7.4 `app/services/data/sources.py`

Current role: source adapter protocol, local/synthetic/broker-backed adapters, registry, and circuit breaker state helpers.

Upgrade steps:

- Formalize provider port contracts.
- Keep source names stable.
- Keep broker reads through `app.services.brokers`.
- Move mutation-blocking tests into this layer.
- Consider extracting circuit breaker helpers only after tests exist.

### 7.5 `app/services/data/storage.py`

Current role: SQLite setup, migrations, cache, safe local file paths, atomic writes, CSV/Parquet load/save.

Upgrade steps:

- Remove eager database initialization.
- Add lazy DB accessor.
- Add persistence operation result models.
- Improve idempotency and conflict behavior.
- Add migration metadata and compatibility tests.

### 7.6 `app/services/data/scheduler.py`

Current role: persisted jobs, in-memory tasks, crash recovery, feed registration/status/overflow.

Upgrade steps:

- Remove import-time recovery.
- Keep current job functions.
- Extract feed state to `feeds.py` after tests.
- Replace simulated run behavior with real chunked backfill only in a later slice.

### 7.7 `app/services/data/normalization.py`

Current role: provider DataFrame/file conversion to normalized records.

Upgrade steps:

- Preserve adapter conversion functions.
- Add schema validation around provider DataFrame columns.
- Add quality flags and raw-hash metadata.
- Ensure all outputs are JSON-safe.

### 7.8 `app/services/data/transforms.py`

Current role: resampling, alignment, tick aggregation, synthetic generation, labels.

Upgrade steps:

- Keep API stable.
- Add stricter no-lookahead tests.
- Add deterministic seed tests.
- Ensure NumPy/pandas internals never leak at official boundary.

### 7.9 `app/services/data/validation.py`

Current role: limits, precision, timeframe, session, license, and bar validation.

Upgrade steps:

- Add workflow context validation.
- Add stale behavior validation.
- Add data kind validation.
- Add richer deterministic error codes.
- Avoid database setup at import through lazy persistence accessor.

### 7.10 `app/services/brokers/`

Current role: broker SDK/client boundary.

Upgrade steps for Data compatibility:

- Keep broker clients lazy-loadable.
- Keep read methods stable for Data adapters.
- Do not move broker SDK imports into Data.
- Add fake broker clients for Data tests.
- Add read-only provider contract tests.

## 8. Dependency Order

Implement in this order:

1. Tests around current exports and current behavior.
2. `contracts.py` and `errors.py`.
3. `public_api.py` wrappers.
4. Import-safety/lazy initialization changes.
5. Gateway validation and metadata hardening.
6. Broker-backed source adapter contract hardening.
7. SQLite/cache/idempotency hardening.
8. Feed status/buffer/heartbeat hardening.
9. Transform/normalization/lineage hardening.
10. README/examples and deprecation notes.

Do not start file extraction before steps 1–4 are passing.

## 9. Testing Strategy

### 9.1 Minimum test groups

```text
tests/services/data/
├── test_data_public_exports.py
├── test_data_public_api_wrappers.py
├── test_data_gateway.py
├── test_data_sources.py
├── test_data_broker_read_port.py
├── test_data_storage.py
├── test_data_scheduler.py
├── test_data_feeds.py
├── test_data_validation.py
├── test_data_normalization.py
├── test_data_transforms.py
└── test_data_import_safety.py
```

### 9.2 Required assertions

- Imports are side-effect safe.
- Existing public imports remain available.
- Official tool wrappers return standard envelopes.
- Native APIs remain usable by internal modules.
- Broker reads use broker service clients and never call broker mutation methods.
- Raw pandas/NumPy/broker SDK objects never cross official wrapper boundary.
- Cache and persistence errors are deterministic.
- Feed status is read-only and redacted.
- No silent fallback hides data loss, interpolation, or stale cache behavior.
- Coverage for `app/services/data` stays above 80%.

## 10. Definition of Done

This upgrade is complete when:

- [ ] Existing data imports still work.
- [ ] Official Data tool wrappers exist and return standard envelopes.
- [ ] Data imports do not initialize SQLite, run recovery, start jobs, connect to brokers, or touch network.
- [ ] Broker connectivity remains owned by `app/services/brokers`.
- [ ] Data adapters use broker reads only.
- [ ] SQLite/cache/file persistence is tested and lazy.
- [ ] Feed status is read-only, bounded, and JSON-safe.
- [ ] Data quality and lineage metadata are available to downstream modules.
- [ ] All tests pass with at least 80% Data module coverage.
- [ ] README and examples explain the brownfield upgrade path.

## 11. Explicit Non-Goals

- Do not rebuild `app/services/data` from scratch.
- Do not move broker SDK connection code into Data.
- Do not remove current public exports without a separate migration sprint.
- Do not make Data own trading, order execution, risk approval, or live readiness policy.
- Do not introduce a large folder tree before tests and wrappers are in place.
- Do not make live broker credentials required for local Data tests.
- Do not return raw pandas DataFrames, broker SDK objects, sockets, stream handles, database connections, or unstructured exceptions from official tools.

## 12. Builder Handoff Prompt

Use this prompt for the coding agent:

```text
You are upgrading the existing HaruQuantAI Data module in a brownfield repository.

Authoritative plan: docs/dev/phase-implementation-plan/02-data.md.

Do not rebuild app/services/data from scratch.
Do not delete or rename existing public functions until compatibility tests and migration notes exist.
Preserve collaboration with app/services/brokers; broker clients own SDK connections and Data may only perform read-only market-data calls through broker read ports.

Implementation order:
1. Add characterization tests for current app.services.data exports and existing behavior.
2. Add app/services/data/contracts.py and errors.py.
3. Add public_api.py official wrappers returning standard envelopes while native functions remain compatible.
4. Remove import-time side effects from storage.py and scheduler.py.
5. Harden gateway validation, source adapter contracts, persistence, feed status, normalization, transforms, README, and examples.

Rules:
- File docstring at top of each new or edited file.
- Google-style docstrings for every function/class.
- Use project logger for significant steps.
- Keep modules decoupled and import-safe.
- Use fake broker clients in tests; do not require live broker credentials.
- Maintain >80% Data module coverage.
- Run Ruff and tests before reporting completion.
```

## 13. Supplemental Brownfield Tasks Required for Full Requirement Traceability

The brownfield plan above covers the main migration path. The following supplemental tasks close the remaining one-to-one traceability gaps from the original `02-data.md` requirement ledger without changing the brownfield principle of preserving the current implementation first.

- [ ] **DATA-UPG-055**: Maintain a requirement coverage matrix.

  - Track every original `DATA-FR-*`, `DATA-NFR-*`, `DATA-TEST-*`, `DATA-EX-*`, and `DATA-BR-*` item against one or more brownfield upgrade tasks.
  - Treat unmapped rows as blockers before implementation handoff.
- [ ] **DATA-UPG-056**: Add a central limits manifest.

  - Define maximum records, date range bounds, cache TTL defaults, synthetic generation limits, backfill chunk size, feed buffer depth, scheduler frequency, payload response limits, and per-workflow overrides.
  - Store the manifest in documentation and reference it from validation/gateway tests.
- [ ] **DATA-UPG-057**: Add operational documentation, runbooks, and production sign-off evidence.

  - Document official tool catalog, compatibility exports, environment variables, crash recovery, circuit breaker recovery, troubleshooting, response examples, and release sign-off.
  - Include rollback notes and implementation report requirements.
- [ ] **DATA-UPG-058**: Harden local path safety and approved storage roots.

  - Enforce approved roots: `data/raw/`, `data/processed/`, `data/cache/`, and `artifacts/data/` unless project settings explicitly extend them.
  - Reject parent traversal, hidden/system paths unless configured, unsupported extensions, and unsafe absolute paths.
- [ ] **DATA-UPG-059**: Harden credential and secret handling.

  - Ensure data adapters resolve credentials only through approved configuration/environment paths owned by broker/client layers.
  - Redact passwords, access tokens, API keys, account secrets, broker secrets, raw credential payloads, socket handles, and client internals from logs, exceptions, metadata, and examples.
- [ ] **DATA-UPG-060**: Add source readiness and license manifests with enforcement.

  - Track readiness (`production`, `staging`, `experimental`, `not_available`) and license/attribution rules for each source.
  - Enforce readiness, license, workflow context, and fallback policy before retrieval, storage, scheduler export, artifact generation, or backfill.
- [ ] **DATA-UPG-061**: Define market/session calendar ownership.

  - Keep Phase 1 `get_market_hours` and `get_trading_sessions` limited to current configured hours.
  - Explicitly return `historical_hours_supported=false` and deterministic `UNSUPPORTED_OPERATION` for historical market-hour reconstruction until an approved calendar provider exists.
- [ ] **DATA-UPG-062**: Add downstream canonical contract alignment and golden fixtures.

  - Align Data outputs with Strategy, Simulation, Optimization, Analytics, Risk, Portfolio, Execution, and Agent workflows.
  - Create golden dataset fixtures reused across downstream regression tests.
- [ ] **DATA-UPG-063**: Add retention, backup/restore, and schema ownership policies.

  - Define raw provider payload retention separately from normalized canonical dataset retention.
  - Define backup/restore policy for historical data, cache data, normalized datasets, quality reports, provider metadata, migrations, and manifests.
- [ ] **DATA-UPG-064**: Add final quality gates, rollback evidence, and handoff report.

  - Require Ruff format/check, mypy strict where project-supported, pytest, coverage above 80%, example execution, implementation report, rollback path, and changelog/docs updates before handoff.

## 14. Original `02-data.md` V1 Requirement Coverage Matrix

This matrix maps every original primary requirement ID from `02-data.md` into one or more brownfield upgrade tasks. It deliberately preserves the capability intent of the original ledger while replacing greenfield rebuild sequencing with a safer migration path over the existing `app/services/data/` implementation.

Coverage status meanings:

- **Covered**: directly mapped to existing brownfield tasks.
- **Covered with brownfield reinterpretation**: the original greenfield wording is intentionally satisfied through preservation-first migration.
- **Covered by supplemental task**: now covered by `DATA-UPG-055` through `DATA-UPG-064` above.
- **Covered / deferred by design**: intentionally deferred with deterministic behavior and documentation, matching the original requirement wording.

Total mapped primary requirements: **139** (`DATA-FR`: 103, `DATA-NFR`: 10, `DATA-TEST`: 3, `DATA-EX`: 16, `DATA-BR`: 7).

### Data Gateway Service

| Original ID | Requirement summary                                                                                                 | Brownfield task(s)                                                                                             | Current code / artifact anchor                              | Migration action                                                                                                                             | Test / evidence target                                       | Status                                   |
| ----------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------- |
| DATA-FR-001 | Scope the module as a greenfield professional production module that preserves current data-domain capab…          | DATA-UPG-001, DATA-UPG-004, DATA-UPG-055                                                                       | app/services/data/*                                         | Reinterpret greenfield wording as brownfield hardening: preserve capabilities and upgrade current code instead of replacing it.              | coverage matrix review; characterization tests               | Covered with brownfield reinterpretation |
| DATA-FR-002 | Defer public streaming subscription tools and historical market-hours reconstruction beyond Phase 1, tra…          | DATA-UPG-052, DATA-UPG-057, DATA-UPG-061                                                                       | README; DOMAIN.md; validation.py                            | Document public streaming and historical-hours reconstruction as deferred; return deterministic unsupported-operation behavior where called. | test_market_hours.py; docs checklist                         | Covered / deferred by design             |
| DATA-FR-003 | Implement a__init__ containing only imports and`__all__`, exporting exactly the approved official tool…          | DATA-UPG-006, DATA-UPG-007, DATA-UPG-008, DATA-UPG-020                                                         | app/services/data/__init__.py; public_api.py          | Preserve existing imports during transition; classify official tools separately from compatibility exports before any stricter root gate.    | test_public_exports.py                                       | Covered with compatibility guard         |
| DATA-FR-004 | Type every official tool, require it to accept and propagate`request_id`, log structured events, and pr…         | DATA-UPG-017, DATA-UPG-018, DATA-UPG-019, DATA-UPG-052, DATA-UPG-054                                           | public_api.py; errors.py; README; examples/data_examples.py | Add typed official wrappers, request_id propagation, structured logs, safe examples, and no raw credential exposure.                         | test_public_api.py; test_error_mapping.py; example execution | Covered                                  |
| DATA-FR-005 | Normalize all timestamps crossing the official AI-tool boundary to UTC ISO 8601 strings, including start…          | DATA-UPG-019, DATA-UPG-029, DATA-UPG-046, DATA-UPG-061                                                         | public_api.py; normalization.py; validation.py              | Normalize official-boundary timestamps to UTC ISO strings and disclose volume_kind; keep market-hours current-only.                          | test_utc_boundary.py; test_market_hours.py                   | Covered                                  |
| DATA-FR-006 | Reject unsafe filesystem input: parent traversal using`..`, hidden/system directories unless explicitly…         | DATA-UPG-058                                                                                                   | validation.py; storage.py                                   | Add approved-root validation, parent traversal rejection, hidden/system path policy, and extension allowlist.                                | test_path_safety.py                                          | Covered by supplemental task             |
| DATA-FR-007 | Map deterministic failure conditions to error codes without exposing raw exceptions: `AUTHENTICATION_FAI…          | DATA-UPG-017, DATA-UPG-059                                                                                     | errors.py; public_api.py                                    | Map expected data/provider/security failures into deterministic error codes with redaction.                                                  | test_error_mapping.py                                        | Covered                                  |
| DATA-FR-008 | Restrict`workflow_context` to the exhaustive set `research`, `backtest`, `validation`, `risk`, and `exe… | DATA-UPG-024                                                                                                   | contracts.py; gateway.py; validation.py                     | Restrict workflow_context to approved values and reject unsupported values deterministically.                                                | test_validation.py                                           | Covered                                  |
| DATA-FR-009 | Require start to precede end, returning`TIMESTAMP_OVERLAP` when overlap has no safe policy.                       | DATA-UPG-025                                                                                                   | validation.py; gateway.py                                   | Require start before end and use deterministic timestamp overlap/order errors.                                                               | test_validation.py                                           | Covered                                  |
| DATA-FR-010 | Make state writes atomic, stale-lock recovery auditable, crash recovery idempotent and auditable, and ci…          | DATA-UPG-021, DATA-UPG-022, DATA-UPG-034, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038                             | storage.py; scheduler.py; persistence.py                    | Make state writes atomic, recovery idempotent/auditable, migrations reversible, and circuit-breaker state persistent.                        | test_storage_persistence.py; test_scheduler_recovery.py      | Covered                                  |
| DATA-FR-011 | Resolve credentials internally from approved configuration or environment variables: never accept raw pa…          | DATA-UPG-003, DATA-UPG-031, DATA-UPG-059                                                                       | sources.py; app/services/brokers/*                          | Keep credential resolution in broker/client layers and prevent raw password inputs at data boundary.                                         | test_redaction.py; test_broker_read_only_contract.py         | Covered                                  |
| DATA-FR-012 | Keep production logic free of`print()`; ensure resampling 100,000 M1 bars to H1 targets under 3 seconds…         | DATA-UPG-050, DATA-UPG-064                                                                                     | transforms.py; CI                                           | Remove print-style production output; assert resampling performance and label timestamp alignment.                                           | test_transform_performance.py; lint gates                    | Covered                                  |
| DATA-FR-013 | Achieve coverage above 80% with production sign-off commands passing, and write tests covering: connecti…          | DATA-UPG-010, DATA-UPG-011, DATA-UPG-012, DATA-UPG-013, DATA-UPG-014, DATA-UPG-015, DATA-UPG-037, DATA-UPG-064 | tests/services/data/*                                       | Start with characterization tests, then add coverage for leaks, conflict behavior, import safety, and sign-off commands.                     | coverage report >80%; CI gates                               | Covered                                  |

### Market Data Feeds Integration

| Original ID | Requirement summary                                                                                              | Brownfield task(s)                                                                               | Current code / artifact anchor              | Migration action                                                                                                                   | Test / evidence target                                         | Status                       |
| ----------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------- |
| DATA-FR-014 | Bring internal real-time feed support, feed state, and feed status into scope for Phase 1 production rea…       | DATA-UPG-039, DATA-UPG-040, DATA-UPG-041, DATA-UPG-042, DATA-UPG-043                             | app/services/data/scheduler.py; feeds.py    | Extract feed state only after tests; add bounded buffers, heartbeat, overflow policy, reconnect policy, and read-only feed status. | tests/services/data/test_feed_status.py; test_feed_overflow.py | Covered                      |
| DATA-FR-015 | Expose exactly one low-risk, read-only real-time feed observability tool,`get_feed_status`, reporting s…      | DATA-UPG-039, DATA-UPG-040, DATA-UPG-041, DATA-UPG-042, DATA-UPG-043                             | app/services/data/scheduler.py; feeds.py    | Extract feed state only after tests; add bounded buffers, heartbeat, overflow policy, reconnect policy, and read-only feed status. | tests/services/data/test_feed_status.py; test_feed_overflow.py | Covered                      |
| DATA-FR-016 | Extend the deterministic error-code list with`VALIDATION_FAILED`, `BUFFER_OVERFLOW`, `DATA_DROPPED`, `F…  | DATA-UPG-039, DATA-UPG-040, DATA-UPG-041, DATA-UPG-042, DATA-UPG-043                             | app/services/data/scheduler.py; feeds.py    | Extract feed state only after tests; add bounded buffers, heartbeat, overflow policy, reconnect policy, and read-only feed status. | tests/services/data/test_feed_status.py; test_feed_overflow.py | Covered                      |
| DATA-FR-017 | Normalize real-time records to the same OHLCV/tick/spread contracts and UTC timestamp normalization used…       | DATA-UPG-039, DATA-UPG-040, DATA-UPG-041, DATA-UPG-042, DATA-UPG-043                             | app/services/data/scheduler.py; feeds.py    | Extract feed state only after tests; add bounded buffers, heartbeat, overflow policy, reconnect policy, and read-only feed status. | tests/services/data/test_feed_status.py; test_feed_overflow.py | Covered                      |
| DATA-FR-018 | Enforce bounded buffers and an explicit overflow policy (`halt`, `drop_and_reconcile`, or `backpressure`… | DATA-UPG-039, DATA-UPG-040, DATA-UPG-041, DATA-UPG-042, DATA-UPG-043                             | app/services/data/scheduler.py; feeds.py    | Extract feed state only after tests; add bounded buffers, heartbeat, overflow policy, reconnect policy, and read-only feed status. | tests/services/data/test_feed_status.py; test_feed_overflow.py | Covered                      |
| DATA-FR-019 | Maintain heartbeat tracking and detect timeouts; reconnect/retry using exponential backoff with randomiz…       | DATA-UPG-039, DATA-UPG-040, DATA-UPG-041, DATA-UPG-042, DATA-UPG-043                             | app/services/data/scheduler.py; feeds.py    | Extract feed state only after tests; add bounded buffers, heartbeat, overflow policy, reconnect policy, and read-only feed status. | tests/services/data/test_feed_status.py; test_feed_overflow.py | Covered                      |
| DATA-FR-020 | Define and gate the promotion path for staging real-time sources: initial source readiness is`staging`…       | DATA-UPG-039, DATA-UPG-040, DATA-UPG-041, DATA-UPG-042, DATA-UPG-043, DATA-UPG-060               | feeds.py; sources.py                        | Gate real-time source promotion with readiness manifest and required buffer/heartbeat/reconnect tests.                             | test_feed_status.py; test_source_readiness.py                  | Covered by supplemental task |
| DATA-FR-021 | Write tests covering: dropped data gap creation; feed heartbeat tracking and timeout; feed buffer limit…        | DATA-UPG-014, DATA-UPG-039, DATA-UPG-040, DATA-UPG-041, DATA-UPG-042, DATA-UPG-043, DATA-UPG-064 | scheduler.py; feeds.py; tests/services/data | Add feed characterization and overflow/timeout/gap/reconnect/readiness tests.                                                      | test_feed_overflow.py; test_feed_timeout.py                    | Covered                      |

### Data Storage and Database Persistence

| Original ID | Requirement summary                                                                                            | Brownfield task(s)                                                                 | Current code / artifact anchor               | Migration action                                                                                                                    | Test / evidence target                                                 | Status  |
| ----------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------- |
| DATA-FR-022 | Make SQLite the default single-node ACID-capable persistence backend (sufficient for single-node local s…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-023 | Derive data ingestion and backfill idempotency keys from a hash of source, symbol, data kind, timeframe,…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-024 | Enforce database connection pool limits, timeouts, and automatic leak detection so long-running real-tim…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-025 | Persist source circuit breaker state, source revision/raw-hash metadata, data license/attribution metada…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-026 | Version, audit, and make reversible all database migrations (migration ID, source schema version, target…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-027 | Keep all internal/raw objects (pandas DataFrames, NumPy arrays, broker SDK objects, HTTP/MCP clients, so…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-028 | Map persistence failures to deterministic error codes (`DATABASE_ERROR`, `DB_CONNECTION_ERROR`, `DB_WRIT… | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-029 | Persist large historical datasets by reference (metadata) instead of inline when response limits are exc…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-030 | Define standard response/persistence metadata for every official tool and persistence request: tool name…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |
| DATA-FR-031 | Write tests covering: persistence transactions; SQLite/default persistence backend initialization; datab…     | DATA-UPG-021, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038 | app/services/data/storage.py; persistence.py | Make SQLite lazy and auditable; add persistence contracts, idempotency keys, migrations, leak checks, and source revision metadata. | tests/services/data/test_storage_persistence.py; test_import_safety.py | Covered |

### Data Domain Documentation and Architecture Overview

| Original ID | Requirement summary                                                                                         | Brownfield task(s)                                     | Current code / artifact anchor     | Migration action                                                                                            | Test / evidence target | Status                       |
| ----------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------- | ---------------------------- |
| DATA-FR-032 | Place this requirements document in`docs/planning/DOMAIN.md` (it covers the full data module rather tha… | DATA-UPG-052, DATA-UPG-055, DATA-UPG-056, DATA-UPG-057 | README; DOMAIN.md; coverage matrix | Add DOMAIN/README coverage, tool catalog, export list, env refs, crash/circuit runbooks, sign-off template. | docs checklist         | Covered by supplemental task |

### Data Ingestion Scheduler and Cron Orchestrator

| Original ID | Requirement summary                                                                                         | Brownfield task(s)                                                                                             | Current code / artifact anchor                                       | Migration action                                                                                                                                       | Test / evidence target                                           | Status                       |
| ----------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- | ---------------------------- |
| DATA-FR-033 | Resolve the scheduler naming conflict by exporting exactly`create_data_update_job`, `start_data_update_… | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-034 | Implement each scheduler lifecycle tool with its specific contract:`create_data_update_job` creates per… | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-035 | Define job and request schemas: scheduler job requests include job name, source, symbol(s), optional tim…  | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-036 | Make scheduler job lifecycle explicit, idempotent, and crash-recoverable: duplicate job creation is idem…  | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-037 | Implement chunked, resumable, checkpointed historical backfill with default chunk sizes of 100,000 recor…  | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-038 | Persist backfill checkpoints and recover deterministically: recovery resumes from the last committed che…  | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-039 | Reconcile real-time gaps through historical backfill where supported and configured: if overflow policy…   | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-040 | Enforce license metadata before any storage, scheduler export, or artifact generation: external/vendor d…  | DATA-UPG-034, DATA-UPG-060                                                                                     | storage.py; scheduler.py; source_license_manifest                    | Enforce license metadata before storage, scheduler export, artifacts, or backfill.                                                                     | test_license_enforcement.py                                      | Covered by supplemental task |
| DATA-FR-041 | Define the module's concurrency, rate-limiting, and observability model: use`asyncio` for real-time fee… | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-042 | Define the module's internal layering and persistence/feed-state scope: internal layers for contracts, r…  | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |
| DATA-FR-043 | Produce a central limits manifest (maximum records, date range, cache TTL, synthetic generation size, ba…  | DATA-UPG-052, DATA-UPG-054, DATA-UPG-056, DATA-UPG-057                                                         | README; examples/data_examples.py; limits manifest                   | Add central limits manifest, response examples, troubleshooting, examples, and production sign-off artifact.                                           | docs/examples checklist                                          | Covered by supplemental task |
| DATA-FR-044 | Write tests covering: backfill chunking, idempotency, source revision handling; automatic historical bac…  | DATA-UPG-014, DATA-UPG-022, DATA-UPG-034, DATA-UPG-035, DATA-UPG-036, DATA-UPG-037, DATA-UPG-038, DATA-UPG-039 | app/services/data/scheduler.py; storage.py; persistence.py; feeds.py | Preserve scheduler helpers, remove import-time recovery, add persisted lifecycle contracts, backfill checkpoints, idempotency, and gap reconciliation. | tests/services/data/test_scheduler.py; test_backfill_recovery.py | Covered                      |

### External Vendor Data Source Connectors

| Original ID | Requirement summary                                                                                         | Brownfield task(s)                                                                                             | Current code / artifact anchor                       | Migration action                                                                                                                                                        | Test / evidence target                                                 | Status                       |
| ----------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------- |
| DATA-FR-045 | Provide one internal broker/data gateway interface that routes a single internal request contract to man…  | DATA-UPG-003, DATA-UPG-009, DATA-UPG-030, DATA-UPG-031, DATA-UPG-032, DATA-UPG-033, DATA-UPG-059, DATA-UPG-060 | app/services/data/sources.py; app/services/brokers/* | Keep broker connectivity in brokers; formalize read-only source protocol, adapter readiness, license enforcement, source metadata, and deterministic provider failures. | tests/services/data/test_sources.py; test_broker_read_only_contract.py | Covered                      |
| DATA-FR-046 | Implement the common internal source adapter protocol: every adapter validates source-specific requireme…  | DATA-UPG-003, DATA-UPG-009, DATA-UPG-030, DATA-UPG-031, DATA-UPG-032, DATA-UPG-033, DATA-UPG-059, DATA-UPG-060 | app/services/data/sources.py; app/services/brokers/* | Keep broker connectivity in brokers; formalize read-only source protocol, adapter readiness, license enforcement, source metadata, and deterministic provider failures. | tests/services/data/test_sources.py; test_broker_read_only_contract.py | Covered                      |
| DATA-FR-047 | Keep broker-capable adapters strictly read-only in the data module: broker adapters never place trades,…   | DATA-UPG-003, DATA-UPG-009, DATA-UPG-030, DATA-UPG-031, DATA-UPG-032, DATA-UPG-033, DATA-UPG-059, DATA-UPG-060 | app/services/data/sources.py; app/services/brokers/* | Keep broker connectivity in brokers; formalize read-only source protocol, adapter readiness, license enforcement, source metadata, and deterministic provider failures. | tests/services/data/test_sources.py; test_broker_read_only_contract.py | Covered                      |
| DATA-FR-048 | Implement the MT5 adapter: initial source readiness`staging` until live credential, broker, timeout, an… | DATA-UPG-003, DATA-UPG-031, DATA-UPG-032, DATA-UPG-059, DATA-UPG-060                                           | sources.py; app/services/brokers/mt5.py              | Use existing broker-backed MT5 reads only; add readiness, redaction, metadata, UTC, and broker-unavailable tests.                                                       | test_mt5_adapter_contract.py                                           | Covered                      |
| DATA-FR-049 | Implement the cTrader adapter using the approved cTrader adapter/MCP boundary: initial source readiness…   | DATA-UPG-003, DATA-UPG-031, DATA-UPG-032, DATA-UPG-060                                                         | sources.py; app/services/brokers/ctrader.py          | Use existing cTrader broker boundary for reads only; add normalization, metadata, and client-boundary tests.                                                            | test_ctrader_adapter_contract.py                                       | Covered                      |
| DATA-FR-050 | Implement the Dukascopy adapter: initial source readiness`staging` until historical/live capability, ra… | DATA-UPG-030, DATA-UPG-031, DATA-UPG-032, DATA-UPG-060                                                         | sources.py; app/services/brokers/dukascopy.py        | Preserve adapter registry; represent Dukascopy capability/readiness, network handling, metadata, and deterministic errors.                                              | test_dukascopy_adapter_contract.py                                     | Covered                      |
| DATA-FR-051 | Implement Binance support as symbol-discovery only via`list_symbols(source="binance")`: initial source…  | DATA-UPG-033, DATA-UPG-060                                                                                     | sources.py; app/services/brokers/binance.py          | Keep Binance as symbol-discovery only in Data; never promote to execution/trading adapter.                                                                              | test_binance_symbol_discovery_only.py                                  | Covered                      |
| DATA-FR-052 | Normalize records consistently across all sources: OHLCV records normalize timestamp, open, high, low, c…  | DATA-UPG-003, DATA-UPG-009, DATA-UPG-030, DATA-UPG-031, DATA-UPG-032, DATA-UPG-033, DATA-UPG-059, DATA-UPG-060 | app/services/data/sources.py; app/services/brokers/* | Keep broker connectivity in brokers; formalize read-only source protocol, adapter readiness, license enforcement, source metadata, and deterministic provider failures. | tests/services/data/test_sources.py; test_broker_read_only_contract.py | Covered                      |
| DATA-FR-053 | Implement explicit, opt-in source fallback:`fallback_sources` is an explicit optional list on data retr… | DATA-UPG-003, DATA-UPG-009, DATA-UPG-030, DATA-UPG-031, DATA-UPG-032, DATA-UPG-033, DATA-UPG-059, DATA-UPG-060 | app/services/data/sources.py; app/services/brokers/* | Keep broker connectivity in brokers; formalize read-only source protocol, adapter readiness, license enforcement, source metadata, and deterministic provider failures. | tests/services/data/test_sources.py; test_broker_read_only_contract.py | Covered                      |
| DATA-FR-054 | Enforce resilience policy on every external source call: explicit timeouts, bounded retries, rate limits…  | DATA-UPG-003, DATA-UPG-009, DATA-UPG-030, DATA-UPG-031, DATA-UPG-032, DATA-UPG-033, DATA-UPG-059, DATA-UPG-060 | app/services/data/sources.py; app/services/brokers/* | Keep broker connectivity in brokers; formalize read-only source protocol, adapter readiness, license enforcement, source metadata, and deterministic provider failures. | tests/services/data/test_sources.py; test_broker_read_only_contract.py | Covered                      |
| DATA-FR-055 | Maintain and document a source readiness manifest and a source license manifest declaring readiness/lice…  | DATA-UPG-003, DATA-UPG-009, DATA-UPG-030, DATA-UPG-031, DATA-UPG-032, DATA-UPG-033, DATA-UPG-059, DATA-UPG-060 | app/services/data/sources.py; app/services/brokers/* | Keep broker connectivity in brokers; formalize read-only source protocol, adapter readiness, license enforcement, source metadata, and deterministic provider failures. | tests/services/data/test_sources.py; test_broker_read_only_contract.py | Covered                      |
| DATA-FR-056 | Never log or return credentials or secrets anywhere in the connector layer: passwords, access tokens, AP…  | DATA-UPG-018, DATA-UPG-019, DATA-UPG-024, DATA-UPG-025, DATA-UPG-059                                           | public_api.py; gateway.py; errors.py                 | Keep official tools thin and validate date range/limit while redacting all credential-like data.                                                                        | test_public_api.py; test_redaction.py                                  | Covered by supplemental task |
| DATA-FR-057 | Write data quality tests covering adversarial market conditions: zero-volume bars, extreme spread wideni…  | DATA-UPG-044, DATA-UPG-060, DATA-UPG-064                                                                       | validation.py; tests/services/data                   | Add adversarial quality fixtures and production license-enforcement tests.                                                                                              | test_quality_adversarial.py; test_license_enforcement.py               | Covered                      |
| DATA-FR-058 | Note that the HaruQuantAI Tool Function Standard, Code Quality Standard, Agent Standard, and Agentic AI…   | DATA-UPG-052, DATA-UPG-057, DATA-UPG-064                                                                       | README; DOMAIN.md                                    | Document external standards and safe deterministic behavior when adapters are disabled/unavailable.                                                                     | docs checklist; adapter unavailable tests                              | Covered by supplemental task |

### File Storage and Parquet I/O Helpers

| Original ID | Requirement summary                                                                                           | Brownfield task(s)                                                                 | Current code / artifact anchor           | Migration action                                                                                                            | Test / evidence target                      | Status                       |
| ----------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ---------------------------- |
| DATA-FR-059 | Support`save_market_data` and `load_local_dataset` as the official local storage tools, package path `a… | DATA-UPG-012, DATA-UPG-034, DATA-UPG-058                                           | storage.py; public_api.py                | Preserve save/load helpers and wrap them as official local-storage tools with validated requests.                           | test_local_storage.py                       | Covered                      |
| DATA-FR-060 | Enforce approved storage roots and path safety on every local file operation: approved storage roots con…    | DATA-UPG-058                                                                       | validation.py; storage.py                | Configure and enforce approved storage roots for every local operation.                                                     | test_path_safety.py                         | Covered by supplemental task |
| DATA-FR-061 | Require explicit`overwrite=True` to overwrite, returning `FILE_ALREADY_EXISTS` when an existing file is… | DATA-UPG-012, DATA-UPG-017, DATA-UPG-058                                           | storage.py; errors.py                    | Require explicit overwrite; map existing/missing files to deterministic errors.                                             | test_local_storage.py                       | Covered                      |
| DATA-FR-062 | Make storage writes crash-safe: write to a temp artifact then atomically commit/rename; quarantine parti…    | DATA-UPG-012, DATA-UPG-034, DATA-UPG-058                                           | storage.py                               | Use temp-write then atomic rename and quarantine failed partial artifacts.                                                  | test_atomic_storage.py                      | Covered                      |
| DATA-FR-063 | Implement the CSV source adapter: initial source readiness`production`; supports loading OHLCV records,…   | DATA-UPG-012, DATA-UPG-030, DATA-UPG-058, DATA-UPG-060                             | sources.py; storage.py; normalization.py | Harden existing CSV adapter with path safety, timestamp/timezone handling, alias mapping, filtering, and validation.        | test_csv_adapter.py                         | Covered                      |
| DATA-FR-064 | Implement the Parquet source adapter as the preferred local storage format for larger datasets: initial…     | DATA-UPG-012, DATA-UPG-030, DATA-UPG-058, DATA-UPG-060                             | sources.py; storage.py; normalization.py | Harden Parquet adapter as preferred large local format with metadata preservation and performance target.                   | test_parquet_adapter.py; performance test   | Covered                      |
| DATA-FR-065 | Implement metadata manifests and source-revision freshness for local datasets: storage writes include me…    | DATA-UPG-038, DATA-UPG-047, DATA-UPG-060, DATA-UPG-063                             | storage.py; persistence.py               | Add metadata manifests, source revision freshness, immutable local dataset policy, and redistribution restrictions.         | test_storage_metadata.py                    | Covered by supplemental task |
| DATA-FR-066 | Implement the source adapter protocol contract location and gateway routing for storage-backed sources:…     | DATA-UPG-003, DATA-UPG-009, DATA-UPG-030, DATA-UPG-031, DATA-UPG-033, DATA-UPG-064 | sources.py; app/services/brokers/*       | Formalize adapter protocol and gateway routing while preserving existing source names and small-file extraction discipline. | test_source_registry.py; sign-off checklist | Covered                      |
| DATA-FR-067 | Write storage tests covering valid save and load, unsupported extension rejection, and unsafe path rejec…    | DATA-UPG-012, DATA-UPG-058                                                         | storage.py; validation.py                | Add storage tests for valid save/load, unsupported extension, and unsafe path rejection.                                    | test_local_storage.py; test_path_safety.py  | Covered                      |

### Domain Exception Handling and Error Routing

| Original ID | Requirement summary                                                                                          | Brownfield task(s)                       | Current code / artifact anchor                 | Migration action                                                                                   | Test / evidence target                   | Status                       |
| ----------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------- | ---------------------------- |
| DATA-FR-068 | Import and reuse all standard system exceptions and error codes (`VALIDATION_FAILED`, `AUTHENTICATION_FA… | DATA-UPG-017, DATA-UPG-057               | errors.py; README                              | Reuse app.utils.errors taxonomy and document deterministic code reference.                         | test_error_mapping.py                    | Covered                      |
| DATA-FR-069 | Have every official tool handle errors deterministically through the standard envelope:`status` is `suc…  | DATA-UPG-017, DATA-UPG-018, DATA-UPG-019 | errors.py; public_api.py                       | Return standard success/error envelopes for every official tool with deterministic codes.          | test_standard_envelope.py                | Covered                      |
| DATA-FR-070 | Route input-validation failures consistently: any unsupported or invalid`workflow_context` returns `INV…  | DATA-UPG-017, DATA-UPG-024, DATA-UPG-044 | validation.py; errors.py                       | Route invalid workflow/input/bad-data cases consistently and never silently normalize unsafe data. | test_validation_errors.py                | Covered                      |
| DATA-FR-071 | Redact secret-like values from all errors and logs.                                                          | DATA-UPG-017, DATA-UPG-059               | errors.py; logging hooks                       | Redact secret-like values from logs and errors.                                                    | test_redaction.py                        | Covered by supplemental task |
| DATA-FR-072 | Write tests verifying deterministic error code mapping for every official tool, and write usage examples…   | DATA-UPG-017, DATA-UPG-054, DATA-UPG-064 | tests/services/data; examples/data_examples.py | Add deterministic error mapping tests and success/error usage examples.                            | test_error_mapping.py; example execution | Covered                      |

### Data Cache Layer and TTL Manager

| Original ID | Requirement summary                                                                                             | Brownfield task(s)                                                                               | Current code / artifact anchor               | Migration action                                                                                               | Test / evidence target                           | Status                       |
| ----------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------------- |
| DATA-FR-073 | Fix approved storage roots for Phase 1 to`data/raw/`, `data/processed/`, `data/cache/`, and `artifacts/… | DATA-UPG-028, DATA-UPG-056, DATA-UPG-058                                                         | storage.py; gateway.py; limits manifest      | Define approved cache roots and TTL defaults/max overrides by data kind/workflow.                              | test_cache_policy.py; docs checklist             | Covered by supplemental task |
| DATA-FR-074 | Build the cache to support key creation, reads, writes, stale detection, source revision detection, and…       | DATA-UPG-027, DATA-UPG-028, DATA-UPG-035, DATA-UPG-038                                           | gateway.py; storage.py                       | Build explicit cache key/read/write/stale/source-revision behavior around existing cache helpers.              | test_cache_policy.py                             | Covered                      |
| DATA-FR-075 | Invalidate cache entries automatically whenever`schema_version`, `normalization_version`, or `raw_data_…   | DATA-UPG-028, DATA-UPG-035, DATA-UPG-038                                                         | storage.py; persistence.py                   | Invalidate on schema/normalization/raw hash changes and expose source revision policy.                         | test_cache_invalidation.py                       | Covered                      |
| DATA-FR-076 | Govern stale cache behavior through the`stale_data_behavior` input parameter (never returning stale cac…     | DATA-UPG-028, DATA-UPG-024                                                                       | gateway.py; storage.py                       | Add stale_data_behavior defaults by workflow and never return stale cache silently.                            | test_stale_cache_behavior.py                     | Covered                      |
| DATA-FR-077 | Make cache failures non-corrupting: cache write/read errors never corrupt successful source fetches; if…       | DATA-UPG-017, DATA-UPG-028                                                                       | gateway.py; storage.py; errors.py            | Make cache failures non-corrupting and include warning metadata with propagated request_id.                    | test_cache_failure_non_corrupting.py             | Covered                      |
| DATA-FR-078 | Implement`clear_data_cache` defaulting to dry-run, validating namespace, source filter, symbol filter,…      | DATA-UPG-028, DATA-UPG-058                                                                       | storage.py; public_api.py                    | Make clear_data_cache dry-run by default and validate namespace/source/symbol/root before destructive actions. | test_clear_cache_dry_run.py                      | Covered                      |
| DATA-FR-079 | Map throttling to`RATE_LIMIT_EXCEEDED` on HTTP 429 or source throttling, forbidding immediate retry aft…     | DATA-UPG-017, DATA-UPG-028, DATA-UPG-043                                                         | gateway.py; sources.py; feeds.py             | Map throttling to RATE_LIMIT_EXCEEDED and avoid immediate retry/thundering herd.                               | test_rate_limit.py; test_reconnect_policy.py     | Covered                      |
| DATA-FR-080 | Keep all behavior deterministic, documented, and auditable: data validation, normalization, quality scor…      | DATA-UPG-017, DATA-UPG-027, DATA-UPG-028, DATA-UPG-036, DATA-UPG-047, DATA-UPG-052, DATA-UPG-057 | gateway.py; storage.py; scheduler.py; README | Document and audit validation, normalization, quality, timestamps, cache, metadata, migrations, and recovery.  | logging/audit tests; docs checklist              | Covered                      |
| DATA-FR-081 | Write tests verifying cache hit, miss, stale, and invalidation behavior for every official tool where ap…      | DATA-UPG-028, DATA-UPG-035, DATA-UPG-038, DATA-UPG-064                                           | tests/services/data                          | Add cache hit/miss/stale/invalidation tests for official tools where applicable.                               | test_cache_policy.py; test_cache_invalidation.py | Covered                      |

### Data Domain Models and Primitives

| Original ID | Requirement summary                                                                                               | Brownfield task(s)                                     | Current code / artifact anchor                | Migration action                                                                                                           | Test / evidence target                             | Status                                   |
| ----------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------- |
| DATA-FR-082 | Rebuild the data module as a clean, contract-driven, agent-safe, testable, maintainable domain under `ap…        | DATA-UPG-001, DATA-UPG-004, DATA-UPG-016, DATA-UPG-020 | app/services/data/*                           | Reinterpret rebuild mandate as brownfield clean-up: contract-driven wrappers and extraction without deleting current code. | characterization + contract tests                  | Covered with brownfield reinterpretation |
| DATA-FR-083 | Implement`get_market_data`, `get_tick_data`, `get_spread_data`, and `get_historical_volume`, plus `get_… | DATA-UPG-016, DATA-UPG-027, DATA-UPG-047, DATA-UPG-062 | models.py; contracts.py; normalization.py     | Align data contracts/metadata with downstream workflows and canonical market-data expectations.                            | test_contract_alignment.py                         | Covered                                  |
| DATA-FR-084 | Return the standard HaruQuantAI response schema from every official AI tool: status, message, data, erro…        | DATA-UPG-018, DATA-UPG-019                             | public_api.py                                 | Return standard HaruQuantAI envelopes and metadata for every official AI tool.                                             | test_standard_envelope.py                          | Covered                                  |
| DATA-FR-085 | Ensure all market data crossing the official AI-tool boundary is JSON-serializable and contract-complian…        | DATA-UPG-026, DATA-UPG-044, DATA-UPG-050, DATA-UPG-056 | gateway.py; validation.py; transforms.py      | Support OHLCV/tick/spread/volume behavior, defaults, limits, spread query, and performance target.                         | test_data_kinds.py; performance test               | Covered                                  |
| DATA-FR-086 | Validate asset-specific and tick-specific data integrity: missing required asset-specific metadata retur…        | DATA-UPG-044, DATA-UPG-046, DATA-UPG-062               | validation.py; models.py; contracts.py        | Add asset/tick integrity validation and asset-specific metadata handling.                                                  | test_quality_validation.py; test_asset_metadata.py | Covered                                  |
| DATA-FR-087 | Detect data quality issues before records leave validation: duplicate timestamps, out-of-order records,…         | DATA-UPG-044, DATA-UPG-050                             | validation.py; normalization.py               | Detect duplicate/out-of-order/missing/stale/partial/OHLC/spread/volume/tick issues before boundary.                        | test_quality_validation.py; performance test       | Covered                                  |
| DATA-FR-088 | Enforce workflow-aware precision and numeric serialization policy, disclosed in metadata: numeric output…        | DATA-UPG-024, DATA-UPG-046, DATA-UPG-062               | validation.py; normalization.py; contracts.py | Add workflow-aware precision/serialization/quantization and fail-closed precision mismatch behavior.                       | test_precision_policy.py                           | Covered                                  |
| DATA-FR-089 | Enforce schema evolution rules: schema evolution requires backward compatibility or explicit invalidatio…        | DATA-UPG-017, DATA-UPG-036, DATA-UPG-038, DATA-UPG-063 | errors.py; storage.py; contracts.py           | Define schema evolution/drift/invalidation policy and DATA_SCHEMA_DRIFT behavior.                                          | test_schema_drift.py                               | Covered by supplemental task             |
| DATA-FR-090 | Apply default`spread_policy` of `average`, reject invalid or unsorted ticks during aggregation unless r…     | DATA-UPG-048, DATA-UPG-051                             | transforms.py                                 | Default spread_policy=average; validate tick order; add labeling metadata.                                                 | test_transforms.py                                 | Covered                                  |
| DATA-FR-091 | Disclose`historical_hours_supported=false` and return `UNSUPPORTED_OPERATION` for historical market-hou…     | DATA-UPG-061                                           | validation.py; README                         | Disclose historical_hours_supported=false and return UNSUPPORTED_OPERATION for historical reconstruction.                  | test_market_hours.py                               | Covered by supplemental task             |
| DATA-FR-092 | Write tests verifying downstream contract alignment for strategy, simulation, optimization, analytics, r…        | DATA-UPG-062, DATA-UPG-064                             | tests/services/data; golden fixtures          | Add downstream contract alignment tests across all consumers.                                                              | test_contract_alignment.py                         | Covered by supplemental task             |

### Synthetic and Backtest Mock Data Adapters

| Original ID | Requirement summary                                                                                           | Brownfield task(s)                       | Current code / artifact anchor | Migration action                                                                                              | Test / evidence target                         | Status                       |
| ----------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------- |
| DATA-FR-093 | Adopt a conservative source-readiness posture across sources: local and synthetic sources may be `produc…    | DATA-UPG-033, DATA-UPG-060               | sources.py; readiness manifest | Keep local/synthetic production-ready if tests pass; external/broker sources staging until validation passes. | test_source_readiness.py                       | Covered by supplemental task |
| DATA-FR-094 | Implement`generate_synthetic_ticks` and `generate_synthetic_bars` as dedicated official synthetic-gener… | DATA-UPG-019, DATA-UPG-049, DATA-UPG-056 | transforms.py; public_api.py   | Expose dedicated synthetic-generation wrappers with GBM Phase 1, seeds, and bounded response policy.          | test_synthetic_generation.py                   | Covered                      |
| DATA-FR-095 | Make synthetic generation deterministic when a seed is supplied, bounded by direct-response limits of 10…    | DATA-UPG-049, DATA-UPG-050, DATA-UPG-056 | transforms.py; limits manifest | Make seeded generation deterministic and enforce synthetic record limits/performance target.                  | test_synthetic_generation.py; performance test | Covered                      |

### Market Data Transformation and Resampling Utilities

| Original ID | Requirement summary                                                                                             | Brownfield task(s)                                     | Current code / artifact anchor              | Migration action                                                                          | Test / evidence target                   | Status                       |
| ----------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------------------- | ---------------------------- |
| DATA-FR-096 | Normalize timezone handling across OHLCV, tick, spread, metadata, sessions, availability, and volume out…      | DATA-UPG-027, DATA-UPG-029, DATA-UPG-047, DATA-UPG-061 | normalization.py; gateway.py; validation.py | Normalize UTC official boundary and preserve broker/source timezone and metadata.         | test_utc_boundary.py; test_metadata.py   | Covered                      |
| DATA-FR-097 | Implement`get_trading_sessions` and `get_market_hours` for Phase 1 with current configured hours only,…    | DATA-UPG-019, DATA-UPG-061                             | validation.py; public_api.py                | Implement current configured hours and sessions only; defer historical calendar provider. | test_market_hours.py                     | Covered by supplemental task |
| DATA-FR-098 | Implement`resample_ohlcv`, `align_multitimeframe_data`, and `aggregate_ticks_to_bars` with lookahead-le… | DATA-UPG-048, DATA-UPG-050, DATA-UPG-051               | transforms.py                               | Harden resampling, no-lookahead alignment, and tick aggregation defaults.                 | test_transforms.py; test_no_lookahead.py | Covered                      |
| DATA-FR-099 | Implement`label_market_data` for deterministic historical labeling that never claims predictive value:…      | DATA-UPG-048, DATA-UPG-051                             | transforms.py                               | Keep labeling deterministic and horizon-bounded without predictive claims.                | test_labels.py                           | Covered                      |

### Input Parameter Validation Helpers

| Original ID | Requirement summary                                                                                         | Brownfield task(s)                                     | Current code / artifact anchor             | Migration action                                                                                                     | Test / evidence target                                  | Status                       |
| ----------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------- |
| DATA-FR-100 | Validate every official tool's inputs and run data quality validation after normalization and before ret…  | DATA-UPG-024, DATA-UPG-025, DATA-UPG-044, DATA-UPG-058 | validation.py; gateway.py                  | Validate official inputs and run quality validation after normalization without silent repairs for strict workflows. | test_validation.py; test_quality_validation.py          | Covered                      |
| DATA-FR-101 | Bound and protect response payloads: direct official-tool responses use safe default limits to avoid lar…  | DATA-UPG-027, DATA-UPG-056                             | gateway.py; public_api.py; limits manifest | Bound official responses and use references/chunking/generator patterns for oversized payloads.                      | test_payload_limits.py                                  | Covered by supplemental task |
| DATA-FR-102 | Map validation/throttling failures to deterministic codes:`DATA_QUALITY_FAILED` for data-content valida… | DATA-UPG-017, DATA-UPG-028, DATA-UPG-044               | errors.py; gateway.py; validation.py       | Map quality/limit/rate failures to deterministic codes and prevent duplicate committed chunks.                       | test_error_mapping.py; test_duplicate_ingestion.py      | Covered                      |
| DATA-FR-103 | Write tests covering: duplicate ingestion no-op behavior; quality failure for every official tool; dupli…  | DATA-UPG-035, DATA-UPG-044, DATA-UPG-064               | tests/services/data                        | Add duplicate, gap, quality, stale, partial, and production timestamp tests.                                         | test_quality_validation.py; test_duplicate_ingestion.py | Covered                      |

### Persistence, lineage, calendars, and provider contracts

| Original ID   | Requirement summary                                                                                          | Brownfield task(s)                                                   | Current code / artifact anchor               | Migration action                                                                                                    | Test / evidence target                           | Status                       |
| ------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------------- |
| DATA-NFR-001  | Adopt the Phase 1.5 canonical market data contracts instead of defining duplicate Bar, Tick, Symbol, Tim…   | DATA-UPG-016, DATA-UPG-062                                           | contracts.py; models.py                      | Adopt canonical market-data contracts and avoid duplicate domain model drift.                                       | test_contract_alignment.py                       | Covered by supplemental task |
| DATA-NFR-002  | Define database migration ownership, migration naming, forward migration, rollback expectation, and sche…   | DATA-UPG-036, DATA-UPG-063                                           | storage.py; persistence.py; docs             | Document migration ownership, naming, forward/rollback expectations, and schema version recording.                  | test_migrations.py; docs checklist               | Covered by supplemental task |
| DATA-NFR-003  | Implement data lineage metadata for provider, provider request ID, retrieved timestamp, normalized times…   | DATA-UPG-038, DATA-UPG-047                                           | normalization.py; storage.py; persistence.py | Implement lineage metadata: provider/request/retrieved/normalized/raw hash/transformation hash/quality reference.   | test_lineage_metadata.py                         | Covered                      |
| DATA-NFR-004  | Define raw provider payload retention rules separately from canonical normalized market-data retention r…   | DATA-UPG-063                                                         | README; storage.py                           | Separate raw provider payload retention from normalized canonical retention.                                        | docs checklist; retention policy test            | Covered by supplemental task |
| DATA-NFR-005  | Define symbol master ownership for canonical symbols, broker symbols, precision, lot size, tick size, as…   | DATA-UPG-030, DATA-UPG-046, DATA-UPG-060, DATA-UPG-062               | sources.py; models.py; readiness manifest    | Define symbol master ownership for canonical/broker symbols, precision, lot/tick sizes, sessions, and availability. | test_symbol_metadata.py                          | Covered by supplemental task |
| DATA-NFR-006  | Define market/session calendar ownership and how Data distinguishes expected session gaps from unexpecte…   | DATA-UPG-061                                                         | README; validation.py                        | Define calendar ownership and expected vs unexpected gaps.                                                          | test_market_hours.py; docs checklist             | Covered by supplemental task |
| DATA-NFR-007  | Define backup and restore policy for historical data, cache data, normalized datasets, data-quality repo…   | DATA-UPG-063                                                         | README; persistence docs                     | Define backup/restore for historical/cache/normalized/quality/provider metadata.                                    | docs checklist                                   | Covered by supplemental task |
| DATA-NFR-008  | Create golden dataset fixtures used by Data, Indicators, Strategies, Simulation, Analytics, Optimization…   | DATA-UPG-062                                                         | tests/fixtures/data/golden/*                 | Create golden dataset fixtures for cross-module regression tests.                                                   | fixture validation tests                         | Covered by supplemental task |
| DATA-NFR-009  | Implement a canonical`MarketDataProvider` interface boundary for MT5, cTrader, Binance, file, database,…  | DATA-UPG-009, DATA-UPG-030                                           | contracts.py; sources.py                     | Implement canonical MarketDataProvider/BrokerMarketDataPort interface for all sources.                              | test_source_protocol.py                          | Covered                      |
| DATA-NFR-010  | Ensure provider adapters return canonical contracts and never leak raw provider SDK objects across the s…   | DATA-UPG-027, DATA-UPG-030, DATA-UPG-031                             | sources.py; normalization.py; public_api.py  | Ensure adapters return canonical contracts and never leak raw SDK objects.                                          | test_no_raw_object_leakage.py                    | Covered                      |
| DATA-TEST-001 | Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, an…   | DATA-UPG-055, DATA-UPG-064                                           | tests/services/data/*                        | Use this matrix to ensure normal/edge/invalid/fail-closed/logging/schema/regression tests exist per requirement.    | coverage matrix + pytest                         | Covered by supplemental task |
| DATA-TEST-002 | Preserve the project gate of at least 80% coverage for each affected file and package.                       | DATA-UPG-064                                                         | CI; coverage config                          | Preserve >80% coverage per affected file/package.                                                                   | coverage report                                  | Covered by supplemental task |
| DATA-TEST-003 | Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.             | DATA-UPG-017, DATA-UPG-018, DATA-UPG-019, DATA-UPG-020, DATA-UPG-064 | public_api.py;__init__.py; errors.py   | Verify envelopes, deterministic errors, import behavior, and ownership boundaries.                                  | test_standard_envelope.py; test_import_safety.py | Covered                      |
| DATA-EX-001   | `example_01_metadata_and_discovery`: Demonstrate symbol discovery, source capabilities, metadata lookup,… | DATA-UPG-054                                                         | examples/data_examples.py                    | Add metadata/discovery example.                                                                                     | example_01_metadata_and_discovery                | Covered                      |
| DATA-EX-002   | `example_02_historical_data_retrieval`: Demonstrate OHLCV retrieval across approved sources with standar… | DATA-UPG-054                                                         | examples/data_examples.py                    | Add historical retrieval example with unavailable-provider handling.                                                | example_02_historical_data_retrieval             | Covered                      |
| DATA-EX-003   | `example_03_local_file_sources`: Demonstrate CSV and Parquet loading through safe paths and normalized c… | DATA-UPG-054, DATA-UPG-058                                           | examples/data_examples.py                    | Add local CSV/Parquet safe path example.                                                                            | example_03_local_file_sources                    | Covered                      |
| DATA-EX-004   | `example_04_synthetic_generation`: Demonstrate reproducible synthetic bars and ticks with seeds and sour… | DATA-UPG-054                                                         | examples/data_examples.py                    | Add reproducible synthetic bars/ticks example.                                                                      | example_04_synthetic_generation                  | Covered                      |
| DATA-EX-005   | `example_05_timeframes_sessions_and_market_hours`: Demonstrate timeframe parsing, market-hour lookup, tr… | DATA-UPG-054, DATA-UPG-061                                           | examples/data_examples.py                    | Add timeframes, sessions, market-hours, UTC example.                                                                | example_05_timeframes_sessions_and_market_hours  | Covered                      |
| DATA-EX-006   | `example_06_transformations_and_alignment`: Demonstrate resampling, tick aggregation, labeling, and look… | DATA-UPG-054                                                         | examples/data_examples.py                    | Add transforms/alignment/labeling example.                                                                          | example_06_transformations_and_alignment         | Covered                      |
| DATA-EX-007   | `example_07_cache_and_storage`: Demonstrate cache hits/misses, TTL behavior, manifests, and scoped cache… | DATA-UPG-054                                                         | examples/data_examples.py                    | Add cache/storage TTL/manifests example.                                                                            | example_07_cache_and_storage                     | Covered                      |
| DATA-EX-008   | `example_08_scheduler_jobs`: Demonstrate update-job creation, status inspection, start/stop behavior, ch… | DATA-UPG-054                                                         | examples/data_examples.py                    | Add scheduler jobs/checkpoint/recovery example.                                                                     | example_08_scheduler_jobs                        | Covered                      |
| DATA-EX-009   | `example_09_feed_status_and_readiness`: Demonstrate feed heartbeat, gap/staleness status, readiness meta… | DATA-UPG-054                                                         | examples/data_examples.py                    | Add feed status/readiness example.                                                                                  | example_09_feed_status_and_readiness             | Covered                      |
| DATA-EX-010   | The single usage file must be runnable as a script and organize separate examples as focused functions.      | DATA-UPG-054                                                         | examples/data_examples.py                    | Keep single script with focused example functions.                                                                  | example script execution                         | Covered                      |
| DATA-EX-011   | Examples must extensively cover the phase's official public capabilities, important edge cases, fail-clo…   | DATA-UPG-054                                                         | examples/data_examples.py                    | Cover public capabilities, edge cases, fail-closed paths, and envelope fields.                                      | example execution + docs review                  | Covered                      |
| DATA-EX-012   | Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redact…   | DATA-UPG-017, DATA-UPG-019, DATA-UPG-059                             | gateway.py; public_api.py; logging tests     | Log calls/failures/success/governed decisions with redacted metadata.                                               | test_logging_redaction.py                        | Covered by supplemental task |
| DATA-EX-013   | All Python modules and public functions/classes must have appropriate file-level and Google-style docstr…   | DATA-UPG-064                                                         | all Python modules                           | Require file-level and Google-style public function/class docstrings.                                               | ruff/pydocstyle-equivalent review                | Covered by supplemental task |
| DATA-EX-014   | Implement unit tests for all modules and verify coverage is at least 80%.                                    | DATA-UPG-064                                                         | tests/services/data/*                        | Implement unit tests for all touched modules and verify >=80% coverage.                                             | coverage report                                  | Covered by supplemental task |
| DATA-EX-015   | The implementation must pass all CI quality gates (Ruff format, Ruff check, mypy --strict, pytest, and c…   | DATA-UPG-064                                                         | CI                                           | Pass Ruff format/check, mypy strict where configured, pytest, and coverage gates.                                   | CI quality gates                                 | Covered by supplemental task |
| DATA-EX-016   | Update module README and active documentation for any architecture or API changes.                           | DATA-UPG-052, DATA-UPG-057                                           | README; DOMAIN.md; changelog                 | Update README and active docs for API/architecture changes.                                                         | docs checklist                                   | Covered by supplemental task |
| DATA-BR-001   | Done criterion: All 701 checkbox tasks are implemented or explicitly deferred with a documented reason.      | DATA-UPG-055, DATA-UPG-057, DATA-UPG-064                             | coverage matrix; implementation report       | Mark all 701 tasks implemented or explicitly deferred with reasons.                                                 | release checklist                                | Covered by supplemental task |
| DATA-BR-002   | Done criterion: Scope stayed within this phase and approved dependency surfaces.                             | DATA-UPG-001, DATA-UPG-003, DATA-UPG-004                             | implementation report                        | Keep scope inside Data phase and approved broker/data boundaries.                                                   | review checklist                                 | Covered                      |
| DATA-BR-003   | Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.          | DATA-UPG-006, DATA-UPG-007, DATA-UPG-008, DATA-UPG-020               | __init__.py; public_api.py             | Ensure public exports match registry rules and avoid unapproved helper exposure.                                    | test_public_exports.py                           | Covered                      |
| DATA-BR-004   | Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are…   | DATA-UPG-017, DATA-UPG-018, DATA-UPG-019, DATA-UPG-059               | public_api.py; errors.py; logging            | Satisfy envelopes, metadata, request IDs, error codes, logging, and redaction.                                      | test_standard_envelope.py; test_redaction.py     | Covered                      |
| DATA-BR-005   | Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.     | DATA-UPG-054, DATA-UPG-064                                           | tests; examples; CI                          | Pass unit tests, examples, typing, linting, formatting, and coverage.                                               | CI quality gates                                 | Covered by supplemental task |
| DATA-BR-006   | Done criterion: Active docs and changelog are updated for any implemented project meaning changes.           | DATA-UPG-052, DATA-UPG-057                                           | README; DOMAIN.md; changelog                 | Update active docs and changelog for project-meaning changes.                                                       | docs checklist                                   | Covered by supplemental task |
| DATA-BR-007   | Done criterion: Rollback path and implementation report are recorded before handoff.                         | DATA-UPG-057, DATA-UPG-064                                           | implementation report; rollback notes        | Record rollback path and implementation report before handoff.                                                      | handoff checklist                                | Covered by supplemental task |
