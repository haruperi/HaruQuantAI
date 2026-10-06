# F01: ten host capabilities

Replace the P01/P02 JAR backlog with the following ten cohesive capabilities.
They belong to one host and share one lifecycle. IDs H01-H10 are V2 planning
labels, not registered FEAT/FR identities. See [architecture](architecture.md).

## H01 App/host bootstrap

**Build:** explicit configuration -> logging -> owned paths/persistence -> services
-> discovery -> routes -> readiness. Reverse acquired stages during shutdown or
failed startup. Use the FastAPI lifespan and an explicit composition function.
Imports perform no initialization. Distinguish starting, ready, unavailable and
stopping; the server listening does not prove readiness.

**Acceptance:** a fresh process boots and exits cleanly; a failed stage releases
earlier acquisitions; repeated stop is safe; missing optional domains do not block
unrelated work. The browser reads real readiness. A clean installation works
without SQX or a Java runtime.

## H02 Centralized logging

**Build:** explicitly configured standard-library named loggers and one structured
event shape, including timestamp, level, component, FR/event/outcome and relevant
request/job/resource IDs. Console, rotating file and a bounded debug projection
share redaction and lifecycle. Use `contextvars` for request correlation and
explicit worker log forwarding. Do not rebuild Java logging bridges or agents.

**Acceptance:** normal/failure/cancellation outcomes emit requirement events;
worker events correlate; secrets/physical paths are redacted before every sink;
overflow/sink failure is visible without recursive logging. DebugConsole connects,
filters and reconnects according to the approved display/cursor contract.

## H03 System and hardware diagnostics

**Build:** read-only psutil/OS observations for CPU, memory, disk/runtime health and
owned process utilization. Return unavailable probes explicitly. Compute worker
limits from observed capacity and validated settings. Benchmarking is a bounded
diagnostic job when implemented, with measured workload/environment metadata.

**Acceptance:** missing probe, invalid CPU count and timeout fail as specified;
readiness and diagnostics distinguish unavailable from zero. A failed optional
benchmark does not invent a score. Affinity/GPU flags activate only qualified
consumers; runtime probing never changes process priority or launches donor code.

## H04 Settings and configuration

**Build:** Pydantic schemas with documented defaults/precedence. Separate operational
bind/credential/data-root inputs from persisted user preferences and domain-owned
experiment settings. Atomic revision-checked preferences follow the approved P01
contract. Domain forms consume their owner's metadata; cloning a Settings JAR
creates no extra capability.

**Acceptance:** reject invalid/unknown/nonfinite values and incompatible revisions;
reload preserves accepted settings; conflicts and write failures remain visible.
Secret fields stay out of projections/logs. Changing a remote/trading/GPU/SMTP
preference does not by itself activate a service or grant authority.

## H05 Workspace and plugin discovery

**Build:** a small package-owned manifest plus explicit factory/attachment hooks.
Validate identity, version, contained entrypoint, dependencies and typed slots
before executing a contribution. Load the known workspace/plugin package roots
through injected host services. Use the same descriptions for UI availability.

**Acceptance:** missing, duplicate, malformed and incompatible contributions have
precise states; adding a concept needs no unrelated central catalog edit. A
zero-plugin workspace remains usable where possible. Disable/restart/removal
releases owned routes/jobs/subscriptions and preserves retained bytes. Begin with
startup discovery and controlled disable/restart; implement safe reload only for
contributions that require it. General hot reload is not an initial dependency.

## H06 Transport and events

**Build:** one versioned HTTP envelope, stable errors, request IDs, validated domain
routes and one bounded authenticated event mechanism. Keep the existing UI transport
factory; domains own their payloads. SSE covers settings/progress/log projections
where sufficient. Snapshots provide reconnection recovery.

**Acceptance:** malformed/version-mismatched payloads fail; errors have no success
data; event IDs/order and retention gaps are explicit; expired sessions and slow
consumers release resources. A reconnect never substitutes fixture success.
Use HTTP for commands and queries instead of generic RPC/reactive-stream replicas.

## H07 Jobs

**Build:** one coordinator with queued -> running -> succeeded/failed/cancelled
outcomes, explicit cancellation-request/interruption state, finite admission bounds,
attempts and progress. Trusted CPU operations use bounded worker processes; I/O
uses async tasks. Domain methods provide validated specifications and chunk/checkpoint
hooks. Persistent job history is added when the first durable workflow needs it.

**Acceptance:** queue overflow, cancellation, worker loss, shutdown and duplicate
submission have documented outcomes. Child jobs belong to their parent; counts
reconcile. A crashed job is interrupted until verified recovery, not silently
complete. Retry budgets and idempotency are operation-specific. Remote execution
uses this contract later; it does not add a second scheduler.

## H08 Resource services

**Build:** scoped file/artifact access, immutable publication, checksum/size/media
metadata, temporary staging/cleanup, bounded cache and safe archive handling.
Use Python filesystem/hash/archive primitives. Cache only measured repeated work,
with versioned keys and bounds; durable artifacts are authoritative.

**Acceptance:** traversal, absolute/escaped archive entries, junction escapes,
oversized expansion, corrupt checksums and missing files fail. No untrusted pickle
or Java object deserialization. Preserve resource revisions across producer removal.
Bounded network acquisition uses the same httpx lifecycle/policy; providers own
their authentication, symbol mapping, pagination and response semantics.

## H09 Persistence

**Build:** host-owned transactions, schema compatibility, leases, revision checks,
retention and recovery. Keep P01 atomic preferences; propose SQLite control records
plus immutable artifacts for later workflows, as described in [architecture](architecture.md).
Domain owners define their record schemas; receive narrow typed repositories.

**Acceptance:** test rollback, concurrent updates, restart and interrupted publication
in isolated stores. Validate orphan/missing-file recovery; removal preserves unrelated
records. No plugin SQL/raw handles. No automatic migration/adoption/reset of existing
stores. Approve the operational schema/root separately before activation.

## H10 Security and session authority

**Build:** use the approved loopback session/origin/token contract, with explicit
permission checks at domain/resource/tool boundaries. Keep secrets in operational
configuration or an approved secret capability. Scope external/destructive actions
to exact targets. Remote access requires a later authenticated/TLS deployment plan.

**Acceptance:** expired/foreign sessions, denied paths and forbidden commands fail
closed; credentials never appear in events/preferences/logs. Restart invalidates
sessions. Live trading, destructive tasks, external scripts, paid tools and mail
remain separately controlled. Trusted worker processes do not qualify as a sandbox
for user or AI-generated code.

## Java dependency dispositions

| Old dependency family | V2 destination and preserved obligation |
| --- | --- |
| Commons/Guava/Fastutil utility collections | H04/H08 and ordinary typed helpers; preserve consumed conversion/order/bound rules where externally meaningful |
| SLF4J, Logback, Commons/JBoss logging | H02; one event/redaction/sink contract |
| OpenTelemetry APIs/context/instrumentation | H02/H06 correlation and lifecycle; postpone exporter/agent machinery until needed |
| JNA, OSHI, WMI, jProcesses, PSUtils | H03 diagnostics; H07/H08 for actual process/file consumers |
| Animal Sniffer, JetBrains, Checker, Error Prone, J2ObjC, JSpecify, JSR305 annotations | JVM annotation mechanics omitted; explicit Python types, schema checks and actual runtime guards cover target invariants |
| jrt-fs and Kotlin runtime support | JVM-only machinery omitted; H01 qualifies CPython startup/packaging and actual resource availability |
| Jetty, Reactor, Reactive Streams | H06/H07 using FastAPI/asyncio/bounded queues |
| JSPF | H05 literal manifests, typed slots and explicit lifecycle |
| Jackson, JSON/Johnzon/Geronimo, schema validators/generators | H04/H06 schemas/JSON; format-specific adapters retain documented external representations |
| Objenesis/Classmate | Java object/reflection mechanics omitted; H04/H05 construct typed objects explicitly |
| JDOM/StAX/XStream/FST/XML/YAML | H08 boundary primitives and owning format consumers; native compatibility remains F03/F05 work |
| H2/SQLite JDBC | H09 target storage; any accepted donor import is a separate format adapter, not a database-engine replica |
| ZIP4J/Commons Compress/XZ | H08 bounded archives; supported compression/encryption variants need explicit coverage |
| OkHttp/Okio/Apache HTTP components | H08 bounded acquisition via httpx; provider-specific behavior remains F02/F12 |
| MCP/JSON wrappers | H06 transport helpers; F12 owns actual MCP protocol compatibility and tools |

JVM-only applies to runtime machinery, not automatically to all behavior in an
archive. The [task map](legacy-task-map.csv) records the primary destination and
consumers. Revisit actual consumed semantics at implementation time.

## Foundation delivery boundary

First connect bootstrap, logs, health, preferences, minimum attachment, transport
and sessions. Then add durable jobs/resources/persistence for the data/backtest
journey. Do not wait for every Java disposition to build a usable local loop.

The already approved P01 v2 plan specifies `/api/v1`, loopback session rules,
payload/deadline bounds, authenticated events, DebugConsole behavior and atomic
`preferences.json`. It remains authoritative for that work. V2 proposes grouping
and later breadth; changing those contracts requires an explicit plan iteration.
Full discovery, jobs and operational persistence are future capabilities, not
already implemented merely because the shell contains provisional clients.
