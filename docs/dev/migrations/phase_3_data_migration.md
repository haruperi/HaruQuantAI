# Phase 3 Data StandardResponse Migration

> **Plan ID:** `DATA-001`  
> **Document status:** Approved planning artifact; implementation not yet authorized  
> **Prepared:** 2026-07-27  
> **Target domain:** `app/services/data`  
> **Migration program:** HaruQuantAI standard public-operation responses  
> **Intended reader:** A coding agent that may have no prior conversation context

## 1. Purpose

This document is the complete implementation handoff for migrating the HaruQuantAI
Data domain to the Utils-owned `StandardResponse[T]` contract.

It is deliberately self-contained. The receiving coding agent must not assume access
to the conversation in which the response architecture was designed or to the agents
that implemented the earlier phases.

This document is a plan, not implementation authorization. Before changing any
repository file, the coding agent must:

1. Read the repository authorities listed below.
2. Inspect the current worktree and refresh the inventories in this plan.
3. Produce the repository-required dry-run report, including any plan delta caused by
   repository changes since 2026-07-27.
4. Wait for a standalone owner message whose trimmed complete content is exactly
   `APPROVED: EXECUTE`.

Approval to create this document does not authorize the Data implementation.

## 2. Repository Authority and Working Rules

The repository authority order is:

1. Owner instructions
2. `AGENTS.md`
3. `docs/PROJECT.md`
4. `docs/ARCHITECTURE.md`
5. `docs/CHANGELOG.md`

The Data package's canonical current-state feature registry is:

- `app/services/data/README.md`

Each feature module README is authoritative for its focused feature. The coding agent
must read the root Data README and every feature README affected by the migration
before editing.

Important repository rules include:

- Preserve existing user changes in a dirty worktree.
- Do not reset, clean, or overwrite unrelated changes.
- Use `apply_patch` for manual file edits.
- Change only approved scope.
- Add or update exact functional requirements and usage evidence.
- Keep one feature per module folder and one focused responsibility per file.
- Use Google-style docstrings and explicit type annotations.
- Use the system logger at public service, external interaction, state transition,
  persistence, retry, and failure boundaries.
- Maintain at least 80% package coverage.
- Use targeted tests during development and the complete Data gate at completion.
- Do not perform live provider mutations.
- Do not commit or push unless separately requested.

## 3. Migration Program Background

### 3.1 Governing principle

The owner-approved system principle is:

> Every HaruQuantAI-owned public operation that accepts one bounded request and
> produces one completed outcome must return `StandardResponse[T]`, whether or not it
> is registered as an AI tool.

This standardization is not permission to expose every function to an AI agent.
Tool registration remains a separate decision. The response standard gives internal
and external callers one predictable function-level result contract and makes a
qualifying operation tool-ready when its inputs and raw output are also suitable for
tool serialization.

### 3.2 StandardResponse contract

Utils owns `StandardResponse[T]` and its supporting contracts. The exact top-level
fields are:

```text
status
message
data
error
metadata
```

The contract currently uses `message`, not `content`.

Key invariants:

- `status` is exactly `"success"` or `"error"`.
- `message` is a bounded, trimmed string.
- `data` is the raw successful result `T`, or `None`.
- `error` is `None` on success.
- On error, `data` is `None` and `error` contains exactly `code` and `details`.
- `metadata` contains version/schema identity, operation/domain/risk identity,
  request/correlation IDs, execution duration, side-effect declarations, and
  `extensions`.
- `execution_ms` uses a monotonic clock and is rounded to three decimal places.
- Successful operations may legitimately return `data=None`.
- Raw results are never nested inside a synthetic `result` or `payload` object.

The relevant Utils implementation is under:

- `app/utils/responses/`
- `app/utils/errors/`

The coding agent must use the existing Utils factories and contracts rather than
creating a Data-local duplicate of the standard envelope.

### 3.3 Error ownership

Utils owns:

- The common error-definition shape.
- Common business-neutral/system error codes.
- Catalogue validation.
- Safe exception mapping.
- Standard error and response validation.

Each producing domain owns:

- Its domain error codes.
- Descriptions.
- Retry policy.
- Severity.
- Operator actions.
- Mapping of domain failure evidence into `error.details`.

Therefore, this migration must not move all Data business codes into a global Utils
business-code file. Data retains one immutable Data-owned catalogue while using the
Utils-owned `ErrorDefinition` contract.

### 3.4 Completed earlier phases

#### Phase 1 — Utils

The Utils foundation is implemented. It provides:

- `StandardResponse[T]`
- `StandardError`
- `ResponseMetadata`
- `RiskLevel`
- `JsonValue`
- `build_response_metadata`
- `success_response`
- `error_response`
- `exception_response`
- Monotonic execution timing
- Common error catalogue and catalogue validation

The coding agent must inspect current files rather than relying only on this summary.

#### Phase 2 — Brokers

Brokers has been migrated to `StandardResponse[T]`.

Important precedents from that phase:

- The raw Broker result is directly in `data`.
- Former generic Broker envelope evidence is in `metadata.extensions`.
- Former Broker error evidence is in `error.details`.
- Broker-specific error codes remain Brokers-owned.
- Public protocol annotations and concrete implementations agree.
- Data and Trading consumers explicitly inspect Broker responses.
- Streaming event iterators retain event contracts; bounded subscribe/unsubscribe
  operations use `StandardResponse`.

Relevant reference files:

- `app/services/brokers/contracts/responses.py`
- `app/services/brokers/contracts/error_catalog.py`
- `app/services/brokers/adapter_runtime/base.py`
- `app/services/brokers/README.md`

The Data migration should follow the same shared-envelope principles while preserving
Data-specific behavior and architecture.

## 4. Data Domain Context

Data is a foundation domain. It acquires, normalizes, validates, stores, transforms,
and serves market data and read-only account/market evidence. It also owns shared
SQLite transaction, locking, and migration execution infrastructure.

Data does not own:

- Strategy decisions.
- Risk policy.
- Position sizing.
- Simulated fills.
- Broker mutations.
- Live trading decisions.
- Broker credentials or transport implementations.

Data consumes read-only Broker operations through the Brokers public boundary.
Broker responses are already `StandardResponse[T]`; Data currently unwraps Broker
payloads from `data` and validates Brokers-owned extension evidence.

The approved Data architecture contains fifteen feature modules:

1. `FEAT-DATA-01` Canonical Data Contracts
2. `FEAT-DATA-02` Market Data Retrieval
3. `FEAT-DATA-03` Local Dataset Loading
4. `FEAT-DATA-04` Synthetic Data Generation
5. `FEAT-DATA-05` Tick-Series Derivation
6. `FEAT-DATA-06` Data Persistence and Storage
7. `FEAT-DATA-07` Data Quality and Validation
8. `FEAT-DATA-08` Data Transformation and Resampling
9. `FEAT-DATA-09` Time and Session Handling
10. `FEAT-DATA-10` Data Source Governance
11. `FEAT-DATA-11` Economic Calendar
12. `FEAT-DATA-12` Real-Time Feed Lifecycle and Observability
13. `FEAT-DATA-13` Scheduler and Job Management
14. `FEAT-DATA-14` Cross-Domain Evidence
15. `FEAT-DATA-15` Audit Evidence

The package root currently exposes exactly 207 approved names. This migration changes
operation return contracts, not the public-name inventory.

## 5. Migration Goal

Migrate every qualifying Data-owned public operation to:

```python
StandardResponse[T]
```

The migration must preserve these invariants:

- The exact existing successful result `T` goes directly into `data`.
- `MarketDataset`, `DataFrame`, mapping, tuple, bytes, proxy, lock, manifest, result
  DTO, and every other existing raw value retain their runtime type.
- A type whose name ends in `Result` is not automatically an envelope. Data business
  DTOs such as `MigrationResult`, `VolumeResult`, and `TransactionResult` remain raw
  business payloads in `data`.
- No raw result is placed in `metadata.extensions`.
- No raw result is wrapped in `{"result": ...}`, `{"payload": ...}`, or an equivalent
  container.
- Successful operations currently returning `None` return a successful response with
  `data=None`.
- Expected public failures return standard error responses.
- Constructors and non-operation boundaries retain their existing behavior.
- Existing algorithms, numerical behavior, schemas, database layout, cache identity,
  provider policy, and data-quality semantics remain unchanged.

## 6. Inventory and Classification

The planning-time inventory found:

- 110 package-root public functions.
- 22 direct public methods on package-root exported classes.
- 130 qualifying public operations.
- 2 explicit exclusions.

The coding agent must regenerate this inventory before editing and issue a plan delta
if the current repository differs materially.

### 6.1 FEAT-DATA-01 — Canonical Data Contracts

This feature owns the response/error integration but has no existing public completed
operation to wrap.

Create:

- `app/services/data/contracts/responses.py`

Edit:

- `app/services/data/contracts/errors.py`
- `app/services/data/contracts/__init__.py`
- `app/services/data/__init__.py`
- `app/services/data/contracts/README.md`
- `app/services/data/README.md`

### 6.2 FEAT-DATA-02 — Market Data Retrieval

Candidate count: 12.

Files:

- `app/services/data/market_data/pipeline.py`
- `app/services/data/market_data/symbol_discovery.py`

Operations:

- `fetch_market_dataset`
- `get_market_data`
- `get_tick_data`
- `get_spread_data`
- `discover_symbols`
- `fetch_symbol_metadata`
- `inspect_availability`
- `fetch_historical_volume`
- `get_symbol_metadata`
- `list_symbols`
- `get_data_availability`
- `get_historical_volume`

### 6.3 FEAT-DATA-03 — Local Dataset Loading

Candidate count: 3.

Files:

- `app/services/data/local_datasets/csv_loader.py`
- `app/services/data/local_datasets/parquet_loader.py`
- `app/services/data/persistence/dataset_writer.py`

Operations:

- `load_csv`
- `load_parquet`
- `load_local_dataset`

### 6.4 FEAT-DATA-04 — Synthetic Data Generation

Candidate count: 3.

File:

- `app/services/data/synthetic_data/gbm.py`

Operations:

- `generate_synthetic_dataset`
- `generate_synthetic_ticks`
- `generate_synthetic_bars`

### 6.5 FEAT-DATA-05 — Tick-Series Derivation

Candidate count: 2.

File:

- `app/services/data/tick_derivation/generator.py`

Operations:

- `generate_tick_series`
- `generate_tick_series_to_parquet`

`generate_tick_series_to_parquet` must retain its raw mapping as `data` and declare
its file-write capability in response metadata.

### 6.6 FEAT-DATA-06 — Data Persistence and Storage

Candidate count: 16.

Files:

- `app/services/data/persistence/locking.py`
- `app/services/data/persistence/cache.py`
- `app/services/data/persistence/backup.py`
- `app/services/data/persistence/transactions.py`
- `app/services/data/persistence/external_import.py`
- `app/services/data/persistence/migrations.py`
- `app/services/data/persistence/dataset_writer.py`

Operations:

- `acquire_write_lock`
- `clear_cache_entry`
- `clear_data_cache`
- `create_backup`
- `describe_import_dialects`
- `enforce_retention_policy`
- `execute_transaction`
- `get_cache_entry`
- `import_external_dataset`
- `load_dataset`
- `put_cache_entry`
- `restore_from_backup`
- `run_data_migrations`
- `run_domain_migrations`
- `save_dataset`
- `save_market_data`

The existing lock, transaction, checksum, lease, atomicity, approved-path, and
migration-ledger rules remain unchanged.

### 6.7 FEAT-DATA-07 — Data Quality and Validation

Candidate count: 12.

Files:

- `app/services/data/quality/__init__.py`
- `app/services/data/quality/contracts.py`
- `app/services/data/quality/anomalies.py`
- `app/services/data/quality/asset_metadata.py`
- `app/services/data/quality/policy.py`
- `app/services/data/quality/series.py`

Operations:

- `aggregate_flags`
- `detect_extreme_spread_widening`
- `detect_flatline_periods`
- `detect_price_jumps`
- `detect_timestamp_gaps`
- `detect_zero_volume_bars`
- `get_quality_policy`
- `inspect_data_quality`
- `inspect_dataset_quality`
- `inspect_records_quality`
- `summarize_quality_remediation`
- `validate_symbol_metadata`

### 6.8 FEAT-DATA-08 — Data Transformation and Resampling

Candidate count: 8.

Files:

- `app/services/data/transformation/alignment.py`
- `app/services/data/transformation/resampling.py`
- `app/services/data/transformation/tabular.py`
- `app/services/data/transformation/tick_aggregation.py`

Operations:

- `aggregate_ticks`
- `aggregate_ticks_to_bars`
- `align_datasets`
- `align_multitimeframe_data`
- `resample_dataset`
- `resample_ohlcv`
- `to_ohlcv_dataframe`
- `to_tick_dataframe`

A returned `pandas.DataFrame` remains the raw `data` value. The standard response
does not make that operation automatically suitable for an AI tool; tool registration
must separately account for serialization.

### 6.9 FEAT-DATA-09 — Time and Session Handling

Candidate count: 12.

Files:

- `app/services/data/time_sessions/utc.py`
- `app/services/data/time_sessions/timeframes.py`
- `app/services/data/time_sessions/gaps.py`
- `app/services/data/time_sessions/named_sessions.py`
- `app/services/data/time_sessions/exchange_calendar.py`
- `app/services/data/time_sessions/schedule.py`
- `app/services/data/time_sessions/weekly_schedule.py`

Operations:

- `require_utc`
- `get_timeframe_spec`
- `validate_resample_target`
- `classify_gap`
- `get_active_market_sessions`
- `get_exchange_sessions`
- `get_current_schedule`
- `get_market_hours`
- `get_trading_sessions`
- `MarketCalendar.get_schedule`
- `WeeklyScheduleProvider.get_sessions`
- `WeeklyScheduleProvider.get_schedule`

### 6.10 FEAT-DATA-10 — Data Source Governance

Candidate count: 17.

Files:

- `app/services/data/sources/registry.py`
- `app/services/data/sources/composition.py`
- `app/services/data/sources/policy.py`
- `app/services/data/sources/read_only.py`
- `app/services/data/sources/protocol.py`
- `app/services/data/sources/local_adapter.py`

Operations:

- `ensure_source`
- `ensure_source_access`
- `evaluate_source_policy`
- `get_source_descriptor`
- `list_composable_sources`
- `list_registered_sources`
- `promote_source`
- `register_source`
- `resolve_source`
- `verify_read_only_call`
- `wrap_broker_client`
- `MarketDataSource.fetch`
- `MarketDataSource.list_symbols`
- `MarketDataSource.get_symbol_metadata`
- `LocalMarketDataSource.fetch`
- `LocalMarketDataSource.list_symbols`
- `LocalMarketDataSource.get_symbol_metadata`

Source capability, readiness, licensing, promotion, rate-limit, circuit-breaker, and
read-only enforcement must not change.

### 6.11 FEAT-DATA-11 — Economic Calendar

Candidate count: 22.

Files:

- `app/services/data/economic_calendar/calendar_state.py`
- `app/services/data/economic_calendar/restriction.py`
- `app/services/data/economic_calendar/profiling.py`
- `app/services/data/economic_calendar/store.py`
- `app/services/data/economic_calendar/service.py`
- `app/services/data/economic_calendar/scraper.py`
- `app/services/data/economic_calendar/providers.py`

Operations:

- `calendar_state_provenance`
- `derive_calendar_state`
- `evaluate_calendar_state`
- `from_row`
- `get_economic_events`
- `get_persisted_events`
- `get_symbol_economic_events`
- `get_symbol_event_profile`
- `is_news_restricted`
- `is_news_restricted_events`
- `populate_market_context_calendar`
- `scrape_economic_calendar`
- `CalendarTransport.fetch_site`
- `EconomicCalendarProvider.get_events`
- `CalendarScrapeProvider.get_events`
- `EconomicEventStore.upsert`
- `EconomicEventStore.query`
- `EconomicEventStore.refresh_windows`
- `ScrapeResult.to_dataframe`
- `ScrapeResult.save`
- `ScrapeResult.serialize`
- `ScrapeResult.deserialize`

### 6.12 FEAT-DATA-12 — Real-Time Feed Lifecycle and Observability

Candidate count: 6.

Files:

- `app/services/data/realtime_feeds/buffer.py`
- `app/services/data/realtime_feeds/reconnection.py`
- `app/services/data/realtime_feeds/status.py`

Operations:

- `start_internal_feed`
- `ingest_feed_event`
- `reconcile_feed_gap`
- `reconnect_feed`
- `read_feed_status`
- `get_feed_status`

This migration applies to bounded lifecycle operations. It does not replace feed event
DTOs with function responses.

### 6.13 FEAT-DATA-13 — Scheduler and Job Management

Candidate count: 10.

Files:

- `app/services/data/data_jobs/backfill.py`
- `app/services/data/data_jobs/job.py`
- `app/services/data/data_jobs/recovery.py`

Operations:

- `derive_backfill_key`
- `execute_backfill_chunk`
- `schedule_update_job`
- `read_update_job_status`
- `run_data_update_job_once`
- `create_data_update_job`
- `start_data_update_job`
- `stop_data_update_job`
- `get_data_update_job_status`
- `recover_update_jobs`

### 6.14 FEAT-DATA-14 — Cross-Domain Evidence

Candidate count: 5.

Files:

- `app/services/data/evidence/account_state.py`
- `app/services/data/evidence/fx_conversion.py`
- `app/services/data/evidence/market_context.py`

Operations:

- `get_account_state_snapshot`
- `get_fx_conversion_evidence`
- `get_market_context_evidence`
- `FXRateProvider.get_rate_leg`
- `MarketContextProvider.get_market_context`

Evidence freshness, provenance, missingness, and fail-closed behavior must remain
unchanged.

### 6.15 FEAT-DATA-15 — Audit Evidence

Candidate count: 2.

Files:

- `app/services/data/audit/store.py`
- `app/services/data/audit/query.py`

Operations:

- `persist_audit_event`
- `query_audit_events`

Authentication, authorization, redaction, bounded queries, and durable audit
semantics must remain unchanged.

## 7. Explicit Exclusions

The following are not completed-operation boundaries and must not be migrated:

- `data_settings_context`: a context manager with a scoped lifetime.
- `ColumnMapping.bar_columns()`: a trivial value-object accessor.
- Constructors.
- Pydantic and dataclass validators.
- Properties.
- `WriteLock.__enter__` and `WriteLock.__exit__`.
- Private functions and methods.
- Methods on internal classes that are not exposed through the authoritative Data
  package root.
- Event objects or iterator yields.
- Constants, enums, request DTOs, result DTOs, and other data contracts.

If the refreshed inventory finds another public callable that does not produce one
completed outcome, the coding agent must document it as a proposed exclusion and
obtain approval through a plan delta rather than silently excluding it.

## 8. Response Infrastructure Design

Create:

- `app/services/data/contracts/responses.py`

This focused file should own only Data-specific construction and consumption of the
Utils standard response. It must not contain feature algorithms.

Required responsibilities:

- `data_start_time() -> int`, using `time.perf_counter_ns()`.
- Immutable static operation metadata for every qualifying public operation.
- `build_data_response(...) -> StandardResponse[T]`.
- Safe conversion of `DataError` to a standard error response.
- A private helper for consuming a `StandardResponse[T]` received from a public
  Data-owned protocol.
- Request-ID selection and validation needed to construct valid metadata even when
  a caller supplies an invalid identifier.
- Domain-specific error detail preservation.

The helper must use existing Utils contracts and factories. It must not duplicate:

- `StandardResponse`
- `StandardError`
- `ResponseMetadata`
- `RiskLevel`
- `get_execution_ms`
- Common exception mapping
- Common error-catalogue validation

## 9. Data Error Migration

Current Data errors are defined in:

- `app/services/data/contracts/errors.py`

The current public mapping name is:

- `DATA_ERROR_MANIFEST`

The planning-time manifest contains 36 codes:

- `INVALID_INPUT`
- `VALIDATION_FAILED`
- `DATA_QUALITY_FAILED`
- `DATA_NOT_FOUND`
- `EMPTY_RESULT`
- `LIMIT_EXCEEDED`
- `UNSUPPORTED_SOURCE`
- `UNSUPPORTED_TIMEFRAME`
- `UNSUPPORTED_OPERATION`
- `SOURCE_UNAVAILABLE`
- `SERVICE_UNAVAILABLE`
- `NETWORK_ERROR`
- `TIMEOUT`
- `LICENSE_RESTRICTION`
- `CREDENTIALS_MISSING`
- `AUTHENTICATION_FAILED`
- `PERMISSION_DENIED`
- `POLICY_BLOCKED`
- `STALE_EVIDENCE`
- `CIRCUIT_BREAKER_OPEN`
- `PRECISION_MISMATCH`
- `MISSING_ASSET_METADATA`
- `DATABASE_ERROR`
- `DB_CONNECTION_ERROR`
- `DB_WRITE_FAILED`
- `CONCURRENT_WRITE_LOCKED`
- `FILE_CORRUPTED`
- `SCHEMA_MIGRATION_FAILED`
- `JOB_NOT_FOUND`
- `SCHEDULER_ERROR`
- `CHECKPOINT_CORRUPTED`
- `STATE_RECOVERY_FAILED`
- `BUFFER_OVERFLOW`
- `DATA_DROPPED`
- `FEED_HEARTBEAT_TIMEOUT`
- `UNKNOWN_ERROR`

Required changes:

1. Retain the public `DATA_ERROR_MANIFEST` name unless the owner separately approves a
   breaking API change.
2. Replace Data's duplicate `ErrorDefinition` dataclass with the Utils-owned
   `ErrorDefinition`.
3. Give every definition `domain="data"`.
4. Map the existing safe message to the shared `description`.
5. Preserve the existing category, severity, retryable policy, and operator action.
6. Keep `DataError` for private core logic, validation, and domain-internal failure
   propagation.
7. Stop allowing expected `DataError` instances to escape qualifying public operation
   boundaries.

When mapping a `DataError`, preserve:

- `code` as `StandardError.code`.
- `safe_message` as the response `message`.
- `safe_details` in `error.details`.
- `request_id` in `error.details` when present.
- `retryable` in `error.details`.
- `severity` in `error.details`.
- `operator_action` in `error.details`.

Do not include raw exception text, tracebacks, credentials, tokens, provider payloads,
database statements, or sensitive paths.

Unexpected exceptions must use the existing Utils safe exception mapper. Cancellation
and process-control exceptions must propagate rather than being converted:

- `asyncio.CancelledError`
- `GeneratorExit`
- `KeyboardInterrupt`
- `SystemExit`

## 10. Internal Core and Public Boundary Pattern

The Data domain currently contains many public-to-public calls. Naively changing each
return type would produce nested responses and break internal algorithms.

The required pattern is:

1. Preserve the existing raw implementation as a private core function or method.
2. Keep the documented public name as a thin response boundary.
3. Start monotonic timing at the first line of the public operation.
4. Resolve a canonical request ID before constructing response metadata.
5. Call the private raw core.
6. Put the exact raw result into `data`.
7. Convert `DataError` to an approved error response.
8. Convert unexpected exceptions through Utils.
9. Keep internal calls on private raw cores.

Example shape:

```python
def _resample_dataset_raw(
    dataset: MarketDataset,
    target_timeframe: str,
) -> MarketDataset:
    ...


def resample_dataset(
    dataset: MarketDataset,
    target_timeframe: str,
) -> StandardResponse[MarketDataset]:
    start_time = data_start_time()
    request_id = ...
    try:
        result = _resample_dataset_raw(dataset, target_timeframe)
    except DataError as error:
        return build_data_response(
            operation="data.transformation.resample_dataset",
            request_id=request_id,
            start_time=start_time,
            error=error,
        )
    return build_data_response(
        operation="data.transformation.resample_dataset",
        request_id=request_id,
        start_time=start_time,
        data=result,
    )
```

The exact implementation may reduce repetition through a typed private boundary
helper, but it must preserve:

- Public signatures apart from the return type.
- Static type precision.
- Docstring accuracy.
- Async semantics.
- Cancellation behavior.
- Raw output identity.
- Focused file ownership.

A broad decorator that obscures signatures, request-ID behavior, operation metadata,
or error types is not acceptable.

## 11. Public Protocol Boundaries

Data owns several public protocols or public callable interfaces:

- `MarketDataSource`
- `MarketCalendar`
- `EconomicCalendarProvider`
- `CalendarTransport`
- `FXRateProvider`
- `MarketContextProvider`

Their qualifying methods must declare `StandardResponse[T]`. HaruQuantAI-owned
implementations must conform.

When an outer Data operation invokes one of these public protocols:

1. Receive the nested operation response.
2. Validate its status and required metadata.
3. Extract the raw `data` only on success.
4. Convert a failed response into a Data-owned internal error for the outer operation.
5. Preserve relevant approved error evidence.
6. Never return `StandardResponse[StandardResponse[T]]`.

Externally supplied test fakes and integrations implementing these protocols must be
updated. This is an intentional return-contract break and must be covered by
contract tests.

## 12. Request and Correlation Identity

Every response needs a valid Utils request ID.

Resolution order:

1. A validated request object's existing `request_id`.
2. An explicit valid `request_id` argument.
3. A generated `req-` UUID4 identifier at the public boundary.

An invalid caller-supplied request ID must not be silently accepted for a successful
operation. The operation should:

- Generate a valid response request ID so the error response itself is valid.
- Return the existing appropriate Data validation code.
- Identify `request_id` as the invalid field in safe details.

Existing correlation identifiers should be propagated where a current request or
result contract provides one. The migration must not invent business correlation
relationships.

## 13. Metadata Policy

Every Data response uses:

```text
domain = "data"
places_trade = False
```

Metadata is static per operation and describes what the operation can do, not only
what happened on one particular invocation.

### 13.1 Pure operations

Examples:

- Quality calculations.
- Deterministic transformations.
- UTC validation.
- Timeframe lookup.
- Gap classification.
- Synthetic generation that performs no I/O.

Classification:

```text
risk_level = "none"
read_only = True
writes_file = False
modifies_database = False
places_trade = False
requires_network = False
```

### 13.2 Local or database reads

Classification:

```text
risk_level = "low"
read_only = True
writes_file = False
modifies_database = False
places_trade = False
requires_network = False
```

Reading a file is not `writes_file=True`. Reading a database is not
`modifies_database=True`.

### 13.3 Provider/source reads

Classification:

```text
risk_level = "low"
read_only = True
requires_network = True
```

The other mutation flags remain false.

If an operation can resolve either a local or network source, declare
`requires_network=True` conservatively because the operation can require network
access.

### 13.4 In-memory state mutation

Examples include registry or feed lifecycle state that changes without a file or
database write.

Classification:

```text
risk_level = "low" or "medium"
read_only = False
writes_file = False
modifies_database = False
places_trade = False
```

### 13.5 File writes

Classification:

```text
risk_level = "medium"
read_only = False
writes_file = True
```

### 13.6 Database writes

Classification:

```text
risk_level = "medium"
read_only = False
modifies_database = True
```

### 13.7 Destructive or schema-sensitive storage operations

Restore, retention deletion, migrations, and recovery operations should use:

```text
risk_level = "high"
read_only = False
```

Set `writes_file` and `modifies_database` according to the operation's actual
capability.

### 13.8 Extensions

Data currently returns raw business values rather than a generic Data envelope.
Therefore, most operations should use:

```python
extensions={}
```

Do not move fields from:

- `MarketDataset`
- `DataQualityReport`
- `StorageManifest`
- `MigrationResult`
- `TransactionResult`
- `VolumeResult`
- `AccountStateSnapshot`
- `MarketContextEvidence`
- `FXConversionEvidence`
- Or any other raw Data contract

into `metadata.extensions`.

Extensions are only for genuine non-payload envelope evidence that existed before
the migration or is required by the shared response contract.

## 14. Functional Requirements

Add the following requirements to the authoritative Data README.

### FR-DATA-130

Every qualifying Data public operation returns Utils-owned `StandardResponse[T]`.
The raw result `T` is stored directly in `data`; success and error branches are
exclusive; execution duration uses a monotonic clock and is expressed in milliseconds
rounded to three decimal places; metadata declares static risk and side-effect
capabilities; nested standard responses are forbidden.

### FR-DATA-131

Every qualifying Data public operation maps failures through the approved Data or
common error catalogue, preserves all safe prior `DataError` evidence, rejects
unapproved codes, redacts unsafe diagnostics, and allows cancellation or
process-control exceptions to propagate.

Update existing requirements:

- `FR-DATA-013`: `DATA_ERROR_MANIFEST` uses the Utils-owned immutable
  `ErrorDefinition` contract.
- `NFR-DATA-008`: governed operation responses carry request/correlation and duration
  evidence.
- `NFR-DATA-010`: existing Data result contracts remain compatible as the raw value
  inside `data`.
- `NFR-DATA-011`: the package root remains the sole approved boundary and retains
  exactly 207 exported names.
- `NFR-DATA-012`: response-shape, error-branch, metadata, timing, and raw-result
  preservation are tested for all qualifying operations.

All existing feature requirements remain in force.

The Data README contains narrative requirement-count statements that may not match a
simple current-text inventory. The coding agent must reconcile the authoritative
requirement rows and usage functions before updating any count. It must not silently
delete, renumber, or merge requirements.

## 15. Consumer Coordination

The planning-time production call-site scan found required changes in Strategy and
Research.

### 15.1 Strategy

Files:

- `app/services/strategy/checkpoints/store.py`
- `app/services/strategy/migrations/definitions.py`
- `app/services/strategy/registry/_mutations.py`
- `app/services/strategy/registry/listing.py`
- `app/services/strategy/registry/parameters.py`
- `app/services/strategy/registry/registration.py`
- `app/services/strategy/registry/resolution.py`

Affected Data operations include:

- `execute_transaction`
- `run_domain_migrations`
- `persist_audit_event`

Required behavior:

- Inspect `status` before reading `data`.
- Fail closed on malformed or failed Data responses.
- Preserve Strategy's current domain error semantics.
- Do not migrate Strategy public operations in this phase.
- Do not import Data private cores.

### 15.2 Research

Files:

- `app/services/research/data/preparation.py`
- `app/services/research/data/validation.py`

Affected Data operation:

- `to_ohlcv_dataframe`

Required behavior:

- Validate success before using the DataFrame.
- Treat absent data as a failure.
- Translate Data error evidence into existing Research failure semantics.
- Do not migrate Research public operations in this phase.

### 15.3 Additional consumers

Tests and usage programs in these domains directly call Data public operations:

- Indicators
- Simulator
- Strategy
- Research
- Optimization
- Portfolio
- System integration

The coding agent must rerun the cross-domain call-site search. Any newly discovered
production consumer is part of a plan delta unless it is a direct, necessary
adaptation to the approved Data return-contract change.

Consumer rules:

- Never access `.data` before checking success.
- Never interpret `data=None` as a valid non-null business result.
- Never catch `DataError` around a public operation that now reports expected failure
  in-band.
- Never reach into `app.services.data` private implementations to retain the old raw
  return behavior.
- Do not add compatibility wrapper functions.

## 16. Test Plan

### 16.1 New focused tests

Create:

- `tests/data/unit/test_standard_responses.py`
- `tests/data/integration/test_standard_response_boundaries.py`

The coding agent may extend an existing focused test instead of creating a duplicate
only when the existing file clearly owns that responsibility. Any such change must be
documented in its dry run.

### 16.2 Required response tests

Test all of the following:

- Every one of the 130 candidates declares and returns `StandardResponse[...]`.
- Only the two approved exclusions remain non-standard.
- Exact five-field top-level serialization.
- Missing or additional top-level fields fail validation.
- Raw result type and runtime identity are preserved where applicable.
- Mapping proxies serialize without replacing the runtime object.
- No public operation returns a nested standard response.
- A successful raw `None` remains valid.
- Error responses require `data=None`.
- Every current Data code appears exactly once.
- Unapproved codes fail catalogue validation.
- Every legacy `DataError` field is preserved in its approved destination.
- Raw exception text and secrets are absent.
- Invalid request IDs produce valid traced error responses.
- `execution_ms` is non-negative, monotonic, and rounded to three decimals.
- Static risk and side-effect metadata match the operation registry.
- All Data operations declare `places_trade=False`.
- Async cancellation propagates.
- Public protocol implementations and consumers agree.
- The package root still exports exactly 207 names.
- Imports remain side-effect free.

### 16.3 Existing Data tests

Update only operation-calling tests under:

- `tests/data/unit/`
- `tests/data/integration/`

Algorithm-focused unit tests may test a private raw core when that is the actual unit
under test, but each public operation must still have direct response-boundary tests.

The implementation agent must produce an exact changed-test list in its final report.
It must not blanket-format unrelated test files.

### 16.4 Standalone usage evidence

Update all fifteen numbered programs:

- `tests/data/usage/01_contracts.py`
- `tests/data/usage/02_market_data.py`
- `tests/data/usage/03_local_datasets.py`
- `tests/data/usage/04_synthetic_data.py`
- `tests/data/usage/05_tick_derivation.py`
- `tests/data/usage/06_persistence.py`
- `tests/data/usage/07_quality.py`
- `tests/data/usage/08_transformation.py`
- `tests/data/usage/09_time_sessions.py`
- `tests/data/usage/10_sources.py`
- `tests/data/usage/11_economic_calendar.py`
- `tests/data/usage/12_realtime_feeds.py`
- `tests/data/usage/13_data_jobs.py`
- `tests/data/usage/14_evidence.py`
- `tests/data/usage/15_audit.py`

Each usage program must:

- Call public operations through `app.services.data`.
- Assert or visibly demonstrate response status.
- Access raw values through `data`.
- Demonstrate at least one relevant error branch.
- Preserve realistic, bounded, secret-safe input.
- Remain directly executable.

### 16.5 Consumer tests

Run and update the focused Strategy and Research tests corresponding to the production
consumer files. Also run directly affected Indicators, Simulator, Optimization,
Portfolio, and system tests discovered by the refreshed call-site scan.

Do not migrate those domains' own public response contracts in this phase.

## 17. Documentation Plan

Update:

- `app/services/data/README.md`
- `app/services/data/contracts/README.md`
- `app/services/data/market_data/README.md`
- `app/services/data/local_datasets/README.md`
- `app/services/data/synthetic_data/README.md`
- `app/services/data/tick_derivation/README.md`
- `app/services/data/persistence/README.md`
- `app/services/data/quality/README.md`
- `app/services/data/transformation/README.md`
- `app/services/data/time_sessions/README.md`
- `app/services/data/sources/README.md`
- `app/services/data/economic_calendar/README.md`
- `app/services/data/realtime_feeds/README.md`
- `app/services/data/data_jobs/README.md`
- `app/services/data/evidence/README.md`
- `app/services/data/audit/README.md`
- `app/services/strategy/README.md` where consumer behavior changes
- `app/services/research/README.md` where consumer behavior changes
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `docs/CHANGELOG.md`

Documentation must state:

- Utils owns the standard envelope.
- Data owns its raw results, error codes, and extension semantics.
- Every qualifying Data operation uses `StandardResponse[T]`.
- Raw Data contracts remain directly in `data`.
- Expected Data failures are returned rather than raised at public operation
  boundaries.
- Constructors and explicitly excluded non-operation boundaries may still raise
  validation errors.
- AI tool registration remains separate.
- Non-JSON runtime values are not automatically tool-serializable.

Do not turn `docs/CHANGELOG.md` into a second feature registry or test ledger.

## 18. Implementation Sequence

Implement in the following order.

### Slice 1 — Baseline and characterization

1. Read all authorities and current Data documentation.
2. Record `git status`.
3. Regenerate the public callable inventory.
4. Regenerate public-to-public and cross-domain call graphs.
5. Run targeted baseline tests.
6. Add characterization tests for raw values and failure evidence.
7. Stop and issue a plan delta if current behavior differs materially from this plan.

### Slice 2 — Contracts and errors

1. Adapt `DATA_ERROR_MANIFEST` to Utils `ErrorDefinition`.
2. Preserve `DataError` behavior for private cores.
3. Implement `contracts/responses.py`.
4. Add operation metadata and request-ID handling.
5. Add response/error/timing tests.

### Slice 3 — Pure operations

Migrate:

- Quality.
- Synthetic data.
- Pure transformation operations.
- Pure time/session helpers.

These operations provide the lowest-risk validation of the wrapper/core pattern.

### Slice 4 — Local artifacts and tick derivation

Migrate:

- Local CSV/Parquet loading.
- Dataset load facades.
- Tick generation.
- Parquet output.

Verify raw DataFrame, mapping, dataset, and file-artifact outcomes.

### Slice 5 — Persistence and audit

Migrate:

- Transactions.
- Locks.
- Cache.
- Dataset writing.
- Import.
- Backup/restore/retention.
- Migrations.
- Audit persistence/query.

Reverify transactionality, lock leases, migration checksums, approved paths, and
resource cleanup.

### Slice 6 — Sources and market retrieval

Migrate:

- Source protocols and local implementations.
- Registry and policy.
- Read-only proxy operations.
- Market/tick/spread retrieval.
- Symbol metadata, listing, availability, and volume.

Verify Broker response consumption and no Broker mutation access.

### Slice 7 — Evidence and economic calendar

Migrate:

- Account, market-context, and FX evidence.
- Provider protocols.
- Calendar acquisition, querying, restriction, state, persistence, and result
  convenience methods.

Verify async cancellation, provider failure propagation, freshness, provenance, and
explicit missingness.

### Slice 8 — Feeds and jobs

Migrate:

- Feed lifecycle and status.
- Backfills.
- Update-job lifecycle.
- Recovery.

Verify bounded buffers, checkpoints, leases, and fail-closed recovery.

### Slice 9 — Consumer coordination

Adapt:

- Strategy production consumers.
- Research production consumers.
- Directly affected tests and usage programs in other domains.

Do not migrate other domains' public response contracts.

### Slice 10 — Documentation and completion gate

1. Update Data and affected consumer documentation.
2. Run format, lint, typing, unit, integration, usage, coverage, and consumer gates.
3. Inspect the complete diff.
4. Verify no raw-return compatibility wrapper was introduced.
5. Produce the repository-required final report with exact files and evidence.

## 19. Validation Commands

Use targeted tests during each slice. At Data completion, run:

```powershell
uv run ruff check app/services/data tests/data
uv run ruff format --check app/services/data tests/data
uv run mypy app/services/data tests/data

uv run pytest tests/data/unit --no-cov -q
uv run pytest tests/data/integration --no-cov -q
```

Run every numbered usage program:

```powershell
Get-ChildItem tests/data/usage -File |
    Where-Object { $_.Name -match '^\d\d_.*\.py$' } |
    ForEach-Object {
        uv run python $_.FullName
        if ($LASTEXITCODE -ne 0) {
            throw "Usage failed: $($_.FullName)"
        }
    }
```

Measure Data package coverage without allowing repository-wide pytest coverage
settings to distort the scoped percentage:

```powershell
$env:COVERAGE_FILE = ".coverage.data_migration"
uv run coverage erase
uv run coverage run --branch --source=app.services.data `
    -m pytest tests/data --no-cov -q
uv run coverage report --include="app/services/data/*" --fail-under=80
```

Remove the exact temporary coverage file after verification, after resolving and
checking that it is inside the workspace.

Run targeted affected-consumer tests. The refreshed call-site scan determines the
final exact list. At minimum, include focused Strategy registry/checkpoint/migration
tests and Research data preparation/validation tests.

Run:

```powershell
git diff --check
git status --short
git diff --stat
```

Live provider validation is opt-in and must use verified development, demo, paper, or
sandbox targets. A provider outage or credential absence must not be represented as a
successful provider read.

## 20. Scope Boundaries

### Included

- Standard responses for all 130 qualifying Data public operations.
- Data response construction and consumption helpers.
- Alignment of Data error definitions with the Utils-owned shape.
- Preservation of all safe existing DataError evidence.
- Private raw-core separation needed to avoid nested responses.
- Public Data protocol return changes.
- Necessary Strategy and Research consumer coordination.
- Necessary direct consumer test/usage coordination.
- Data and affected active documentation.

### Excluded

- Changes to Data algorithms.
- Numerical-result changes.
- New data sources or providers.
- Database schema changes.
- New migrations.
- New cache behavior.
- New fallback policy.
- New retry policy.
- New agent tools or tool registration.
- Changes to Risk, Trading, Strategy, Research, Indicators, Simulator, Optimization,
  Portfolio, Analytics, or API public response contracts.
- Compatibility shims that preserve old raw public returns.
- Duplicate wrapper-only public functions.
- Live broker mutation.
- Commits or pushes.

## 21. Risks and Required Safeguards

### 21.1 Nested responses

Risk: Existing public functions call other public functions and would receive
`StandardResponse` instead of the expected raw value.

Safeguard: Private raw cores and explicit public-protocol unwrapping.

### 21.2 Protocol implementer breakage

Risk: Test fakes or external implementations of Data-owned protocols still return raw
values.

Safeguard: Update protocol contracts, owned implementations, fakes, and contract
tests atomically.

### 21.3 Non-JSON raw values

Risk: DataFrames, locks, proxies, bytes, and service objects may not be directly
serializable as AI tool results.

Safeguard: Preserve them as raw runtime `data`. Do not alter the result merely for
tool serialization. Tool registration must separately require an appropriate
serializable contract.

### 21.4 Incorrect side-effect declarations

Risk: A source-dependent operation may be marked local/read-only even though it can
perform network or persistence work.

Safeguard: Use conservative static “can perform” traits and test the operation
metadata registry exhaustively.

### 21.5 Lost error evidence

Risk: Converting raised `DataError` instances to responses could drop retry,
severity, operator, request, or safe-detail evidence.

Safeguard: Characterization tests before implementation and exact mapping tests after.

### 21.6 Invalid request IDs

Risk: An invalid caller ID prevents construction of the response needed to report the
validation failure.

Safeguard: Generate a valid response trace ID for the error response while rejecting
the caller value for operation success.

### 21.7 Dirty worktree

Risk: Earlier Utils/Brokers migration changes or unrelated owner work may be present.

Safeguard: Inspect status before every slice, preserve unrelated changes, and never
use destructive reset/clean commands.

### 21.8 External provider instability

Risk: Network usage programs may fail due to provider reachability rather than a
response-contract regression.

Safeguard: Separate contract/unit evidence from opt-in provider evidence, report the
actual external failure, and never fabricate success.

### 21.9 Baseline failures

At planning time, unrelated system-test failures had previously been observed around:

- Performance-report construction missing `correlation_id`/`created_at`.
- `LiveSession` construction missing `auth_context_source`.

The coding agent must verify whether these still exist. They are not part of the Data
migration unless the Data changes directly cause or expose them. Do not fix them under
this plan without an approved plan delta.

## 22. Rollback

Rollback must be scoped to Phase 3:

1. Remove `app/services/data/contracts/responses.py`.
2. Restore Data's previous raw public return annotations and implementations.
3. Restore the previous `DataError`/`DATA_ERROR_MANIFEST` definition.
4. Restore public protocol raw return contracts.
5. Remove Strategy and Research response-unwrapping changes.
6. Restore affected Data and consumer tests/usage programs.
7. Restore Data and affected consumer documentation.
8. Rerun the pre-migration Data and consumer baseline commands.

Do not revert:

- Utils StandardResponse infrastructure.
- Brokers StandardResponse migration.
- Unrelated owner changes.
- Unrelated dirty-worktree files.

If rollback requires destructive Git commands, obtain the repository-required
approval first.

## 23. Definition of Done

Phase 3 is complete only when all of the following are true:

- [ ] Scope strictly follows this plan and any approved plan deltas.
- [ ] The refreshed inventory accounts for every Data package-root public callable.
- [ ] All qualifying operations return `StandardResponse[T]`.
- [ ] Every exclusion is explicitly justified.
- [ ] Raw successful values remain directly in `data`.
- [ ] No nested standard response exists.
- [ ] Existing Data schemas and business outcomes are unchanged.
- [ ] Data errors use Utils `ErrorDefinition` while remaining Data-owned.
- [ ] All 36 current Data error codes are preserved or an owner-approved delta exists.
- [ ] All safe legacy DataError evidence is retained.
- [ ] Metadata timing, request identity, risk, and side-effect traits are validated.
- [ ] The package root still exposes exactly 207 approved names.
- [ ] Public protocols and implementations agree.
- [ ] Strategy and Research consumers fail closed on Data error responses.
- [ ] No other domain's public response contract was migrated.
- [ ] All fifteen usage programs pass or an honest external-only limitation is
  documented.
- [ ] Data unit and integration tests pass.
- [ ] Affected consumer tests pass.
- [ ] Data package coverage is at least 80%.
- [ ] Ruff, format, mypy, and `git diff --check` pass.
- [ ] Active documentation is updated.
- [ ] The final report lists exact changed files, commands, results, decisions,
  remaining risks, and rollback path.

## 24. Required Final Report

The coding agent's final report must include:

- Scope-compliance statement.
- Exact files changed.
- Requirements implemented.
- Response and error contracts used.
- Decisions and implications.
- Consumer adaptations.
- Tests and usage programs run.
- Exact command results.
- Coverage result.
- External-provider limitations, if any.
- Documentation updated.
- Rollback path.
- Confirmation that no commit or push occurred unless separately authorized.

