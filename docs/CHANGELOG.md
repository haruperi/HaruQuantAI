# Changelog

## [Unreleased]

### Changed

- `CHG-009` Central settings and logger boundary: Made `app.utils.AppSettings` the
  sole repository `.env` loader, removed the exported dotenv/named-secret helpers,
  moved DATA and API composition to immutable typed settings, and changed provider
  usage/integration profiles to typed `SecretStr` fields. DATA production code no
  longer reads `os.environ`; isolated examples use explicit context-local settings.
  Normal services import only `logger`; the first runtime emission loads centralized
  logging settings, while configure/flush/shutdown remain specialized override and
  lifecycle APIs.
- `CHG-008` Shared logging defaults: Kept Utils imports side-effect-free while
  making the first runtime global bound-logger emission atomically activate the approved
  default console and bounded-file profile. Normal callers now import only
  `logger`; explicit logging configuration and lifecycle functions remain available
  for specialized overrides. Concurrent first use is idempotent, and an existing
  explicit profile is never replaced by lazy activation. Import-time log attempts
  remain inert and cannot create handlers, threads, directories, or files.
- `CHG-007` Data usage examples: Replaced the pytest-shaped usage directory with
  eight standalone, feature-ordered scripts and one cross-feature `usecases.py`
  cookbook. Added runnable examples for provider and local historical reads, cache,
  sessions, resampling, tick/bar transforms, no-lookahead alignment, symbol merging,
  synthetic data, update-job lifecycle, cache cleanup, boundary classification, and
  quality/lineage inspection. Real provider calls are explicitly opt-in; the default
  integration path remains deterministic and offline.
- `CHG-006` Data completion reconciliation: Aligned the final package inventory,
  receiver-owned audit contracts, injected provider/broker boundaries, exact public
  signatures, feature-owned limits, persisted-state ownership, validation commands,
  and completed Data contract statuses across the Data README, project registry, and
  architecture record.
- `CHG-004` Build Prompts: Merged Prompt 1 (Domain implementation roadmap) and Prompt 2 (Implement one feature) into a single Prompt 1 (Domain audit and feature implementation), renumbering Prompt 3 and Prompt 4 accordingly.
- `CHG-005` Authoritative specification reconciliation: Rebuilt the Data domain
  specification into dependency-ordered contract, storage, source, access,
  processing, job, feed, and public-API requirements with exact typed signatures,
  side effects, deterministic failures, persisted-state ownership, export boundaries,
  and runnable usage/unit-test locations. Standardized Data schema IDs on
  `data.*.v1`, separated pure evidence contracts from access-layer acquisition,
  retained fail-closed broker/provider release gates, reconciled completed Brokers
  contracts in the project registry, and removed stale cTrader network-gap language.
  The all-features roadmap remains an approval envelope; implementation proceeds one
  bounded feature per approved cycle. No Data implementation status was advanced by
  this documentation-only change.

### Added

- `ADD-028` Runnable Data usage suite: Added feature-focused examples for contracts,
  storage, sources, access, processing/tabular behavior, jobs, feeds, market context,
  FX, and the package root. The integration runner executes each standalone usage
  script in an isolated subprocess without relying on a fixed test count.
- `ADD-027` Typed Domain Boundary: Implemented the package root with exactly 23
  approved typed operations for retrieval, reference, storage, processing, jobs, and
  feeds, backed by one focused `public_api/operations.py` facade and exact export tests.
- `ADD-026` Internal Real-Time Feed Lifecycle (`FR-DATA-046` to `FR-DATA-048`):
  Implemented contract-owned feed schemas, bounded `halt`, `drop_and_reconcile`, and
  `backpressure` overflow policies, durable heartbeat/gap/reconnect/breaker evidence,
  restart-safe breaker restoration, reconciliation, and read-only derived status.
- `ADD-025` Update Jobs and Historical Backfills (`FR-DATA-041` to `FR-DATA-045`):
  Implemented contract-owned job schemas, atomic lease acquisition, stable
  idempotency, prepared publication, finalize/recovery checkpoints, and truthful
  create/start/stop/run-once/status scheduling.
- `ADD-024` Deterministic Market-Data Processing (`FR-DATA-036` to `FR-DATA-039`, `FR-DATA-080` to `FR-DATA-084`): Implemented the data processing package (`processing/`). Added `timeframes.py` for canonical timeframe specs and duration checks, `transforms.py` for resampling, backward-alignment, and tick-aggregation, `synthetic.py` for deterministic GBM price path generation, and `tabular.py` for private DataFrame serialization, datetime UTC sorting, and OHLC/OHLCV validation checks. All unit/usage tests pass successfully with 100% style compliance and all files exceeding the 80% coverage gate.
- `ADD-023` Market evidence orchestration (`FR-DATA-030` to `FR-DATA-035`,
  `FR-DATA-075/076`, `FR-DATA-078/079`): Implemented historical/reference/session
  reads plus caller-injected market-context, FX-rate, and calendar providers. Account
  evidence remains a caller-owned Brokers `BrokerAdapter` read in `sources/broker.py`.
- `ADD-022` Data source policy and caller-owned reads (`FR-DATA-022` to
  `FR-DATA-028`): Implemented the provider-neutral source protocol, lazy explicit
  registry, required source policy, durable attempts/readiness/rate/breaker state,
  atomic promotion audit, explicit fallback, and injected read-only broker/external
  adapters without owning provider lifecycle or credentials.
- `ADD-021` Data persistent storage features (`FR-DATA-014`, `FR-DATA-016`, `FR-DATA-017`, `FR-DATA-018`, `FR-DATA-019`, `FR-DATA-020`, `FR-DATA-021`, `FR-DATA-077`): Completed the Data Persistence Infrastructure implementation by creating `datasets.py` (atomic CSV/Parquet loads/saves), `cache.py` (TTL-bound local caching), and `audit.py` (governed, keyset-paginated audit event logging). Wrote full unit and usage tests verifying correctness and ensuring >80% branch coverage (datasets.py at 80%, cache.py at 92%, audit.py at 97%).
- `ADD-020` Data context and FX acquisition (`FR-DATA-076`, `FR-DATA-079`):
  Implemented fail-closed acquisition through caller-injected providers, explicit
  freshness/missingness, deterministic allowed-path selection, and exact Decimal
  conversion evidence; no stub or guessed provider default remains.
- `ADD-019` Data domain migrations (`FR-DATA-015`): Implemented the domain
  migration runner `run_domain_migrations` with exclusive database write locking,
  idempotent ledger table creation, applied migration history tracking, strict
  order and checksum validations, atomic step-wise execution inside bounded SQLite
  transactions, and redacted error mappings. Verified on Python 3.14: unit and usage
  tests pass, Ruff and strict mypy are clean, and migrations.py branch coverage is 95%.
- `ADD-018` Data path-scoped write leases (`FR-DATA-016`): Reconciled the
  lock-before-migrations dependency by making `data_write_locks` the sole explicit
  call-time bootstrap table. Added required no-default
  `WRITE_LOCK_LEASE_SECONDS`, caller-owned request IDs, atomic SQLite UPSERT
  acquisition, deterministic active-owner conflicts, exact-owner context release,
  and bounded prior-owner/recovery-time/count evidence for stale takeover. Imports
  perform no configuration or persistence work. Focused locking tests cover conflict,
  release, and stale recovery behavior.

- `ADD-017` Data bounded SQLite transactions (`FR-DATA-014`): Added call-time,
  fail-closed `DATABASE_URL` / `DATA_DIR` / busy-timeout validation, one short-lived
  Python 3.14 PEP 249 transaction per caller-owned statement plan, bounded normalized
  result rows, deterministic busy/locked classification, SQLite authorizer guards
  against caller transaction control and database attachment, atomic rollback, and
  redacted error mapping. Focused unit, usage, and boundary tests cover transaction
  success, authorization, result bounds, and atomic rollback.

- `ADD-016` Data canonical contracts (`FR-DATA-001`–`008`, `010`–`013`,
  `075/076`, `077`–`079`): Added the complete immutable,
  provider-neutral Section 4.1 vocabulary for UTC market records, source/license
  evidence, datasets and quality/availability, read-only account snapshots,
  market-context and FX evidence, deterministic errors, audit paging, handle-free
  storage, reference, job/backfill, and feed schemas. Added exact package exports,
  JSON-safe frozen mappings, fail-closed license validation, requirement-named
  usage/unit/integration tests, including Data-owned audit query/page contracts over
  Utils-owned audit event envelopes.

- `ADD-001` Shared contracts: Added immutable `AuthContext v1` and bounded redacted `AuditEvent v1` contracts.
- `ADD-002` Errors: Added typed shared errors, normalized metadata, safe exception mapping, and injected event routing.
- `ADD-003` Identity: Added validated prefixed UUID4 generation, validation, and deterministic stable identifiers.
- `ADD-004` Time: Added injected UTC clocks, strict timestamp parsing and formatting, age calculation, and freshness checks.
- `ADD-005` Serialization: Added bounded JSON-safe conversion and deterministic canonical JSON serialization.
- `ADD-006` Security: Added denylist-first redaction, password hashing, Fernet encryption, and active secret-version selection.
- `ADD-007` Settings: Added immutable Pydantic runtime settings, explicit environment loading, and secret-reference resolution.
- `ADD-008` Logging: Added source-aware structured logging, scoped console color, queued delivery, rotation, redaction, and specialized file routing.
- `ADD-009` Brokers (partial): Added adapter-local circuit/subscription runtime, lazy explicit registry, fail-closed provider adapters and mappings, and deterministic broker test utilities. Package completion remains blocked by provider/runtime evidence, the pending Yahoo probe-symbol decision, and package-wide validation gates.
- `ADD-010` Brokers contracts: Completed the canonical provider-neutral V1 boundary with exact enums, immutable redacted/UTC DTOs, stable results/errors/pages, focused async protocols, adapter schema metadata, deterministic unsupported defaults, exact exports, and one unit plus runnable usage test for every mapped public requirement.
- `ADD-011` Brokers runtime/registry/provider completion: Added the full targeted unit and integration test suite for `runtime/`, `registry/`, `mt5/`, `ctrader/`, `binance/`, `dukascopy/`, `yahoo/`, and `testing/` (348 pytest tests total), plus `NFR-BRK-007`/`NFR-BRK-010` security and performance test coverage.
- `ADD-012` Utils dotenv/credential helpers: Added `app.utils.settings.load_dotenv_file` and `resolve_named_secrets` — business-neutral, domain-agnostic helpers for composition-root-style credential resolution from a dotenv file plus the process environment. Used by the Brokers usage scripts that exercise real MT5/cTrader demo credentials; Utils still resolves no domain contract and owns no broker-specific settings model. These helpers were subsequently removed by `CHG-009` when `.env` loading was centralized in `AppSettings`.
- `ADD-013` Brokers standalone real-usage scripts: Added `tests/brokers/usage/{02_runtime,03_mt5,04_ctrader,05_binance,06_dukascopy,07_yahoo,08_registry,09_testing}.py`, matching the `tests/utils/usage/NN_*.py` numbered convention — each number is the file's Section 4 subsection (`03_mt5.py` is §4.3 `mt5/`, etc.), and no `test_` prefix or `_usage` suffix is used since the `usage/` folder name already says what the files are. These are standalone, non-pytest-collected scripts (`example_*()` functions, `if __name__ == "__main__":`) run directly via `python`, demonstrating genuinely real behavior instead of fixtures: a real MT5 demo-terminal connection and account read, a real Binance testnet connection (public endpoints need no credentials) with real symbol/kline reads, real Yahoo Finance historical-bar reads (both the no-probe and `probe_symbol` connect paths), and a real (network-permitting) Dukascopy tick fetch. cTrader's script validates real demo credentials at construction time and genuinely attempts `connect()`, honestly reporting the real fail-closed outcome since no network transport exists yet. `09_testing.py` demonstrates `FakeBrokerAdapter` itself, which is the one legitimate use of a fake in this directory. `contracts` (§4.1) and the package root (§4.10) keep the pre-existing pytest-collected convention (`test_usage_contracts.py`, `test_usage_public_api.py`).

- `ADD-014` Brokers observability (`NFR-BRK-008`): Added redacted structured logging across the domain — centralized at the shared adapter result/state-transition/unsupported sinks (`contracts/protocols.py`), plus the runtime circuit breaker and subscription, the registry factory, and every provider transport (MT5, cTrader, Binance, Dukascopy, Yahoo). Each record binds provider, environment, operation, request ID, result, provider code, and measured latency through `logger.bind(...)` (redaction-safe; no secret or full account identifier is ever bound). Added `tests/brokers/unit/test_observability.py` log-capture coverage. Also aligned `pyproject.toml` `ruff target-version` to `py314`. Verified on Python 3.14: `ruff` and strict `mypy` clean, the 3-test observability suite and the full 391-test domain suite pass, and package branch coverage is 92.25%.

- `ADD-015` Brokers cTrader live transport: Added `ctrader/network.py` — a concrete Spotware Open API client that closes the previously stubbed network gap. It runs a single process-wide Twisted reactor on a daemon thread (Option A: shared reactor, per-session isolation), performs the application→account-list→account-auth→trader handshake, and exposes an async `send` that bridges reactor Deferreds to asyncio via `reactor.callFromThread`/`loop.call_soon_threadsafe`. `CTraderBrokerAdapter` now builds this client as the default transport `sender` (the injected-transport seam is preserved for tests), and `connect()`/`disconnect()` drive and release it with a canonical `BROKER_CONNECTION_FAILED` on handshake failure. SDK/Twisted imports are lazy (import-safe); no protobuf/SDK object crosses the adapter boundary. Verified live against Spotware's demo servers via `tests/brokers/usage/04_ctrader.py` (`connect(): success`); `ruff`, strict `mypy` (37 files), and the full 391-test domain suite pass at 92.02% coverage. Added `twisted`/`twisted.*` to the mypy `ignore_missing_imports` overrides; live-only reactor paths are marked `# pragma: no cover`.

### Fixed

- `FIX-004` DATA completion review: Corrected twelve review groups covering boundary
  ownership and safe errors; explicit configuration/IDs/Decimal values; injected
  sources and durable readiness; historical cache/fallback/provenance; schedule,
  context, FX, and account evidence; migration-only schemas; recoverable backfill
  publication; feed policy/reconciliation/restart state; exact public exports and
  tabular safety; runnable traceability tests; and authoritative documentation.
  Cache TTL/clear limits now fail before persistence access, raw exceptions and
  sensitive details do not cross public/log boundaries, and status reads are
  mutation-free.
- `FIX-001` Brokers registry release gate: `registry/catalogue.py`'s static capability catalogue marked every operation `UNAVAILABLE` unconditionally, including `connect`/`is_connected` — so no adapter created through `create_broker_adapter()` could ever connect or report its own state, regardless of implementation. Fixed by marking `connect`/`is_connected` `AVAILABLE` when implemented (the adapter's own verification act and a purely local state read); every other capability remains gated by credential-verified release evidence exactly as before.
- `FIX-002` MT5 false-success on failed verification: `mt5/adapter.py::connect()` returned `status="success"` when account/server verification failed via the boolean `verified` check (as opposed to a caught transport exception), because `self._last_error` was never set on that path and `_result()` derives `status` from `error` truthiness. Fixed by constructing a `BROKER_CONNECTION_FAILED` error before returning on that path.
- `FIX-003` Yahoo zero-duration bar / `DEC-BRK-001` resolved: every Yahoo-mapped bar set `closing_timestamp == opening_timestamp`, violating `BrokerBar`'s own ordering invariant and making every real bar construction raise. Resolved the open `probe_symbol` decision by adding an explicit, optional `probe_symbol` field to `BrokerConnectionConfig`; `YahooBrokerAdapter.connect()` now performs a genuine verification probe when a symbol is configured and verifies transport/session only otherwise (never a hidden default symbol). `yahoo/mapping.py` now derives the closing timestamp from the parsed provider interval.

### Status

- Utils foundation is implemented and verified: 74 domain tests pass on Python 3.14 with `ruff`, `ruff format --check`, and strict `mypy` clean; measured branch coverage is 84.77% (≥ 80% gate).
- The Utils-owned scope of `WF-UTL-001` (structured logging and redaction) is complete. `WF-UTL-002` (settings bootstrap) and `WF-UTL-003` (audit-event construction) remain `Partial`: the Brokers `BrokerConnectionConfig v1` injection and Data audit-persistence handoffs land with those domains.
- Shared `AuthContext v1` and `AuditEvent v1` are implemented and tested on the Utils
  producer side and consumed by Data audit storage; their system rows remain
  `Partial` pending the registered Risk and UI/API consumers.
- Data is `Completed`: contracts, persistence, sources, access, processing, jobs,
  feeds, and the 23-operation facade pass the complete domain-scoped unit,
  integration, usage, contract, import-safety, typing, formatting, and coverage gates.
- Brokers remains `Partial` package-wide (`NFR-BRK-008` structured-observability logging is implemented and verified on Python 3.14 — 391 domain tests pass at 92.25% coverage, and `WF-BRK-004` submit-one-mutation stays `Missing` pending the Trading domain), but every other feature (`contracts`, `runtime`, `registry`, `mt5`, `ctrader`, `binance`, `dukascopy`, `yahoo`, `testing`) is now `Completed` at the file/FR level: 391 targeted pytest unit/integration tests pass plus 8 standalone real-usage scripts run successfully outside pytest, `ruff check`, `ruff format --check`, and strict `mypy app/services/brokers` are clean, and branch coverage over `app/services/brokers` is 92.02% (≥ 80% gate). `DEC-BRK-001` is resolved. MT5, Binance, and Yahoo each have a genuine verified real connection (MT5 against a real demo account with a real account read; Binance against the real testnet, whose public market-data endpoints need no credentials; Yahoo against the real Yahoo Finance service). cTrader now connects live to Spotware's demo servers via the `ctrader/network.py` handshake, verified by `04_ctrader.py` (`connect(): success`). Dukascopy's real host (`datafeed.dukascopy.com`) is unreachable from this environment's network specifically — confirmed by a direct HTTPS probe showing Yahoo and Binance are reachable from the same environment while Dukascopy times out. Two pre-existing defects were found and fixed while adding tests: the registry's static capability catalogue permanently blocked `connect`/`is_connected` on every real adapter, and MT5's `connect()` could report `status="success"` on a failed account/server verification.

### Changed

- `CHG-001` Brokers specification: Resolved the implementation-readiness blockers by fixing Data/Brokers symbol ownership, composition-root configuration injection, `BrokerResult[None]`, bounded FIFO streaming, transport circuit breaking, contract registration, exact enum/schema vocabularies, provider/profile capability and configuration matrices, dependency order, per-file FR assignments, lazy exports, and the complete test manifest. No Brokers implementation status was advanced by this documentation change.
- `CHG-002` Brokers progress reporting: Reconciled implemented-but-unverified README rows to `Partial`, retained mutation workflow and structured-observability work as `Missing`, and added an evidence matrix that explicitly records untested provider connections, passing deterministic checks, coverage, and remaining release gates.
- `CHG-003` Brokers contract blockers: Replaced the underspecified order product-field bag with the exact V1 MT5/cTrader-compatible field vocabulary, added read-only adapter contract/schema metadata, assigned shared Utils dependencies explicitly, and separated boundary completion from downstream provider fulfillment. Provider adapters now consume their private fail-closed defaults from `contracts/protocols.py`; `contracts/unsupported.py` owns only deterministic unsupported-result construction and the shared UTC clock bridge.
