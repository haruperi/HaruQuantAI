# Data — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** Data
* **Repository:** `haruperi/HaruQuant`
* **Audited ref:** `main`
* **Audited commit:** `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Package path:** `app/services/data`
* **Tests path requested:** `ttests/unit/app/services/data`
* **Tests path found:** `tests/unit/app/services/data`
* **Known usage path:** `tests/usage/app/services/02_data.py`
* **Package root:** `app/services/data`
* **Module folders:** No child Python package folders were found; the domain is a flat package.
* **Python files inspected:**
  * `app/services/data/__init__.py`
  * `app/services/data/_common.py`
  * `app/services/data/calendar.py`
  * `app/services/data/csv.py`
  * `app/services/data/frames.py`
  * `app/services/data/gateway.py`
  * `app/services/data/generators.py`
  * `app/services/data/labeling.py`
  * `app/services/data/licensing.py`
  * `app/services/data/models.py`
  * `app/services/data/parquet.py`
  * `app/services/data/responses.py`
  * `app/services/data/scheduler.py`
  * `app/services/data/storage.py`
  * `app/services/data/transforms.py`
  * `app/services/data/validation.py`
* **Documentation inspected:** `app/services/data/README.md`, `docs/haruquant/plans/retire_data_common_plan.md`, and relevant upgrade-plan/search results.
* **Related production packages searched:**
  * `app/services/brokers`
  * `app/services/indicator`
  * `app/services/optimization`
  * `app/services/research`
  * `app/services/risk`
  * `app/services/simulation`
  * `app/services/utils`
* **Tests and examples searched:**
  * `tests/unit/app/services/data/*`
  * `tests/usage/app/services/02_data.py`
  * `tests/usage/app/services/data.py`
  * related indicator, strategy, and simulation usage files
  * `scripts/benchmarks/ticks_generation.py`
  * relevant scripts under `scripts/examples`
* **Registration mechanisms checked:**
  * `app.services.data.__all__`
  * `standardize_domain_exports(...)`
  * `standardize_tool_callable(...)`
  * `ADAPTER_REGISTRY`
  * `service_modules(...)`
  * `resolve_service_attr(...)`
  * import-time SQLite initialization/recovery
* **Audit limitations:**
  * This is a static audit of the repository snapshot above.
  * Tests were inspected but not executed because a complete local checkout and provider runtime were not available.
  * Live MT5, cTrader, Dukascopy, Binance, Yahoo, and CCXT behavior could not be exercised.
  * Dynamic use from external applications outside this repository cannot be ruled out.
  * GitHub code search can miss runtime-generated names, values assembled entirely from configuration, or consumers outside the indexed repository.

### Metric methodology

The public-symbol metric uses the package facade's declared `app.services.data.__all__`. The caller percentage counts facade symbols with confirmed non-test consumers outside the data package. Internal calls, tests, examples, and scripts are reported separately in the caller map.

## 2. Executive Summary

The Version 1 data domain currently provides five substantial groups of behavior:

1. A multi-source historical/tick/spread gateway with licensing, rate limiting, provider adapters, normalization, SQLite caching, and DataFrame output.
2. Local CSV/Parquet loading and persistence, including tool-style response envelopes.
3. Market-data transformation, synthetic generation, tick reconstruction, aggregation, alignment, and labeling.
4. Canonical Pydantic record models, timeframe/limit validation, and a lightweight `Data` DataFrame wrapper.
5. SQLite-backed scheduler/feed state management.

The most credible working runtime workflow is simulation tick preparation. `app/services/simulation/data_preparation.py` directly imports `TicksGenerator`, the four tick-model constants, and `load_parquet`. Research code directly uses `TimeframeManager`, while indicators, optimization, and shared utilities use `Data`. The gateway itself is substantial and exercised by unit/usage code, but no confirmed production service entry point was found calling package-level `get_data`; broker-backed execution remains unverified.

The package facade is internally inconsistent. `app/services/data/__init__.py` declares 99 exports, but 14 names are never bound. The function called to standardize or inject those names, `standardize_domain_exports`, is a logging-only placeholder. The README and initializer still refer to a missing `market_tools.py`. A current unit test expects an entirely different 32-name API and includes `generate_ticks_frame`, which is absent from the current initializer. This is confirmed API drift, not merely documentation drift.

The scheduler persists definitions and status transitions but does not fetch, transform, or save market data. Its worker loop updates status and sleeps. Feed management registers mock/in-memory state and handles overflow counters, but no live provider subscription or heartbeat loop was found. These workflows are partial.

The legacy `_common.py` remains a large duplicate implementation containing old cache, response, gateway-tool, frame, and file-persistence behavior. Direct static imports into it were not found, but dynamic service discovery means complete non-use cannot be proved.

**Audit metrics:** Module folders: 1 | Files: 16 | Public symbols: 99 declared package exports (85 bound, 14 unbound) | Symbols with confirmed callers: 13 (13.1% external production/runtime) | Workflows found: 9

**Evidence trustworthiness:** High for package structure, symbol definitions, static imports, direct call sites, facade defects, and scheduler behavior. Medium for broker operational status and dynamic/external use because those require runtime/provider access.

## 3. Actual Package Structure

```text
app.services.data
├── __init__.py
│   ├── Declares 99 package exports
│   ├── Binds 85 names
│   ├── Lists 14 names that are not bound
│   └── Calls standardize_domain_exports(...), currently a no-op placeholder
│
├── _common.py
│   ├── Data
│   │   ├── df
│   │   ├── symbol
│   │   ├── timeframe
│   │   └── close
│   ├── data_cache_get_path()
│   ├── data_cache_make_key()
│   ├── data_cache_get()
│   ├── data_cache_set()
│   ├── data_cache_clear()
│   ├── get_ohlcv_data()
│   ├── get_spread_data()
│   ├── get_symbol_metadata()
│   ├── get_trading_sessions()
│   ├── get_market_hours()
│   ├── get_historical_volume()
│   ├── resample_ohlcv()
│   ├── align_multitimeframe_data()
│   ├── get_tick_data()
│   ├── get_data_availability()
│   ├── binance_data_list_symbols()
│   └── data_df()
│
├── calendar.py
│   ├── Session-hour constants
│   ├── get_market_hours()
│   └── get_trading_sessions()
│
├── csv.py
│   ├── CSVDataSource
│   │   └── fetch_data()
│   ├── load_csv()
│   ├── clear_data_cache()
│   ├── get_cached_data()
│   ├── csv_data_fetch_range()
│   ├── csv_data_load()
│   ├── csv_data_saver_file_exists()
│   ├── csv_data_saver_save()
│   └── csv_data_saver_load()
│
├── frames.py
│   ├── Data
│   │   ├── df
│   │   ├── symbol
│   │   ├── timeframe
│   │   ├── close
│   │   └── __getattr__()
│   └── data_df()
│
├── gateway.py
│   ├── SourceAdapterProtocol
│   │   ├── is_ready()
│   │   ├── get_market_data()
│   │   ├── get_tick_data()
│   │   ├── list_symbols()
│   │   └── get_symbol_metadata()
│   ├── TokenBucketLimiter
│   │   └── consume()
│   ├── CSVAdapter
│   ├── ParquetAdapter
│   ├── SyntheticAdapter
│   ├── CCXTAdapter
│   ├── BrokerAdapter
│   ├── RATE_LIMITERS
│   ├── ADAPTER_REGISTRY
│   ├── check_rate_limit()
│   ├── get_circuit_breaker()
│   ├── update_circuit_breaker()
│   ├── check_circuit_breaker_barrier()
│   ├── normalize_file_records()
│   ├── get_source_adapter()
│   ├── execute_gateway_request()
│   ├── execute_gateway_dataframe_request()
│   ├── execute_gateway_tick_dataframe_request()
│   ├── get_data()
│   ├── get_symbol_metadata()
│   ├── list_symbols()
│   └── get_data_availability()
│
├── generators.py
│   ├── TICK_MODEL_REAL
│   ├── TICK_MODEL_GENERATED
│   ├── TICK_MODEL_TRADING_BAR
│   ├── TICK_MODEL_OHLC_M1
│   ├── SUPPORTED_MODELS
│   ├── SPREAD_NATIVE
│   ├── SPREAD_FIXED
│   ├── SPREAD_VARIABLE
│   ├── SUPPORTED_SPREAD_MODELS
│   ├── TicksGenerator
│   │   └── generate()
│   ├── generate_ticks()
│   └── generate_ticks_to_parquet()
│
├── labeling.py
│   └── labeler_lexlb()
│
├── licensing.py
│   ├── register_license()
│   └── validate_license()
│
├── models.py
│   ├── validate_utc_timestamp_helper()
│   ├── OHLCVRecord
│   ├── TickRecord
│   ├── SpreadRecord
│   ├── SymbolMetadata
│   └── DataAvailability
│
├── parquet.py
│   ├── get_data_dir()
│   ├── load_parquet()
│   ├── parquet_data_load()
│   ├── parquet_data_saver_file_exists()
│   ├── parquet_data_saver_save()
│   └── parquet_data_saver_load()
│
├── responses.py
│   └── Private tool-response helpers only
│
├── scheduler.py
│   ├── ACTIVE_JOB_TASKS
│   ├── ACTIVE_FEEDS
│   ├── BACKGROUND_TASKS
│   ├── recover_crashed_jobs()
│   ├── create_data_update_job()
│   ├── start_data_update_job()
│   ├── stop_data_update_job()
│   ├── run_data_update_job_once()
│   ├── get_data_update_job_status()
│   ├── register_mock_feed()
│   ├── handle_feed_overflow()
│   └── get_feed_status()
│
├── storage.py
│   ├── Bar
│   ├── DatabaseHelper
│   │   ├── get_connection()
│   │   └── init_database()
│   ├── APPROVED_STORAGE_ROOTS
│   ├── QUARANTINE_DIR
│   ├── DB_FILE_PATH
│   ├── validate_storage_path()
│   ├── generate_cache_key()
│   ├── get_cached_data()
│   ├── set_cached_data()
│   ├── clear_data_cache()
│   ├── save_market_data()
│   ├── load_local_dataset()
│   └── load_ohlcv_csv()
│
├── transforms.py
│   ├── TimeframeManager
│   │   ├── timeframe_to_frequency()
│   │   ├── validate_timeframe()
│   │   ├── can_resample()
│   │   ├── resample()
│   │   └── resample_multi_timeframe()
│   ├── BarAggregator
│   │   ├── add_tick()
│   │   ├── add_bar()
│   │   ├── get_current_bar()
│   │   ├── get_completed_bars()
│   │   └── flush()
│   ├── timeframe_to_pandas_freq()
│   ├── timeframe_to_minutes()
│   ├── resample_ohlcv()
│   ├── align_multitimeframe_data()
│   ├── aggregate_ticks_to_bars()
│   ├── generate_synthetic_ticks()
│   ├── generate_synthetic_bars()
│   └── label_market_data()
│
└── validation.py
    ├── BarProtocol
    ├── Limit/timeframe/cache constants
    ├── validate_limit()
    ├── normalize_numeric()
    ├── validate_step_alignment()
    ├── validate_timeframe()
    ├── validate_timezone()
    └── validate_bars()
```

### Package facade defects

The following names are declared in `app.services.data.__all__` but are not assigned in `app/services/data/__init__.py`:

```text
binance_data_list_symbols
data_cache_clear
data_cache_get
data_cache_get_path
data_cache_make_key
data_cache_set
data_df
get_historical_volume
get_market_hours
get_ohlcv_data
get_spread_data
get_tick_data
get_trading_sessions
resample_ohlcv
```

`standardize_domain_exports(globals(), __all__, tool_category="data")` does not repair this. Its implementation in `app/services/utils/standard.py` only logs that standardization was invoked.

## 4. Module and File Inventory

Files are ordered approximately from foundational contracts toward orchestrators and facades.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| data | `models.py` | Canonical record and metadata validation | `OHLCVRecord`, `TickRecord`, `SpreadRecord`, `SymbolMetadata`, `DataAvailability` | Standard library; Pydantic; utils logger | Used internally by gateway | Supporting |
| data | `validation.py` | Limits, timeframe, timezone, numeric and bar validation | validation functions, `BarProtocol` | Standard library; utils errors/logger | Used internally; `TimeframeManager` overlaps | Supporting |
| data | `frames.py` | DataFrame wrapper and tool-payload conversion | `Data`, `data_df` | Standard library; pandas; utils logger | `Data` used cross-domain; `data_df` not package-bound | Essential / Questionable |
| data | `responses.py` | Standard tool response construction | private `_data_tool_*` helpers | Standard library; utils errors/standard | Used by CSV/Parquet/labeling | Supporting |
| data | `csv.py` | Direct CSV source, in-memory cache, and tool wrappers | `CSVDataSource`, CSV tools | Standard library; pandas; frames/responses/utils | Examples/tests; direct utility | Useful |
| data | `parquet.py` | Direct Parquet loading and tool wrappers | Parquet tools, `load_parquet` | Standard library; pandas; frames/responses/utils | `load_parquet` used by simulation | Essential |
| data | `storage.py` | SQLite schema/cache and approved-root local file I/O | `DatabaseHelper`, cache and dataset functions | Standard library; pandas; SQLite; utils errors/logger/paths | Core internal gateway dependency | Essential |
| data | `licensing.py` | Source/symbol license registry and workflow restrictions | `register_license`, `validate_license` | Standard library; SQLite via storage; utils errors/logger | Used by gateway/scheduler | Supporting |
| data | `calendar.py` | Static FX market hours/session windows | `get_market_hours`, `get_trading_sessions` | Standard library; utils logger | Example/test only; package binding broken | Questionable |
| data | `transforms.py` | Resampling, alignment, aggregation, synthetic records, historical labels | `TimeframeManager`, `BarAggregator`, transform functions | Standard library; NumPy; pandas; validation/utils | `TimeframeManager` used by research; others mainly tests/examples | Useful |
| data | `generators.py` | Signal-aware tick reconstruction for simulation/backtests | tick constants, `TicksGenerator`, `generate_ticks`, Parquet export | Standard library; NumPy; pandas; PyArrow; utils errors/logger | `TicksGenerator` used by simulation/optimization | Essential |
| data | `labeling.py` | Local-extrema label tool envelope | `labeler_lexlb` | Standard library; NumPy/pandas; responses/utils | Test/example only | Useful |
| data | `gateway.py` | Source routing, broker/file/synthetic adapters, normalization, cache, public DataFrame API | adapters, registry, `get_data`, metadata/discovery APIs | Standard library; pandas; models/storage/transforms/licensing; brokers; utils | Internally coherent; package/examples/tests; live providers unverified | Essential |
| data | `scheduler.py` | Persisted job/feed status and async state loops | job/feed lifecycle functions | Standard library; asyncio; licensing/storage/utils | Tests/examples; execution does not move data | Questionable |
| data | `_common.py` | Legacy monolithic data facade and duplicate helpers | old data tools/cache/frame/file behavior | Standard library; pandas/NumPy; optional LMDB; service discovery; utils | Possibly used dynamically; no direct caller found | No demonstrated value / Questionable |
| data | `__init__.py` | Package facade | 99 declared exports | All public modules; utils standardizer | Used by callers, but internally inconsistent | Questionable |

### Files with multiple unrelated responsibilities

| File | Unrelated responsibilities found |
|---|---|
| `_common.py` | Tool envelopes, cache, Data wrapper, file I/O, market-data APIs, calendar APIs, transforms, symbol discovery |
| `gateway.py` | Provider adapters, broker connection policy, rate limiting, circuit breakers, normalization, caching, metadata, discovery, availability |
| `storage.py` | Schema migration, cache persistence, approved-path security, atomic dataset writes, dataset parsing |
| `transforms.py` | Timeframe conversion, batch resampling, streaming aggregation, synthetic generation, multi-timeframe alignment, historical labeling |
| `scheduler.py` | Job definitions, async task lifecycle, crash recovery, feed registry, overflow policy, feed status |

## 5. Public Behaviour Inventory

### `__init__.py`

**File responsibility:** Package facade only.

| Symbol group | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| 85 bound names | Re-exports | Expose implementation symbols at `app.services.data` | N/A | Import-time side effects from imported modules | Import/provider dependency errors | Tests, examples, selected cross-domain consumers | `test_public_exports.py` and others | Used, but unstable | Questionable |
| 14 unbound `__all__` names | Broken declarations | Claims package API that does not exist | Attribute lookup → failure | None | `AttributeError`/import failure | Intended package consumers | Stale public-export tests expect some | Unused as actual bindings | No demonstrated value |
| `standardize_domain_exports(...)` call | Registration call | Intended export/tool standardization | module globals + names → `None` | Logging only | None expected | Import-time | No meaningful assertion of injection | Ineffective | No demonstrated value |

### `_common.py`

**File responsibility:** Legacy monolithic implementation retained after responsibilities were extracted into dedicated modules.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `Data` and `data_df` | Class/function | Duplicate DataFrame wrapper/payload conversion | DataFrame or payload → wrapper/frame | Local state mutation | Type/value errors | No direct import found; dynamic search possible | Legacy/indirect | Possibly used | Questionable |
| `data_cache_get_path`, `data_cache_make_key` | Functions | Legacy cache location/key generation | cache parameters → path/key | Read-only | Validation errors | No direct caller found | Limited/legacy | Possibly used | Questionable |
| `data_cache_get`, `data_cache_set`, `data_cache_clear` | Functions | Legacy LMDB/pickle cache | key/value → value/status | Read-only / Persistence write | Cache/serialization errors | No direct caller found | Legacy | Possibly used | Questionable |
| `get_ohlcv_data`, `get_tick_data`, `get_spread_data`, `get_historical_volume` | Tool functions | Legacy market-data facade | request parameters → tool envelope | External API call / cache reads | Structured errors | No direct static caller found | Historical tests/docs | Possibly used | Questionable |
| `get_symbol_metadata`, `get_data_availability` | Tool functions | Legacy metadata/availability wrappers | source/symbol → tool envelope | Read-only / possible external call | Structured errors | No direct static caller found | Historical tests/docs | Possibly used | Questionable |
| `get_market_hours`, `get_trading_sessions` | Tool functions | Legacy calendar wrappers | symbol/range → envelope | None | Validation errors | No direct static caller found | Historical tests/docs | Possibly used | Questionable |
| `resample_ohlcv`, `align_multitimeframe_data` | Tool functions | Legacy transformation wrappers | records → envelope | None | Validation errors | No direct static caller found | Historical tests/docs | Possibly used | Questionable |
| `binance_data_list_symbols` | Tool function | Legacy Binance discovery | filters → envelope | External API call | Structured errors | No direct static caller found | Historical tests/docs | Possibly used | Questionable |

**Important:** `_OFFICIAL_AI_TOOLS` passes these functions through `standardize_tool_callable`, but that standardizer is also a placeholder. The loop does not register them in a real registry.

### `calendar.py`

**File responsibility:** Static FX-hours metadata and hourly session windows.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| Session constants | Constants | Define UTC hour ranges for Sydney, Tokyo, London, New York | N/A | None | None | `get_trading_sessions` | Indirect | Supporting | Supporting |
| `get_market_hours(symbol, request_id=None)` | Function | Return fixed Monday-Friday 24-hour market metadata | symbol → dict | Read-only | No explicit validation | Usage examples; stale package-level test | Unit/usage | Test-only at package level | Questionable |
| `get_trading_sessions(start_time, end_time, request_id=None)` | Function | Build hourly session windows | aware datetimes → list[dict] | None | Native datetime errors | Usage examples; stale package-level test | Unit/usage | Test-only | Useful |

**Observed defect:** For a session ending at hour `0`, `current.replace(hour=0)` keeps the same date. A 23:00 interval can therefore produce an end before its start.

### `csv.py`

**File responsibility:** Direct CSV loading, source slicing, DataFrame cache, and CSV tool wrappers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `load_csv(file_path, index_col=0, parse_dates=True)` | Function | Load CSV into DataFrame | path/options → DataFrame | Read-only | pandas/file errors | Usage examples | Unit/usage | Test/example-only | Useful |
| `CSVDataSource.fetch_data(...)` | Method | Slice CSV data by positional range and return `Data` | path/symbol/timeframe/range → `Data` | Read-only | validation/file errors | `csv_data_fetch_range` | Unit/usage | Used internally | Supporting |
| `clear_data_cache()` | Function | Clear shared in-memory DataFrame cache | none → `None` | Local state mutation | None expected | tests/examples | Unit | Test/example-only | Supporting |
| `get_cached_data(key, loader_func)` | Function | Memoize DataFrame-like loader results | key/callable → cached object | Local state mutation | loader errors | CSV implementation/tests | Unit | Used internally | Supporting |
| `csv_data_fetch_range(...)` | Tool function | Return CSV range in standard envelope | source/range → dict | Read-only | Errors converted to envelope | Usage examples/tests | Unit/usage | Test/example-only | Useful |
| `csv_data_load(...)` | Tool function | Return entire CSV as JSON-safe records | path/options → dict | Read-only | Errors converted to envelope | Usage examples/tests | Unit/usage | Test/example-only | Useful |
| `csv_data_saver_file_exists(...)` | Tool function | Check target CSV existence | path/symbol/timeframe → dict | Read-only | Errors converted to envelope | Usage examples/tests | Unit/usage | Test/example-only | Supporting |
| `csv_data_saver_save(...)` | Tool function | Save `Data` plus sidecar metadata | data/path/options → dict | Persistence write | Errors converted to envelope | Usage examples/tests | Unit/usage | Test/example-only | Useful |
| `csv_data_saver_load(...)` | Tool function | Load saved CSV plus metadata | path/symbol/timeframe → dict | Read-only | Structured not-found/error | Usage examples/tests | Unit/usage | Test/example-only | Useful |

### `frames.py`

**File responsibility:** Canonical lightweight `Data` wrapper and payload conversion.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `Data.__init__(df, symbol=None, timeframe=None)` | Constructor | Wrap DataFrame and metadata | DataFrame + metadata → `Data` | Local state mutation | Type/value errors | CSV/Parquet, indicators, optimization, utils, usage scripts | Cross-domain tests | Used | Essential |
| `Data.df`, `symbol`, `timeframe`, `close` | Properties | Expose frame and common metadata/close series | object → values | Read-only | `AttributeError`/column error | Indicator/optimization/utils consumers | Covered indirectly | Used | Essential |
| `Data.__getattr__(name)` | Method | Resolve DataFrame columns dynamically | column name → Series | Read-only | `AttributeError` | Indicator-style workflows | Indirect | Used | Useful |
| `data_df(payload)` | Function | Convert tool envelope to DataFrame | dict → DataFrame | Read-only | Type and payload errors | No confirmed production caller | Usage/legacy | Unbound package export | Questionable |

### `gateway.py`

**File responsibility:** Unified source routing, provider normalization, safety gates, cache integration, and public market-data APIs.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `SourceAdapterProtocol` methods | Protocol | Define readiness, bars, ticks, symbols, metadata interface | provider request → records/metadata | Depends on implementation | Provider errors | Adapter registry/type checking | Unit | Used internally | Supporting |
| `TokenBucketLimiter.consume()` | Method | Refill and consume one token | none → bool | Local state mutation | None expected | `check_rate_limit` | Unit | Used internally | Supporting |
| `CSVAdapter` public methods | Class methods | Read/filter local CSV bars/ticks and inspect symbols/metadata | request → records/list/dict | Read-only | file/pandas errors | Gateway registry | Unit/usage | Used internally | Useful |
| `ParquetAdapter` public methods | Class methods | Read/filter local Parquet bars/ticks and inspect symbols/metadata | request → records/list/dict | Read-only | file/pandas errors | Gateway registry | Unit/usage | Used internally | Useful |
| `SyntheticAdapter` public methods | Class methods | Return deterministic generated bars/ticks/static symbols | request → records/list/dict | None | validation errors | Gateway registry | Unit/usage | Used internally | Useful |
| `CCXTAdapter` public methods | Class methods | Retrieve exchange OHLCV, normalize records, expose metadata | request → DataFrame/records/list/dict | External API call | `ExternalServiceError`, `ValidationError` | Gateway registry | Unit/mocked | Possibly used | Useful |
| `BrokerAdapter` public methods | Class methods | Connect to broker client and retrieve/normalize bars/ticks/metadata | request → DataFrame/records/list/dict | External API call | provider and circuit errors | Gateway registry; MT5/cTrader/etc. | Unit/mocked/usage | Possibly used | Essential |
| `RATE_LIMITERS` | Constant registry | Per-source token buckets | N/A | Mutable local state | N/A | `check_rate_limit` | Unit | Used internally | Supporting |
| `ADAPTER_REGISTRY` | Constant registry | Map source names to adapters | N/A | Import-time instances | Import/provider dependency errors | `get_source_adapter` | Unit | Used internally | Essential |
| `check_rate_limit(source)` | Function | Enforce per-source token rate | source → `None` | Local state mutation | `ExternalServiceError` | Gateway execution | Unit | Used internally | Supporting |
| `get_circuit_breaker(source)` | Function | Read persisted source breaker state | source → dict | Read-only | DB errors are swallowed to defaults | Gateway/BrokerAdapter | Unit | Used internally | Supporting |
| `update_circuit_breaker(...)` | Function | Persist breaker state | state → `None` | Persistence write | DB errors logged/swallowed | BrokerAdapter/barrier | Unit | Used internally | Supporting |
| `check_circuit_breaker_barrier(source)` | Function | Block open circuit or transition to half-open | source → `None` | Persistence write on transition | `ExternalServiceError` | BrokerAdapter | Unit | Used internally | Supporting |
| `normalize_file_records(...)` | Function | Normalize MT5-style or standard file records | records/context → records | None | conversion errors partly tolerated | CSV/Parquet adapters | Unit | Used internally | Supporting |
| `get_source_adapter(source)` | Function | Resolve registered adapter | source → protocol | Read-only | `ValidationError` | Gateway APIs | Unit | Used internally | Essential |
| `execute_gateway_request(...)` | Function | Older record-list gateway path | request → list[dict] | Cache write / external call | data/provider/validation errors | Tests; no current `get_data` call | Unit | Test-only / superseded | Questionable |
| `execute_gateway_dataframe_request(...)` | Function | DataFrame-first OHLCV flow | request → DataFrame | Cache write / external call | data/provider/validation errors | `get_data` | Unit/usage | Used internally | Essential |
| `execute_gateway_tick_dataframe_request(...)` | Function | DataFrame-first tick/spread flow | request → DataFrame | Cache write / external call | data/provider/validation errors | `get_data` | Unit/usage | Used internally | Essential |
| `get_data(...)` | Function | Public bars/ticks/spreads/volume service API | strings/options → DataFrame | Cache write / external API call | `ValidationError`, `ExternalServiceError`, `DataError` | Tests and usage scripts; no confirmed production service caller | Extensive unit/usage | Test/example-only as entry point | Essential capability, unconfirmed runtime use |
| `get_symbol_metadata(...)` | Function | Normalize adapter metadata into `SymbolMetadata` | symbol/source → dict | Read-only / adapter call | validation/provider errors | Tests/usage | Unit/usage | Test/example-only | Useful |
| `list_symbols(...)` | Function | Return adapter symbols | source → list[str] | Read-only / possible provider call | validation/provider errors | Tests/usage | Unit/usage | Test/example-only | Useful |
| `get_data_availability(...)` | Function | Summarize cached record ranges/count | symbol/timeframe/source → dict | Read-only | DB errors logged | Tests/usage | Unit/usage | Test/example-only | Questionable |

### `generators.py`

**File responsibility:** Reconstruct simulation ticks from real ticks or bars and optionally stream to Parquet.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TICK_MODEL_*` | Constants | Select real/generated/trading-bar/M1-OHLC algorithms | N/A | None | None | Simulation preparation, examples, tests | Unit | Used | Essential |
| `SPREAD_*` | Constants | Select native/fixed/variable spread behavior | N/A | None | None | Generator defaults/tests | Unit | Used internally | Supporting |
| `SUPPORTED_MODELS`, `SUPPORTED_SPREAD_MODELS` | Constants | Configuration validation sets | N/A | None | None | `TicksGenerator` | Unit | Used internally | Supporting |
| `TicksGenerator.__init__(...)` | Constructor | Validate and store tick-generation configuration | model/data/spread options → instance | Local state mutation | `ValidationError` | Simulation preparation, optimization, scripts, tests | Extensive unit | Used | Essential |
| `TicksGenerator.generate(bars)` | Method | Dispatch selected generation algorithm | bars → standardized tick DataFrame | None | `ValidationError` | Simulation preparation | Extensive unit | Used | Essential |
| `generate_ticks(...)` | Function | Convenience DataFrame API around `TicksGenerator` | records/frame/options → DataFrame | None | `ValidationError` | Benchmark, examples, tests | Unit | Test/script-only | Useful |
| `generate_ticks_to_parquet(...)` | Function | Generate in bounded chunks and write Parquet | inputs/path/options → metadata dict | Persistence write | validation/PyArrow/file errors | Tests/docs | Unit | Test-only | Useful |

### `labeling.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `labeler_lexlb(data, up_threshold, down_threshold, request_id=None)` | Tool function | Create local-extrema labels in a standard envelope | series/thresholds → dict | None | Exceptions converted to envelope | Usage examples/tests | Unit/usage | Test/example-only | Useful |

### `licensing.py`

**File responsibility:** Persist and enforce source/symbol license policy.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `register_license(...)` | Function | Upsert source/symbol license metadata | license fields → `None` | Persistence write | `ValidationError` | Tests/admin-style use | Unit | Test-only | Useful |
| `validate_license(source, symbol, workflow_context, request_id=None)` | Function | Resolve registry/default policy and fail closed for restricted contexts | request → license dict | Read-only | `ValidationError` | Gateway and scheduler | Unit | Used internally | Essential supporting |

**Import-time behavior:** `_ensure_licensing_table()` creates/updates the SQLite schema when the module is imported.

### `models.py`

**File responsibility:** Canonical validation contracts.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `validate_utc_timestamp_helper(value)` | Function | Require timezone-aware UTC-compatible timestamp | timestamp → timestamp | None | Pydantic/value errors | Pydantic validators | Unit | Used internally | Supporting |
| `OHLCVRecord` | Pydantic model | Validate canonical bar fields and OHLC relationships | record → model | Local state validation | Pydantic validation error | Gateway | Unit | Used internally | Essential |
| `TickRecord` | Pydantic model | Validate canonical tick and ask/bid relationship | record → model | Local state validation | Pydantic validation error | Gateway | Unit | Used internally | Essential |
| `SpreadRecord` | Pydantic model | Validate spread record | record → model | Local state validation | Pydantic validation error | Gateway | Unit | Used internally | Supporting |
| `SymbolMetadata` | Pydantic model | Canonicalize instrument metadata | fields → model | Local state validation | Pydantic validation error | Gateway | Unit | Used internally | Supporting |
| `DataAvailability` | Pydantic model | Canonicalize availability summary | fields → model | Local state validation | Pydantic validation error | Gateway | Unit | Used internally | Supporting |

### `parquet.py`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `get_data_dir()` | Function | Resolve/create default Parquet directory | none → Path | Persistence write (directory) | filesystem errors | Parquet helpers | Unit | Used internally | Supporting |
| `load_parquet(file_path)` | Function | Load Parquet DataFrame | path → DataFrame | Read-only | pandas/file errors | Simulation preparation; examples/tests | Unit/usage | Used | Essential |
| `parquet_data_load(...)` | Tool function | Load Parquet as JSON-safe envelope | path → dict | Read-only | Errors converted to envelope | Examples/tests | Unit/usage | Test/example-only | Useful |
| `parquet_data_saver_file_exists(...)` | Tool function | Check saved Parquet existence | path/options → dict | Read-only | Errors converted to envelope | Examples/tests | Unit/usage | Test/example-only | Supporting |
| `parquet_data_saver_save(...)` | Tool function | Save `Data` and metadata | data/path/options → dict | Persistence write | Errors converted to envelope | Examples/tests | Unit/usage | Test/example-only | Useful |
| `parquet_data_saver_load(...)` | Tool function | Load saved Parquet and metadata | path/options → dict | Read-only | Structured not-found/error | Examples/tests | Unit/usage | Test/example-only | Useful |

### `responses.py`

**File responsibility:** Internal standardized response builders.

No non-underscore public exports were found. `_data_tool_response`, `_data_tool_validation_error`, `_data_tool_execution_error`, `_execution_ms`, and `_data_tool_spec` support CSV, Parquet, and labeling wrappers.

### `scheduler.py`

**File responsibility:** Persist job/feed state and maintain lightweight async task loops.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `ACTIVE_JOB_TASKS`, `ACTIVE_FEEDS`, `BACKGROUND_TASKS` | Mutable constants | Track process-local tasks/feed state | N/A | Local state mutation | N/A | Scheduler functions | Unit | Used internally | Supporting |
| `recover_crashed_jobs()` | Function | Mark persisted `running` jobs as `recovering` | none → count | Persistence write | DB errors logged/swallowed | Import-time call, tests | Unit | Used internally | Supporting |
| `create_data_update_job(...)` | Function | Validate and persist job definition | job fields → dict | Persistence write | `ValidationError`, `DataError` | Usage/tests | Unit/usage | Test/example-only | Useful |
| `start_data_update_job(name, ...)` | Function | Mark job running and create async loop | name → dict | Persistence write / local task state | validation/data errors | Usage/tests | Unit/usage | Test/example-only | Questionable |
| `stop_data_update_job(name, ...)` | Function | Cancel task and mark job stopped | name → dict | Persistence write / local task state | validation/data errors | Usage/tests | Unit/usage | Test/example-only | Useful |
| `run_data_update_job_once(name, ...)` | Function | Schedule one status-only execution | name → dict | Persistence write / local task state | validation/data errors | Tests | Unit | Test-only | Questionable |
| `get_data_update_job_status(name, ...)` | Function | Read persisted job status | name → dict | Read-only | validation/data errors | Usage/tests | Unit/usage | Test/example-only | Useful |
| `register_mock_feed(...)` | Function | Create/update mock feed state in memory and SQLite | feed fields → `None` | Local state mutation / Persistence write | `DataError` | Tests | Unit | Test-only | Questionable |
| `handle_feed_overflow(feed_id, policy)` | Function | Apply overflow status/counter policy | feed/policy → dict | Local state mutation / Persistence write | validation/data errors | Tests | Unit | Test-only | Useful as isolated policy |
| `get_feed_status(...)` | Function | Retrieve feed state from memory or SQLite | filters → dict/list | Read-only | validation/data errors | Tests | Unit | Test-only | Useful as isolated query |

**Critical behavior:** `_run_job_loop` and `_execute_single_run` only update database status/checkpoint fields and sleep. They do not call `get_data`, provider adapters, transforms, or storage writers.

### `storage.py`

**File responsibility:** SQLite initialization/cache plus secure local dataset I/O.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `Bar` | Dataclass | Canonical OHLCV bar for CSV loader | fields → object | None | native type errors | `load_ohlcv_csv`, validation | Unit | Used internally | Supporting |
| `DatabaseHelper.__init__` | Constructor | Create DB parent and initialize schema | db path → helper | Persistence write | `DataError` | import-time `db_helper` | Unit | Used internally | Essential supporting |
| `DatabaseHelper.get_connection()` | Context manager | Configure transaction, commit/rollback/close | none → connection | Persistence write | `DataError` | licensing/gateway/scheduler/storage | Unit | Used internally | Essential |
| `DatabaseHelper.init_database()` | Method | Create migration and core tables | none → `None` | Persistence write | `DataError` | constructor | Unit | Used internally | Essential |
| Storage constants | Constants | Approved roots, quarantine and DB paths, schema versions | N/A | None | None | storage functions | Unit | Used internally | Supporting |
| `validate_storage_path(path_str)` | Function | Enforce approved roots and CSV/Parquet extensions | path → resolved Path | Read-only | `ValidationError` | save/load dataset | Unit | Used internally | Essential supporting |
| `generate_cache_key(...)` | Function | Build deterministic SHA-256 key | request dimensions → string | None | None expected | Gateway | Unit | Used internally | Supporting |
| `get_cached_data(key, stale_data_behavior, request_id=None)` | Function | Read/decode TTL-aware SQLite cache record | key/policy → dict/None | Read-only | DB/JSON errors mostly swallowed | Gateway | Unit | Used internally | Essential supporting |
| `set_cached_data(...)` | Function | Insert/replace cache record | record dimensions → `None` | Persistence write | Errors logged/swallowed | Gateway | Unit | Used internally | Essential supporting |
| `clear_data_cache(...)` | Function | Dry-run or delete matching SQLite cache rows | filters → dict | Read-only / Persistence write | `ValidationError` | Usage/tests | Unit/usage | Test/example-only | Useful |
| `save_market_data(...)` | Function | Atomically write normalized records; quarantine failed temp file | records/path/options → dict | Persistence write | `ValidationError`, `DataError` | Tests/usage | Unit | Test/example-only | Useful |
| `load_local_dataset(...)` | Function | Load CSV/Parquet records from approved root | path → list[dict] | Read-only | `ValidationError`, `DataError` | Gateway adapters, storage loader | Unit | Used internally | Essential |
| `load_ohlcv_csv(path)` | Function | Parse timezone-aware CSV rows into validated `Bar` tuple | path → tuple[Bar] | Read-only | `ValueError`/data errors | Tests only | Unit | Test-only | Useful |

**No-op parameter:** `save_market_data(..., include_metadata=True)` assigns the value to `_` and does not write metadata.

### `transforms.py`

**File responsibility:** Timeframe conversion, resampling, aggregation, alignment, synthetic generation, and historical labeling.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TimeframeManager.timeframe_to_frequency()` | Class method | Map supported timeframe to pandas frequency | timeframe → string | None | `ValidationError` | Research cleaning/validation | Unit/research | Used | Essential |
| `TimeframeManager.validate_timeframe()` | Class method | Boolean check against class map | timeframe → bool | None | None | class resampling | Unit | Used internally | Supporting |
| `TimeframeManager.can_resample()` | Class method | Check source-to-higher timeframe ordering | two timeframes → bool | None | None | class resampling | Unit | Used internally | Supporting |
| `TimeframeManager.resample()` | Method | Resample DataFrame OHLCV and last-value extras | frame/options → DataFrame | None | `ValidationError` | Tests/research-adjacent | Unit | Test-only | Useful |
| `TimeframeManager.resample_multi_timeframe()` | Method | Resample to several target frames | frame/list → dict | None | propagated errors | Tests | Unit | Test-only | Useful |
| `BarAggregator.add_tick()` | Method | Convert tick to lower-bar input and aggregate | tick → completed bar/None | Local state mutation | `ValidationError` | Usage/tests | Unit/usage | Test/example-only | Useful |
| `BarAggregator.add_bar()` | Method | Update current OHLCV aggregate | bar → completed bar/None | Local state mutation | `ValidationError` | `add_tick`, tests | Unit | Used internally | Supporting |
| `BarAggregator.get_current_bar()` | Method | Snapshot incomplete bar | none → dict/None | Read-only | None expected | Tests | Unit | Test-only | Supporting |
| `BarAggregator.get_completed_bars()` | Method | Copy completed bars | none → list | Read-only | None expected | Usage/tests | Unit/usage | Test/example-only | Useful |
| `BarAggregator.flush()` | Method | Finalize current bar | none → dict/None | Local state mutation | `ValidationError` | Tests | Unit | Test-only | Useful |
| `timeframe_to_pandas_freq(tf)` | Function | Parse arbitrary M/H/D/W/MN codes to pandas frequency | timeframe → string | None | `ValidationError` | transform functions | Unit | Used internally | Supporting |
| `timeframe_to_minutes(tf)` | Function | Convert timeframe to approximate minutes | timeframe → int | None | `ValidationError` | transform/generator functions | Unit | Used internally | Supporting |
| `resample_ohlcv(...)` | Function | Resample normalized record lists | records/options → records | None | `ValidationError` | Tests/usage | Unit/usage | Test/example-only; package unbound | Useful |
| `align_multitimeframe_data(...)` | Function | Backward-align last closed bars to target timestamps | datasets/options → dict | None | pandas/validation errors | Tests/usage | Unit/usage | Test/example-only | Useful |
| `aggregate_ticks_to_bars(...)` | Function | Vectorized tick-to-OHLCV aggregation | ticks/options → bars | None | `ValidationError` | Tests/usage | Unit/usage | Test/example-only | Useful |
| `generate_synthetic_ticks(...)` | Function | Deterministic random-walk ticks | parameters → records | None | `ValidationError` | SyntheticAdapter/tests/usage | Unit | Used internally | Supporting |
| `generate_synthetic_bars(...)` | Function | Deterministic GBM-like bars | parameters → records | None | `ValidationError` | SyntheticAdapter/tests/usage | Unit | Used internally | Supporting |
| `label_market_data(...)` | Function | Horizon/threshold historical labels | records/options → records | None | `ValidationError` | Tests/usage | Unit/usage | Test/example-only | Useful |

**No-op parameter:** `align_multitimeframe_data(..., alignment_method=...)` logs the value but does not branch on it.

### `validation.py`

**File responsibility:** Shared data limits and validation.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `BarProtocol` | Protocol | Structural contract for canonical bars | N/A | None | None | `validate_bars` typing | Unit | Used internally | Supporting |
| Limit/timeframe/cache constants | Constants | Bound request limits and valid timeframe set | N/A | None | None | Gateway/scheduler | Unit | Used internally | Supporting |
| `validate_limit(...)` | Function | Resolve default and enforce positive maximum | limit/max/default → int | None | `ValidationError` | Gateway | Unit | Used internally | Essential supporting |
| `normalize_numeric(...)` | Function | Round numeric values by workflow precision | value/digits/context → number | None | conversion errors | Gateway record path | Unit | Used internally | Supporting |
| `validate_step_alignment(...)` | Function | Require value aligned to increment | value/step/name → `None` | None | `ValidationError` | Tests/possible callers | Unit | Test-only | Useful |
| `validate_timeframe(...)` | Function | Normalize and enforce configured timeframe set | string → uppercase string | None | `ValidationError` | Gateway/transforms | Unit | Used internally | Essential supporting |
| `validate_timezone(...)` | Function | Require supported timezone name | string → string | None | `ValidationError` | Tests | Unit | Test-only | Useful |
| `validate_bars(...)` | Function | Validate nonempty, ordered, timezone-aware OHLCV bars | iterable → tuple | None | `ValueError` | `load_ohlcv_csv` | Unit | Used internally | Supporting |

## 6. Actual Workflows

### `V1-WF-DATA-001` — Unified Historical OHLCV Query

* **Scope:** Cross-domain
* **Trigger:** Caller invokes `gateway.get_data(..., data_kind="ohlcv")`.
* **Input boundary:** Symbol, timeframe, UTC-compatible start/end strings, source, limit, workflow context, optional fallbacks.
* **Functions and methods used:**
  * `get_data`
  * `validate_timeframe`
  * `validate_limit`
  * `execute_gateway_dataframe_request`
  * `validate_license`
  * `check_rate_limit`
  * storage cache functions
  * `get_source_adapter`
  * adapter `get_market_dataframe`/`get_market_data`
  * canonical DataFrame validation
* **Files involved:** `gateway.py`, `validation.py`, `licensing.py`, `storage.py`, `models.py`, plus provider modules.
* **External dependencies:** pandas, SQLite, selected broker/file/CCXT provider.
* **Output boundary:** UTC-indexed DataFrame with `open`, `high`, `low`, `close`, `volume`, `spread`.
* **Failure behaviour:** Validations raise; source failures try fallbacks; final provider errors propagate as `ValidationError`, `ExternalServiceError`, or `DataError`; cache writes can fail open.
* **Operational status:** **Unverified** for live providers; **Working by static path and synthetic/local tests**.
* **Evidence:** `gateway.get_data`, `execute_gateway_dataframe_request`, `ADAPTER_REGISTRY`; detailed path in `tests/usage/app/services/02_data.py::example_01_mt5_bars`.

```text
Caller
→ get_data()
→ validate request
→ validate_license()
→ check_rate_limit()
→ SQLite cache lookup
→ source adapter
→ provider/file/synthetic retrieval
→ vectorized canonicalization
→ cache write
→ UTC-indexed DataFrame
```

### `V1-WF-DATA-002` — Tick, Spread, and Volume Query

* **Scope:** Cross-domain
* **Trigger:** `get_data(..., data_kind="ticks" | "spreads" | "volume")`.
* **Input boundary:** Symbol, date range, source, optional timeframe for volume.
* **Functions and methods used:** `get_data`, `execute_gateway_tick_dataframe_request`, adapter tick retrieval, tick canonicalization; volume delegates back to OHLCV flow.
* **Files involved:** `gateway.py`, `storage.py`, `licensing.py`, `validation.py`.
* **External dependencies:** pandas, SQLite, broker/file/synthetic provider.
* **Output boundary:** UTC-indexed tick/spread DataFrame or one-column volume DataFrame.
* **Failure behaviour:** Same fallback/error policy as OHLCV.
* **Operational status:** **Unverified** for live providers; synthetic path is represented in tests.
* **Evidence:** `gateway.get_data`, `execute_gateway_tick_dataframe_request`, `SyntheticAdapter.get_tick_data`.

```text
Caller
→ get_data()
→ tick/spread request path
→ cache
→ adapter.get_tick_dataframe()/get_tick_data()
→ canonical tick validation
→ optional spread projection
→ DataFrame
```

### `V1-WF-DATA-003` — Simulation Tick Reconstruction

* **Scope:** Cross-domain
* **Trigger:** Simulation data preparation selects `trading_timeframe`, `m1_ohlc`, `generated`, or `real`.
* **Input boundary:** Prepared bar DataFrame and optional M1 bars/real ticks.
* **Functions and methods used:** `TicksGenerator.__init__`, `TicksGenerator.generate`.
* **Files involved:** `app/services/simulation/data_preparation.py`, `generators.py`, optionally `parquet.py`.
* **External dependencies:** pandas, NumPy; PyArrow when exporting.
* **Output boundary:** Standardized tick DataFrame passed to simulation.
* **Failure behaviour:** Invalid configuration raises `ValidationError`; empty generated output is converted to simulation failure.
* **Operational status:** **Working** by confirmed runtime call path.
* **Evidence:** `app/services/simulation/data_preparation.py::_generate_ticks_for_backtest`.

```text
Simulation request
→ resolve tick/spread model
→ TicksGenerator(...)
→ generate(bars)
→ standardized tick DataFrame
→ simulator
```

### `V1-WF-DATA-004` — Local CSV/Parquet Load and Save

* **Scope:** Internal and cross-domain
* **Trigger:** Direct loader/tool wrapper, gateway local adapter, or simulation Parquet preparation.
* **Input boundary:** Approved or explicit file path and optional metadata.
* **Functions and methods used:** `load_csv`, `load_parquet`, CSV/Parquet tool wrappers, `load_local_dataset`, `save_market_data`.
* **Files involved:** `csv.py`, `parquet.py`, `frames.py`, `responses.py`, `storage.py`, `gateway.py`.
* **External dependencies:** pandas, PyArrow/Parquet engine, filesystem.
* **Output boundary:** DataFrame, list of records, `Data`, or standard tool envelope depending entry point.
* **Failure behaviour:** Direct functions raise; tool wrappers convert failures to envelopes; storage writes quarantine failed temp files.
* **Operational status:** **Working by static path and tests/examples**.
* **Evidence:** `CSVAdapter`, `ParquetAdapter`, simulation import of `load_parquet`, usage examples 8–17.

```text
Path
→ direct loader or tool wrapper
→ pandas read/write
→ optional Data wrapper/metadata envelope
→ caller or local gateway adapter
```

### `V1-WF-DATA-005` — Market-Data Transformation

* **Scope:** Internal
* **Trigger:** Caller requests resampling, alignment, or tick aggregation.
* **Input boundary:** Normalized record lists/DataFrames.
* **Functions and methods used:** `resample_ohlcv`, `align_multitimeframe_data`, `aggregate_ticks_to_bars`, `TimeframeManager`, `BarAggregator`.
* **Files involved:** `transforms.py`, `validation.py`.
* **External dependencies:** pandas, NumPy.
* **Output boundary:** Transformed records/DataFrames or completed bars.
* **Failure behaviour:** Validation/pandas exceptions; empty inputs usually return empty outputs.
* **Operational status:** **Working in tests/examples; limited confirmed runtime use**.
* **Evidence:** usage examples 26–28; research uses `TimeframeManager`.

```text
Normalized market data
→ timeframe validation
→ resample/align/aggregate
→ transformed market data
```

### `V1-WF-DATA-006` — Synthetic Data Generation

* **Scope:** Internal
* **Trigger:** Synthetic gateway source or direct transform call.
* **Input boundary:** Symbol, start time, count, prices, volatility, timeframe.
* **Functions and methods used:** `SyntheticAdapter`, `generate_synthetic_bars`, `generate_synthetic_ticks`.
* **Files involved:** `gateway.py`, `transforms.py`, `validation.py`.
* **External dependencies:** NumPy, pandas.
* **Output boundary:** Deterministic bar/tick records.
* **Failure behaviour:** Invalid parameters raise `ValidationError`.
* **Operational status:** **Working in unit/usage paths**.
* **Evidence:** gateway synthetic tests and `example_07_synthetic_bars`.

```text
Synthetic source request
→ SyntheticAdapter
→ seeded generator
→ canonical records
→ gateway canonicalization/cache
```

### `V1-WF-DATA-007` — Historical Label Generation

* **Scope:** Internal
* **Trigger:** Direct labeling call.
* **Input boundary:** Close series or bar records plus thresholds/horizon.
* **Functions and methods used:** `labeler_lexlb` or `label_market_data`.
* **Files involved:** `labeling.py`, `transforms.py`, `responses.py`.
* **External dependencies:** NumPy/pandas.
* **Output boundary:** Tool envelope or records containing labels/metadata.
* **Failure behaviour:** `labeler_lexlb` returns error envelope; `label_market_data` raises validation errors.
* **Operational status:** **Working in tests/examples; no production caller found**.
* **Evidence:** usage examples 23–24.

### `V1-WF-DATA-008` — Persisted Update Job Lifecycle

* **Scope:** Internal
* **Trigger:** Create/start/run-once/stop scheduler calls.
* **Input boundary:** Job definition including source, symbols, timeframes, format, path, schedule.
* **Functions and methods used:** scheduler lifecycle functions and SQLite.
* **Files involved:** `scheduler.py`, `licensing.py`, `storage.py`.
* **External dependencies:** asyncio, SQLite.
* **Output boundary:** Persisted state/status dict.
* **Failure behaviour:** Validation and DB errors; background loop catches most exceptions and retries.
* **Operational status:** **Partial**.
* **Evidence:** `_run_job_loop` only updates status and sleeps; `_execute_single_run` only marks completion.

```text
Create job
→ persist definition
→ start/run once
→ update status/checkpoint
→ sleep or complete
→ no data retrieval, transformation, or storage operation
```

### `V1-WF-DATA-009` — Feed Status and Overflow Tracking

* **Scope:** Internal
* **Trigger:** Mock feed registration, status query, or overflow event.
* **Input boundary:** Feed identity/state/counters and overflow policy.
* **Functions and methods used:** `register_mock_feed`, `handle_feed_overflow`, `get_feed_status`.
* **Files involved:** `scheduler.py`, `storage.py`.
* **External dependencies:** SQLite.
* **Output boundary:** Persisted/in-memory feed status.
* **Failure behaviour:** Missing feeds and DB errors raise.
* **Operational status:** **Partial**.
* **Evidence:** No provider subscription, event ingestion, heartbeat updater, or reconnect loop calls these functions in production code.

```text
Mock/manual feed state
→ in-memory + SQLite registration
→ overflow policy/status query
→ counters/state only
```

## 7. Usage and Caller Map

| Public symbol or group | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `Data` | indicators, optimization, utils, CSV/Parquet helpers | Direct import/instantiation | Runtime | `app/services/indicator/*`, `app/services/optimization/*`, `app/services/utils/common.py` |
| `TicksGenerator` | simulation data preparation, optimization parallel path | Direct import/instantiation | Runtime | `app/services/simulation/data_preparation.py`, `app/services/optimization/parallel.py` |
| `TICK_MODEL_REAL` | simulation data preparation | Direct import/reference | Runtime | `_resolve_tick_generator_config` |
| `TICK_MODEL_GENERATED` | simulation data preparation | Direct import/reference | Runtime | `_resolve_tick_generator_config` |
| `TICK_MODEL_TRADING_BAR` | simulation data preparation | Direct import/reference | Runtime | `_resolve_tick_generator_config` |
| `TICK_MODEL_OHLC_M1` | simulation data preparation | Direct import/reference | Runtime | `_resolve_tick_generator_config` |
| `load_parquet` | simulation data preparation | Direct import/call | Runtime | `app/services/simulation/data_preparation.py` |
| `TimeframeManager` | research cleaning and validation | Direct import/call | Runtime | `app/services/research/data/cleaning.py`, `validation.py` |
| `OHLCVRecord`, `TickRecord`, `SpreadRecord`, `SymbolMetadata`, `DataAvailability` | gateway | Direct import/instantiation | Runtime internal | `app/services/data/gateway.py` |
| `validate_license` | gateway, scheduler | Direct call | Runtime internal | `execute_gateway_*`, `_validate_job_creation_args` |
| storage cache functions | gateway | Direct call | Runtime internal | `_check_gateway_cache`, gateway execution |
| `generate_synthetic_bars`, `generate_synthetic_ticks` | `SyntheticAdapter` | Direct call | Runtime internal | `gateway.py` |
| `get_data` | data usage scripts and data unit tests | Direct import/call | Test/example | `tests/usage/app/services/02_data.py`, gateway tests |
| `generate_ticks` | benchmark, usage, unit tests | Direct call | Script/test | `scripts/benchmarks/ticks_generation.py`, usage/tests |
| `generate_ticks_to_parquet` | unit tests/docs | Direct call | Test | `test_generators.py` |
| CSV/Parquet tool wrappers | usage and unit tests | Direct call | Test/example | usage examples 8–17 |
| transform functions | usage and unit tests | Direct call | Test/example | usage examples 24–28 |
| scheduler functions | usage and unit tests | Direct call | Test/example | usage examples 29–30, scheduler tests |
| feed functions | unit tests | Direct call | Test | `test_feeds_scheduler.py`, scheduler extra tests |
| calendar functions | direct submodule usage/examples; stale package test | Direct call | Test/example | `tests/usage/app/services/02_data.py` |
| `_common.py` public functions | No direct import/call found | Possible dynamic resolution | Unknown | dynamic service discovery remains possible |
| 14 unbound `__all__` names | No callable package object exists | Declared only | None | `__init__.py` versus no-op standardizer |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on | Symbols or capabilities consumed | Where used in this domain | Evidence |
|---|---|---|---|
| `app.services.brokers.mt5` | `get_mt5_client` and bar/tick client methods | `gateway._mt5_client`, `BrokerAdapter` | `gateway.py` |
| `app.services.brokers.ctrader` | `get_ctrader_client` | `gateway._ctrader_client` | `gateway.py` |
| `app.services.brokers.dukascopy` | `get_dukascopy_client` | `gateway._dukascopy_client` | `gateway.py` |
| `app.services.brokers.binance` | `get_binance_client` | `gateway._binance_client` | `gateway.py` |
| `app.services.brokers.yahoo` | `get_yahoo_client` | `gateway._yahoo_client` | `gateway.py` |
| `app.services.utils.errors` | `DataError`, `ValidationError`, `ExternalServiceError` | Most modules | Direct imports |
| `app.services.utils.logger` | structured logging | All substantive modules | Direct imports |
| `app.services.utils.normalization` | `_parse_datetime` and legacy timestamp helpers | gateway and `_common` | Direct imports |
| `app.services.utils.paths` | path normalization/parent creation | storage | Direct imports |
| `app.services.utils.standard` | tool response/export standardization | initializer, responses, `_common` | Direct imports; standardizers are placeholders |
| `app.services.utils.common` | DataFrame cache/serialization helpers | CSV/frames-related code | Direct imports |
| SQLite | cache, licenses, jobs, feeds, circuit breakers | storage/licensing/gateway/scheduler | `DatabaseHelper` |
| pandas/NumPy | frame transformations and generation | most data-processing files | Third-party imports |
| Pydantic | canonical record validation | models/gateway | Third-party imports |
| PyArrow | bounded Parquet tick export | generators | Third-party imports |
| CCXT/yfinance/broker SDKs | provider access | gateway adapters/broker clients | Lazy or broker-side imports |

### Inbound — other packages depend on this domain

| Consuming package | Symbols consumed | Purpose | Evidence |
|---|---|---|---|
| `app.services.simulation` | `TicksGenerator`, four tick-model constants, `load_parquet` | Prepare tick stream and source data for backtests | `data_preparation.py` |
| `app.services.optimization` | `TicksGenerator`, `Data` | Optimization/simulation preparation and frame handling | code-search imports |
| `app.services.research.data` | `TimeframeManager` | Expected frequency, timeframe validation, cleaning | `cleaning.py`, `validation.py` |
| `app.services.indicator` | `Data` | Accept/return wrapped data in indicator APIs | indicator modules and standard facade |
| `app.services.utils` | `Data` | Shared merge/concat/cache operations | `utils/common.py` |
| scripts/benchmarks | `generate_ticks`/generator symbols | Performance measurements | `scripts/benchmarks/ticks_generation.py` |
| scripts/examples | gateway, Data, transforms, generators | Demonstration/manual workflows | `scripts/examples/*` |
| tests/usage | broad package and submodule API | Usage catalog | `tests/usage/app/services/02_data.py` |
| tests/unit | broad implementation coverage | Contract/behavior verification | `tests/unit/app/services/data/*` |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `_common.py::Data` | `frames.py::Data` | DataFrame wrapper and metadata access | Both define equivalent named abstraction | Divergent behavior and dynamic resolution ambiguity |
| `_common.py` response helpers | `responses.py` | Standard tool envelopes/errors | Extracted helpers remain duplicated | Inconsistent envelopes |
| `_common.py` file persistence | `frames.py` + `csv.py` + `parquet.py` | Save/load Data plus sidecar metadata | Same helper names/flows | Multiple sources of truth |
| `_common.py` market-data tools | `gateway.py` | OHLCV/tick/spread/metadata/availability | Same capability names | Caller may reach old or new path |
| `_common.py` calendar tools | `calendar.py` | Hours and sessions | Same public names | Package binding confusion |
| `_common.py` transforms | `transforms.py` | Resampling/alignment | Same capability names | Return-type/envelope inconsistency |
| `csv.clear_data_cache` | `storage.clear_data_cache` | Cache clearing | One clears process DataFrame cache; one clears SQLite gateway cache | Same name, different target and signature |
| `csv.get_cached_data` | `storage.get_cached_data` | Cache retrieval | One memoizes arbitrary DataFrames; one reads TTL SQLite records | Package-level binding hides gateway cache function |
| `TimeframeManager.timeframe_to_frequency` | `timeframe_to_pandas_freq` | Timeframe-to-pandas conversion | Separate maps/parsers | Different accepted timeframe sets |
| `TimeframeManager.validate_timeframe` | `validation.validate_timeframe` | Timeframe validation | Boolean restricted map vs normalized broad validation | Contradictory acceptance |
| `TimeframeManager.resample` | `resample_ohlcv` | OHLCV resampling | DataFrame API vs record-list API | Behavior/column conventions can diverge |
| `execute_gateway_request` | DataFrame-first gateway functions | Source/license/cache/adapter orchestration | Two complete execution paths | Older path can drift; current `get_data` uses only DataFrame path |
| `labeler_lexlb` | `label_market_data` | Historical labeling | Local-extrema vs horizon threshold | Capability overlap with different contract/error style |
| `save_market_data` | CSV/Parquet saver tools | Local persistence | Atomic approved-root writer vs Data/sidecar wrappers | Different security, metadata, and return contracts |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| 14 unbound package exports | Declared in `__all__`, absent from module globals | Initializer imports, definitions, standardizer implementation, repo search | High | `__init__.py`; placeholder `standardize_domain_exports` |
| Missing `market_tools.py` | README/initializer comments depend on a file that does not exist | Direct repository fetch and path/code search | High | Fetch returned not found; README/comments reference it |
| `_common.py` | No direct static caller; duplicates extracted modules | imports, calls, service discovery, docs | Medium | Only plan/frames/responses references found; dynamic discovery remains |
| `execute_gateway_request` | Superseded record-list path; current `get_data` does not call it | function-call and import search | Medium | Tests and definition found; DataFrame path is current |
| `load_ohlcv_csv` | Only unit-test caller found | import/call search | High | storage persistence test |
| `generate_ticks_to_parquet` | Unit-test/documentation use only | import/call search | High | generator tests and README |
| scheduler lifecycle | No production caller found; run loop is status-only | import/call/API/scheduled-task search | High for no repository caller; Medium for external use | usage/tests only |
| feed registration/overflow/status | Mock/test state, no live feed wiring | subscriber/callback/registry/call search | High within repository | scheduler tests only |
| calendar package exports | Functions exist in submodule but package names are unbound | initializer and caller search | High | direct submodule imports in usage file |
| `alignment_method` | Accepted/logged but does not affect algorithm | function-body inspection | High | `align_multitimeframe_data` |
| `include_metadata` in `save_market_data` | Ignored | function-body inspection | High | assigned to `_` |
| `get_data_availability` | Reports cache rows only, always zero gaps and `is_ready=True` | body inspection | High | hard-coded model values |
| `SyntheticAdapter.end_time` | Ignored; fixed counts of 100 bars/250 ticks | method-body inspection | High | `# noqa: ARG002`, fixed generator counts |
| Broker/local `list_symbols` | Static lists or filename prefix parsing, not robust provider discovery | adapter-body inspection | High | gateway adapters |
| package public-export test | Expects exactly 32 APIs and `generate_ticks_frame`; current facade has 99 and lacks that symbol | test versus initializer comparison | High | `test_public_exports.py` and `__init__.py` |

### Confidence scale

| Confidence | Meaning |
|---|---|
| **High** | Relevant static usage categories were searched and evidence is explicit |
| **Medium** | Static searches are complete enough for a finding, but dynamic/external use cannot be excluded |
| **Low** | Evidence was partial or inaccessible |

No item is labeled “dead code” solely from absence of a direct import where dynamic discovery remains possible.

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Scheduled update jobs | No call to gateway, adapter, transform, or storage writer | Jobs can appear successful without moving data | `_run_job_loop`, `_execute_single_run` |
| Real-time feed monitoring | No live subscription, heartbeat updater, event consumer, or reconnect driver | Only manually registered/mock status can be observed | scheduler caller search |
| Data availability | No provider/file scan or gap computation | Readiness/gaps can be misleading | hard-coded `gap_count=0`, `is_ready=True` |
| Package AI/data tool facade | Missing `market_tools.py`; standardizer no-op; 14 names unbound | Documented package imports fail | initializer/README/standardizer |
| Market sessions | Midnight rollover not advanced to next date | Session window may have end before start | `calendar.get_trading_sessions` |
| Synthetic source range | End time does not determine output count | Returned data may exceed/not cover requested range | SyntheticAdapter fixed counts |
| Licensing administration | Registry exists, but no production administrative workflow found | Policy can rely on defaults only | caller search |
| Generated Parquet output | No production pipeline consumes `generate_ticks_to_parquet` | Useful export remains isolated | caller search |
| Legacy tool layer | `_common.py` capabilities are disconnected from current package facade | Old behavior remains ambiguous and duplicative | direct and dynamic usage searches |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-DATA-001` | Package exports 14 undefined names | `app/services/data/__init__.py` | Direct imports and wildcard imports can fail | `__all__` versus imports |
| `V1-ISSUE-DATA-002` | Export standardizer is a placeholder | `app/services/utils/standard.py::standardize_domain_exports` | Expected bindings/metadata are never created | Function logs only |
| `V1-ISSUE-DATA-003` | README/initializer reference removed `market_tools.py` | README and `__init__.py` comments | Public contract cannot be trusted | Missing repository path |
| `V1-ISSUE-DATA-004` | Current public-export unit test is incompatible with current facade | `test_public_exports.py` | Test suite likely fails before behavior checks | 32 expected vs 99 declared |
| `V1-ISSUE-DATA-005` | Legacy monolith duplicates most of the package | `_common.py` | Multiple sources of truth and dynamic ambiguity | Overlap table |
| `V1-ISSUE-DATA-006` | Same cache names represent different cache systems | `csv.py` vs `storage.py` | Callers can clear/read the wrong cache | Package binds CSV versions |
| `V1-ISSUE-DATA-007` | Two gateway execution pipelines coexist | `execute_gateway_request` vs DataFrame execution | Validation/cache behavior can drift | `get_data` uses only DataFrame path |
| `V1-ISSUE-DATA-008` | Scheduler reports successful runs without executing update work | `scheduler.py` | False operational status | Loop only updates rows/sleeps |
| `V1-ISSUE-DATA-009` | Feed workflow is mock/manual only | `register_mock_feed` and related functions | No real feed-health guarantee | No production registration/subscriber |
| `V1-ISSUE-DATA-010` | Timeframe definitions are inconsistent | `validation.py`, `TimeframeManager`, parser functions | One API accepts values another rejects | Different maps/algorithms |
| `V1-ISSUE-DATA-011` | Error contracts are inconsistent | direct loaders, tool wrappers, `validate_bars`, gateway | Callers must handle exceptions, envelopes, and swallowed errors | Public behavior tables |
| `V1-ISSUE-DATA-012` | Importing data modules mutates persistent state | storage, licensing, scheduler | Imports create DB/tables and run recovery | `db_helper`, `_ensure_licensing_table`, `recover_crashed_jobs()` |
| `V1-ISSUE-DATA-013` | Availability output overstates certainty | `gateway.get_data_availability` | Consumers can treat unmeasured gaps/readiness as real | hard-coded fields |
| `V1-ISSUE-DATA-014` | Static adapter metadata/discovery can misrepresent providers | gateway adapters | Symbol support/readiness can be inaccurate | static lists and `is_ready=True` |
| `V1-ISSUE-DATA-015` | Rate limiter claims thread safety without synchronization | `TokenBucketLimiter` | Concurrent calls can race | mutable fields, no lock |
| `V1-ISSUE-DATA-016` | Ignored public parameters | `alignment_method`, `include_metadata`, synthetic `end_time` | API suggests behavior that is not implemented | body inspection |
| `V1-ISSUE-DATA-017` | Market-session rollover defect | `calendar.get_trading_sessions` | Invalid cross-midnight windows | same-date `.replace(hour=0)` |
| `V1-ISSUE-DATA-018` | Files combine several responsibilities | gateway/storage/transforms/scheduler | Higher change coupling and harder usage analysis | inventory |
| `V1-ISSUE-DATA-019` | Cache writes and breaker writes often swallow failures | storage/gateway | Request may succeed without durability/safety state | broad exception logging |
| `V1-ISSUE-DATA-020` | Public return types are inconsistent across parallel capabilities | direct APIs vs tool APIs vs legacy `_common` | DataFrame/list/tuple/dict envelope differences | behavior inventory |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-DATA-001` | Unified OHLCV retrieval | `gateway.get_data`, adapters, cache, models | `V1-WF-DATA-001` | Test/example entry point; internal path complete | Essential | Live providers unverified |
| `V1-CAP-DATA-002` | Tick/spread/volume retrieval | gateway tick DataFrame path | `V1-WF-DATA-002` | Test/example entry point | Essential | Live providers unverified |
| `V1-CAP-DATA-003` | Source adapter routing | `ADAPTER_REGISTRY`, adapters, broker specs | 001–002 | Used internally | Essential | Static readiness/symbol lists |
| `V1-CAP-DATA-004` | Canonical records and DataFrames | models, gateway canonicalizers, `Data` | 001–005 | Used | Essential | Multiple contract styles remain |
| `V1-CAP-DATA-005` | SQLite gateway cache | storage cache functions | 001–002 | Used internally | Essential | Writes fail open |
| `V1-CAP-DATA-006` | License gating | licensing registry/validation | 001–002, 008 | Used internally | Supporting | Admin workflow not found |
| `V1-CAP-DATA-007` | Rate limiting and circuit breakers | gateway limiter/breaker functions | 001–002 | Used internally | Supporting | Concurrency and durability limitations |
| `V1-CAP-DATA-008` | Local CSV/Parquet access | csv/parquet/storage/adapters | 004 | Used; Parquet load has runtime consumer | Essential | Parallel persistence contracts |
| `V1-CAP-DATA-009` | Secure atomic dataset writing | `storage.save_market_data` | 004 | Test/example-only | Useful | Metadata flag ignored |
| `V1-CAP-DATA-010` | Timeframe conversion/resampling | `TimeframeManager`, transform functions | 005 | Partly runtime, partly test/example | Useful | Inconsistent accepted sets |
| `V1-CAP-DATA-011` | Tick/bar aggregation | `BarAggregator`, `aggregate_ticks_to_bars` | 005 | Test/example-only | Useful | No production feed integration |
| `V1-CAP-DATA-012` | Multi-timeframe alignment | `align_multitimeframe_data` | 005 | Test/example-only | Useful | `alignment_method` ignored |
| `V1-CAP-DATA-013` | Synthetic data | transform generators, SyntheticAdapter | 006 | Used internally/tests | Useful | Request range not honored fully |
| `V1-CAP-DATA-014` | Simulation tick reconstruction | `TicksGenerator` | 003 | Used | Essential | Strongest confirmed cross-domain workflow |
| `V1-CAP-DATA-015` | Tick Parquet streaming | `generate_ticks_to_parquet` | 003/004 | Test-only | Useful | Isolated from runtime |
| `V1-CAP-DATA-016` | Historical labeling | `labeler_lexlb`, `label_market_data` | 007 | Test/example-only | Useful | Two distinct contracts |
| `V1-CAP-DATA-017` | Market hours/sessions | calendar functions | 005-adjacent | Test/example-only | Questionable | Package binding broken; rollover bug |
| `V1-CAP-DATA-018` | Scheduled update definitions | scheduler job CRUD/state | 008 | Test/example-only | Questionable | No actual update execution |
| `V1-CAP-DATA-019` | Feed status/overflow state | scheduler feed functions | 009 | Test-only | Questionable | Mock/manual only |
| `V1-CAP-DATA-020` | Data availability summary | gateway cache query | 001-adjacent | Test/example-only | Questionable | Does not calculate gaps/readiness |
| `V1-CAP-DATA-021` | Legacy AI data tools | `_common.py` | Legacy/disconnected | Possibly used | Questionable | Dynamic use cannot be excluded |
| `V1-CAP-DATA-022` | Package facade | `__init__.py` | All | Used but broken | Questionable | 14 unbound exports and stale tests |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

The following V1 behavior demonstrably provides value:

* `TicksGenerator` and its model constants are actively used by simulation data preparation.
* `load_parquet` is an active simulation dependency.
* `TimeframeManager.timeframe_to_frequency` supports research cleaning and validation.
* `Data` is consumed by indicator, optimization, and utility code.
* Gateway adapter routing, canonical OHLCV/tick DataFrames, schema validation, licensing, cache integration, and source fallback form a coherent capability even though production entry-point use and live provider behavior are not confirmed.
* SQLite transaction handling, cache-key generation, approved-root validation, atomic writes, and quarantine behavior are useful support functions.
* CSV/Parquet tool wrappers, resampling, alignment, aggregation, synthetic data, and labeling are functional utilities with test/example evidence.

### Behaviour that exists but is disconnected

* Scheduler jobs do not execute their declared data-update purpose.
* Feed status/overflow functions are not connected to live feeds.
* `generate_ticks_to_parquet` has no production consumer.
* Calendar and several transform tools exist only through direct submodule imports because package bindings are missing.
* `get_data_availability` is not connected to actual provider/file availability or gap detection.
* Licensing registration has no confirmed production administration path.
* `_common.py` retains legacy tools without a clear current owner or direct caller.

### Likely dead weight

No item is conclusively labeled dead where dynamic discovery remains possible. The strongest candidates for removal review are:

* unbound names in `__all__`;
* the stale public-export expectations;
* the superseded `execute_gateway_request` list-record pipeline;
* duplicated implementations in `_common.py`;
* status-only scheduler execution;
* mock-only feed management in production package code.

### Duplicated responsibilities

The highest-risk duplication is `_common.py` versus the extracted modules. Cache names are additionally duplicated between `csv.py` and `storage.py` with different semantics. Timeframe validation/resampling and gateway execution each have multiple implementations.

### Important uncertainties

* Whether external applications import `_common.py` or dynamically resolve its tools.
* Whether live broker adapters satisfy their assumed DataFrame schemas.
* Whether the current test suite is intentionally in transition or simply failing.
* Whether provider credentials, optional packages, and local data files make all adapters operational.
* Whether package-level imports are supplemented by runtime monkey-patching outside the repository; no such mechanism was found in the inspected code.

### Manual confirmation required

* Execute the complete data test suite against this exact commit.
* Import `app.services.data`, iterate its `__all__`, and record missing attributes.
* Exercise one real request for every broker source and verify provider columns.
* Confirm whether any deployed process uses `_common.py`.
* Confirm whether scheduler jobs are expected to move data or are intentionally status-only.
* Confirm whether the current 99-name facade or the 32-name unit-test contract is authoritative.

## Final Validation

* Every Python file found under `app/services/data` is represented.
* Every package `__all__` entry was checked against the initializer bindings.
* Public classes, functions, principal methods, constants, adapters, and registries are represented.
* Static callers were searched across the available repository.
* Inbound and outbound dependencies are summarized.
* Workflows are based on actual function paths.
* Production/runtime use is distinguished from tests, examples, and scripts.
* Dynamic/indirect uncertainty is labeled.
* No Version 2 requirements or redesign proposals were created.
* No repository code was changed.

## Evidence Not Accessible

* A runnable local checkout and complete dependency environment.
* Live provider terminals/accounts, API credentials, and network responses.
* Runtime SQLite/LMDB/cache contents from deployed environments.
* Consumers outside the indexed `haruperi/HaruQuant` repository.
* Confirmation of dynamic imports or monkey-patching performed only by deployment configuration.
