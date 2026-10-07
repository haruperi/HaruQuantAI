# Host authority and current reference tooling

Status: P00 complete for SQX145 reference readiness and owner-approved gap dispositions; static publication checks passed. Application host runtime is a separate delivery scope.

The host owns universal lifecycle, telemetry, sessions, typed capability discovery,
transport, jobs and shared resource custody. Domain numerical algorithms belong to
their owning workspace/plugin. This documentation activates no service or schema.

[Project](../../docs/PROJECT.md), [architecture](../../docs/ARCHITECTURE.md),
[evidence procedure](../../docs/dev/evidence/README.md) and `AGENTS.md` own authority.

## Registered feature

| Identity | Responsibility | Status |
| --- | --- | --- |
| `FEAT-HOST-EVIDENCE` | Host-governed reference manifests, fixtures and qualification in tests/reference | Implemented tooling; P00 reference readiness/disposition complete with recorded static passes; application/runtime qualification belongs to owning features |
| `FEAT-HOST-BOOT` | Universal host bootstrap, lifespan stages, reverse-order shutdown, readiness assessment, and browser shell HTTP composition in `app/host/bootstrap.py` | Implemented and verified; Phase 1 task 1.1 qualified |
| `FEAT-HOST-LOGGING` | Centralized application telemetry, multi-sink routing, credential/path redaction, in-memory ring buffer, and DebugConsole projection in `app/host/logging.py` | Implemented and verified; Phase 1 task 1.2 qualified |
| `FEAT-HOST-DIAG` | System capacity, process health, hardware capability inspection, and computational benchmarking in `app/host/diagnostics.py` | Implemented and verified; Phase 1 task 1.3 qualified |
| `FEAT-HOST-DISCOVERY` | Workspace and plugin discovery, manifest verification, containment security, extension slot registration, dependency resolution, and typed lifecycle attachment in `app/host/discovery.py` | Implemented and verified; Phase 1 task 1.5 qualified |
| `FEAT-HOST-RESPONSE` | Universal immutable response envelope, structured error taxonomy, and execution metadata in `app/host/response.py` | Implemented and verified; Phase 1 task 1.6 qualified |
| `FEAT-HOST-TRANSPORT` | Unified HTTP transport middleware, request correlation, session authentication, in-memory event bus, and Server-Sent Events streaming in `app/host/transport.py` | Implemented and verified; Phase 1 task 1.6 qualified |
| `FEAT-HOST-JOBS` | Hardware diagnostics, process pool allocation, budget admission, cooperative cancellation, restart reconciliation, and event broadcasting in `app/host/jobs.py` | Implemented and verified; Phase 1 task 1.7 qualified |
| `FEAT-HOST-RESOURCES` | Immutable artifact custody, content-addressed storage, path containment, Zip-Slip/expansion bomb prevention, bounded caching, and REST management in `app/host/resources.py` | Implemented and verified; Phase 1 task 1.8 qualified |
| `FEAT-HOST-PERSISTENCE` | Central SQLite persistence authority, schema migrations, narrow typed repositories, optimistic revision concurrency, cooperative leases, and restart reconciliation in `app/host/persistence.py` | Implemented and verified; Phase 1 task 1.9 qualified |

## Registered functional requirements

| Identity | Responsibility | Required logs |
| --- | --- | --- |
| `FR-HOST-EVIDENCE-ROOT-RESOLUTION` | Resolve explicit sole donor/repository roots and contain locators; never substitute donor roots. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-MANIFEST-VALIDATION` | Reject malformed, duplicate, nonfinite, oversized or incorrectly typed reference JSON; verify source identities. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION` | Reconcile current archive/resource bytes, complete member metadata and exact fingerprints/counts. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-FIXTURE-VALIDATION` | Validate independent observations, exact outputs, timestamps, source hashes and truthful static/runtime provenance. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-LEDGER-INTEGRITY` | Validate schema v4, atomic records, current sources, monotonic allocation, related records, mappings and pass artifacts. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-OWNERSHIP-GATES` | Bind current archive/features/FR seeds to proposed owners; check registered identities and reject unqualified runtime release. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-QUALIFICATION-CLI` | Run offline evidence gates by default and explicit read-only --check-donor checks; emit outcome logs and nonzero failures. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-BOOT-LIFECYCLE-STAGES` | Strict progression through ordered host lifespan stages (CONFIGURING, PATHS, LOGGING, DISCOVERY, SERVICES, ROUTES, READY). | INFO stage advances, ERROR on stage startup failure with fr_id and stage identity. |
| `FR-HOST-BOOT-REVERSE-SHUTDOWN` | Idempotent reverse-order teardown and automatic rollback of acquired stages upon startup failure. | INFO stage release events, INFO safe repeated stop, ERROR stage release failure with fr_id. |
| `FR-HOST-BOOT-READINESS-ASSESSMENT` | Comprehensive readiness checks and system health state snapshots. | DEBUG ready queries, WARNING degraded/stopped queries with structured snapshot. |
| `FR-HOST-BOOT-APP-COMPOSITION` | Lazy factory composition of FastAPI application and router mounting without import-time side-effects. | INFO composition start/finish and route mounting with fr_id. |
| `FR-HOST-BOOT-SHELL-PROJECTION` | Browser shell contract endpoints for status, readiness inspection, Home/About metadata, and settings. | INFO app-loaded acknowledgement and settings writes, DEBUG status queries with fr_id. |
| `FR-HOST-LOG-RESOLVE-NAMESPACE` | Resolve namespaces and bootstrap telemetry lazily on first runtime emission without import-time side-effects. | DEBUG on namespace initialization; fr_id structured attributes. |
| `FR-HOST-LOG-BOUND-CONTEXT` | Expose bound logger with immutable contextual key-value mapping. | Attaches immutable context key-value pairs to every emitted event. |
| `FR-HOST-LOG-SECRET-REDACTION` | Fingerprint detected credentials with deterministic SHA-256 digests before emission. | Replaces credentials with [REDACTED:<digest:12>]. |
| `FR-HOST-LOG-PATH-REDACTION` | Sanitize physical host filesystem paths to prevent local username/directory leakage. | Replaces absolute host paths with logical [PATH:<basename>] references. |
| `FR-HOST-LOG-STRUCTURED-FORMATTING` | Serialize events to bounded JSON and human-readable terminal text. | Formats records for terminal and disk with bounded 16KB size limit. |
| `FR-HOST-LOG-MULTI-SINK-ROUTING` | Demux events across app, access, debug, and error logs. | Routes events to app.log, access.log, debug.log, and errors.log. |
| `FR-HOST-LOG-WINDOWS-ROTATING-ZIP` | Enforce byte-limit ZIP rotation and retention pruning with Windows-safe file closure. | Closes open stream, renames, creates deflated ZIP, deletes raw log, and prunes older than retention_days. |
| `FR-HOST-LOG-RING-BUFFER` | In-memory bounded ring buffer with monotonic cursor tracking and gap detection. | Assigns monotonic cursors, detects gaps when client cursor is older than ring buffer. |
| `FR-HOST-LOG-DEBUG-CONSOLE-PROJECTION` | FastAPI endpoints for browser DebugConsole workspace log querying, categories, and clearance. | INFO on log queries, category discovery, and ring buffer clearance. |
| `FR-HOST-LOG-REQUEST-CORRELATION` | Scope correlation tokens across asynchronous execution boundaries using contextvars. | Injects scoped correlation tokens into concurrent async event contexts. |
| `FR-HOST-LOG-SAFE-ERROR-BOUNDARY` | Extract safe diagnostics and bounded call-site frames without sensitive tracebacks. | Captures exception class, message, and bounded call-site frames. |
| `FR-HOST-LOG-ASYNC-QUEUE` | Non-blocking bounded queue worker with backpressure drop tracking. | Discards events non-blockingly on saturation and tracks drop metrics. |
| `FR-HOST-LOG-LIBRARY-BRIDGE` | Forward and sanitize third-party standard-library loggers through telemetry engine. | Intercepts foreign logging records and routes through telemetry engine. |
| `FR-HOST-LOG-LIFECYCLE-SYNC` | Clean shutdown, queue draining, atexit cleanup, and test isolation resets. | Synchronizes queued events, releases file handles, and resets singleton state. |
| `FR-HOST-DIAG-SYSTEM-PROBE` | Probe CPU, memory, disk, and process metrics with bounded execution and explicit zero-vs-unavailable discrimination. | DEBUG on successful probes; WARNING with error details when degraded or unavailable. |
| `FR-HOST-DIAG-WORKER-ALLOCATION` | Derive worker concurrency limits from hardware capacity and validated configuration profiles. | INFO with core allocation, active mode, and bounds. |
| `FR-HOST-DIAG-THREAD-AFFINITY` | Inspect and apply process CPU core affinity where supported by OS and privilege boundaries. | INFO on affinity application; WARNING when unsupported. |
| `FR-HOST-DIAG-GPU-QUALIFICATION` | Inspect GPU acceleration availability safely without crashing or blocking host startup. | DEBUG detailing GPU device detection status. |
| `FR-HOST-DIAG-BENCHMARK-EXECUTION` | Execute bounded real computational benchmarks with wall-clock throughput measurement and cooperative cancellation. | INFO on benchmark start, completion, and cancellation; never synthesizes fake scores. |
| `FR-HOST-DIAG-PROJECTION` | Expose FastAPI REST endpoints for real-time system diagnostics and benchmark lifecycle management. | DEBUG on routine diagnostic inspection; INFO on benchmark jobs. |
| `FR-HOST-SETTINGS-SCHEMA` | Transactional SQLite `host_settings` table initialization and schema constraint verification. | Emits INFO on table creation; DEBUG on verification. |
| `FR-HOST-SETTINGS-LOAD` | Query and parse scoped configuration records into memory with defaults initialization. | Emits INFO on loading records with item count and discovered scopes. |
| `FR-HOST-SETTINGS-DOT-ACCESS` | Recursive dot-notation and dictionary-style attribute navigation. | Emits DEBUG when accessing setting attributes or namespaces. |
| `FR-HOST-SETTINGS-VALIDATION` | Validate type, range, finite values, and credentials according to ratified rules. | Emits WARNING with reason when validation rejects a payload. |
| `FR-HOST-SETTINGS-UPDATE` | Atomic batch upsert with monotonic revision and conflict detection. | Emits INFO on committed batch with changed count and updated revision. |
| `FR-HOST-SETTINGS-PATH-VALIDATION` | Validate configured workspace filesystem paths on disk. | Emits INFO when path exists; WARNING when path is absent. |
| `FR-HOST-SETTINGS-PROJECTION` | FastAPI REST endpoints for settings snapshot and updates. | Emits DEBUG on query; INFO on settings updates. |
| `FR-HOST-DISC-MANIFEST-SCHEMA` | Package identity, semver, contained entrypoints, slot declarations, and dependency metadata schema validation. | INFO on valid manifest discovery; ERROR on validation failure. |
| `FR-HOST-DISC-CONTAINMENT-SECURITY` | Strict directory containment, forbidding path traversal (`..`), symbolic link escapes, and uncontained entrypoints. | WARNING/ERROR with security violation details. |
| `FR-HOST-DISC-SLOT-REGISTRATION` | Typed host extension slots registry and attachment cardinality validation. | INFO on slot registration; WARNING on incompatible slot request. |
| `FR-HOST-DISC-DEPENDENCY-RESOLUTION` | Topological dependency ordering, missing dependency detection, and circular dependency prevention. | INFO on resolved DAG; ERROR on missing dependency or cycle. |
| `FR-HOST-DISC-CAPABILITY-INJECTION` | Typed host capability context injection into plugin factories via `PluginHostContext`. | INFO on successful capability binding and factory invocation. |
| `FR-HOST-DISC-LIFECYCLE-MANAGEMENT` | Safe attachment, activation, controlled disabling, reload, and uninstallation with resource cleanup. | INFO on lifecycle state transitions; ERROR on factory failure. |
| `FR-HOST-DISC-BROWSER-PROJECTION` | FastAPI REST projection endpoints exposing discovered packages, status, slot bindings, and lifecycle operations. | DEBUG on status queries; INFO on state mutations. |
| `FR-HOST-RESPONSE-SUCCESS-ENVELOPE` | Success envelope instantiation with automatic UTC timestamps, duration, and telemetry logging. | Emits INFO log with summary, duration, and correlation ID. |
| `FR-HOST-RESPONSE-ERROR-ENVELOPE` | Error envelope instantiation with structured error codes, messages, and retryability semantics. | Emits WARNING log with machine-readable error code, message, and correlation ID. |
| `FR-HOST-RESPONSE-SERIALIZATION` | Dictionary and JSON transformation of standard response envelopes with field validation. | Emits DEBUG log when serializing envelope. |
| `FR-HOST-TRANSPORT-MIDDLEWARE` | ASGI middleware injecting X-Request-Id, response timing, and mapping unhandled exceptions to StandardResponse. | Emits INFO on request completion with duration and req_id; ERROR on unhandled server exceptions. |
| `FR-HOST-TRANSPORT-SESSION-AUTH` | In-memory session token creation, expiration verification, and Bearer token authentication. | Emits INFO on token creation; WARNING on missing, invalid, or expired credentials. |
| `FR-HOST-TRANSPORT-EVENT-BUS` | In-memory multi-channel event broker with monotonic cursors, ring buffer history, and slow-consumer drop protection. | Emits DEBUG on publication; INFO on subscriber registration and unregistration. |
| `FR-HOST-TRANSPORT-SSE-STREAMING` | Server-Sent Events streaming with channel demux, cursor replay, snapshot gap detection, and clean disconnects. | Emits INFO on stream connect/disconnect; WARNING on queue saturation and backpressure drops. |
| `FR-HOST-TRANSPORT-REST-PROJECTION` | FastAPI transport router exposing `/auth/login`, `/auth/status`, `/events`, `/events/publish`, and `/events/snapshot`. | Emits DEBUG on transport router composition. |
| `FR-HOST-JOBS-HARDWARE-DIAGNOSTICS` | System metrics sampling (CPU cores, RAM bytes, OS platform, Python version). | Emits INFO log when hardware diagnostics are collected. |
| `FR-HOST-JOBS-POOL-ALLOCATION` | Platform-bounded multiprocessing worker pool allocation. | Emits INFO log with allocated worker counts upon process pool creation. |
| `FR-HOST-JOBS-BUDGET-ADMISSION` | Resource-guarded task admission validating worker slots and memory reservations. | Emits INFO log detailing task ID, owner, worker budget, memory reservation, and timeout. |
| `FR-HOST-JOBS-EXECUTION-LIFECYCLE` | Asynchronous task execution, timeout supervision, and lifecycle state transitions. | Emits INFO/WARNING/ERROR logs on lifecycle transitions; failures include safe code locations omitting secrets. |
| `FR-HOST-JOBS-COOPERATIVE-CANCELLATION` | Owner-scoped and job-level cooperative cancellation via JobContext checkpoints. | Emits INFO log when cancellation is requested and acknowledged. |
| `FR-HOST-JOBS-DEDUPLICATION` | Concurrent task deduplication preventing duplicate execution of identical dedup_keys. | Emits INFO when dedup key is registered or released; WARNING when duplicate submission is rejected. |
| `FR-HOST-JOBS-RESTART-RECONCILIATION` | Durable SQLite storage (`host_jobs`) reconciling orphaned or active jobs to INTERRUPTED on reboot. | Emits INFO when orphaned or active jobs from previous runs are reconciled. |
| `FR-HOST-JOBS-EVENT-BROADCAST` | Real-time broadcasting of job state updates and progress reports to the EventBus. | Emits DEBUG when job lifecycle updates and progress reports are broadcast. |
| `FR-HOST-JOBS-REST-API` | FastAPI jobs router exposing endpoints for capacity, job submission, querying, and cancellation. | Emits DEBUG when jobs router is constructed and endpoints are invoked. |
| `FR-HOST-RESOURCES-STAGING-PUBLICATION` | Stage raw bytes and files into transient custody and publish into immutable SHA-256 content-addressed store. | Emits INFO detailing resource ID, SHA-256 digest, byte size, and store path. |
| `FR-HOST-RESOURCES-CONTAINMENT-SECURITY` | Sandbox containment resolver rejecting traversal (`..`), foreign drive components, and forbidden symlinks. | Emits DEBUG on verified path; WARNING/ERROR on traversal attempts and drive escapes. |
| `FR-HOST-RESOURCES-ARCHIVE-INSPECTION` | Pre-extraction inspection of ZIP and TAR archives for entry counts, uncompressed byte limits, and compression bombs. | Emits INFO summarizing entry counts and safety; WARNING on limit violations. |
| `FR-HOST-RESOURCES-ARCHIVE-EXTRACTION` | Transaction-safe contained extraction into sandbox directory with automatic directory rollback upon failure. | Emits INFO with destination and extracted count; ERROR on extraction failure with rollback. |
| `FR-HOST-RESOURCES-BOUNDED-CACHE` | Thread-safe, byte-bounded LRU and TTL memory cache for resource payloads with hit/miss/eviction telemetry. | Emits DEBUG on hit/miss; INFO on LRU eviction events recording freed bytes and counts. |
| `FR-HOST-RESOURCES-HTTPX-ACQUISITION` | Bounded remote artifact streaming download via httpx with size limits, timeouts, and orphan rollback. | Emits INFO on acquisition success; ERROR on HTTP failures or byte ceiling violations. |
| `FR-HOST-RESOURCES-ORPHAN-CLEANUP` | Automated garbage collection of abandoned or expired staging directories to bound disk usage. | Emits INFO recording count of purged staging directories. |
| `FR-HOST-RESOURCES-REST-PROJECTION` | FastAPI REST projection endpoints exposing staging, publishing, retrieval, inspection, extraction, and cache status. | Emits DEBUG on router composition; INFO on resource mutations and query invocations. |
| `FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION` | Versioned schema migration ledger, checksum verification, and physical `PRAGMA integrity_check`. | Emits INFO on initialization and migrations; ERROR on schema drift or corruption. |
| `FR-HOST-PERSISTENCE-TRANSACTIONS` | Serialized ACID write transactions using `BEGIN IMMEDIATE` and `COMMIT;` with operational busy timeout handling. | Emits DEBUG on begin/commit; WARNING on rollback; ERROR on contention timeout. |
| `FR-HOST-PERSISTENCE-TYPED-REPOSITORY` | Narrow typed CRUD repository mapping Pydantic models to JSON payload envelopes with keyset pagination. | Emits DEBUG on queries/reads; INFO on entity creation and mutations. |
| `FR-HOST-PERSISTENCE-REVISION-CONCURRENCY` | Optimistic monotonic revision checks asserting persisted revision matches `expected_revision`. | Emits WARNING on revision conflict without silent data overwrites. |
| `FR-HOST-PERSISTENCE-LEASE-COORDINATION` | Cooperative distributed worker leases with atomic acquisition, heartbeats/renewal, and TTL expiration. | Emits INFO on acquire/renew/release; WARNING on conflict contention. |
| `FR-HOST-PERSISTENCE-RESTART-RECOVERY` | Startup reconciliation auditing physical integrity, schema readiness, and pruning dead/expired worker leases. | Emits INFO on audit start and completion; ERROR on failed integrity checks. |
| `FR-HOST-PERSISTENCE-REST-PROJECTION` | FastAPI REST projection endpoints exposing database status, schema migrations, integrity checks, and leases. | Emits DEBUG on router composition; INFO on lease and recovery actions. |

## Ratified reference decisions

Owner approved the current-only migration plan version 1 and P00 closure plan version 2 on 2026-10-06 with `APPROVED: EXECUTE`. Closure approval ratifies the two disposition decisions below; it registers no application feature or FR.

| Identity | Approved decision |
| --- | --- |
| `DEC-HOST-P00-AUTHORITY-RESTORATION` | Project/architecture and owning READMEs define current target authority; retained UI status does not establish backend service availability. |
| `DEC-HOST-P00-SCHEMA-EVOLUTION` | Strict schema version 4 binds only 145-dev1; atomic claims, classifications, limits, source locations/hashes, mapping/review/clean-room fields and truthful validation remain mandatory. |
| `DEC-HOST-P00-REGISTRY-BOUNDARY` | Register only the existing evidence tooling capability here. All application JAR/resource feature and FR allocations remain proposals until their owning feature plans ratify them. Domain READMEs own status. |
| `DEC-HOST-P00-LOGGING-ADAPTER` | Reference tooling uses explicit standard-library named loggers, structured FR identifiers and stable redacted codes. No logging configuration or I/O at import; API callers/CLI explicitly configure handlers. |
| `DEC-HOST-P00-VALIDATION-DEPENDENCY` | Use the declared and locked development jsonschema dependency for full Draft 2020-12/format validation. This migration adds no dependency. |
| `DEC-HOST-P00-BOUNDED-FIXTURES` | UTF-8 JSON reads reject duplicate keys/nonfinite numbers and exceedance of 4 MiB. Relative forward-slash locators reject traversal, absolute/drive/UNC paths and resolved escapes. Fixtures use isolated static observations; no donor writes. |
| `DEC-HOST-P00-RELEASE-GATES` | Exact static counts/hashes/order use zero tolerance. Static qualification does not establish numerical semantics, activation or runtime parity. Donor-derived claims require body/observation evidence; the limited unavailable-host-source disposition permits approved target-owned host contracts. Missing domain/runtime evidence still blocks dependent claims and release. |
| `DEC-HOST-P00-MODULE-HEADING` | Concrete Python tooling follows the five canonical module docstring sections, descriptive FR identities, explicit typed signatures and observable FR logs. |
| `DEC-HOST-SQX145-REFERENCE` | The sole reference is the downloaded 145-dev1 cohort under SQX_145_REFERENCE_ROOT. No alternate donor root, snapshot lookup, source backfill or compatibility fallback. Fresh record IDs use SQX145-EV-NNNNNN starting at 000132; preserve the allocation high-water mark. |
| `DEC-HOST-SQX145-BYTE-IDENTITY` | Fingerprint-bound published references serialize deterministically as UTF-8/LF with scoped Git attributes. Hash final bytes and reject unexplained drift; metadata shards remain bounded. |
| `DEC-HOST-P00-CLOSURE-BOUNDARY` | P00 accepts verified reference tooling/inventory, reconciled ownership proposals and explicit gap dispositions. Application registration, execution and applicable independent runtime comparisons belong to owning feature plans and release gates; P00 closure grants no runtime/parity authority. |
| `DEC-HOST-P00-UNAVAILABLE-HOST-SOURCE` | The audited MainApp/AppSettings/CpuInfo host-service bodies receive an accepted source limitation. HaruQuantAI may implement its own universal lifecycle/settings/path/CPU contracts, informed by directly inspected callers, through approved feature plans. Unsupported semantics are explicit normative target decisions. This exception covers no missing numerical, trading, AI or domain algorithm and grants no exact-translation/parity claim. |
| `DEC-HOST-SINGLE-BOOTSTRAP-MODULE` | Merged proposed bootstrap and readiness capabilities into a single canonical module `app/host/bootstrap.py` for unified lifecycle coordination and zero circular dependencies. |
| `DEC-HOST-LIFESPAN-REVERSE-SHUTDOWN` | Acquired stages during startup are tracked in an internal LIFO stack and rolled back in strict reverse order upon startup failure or teardown; repeated shutdown calls are safe and idempotent. |
| `DEC-HOST-SINGLE-LOGGING-MODULE` | Merged centralized logging, redaction filtering, rotating ZIP sinks, in-memory ring buffer, and DebugConsole projections into a single canonical module `app/host/logging.py`. |
| `DEC-HOST-SECRET-FINGERPRINTING` | Sensitive credentials are deterministically hashed with SHA-256 and redacted as `[REDACTED:<digest:12>]`, preserving auditability of repeated secrets without exposing plaintext. |
| `DEC-HOST-ZIP-ROTATION-WINDOWS` | Rotating file sinks close open file handles prior to renaming to guarantee compatibility with Windows file-locking semantics, compressing rotated logs to deflated `.zip` archives. |
| `DEC-HOST-SINGLE-DIAGNOSTICS-MODULE` | Merged system probes, CPU/memory/disk/process diagnostics, worker capacity derivation, thread affinity, GPU qualification, and computational benchmarks into a single canonical module `app/host/diagnostics.py`. |
| `DEC-HOST-REAL-BENCHMARK-MEASUREMENT` | Hardware diagnostic benchmarks perform actual bounded CPU-bound workload execution with duration and throughput measurement; synthetic or fabricated benchmark scores are prohibited. |
| `DEC-HOST-SINGLE-SETTINGS-MODULE` | Merged settings persistence store, dot-access node, validation, workspace path checks, and FastAPI router into a single canonical module `app/host/settings.py`. |
| `DEC-HOST-SQLITE-SETTINGS-STORE` | Authoritative persistence for host settings is backed by the `host_settings` table in `data/database/haruquantai.db` with atomic `BEGIN IMMEDIATE` transactions and monotonic revision tracking. |
| `DEC-HOST-SINGLE-DISCOVERY-MODULE` | Merged plugin discovery, manifest verification, slot registry, dependency resolution, capability injection, lifecycle management, and REST API projections into a single canonical module `app/host/discovery.py`. |
| `DEC-HOST-CONTAINED-PLUGIN-EXECUTION` | Plugin manifests and entrypoints are strictly bounded within declared package directories; path traversal, symlink escapes, and unverified global module paths are rejected to guarantee host security and tenant isolation. |
| `DEC-HOST-ZERO-PLUGIN-RESILIENCE` | The host runtime and browser workspaces operate seamlessly with zero installed plugins; missing or incompatible plugins degrade gracefully without blocking host boot or execution. |
| `DEC-HOST-CANONICAL-RESPONSE-ENVELOPE` | Universal immutable result envelope `StandardResponse[T]`, error taxonomy `StandardError`, and execution metadata `ResponseMetadata` in `app/host/response.py` serve as the foundational contract across host lifecycle services, HTTP transport, and domain clients. |
| `DEC-HOST-SINGLE-TRANSPORT-MODULE` | Merged HTTP transport middleware, request correlation, error handling, session authentication, in-memory event bus, and SSE streaming into a single canonical module `app/host/transport.py`. |
| `DEC-HOST-BOUNDED-SSE-STREAMING` | SSE event streams enforce bounded per-subscriber queues (`asyncio.Queue(maxsize=256)`) and monotonic cursor tracking; saturated consumers drop events without blocking server dispatch and clean up immediately upon client disconnect. |
| `DEC-HOST-SINGLE-JOBS-MODULE` | Merged hardware diagnostics, process pool allocation, budget admission, cooperative cancellation, SQLite durability, restart reconciliation, and REST endpoints into a single canonical module `app/host/jobs.py`. |
| `DEC-HOST-RESOURCE-BUDGET-ADMISSION` | Background compute jobs declare worker and memory budgets guarded by hard capacity ceilings (`CapacityExceededError`, `BudgetExceededError`) to prevent host resource starvation. |
| `DEC-HOST-RESTART-RECONCILIATION` | On coordinator initialization, active in-flight jobs (`queued`, `running`, `cancellation_requested`) stored in SQLite are reconciled to `interrupted` without fabricating false success or hanging indefinitely. |
| `DEC-HOST-SINGLE-PERSISTENCE-MODULE` | Merged database engine, connection pragmas, schema migrations, typed repositories, cooperative leases, restart recovery, and REST routes into a single canonical module `app/host/persistence.py`. |
| `DEC-HOST-ZERO-RAW-SQL-EXPOSURE` | Domain plugins and workspaces access storage exclusively through typed `PersistenceAccess` facades and `TypedRepository[T]`; raw SQL execution and direct SQLite handles are strictly forbidden. |
| `DEC-HOST-SERIALIZED-WRITE-TRANSACTIONS` | Write transactions enforce `BEGIN IMMEDIATE;` to serialize concurrent writers at transaction start, eliminating SQLite deadlock upgrades under WAL mode. |
| `DEC-HOST-OPTIMISTIC-REVISION-CONCURRENCY` | Entity updates and deletions require monotonic revision validation (`expected_revision`), raising `RevisionConflictError` on divergence to prevent split-brain overwrites. |

## Ownership and release boundaries

- [Current P00 review](../../docs/dev/evidence/sqx145/p00-review.json) retains the earlier static observations unchanged. [Host-core research](../../docs/dev/evidence/p00-host-core-research.md) records the bounded packaging/caller audit and approved disposition.
- P00 closure qualifies reference readiness and disposition of known gaps. Application features, backend/UI execution and runtime comparisons remain their own approved delivery scopes.
- MainApp/AppSettings/CpuInfo bodies remain unavailable within the audited static boundary. Universal host services can follow approved HaruQuantAI contracts under the limited disposition; settings precedence, durability, CPU policy and lifecycle must be explicit target decisions and tested before delivery.
- The 23 selected AI gaps belong to phase 19.1. Other data/trading/engine gaps remain feature-level research obligations. Existing SC-02 limits blockers to declared dependencies.
- `manifest.py`, `fixtures.py` and `validate.py` map constructors/helpers to their documented FRs. Their imports configure no handlers or filesystem activity.
- All current JAR/resource application allocations remain proposed until owning feature plans ratify them. `FEAT-HOST-JRT-FS` is a proposed JVM-only disposition, not a Python implementation obligation.
- Missing domain bodies/independent observations cannot be replaced by guessed SQX behavior. Application tests do not establish donor parity; installed-product activation remains unverified.
- Persistence schemas/migrations/transactions/retention require a ratified host capability; plugins receive focused typed interfaces and never ad-hoc SQL authority.
- Reference tooling opens no operational database and never launches the donor. Live/irreversible effects retain distinct authorization.
