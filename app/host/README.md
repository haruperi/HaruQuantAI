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
