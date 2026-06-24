## Phase 2 Data Foundation

### Goal

Implement the Data Foundation requirements under `app/services/data/` while preserving the phase module boundaries and governance rules.

Task inventory: 701 checkbox tasks (701 checked, 0 unchecked).

### Dependency Files and Functionality


Required functionality:

- Structured log and error envelope primitives are available.
- OHLCV dataframe quality inspection and diagnostics check.
- SQLite persistence setup and db path normalization.
- Data schemas and range check validation helpers exist.


### Functionality to Implement

Tasks are grouped by domain functionality. Each requirement is now part of its corresponding functional contract.

#### Data Gateway Service

- [ ] Scope the module as a greenfield professional production module that preserves current data-domain capabilities at the capability level (not old function names), with backward compatibility out of scope; treat the v8 specification as the authoritative baseline with this document as the production-hardening closure layer.
  - Backward compatibility remains out of scope
  - Preserve capabilities at the capability level, not old function names
  - v8 specification remains the authoritative baseline; this document is the production-hardening closure layer
- [ ] Defer public streaming subscription tools and historical market-hours reconstruction beyond Phase 1, tracking both as implementation planning issues rather than Phase 1 blockers.
  - Public streaming subscription tools remain out of Phase 1; define the future tool surface before export
  - Historical market-hours reconstruction deferred until a market-calendar provider is approved
  - Track future-phase decisions as planning issues, not Phase 1 blockers
- [ ] Implement `app/services/data/__init__.py` containing only imports and `__all__`, exporting exactly the approved official tool surface (`get_data`, `list_symbols`, `get_market_hours`) and nothing else, with any future tool addition requiring an explicit specification update.
  - Contains only imports and `__all__`
  - Exports only the approved official tool surface in Section 1.2 unless a future specification explicitly adds more
  - Exposes only safe, intentional, agent-callable tools
  - Supports `get_data`, `list_symbols`, `get_market_hours`
  - Official exports match this requirements document; downstream modules import only through `app.services.data`
- [ ] Type every official tool, require it to accept and propagate `request_id`, log structured events, and provide usage examples where applicable; never expose raw exceptions or credential loaders, and never log or expose credentials.
- [ ] Normalize all timestamps crossing the official AI-tool boundary to UTC ISO 8601 strings, including start/end timestamps when provided; disclose the primary volume value through `volume_kind`; have `get_market_hours` return current configured hours only for Phase 1.
- [ ] Reject unsafe filesystem input: parent traversal using `..`, hidden/system directories unless explicitly allowed by configuration, and unsupported extensions.
- [ ] Map deterministic failure conditions to error codes without exposing raw exceptions: `AUTHENTICATION_FAILED` on auth failure, `CIRCUIT_BREAKER_OPEN` on open circuit breaker, `PERMISSION_DENIED` on permission failure, `UNSUPPORTED_TIMEFRAME` on unsupported timeframe, `UNSUPPORTED_OPERATION` on historical market-hour reconstruction (unless an approved calendar provider supports it) and on unsupported public streaming operations, and `CREDENTIALS_MISSING` on missing credentials.
- [ ] Restrict `workflow_context` to the exhaustive set `research`, `backtest`, `validation`, `risk`, and `execution_bound`, allowing exploratory backtests to opt into `float` only when explicitly marked non-validation.
- [ ] Require start to precede end, returning `TIMESTAMP_OVERLAP` when overlap has no safe policy.
- [ ] Make state writes atomic, stale-lock recovery auditable, crash recovery idempotent and auditable, and circuit-breaker transitions auditable, returning `STATE_RECOVERY_FAILED` on failed crash recovery; enforce no-silent-fallback behavior throughout the gateway.
- [ ] Resolve credentials internally from approved configuration or environment variables: never accept raw passwords unless a future explicit security design approves it, and never expose credential loaders.
- [ ] Keep production logic free of `print()`; ensure resampling 100,000 M1 bars to H1 targets under 3 seconds; ensure labels align to input timestamps.
- [ ] Achieve coverage above 80% with production sign-off commands passing, and write tests covering: connection leak detection; conflicting ingestion key behavior; invalid input, successful call, unsupported timeframe (where applicable), empty result, request ID propagation, logging footprint, and side-effect/read-only flags for every official tool; recovery from stale locks; no-silent-fallback behavior; circuit breaker open/half-open/closed transitions; raw data hash propagation; and rejection or logging of interpolation/forward-fill outside research workflows.

#### Market Data Feeds Integration

- [ ] Bring internal real-time feed support, feed state, and feed status into scope for Phase 1 production readiness wherever a source adapter declares live or streaming capability, providing reliable, normalized, auditable access alongside historical, local, synthetic, broker, and external market data.
  - Internal real-time feed support, feed state, and feed status are in scope for production readiness
  - Internal real-time feed support in scope for Phase 1 hardening where a source declares live or streaming capability
  - Module supports an internal real-time feed layer for live tick, spread, and bar-oriented data where source adapters declare live or streaming capability
  - Module provides reliable, normalized, auditable access to historical, real-time, local, synthetic, broker, and external market data
  - Document real-time feed limitations for Phase 1
- [ ] Expose exactly one low-risk, read-only real-time feed observability tool, `get_feed_status`, reporting source, symbol, data kind, connection state, feed readiness, last heartbeat timestamp, last event timestamp, buffer depth, configured buffer capacity, dropped event count, gap count, reconnect count, circuit breaker state, and last error code, and never exposing raw stream handles, sockets, clients, credentials, or connection strings.
  - `get_feed_status` is the canonical feed observability tool
  - Module exposes one low-risk, read-only real-time feed observability tool named `get_feed_status`
  - Feed inspection added through `get_feed_status`; internal feed state observable through it for heartbeat, buffer health, dropped data, gap reconciliation, reconnects, and circuit-breaker state
  - Reports source, symbol, data kind, connection state, feed readiness, heartbeat/event timestamps, buffer depth/capacity, dropped/gap/reconnect counts, circuit breaker state, last error code
  - Read-only; does not mutate state; does not expose raw connection handles, socket details, client objects, or credential-bearing connection strings
  - Feed status requests accept feed ID, source, symbol, data kind, and request ID
  - Feed status outputs include feed ID, state, heartbeat timestamp, last event timestamp, buffer depth, dropped count, gap count, reconnect count, circuit breaker state, last error
  - Feed status exposes heartbeat health, buffer health, gap health, reconnect health, circuit breaker state, last error
- [ ] Extend the deterministic error-code list with `VALIDATION_FAILED`, `BUFFER_OVERFLOW`, `DATA_DROPPED`, `FEED_HEARTBEAT_TIMEOUT`, and `FEED_RECONCILIATION_FAILED`, returned or logged on heartbeat timeout, buffer overflow, dropped records, and failed gap reconciliation respectively.
  - `VALIDATION_FAILED`, `BUFFER_OVERFLOW`, `DATA_DROPPED` included in the deterministic error-code list
  - `BUFFER_OVERFLOW` and `DATA_DROPPED` added to deterministic error codes
  - Deterministic error-code list includes `DATA_DROPPED`, `BUFFER_OVERFLOW`, `FEED_HEARTBEAT_TIMEOUT`, `FEED_RECONCILIATION_FAILED`
  - Feed heartbeat timeout returns or logs `FEED_HEARTBEAT_TIMEOUT`
  - Feed buffer overflow returns or logs `BUFFER_OVERFLOW`
  - Dropped feed records return or log `DATA_DROPPED`
  - Failed feed gap reconciliation returns `FEED_RECONCILIATION_FAILED`
- [ ] Normalize real-time records to the same OHLCV/tick/spread contracts and UTC timestamp normalization used by historical data, flagging missing, stale, partial, conflicting, dropped, revised, or license-restricted data, and keeping feed gaps visible to downstream consumers rather than hidden by synthetic fills.
- [ ] Enforce bounded buffers and an explicit overflow policy (`halt`, `drop_and_reconcile`, or `backpressure`) for real-time ingestion, using bounded queues so ingestion never causes unbounded memory growth; `backpressure` slows ingestion without unbounded growth, `drop_and_reconcile` records a gap and attempts historical backfill if supported, and `halt` stops ingestion and requires operator/scheduler recovery.
  - Real-time feeds use bounded buffers; ingestion uses bounded queues, no unbounded memory growth
  - Overflow policy accepts only `halt`, `drop_and_reconcile`, or `backpressure`
  - Feed overflow with `backpressure` slows ingestion without unbounded memory growth
- [ ] Maintain heartbeat tracking and detect timeouts; reconnect/retry using exponential backoff with randomized jitter governed by a reconnect policy (maximum retries, backoff, jitter, maximum backoff, circuit breaker cooldown); split oversized source adapters into focused client, instrument, normalization, and live-feed modules where needed.
  - Reconnect and retry logic uses exponential backoff with randomized jitter
  - Real-time feeds maintain heartbeat tracking and detect timeouts, returning/logging `FEED_HEARTBEAT_TIMEOUT`
  - Real-time feed state is observable and resilient
  - Reconnect policy includes maximum retries, exponential backoff, jitter, maximum backoff, circuit breaker cooldown
  - Oversized source adapters split into focused client, instrument, normalization, and live-feed modules where needed
- [ ] Define and gate the promotion path for staging real-time sources: initial source readiness is `staging` for `real_time_feed_gateway` until buffer, heartbeat, recovery, gap reconciliation, and circuit-breaker tests pass, with the promotion process and evidence package for moving MT5, cTrader, Dukascopy, Binance symbol discovery, or the real-time feed gateway from `staging` to `production` defined.
- [ ] Write tests covering: dropped data gap creation; feed heartbeat tracking and timeout; feed buffer limit behavior; feed overflow under `halt`, `drop_and_reconcile`, and `backpressure`; feed reconnect with exponential backoff and jitter; and the `get_feed_status` schema.

#### Data Storage and Database Persistence

- [ ] Make SQLite the default single-node ACID-capable persistence backend (sufficient for single-node local state persistence) while keeping the persistence interface append-optimized and TSDB-ready for future high-frequency tick/spread storage without rewriting gateway routing logic; document the future backend selection and migration procedure.
  - SQLite is sufficient for single-node local state persistence; SQLite shall be the default single-node ACID-capable persistence backend
  - Persistence abstraction must be TSDB-ready for future high-frequency tick and spread storage; persistence interface shall be append-optimized and TSDB-ready
  - Persistence abstraction supports append-optimized TSDB backends in future phases without rewriting gateway routing logic, and supports a future append-optimized TSDB backend
  - Pending: select the future high-frequency tick/spread TSDB backend after the TSDB-ready persistence interface is validated
  - TimescaleDB preferred future relational time-series backend for high-frequency tick/spread persistence when multi-node or high-throughput persistence becomes required
  - InfluxDB or equivalent metrics-oriented TSDBs may be considered later for telemetry/observational data but shall not replace the canonical persistence abstraction
  - Document database migration procedure
- [ ] Derive data ingestion and backfill idempotency keys from a hash of source, symbol, data kind, timeframe, start time, end time, schema version, and normalization version, and make all database writes idempotent under retry, transactional, and able to distinguish insert, update, no-op duplicate, and conflict without silently overwriting committed data.
  - Idempotency keys derived from hash of source/symbol/data kind/timeframe/start/end/schema version/normalization version
  - Database writes include deterministic idempotency keys and are idempotent under retry
  - Database writes distinguish insert, update, no-op duplicate, conflict; conflicts return deterministic errors and never silently overwrite committed data
  - Persistence writes use transactions for atomic state changes; persistence abstraction supports append-only ingestion metadata
  - Module persists ingestion idempotency keys
- [ ] Enforce database connection pool limits, timeouts, and automatic leak detection so long-running real-time feed ingestion cannot exhaust connection pools.
  - Database persistence enforces connection limits, timeouts, leak detection
  - Persistence layer enforces connection pool limits, connection timeouts, automatic leak detection
  - Database connection pools use strict limits and timeouts
  - Long-running real-time feed ingestion shall not exhaust database connection pools
  - Write tests for connection pool limit behavior and database connection timeout handling
- [ ] Persist source circuit breaker state, source revision/raw-hash metadata, data license/attribution metadata, and feed state, so that on restart a source with a persisted open circuit breaker remains open or half-open for its configured cooldown and does not immediately hammer the failing external source, and a degraded state is persisted whenever an adapter trips a circuit breaker.
  - Module persists source circuit breaker state, source revision and raw hash metadata, data license and attribution metadata, feed state
  - Circuit breaker open state persists across restarts; degraded state persisted when adapter trips a circuit breaker
  - On restart, persisted open circuit breaker remains open/half-open for configured cooldown, no immediate hammering
  - Write test for circuit breaker state persistence across restart
- [ ] Version, audit, and make reversible all database migrations (migration ID, source schema version, target schema version, compatibility result, rollback policy where practical), enforcing backward compatibility checks or mandatory invalidation and re-ingestion; on read, safely migrate data requested with an older `schema_version` or reject with `DATA_SCHEMA_DRIFT` and re-fetch guidance.
  - Database migrations versioned, auditable, reversible where practical; include migration ID, source/target schema version, compatibility result, rollback policy
  - Schema migrations enforce backward compatibility checks, or backward compatibility / mandatory invalidation and re-ingestion
  - Older `schema_version` reads safely migrated or rejected with `DATA_SCHEMA_DRIFT` and re-fetch guidance
  - Write test for schema migration compatibility checks
- [ ] Keep all internal/raw objects (pandas DataFrames, NumPy arrays, broker SDK objects, HTTP/MCP clients, sockets, stream handles, database clients) strictly internal to adapters and never crossing the official AI-tool boundary; official tools never return raw pandas/NumPy/SDK objects, sockets, stream handles, database clients, `None`, or unstructured exceptions.
  - Internal adapters may use pandas, NumPy, broker SDKs, HTTP/MCP clients, sockets, database clients, file-system objects, but these never cross the official AI-tool boundary
  - No DataFrame, NumPy array, SDK object, stream handle, socket, or database client crosses the official tool boundary
  - Every source adapter avoids returning raw SDK, client, stream, socket, or database objects
  - Official tools never return raw pandas objects, NumPy arrays, raw SDK objects, sockets, stream handles, database clients, `None`, or unstructured exceptions
  - Write tests verifying raw DataFrame/NumPy/SDK/stream/socket/client/database objects do not cross the official boundary, and no such object leakage
- [ ] Map persistence failures to deterministic error codes (`DATABASE_ERROR`, `DB_CONNECTION_ERROR`, `DB_WRITE_FAILED`) and ensure database state never stores plaintext secrets.
  - Deterministic error-code list includes `DATABASE_ERROR`, `DB_CONNECTION_ERROR`, `DB_WRITE_FAILED`
  - Database connection failure returns `DB_CONNECTION_ERROR`; write failure returns `DB_WRITE_FAILED`; persistence failure returns `DATABASE_ERROR`
  - Database state does not store plaintext secrets
- [ ] Persist large historical datasets by reference (metadata) instead of inline when response limits are exceeded, normalize all source-specific market data into canonical internal contracts before returning or persisting, prefer Parquet as the local file format for large persisted datasets in Phase 1, and cap maximum persisted synthetic generation size at 1,000,000 records unless explicitly raised by configuration and covered by performance tests.
- [ ] Define standard response/persistence metadata for every official tool and persistence request: tool name, tool version, tool category, risk level, request ID, execution time, read-only/writes-file/modifies-database/places-trade/requires-network flags, source readiness, precision policy, and persistence flags where applicable; tools that mutate persisted state set `modifies_database=True`, retrieval-only tools keep it `False`; database persistence requests include entity type, idempotency key, schema version, normalization version, transaction metadata, and request ID where applicable; no backward-compatibility aliases unless a future phase explicitly approves a temporary migration shim.
- [ ] Write tests covering: persistence transactions; SQLite/default persistence backend initialization; database idempotency keys.

#### Data Domain Documentation and Architecture Overview

- [ ] Place this requirements document in `docs/planning/DOMAIN.md` (it covers the full data module rather than one sprint) and document: the official tool catalog; the final `__all__` export list; the environment variable reference; the crash recovery runbook; circuit breaker behavior and recovery procedure; and the production sign-off template.

#### Data Ingestion Scheduler and Cron Orchestrator

- [ ] Resolve the scheduler naming conflict by exporting exactly `create_data_update_job`, `start_data_update_job`, `stop_data_update_job`, `run_data_update_job_once`, and `get_data_update_job_status` as the authoritative scheduler lifecycle/status tools, explicitly excluding `create_update_job`, `start_update_job`, `stop_update_job`, and `get_update_job_status` from official exports.
  - Scheduler naming conflict resolved by exporting only the `*_data_update_job*` names for lifecycle/status
  - `get_data_update_job_status` is the canonical scheduler status tool; status inspection added through it
  - `get_update_job_status`, `create_update_job`, `start_update_job`, `stop_update_job` are not official exports and shall not be exported as official tools
  - Authoritative scheduler lifecycle tool names are `create_data_update_job`, `start_data_update_job`, `stop_data_update_job`, `run_data_update_job_once`
  - Support the following: `create_data_update_job`, `start_data_update_job`, `stop_data_update_job`, `run_data_update_job_once`
- [ ] Implement each scheduler lifecycle tool with its specific contract: `create_data_update_job` creates persisted update job definitions; `start_data_update_job` starts recurring execution for a valid existing job or valid schedule and never behaves as a one-time run when schedule is omitted; `run_data_update_job_once` executes one immediate update run without creating a recurring schedule; `stop_data_update_job` stops or disables scheduled execution; `get_data_update_job_status` inspects job state without mutating scheduler state, is read-only, non-networked unless job metadata requires source health lookup, and is low-risk while the other scheduler tools are medium-risk.
  - `create_data_update_job` creates persisted update job definitions
  - `start_data_update_job` starts recurring execution for valid job/schedule, not a one-time run when schedule omitted
  - `run_data_update_job_once` executes one immediate run, no recurring schedule created
  - `stop_data_update_job` stops or disables scheduled execution
  - `get_data_update_job_status` inspects job state without mutating scheduler state, read-only, non-networked unless source health lookup required
  - Scheduler tools medium-risk except `get_data_update_job_status` (low-risk, read-only)
  - Module exposes one low-risk read-only scheduler status tool named `get_data_update_job_status`
- [ ] Define job and request schemas: scheduler job requests include job name, source, symbol(s), optional timeframe(s), schedule, storage target, data kind, request ID; job definitions include job ID, job name, source, symbols, timeframes, data kind, storage format, storage path, optional start/end, optional schedule, enabled flag, created/updated timestamps; job status outputs include job ID, state, enabled flag, last run status, last checkpoint, last error, next scheduled run, lease status, recovery state, request ID; job names are stable, non-empty, and safe for file/database keys; scheduler state values are `created`, `running`, `stopped`, `failed`, `completed`, `recovering`; schedules are parseable and bounded; scheduler jobs default to a maximum of 500 symbols and 20 timeframes per job unless configuration/tests approve larger workloads; scheduler frequency is no more frequent than once per minute unless a dedicated live-feed ingestion mechanism is used; scheduler and cache tools include side-effect metadata.
- [ ] Make scheduler job lifecycle explicit, idempotent, and crash-recoverable: duplicate job creation is idempotent or returns a deterministic duplicate-job error; starting an already-running job never creates duplicate workers silently; jobs left `running` after a crash idempotently transition to `recovering` or `failed` per recovery policy and never remain indefinitely `running`; recovery never marks incomplete jobs as completed; scheduler jobs use checkpointing, idempotency, lease-based locks, retry policy, cache policy, path policy, license policy, and crash recovery policy; module persists scheduler job state.
- [ ] Implement chunked, resumable, checkpointed historical backfill with default chunk sizes of 100,000 records or 30 calendar days (whichever first) for OHLCV bars and 1,000,000 records or 1 calendar day (whichever first) for ticks/spreads: backfill jobs persist progress by source, symbol, data kind, timeframe, start, end, schema version, normalization version, chunk ID, idempotency key; a chunk is not marked complete until records, metadata, quality report, source revision metadata, license metadata, and persistence manifest are committed; backfill jobs detect gaps before and after ingestion; backfill idempotency keys derive from source, symbol, data kind, timeframe, start, end, schema version, normalization version; backfill jobs include source, symbols, timeframes, data kinds, start, end, chunk policy, destination, schedule/one-time mode, recovery policy, request ID, metadata options; historical requests support chunk size, backfill mode, gap resolution policy, overlap policy, data version policy, precision policy, workflow context, persistence target where applicable.
- [ ] Persist backfill checkpoints and recover deterministically: recovery resumes from the last committed checkpoint (not the last attempted record); stale locks expire per configured lease timeout; crash recovery logs the lease-expiration reason; backfill and recovery events are auditable; corrupted state returns `STATE_RECOVERY_FAILED` or `CHECKPOINT_CORRUPTED`, corrupted checkpoint specifically returns `CHECKPOINT_CORRUPTED`; persistence errors never mark jobs or chunks as complete; recovery never duplicates committed chunks.
  - Deterministic error-code list includes `CHECKPOINT_CORRUPTED`
- [ ] Reconcile real-time gaps through historical backfill where supported and configured: if overflow policy is `drop_and_reconcile`, immediately flag a data gap, update feed gap-count metadata, emit `DATA_DROPPED` or `BUFFER_OVERFLOW`, and trigger historical backfill for the missing window when the source supports it; real-time buffer overflow flags gaps and triggers backfill when configured and supported.
- [ ] Enforce license metadata before any storage, scheduler export, or artifact generation: external/vendor data sources include license metadata before data is stored, exported, scheduled, or used in validation/risk/execution-bound workflows; missing license metadata fails closed with `LICENSE_RESTRICTION` for storage, scheduler, export, validation, risk, execution-bound workflows; backfill jobs enforce the same license restriction.
  - Deterministic error-code list includes `JOB_NOT_FOUND`, `SCHEDULER_ERROR`
  - Missing scheduler job returns `JOB_NOT_FOUND`; scheduler errors return `SCHEDULER_ERROR`
- [ ] Define the module's concurrency, rate-limiting, and observability model: use `asyncio` for real-time feed ingestion/network I/O and `multiprocessing` or chunked batch processing for heavy synthetic generation/large historical backfills to prevent event-loop blocking and GIL contention; maintain a global thread/async-safe rate-limit token bucket per source so concurrent scheduler jobs, feeds, and agent requests collectively respect external API rate limits; propagate the same `request_id` through logs, response metadata, adapter logs, cache logs, scheduler logs, feed logs, and persistence audit records where feasible; official tools convert adapter, gateway, cache, persistence, scheduler, and feed exceptions into standard error responses.
- [ ] Define the module's internal layering and persistence/feed-state scope: internal layers for contracts, responses, validation, normalization, quality, timeframes, cache, registry, gateway routing, source adapters, storage, persistence, transforms, generators, labeling, scheduler, feed state, versioning, precision, rate limits, licensing, and audit logging; SQLite as the default ACID-capable single-node persistence backend for scheduler state, feed state, cache metadata, checkpoints, idempotency keys, audit state; a persistence abstraction for scheduler state, feed state, cache metadata, source revisions, license metadata, data manifests, checkpoints, idempotency keys, circuit breaker state, audit events; real-time feed state persists feed leases, heartbeat state, buffer metadata, last processed timestamp, last committed checkpoint, gap windows, reconnect count, circuit breaker state; live data persisted only through explicit persistence/scheduler/feed-ingestion/storage workflows; feed configuration includes source, symbol, data kind, optional timeframe, buffer capacity, overflow policy, heartbeat timeout, reconnect policy, backfill-on-gap flag, persistence target, request ID; quality reports included for fetched, loaded, generated, resampled, aggregated, and backfilled data.
- [ ] Produce a central limits manifest (maximum records, date range, cache TTL, synthetic generation size, backfill chunk size, feed buffer depth, scheduler frequency) and document: why `get_data_update_job_status` and `get_feed_status` are included; usage examples for market data, local storage, symbols, synthetic generation, labeling, scheduler, job status, feed status; troubleshooting for MT5, cTrader, Dukascopy, Binance symbol discovery, local storage, cache, database persistence, scheduler, crash recovery, feed health; response examples for OHLCV, tick, spread, market hours, trading sessions, availability, historical volume, scheduler status, feed status, error responses; ensure a production sign-off artifact is created before release.
- [ ] Write tests covering: backfill chunking, idempotency, source revision handling; automatic historical backfill after dropped data where supported; backfill checkpoint resume; backfill cache invalidation; recovery from corrupted checkpoints; dry-run behavior for cache, scheduler, and file operations where applicable; license restriction enforcement for storage, scheduler exports, and backfill; scheduler create/start/stop/run-once; duplicate start and duplicate job creation behavior; missing job behavior; invalid source/symbol/timeframe/schedule; scheduler state persistence.

#### External Vendor Data Source Connectors

- [ ] Provide one internal broker/data gateway interface that routes a single internal request contract to many external source APIs (MT5, cTrader, Dukascopy, Binance, and future approved providers), using adapter capability declarations and enforcing source readiness before execution.
  - Broker/data gateway is internal and routes one internal contract to many external APIs
  - Module provides one internal broker/data gateway interface routing one internal request contract to many external source APIs
  - Internal gateway routes one internal request format to many source adapters
  - Gateway uses adapter capability declarations before execution; enforces source readiness before execution
  - Gateway enforces credential policy, source readiness, rate limits, retry policy, circuit breaker policy, license policy, source revision policy, normalization policy, quality policy, precision policy consistently across adapters
  - Source registry provides internal adapter lookup and registration; not exported as an official AI tool unless a future requirement explicitly approves it
  - Write tests for adapter capability declarations, adapter readiness levels, source registry lookup/registration, and source registry non-export
- [ ] Implement the common internal source adapter protocol: every adapter validates source-specific requirements, fetches/loads raw source data, converts raw fields into normalized records, preserves source metadata, maps source errors to deterministic internal errors, supports circuit breaker state, avoids logging secrets, and exposes no direct official AI tool functions; mark adapters `production`, `staging`, `experimental`, or `not_available`, with unavailable adapters failing safely and deterministically and preserving safe source context plus request ID in errors.
  - Every source adapter implements a common internal source protocol, validates source-specific requirements, fetches/loads raw data, converts to normalized records, preserves source metadata, maps errors deterministically, avoids logging secrets
  - Source adapters expose no direct official AI tool functions; support circuit breaker state
  - Source adapters marked `production`/`staging`/`experimental`/`not_available`; unavailable adapters fail safely and deterministically
  - Adapter errors preserve safe source context and request ID
  - Naive timestamps exist only inside source adapters before normalization
  - Write tests per adapter for source-specific normalization, deterministic error mapping, missing optional dependency behavior, mocked network/client failure, and no secret leakage
- [ ] Keep broker-capable adapters strictly read-only in the data module: broker adapters never place trades, close positions, modify account state, modify terminal settings, or modify risk settings; MT5 adapter specifically never places orders or modifies broker state; the module overall never places trades, closes positions, modifies broker account/terminal/risk settings, or performs execution actions.
- [ ] Implement the MT5 adapter: initial source readiness `staging` until live credential, broker, timeout, and data validation tests pass; secure credential resolution from environment/config kept inside the adapter/client layer; symbol listing, OHLCV bars, tick data where available, symbol metadata/details, timeframe mapping, UTC timestamp normalization, broker timezone metadata, broker-unavailable error handling; write test for MT5 credential redaction.
- [ ] Implement the cTrader adapter using the approved cTrader adapter/MCP boundary: initial source readiness `staging` until client-boundary, network, and normalization tests pass; supports symbol listing, bar loading, cTrader bar normalization, timeframe mapping, source metadata preservation, deterministic network/client errors; raw cTrader client construction stays internal; write test for cTrader client-boundary behavior.
- [ ] Implement the Dukascopy adapter: initial source readiness `staging` until historical/live capability, rate-limit, and normalization tests pass; supports instrument discovery, internal instrument metadata lookup, historical OHLCV/tick fetch where implemented, source interval mapping, live/stream-oriented fetch where supported (represented as an internal adapter capability), normalization, HTTP/network handling, retry/timeouts, source metadata preservation; client internals stay internal; split into smaller client/instruments/normalization/source/live modules if oversized; defer public Dukascopy streaming subscription tools until a later specification explicitly approves public streaming tools; write test for Dukascopy historical/live capability representation.
- [ ] Implement Binance support as symbol-discovery only via `list_symbols(source="binance")`: initial source readiness `staging` for symbol discovery only, and Binance support never becomes a trading or execution adapter inside the data module; write test for Binance symbol-discovery-only behavior.
- [ ] Normalize records consistently across all sources: OHLCV records normalize timestamp, open, high, low, close, volume, tick volume, real volume, spread, source, symbol, timeframe (preserving both tick volume and real volume when a source provides both); tick records normalize timestamp, bid, ask, last, volume, spread, source, symbol; spread records normalize timestamp, symbol, bid, ask, spread points, spread pips, source; symbol metadata normalizes asset class, base/quote currency, contract size, tick size, tick value, point, digits, lot limits, lot step, margin currency, profit currency, trading hours, source metadata; `get_historical_volume` may derive volume from OHLCV, tick records, or source-native volume data if the public response contract remains stable and tested.
- [ ] Implement explicit, opt-in source fallback: `fallback_sources` is an explicit optional list on data retrieval requests, defaults to empty, and fallback never occurs unless the caller supplies it; before use, fallback validates source readiness, capability declarations, license policy, and workflow context; fallback metadata includes requested source, actual source, fallback used, fallback reason, attempted fallback chain; write test for explicit fallback source behavior.
- [ ] Enforce resilience policy on every external source call: explicit timeouts, bounded retries, rate limits, and circuit breakers; map network/source failures to deterministic codes — `TIMEOUT` on timeout, `NETWORK_ERROR` on network failure, `BROKER_UNAVAILABLE` when broker unavailable, `SOURCE_NOT_CONFIGURED` for disabled/unconfigured source, `UNSUPPORTED_SOURCE` for unsupported source, `UNSUPPORTED_OPERATION` for unsupported valid-source capability, `EMPTY_RESULT`/`DATA_NOT_FOUND` per context for empty result, `DATA_SOURCE_REVISION_DETECTED` on source revision mismatch — and include retry metadata when retries are exhausted; never immediately retry after throttling.
  - Write tests covering: rate-limit tracking, HTTP 429 handling, no-immediate-retry behavior; network timeout/429/retry/circuit breaker behavior with mocks; unsupported source per official tool where applicable; source failure per official tool
- [ ] Maintain and document a source readiness manifest and a source license manifest declaring readiness/license per source, included in source-specific response metadata and enforced by the gateway and fallback policy; historical data preserves source revision metadata where available and exposes gaps, overlaps, completeness, quality status, source readiness, license metadata, and precision policy in metadata; availability outputs include available ranges, gaps, completeness, record count, source readiness, source metadata; spread outputs include records/summaries, record count, symbol, source, start, end, quality report, source metadata, license metadata, precision metadata; a central limits manifest defines default/maximum values by data kind, source, workflow context, response mode; document a source adapter catalog alongside the readiness and license manifests.
- [ ] Never log or return credentials or secrets anywhere in the connector layer: passwords, access tokens, API keys, account secrets, broker secrets, and raw credential payloads are never logged or returned; official tools remain thin orchestration functions that validate inputs, call internal services/adapters, and return standard responses; either date range or limit is provided unless the source has a safe default.
- [ ] Write data quality tests covering adversarial market conditions: zero-volume bars, extreme spread widening (e.g. `>1000` pips), NaN/Inf values from source APIs, and flash-crash price anomalies; cover production tests for license restriction enforcement.
- [ ] Note that the HaruQuantAI Tool Function Standard, Code Quality Standard, Agent Standard, and Agentic AI Playbook exist outside this source-requirements document and may define cross-cutting details not repeated here; Phase 1 may proceed without complete external source adapter implementations when disabled/unavailable adapters fail safely and deterministically and contracts, responses, validation, timeframes, registry, exports, and tests meet Phase 1 acceptance; no blocking open questions remain for Phase 1 implementation based on current source material; cTrader and Dukascopy clients are internal.

#### File Storage and Parquet I/O Helpers

- [ ] Support `save_market_data` and `load_local_dataset` as the official local storage tools, package path `app/services/data/`: `save_market_data` saves validated normalized records to CSV or Parquet; `load_local_dataset` loads CSV or Parquet datasets into normalized records; storage requests include path, format, overwrite flag, create-parents flag, include-metadata flag, request ID.
  - Support the following: `save_market_data`, `load_local_dataset`
  - Package path is `app/services/data/`
  - `save_market_data` saves validated normalized records to CSV or Parquet
  - `load_local_dataset` loads CSV or Parquet datasets into normalized records
  - Storage requests include path, format, overwrite flag, create-parents flag, include-metadata flag, request ID
- [ ] Enforce approved storage roots and path safety on every local file operation: approved storage roots configurable only through HaruQuant settings; storage paths resolve under approved roots; absolute paths outside approved roots rejected; local paths validated against approved storage roots; documentation includes the approved storage roots list.
  - Approved storage roots configurable only through HaruQuant settings; documented
  - Absolute paths outside approved roots rejected; storage paths resolve under approved roots
  - Local file operations enforce approved storage roots and path validation
  - Storage requests validate path safety, default to `overwrite=False`
  - Unsafe path returns `PATH_NOT_ALLOWED`
  - Write test for every official tool covering path safety where applicable
- [ ] Require explicit `overwrite=True` to overwrite, returning `FILE_ALREADY_EXISTS` when an existing file is hit with `overwrite=False`, and `FILE_NOT_FOUND` for missing local files.
  - Overwrite operations require explicit `overwrite=True`
  - Existing local file with `overwrite=False` returns `FILE_ALREADY_EXISTS`
  - Missing local file returns `FILE_NOT_FOUND`
  - Write storage tests for overwrite blocked by default
- [ ] Make storage writes crash-safe: write to a temp artifact then atomically commit/rename; quarantine partial artifacts from failed writes.
  - Storage writes use temp artifact plus atomic final commit/rename semantics
  - File writes use temp files plus atomic rename or equivalent safe commit semantics
  - Storage writes quarantine partial artifacts from failed writes; partial artifacts from failed writes are quarantined
  - Write test for quarantine of partial artifacts
- [ ] Implement the CSV source adapter: initial source readiness `production`; supports loading OHLCV records, loading tick records when columns allow, saving normalized records through the storage layer; supports configurable timestamp column, delimiter, column alias mapping, strict path safety, date filtering, validation after load; naive local CSV timestamps require source timezone detection or a request-level `source_timezone` override.
- [ ] Implement the Parquet source adapter as the preferred local storage format for larger datasets: initial source readiness `production`; supports loading OHLCV and tick records, saving normalized records, preserving schema metadata where possible, date filtering, safe path validation, validation after load; naive local Parquet timestamps require source timezone detection or `source_timezone` override; loading 100,000 local Parquet records should target under 2 seconds.
- [ ] Implement metadata manifests and source-revision freshness for local datasets: storage writes include metadata manifests when `include_metadata=True`; optional source metadata may include source version, source update timestamp, raw data hash, vendor response time, remaining rate-limit quota, terminal path, adapter version; local immutable datasets have no time-based expiry when file hash and modified timestamp remain unchanged; redistribution-restricted data is never exported outside approved internal paths; write test for storage metadata preservation.
- [ ] Implement the source adapter protocol contract location and gateway routing for storage-backed sources: source adapters implement the common internal source protocol in `app/services/data/sources/base.py` or a future explicitly versioned replacement path; the gateway routes requests to adapters for CSV, Parquet, MT5, cTrader, Dukascopy, Binance symbol discovery, synthetic generation, real-time feed providers, and future approved providers; MT5 source supports terminal path handling, connection lifecycle management, symbol listing, OHLCV bars, tick data where available, symbol metadata/details, timeframe mapping, UTC timestamp normalization, broker timezone metadata, broker-unavailable errors; `workflow_context` is an explicit input wherever precision, validation strictness, storage, or downstream risk differs; implementation files remain small and single-responsibility; module is not marked production-ready until a production sign-off artifact is produced.
- [ ] Write storage tests covering valid save and load, unsupported extension rejection, and unsafe path rejection.

#### Domain Exception Handling and Error Routing

- [ ] Import and reuse all standard system exceptions and error codes (`VALIDATION_FAILED`, `AUTHENTICATION_FAILED`, `PERMISSION_DENIED`, `CIRCUIT_BREAKER_OPEN`, `UNKNOWN_ERROR`, `STATE_RECOVERY_FAILED`, `CREDENTIALS_MISSING`, and the rest of the deterministic error-code list) from `app.utils.errors` to prevent duplicate declaration, with custom data exceptions inheriting from `app.utils.errors.Error` or `HaruQuantError`; document an error-code reference covering all deterministic codes.
- [ ] Have every official tool handle errors deterministically through the standard envelope: `status` is `success` or `error`; `error` is null on success or contains a deterministic code and details on failure; official data tools use deterministic error codes throughout, never falling back to `UNKNOWN_ERROR` for expected unsupported capabilities — `UNKNOWN_ERROR` is reserved only for unexpected failures after deterministic mapping is exhausted.
- [ ] Route input-validation failures consistently: any unsupported or invalid `workflow_context` returns `INVALID_INPUT`; other input validation failures return `VALIDATION_FAILED` or `INVALID_INPUT` according to context; bad data is never silently normalized without visible warnings or errors.
- [ ] Redact secret-like values from all errors and logs.
- [ ] Write tests verifying deterministic error code mapping for every official tool, and write usage examples that show realistic workflows handling both success and error responses.

#### Data Cache Layer and TTL Manager

- [ ] Fix approved storage roots for Phase 1 to `data/raw/`, `data/processed/`, `data/cache/`, and `artifacts/data/`, and define per-data-kind cache TTL defaults: historical daily-or-higher data defaults to 86,400 seconds, intraday bar data to 3,600 seconds, tick data to 900 seconds unless the source declares a stricter freshness policy; cache TTL override is non-negative, within configured maximum, and capped at a 7-day maximum request-level override unless a source declares a stricter maximum; streaming/live data defaults to cache TTL `0` and is not persistently cached unless explicitly stored through a persistence workflow, and live data does not use persistent cache by default; document the cache TTL and invalidation policy.
- [ ] Build the cache to support key creation, reads, writes, stale detection, source revision detection, and safe clearing, with cache keys including source, data kind, symbol, timeframe, start, end, schema version, normalization version, request flags, source revision metadata, and raw data hash where available; historical requests support source, symbol, data kind, timeframe where applicable, start, end, limit, cache policy, source timezone, workflow context, fallback sources, request ID; data retrieval tools accept source, symbol, data kind, timeframe where applicable, date range, limit, cache controls, source timezone override, stale-data behavior, quality failure behavior, workflow context, fallback sources, request ID.
- [ ] Invalidate cache entries automatically whenever `schema_version`, `normalization_version`, or `raw_data_hash` changes, regardless of TTL, and document that this is the invalidation trigger; historical data includes raw data hash in cache identity when available and never silently uses stale cache entries; a new `schema_version` reads data written by the previous minor version or triggers mandatory cache invalidation and re-ingestion; historical data providers that revise old data, and source revisions generally, trigger cache invalidation or strict failure according to `DataVersionPolicy`; write tests for cache invalidation on schema version change, on normalization version change, and production tests for source revision detection plus cache invalidation.
- [ ] Govern stale cache behavior through the `stale_data_behavior` input parameter (never returning stale cache silently): default `refresh_and_return` for execution-bound workflows, forcing a source refresh before return; default `return_with_warning` for research workflows, returning stale data only with explicit warning metadata; missing cache entries are treated as cache misses triggering source fetch or deterministic failure, with stale-cache behavior never applied to missing entries; cache miss returns or logs `CACHE_MISS`, cache stale returns or logs `CACHE_STALE`.
- [ ] Make cache failures non-corrupting: cache write/read errors never corrupt successful source fetches; if source fetch succeeds but cache write fails, return source data with a warning and log the cache failure (cache write failure returns data with warning if source fetch succeeded); propagate request ID through cache reads, writes, misses, stale decisions, invalidation, and clear operations in logs.
- [ ] Implement `clear_data_cache` defaulting to dry-run, validating namespace, source filter, symbol filter, dry-run option, and allowed cache root before any destructive clear.
  - `clear_data_cache`
  - Defaults to dry-run
  - Validates namespace, source filter, symbol filter, dry-run option, allowed cache root
- [ ] Map throttling to `RATE_LIMIT_EXCEEDED` on HTTP 429 or source throttling, forbidding immediate retry after throttling, and ensure real-time reconnection avoids thundering-herd behavior after crashes, restarts, network partitions, and source throttling.
- [ ] Keep all behavior deterministic, documented, and auditable: data validation, normalization, quality scoring, timestamp handling, cache handling, source metadata, and persistence behavior are deterministic and documented; every official tool logs call start, validation failure, source failure, cache hit/miss/stale status, persistence failure, successful completion, execution time, and error code on failure; schema migration and cache invalidation events are auditable; crash recovery never bypasses validation, path policy, license policy, cache policy, source readiness policy, precision policy, or gateway policy; generated artifacts, local credentials, notebooks, temp files, `__pycache__`, and `.pyc` files are never committed.
- [ ] Write tests verifying cache hit, miss, stale, and invalidation behavior for every official tool where applicable.

#### Data Domain Models and Primitives

- [ ] Rebuild the data module as a clean, contract-driven, agent-safe, testable, maintainable domain under `app/services/data/`, with downstream modules adapting to the new contracts rather than relying on aliases.
- [ ] Implement `get_market_data`, `get_tick_data`, `get_spread_data`, and `get_historical_volume`, plus `get_symbol_metadata` and `get_data_availability`: `get_market_data` fetches normalized historical OHLCV bar data; `get_tick_data` fetches normalized historical tick data; `get_spread_data` fetches or derives normalized historical spread data; `get_historical_volume` returns volume-specific historical records or summaries and may be direct or derived from OHLCV/tick/source-native volume data if its response contract remains stable and tested; historical tick retrieval requires explicit date ranges or bounded limits and is tested; historical OHLCV and spread retrieval/derivation, and data availability/gap detection, are tested.
  - Support the following: `get_symbol_metadata`, `get_data_availability`
- [ ] Return the standard HaruQuantAI response schema from every official AI tool: status, message, data, error, metadata; error responses include status, message, error code, details, request ID, metadata; every tool has metadata and side-effect flags; write tests for standard return schema and metadata correctness for every official tool.
- [ ] Ensure all market data crossing the official AI-tool boundary is JSON-serializable and contract-compliant, storing large historical data locally and referencing it through metadata where direct response payloads would be unsafe, bounded by direct-response limits: default 5,000 / maximum 50,000 records for OHLCV bars, default 10,000 / maximum 250,000 records for spread records; data availability tools never materialize more than 1,000,000 records solely for counts unless an operator explicitly enables a bounded audit mode; converting 100,000 DataFrame rows to records should target under 3 seconds.
- [ ] Validate asset-specific and tick-specific data integrity: missing required asset-specific metadata returns/emits `MISSING_ASSET_METADATA` when the asset class and workflow require those fields (added to the deterministic error-code list); tick records validate at least one of bid/ask/last exists and `ask >= bid` when both present; symbol metadata supports asset-specific extensions for futures, options, bonds, and crypto where required; production tests cover asset-specific metadata validation, and data quality tests cover valid OHLCV pass, negative spread, and tick ask-bid violations.
- [ ] Detect data quality issues before records leave validation: duplicate timestamps, out-of-order records, missing timestamps, OHLC inconsistencies, negative volume, negative spread, stale data, partial data, and tick ask-bid violations; validation of 10,000 OHLCV records should target under 500ms; normalization, gap, overlap decisions and precision policy appear in metadata or the quality report.
- [ ] Enforce workflow-aware precision and numeric serialization policy, disclosed in metadata: numeric output defaults to `decimal_string` for `backtest`, `validation`, `risk`, `execution_bound` workflows, and may use `float` only for `research` workflows when metadata discloses the policy; precision quantization runs before records cross official boundaries when symbol metadata provides required precision; risk and execution-bound workflows fail closed on precision mismatch, returning `PRECISION_MISMATCH`; document the precision/numeric serialization policy by workflow context; write tests for precision behavior across research/backtest/validation/risk/execution-bound workflows, for `decimal_string`/`float` numeric serialization, for precision quantization, and for execution-bound precision mismatch failure.
- [ ] Enforce schema evolution rules: schema evolution requires backward compatibility or explicit invalidation and re-ingestion; schema drift returns `DATA_SCHEMA_DRIFT`; `VALIDATION_FAILED` is used for input/contract/request validation failures.
- [ ] Apply default `spread_policy` of `average`, reject invalid or unsorted ticks during aggregation unless repair is explicitly enabled, and describe the label method and parameters in labeling metadata.
- [ ] Disclose `historical_hours_supported=false` and return `UNSUPPORTED_OPERATION` for historical market-hour reconstruction until a historical calendar provider is approved.
- [ ] Write tests verifying downstream contract alignment for strategy, simulation, optimization, analytics, risk, portfolio, execution, and agentic workflows, and production tests covering downstream contract alignment; downstream contract alignment tests pass.

#### Synthetic and Backtest Mock Data Adapters

- [ ] Adopt a conservative source-readiness posture across sources: local and synthetic sources may be `production` (synthetic initial readiness is `production`); external/broker sources remain `staging` until mocked and live validation passes.
- [ ] Implement `generate_synthetic_ticks` and `generate_synthetic_bars` as dedicated official synthetic-generation tools (rather than a normal external adapter, unless future design requires source-like behavior): `generate_synthetic_ticks` supports symbol, start timestamp, number of ticks, start price, average spread, volatility, volume behavior, seed; `generate_synthetic_bars` supports symbol, timeframe, start timestamp, number of bars, start price, drift, volatility, spread behavior, volume behavior, method, seed, and supports GBM in Phase 1 (GBM synthetic generation is sufficient for Phase 1; `mean_reverting`, `trend`, and `seasonal` processes are Phase 2 extensions).
  - Support the following: `generate_synthetic_ticks`, `generate_synthetic_bars`
- [ ] Make synthetic generation deterministic when a seed is supplied, bounded by direct-response limits of 100,000 records for synthetic bars and 250,000 records for synthetic ticks, targeting under 3 seconds to generate 100,000 synthetic ticks.

#### Market Data Transformation and Resampling Utilities

- [ ] Normalize timezone handling across OHLCV, tick, spread, metadata, sessions, availability, and volume outputs: UTC at the official boundary; original source/broker timezone preserved in metadata when known; source timezone override must be a valid IANA timezone; adapters resolve DST ambiguities using explicit broker timezone mapping or the Python `fold` attribute before normalization to UTC; required source metadata includes source, requested source, actual source, source readiness, source capability declaration, schema version, normalization version, timestamp timezone, request ID, license metadata where applicable; OHLCV outputs include records, record count, symbol, timeframe, source, start, end, timestamp timezone, source timezone, schema version, normalization version, quality report, source metadata, license metadata, precision metadata.
- [ ] Implement `get_trading_sessions` and `get_market_hours` for Phase 1 with current configured hours only, deferring historical holiday/DST/broker-session reconstruction to a future `MarketCalendarProvider` abstraction using IANA timezones and exchange/broker calendar datasets behind an internal provider interface: `get_market_hours` returns timezone-aware market hours with session start/end as UTC ISO 8601 strings; `get_trading_sessions` returns normalized trading session windows and labels; source adapters declare capabilities for OHLCV, ticks, spread, symbol metadata, market hours, streaming, writes, credentials, network requirements.
  - `get_trading_sessions`
  - Pending: select the future `MarketCalendarProvider` implementation for historical holidays, daylight-saving, and broker-session reconstruction
- [ ] Implement `resample_ohlcv`, `align_multitimeframe_data`, and `aggregate_ticks_to_bars` with lookahead-leakage prevention as the default: `resample_ohlcv` accepts normalized OHLCV records, validates source/target timeframe, aggregates open as first open, high as max high, low as min low, close as last close, volume as sum, and spread per explicit `spread_policy`; `align_multitimeframe_data` prevents lookahead leakage by default (`allow_lookahead=False`, `alignment_method="last_known_closed_bar"`); `aggregate_ticks_to_bars` converts normalized tick records into OHLCV bars.
  - Support the following: `resample_ohlcv`, `align_multitimeframe_data`, `aggregate_ticks_to_bars`
- [ ] Implement `label_market_data` for deterministic historical labeling that never claims predictive value: supports LEXLB-style labels or an equivalent current deterministic labeling method, configurable lookahead horizon and threshold with input validation, and prevents lookahead leakage beyond the declared horizon.
  - `label_market_data`

#### Input Parameter Validation Helpers

- [ ] Validate every official tool's inputs and run data quality validation after normalization and before returning market data to downstream workflows, never silently interpolating, forward-filling, or repairing gaps for backtest, validation, risk, or execution-bound workflows.
- [ ] Bound and protect response payloads: direct official-tool responses use safe default limits to avoid large agent payloads; payload sizes are configurable and bounded; for responses approaching maximum limits, the module supports generator/yield patterns or chunked iteration to prevent out-of-memory conditions during serialization and payload construction; limits are positive and within configured maximums; any request exceeding configured limits returns `LIMIT_EXCEEDED`.
- [ ] Map validation/throttling failures to deterministic codes: `DATA_QUALITY_FAILED` for data-content validation failures, `LIMIT_EXCEEDED` for excessive request limits, `RATE_LIMIT_EXCEEDED` for rate limiting; recovery never duplicates committed chunks.
- [ ] Write tests covering: duplicate ingestion no-op behavior; quality failure for every official tool; duplicate timestamps (warning or failure per configured policy); out-of-order timestamps; missing timestamps and inferred gaps; OHLC inconsistency; negative volume; stale data; partial data; and production tests for timestamp gap and overlap defaults.


### Hardening Amendments

#### Persistence, lineage, calendars, and provider contracts

Requirements:

- [ ] Adopt the Phase 1.5 canonical market data contracts instead of defining duplicate Bar, Tick, Symbol, Timeframe, or DataSlice models.
- [ ] Define database migration ownership, migration naming, forward migration, rollback expectation, and schema-version recording for all persisted data stores.
- [ ] Implement data lineage metadata for provider, provider request ID, retrieved timestamp, normalized timestamp, raw source hash, transformation hash, and quality-check result reference.
- [ ] Define raw provider payload retention rules separately from canonical normalized market-data retention rules.
- [ ] Define symbol master ownership for canonical symbols, broker symbols, precision, lot size, tick size, asset class, sessions, and provider availability.
- [ ] Define market/session calendar ownership and how Data distinguishes expected session gaps from unexpected missing data.
- [ ] Define backup and restore policy for historical data, cache data, normalized datasets, data-quality reports, and provider metadata.
- [ ] Create golden dataset fixtures used by Data, Indicators, Strategies, Simulation, Analytics, Optimization, and Research regression tests.
- [ ] Implement a canonical `MarketDataProvider` interface boundary for MT5, cTrader, Binance, file, database, and simulator-backed data sources.
- [ ] Ensure provider adapters return canonical contracts and never leak raw provider SDK objects across the service boundary.

### Unit Tests Required

```text

tests/unit/app/utils/

tests/unit/app/services/data/test_public_exports.py

tests/unit/app/services/data/test_quality_and_transforms.py

tests/unit/app/services/data/test_cache_storage_persistence.py

tests/unit/app/services/data/test_gateway_and_sources.py

tests/unit/app/services/data/test_feeds_scheduler.py

tests/integration/app/services/data/test_downstream_contracts.py

```

Test coverage:

- [ ] Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- [ ] Preserve the project gate of at least 80% coverage for each affected file and package.
- [ ] Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/02_data.py

```

Usage examples must show:

- [ ] `example_01_metadata_and_discovery`: Demonstrate symbol discovery, source capabilities, metadata lookup, and data availability checks.
- [ ] `example_02_historical_data_retrieval`: Demonstrate OHLCV retrieval across approved sources with standard failure handling for unavailable providers.
- [ ] `example_03_local_file_sources`: Demonstrate CSV and Parquet loading through safe paths and normalized contracts.
- [ ] `example_04_synthetic_generation`: Demonstrate reproducible synthetic bars and ticks with seeds and source manifests.
- [ ] `example_05_timeframes_sessions_and_market_hours`: Demonstrate timeframe parsing, market-hour lookup, trading sessions, and UTC normalization.
- [ ] `example_06_transformations_and_alignment`: Demonstrate resampling, tick aggregation, labeling, and lookahead-free multi-timeframe alignment.
- [ ] `example_07_cache_and_storage`: Demonstrate cache hits/misses, TTL behavior, manifests, and scoped cache clearing.
- [ ] `example_08_scheduler_jobs`: Demonstrate update-job creation, status inspection, start/stop behavior, checkpointing, and recovery surfaces.
- [ ] `example_09_feed_status_and_readiness`: Demonstrate feed heartbeat, gap/staleness status, readiness metadata, and circuit-breaker reporting.
- [ ] The single usage file must be runnable as a script and organize separate examples as focused functions.
- [ ] Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- [ ] Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.

### Quality and Documentation Standards

- [ ] All Python modules and public functions/classes must have appropriate file-level and Google-style docstrings.
- [ ] Implement unit tests for all modules and verify coverage is at least 80%.
- [ ] The implementation must pass all CI quality gates (Ruff format, Ruff check, mypy --strict, pytest, and coverage at least 80%).
- [ ] Update module README and active documentation for any architecture or API changes.


### Acceptance Checklist

- [ ] Done criterion: All 701 checkbox tasks are implemented or explicitly deferred with a documented reason.
- [ ] Done criterion: Scope stayed within this phase and approved dependency surfaces.
- [ ] Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- [ ] Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- [ ] Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- [ ] Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- [ ] Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(data-foundation): implement market data gateway and client connections



- Implement MT5, cTrader, Dukascopy, Yahoo Finance, and Binance connection clients

- Build a resilient market data gateway in `app/services/data/gateway.py`

- Setup SQLite persistence cache for bars and ticks data in `data/persistence`

- Add support for raw CSV/Parquet file ingestion and directory normalization

- Expose 24 official market data retrieval and ingestion AI tools

```
