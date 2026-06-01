# HaruQuantAI Data Module Technical Specification v8

**Document status:** Production-ready standalone implementation specification — final pre-implementation baseline
**Specification version:** v8
**Created:** 2026-05-31
**Target package:** `tools/data/`
**Primary standard:** HaruQuantAI Tool Function Standard
**Companion standards:** HaruQuantAI Code Quality Standard, Agent Standard, Agentic AI Playbook
**Implementation stance:** Complete professional rebuild of the data module from a clean standalone target design
**Backward compatibility:** Not required

## v8 Production Closure Updates

This version closes the final pre-implementation specification gaps and the final industry-grade production hardening additions and is the authoritative baseline for rebuilding `tools/data/`.

It incorporates the final non-blocking review observations before implementation:

- adds `UNSUPPORTED_OPERATION` to the required deterministic error-code list
- confirms Phase 1 `get_market_hours` may return current market hours only, with historical changes deferred
- confirms Phase 1 synthetic data requires only `gbm`, while mean-reverting and trend processes are Phase 2 extensions
- confirms `get_historical_volume` may be implemented directly or derived from `get_market_data` as long as its public contract is stable
- confirms multi-timeframe alignment defaults to `allow_lookahead=False` with `last_known_closed_bar`

This version adds the final industry-grade production hardening layer:

- raw data versioning and source revision tracking
- precision and rounding enforcement by symbol and asset class
- explicit timestamp gap and overlap resolution policy
- deterministic rate-limit and backoff strategy for network sources
- asset-specific metadata extensions for futures, options, bonds, and crypto
- downstream contract alignment gates for simulation, optimization, risk, and execution
- data licensing and attribution tracking
- additional deterministic error codes for source revision, precision, timestamp overlap, rate limits, licensing, and schema drift

This version also retains the final production-closure additions:

- dedicated contracts for data availability, spread records, historical volume, market hours, and trading sessions
- explicit cache expiry and request-level cache TTL policy
- request-level `source_timezone` override for CSV/local datasets with naive timestamps
- bounded request limits with deterministic `LIMIT_EXCEEDED` failures
- `SOURCE_NOT_CONFIGURED` error semantics for disabled or unconfigured sources
- source metadata standards
- request ID propagation into cache operations
- tick-volume and real-volume handling for MT5-like OHLCV records
- resampling aggregation rules for volume and spread
- scheduler one-time vs recurring job behavior
- explicit Phase 1 non-goal for streaming subscriptions, with future extension rules

---

## 1. Executive Summary

This document defines the complete production-ready target design for the HaruQuantAI Data Module.

The module must be rebuilt as a clean, contract-driven, agent-safe, testable, and maintainable data domain under:

```text
tools/data/
```

The data module is the foundation for strategy creation, simulation, optimization, analytics, risk, portfolio management, paper trading, live execution preparation, and agent workflows. It must therefore provide reliable, normalized, auditable access to historical and live market data from local and external sources while preserving the full functional coverage of the current data domain.

This v8 design is a production-ready standalone implementation specification. It defines the canonical production target for the data module without depending on old APIs, old file names, old implementation patterns, or compatibility wrappers. Required functionality is preserved at the capability level through clean contracts, official tools, source adapters, validation rules, tests, usage examples, and acceptance gates.

The final production module must support:

- OHLCV bar data access
- tick data access
- spread data access
- symbol metadata access
- market hours and trading session access
- data availability inspection
- historical volume inspection
- multi-timeframe alignment
- OHLCV resampling
- local CSV source loading and saving
- local Parquet source loading and saving
- MT5 source integration
- cTrader source integration through MCP/client boundary
- Dukascopy historical data integration
- Dukascopy live/stream-oriented data access where supported
- Binance symbol listing or equivalent exchange-symbol discovery where supported
- synthetic tick generation
- synthetic OHLCV generation using GBM-style generation
- tick-to-bar aggregation
- timeframe utilities
- labeling tools such as LEXLB-style labeling
- scheduled data update lifecycle management
- cache key creation, cache read/write, and cache clearing
- strict data validation and normalization
- agent-safe standard tool responses
- tests, usage examples, and documentation for every official AI tool

The target outcome is:

```text
Few clean official data tools.
Many internal adapters and helpers.
Strict contracts.
No raw DataFrame leakage at the AI-tool boundary.
Deterministic validation.
Auditable behavior.
Production-friendly defaults.
```

---



## 1A. Production-Ready Definition

This document is considered production-ready because it defines the full implementation target, governance rules, module boundaries, acceptance criteria, tests, usage examples, safety behavior, observability requirements, and phase gates required to build the HaruQuantAI Data Module professionally.

The implementation created from this specification is production-ready only when all of the following are true:

1. Every official AI tool exported from `tools/data/__init__.py` follows the HaruQuantAI Tool Function Standard.
2. Every official AI tool returns the standard response schema and never returns raw pandas objects, raw SDK objects, `None`, or unstructured exceptions.
3. Every official AI tool accepts `request_id: Optional[str] = None` and propagates it through logs, metadata, audit-relevant output, and downstream source calls where practical.
4. Every official AI tool has complete unit tests, schema tests, error-path tests, metadata tests, and usage examples.
5. The package reaches at least 80% test coverage, with no critical path excluded from coverage without documented justification.
6. All market data crossing the AI-tool boundary is JSON-serializable and contract-compliant.
7. Internal source adapters may use pandas, SDK objects, sockets, network clients, and broker APIs, but those details must not leak through official tool responses.
8. Data validation, normalization, quality scoring, timestamp handling, cache handling, and source metadata are deterministic and documented.
9. Scheduler and cache tools have explicit side-effect metadata and are not mislabeled as read-only tools.
10. MT5, cTrader, Dukascopy, and exchange-source integrations handle credentials, network errors, timeouts, retries, and unavailable services safely.
11. All production files contain module docstrings, typed public functions, useful docstrings, structured logging, and explicit error handling.
12. No secrets, account IDs with passwords, API keys, raw tokens, or credential payloads are logged or returned.
13. CI quality gates pass: `black`, `isort`, `flake8`, `mypy`, `pytest`, and coverage above 80%.
14. Downstream modules can consume the official data contracts without relying on undocumented internals.
15. The implementation has a clear README or documentation section explaining source configuration, examples, environment variables, and common failure modes.

### 1A.1 Production Sign-Off Rule

The data module must not be marked production-ready until these commands pass:

```bash
black .
isort .
flake8 .
mypy tools tests
pytest --cov=tools --cov=tests --cov-fail-under=80
```

The production sign-off artifact must include:

```text
- implemented spec version
- test command output summary
- coverage percentage
- exported tool list
- known limitations
- source adapters enabled
- environment variables required
- downstream modules validated
```

### 1A.2 No Partial Production Rule

A source adapter may be individually marked as unavailable, experimental, or disabled by configuration, but the core data module must still behave safely.

If an adapter is disabled or unavailable:

```text
- the official tool must return status="error"
- the error code must be deterministic
- the message must explain the unavailable source
- no fallback source may be used silently
- metadata must identify the requested source and request_id
```

### 1A.3 Production Defaults

Production defaults must be safe:

```text
allow_stale = False
validate_data = True
normalize_timestamps = True
return_quality_report = True for data-fetching tools
read_only = True for retrieval tools
writes_file = True only for explicit storage tools
modifies_database = False unless a future persistent database is introduced
places_trade = False for every data module tool
requires_network = True only for external/broker/source-network tools
```

## 2. Design Goals

### 2.1 Primary Goals

The v8 data module must:

1. Provide a stable production data foundation for HaruQuantAI.
2. Expose only safe, intentional, agent-callable tools from `tools/data/__init__.py`.
3. Preserve the full capability coverage of the current data module at the functional level.
4. Use clean internal adapters for different sources.
5. Normalize all market data into a consistent internal contract.
6. Return standard HaruQuantAI tool responses from every official AI tool.
7. Keep pandas and source SDK objects inside the implementation boundary.
8. Make every public behavior testable.
9. Avoid unnecessary abstraction while removing oversized mixed-responsibility files.
10. Support future strategy, simulation, analytics, risk, portfolio, and execution modules without ambiguity.

### 2.2 Non-Goals

The v8 data module must not:

- preserve old API names merely for compatibility
- expose raw clients as official AI tools
- expose credential loaders as official AI tools
- expose internal cache helpers as official AI tools
- return raw pandas DataFrames from official AI tools
- place trades or modify broker account state
- perform strategy logic, backtesting logic, analytics scoring, or risk approval
- silently normalize bad data without reporting quality warnings
- hide stale, partial, missing, or conflicting data
- mix scheduler lifecycle logic into low-risk data retrieval tools
- log credentials, account passwords, access tokens, or private broker secrets

---

## 3. Production Verdict and Implementation Rule

The data module shall be implemented as a **greenfield professional production module**.

The implementation must be a clean production implementation that preserves required capabilities through professional boundaries, explicit contracts, safe official exports, deterministic validation, complete tests, and operational documentation.

### 3.1 Functional Preservation Rule

Current functionality must be preserved as capabilities, not necessarily as old function names.

For example:

```text
Old capability: load data from CSV
New design: expose get_market_data(source="csv") and save_market_data(source="csv") where appropriate.
```

```text
Old capability: list MT5 symbols with credentials
New design: expose list_symbols(source="mt5") and keep credential resolution internal.
```

```text
Old capability: create/start/stop scheduled updater
New design: expose explicit scheduler tools with medium risk classification and clear lifecycle contracts.
```

### 3.2 No Backward Compatibility Rule

Backward compatibility is not required.

The module defines the canonical API through:

```text
tools/data/__init__.py
```

Downstream modules must integrate with this v8 API directly. Compatibility aliases are intentionally not part of the data module.

---

## 4. Canonical Architecture

### 4.1 Target Folder Structure

```text
tools/
    data/
        __init__.py
        contracts.py
        responses.py
        errors.py
        constants.py
        validation.py
        normalization.py
        quality.py
        timeframes.py
        cache.py
        registry.py

        sources/
            __init__.py
            base.py
            csv_source.py
            parquet_source.py
            mt5_source.py
            ctrader_source.py
            dukascopy_source.py
            binance_source.py

        storage/
            __init__.py
            csv_store.py
            parquet_store.py
            path_policy.py

        transforms/
            __init__.py
            resampling.py
            alignment.py
            aggregation.py

        generators/
            __init__.py
            synthetic_ticks.py
            synthetic_bars.py
            gbm.py

        labeling/
            __init__.py
            lexlb.py

        scheduler/
            __init__.py
            updater.py
            jobs.py
            state.py

tests/
    unit/
        tools/
            data/
                test_contracts.py
                test_responses.py
                test_validation.py
                test_normalization.py
                test_quality.py
                test_timeframes.py
                test_cache.py
                test_registry.py
                test_init_exports.py

                sources/
                    test_base.py
                    test_csv_source.py
                    test_parquet_source.py
                    test_mt5_source.py
                    test_ctrader_source.py
                    test_dukascopy_source.py
                    test_binance_source.py

                storage/
                    test_csv_store.py
                    test_parquet_store.py
                    test_path_policy.py

                transforms/
                    test_resampling.py
                    test_alignment.py
                    test_aggregation.py

                generators/
                    test_synthetic_ticks.py
                    test_synthetic_bars.py
                    test_gbm.py

                labeling/
                    test_lexlb.py

                scheduler/
                    test_updater.py
                    test_jobs.py
                    test_state.py

    usage/
        tools/
            data/
                market_data.py
                local_storage.py
                source_symbols.py
                synthetic_generation.py
                labeling.py
                scheduler.py
```

### 4.2 Architecture Layers

The module has six layers:

| Layer | Purpose |
|---|---|
| Official AI Tool Layer | Agent-callable functions exported from `tools/data/__init__.py` |
| Service/Orchestration Layer | Small internal functions that coordinate validation, source selection, cache, normalization, and responses |
| Source Adapter Layer | Source-specific implementations for CSV, Parquet, MT5, cTrader, Dukascopy, Binance/symbol discovery |
| Contract Layer | Typed dataclasses/Pydantic models/enums for requests, records, metadata, quality results, cache keys |
| Transformation Layer | Resampling, alignment, aggregation, labeling, synthetic generation |
| Storage and Cache Layer | Safe local persistence, cache keys, cache read/write, file path policy |

### 4.3 Boundary Rule

Official tools are thin and agent-facing. They validate user/tool inputs, call internal services/adapters, and return standard responses.

Internal adapters may use pandas, NumPy, broker SDKs, HTTP clients, MCP clients, and file system objects. These must not leak across the official AI tool boundary.

---

## 5. Official AI Tool Surface

The v8 module must expose a smaller, clearer official tool surface. These are the canonical agent-callable tools.

### 5.1 Required Official Tools

`tools/data/__init__.py` must export only the following official AI tools unless a future spec version explicitly adds more:

```python
__all__ = [
    "get_market_data",
    "get_tick_data",
    "get_spread_data",
    "get_symbol_metadata",
    "list_symbols",
    "get_data_availability",
    "get_market_hours",
    "get_trading_sessions",
    "get_historical_volume",
    "save_market_data",
    "load_local_dataset",
    "resample_ohlcv",
    "align_multitimeframe_data",
    "generate_synthetic_ticks",
    "generate_synthetic_bars",
    "aggregate_ticks_to_bars",
    "label_market_data",
    "create_data_update_job",
    "start_data_update_job",
    "stop_data_update_job",
    "run_data_update_job_once",
    "clear_data_cache",
]
```



### 5.1A Production Official Tool Matrix

The following table is the canonical v8 official tool surface. Only these tools should be exported from `tools/data/__init__.py` unless a future specification version approves additional exports.

| Tool | Purpose | Risk | Read Only | Writes File | Requires Network | Required Tests |
|---|---|---:|---:|---:|---:|---|
| `get_market_data` | Fetch normalized OHLCV bars | low | yes | no | source-dependent | success, invalid input, source failure, empty result, quality warnings, schema |
| `get_tick_data` | Fetch normalized tick records | low | yes | no | source-dependent | success, invalid input, source failure, schema, timestamp normalization |
| `get_spread_data` | Fetch or derive spread records/statistics | low | yes | no | source-dependent | success, missing spread, invalid source, schema |
| `get_symbol_metadata` | Fetch symbol contract metadata | low | yes | no | source-dependent | success, missing symbol, invalid source, schema |
| `list_symbols` | List tradable or available symbols | low | yes | no | source-dependent | success, source unavailable, filtering, schema |
| `get_data_availability` | Inspect available data ranges | low | yes | no | source-dependent | success, no data, invalid date range, schema |
| `get_market_hours` | Return market hours for symbol/source | low | yes | no | source-dependent | success, unknown symbol, timezone correctness |
| `get_trading_sessions` | Return normalized trading session windows | low | yes | no | source-dependent | success, invalid timezone, weekend/session handling |
| `get_historical_volume` | Return volume history/summary | low | yes | no | source-dependent | success, empty volume, invalid timeframe, schema |
| `save_market_data` | Save validated data to approved local storage | medium | no | yes | no | success, unsafe path, invalid data, overwrite policy |
| `load_local_dataset` | Load local CSV/Parquet dataset | low | yes | no | no | success, missing file, unsafe path, invalid schema |
| `resample_ohlcv` | Resample OHLCV records | low | yes | no | no | success, invalid timeframe, aggregation correctness |
| `align_multitimeframe_data` | Align multiple timeframe datasets | low | yes | no | no | success, missing base timeframe, alignment correctness |
| `generate_synthetic_ticks` | Generate deterministic synthetic ticks | low | yes | no | no | seed determinism, invalid parameters, schema |
| `generate_synthetic_bars` | Generate deterministic synthetic bars | low | yes | no | no | seed determinism, OHLC validity, schema |
| `aggregate_ticks_to_bars` | Aggregate ticks into OHLCV bars | low | yes | no | no | aggregation correctness, empty ticks, timestamp bins |
| `label_market_data` | Apply deterministic market labels | low | yes | no | no | success, invalid labeler, no lookahead, schema |
| `create_update_job` | Create scheduled update job definition/state | medium | no | yes | optional | idempotency, duplicate job, invalid schedule |
| `start_update_job` | Start or enable scheduled update job | medium | no | yes | optional | idempotency, unavailable scheduler, permission policy |
| `stop_update_job` | Stop or disable scheduled update job | medium | no | yes | optional | idempotency, missing job, state correctness |
| `get_update_job_status` | Inspect scheduled update job status | low | yes | no | no | success, missing job, schema |
| `clear_data_cache` | Clear approved cache entries | medium | no | yes | no | target scope, unsafe path, dry-run, idempotency |

All tools must include `request_id`, standard metadata, deterministic error codes, and execution timing.

### 5.2 Tool Classification

| Tool | Risk | Read-only | Writes file | Requires network | Purpose |
|---|---|---:|---:|---:|---|
| `get_market_data` | low | yes | no | source-dependent | Fetch normalized OHLCV bars |
| `get_tick_data` | low | yes | no | source-dependent | Fetch normalized tick data |
| `get_spread_data` | low | yes | no | source-dependent | Fetch normalized spread data |
| `get_symbol_metadata` | low | yes | no | source-dependent | Fetch symbol contract/session metadata |
| `list_symbols` | low | yes | no | source-dependent | List available symbols for a source |
| `get_data_availability` | low | yes | no | source-dependent | Inspect available date ranges/counts |
| `get_market_hours` | low | yes | no | source-dependent | Return market hours for symbol/source |
| `get_trading_sessions` | low | yes | no | source-dependent | Return session windows and session labels |
| `get_historical_volume` | low | yes | no | source-dependent | Return historical volume summary |
| `save_market_data` | medium | no | yes | no | Save normalized data to CSV/Parquet |
| `load_local_dataset` | low | yes | no | no | Load local CSV/Parquet dataset |
| `resample_ohlcv` | low | yes | no | no | Resample bars to target timeframe |
| `align_multitimeframe_data` | low | yes | no | no | Align multiple timeframe datasets |
| `generate_synthetic_ticks` | low | yes | no | no | Generate synthetic tick stream |
| `generate_synthetic_bars` | low | yes | no | no | Generate synthetic OHLCV bars |
| `aggregate_ticks_to_bars` | low | yes | no | no | Aggregate ticks into OHLCV bars |
| `label_market_data` | low | yes | no | no | Generate deterministic labels for model/research workflows |
| `create_data_update_job` | medium | no | yes | source-dependent | Create scheduled update job definition |
| `start_data_update_job` | medium | no | yes | source-dependent | Start scheduled updater lifecycle |
| `stop_data_update_job` | medium | no | yes | no | Stop scheduled updater lifecycle |
| `run_data_update_job_once` | medium | no | yes | source-dependent | Run one controlled update cycle |
| `clear_data_cache` | medium | no | yes/delete | no | Clear cache records safely |

### 5.3 What Is Intentionally Internal

The following capabilities must exist, but should remain internal unless future design requires exposure:

- source-specific raw fetch functions
- source-specific normalization helpers
- MT5 credential loading
- MT5 client construction
- cTrader client construction
- Dukascopy instrument lookup internals
- cache key builders
- cache file path builders
- cache get/set internals
- path safety helpers
- timezone coercion helpers
- DataFrame conversion helpers
- bar aggregation classes if not directly agent-safe
- timeframe manager classes if not directly agent-safe

---

## 6. Standard Tool Response Contract

Every official AI tool must return the exact standard top-level schema:

```python
{
    "status": "success" | "error",
    "message": str,
    "data": Any,
    "error": None | {
        "code": str,
        "details": str,
    },
    "metadata": {
        "tool_name": str,
        "tool_version": str,
        "tool_category": "data",
        "tool_risk_level": "low" | "medium" | "high" | "critical",
        "request_id": str | None,
        "execution_ms": float,
        "read_only": bool,
        "writes_file": bool,
        "modifies_database": bool,
        "places_trade": bool,
        "requires_network": bool,
    },
}
```

### 6.1 Data Payload Contract for Market Data

`get_market_data` must return `data` in this shape:

```python
{
    "records": list[dict],
    "record_count": int,
    "symbol": str,
    "timeframe": str,
    "source": str,
    "start": str | None,
    "end": str | None,
    "timestamp_timezone": "UTC",
    "source_timezone": str | None,
    "schema_version": str,
    "quality": {
        "status": "pass" | "warn" | "fail",
        "warnings": list[str],
        "errors": list[str],
        "metrics": dict,
    },
    "source_metadata": dict,
}
```

### 6.2 OHLCV Record Contract

Every normalized OHLCV record must use this schema:

```python
{
    "timestamp": "2026-05-31T10:00:00Z",
    "open": 1.2345,
    "high": 1.2360,
    "low": 1.2330,
    "close": 1.2350,
    "volume": 1234.0,
    "tick_volume": 1234.0 | None,
    "real_volume": 1234.0 | None,
    "spread": 0.00012 | None,
    "source": "mt5" | "csv" | "parquet" | "dukascopy" | "ctrader" | "synthetic",
    "symbol": "EURUSD",
    "timeframe": "H1",
}
```

Required invariants:

```text
high >= max(open, close, low)
low <= min(open, close, high)
volume >= 0 when volume is present
tick_volume >= 0 when tick_volume is present
real_volume >= 0 when real_volume is present
spread >= 0 when spread is present
timestamp must be UTC ISO 8601 after normalization
records must be sorted ascending by timestamp
```

### 6.3 Tick Record Contract

Every normalized tick record must use this schema:

```python
{
    "timestamp": "2026-05-31T10:00:00.123Z",
    "bid": 1.2344 | None,
    "ask": 1.2346 | None,
    "last": 1.2345 | None,
    "volume": 1.0 | None,
    "spread": 0.0002 | None,
    "source": "mt5" | "dukascopy" | "ctrader" | "synthetic",
    "symbol": "EURUSD",
}
```

Required invariants:

```text
at least one of bid, ask, last must be present
ask >= bid when both bid and ask are present
spread = ask - bid when bid and ask are present unless source provides a known spread field
volume >= 0 when present
timestamp must be UTC ISO 8601 after normalization
records must be sorted ascending by timestamp
```

### 6.4 Symbol Metadata Contract

`get_symbol_metadata` must return source-normalized metadata:

```python
{
    "symbol": str,
    "source": str,
    "asset_class": "forex" | "metal" | "index" | "crypto" | "commodity" | "equity" | "unknown",
    "base_currency": str | None,
    "quote_currency": str | None,
    "contract_size": float | None,
    "tick_size": float | None,
    "tick_value": float | None,
    "point": float | None,
    "digits": int | None,
    "min_lot": float | None,
    "max_lot": float | None,
    "lot_step": float | None,
    "margin_currency": str | None,
    "profit_currency": str | None,
    "trading_hours": dict | None,
    "source_metadata": dict,
}
```

### 6.5 Spread Record Contract

`get_spread_data` must return spread as a first-class time-series contract, not only as an optional OHLCV field.

Every normalized spread record must use this schema:

```python
{
    "timestamp": "2026-05-31T10:00:00.000Z",
    "symbol": "EURUSD",
    "bid": 1.2344 | None,
    "ask": 1.2346 | None,
    "spread_points": 2.0 | None,
    "spread_pips": 0.2 | None,
    "source": "mt5" | "csv" | "parquet" | "dukascopy" | "ctrader" | "synthetic",
}
```

Required invariants:

```text
timestamp must be UTC ISO 8601 after normalization
ask >= bid when both are present
at least one of spread_points, spread_pips, or bid/ask must be available
spread values must be non-negative when present
records must be sorted ascending by timestamp
```

### 6.6 Data Availability Response Contract

`get_data_availability` must return a stable contract that downstream modules can use before fetching large datasets.

```python
{
    "symbol": str,
    "source": str,
    "data_kind": "ohlcv" | "tick" | "spread" | "volume" | "metadata",
    "timeframe": str | None,
    "start": str | None,
    "end": str | None,
    "record_count": int | None,
    "available_ranges": list[dict[str, str]],
    "gaps": list[dict[str, str]],
    "is_complete": bool | None,
    "source_metadata": dict,
}
```

Gap objects must use UTC ISO 8601 timestamps:

```python
{"start": "2026-01-01T00:00:00Z", "end": "2026-01-01T01:00:00Z", "reason": "missing_records"}
```

### 6.7 Historical Volume Response Contract

`get_historical_volume` must return a volume-specific payload. It may derive volume from OHLCV records, tick records, or source-native volume data.

```python
{
    "symbol": str,
    "source": str,
    "timeframe": str | None,
    "start": str | None,
    "end": str | None,
    "volume_kind": "tick_volume" | "real_volume" | "contract_volume" | "unknown",
    "records": list[dict],
    "total_volume": float | None,
    "average_volume": float | None,
    "record_count": int,
    "source_metadata": dict,
}
```

Each volume record must include:

```python
{
    "timestamp": str,
    "volume": float,
    "tick_volume": float | None,
    "real_volume": float | None,
}
```

### 6.8 Market Hours and Trading Session Contracts

`get_market_hours` and `get_trading_sessions` must return timezone-aware data. All returned `start` and `end` fields must be UTC ISO 8601 strings. Original source or broker timezone must be retained in metadata.

Trading session objects must use this shape:

```python
{
    "session_name": "asia" | "london" | "new_york" | "custom",
    "start": "2026-05-31T00:00:00Z",
    "end": "2026-05-31T08:00:00Z",
    "original_timezone": str,
    "is_open": bool | None,
    "source": str,
}
```

Phase 1 limitation: `get_market_hours` may return current configured hours only. Historical changes for holidays, daylight-saving shifts, and broker-specific session changes are optional until the market-calendar integration phase. The response must clearly mark this limitation in `source_metadata["historical_hours_supported"]`.

### 6.9 Source Metadata Standard

Every response containing `source_metadata` should include these keys when available:

```python
{
    "source_version": str | None,
    "request_id": str | None,
    "response_time_ms": float | None,
    "broker_timezone": str | None,
    "source_timezone": str | None,
    "terminal_path": str | None,
    "rate_limit_remaining": int | None,
    "historical_hours_supported": bool | None,
}
```

Sensitive values such as passwords, access tokens, full credential payloads, and raw account secrets must never appear in `source_metadata`.

---

## 7. Core Contracts and Enums

The file `tools/data/contracts.py` must define the core data contracts.

Recommended contracts:

```python
DataSource
DataKind
Timeframe
AssetClass
QualityStatus
CachePolicy
MarketDataRequest
TickDataRequest
SpreadDataRequest
SymbolMetadataRequest
DataAvailabilityRequest
SaveMarketDataRequest
LocalDatasetRequest
DataQualityReport
OHLCVRecord
TickRecord
SpreadRecord
SymbolMetadata
MarketDataPayload
TickDataPayload
ToolResponse
```

### 7.1 DataSource Enum

```python
class DataSource(str, Enum):
    CSV = "csv"
    PARQUET = "parquet"
    MT5 = "mt5"
    CTRADER = "ctrader"
    DUKASCOPY = "dukascopy"
    BINANCE = "binance"
    SYNTHETIC = "synthetic"
```

### 7.2 Timeframe Enum

Minimum supported timeframes:

```text
TICK
S1
M1
M5
M15
M30
H1
H4
D1
W1
MN1
```

### 7.3 DataKind Enum

```text
ohlcv
tick
spread
metadata
availability
sessions
volume
```

---



## 7A. Production Request Contracts

Every official tool must validate external inputs before calling internal adapters. Tools may accept simple Python arguments, but internally they must be normalized into typed request contracts.

### 7A.1 MarketDataRequest

Required fields:

```python
symbol: str
source: DataSource
timeframe: Timeframe
start: str | None
end: str | None
limit: int | None
cache_ttl_seconds: int | None
source_timezone: str | None
request_id: str | None
```

Validation rules:

```text
- symbol must be a non-empty normalized trading symbol.
- source must be supported and enabled.
- timeframe must be valid for OHLCV data.
- start and end must be UTC ISO 8601 when provided.
- start must be before end.
- limit must be positive and within the configured maximum for the requested data kind.
- source_timezone, when provided, must be a valid IANA timezone and overrides adapter timezone detection for naive timestamps.
- cache_ttl_seconds, when provided, must be non-negative and must not exceed configured maximum TTL.
- either date range or limit must be provided unless the source has a safe default.
```

### 7A.2 TickDataRequest

Required fields:

```python
symbol: str
source: DataSource
start: str | None
end: str | None
limit: int | None
cache_ttl_seconds: int | None
source_timezone: str | None
request_id: str | None
```

Validation rules:

```text
- date range is preferred for historical tick retrieval.
- source must explicitly support ticks.
- limit must be bounded to prevent excessive memory usage.
- source_timezone, when provided, must be a valid IANA timezone and overrides adapter timezone detection for naive timestamps.
- cache_ttl_seconds, when provided, must be non-negative and must not exceed configured maximum TTL.
- tick timestamps must normalize to UTC before returning.
```

### 7A.3 StorageRequest

Required fields:

```python
path: str
format: "csv" | "parquet"
overwrite: bool
request_id: str | None
```

Validation rules:

```text
- path must resolve under an approved storage root.
- parent directories may be created only by explicit storage tools.
- overwrite=False must fail if the target exists.
- extension must match the requested format.
```

### 7A.4 SchedulerJobRequest

Required fields:

```python
job_name: str
source: DataSource
symbol: str
timeframe: Timeframe | None
schedule: str
storage_target: str
request_id: str | None
```

Validation rules:

```text
- job_name must be stable, non-empty, and safe for file/database keys.
- schedule must be parseable and bounded.
- job must include source, symbol, destination, and data kind.
- duplicate job creation must be idempotent or return a deterministic duplicate error.
```


## 7B. Industry-Grade Production Contracts

These contracts are mandatory for production implementation. They prevent silent data drift, precision mismatch, ambiguous timestamp repair, unsafe network retry behavior, missing asset metadata, and license misuse.

### 7B.1 Raw Data Versioning and Source Revision Tracking

Historical data providers may revise prior data because of tick corrections, broker session adjustments, corporate-action retrofits, vendor restatements, or source-side repair. The data module must treat source revision as part of data identity.

Required enum:

```python
class DataVersionPolicy(str, Enum):
    STRICT = "strict"
    WARN_AND_REVALIDATE = "warn_and_revalidate"
    IGNORE = "ignore"
```

Required contract:

```python
@dataclass(frozen=True)
class SourceRevisionMetadata:
    raw_data_hash: str | None
    source_update_timestamp: str | None
    revision_policy: DataVersionPolicy = DataVersionPolicy.WARN_AND_REVALIDATE
```

Rules:

- Source adapters should compute `raw_data_hash` as SHA-256 of the raw source payload when feasible.
- Cache keys must include `raw_data_hash` when available.
- If a source returns a different `raw_data_hash` for the same symbol, timeframe, source, and date range, the cache must be invalidated.
- The event must be logged with `DATA_SOURCE_REVISION_DETECTED`.
- For production backtest, validation, and execution-bound workflows, `STRICT` or `WARN_AND_REVALIDATE` is required.
- `IGNORE` is allowed only for exploratory research and must be visible in metadata.

### 7B.2 Precision and Rounding Enforcement

Normalized price and volume values must be precision-aligned before leaving adapters. This is required for reliable simulation, risk, execution sizing, and broker comparison.

Required enum and policy:

```python
class PrecisionMode(str, Enum):
    SYMBOL_TICK_SIZE = "symbol_tick_size"
    FIXED_DECIMAL = "fixed_decimal"
    RAW_SOURCE = "raw_source"

@dataclass(frozen=True)
class PrecisionPolicy:
    price_precision: PrecisionMode = PrecisionMode.SYMBOL_TICK_SIZE
    volume_precision: PrecisionMode = PrecisionMode.FIXED_DECIMAL
    max_decimals: int = 10
    rounding_mode: Literal[
        "ROUND_HALF_EVEN",
        "ROUND_DOWN",
        "ROUND_UP",
    ] = "ROUND_HALF_EVEN"
```

Rules:

- Prices should be quantized to symbol tick size when symbol metadata provides a valid tick size.
- Volumes should be quantized according to volume step, lot step, contract size, or configured fixed decimal rules.
- `RAW_SOURCE` is allowed only when no precision metadata exists and the workflow is not execution-bound.
- Mismatched precision must emit `PRECISION_MISMATCH`.
- Execution-bound workflows must fail closed on precision mismatch.
- Internal numeric implementation may use `Decimal` where deterministic quantization is required; JSON tool output may serialize final values as strings or floats according to the public contract, but precision metadata must disclose the applied policy.

### 7B.3 Timestamp Gap and Overlap Resolution

The module must not only detect gaps and overlaps; it must define how they are resolved. DST changes, broker session transitions, exchange halts, vendor interruptions, and repeated ticks can create ambiguous time series.

Required enums:

```python
class GapResolutionPolicy(str, Enum):
    FAIL = "fail"
    FORWARD_FILL = "forward_fill"
    STRICT_NAN = "strict_nan"
    INTERPOLATE = "interpolate"

class OverlapPolicy(str, Enum):
    KEEP_FIRST = "keep_first"
    KEEP_LAST = "keep_last"
    MERGE_AVERAGE = "merge_average"
    FAIL = "fail"
```

Production defaults:

```text
GapResolutionPolicy = STRICT_NAN
OverlapPolicy = KEEP_LAST
```

Rules:

- Forward-fill and interpolation must be explicitly requested and logged.
- `INTERPOLATE` is research-only and must not be used for production backtesting, validation evidence, risk approval, or execution-bound workflows.
- Duplicate timestamps must use the configured `OverlapPolicy`.
- If no safe resolution is possible, return `TIMESTAMP_OVERLAP` or `VALIDATION_FAILED`.
- Gap and overlap decisions must appear in the data quality report.

### 7B.4 Deterministic Rate-Limit and Backoff Strategy

Network-backed sources must use deterministic rate-limit control. Immediate retry loops are forbidden.

Required config and protocol:

```python
@dataclass(frozen=True)
class RateLimitConfig:
    max_requests_per_second: float
    max_requests_per_minute: int
    max_concurrent_connections: int = 1
    backoff_policy: Literal["fixed", "exponential", "jittered"] = "exponential"
    max_backoff_seconds: int = 30

class RateLimitTracker(Protocol):
    def can_request(self, source: DataSource) -> bool: ...
    def record_request(self, source: DataSource, status: int) -> None: ...
    def wait_time_seconds(self, source: DataSource) -> float: ...
```

Rules:

- Every network adapter must check `can_request()` before fetching.
- HTTP 429 or source-specific throttling must return or log `RATE_LIMIT_EXCEEDED`.
- Retry behavior must use configured backoff and respect `max_backoff_seconds`.
- Adapters must never retry immediately after throttling.
- Rate-limit metadata should include remaining quota when the source provides it.

### 7B.5 Asset-Specific Metadata Extensions

Generic symbol metadata is not sufficient for all asset classes. The module must support asset-specific extensions without bloating the base contract.

Required protocol and example contracts:

```python
class AssetMetadataExtension(Protocol):
    def get_futures_extension(self) -> FuturesMetadata | None: ...
    def get_options_extension(self) -> OptionsMetadata | None: ...
    def get_bond_extension(self) -> BondMetadata | None: ...

@dataclass(frozen=True)
class FuturesMetadata:
    expiry: str
    contract_multiplier: Decimal
    tick_size: Decimal
    first_notice_date: str | None

@dataclass(frozen=True)
class OptionsMetadata:
    strike: Decimal
    expiry: str
    style: Literal["european", "american"]
    multiplier: Decimal
```

Rules:

- If `asset_class` requires extension fields and those fields are missing, emit `MISSING_ASSET_METADATA`.
- Missing required asset metadata must downgrade data realism and validation confidence.
- Futures and options contracts must include expiry and multiplier when used for backtesting, risk, or execution-bound workflows.
- FX and spot crypto may use the base `SymbolMetadata` contract plus precision metadata.

### 7B.6 Data Licensing and Attribution Tracking

Every source must disclose license metadata where known. This prevents illegal redistribution and unsafe artifact exports.

Required contract:

```python
@dataclass(frozen=True)
class DataLicenseMetadata:
    license_type: str
    attribution_required: bool
    redistribution_allowed: bool
    vendor: str
    terms_url: str | None
```

Rules:

- `source_metadata` must include a `license` object when the source is external or vendor-provided.
- If `redistribution_allowed=False`, storage and scheduler tools must block export to external paths.
- License restriction failures must return `LICENSE_RESTRICTION`.
- Attribution requirements must be preserved in generated reports, datasets, and metadata manifests.

### 7B.7 Downstream Contract Alignment Gate

The data module must not drift from simulation, optimization, analytics, risk, portfolio, and execution contracts.

Required test file:

```text
tests/integration/tools/data/test_contract_alignment.py
```

Minimum assertions:

- `OHLCVRecord` fields align with simulation bar contracts.
- `TickRecord` fields align with simulation tick contracts.
- Timestamp timezone, sorting, precision, and gap policies are identical or explicitly transformed.
- Any divergence requires a named adapter transformation and audit log.
- Strategy, simulation, risk, and execution modules must not guess field meanings.


## 8. Source Adapter Standard

Every source adapter must implement a common internal protocol in `tools/data/sources/base.py`.

### 8.1 Base Adapter Interface

```python
class MarketDataSource(Protocol):
    source_name: DataSource

    def list_symbols(self, request: SymbolListRequest) -> SourceResult: ...
    def get_ohlcv(self, request: MarketDataRequest) -> SourceResult: ...
    def get_ticks(self, request: TickDataRequest) -> SourceResult: ...
    def get_spread(self, request: SpreadDataRequest) -> SourceResult: ...
    def get_symbol_metadata(self, request: SymbolMetadataRequest) -> SourceResult: ...
    def get_data_availability(self, request: DataAvailabilityRequest) -> SourceResult: ...
```

Adapters may raise internal exceptions, but official tools must convert them into standard error responses.

### 8.2 Adapter Responsibilities

Each adapter must:

- validate source-specific requirements
- fetch or load raw source data
- convert raw fields into internal records
- preserve source metadata
- avoid logging secrets
- map source errors to deterministic internal errors
- avoid returning raw SDK/client objects
- expose no direct official AI tool functions

### 8.3 Source Registry

`tools/data/registry.py` must provide source lookup.

Recommended functions:

```python
get_source_adapter(source: DataSource) -> MarketDataSource
register_source_adapter(source: DataSource, adapter: MarketDataSource) -> None
list_registered_sources() -> list[str]
```

The source registry is internal. It should not be exported as an official AI tool unless future requirements demand it.

---

## 9. Source-Specific Requirements

### 9.1 CSV Source

The CSV source must support:

- loading OHLCV records from CSV
- loading tick records from CSV when columns allow
- saving normalized records to CSV through storage layer
- configurable timestamp column
- configurable delimiter when needed
- column alias mapping
- strict path safety
- optional date range filtering
- data quality validation after load

Required supported column aliases:

```text
timestamp: timestamp, time, datetime, date
open: open, Open, o
high: high, High, h
low: low, Low, l
close: close, Close, c
volume: volume, Volume, tick_volume, real_volume, v
spread: spread, Spread
bid: bid, Bid
ask: ask, Ask
last: last, Last, price
```

### 9.2 Parquet Source

The Parquet source must support:

- loading OHLCV/tick records from Parquet
- saving normalized records to Parquet
- preserving schema metadata where possible
- date range filtering
- safe path validation
- validation after load

Parquet is the preferred local storage format for larger datasets.

### 9.3 MT5 Source

The MT5 source must support:

- secure credential resolution from environment/config, not user-visible tool args
- MT5 terminal path handling
- connection lifecycle management
- list symbols
- get OHLCV bars
- get tick data where available
- get symbol metadata/details
- map MT5 timeframes to HaruQuant timeframes
- normalize broker timestamps to UTC
- preserve broker/source timezone metadata
- return clear broker unavailable errors

MT5 tools are read-only in this module. They must not place orders, close positions, modify account state, or change terminal settings.

Credential rules:

```text
Do not expose get_mt5_credentials as an official AI tool.
Do not return passwords or account secrets in any tool response.
Do not log login/password/server secrets.
Credential resolution belongs inside the adapter/client layer.
```

### 9.4 cTrader Source

The cTrader source must support:

- client boundary through the approved cTrader adapter/MCP mechanism
- list symbols
- load bars
- normalize cTrader bars
- map cTrader timeframe names to HaruQuant timeframes
- preserve source metadata
- return network/client errors as standard tool errors

Raw cTrader client construction must remain internal.

### 9.5 Dukascopy Source

The Dukascopy source must support:

- instrument discovery/listing
- instrument metadata lookup internally
- historical OHLCV or tick fetch where implemented
- source-specific interval mapping
- live or stream-oriented fetch where supported
- normalization of source bars/ticks
- robust HTTP/network error handling
- retry/timeouts through internal client policy
- source metadata preservation

The Dukascopy implementation must be split into small files if it becomes large. One oversized file is not acceptable.

Suggested split if needed:

```text
sources/dukascopy_source.py
sources/dukascopy_client.py
sources/dukascopy_instruments.py
sources/dukascopy_normalization.py
sources/dukascopy_live.py
```

### 9.6 Binance or Exchange Symbol Discovery Source

The module must preserve symbol discovery capability equivalent to `binance_data_list_symbols`.

This should be represented as:

```python
list_symbols(source="binance")
```

It must not become a general-purpose trading/execution exchange adapter inside the data module.

### 9.7 Synthetic Source

Synthetic data generation must be represented through dedicated official tools rather than a normal external source adapter unless future design requires source-like behavior.

Required synthetic capabilities:

- generate synthetic tick records
- generate synthetic OHLCV bars
- GBM-style bar generation
- deterministic seed support
- reproducible output when seed is supplied
- configurable drift, volatility, spread, volume behavior, start price, start timestamp, and number of records

---



### 9.8 Source Readiness Levels

Each source adapter must declare its readiness level.

```text
production = implemented, tested, documented, enabled by config, safe error handling
staging = implemented and tested, but not enabled by default
experimental = partial support, disabled by default, must return clear unavailable errors when disabled
not_available = known source type but intentionally disabled or not yet implemented
```

Official tools must include source readiness in metadata when source-specific behavior is involved.

### 9.9 Source Fallback Rule

Source fallback is never silent.

If the caller requests `source="mt5"`, the tool must not silently fallback to CSV, Parquet, Dukascopy, or synthetic data. Any fallback must be explicit in the request, such as:

```python
fallback_sources=["parquet", "csv"]
```

When fallback is used, the response metadata must include:

```text
requested_source
actual_source
fallback_used
fallback_reason
```

### 9.10 Source Capability Declaration

Each adapter must expose an internal capability declaration:

```python
supports_ohlcv: bool
supports_ticks: bool
supports_spread: bool
supports_symbol_metadata: bool
supports_market_hours: bool
supports_streaming: bool
supports_writes: bool
requires_credentials: bool
requires_network: bool
```

Official tools must check capability declarations before execution. Unsupported operations must return `UNSUPPORTED_OPERATION`, not `UNKNOWN_ERROR`.

## 10. Data Quality Policy

Data quality validation is mandatory before data is returned to strategy, simulation, analytics, risk, portfolio, or agent workflows.

### 10.1 Required OHLCV Checks

The validator must check:

- missing required columns
- invalid numeric types
- missing timestamps
- duplicate timestamps
- out-of-order timestamps
- non-UTC or naive timestamps after normalization
- `high < open`
- `high < close`
- `high < low`
- `low > open`
- `low > close`
- negative volume
- negative spread
- zero or negative prices where invalid
- large timestamp gaps relative to timeframe
- unexpected weekend/session gaps when session policy disallows them
- incomplete final candle flag
- stale data flag
- partial data flag
- source metadata missing

### 10.2 Required Tick Checks

The validator must check:

- missing timestamp
- duplicate timestamp handling
- out-of-order ticks
- all price fields missing
- `ask < bid`
- negative spread
- negative volume
- stale tick timestamp
- partial tick fields

### 10.3 Quality Status Rules

Quality result must be one of:

```text
pass = data is suitable for normal downstream use
warn = data can be used, but warnings must be visible
fail = data must not be used unless caller explicitly allows failed quality data
```

Official tools must default to:

```python
fail_on_quality_error=True
```

If `fail_on_quality_error=False`, the response may return `status="success"` with `quality.status="fail"`, but the message must clearly state that the data failed validation.

### 10.4 Data Quality Report Shape

```python
{
    "status": "pass" | "warn" | "fail",
    "warnings": list[str],
    "errors": list[str],
    "metrics": {
        "record_count": int,
        "duplicate_timestamps": int,
        "missing_timestamps": int,
        "out_of_order_records": int,
        "gap_count": int,
        "max_gap_seconds": float | None,
        "negative_volume_count": int,
        "negative_spread_count": int,
        "ohlc_inconsistency_count": int,
        "stale": bool,
        "partial": bool,
    },
}
```

---

## 11. Timestamp, Timezone, and Broker-Time Policy

Timestamps are critical for trading correctness.

### 11.1 Internal Timestamp Rule

```text
All normalized internal timestamps must be UTC ISO 8601 strings at the official AI tool boundary.
```

### 11.2 Source Timezone Rule

Every payload must preserve:

```text
timestamp_timezone = "UTC"
source_timezone = original source timezone if known
broker_timezone = broker timezone if applicable
```

### 11.3 Naive Timestamp Rule

Naive timestamps may only exist inside source adapters before normalization.

Official tools must not return naive timestamps.

### 11.4 Session Calculations

Trading session calculations must declare the timezone used.

Session outputs must include:

```python
{
    "session_name": str,
    "start": str,
    "end": str,
    "timezone": str,
    "is_open": bool,
    "source": str,
}
```

---

## 12. Cache Policy

The cache system must be deterministic, transparent, and safe.

### 12.1 Cache Key Rule

Cache identity must include source revision metadata where available. `raw_data_hash` is part of the cache identity when provided by the source adapter. Silent cache hits on revised source data are forbidden.


Cache keys must include:

- source
- data kind
- symbol
- timeframe
- start
- end
- normalization version
- schema version
- important request flags

Example logical key:

```text
source=mt5|kind=ohlcv|symbol=EURUSD|tf=H1|start=2026-01-01|end=2026-02-01|schema=1.0.0|norm=1.0.0
```

### 12.2 Cache Metadata

Cached records must include:

```python
{
    "cache_key": str,
    "created_at": str,
    "expires_at": str | None,
    "source": str,
    "schema_version": str,
    "record_count": int,
    "quality_status": str,
}
```

### 12.2A Cache Expiry and TTL Policy

Cache expiry must be deterministic and source-aware. Defaults:

```text
historical daily-or-higher data: 86,400 seconds / 1 day
intraday bar data: 3,600 seconds / 1 hour
tick data: 900 seconds / 15 minutes unless source declares stricter freshness
streaming/live data: 0 seconds / no persistent cache by default
local immutable datasets: no expiry unless file modified timestamp changes
```

Official tools may expose `cache_ttl_seconds`. When provided, it overrides the default only if it is non-negative and within the configured maximum TTL.

Cache metadata must include the chosen TTL source:

```python
"ttl_policy": "default" | "request_override" | "source_override" | "disabled"
```

### 12.2B Cache Request ID Propagation

Cache reads, writes, misses, stale-cache decisions, and cache clear operations must include the caller's `request_id` in internal logs where feasible. Cache failures must use the same `request_id` as the parent official tool call.

### 12.3 Stale Cache Rule

Stale cache must never be silently returned.

Default:

```python
allow_stale=False
```

If stale data is returned because `allow_stale=True`, the response must include a warning.

### 12.4 Cache Failure Rule

Cache failure must not corrupt source fetch results.

If source fetch succeeds but cache write fails:

- return source data successfully
- include a warning in metadata or quality report
- log the cache failure

### 12.5 Clear Cache Tool

`clear_data_cache` is a medium-risk official tool because it deletes local artifacts.

It must validate:

- cache namespace
- source filter
- symbol filter
- dry run option
- allowed cache root

It must support:

```python
dry_run: bool = True
```

Default should be dry-run unless the user or workflow explicitly requests deletion.

---

## 13. Storage and Path Safety Policy

Local storage tools must be safe and deterministic.

### 13.1 Allowed Storage Roots

Local dataset paths must be constrained to approved directories, such as:

```text
data/raw/
data/processed/
data/cache/
artifacts/data/
```

The exact roots should be configurable through HaruQuant settings.

### 13.2 Path Validation

Storage functions must reject:

- absolute paths outside allowed roots
- parent traversal using `..`
- hidden/system directories unless explicitly allowed
- unsupported file extensions
- overwrite operations without explicit `overwrite=True`

### 13.3 Save Behavior

`save_market_data` must support:

```text
format = csv | parquet
overwrite = False by default
create_parents = True by default
include_metadata = True by default
```

---

## 14. Resampling, Alignment, and Aggregation

### 14.1 Resampling

`resample_ohlcv` must:

- accept normalized OHLCV records
- validate source timeframe and target timeframe
- prevent downsampling ambiguity where applicable
- aggregate OHLCV correctly
- preserve symbol/source metadata
- recompute quality report

Aggregation rules:

```text
open = first open
high = max high
low = min low
close = last close
volume = sum volume
spread = average or last according to explicit spread_policy
```

The required `spread_policy` values are:

```text
last      = use the final spread value in the target bar
average   = arithmetic average of spread observations
weighted  = volume-weighted average when volume is available; otherwise fail with INVALID_INPUT unless fallback is enabled
```

Default:

```python
spread_policy="average"
```

### 14.2 Multi-Timeframe Alignment

`align_multitimeframe_data` must:

- accept multiple datasets keyed by timeframe
- sort records by timestamp
- align lower timeframe records to higher timeframe context
- prevent lookahead leakage by default
- include alignment method in metadata

Default:

```python
allow_lookahead=False
alignment_method="last_known_closed_bar"
```

### 14.3 Tick Aggregation

`aggregate_ticks_to_bars` must:

- accept normalized tick records
- produce OHLCV records
- support spread aggregation
- support volume aggregation
- reject unsorted/invalid ticks unless repair is explicitly enabled
- report quality warnings

---

## 15. Synthetic Data Generation

Synthetic generation is for testing, examples, simulation validation, and agent workflows that need controlled sample data.

### 15.1 Determinism Rule

All synthetic tools must support:

```python
seed: int | None = None
```

When a seed is supplied, output must be deterministic.

### 15.2 Synthetic Tick Tool

`generate_synthetic_ticks` must support:

- symbol
- start timestamp
- number of ticks
- start price
- average spread
- volatility
- volume behavior
- seed

### 15.3 Synthetic Bar Tool

`generate_synthetic_bars` must support:

- symbol
- timeframe
- start timestamp
- number of bars
- start price
- drift
- volatility
- spread behavior
- volume behavior
- seed

### 15.4 GBM Rule

GBM-style generation must be available through `generate_synthetic_bars` using:

```python
method="gbm"
```

This avoids exposing multiple overlapping generator tools.

---

## 16. Labeling Policy

`label_market_data` must provide deterministic labeling suitable for research and model preparation.

Required support:

- LEXLB-style labels or equivalent current labeling method
- configurable lookahead horizon
- configurable threshold
- no lookahead leakage beyond declared horizon
- input validation for horizon/threshold
- output labels aligned to input timestamps
- metadata describing label method and parameters

The tool must not claim predictive value. It only labels historical data according to deterministic rules.

---

## 17. Scheduler Policy

Scheduled data updates are useful but side-effecting. They must be separated from low-risk read tools.

### 17.1 Required Scheduler Tools

```python
create_data_update_job
start_data_update_job
stop_data_update_job
run_data_update_job_once
```

### 17.2 Risk Classification

Scheduler tools are `medium` risk because they may:

- create job configuration files
- write/update local data files
- trigger network data fetches
- modify local scheduler state

They must not:

- place trades
- modify risk settings
- start live execution
- bypass cache/path policy

### 17.3 Job Contract

A data update job must include:

```python
{
    "job_id": str,
    "source": str,
    "symbols": list[str],
    "timeframes": list[str],
    "start": str | None,
    "end": str | None,
    "storage_format": "csv" | "parquet",
    "storage_path": str,
    "schedule": str | None,
    "enabled": bool,
    "created_at": str,
    "updated_at": str,
}
```

### 17.4 Scheduler State

Scheduler state must be explicit and persistable:

```text
created
running
stopped
failed
completed
```

### 17.5 Idempotency

Starting an already running job must return a clear success or error based on policy, not create duplicate workers silently.

---

## 18. Error Codes

Official data tools must use deterministic error codes.

Required codes:

```text
INVALID_INPUT
UNSUPPORTED_SOURCE
UNSUPPORTED_TIMEFRAME
UNSUPPORTED_OPERATION
SOURCE_NOT_CONFIGURED
LIMIT_EXCEEDED
DATA_NOT_FOUND
EMPTY_RESULT
DATA_QUALITY_FAILED
STALE_DATA
PARTIAL_DATA
CACHE_ERROR
CACHE_MISS
CACHE_STALE
PATH_NOT_ALLOWED
FILE_NOT_FOUND
FILE_ALREADY_EXISTS
FILE_WRITE_FAILED
SOURCE_UNAVAILABLE
BROKER_UNAVAILABLE
NETWORK_ERROR
TIMEOUT
CREDENTIALS_MISSING
AUTHENTICATION_FAILED
PERMISSION_DENIED
SCHEDULER_ERROR
JOB_NOT_FOUND
TOOL_EXECUTION_FAILED
UNKNOWN_ERROR
```

Additional required production error codes:

```text
DATA_SOURCE_REVISION_DETECTED
PRECISION_MISMATCH
TIMESTAMP_OVERLAP
RATE_LIMIT_EXCEEDED
LICENSE_RESTRICTION
DATA_SCHEMA_DRIFT
MISSING_ASSET_METADATA
```

### 18.1 Unsupported Operation Rule

Use `UNSUPPORTED_OPERATION` when a valid source or adapter exists but does not support the requested capability.

Examples:

- requesting tick data from a source that only supports OHLCV
- requesting streaming from a Phase 1 historical-only adapter
- requesting historical market-hour reconstruction from a current-hours-only source
- requesting a synthetic process that is deferred to a later phase

Do not use `UNKNOWN_ERROR` for unsupported but expected capability gaps.
Do not silently fall back to another source unless the request explicitly allows fallback.

---

## 19. Logging and Audit Requirements

Every production file must define or import the project logger according to HaruQuant standards:

```python
from tools.utils import logger
```

Each official tool must log:

- tool called
- request_id
- source
- symbol where applicable
- timeframe where applicable
- validation failure
- source failure
- cache hit/miss/stale status where applicable
- successful completion
- execution_ms
- error code on failure

Do not log:

- passwords
- account tokens
- full API keys
- MT5 password
- broker account secrets
- full private local paths when avoidable

### 19.1 Traceability

Every official tool must support:

```python
request_id: Optional[str] = None
```

The same `request_id` must appear in:

- logs
- standard tool response metadata
- source adapter logs where applicable
- scheduler job logs where applicable

---

## 20. Security Requirements

### 20.1 Credential Handling

Credentials must be resolved internally from approved configuration or environment variables.

Official AI tools must not accept raw passwords unless a future explicit security design allows it.

### 20.2 Secret Redaction

All errors and logs must redact secret-like values.

### 20.3 Network Calls

Network source adapters must use:

- explicit timeout
- bounded retry policy where appropriate
- clear network error mapping
- no infinite loops
- no silent fallback to stale data

### 20.4 File System Safety

All local file operations must enforce allowed roots and path validation.

---

## 21. Performance Requirements

### 21.1 Baseline Targets

| Operation | Target |
|---|---:|
| Validate 10,000 OHLCV records | < 500 ms baseline |
| Load 100,000 local Parquet records | < 2 seconds baseline |
| Convert 100,000 DataFrame rows to records | < 3 seconds baseline |
| Resample 100,000 M1 bars to H1 | < 3 seconds baseline |
| Generate 100,000 synthetic ticks | < 3 seconds baseline |

These are Phase 1/2 baseline targets, not hard final limits.

### 21.2 Performance Rules

- Avoid row-by-row loops where vectorized operations are practical.
- Keep official tool payload sizes configurable.
- Support `limit` or date ranges to avoid accidental huge responses.
- Large datasets should be stored locally and referenced by metadata where future workflows require it.

---

## 22. Official Tool Specifications

### 22.1 `get_market_data`

Purpose:

Fetch normalized OHLCV bar data from a supported source.

Signature:

```python
def get_market_data(
    symbol: str,
    timeframe: str,
    source: str,
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
    use_cache: bool = True,
    cache_ttl_seconds: int | None = None,
    source_timezone: str | None = None,
    allow_stale: bool = False,
    fail_on_quality_error: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    ...
```

Required behavior:

- validate symbol, timeframe, source, date range, and limit
- retrieve data through source adapter
- normalize timestamps to UTC
- validate OHLCV quality
- use cache policy when enabled
- return standard response

### 22.2 `get_tick_data`

Fetch normalized tick data from supported sources.

Must support MT5, Dukascopy, cTrader, CSV/Parquet if dataset schema allows, and synthetic generation through separate generator tools.

### 22.3 `get_spread_data`

Return spread records or spread summary from source data.

If source has no native spread field but bid/ask exists, spread must be derived. The response `data.records` must follow the `SpreadRecord` contract in Section 6.5.

Required parameters:

```python
symbol: str
source: str
start: str | None
end: str | None
limit: int | None
source_timezone: str | None
request_id: str | None
```

### 22.4 `get_symbol_metadata`

Fetch normalized symbol metadata from source adapter.

Must preserve source-specific metadata under `source_metadata`.

### 22.5 `list_symbols`

List available symbols for a given source.

Signature:

```python
def list_symbols(
    source: str,
    pattern: str | None = None,
    asset_class: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    ...
```

### 22.6 `get_data_availability`

Return available date ranges, record counts, and gaps where known. The response `data` must follow the `DataAvailabilityResponse` contract in Section 6.6.

This tool must be safe and read-only. It must not fetch or materialize large datasets just to count records unless the source declares that as the only available method and the request remains within configured limits.

### 22.7 `get_market_hours`

Return market hours for a symbol/source. All session window timestamps must be UTC ISO 8601 strings. Source or broker timezone must be preserved in `source_metadata`.

Phase 1 may return current configured hours only. Historical changes for holidays and daylight-saving changes are optional until the market-calendar integration phase and must be clearly disclosed in metadata.

### 22.8 `get_trading_sessions`

Return trading session windows and labels using the trading session contract in Section 6.8. All `start` and `end` values must be UTC ISO 8601 strings. The original timezone must be preserved per session or in `source_metadata`.

### 22.9 `get_historical_volume`

Return historical volume data or summary for symbol/timeframe/source. The response `data` must follow the historical volume contract in Section 6.7.

When the source provides both `tick_volume` and `real_volume`, both must be preserved. The primary `volume` value must be documented in `volume_kind`.

### 22.10 `save_market_data`

Save normalized records to CSV or Parquet.

Must validate path safety and default to no overwrite.

### 22.11 `load_local_dataset`

Load local CSV/Parquet dataset and return normalized records.

This is different from `get_market_data(source="csv")` only in that it is explicitly file/dataset oriented.

### 22.12 `resample_ohlcv`

Resample normalized OHLCV records to a higher timeframe.

### 22.13 `align_multitimeframe_data`

Align datasets from multiple timeframes without lookahead leakage by default.

### 22.14 `generate_synthetic_ticks`

Generate deterministic synthetic tick records.

### 22.15 `generate_synthetic_bars`

Generate deterministic synthetic OHLCV bars using configured method.

The generator must accept a deterministic seed and a `process` parameter. Required `process` values:

```text
gbm
mean_reverting
trend
seasonal
```

Phase 1 may implement only `gbm`; the remaining processes are required before Phase 2 is complete.

### 22.16 `aggregate_ticks_to_bars`

Convert tick records into OHLCV bars.

### 22.17 `label_market_data`

Apply deterministic labels to OHLCV records.

### 22.18 Scheduler Tools

`create_data_update_job`, `start_data_update_job`, `stop_data_update_job`, and `run_data_update_job_once` must use the scheduler contract and return standard medium-risk tool responses.

Clarification:

```text
run_data_update_job_once = executes one immediate update run and does not create a recurring schedule.
start_data_update_job = requires a valid existing job or valid schedule and starts recurring execution.
start_data_update_job must not behave as a one-time run when schedule is omitted.
```

### 22.19 `clear_data_cache`

Clear cache safely with dry-run default.

---

## 23. Module-by-Module Implementation Requirements

### 23.1 `contracts.py`

Must define all enums and typed contracts. It must contain no source-specific fetching logic.

### 23.2 `responses.py`

Must provide helpers for standard success/error responses.

Recommended functions:

```python
build_success_response(...)
build_error_response(...)
build_metadata(...)
```

### 23.3 `validation.py`

Must validate external inputs for official tools.

### 23.4 `normalization.py`

Must normalize source-specific records into internal contracts.

### 23.5 `quality.py`

Must implement data quality checks for OHLCV, ticks, spread, timestamps, and metadata.

### 23.6 `timeframes.py`

Must map and validate HaruQuant timeframes and source-specific timeframes.

### 23.7 `cache.py`

Must implement internal cache key creation, get/set, stale detection, and clear operations.

### 23.8 `registry.py`

Must map source names to source adapters.

### 23.9 `sources/*`

Must contain source adapters only.

### 23.10 `storage/*`

Must contain safe local CSV/Parquet persistence and path policy.

### 23.11 `transforms/*`

Must contain deterministic transformations.

### 23.12 `generators/*`

Must contain deterministic synthetic generation.

### 23.13 `labeling/*`

Must contain deterministic labeling algorithms.

### 23.14 `scheduler/*`

Must contain scheduler lifecycle, job contracts, and state persistence.

---


### 23.15 `versioning.py`

Must implement source revision metadata, raw payload hashing helpers, and source revision comparison logic.

### 23.16 `precision.py`

Must implement `PrecisionPolicy`, price and volume quantization, symbol tick-size alignment, and precision mismatch detection.

### 23.17 `rate_limits.py`

Must implement `RateLimitConfig`, `RateLimitTracker`, and source-level backoff coordination for network adapters.

### 23.18 `licensing.py`

Must implement `DataLicenseMetadata`, license validation helpers, attribution metadata handling, and redistribution blocking rules.


## 24. Testing Requirements

Coverage must be above 80% for the data module.

### 24.1 Unit Tests Required for Every Official Tool

Each official tool must test:

- successful call
- invalid input
- unsupported source
- unsupported timeframe where applicable
- empty result
- source failure
- quality failure
- standard return schema
- metadata correctness
- request_id propagation
- error code correctness
- logging footprint
- cache hit/miss behavior where applicable
- path safety where applicable
- dry-run behavior for cache clear and scheduler/file operations

### 24.2 Source Adapter Tests

Each source adapter must test:

- source-specific normalization
- source-specific error mapping
- missing dependency behavior
- network/client failure behavior using mocks
- no secret leakage

### 24.3 Data Quality Tests

Must test:

- valid OHLCV passes
- duplicate timestamps warning/failure
- out-of-order timestamps
- OHLC inconsistency
- negative volume
- negative spread
- stale data
- partial data
- tick ask-bid violation

### 24.4 Storage Tests

Must test:

- valid save/load
- overwrite blocked by default
- unsafe path rejection
- unsupported extension rejection
- metadata preservation

### 24.5 Scheduler Tests

Must test:

- create job
- start job
- stop job
- run once
- duplicate start behavior
- missing job behavior
- invalid source/symbol/timeframe
- state persistence

### 24.6 Usage Examples

Usage examples must exist for:

```text
market_data.py
local_storage.py
source_symbols.py
synthetic_generation.py
labeling.py
scheduler.py
```

Usage examples must show realistic workflows and handle both success and error responses.

---


### 24.7 Industry-Grade Production Tests

The data module must include tests for:

- source revision detection and cache invalidation
- raw data hash propagation into cache metadata
- precision quantization by symbol tick size and fixed decimal rules
- precision mismatch failure behavior for execution-bound workflows
- timestamp gap and overlap resolution defaults
- explicit rejection or logging of interpolation/forward-fill outside research workflows
- rate-limit tracking, HTTP 429 handling, and no-immediate-retry behavior
- asset-specific metadata validation for futures and options
- license restriction enforcement for storage and scheduler exports
- downstream contract alignment with simulation, optimization, analytics, risk, portfolio, and execution contracts


## 25. Phase-by-Phase Implementation Plan

### Phase 1: Core Contracts, Responses, Validation, and Registry

Must include `SourceRevisionMetadata`, `PrecisionPolicy`, `GapResolutionPolicy`, `OverlapPolicy`, `RateLimitConfig`, asset metadata extensions, and `DataLicenseMetadata`.

Deliverables:

```text
tools/data/__init__.py
tools/data/contracts.py
tools/data/responses.py
tools/data/errors.py
tools/data/constants.py
tools/data/validation.py
tools/data/timeframes.py
tools/data/registry.py
tests/unit/tools/data/test_contracts.py
tests/unit/tools/data/test_responses.py
tests/unit/tools/data/test_validation.py
tests/unit/tools/data/test_timeframes.py
tests/unit/tools/data/test_registry.py
tests/unit/tools/data/test_init_exports.py
```

Exit acceptance:

- official exports match this spec
- all standard responses validate
- request_id appears in metadata
- invalid inputs return deterministic error codes
- registry can resolve supported source names
- no source adapter implementation is required to be complete yet

### Phase 2: Local Storage and Local Sources

Must implement precision quantization, source revision metadata persistence, license metadata persistence, and cache key support for `raw_data_hash`.

Deliverables:

```text
tools/data/storage/path_policy.py
tools/data/storage/csv_store.py
tools/data/storage/parquet_store.py
tools/data/sources/csv_source.py
tools/data/sources/parquet_source.py
tools/data/normalization.py
tools/data/quality.py
tests for all above
usage/local_storage.py
```

Exit acceptance:

- CSV load/save works
- Parquet load/save works
- path safety enforced
- OHLCV validation works
- official tools can load/save local datasets

### Phase 3: Transformations and Synthetic Data

Deliverables:

```text
tools/data/transforms/resampling.py
tools/data/transforms/alignment.py
tools/data/transforms/aggregation.py
tools/data/generators/synthetic_ticks.py
tools/data/generators/synthetic_bars.py
tools/data/generators/gbm.py
tests for all above
usage/synthetic_generation.py
```

Exit acceptance:

- resampling works correctly
- multi-timeframe alignment avoids lookahead by default
- tick aggregation works
- synthetic generation is deterministic with seed

### Phase 4: External Source Adapters

Must integrate `RateLimitTracker`, data version policy enforcement, source revision checks, source licensing metadata, and source-specific precision metadata.

Deliverables:

```text
tools/data/sources/mt5_source.py
tools/data/sources/ctrader_source.py
tools/data/sources/dukascopy_source.py
tools/data/sources/binance_source.py
source-specific tests with mocks
usage/source_symbols.py
```

Exit acceptance:

- list symbols works through adapters
- MT5 bars/symbol metadata are supported behind safe credential boundary
- cTrader bars are supported behind client boundary
- Dukascopy historical/live fetch capability is represented cleanly
- network and broker failures return deterministic error codes

### Phase 5: Labeling and Scheduler

Deliverables:

```text
tools/data/labeling/lexlb.py
tools/data/scheduler/state.py
tools/data/scheduler/jobs.py
tools/data/scheduler/updater.py
tests for labeling and scheduler
usage/labeling.py
usage/scheduler.py
```

Exit acceptance:

- labeling is deterministic
- scheduler job lifecycle works
- scheduler state is explicit
- scheduler tools are medium-risk and safe

### Phase 6: Integration, Hardening, and Documentation

Must include `test_contract_alignment.py`, license/revision audit logging, schema drift checks, and downstream contract parity validation.

Deliverables:

```text
full test suite
usage examples
README section or docs/tools/data.md
coverage report
import boundary checks
security/redaction checks
performance smoke tests
```

Exit acceptance:

- coverage > 80%
- all official tools pass schema tests
- no raw DataFrame crosses tool boundary
- no credentials exposed
- no legacy names required
- data module ready for downstream module updates

---

## 26. Downstream Integration Requirements

The following modules must adapt to the v8 data API:

- `tools/strategy/`
- `tools/simulation/`
- `tools/optimization/`
- `tools/analytics/`
- `tools/risk/`
- `tools/portfolio/`
- `tools/execution/`
- `agentic/agents/research.py`
- `agentic/agents/strategy.py`
- `agentic/agents/validation.py`
- `agentic/workflows.py`

Downstream modules must import official tools only from:

```python
from tools.data import get_market_data
```

They must not import from deep implementation files such as:

```python
from tools.data.sources.mt5_source import ...
```

---

## 27. Production Acceptance Criteria

Additional industry-grade acceptance criteria:

- Raw source revision changes invalidate cache or fail according to `DataVersionPolicy`.
- All normalized price and volume fields are precision-aligned before leaving adapters.
- Timestamp gaps and overlaps use explicit configured policies and are reported in quality metadata.
- Network sources respect deterministic rate limits and never immediately retry after throttling.
- Asset-specific metadata is present where required by asset class and workflow realism.
- License metadata is attached to external source data and enforced during storage/export.
- Cross-module contract alignment tests pass before production sign-off.


The v8 data module is production-ready only when all of the following are true:

- [ ] Package path is `tools/data/`.
- [ ] `tools/data/__init__.py` contains only imports and `__all__`.
- [ ] Official exports match the v8 tool surface.
- [ ] Every official tool returns the standard HaruQuantAI tool response schema.
- [ ] Every official tool supports `request_id`.
- [ ] Every official tool has metadata and side-effect flags.
- [ ] Every official tool has input validation.
- [ ] Every official tool has structured logging.
- [ ] Every official tool handles errors without silent failure.
- [ ] Every official tool has unit tests.
- [ ] Every official tool has a usage example where applicable.
- [ ] DataFrame/NumPy/source SDK objects do not cross official tool boundary.
- [ ] OHLCV and tick records use normalized contracts.
- [ ] Data quality validation is applied before returning market data.
- [ ] Timezone normalization uses UTC at the boundary.
- [ ] Source timezone/broker timezone metadata is preserved.
- [ ] Cache keys are deterministic and include schema/normalization version.
- [ ] Stale cache is not returned silently.
- [ ] Local file paths are validated against allowed roots.
- [ ] MT5 credentials are not exposed or logged.
- [ ] cTrader and Dukascopy clients are internal.
- [ ] Scheduler tools are medium-risk and lifecycle-safe.
- [ ] Synthetic generation is deterministic when seed is supplied.
- [ ] Multi-timeframe alignment prevents lookahead by default.
- [ ] Test coverage is above 80%.
- [ ] `__pycache__`, `.pyc`, and build artifacts are excluded from source.
- [ ] Downstream modules import through `tools.data` only.

---



## 27A. Production Implementation Gate

The data module may be promoted to production only after the following gate is satisfied.

### 27A.1 Code Quality Gate

Required:

```text
- all production files have module-level docstrings
- all public functions and classes have docstrings
- all official tools are typed
- no official tool returns raw DataFrame objects
- no official tool returns None
- no official tool raises raw exceptions to the caller
- no production logic uses print()
- no __pycache__, notebooks, temp files, local credentials, or generated artifacts are committed
```

### 27A.2 Tool Standard Gate

For every function exported by `tools/data/__init__.py`:

```text
- listed in __all__ intentionally
- has standard metadata constants
- has side-effect flags
- accepts request_id
- validates inputs
- returns standard schema
- handles errors deterministically
- logs call, validation failure, success, and failure
- includes execution_ms
- has unit tests
- has usage example
```

### 27A.3 Data Correctness Gate

Required checks:

```text
- OHLC consistency: high >= max(open, close), low <= min(open, close)
- no negative prices
- no negative volume
- no negative spread
- no duplicate timestamps unless explicitly allowed for ticks
- timestamps are monotonic after normalization
- timezone metadata is preserved
- quality report is included for fetched and loaded market data
- partial/stale data is flagged, not hidden
- resampling uses deterministic OHLCV aggregation
- synthetic generation is deterministic with seed
```

### 27A.4 Security Gate

Required:

```text
- credentials loaded from environment/config boundary only
- secrets are never logged
- unsafe paths are rejected
- external source calls use bounded timeouts
- network errors map to deterministic error codes
- broker adapters never place trades
- cache clearing is scoped and safe
```

### 27A.5 Test Gate

Minimum tests:

```text
- unit tests for every official tool
- unit tests for every request/response contract
- source adapter tests with mocks for network/broker systems
- data quality tests for good and bad OHLCV/tick data
- storage/path safety tests
- cache key and stale cache tests
- scheduler idempotency/state tests
- usage examples for every official tool group
- coverage >= 80%
```

### 27A.6 Documentation Gate

Required docs:

```text
- data module README or docs section
- official tool catalog
- source adapter catalog
- environment variable reference
- usage examples
- error code reference
- troubleshooting notes for MT5, cTrader, Dukascopy, local storage, and cache
```

### 27A.7 Downstream Integration Gate

Before production sign-off, at least one integration test or smoke workflow must prove that each downstream consumer can use the official data contracts:

```text
- strategy module
- simulation/backtest module
- indicator module
- analytics module
- risk module
- portfolio module
- agentic workflows
```

The downstream modules must adapt to the v8 data contracts. The data module must not add compatibility aliases to preserve older caller behavior.

## 28. Final Implementation Guidance

The data module should be built as a clean professional foundation, not as a compatibility-preserving cleanup.

Recommended implementation mindset:

```text
Start with contracts.
Then responses.
Then validation.
Then local data.
Then transformations.
Then external adapters.
Then scheduler.
Then integration hardening.
```

Do not expose a function just because it exists.

Expose a function only when it is:

- useful to agents or workflows
- safe at the declared risk level
- documented
- typed
- tested
- schema-compliant
- logged
- traceable through request_id

The final module should feel like a reliable data service that agents can call safely, not a collection of raw scripts.

---

## 29. Final Recommendation

Use this v8 document as the official production-ready baseline for rebuilding the HaruQuantAI Data Module.

The next step is to begin Phase 1 implementation against this specification:

```text
contracts.py
responses.py
errors.py
constants.py
validation.py
timeframes.py
registry.py
__init__.py
unit tests
```

No legacy compatibility layer should be added unless a future implementation phase explicitly proves that a temporary migration shim is necessary.


---

## 30A. Final Non-Blocking Implementation Notes

The following points are accepted implementation notes and do not block Phase 1:

1. `get_market_hours` may return current market hours only in Phase 1. Historical daylight-saving changes, holidays, and broker-specific historical market-hour revisions are deferred unless explicitly supported by the selected source.
2. Synthetic data generation requires `process="gbm"` in Phase 1. Additional processes such as `mean_reverting`, `trend`, and `seasonal` are Phase 2 extensions.
3. `get_historical_volume` may be implemented as a direct source capability or derived from `get_market_data`, provided the official response contract remains stable and test-covered.
4. `align_multitimeframe_data` must prevent lookahead bias by default using `allow_lookahead=False` and `alignment_method="last_known_closed_bar"`.
5. `UNSUPPORTED_OPERATION` must be used when a valid adapter/source exists but does not support the requested operation.

---
