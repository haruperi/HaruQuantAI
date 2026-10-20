# Host Platform Registry (`app/host`)

Status: Stage 0 (`P00`) reference qualification and evidence infrastructure active.
Host runtime services (`F01`) belong to Stage 1 (`1A`–`1G`) and are registered when their approved implementation plans execute.

[Project Charter](../../docs/PROJECT.md), [Architecture](../../docs/ARCHITECTURE.md),
[Evidence Procedure](../../docs/dev/evidence/README.md), and [AGENTS.md](../../AGENTS.md) govern authority.

## Registered feature

| Identity | Responsibility | Status |
| --- | --- | --- |
| `FEAT-HOST-EVIDENCE` | Host-governed reference manifests, fixtures, and clean-room ledger qualification in `tests/reference` | Implemented tooling (`Stage 0` / `P00`); static reference readiness verified; application runtime qualification belongs to owning Stage 1–7 features |
| `FEAT-HOST-PERSISTENCE` | Isolated SQLite WAL persistence, 25-table CRUD operations, and atomic batch transactions | Implemented runtime persistence (`Stage 1` / `1A` — `app/host/persistence.py`); WAL mode, schema DDL, 25-table CRUD, canonical HostPersistence functions (`create_record`, `create_entity`, `read_records`, `read_entity`, `update_record`, `update_entity`, `delete_record`, `delete_entity`), and atomic batch transactions (`apply_batch`) |
| `FEAT-HOST-SETTINGS` | Read and atomically update operational settings through persistence with revision checks | `SettingsManager` safe snapshots/catalogue, validated field patches and canonical record mapping; `HostPersistence.apply_batch()` checks revisions in the write transaction; single `settings` export with nested access |
| `FEAT-HOST-SESSION` | Operator session management, opaque token issuance, password hashing, and restart invalidation | Implemented host auth (`Stage 1` / `1B`); 24h opaque bearer tokens, PBKDF2-HMAC-SHA256 password hashing, restart invalidation, and scope authorization |
| `FEAT-HOST-TELEMETRY` | Multi-sink logging in data/logs, recursive secret redaction with SHA-256 fingerprinting, and 2000-record live ring buffer | Implemented runtime telemetry (`Stage 1` / `1C` & `1G` — `app/host/logging.py`); multi-sink file logging (app.log/access.log/errors.log), secret scrubbing & SHA-256 fingerprinting, and `deque(maxlen=2000)` buffer |
| `FEAT-HOST-RESOURCES` | System diagnostics, psutil hardware/storage/DB inspection, $\max(1, \text{cpu\_cores} - 2)$ worker allocation, $<15\%$ RAM memory watchdog, and per-job scratch sandboxing | Implemented resource governance (`Stage 1` / `1D` — `app/host/resources.py`); hardware/DB/workspace probes, worker sizing, memory watchdog, and scratch sandboxes |
| `FEAT-HOST-JOBS` | Multiprocessing background job coordinator (`ProcessPoolExecutor`), cooperative cancellation tokens (`JobContext`), and startup orphan job reconciliation (`RUNNING` $\to$ `INTERRUPTED`) | Implemented job coordinator (`Stage 1` / `1D` — `app/host/jobs.py`); GIL-bypassing process pool, memory-pressure gating, cooperative cancellation, and restart recovery |
| `FEAT-HOST-DISCOVERY` | Dynamic plugin discovery engine, manifest validation, extension slot registry, topological dependency resolution, isolated module loading, and thread-safe lazy lifecycle management | Implemented plugin discovery engine (`Stage 1` / `1E` — `app/host/discovery.py`); 1-level/2-level/AST scanning, containment guard, DAG resolution, `RLock` lazy instance registry, and FastAPI inspection router |
| `FEAT-HOST-RESPONSE` | Bounded public operation response envelope (`ApiResponse[T]`), structured error classification (`StandardError`), and execution metadata (`ResponseMetadata`) | Implemented response envelope (`Stage 1` / `1F` — `app/host/response.py`); immutable `success()`/`failure()` factories, invariants, and JSON dictionary serialization |
| `FEAT-HOST-TRANSPORT` | FastAPI gateway, ASGI request-correlation and exception-envelope middleware, in-memory multi-channel asynchronous `EventBus`, SSE (`/events`), WebSocket (`/ws`), and REST endpoints (`/auth`, `/settings`, `/diagnostics`, `/resources`, `/jobs`) | Implemented transport gateway (`Stage 1` / `1F` & `1G` — `app/host/transport.py`); `TransportMiddleware`, `EventBus` (`jobs`, `system`, `logs`, `databanks`, `settings.changed`), SSE/WS streaming, and shell/auth/settings/diagnostics/jobs routes |
| `FEAT-HOST-BOOT` | Progressive 7-stage host bootstrap state machine (`CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES -> ROUTES -> READY`), service coordinator, and reverse-order LIFO teardown | Implemented progressive bootstrap (`Stage 1` / `1G` — `app/host/bootstrap.py`); `AppHost` 5-method public lifecycle (`startup`, `initialize_db`, `register_modules`, `broadcast_event`, `shutdown`) and reverse LIFO teardown |
| `FEAT-HOST-MAIN` | Main UI and FastAPI/Uvicorn web server entrypoint (`app/main.py`) executing the 7-stage host bootstrap and ASGI server lifecycle | Implemented UI/server entrypoint (`Stage 1` / `1G` — `app/main.py`); config resolution, `create_app`, `run_server`, and `--check-only` verification |
| `FEAT-HOST-CLI` | Headless CLI entrypoint (`app/cli.py`) executing the 7-stage host bootstrap and dispatching commands without starting a web server | Implemented headless CLI (`Stage 1` / `1G` — `app/cli.py`); `HeadlessCliRunner`, `run_cli`, and JSON/text output formatting |

## Registered functional requirements

| Identity | Responsibility | Required logs |
| --- | --- | --- |
| `FR-HOST-EVIDENCE-ROOT-RESOLUTION` | Resolve explicit `SQX_REFERENCE_ROOT` and `HARUQUANTAI_ROOT` roots and contain relative locators without path traversal or fallback substitution. | DEBUG checks, INFO accepted roots, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-MANIFEST-VALIDATION` | Reject malformed, duplicate-key, nonfinite, oversized, or mistyped reference JSON; validate donor/repository manifest models. | DEBUG checks, INFO accepted counts, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION` | Reconcile donor artifact SHA-256 fingerprints, repository reference document hashes, and exact directory counts (`internal/plugins`, `internal/libs/*.jar.enc`, `internal/extend/Snippets/SQ`). | DEBUG checks, INFO accepted totals, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-FIXTURE-VALIDATION` | Validate independent static/runtime fixture observations, exact outputs, UTC timestamps, source hashes, and provenance rules. | DEBUG checks, INFO accepted case counts, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-LEDGER-INTEGRITY` | Validate Draft 2020-12 schema v4, atomic `SQX145-EV-NNNNNN` records, monotonic ID allocation, source catalog bindings, reciprocal supersession/contradiction links, and pass artifacts. | DEBUG checks, INFO checked record counts, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-OWNERSHIP-GATES` | Verify mapped `FEAT-*`, `FR-*`, and `DEC-*` identities against domain registries or explicit `proposed` status, and block premature runtime parity claims. | DEBUG checks, WARNING unresolved runtime authority, INFO checked mappings, ERROR stable failure codes; structured `fr_id`. |
| `FR-HOST-EVIDENCE-QUALIFICATION-CLI` | Execute offline evidence qualification by default and optional read-only `--check-donor` verification; emit structured outcome logs and nonzero exit codes on failure. | INFO start and completion status, ERROR failure diagnostics; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-CREATE` | Execute parameterized single-row and entity creation (`HostPersistence.create_record()`, `HostPersistence.create_entity()`) in SQLite WAL mode with idempotent 25-table schema provisioning. | INFO on record creation; DEBUG on query execution; ERROR on failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-READ` | Execute parameterized queries, filtering, and deterministic cursor pagination (`HostPersistence.read_records()`, `HostPersistence.read_entity()`). | DEBUG on query execution with row count; ERROR on unapproved table or failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-UPDATE` | Execute parameterized updates, upserts, and optimistic revision compare-and-set (`HostPersistence.update_record()`, `HostPersistence.update_entity()`) raising `RevisionConflictError` on mismatch. | INFO on record modification; WARNING on revision conflict; ERROR on failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-DELETE` | Execute parameterized deletion with foreign-key reference guards (`HostPersistence.delete_record()`, `HostPersistence.delete_entity()`). | INFO on deletion; ERROR when blocked by foreign-key reference guards; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-BATCH` | Execute atomic multi-row batch writes (`create`, `update`, `upsert`, `delete`) and settings batches (`HostPersistence.apply_batch()`) inside a `BEGIN IMMEDIATE` transaction with all-or-nothing rollback. | INFO on committed atomic batch; WARNING on revision conflict; ERROR on rollback; structured `fr_id`. |
| `FR-HOST-SETTINGS-LOAD` | Read host settings from SQLite database via persistence read layer and package for application. | INFO settings loaded with scope count; DEBUG on setting access; structured `fr_id`. |
| `FR-HOST-SETTINGS-BATCH-UPDATE` | Atomically update multiple host settings scopes via `settings.update_batch()` with revision conflict checks (`RevisionConflictError`) and reload in-memory state. | INFO on batch settings update and revision increment; WARNING on revision conflict; structured `fr_id`. |
| `FR-HOST-SESSION-CREDENTIALS` | Secure PBKDF2-HMAC-SHA256 password hashing and constant-time verification. | INFO password hashing; WARNING on failed verification; structured `fr_id`. |
| `FR-HOST-SESSION-LIFECYCLE` | Opaque 24-hour token issuance, SHA-256 token indexing, expiration, and revocation. | INFO session created and revoked; WARNING on invalid/expired token; structured `fr_id`. |
| `FR-HOST-SESSION-RESTART-INVALIDATION` | Ephemeral host instance tracking invalidating memory sessions on host restart. | INFO session cache invalidation; structured `fr_id`. |
| `FR-HOST-SESSION-AUTHORIZATION` | Granular permission scope checks against active session privileges. | INFO access granted; WARNING access denied; structured `fr_id`. |
| `FR-HOST-TELEMETRY-ENGINE` | Asynchronous queue-based telemetry worker engine decoupling emission from disk I/O with clean flush/shutdown. | INFO startup and shutdown status; structured `fr_id`. |
| `FR-HOST-TELEMETRY-REDACTION` | Recursive scrubbing of credentials and sensitive tokens from log messages, format args, and attributes. | DEBUG filter execution; structured `fr_id`. |
| `FR-HOST-TELEMETRY-ERROR-BOUNDARY` | Fail-safe error boundary preventing formatting or sink serialization errors from impacting callers. | ERROR fallback warning on formatting failure; structured `fr_id`. |
| `FR-HOST-TELEMETRY-FORMATTING` | Exact millisecond-precision event formatting with console ANSI colorization and clean plain-text files. | DEBUG formatting diagnostics; structured `fr_id`. |
| `FR-HOST-TELEMETRY-SINKS` | Multi-sink output (app.log, errors.log, access.log) with Windows-safe 10MB rotation and 30-backup retention. | INFO sink creation and rotation; structured `fr_id`. |
| `FR-HOST-TELEMETRY-RINGBUFFER` | Live thread-safe in-memory ring buffer for streaming recent structured telemetry events to DebugConsole. | DEBUG query and buffer status; structured `fr_id`. |
| `FR-HOST-TELEMETRY-BOUND-LOGGER` | TelemetryLogger adapter supporting dynamic contextual attribute accumulation via .bind() and facade methods. | DEBUG context binding; structured `fr_id`. |
| `FR-HOST-TELEMETRY-CORRELATION` | Request correlation context propagation across asynchronous tasks and worker threads via contextvars. | DEBUG correlation token lifecycle; structured `fr_id`. |
| `FR-HOST-TELEMETRY-LAZY-BOOTSTRAP` | Public module exports resolving namespaces and bootstrapping telemetry lazily without import side-effects. | INFO lazy engine activation; structured `fr_id`. |
| `FR-HOST-RESOURCES-WORKSPACE-DIRS` | Inspect configured directory existence from `settings.workspace_paths`. | INFO available directories; WARNING absent directories; structured `fr_id`. |
| `FR-HOST-RESOURCES-PROBE-DATABASE` | Perform read-only database probe checking existence, WAL size, and table inventory. | DEBUG on probe success; WARNING if missing; ERROR on read failure; structured `fr_id`. |
| `FR-HOST-RESOURCES-PROBE-CPU` | Probe CPU logical/physical core topology, frequency, and load via `psutil`. | DEBUG on probe completion; WARNING on telemetry exception; structured `fr_id`. |
| `FR-HOST-RESOURCES-PROBE-MEMORY` | Probe physical host RAM capacity, available headroom, and utilization via `psutil`. | DEBUG on probe completion; WARNING on telemetry exception; structured `fr_id`. |
| `FR-HOST-RESOURCES-PROBE-DISK` | Probe filesystem volume capacity and free space percentage. | DEBUG on probe completion; WARNING on telemetry exception; structured `fr_id`. |
| `FR-HOST-RESOURCES-PROBE-PROCESS` | Probe current host Python process memory RSS, CPU load, threads, and uptime. | DEBUG on probe completion; WARNING on telemetry exception; structured `fr_id`. |
| `FR-HOST-RESOURCES-PROBE-STORAGE` | Verify write accessibility and disk space of workspace log and database directories. | DEBUG on storage probe completion; structured `fr_id`. |
| `FR-HOST-RESOURCES-PROBE-HARDWARE` | Gather consolidated CPU and RAM hardware telemetry snapshot. | DEBUG on hardware probe completion; structured `fr_id`. |
| `FR-HOST-RESOURCES-PROBE-HEALTH` | Aggregate database, storage, and hardware probes into `HostHealthReport`. | INFO healthy status; WARNING degraded; structured `fr_id`. |
| `FR-HOST-RESOURCES-WORKER-ALLOCATION` | Derive worker concurrency limits using $\text{workers} = \max(1, \text{cpu\_cores} - 2)$ default policy. | INFO on worker allocation and capacity calculation; structured `fr_id`. |
| `FR-HOST-RESOURCES-CORE-AFFINITY` | Inspect and apply OS process CPU core affinity where supported. | INFO on affinity applied; WARNING when unsupported or denied; structured `fr_id`. |
| `FR-HOST-RESOURCES-GPU-ACCELERATION` | Safely inspect GPU acceleration availability without startup blocking. | DEBUG detailing GPU device detection status; structured `fr_id`. |
| `FR-HOST-RESOURCES-BENCHMARK` | Execute bounded deterministic CPU benchmark with cooperative cancellation. | INFO on benchmark start and completion; structured `fr_id`. |
| `FR-HOST-RESOURCES-MEMORY-WATCHDOG` | Active memory monitor rejecting or pausing tasks when available system RAM drops below 15%, plus data-frame/cleanup guards. | DEBUG when headroom healthy; WARNING/ERROR when available RAM $< 15\%$; structured `fr_id`. |
| `FR-HOST-RESOURCES-SCRATCH-SANDBOX` | Allocate and clean up isolated per-job temporary scratch directories. | INFO on sandbox allocation and cleanup; ERROR on traversal attempt; structured `fr_id`. |
| `FR-HOST-JOBS-POOL-LIFECYCLE` | Manage `ProcessPoolExecutor` worker pool lifecycle sized by $\max(1, \text{cpu\_cores} - 2)$. | INFO on process pool initialization and graceful shutdown; structured `fr_id`. |
| `FR-HOST-JOBS-SUBMISSION` | Submit, execute, and track jobs across `QUEUED`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, and `INTERRUPTED` states. | INFO on job submission and completion; ERROR on task failure; structured `fr_id`. |
| `FR-HOST-JOBS-WATCHDOG-GATE` | Enforce the 15% available RAM watchdog on task admission and execution, rejecting or pausing tasks under memory pressure. | WARNING when jobs are paused or rejected due to RAM $< 15\%$; structured `fr_id`. |
| `FR-HOST-JOBS-CANCELLATION` | Cooperative cancellation and progress reporting across worker processes via `JobContext` tokens. | INFO when cancellation is signaled and when a job terminates early; structured `fr_id`. |
| `FR-HOST-JOBS-RECONCILIATION` | Mark orphan jobs left in `RUNNING` state as `INTERRUPTED` on system startup. | INFO on reconciliation scan; WARNING for each `RUNNING` job marked `INTERRUPTED`; structured `fr_id`. |
| `FR-HOST-JOBS-PERSISTENCE` | Persist job records and state transition events through `app/host/persistence.py` with zero `sqlite3` imports. | DEBUG on job persistence writes and queries; structured `fr_id`. |
| `FR-HOST-DISC-SLOT-REGISTRY` | Register and query typed host extension slots with single/multiple cardinality enforcement and required capability checks. | INFO on slot registration; DEBUG on slot lookup/listing; structured `fr_id`. |
| `FR-HOST-DISC-MANIFEST-SCHEMA` | Validate plugin manifests (`plugin.json` / `manifest.json` or AST `PLUGIN_MANIFEST`) against strict Pydantic schema rules, rejecting duplicate JSON keys, non-finite numbers, and oversized files. | DEBUG on manifest validation; ERROR on schema/JSON rejection; structured `fr_id`. |
| `FR-HOST-DISC-FILESYSTEM-SCANNER` | Scan 1-level, 2-level (`<slot_family>/<plugin>`), and single-file Python AST plugin layouts while quarantining malformed or duplicate plugins without crashing the host (`SC-02`). | INFO on scan start/completion; WARNING/ERROR on scan diagnostics; structured `fr_id`. |
| `FR-HOST-DISC-CONTAINMENT-GUARD` | Enforce strict directory containment within authorized plugin search roots (`verify_containment`), blocking path traversal and symlink escapes. | DEBUG on containment pass; ERROR on containment violation; structured `fr_id`. |
| `FR-HOST-DISC-DEPENDENCY-RESOLVER` | Validate required and optional inter-plugin dependencies, check semantic version bounds, quarantine circular dependencies, and compute topological load ordering. | INFO on resolved load order; ERROR on missing/incompatible/circular dependencies; structured `fr_id`. |
| `FR-HOST-DISC-LIFECYCLE-MANAGER` | Dynamically load verified plugin entrypoints via `importlib.util.spec_from_file_location` and manage `RLock`-guarded lazy instantiation (`get_instance`, `get_instances_for_slot`), caching, attach, enable, cascade disable, reload, and uninstall. | INFO on lifecycle state transitions and lazy instantiation; ERROR on runtime attachment or teardown failures; structured `fr_id`. |
| `FR-HOST-DISC-INSPECTION-API` | Expose FastAPI endpoints (`/discovery/plugins`, `/discovery/slots`, enable/disable/reload) via `create_discovery_router()`. | INFO on router creation and API lifecycle operations; structured `fr_id`. |
| `FR-HOST-RESPONSE-SUCCESS-ENVELOPE` | Construct immutable `ApiResponse.success()` envelopes with UTC timestamps, duration, and correlation metadata. | INFO on success envelope emission; structured `requirement` / `fr_id`. |
| `FR-HOST-RESPONSE-ERROR-ENVELOPE` | Construct immutable `ApiResponse.failure()` envelopes pairing `StandardError` codes, messages, and retryable flags. | WARNING on failure envelope emission; structured `requirement` / `fr_id`. |
| `FR-HOST-RESPONSE-SERIALIZATION` | Transform `ApiResponse` envelopes into JSON-safe dictionaries via `to_dict()`. | DEBUG on envelope serialization; structured `requirement` / `fr_id`. |
| `FR-HOST-TRANSPORT-MIDDLEWARE` | Inject `X-Request-Id` correlation, `X-Response-Time-Ms`, and defense-in-depth HTTP security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`), isolating unhandled server exceptions into canonical 500 error envelopes. | INFO on request completion; ERROR on unhandled server exception; structured `fr_id`. |
| `FR-HOST-TRANSPORT-SECURITY-HEADERS` | Guarantee presence of defense-in-depth HTTP security headers on all gateway responses and exception envelopes. | DEBUG on security header injection; structured `fr_id`. |
| `FR-HOST-TRANSPORT-CONNECTION-TEST` | Execute bounded socket/HTTP reachability probes, latency measurements, and DNS diagnostic checks via `ConnectionTest`. | INFO on connection ping, latency check, and network diagnosis; structured `fr_id`. |
| `FR-HOST-TRANSPORT-SERVLET-CONNECTION` | Manage connection configurations (`list_connections`, `save_connection`, `delete_connection`, `test_connection`) with secret credential redaction via `ServletConnection`. | INFO on connection CRUD operations and reachability testing; structured `fr_id`. |
| `FR-HOST-TRANSPORT-SERVLET-CONSTANTS` | Expose system constants, runtime specs, platform architecture, and memory bounds via `ServletConstants`. | DEBUG on constants and system specs retrieval; structured `fr_id`. |
| `FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE` | Transform `HTTPException` and `RequestValidationError` into `ApiResponse.failure` envelopes with field-level `ValidationIssue` diagnostics. | INFO on handler registration; WARNING on HTTP/validation exception formatting; structured `fr_id`. |
| `FR-HOST-TRANSPORT-EVENT-BUS` | Publish and subscribe to multi-channel host events (`jobs`, `system`, `logs`, `databanks`, `settings.changed`) with monotonic cursors, ring-buffer replay, and slow-consumer queue isolation. | DEBUG on event publish; INFO on subscribe/update/unsubscribe; WARNING on slow-consumer drop; structured `fr_id`. |
| `FR-HOST-TRANSPORT-SSE-STREAMING` | Stream real-time Server-Sent Events over `GET /events` with cursor replay, gap notification, and heartbeats. | INFO on SSE client connect and disconnect; structured `fr_id`. |
| `FR-HOST-TRANSPORT-WS-STREAMING` | Stream bidirectional JSON events and control frames over `WebSocket /ws` with dynamic channel subscriptions. | INFO on WebSocket connect and disconnect; structured `fr_id`. |
| `FR-HOST-TRANSPORT-SESSION-AUTH` | Authenticate operator credentials on `POST /auth/login` and validate bearer tokens on `GET /sessions/me` via `SessionManager`. | INFO on session issuance and verification; WARNING on invalid credentials or unauthorized access; structured `fr_id`. |
| `FR-HOST-TRANSPORT-GATEWAY-APP` | Assemble the FastAPI host gateway app and shell status endpoints (`/status`, `/readiness`, `/app-loaded`, `/about`, `/connections`, `/constants`, `/specs`) mounted across root, `/api/v1`, and `/api/v2`. | INFO on router creation, app initialization, and `/app-loaded` acknowledgement; structured `fr_id`. |
| `FR-HOST-BOOT-STAGE-PROGRESSION` | Validate runtime configuration, create and inspect workspace directory paths, initialize multi-sink telemetry, and instantiate backend application via `AppHost.startup()`. | INFO on stage entry and advancement; ERROR on stage failure; structured `fr_id`. |
| `FR-HOST-BOOT-PERSISTENCE-STAGE` | Initialize SQLite WAL persistence via `AppHost.initialize_db()`, verify all 25 operational tables, and reload host settings. | INFO on schema verification and table inventory count; ERROR on persistence failure; structured `fr_id`. |
| `FR-HOST-BOOT-MODULE-REGISTRATION` | Initialize and coordinate domain services (`SessionManager`, `ResourceManager`, `JobManager`, `PluginLifecycleManager`, `TransportGatewayService`, `DataManagerWorkspace`) and mount routes via `AppHost.register_modules()`. | INFO on service initialization, orphan job recovery, and route mounting; structured `fr_id`. |
| `FR-HOST-BOOT-EVENT-BROADCAST` | Provide global in-memory event bus, WebSocket broadcast, and readiness transition (`host.ready`) via `AppHost.broadcast_event()`. | INFO when transitioning to READY; DEBUG on event publish; structured `fr_id`. |
| `FR-HOST-BOOT-REVERSE-TEARDOWN` | Roll back or shut down acquired bootstrap stages in strict reverse LIFO order via `AppHost.shutdown()`. | INFO on teardown start and stage release; ERROR on cleanup exceptions; structured `fr_id`. |
| `FR-HOST-MAIN-CONFIG-RESOLUTION` | Resolve host bind address, port, debug mode, and workspace paths from CLI arguments and database settings into `AppHost.Config(headless=False)`. | INFO detailing resolved host, port, debug, and `data_dir`; structured `fr_id`. |
| `FR-HOST-MAIN-APP-FACTORY` | Compose the FastAPI application (`create_app`) bound to `AppHost` so entering the ASGI lifespan executes all 7 bootstrap stages and mounts UI/API routers. | INFO when composing the FastAPI application and binding the 7-stage runtime; structured `fr_id`. |
| `FR-HOST-MAIN-UVICORN-LIFECYCLE` | Launch the Uvicorn ASGI server (`uvicorn.run`) or run `--check-only` 7-stage verification, ensuring reverse-order stage teardown and telemetry queue draining on exit. | INFO on Uvicorn server startup, clean stop, and telemetry drain completion; structured `fr_id`. |
| `FR-HOST-CLI-BOOTSTRAP-CONTEXT` | Boot the headless `AppHost` through all 7 stages (`CONFIGURING -> PATHS -> LOGGING -> PERSISTENCE -> SERVICES -> ROUTES -> READY`) via explicit `AppHost` lifecycle methods and guarantee reverse-order LIFO teardown on exit. | INFO on headless 7-stage startup and LIFO teardown; structured `fr_id`. |
| `FR-HOST-CLI-COMMAND-DISPATCH` | Parse and dispatch headless CLI commands (`status`, `health`, `resources`, `jobs`, `plugins`, `settings`, `reconcile`) against live bootstrapped `AppHost` services. | INFO on command dispatch; WARNING/ERROR on invalid command arguments; structured `fr_id`. |
| `FR-HOST-CLI-OUTPUT-FORMATTING` | Emit structured human-readable or `--json` output envelopes (`ApiResponse`) and return deterministic POSIX exit codes (`0` on success, non-zero on failure). | DEBUG when serializing CLI command results; structured `fr_id`. |

## Ratified reference decisions

| Identity | Approved decision |
| --- | --- |
| `DEC-HOST-P00-AUTHORITY-RESTORATION` | `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and owning `README.md` files define target authority; retained React UI surfaces do not establish backend availability or parity. |
| `DEC-HOST-P00-SCHEMA-EVOLUTION` | Strict schema version 4 binds `SQX_REFERENCE_ROOT` (`145-dev1`) and `HARUQUANTAI_ROOT`; atomic claims, classifications, limitations, source locations/hashes, target mappings, clean-room flags, and truthful validation states are mandatory. |
| `DEC-HOST-P00-REGISTRY-BOUNDARY` | Only `FEAT-HOST-EVIDENCE` is registered in `Stage 0`. Application features (`F01`–`F13`) remain `proposed` until their owning stage implementation plans ratify them in domain `README.md` files. |
| `DEC-HOST-P00-LOGGING-ADAPTER` | Reference tooling uses standard-library named loggers (`get_logger(__name__)`), structured `fr_id` extras, and stable redacted error codes without import-time I/O or handler mutation. |
| `DEC-HOST-P00-VALIDATION-DEPENDENCY` | Draft 2020-12 JSON Schema validation uses the locked `jsonschema` development dependency with format checking enabled. |
| `DEC-HOST-P00-BOUNDED-FIXTURES` | UTF-8 JSON reads reject duplicate keys, nonfinite numbers (`NaN`, `Infinity`), and payloads exceeding `4 MiB`. Relative forward-slash locators reject traversal (`..`), drive letters, UNC paths, and symlink escapes. |
| `DEC-HOST-P00-RELEASE-GATES` | Static SHA-256 hashes and directory/file counts require zero tolerance (`tolerance = 0`). Static qualification never establishes runtime execution or numerical parity. |
| `DEC-HOST-P00-MODULE-HEADING` | Every concrete Python module follows `docs/templates/PYTHON_MODULE.md` with five standardized docstring sections (`Description`, `Purpose`, `Key Capabilities`, `Python API Usage`, `CLI Usage`) and non-silent `FR-*` logging. |
| `DEC-HOST-SQX145-REFERENCE` | Logical root `SQX_REFERENCE_ROOT` (accepting `SQX_145_REFERENCE_ROOT` as environment alias) identifies the read-only SQX-145 reference installation. Record IDs follow `SQX145-EV-NNNNNN` monotonically without reuse. |
| `DEC-HOST-P00-CLOSURE-BOUNDARY` | Stage 0 (`P00`) qualifies reference infrastructure, donor artifact hashes, and clean-room ledger integrity. Stage 1–7 runtime implementation and numerical parity are gated by their respective stage plans. |

### Application settings UI persistence

The [settings API contract](../../docs/dev/settings-api.md) connects Application
settings forms through transport -> SettingsManager -> HostPersistence ->
`data/database/haruquantai.db`. The manager owns field definitions, mapping and
validation. Only persistence executes SQL. Patches merge with existing group
objects and retain unknown leaves and legacy records. Account changes and session
revocation commit together. Secret reads expose presence metadata only; events
contain revision/group metadata.

Forms commit on Save; skin and zoom commit immediately. Failed/offline/stale saves
never become committed UI state. Real HTTP/SSE tests use temporary databases and
independent HostPersistence reads across UI reload and backend restart. Saving
configuration does not activate mail, remote servers, MCP, brokers or trading.

### Host audit verification boundary (Iteration 3)

Settings batch validation and writes share a `BEGIN IMMEDIATE` transaction. Empty batches keep their revision; already-active caller transactions are rejected without changing them. Bootstrap binds settings to a database path, and read failures preserve the last successful snapshot and propagate. All three file sinks use the asynchronous engine, and scrubbed fingerprinted log events reach the EventBus `logs` channel with bounded delivery on subscriber event loops. Broker diagnostics are excluded from forwarding to prevent recursion. Configured session/scope checks protect settings, diagnostics/resources, and job reads/cancellation. Service rollback also covers partial acquisition, continues after cleanup errors, and drains/stops telemetry after final lifecycle diagnostics. Job cancellation and shutdown remain cooperative at checkpoints; code that never checks its token can delay shutdown. UI rendering is outside this backend verification.

Settings snapshots and catalogue values come only from stored records. Python retains validation and access policy; the UI owns theme appearance, while the selected theme identifier is persisted as an ordinary setting.


Host event models, bounded replay and subscriber delivery are implemented in
`app/host/events.py`. `transport.py` imports these classes directly for HTTP/SSE/WS
and retains the existing lazy global bus wiring and event exports.
