# HaruQuant Upgrade — Executive Requirements Map

_High-level, merged view of all thirteen implementation phases. Each **main requirement** is a module; each **sub-requirement** is a file-level requirement boundary. Full detail lives in `docs/upgrade-plan/`._

## Contents

- **Phase 1 — Utils Foundation**
- **Phase 2 — Data Service**
- **Phase 3 — Indicator Library**
- **Phase 4 — Strategy Service**
- **Phase 5 — Risk Governance**
- **Phase 6 — Analytics Service**
- **Phase 7 — Trading Service**
- **Phase 8 — Simulator Engine**
- **Phase 9 — Optimization Service**
- **Phase 10 — Live Runtime**
- **Phase 11 — UI & API Gateway**
- **Phase 12 — Research / Edge Lab**
- **Phase 13 — Conversation AI Layer**

---

## Phase 1 : Utils Foundation

_Project-wide utilities: logging, contracts, errors, identity, time, paths, dataframes, validation, security, settings, auth, events, notifications, observability._


**1. Utils** — The package-level public gate for the Utils Foundation
1.1 Init — Package scope, public-name classification, import safety, and shared utility foundation
1.2 Public Tools — Agent attachment restriction and standard official tool surface

**2. Logging** — Configure and emit redacted project-wide logs
2.1 Formatters — Project-wide structured and local-console diagnostics
2.2 Configuration — Explicit configuration, safe file logging, and thread-safe sink behavior
2.3 Lifecycle — Official-tool lifecycle events and cross-utility event logging
2.4 Retention — Safe rotation, bounded retention, and graceful sink degradation

**3. Contracts** — Own the stable cross-domain response/envelope, metadata, constants, canonical JSON, and official-tool boundary…
3.1 Constants — Scope protection and public-name classification
3.2 Tool Response — Standard HaruQuant response envelope and safe error translation
3.3 Canonical JSON — Canonical JSON, generic error compatibility, enum-safe public output
3.4 Tool Boundary — No silent failures, official-tool metadata, supported optional-dependency behavior, and engineering baseline
3.5 Public Tools — Approved tools and quality-envelope integration

**4. Errors** — Provide deterministic shared error types, code catalogs, sanitized error events, and pre-notification error routing
4.1 Exceptions — Shared typed exceptions and controlled unexpected-error mapping
4.2 Catalog — Error catalog and safe fallbacks
4.3 Models — Error event structure, severity classification, and safe context retention
4.4 Router — Deduplicated non-recursive error routing and observability

**5. Identity** — Generate and validate safe collision-resistant identifiers and stable versions
5.1 Generators — ID generation and safe propagation
5.2 Validators — Prefix, request/workflow ID, and version validation

**6. Time** — Own UTC-first parsing, formatting, sequence checks, freshness checks, and monotonic duration support
6.1 UTC — UTC normalisation and deterministic timestamp errors
6.2 Freshness — Freshness, event timing, and clock-drift visibility
6.3 Clock — Monotonic execution timing

**7. Paths** — Resolve and create only approved filesystem paths
7.1 Safe Paths — Safe path traversal and directory creation

**8. Dataframes** — Provide lazy-import, read-only dataframe utility transformations, alignment, serialization, chunking, comparison, and…
8.1 Alignment — Dataframe alignment and caller-owned input protection
8.2 Comparison — OHLC/OHLCV comparison and mismatch reporting
8.3 Serialization — Dataframe record serialization
8.4 Combinations — Chunking and parameter combinations

**9. Quality** — Inspect and report OHLCV/OHLCV-like data quality only
9.1 Models — Deterministic OHLCV quality result contract
9.2 OHLCV — OHLCV structural and integrity inspection
9.3 Scoring — Default penalty scoring and bounded diagnostics
9.4 Public Tool — Read-only quality tool envelope

**10. Validation** — Validate payloads, schemas, numeric ranges, domain handoffs, resource limits, freshness, and contract compatibility…
10.1 Models — Native validation result and bounded invalid-field contract
10.2 Primitives — Numeric and required-field validation
10.3 Schemas — Schema validation, exact paths, and semantic-version compatibility
10.4 Domain Validators — Evidence, approvals, registry, risk/environment, blocked-action, freshness, and artifact validation
10.5 Public Tool — Agent-facing bounded handoff validation

**11. Security** — Provide denylist-first redaction, password helper contracts, optional cryptographic operations, and deterministic…
11.1 Redaction — Denylist-first redaction and bounded nested payload protection
11.2 Passwords — Argon2id hashing and constant-time verification
11.3 Encryption — Lazy Fernet cryptography with secret-safe errors
11.4 Secrets — Active secret-version selection
11.5 Public Tool — Approved audit/log-redaction tool

**12. Settings** — Explicitly load, validate, resolve, and inject immutable runtime settings
12.1 Models — Typed RuntimeSettings and configuration sections
12.2 Loader — Explicit settings loading, precedence, safe defaults, and deterministic validation

**13. Auth** — Validate a supplied internal authentication context and decide whether a named utility/tool operation is authorized
13.1 Models — Actor model and authenticated context
13.2 Authorization — Explicit allowlist, roles/permissions/scopes, sensitive utility checks, audit-safe auth observability

**14. Events** — Define and implement a bounded thread-safe/async-safe in-process event distribution mechanism, event envelopes,…
14.1 Models — Standard event envelope, bounded queue diagnostics, and correlation/idempotency fields
14.2 Protocol — Pub/sub contract, subscriber isolation, external adapter boundary, and event version compatibility
14.3 Idempotency — Bounded event idempotency and deterministic eviction
14.4 In Process — Deterministic local Event Bus execution
14.5 External Adapters — Optional external adapter safety

**15. Notifications** — Decide how to route a sanitized alert under explicit environment/channel policy and optionally deliver it through lazy…
15.1 Models — Notification primitives and explicit environment/channel configuration
15.2 Templates — Safe template rendering and fallback behavior
15.3 Throttling — Alert-storm protection and concurrent routing safety
15.4 Routing — Severity/environment routing, outcome events, failure isolation, and deterministic errors
15.5 Adapters — Provider integration without import-time network/client work

**16. Observability** — Provide low-overhead operational telemetry primitives: metrics registration/recording, health snapshots,…
16.1 Metrics — Bounded metric name/label validation and best-effort local registry recording
16.2 Health — Deterministic component-state snapshots and aggregation
16.3 Circuit Breaker — Local thread/async-safe circuit state machine with open/half-open/closed transition behavior
16.4 Clock Drift — Injected-offset-source drift assessment and observability status only
16.5 Prometheus — Lazy optional exporter rendering and optional external Prometheus integration

**17. Utils (Examples)** — Executable documentation only
17.1 Usage — One runnable script that delegates to the public/support contracts with safe fake/local configuration

---

## Phase 2 : Data Service

_Market-data access, providers, validation, persistence, caching, realtime feeds, and scheduling._


**1. Documentation** — Data domain source-of-truth documentation, tool catalog, operational runbooks, manifests, policy references, and…
1.1 DOMAIN — Data domain source-of-truth documentation, tool catalog, operational runbooks, manifests, policy references, and production sign-off…

**2. Data** — Package gatekeeper
2.1 Init

**3. Gateway** — Shared tool wrapper that keeps standard envelopes, redaction, deterministic exception mapping, request propagation,…
3.1 Tool Boundary — Shared tool wrapper that keeps standard envelopes, redaction, deterministic exception mapping, request propagation, logging, timing, and…
3.2 Payload Boundary — JSON serialization and bounded public-payload construction
3.3 Data Gateway — Single orchestration capability for validated canonical data access
3.4 Public Tools — Thin official callable façade

**4. Validation** — Filesystem-input validation and approved-root enforcement for all local data and artifact paths
4.1 Paths
4.2 Records — Canonical record, asset-specific metadata, tick, OHLCV, sequence, gap, overlap, stale, partial, and quality-report validation
4.3 Timezone Precision — UTC normalization, source-timezone/DST handling, workflow-specific decimal policy, and precision quantization

**5. Errors** — Data-domain deterministic error mapping that reuses `archive.utils.errors` rather than redeclaring shared exceptions
5.1 Mapping

**6. Contracts** — Typed inbound request contracts for retrieval, storage, cache, scheduler, feed, and synthetic workflows
6.1 Requests
6.2 Metadata — Canonical metadata, provenance, manifest, readiness, licensing, quality, and side-effect declarations for public responses and persisted…

**7. Persistence** — Auditable stale-lock, checkpoint, crash-recovery, and durable state transition handling
7.1 Recovery
7.2 Ports — Append-oriented persistence contracts, keeping SQLite default deployment replaceable by a future TSDB without routing rewrite
7.3 Idempotency — Deterministic ingestion/backfill idempotency-key derivation and conflict/no-op classification
7.4 SQLite Store — SQLite single-node ACID implementation, transaction control, bounded connection management, and leak detection
7.5 Migrations — Versioned migration planning, auditability, compatibility decision, rollback expectation, and read-time schema handling
7.6 Manifests — Data, source-revision, license, lineage, quality, retention, and artifact manifests for durable reproducibility

**8. Providers** — Internal-only secure credential reference resolution
8.1 Credentials
8.2 Normalization — Source-to-canonical field normalization and source provenance capture for bars, ticks, spreads, volumes, and symbols
8.3 Readiness — Source readiness and promotion evidence
8.4 Registry — Internal provider registration, lookup, capability filtering, and readiness enforcement
8.5 Protocol — Common internal source-adapter contract
8.6 Adapter — Read-only MT5 data adapter
8.7 Adapter — Read-only cTrader data adapter behind the approved client/MCP boundary
8.8 Adapter — Dukascopy data adapter, decomposed into client, instruments, normalization, historical, and live-capability internals as needed
8.9 Adapter — Binance symbol-discovery-only adapter
8.10 Fallback — Explicit opt-in fallback planning and provenance recording
8.11 Resilience — Provider-call fault-tolerance wrapper: timeouts, bounded retry, rate limiting, circuit breaker policy, and deterministic outcome…
8.12 Csv Adapter — CSV source adapter for safe local loading and normalization
8.13 Parquet Adapter — Parquet source adapter for large local data, schema metadata preservation, and safe local loading

**9. Transforms** — Deterministic OHLCV resampling with explicit source/target timeframe and spread policy
9.1 Resample
9.2 Ticks — Validated, deterministic tick-to-bar aggregation
9.3 Labels — Deterministic historical label construction with bounded declared horizon and explicit non-predictive metadata

**10. Verification** — Unit, contract, property, regression, import-safety, performance, no-silent-fallback, and boundary tests for the Data…
10.1 Data — Unit, contract, property, regression, import-safety, performance, no-silent-fallback, and boundary tests for the Data Foundation
10.2 tests/services/data/ — DATA-TEST-001

**11. Realtime Feeds** — Internal live-capable data ingestion coordination
11.1 Gateway
11.2 Status Tools — Low-risk read-only feed-status public tool boundary
11.3 Buffer — Bounded feed-buffer and overflow-policy implementation
11.4 Reconnect — Reconnect/backoff policy for feed sessions

**12. Scheduler** — Authoritative scheduler lifecycle/status tool façade
12.1 Tools
12.2 Contracts — Typed scheduler job, status, schedule, checkpoint, lease, and recovery contracts
12.3 Lifecycle — Idempotent job transitions, lease ownership, duplicate start protection, state persistence, and safe terminal-state rules
12.4 Backfill — Chunked, resumable, idempotent historical backfill that commits data and checkpoint evidence together
12.5 Recovery — Job/checkpoint recovery from last committed state and explicit corruption/failure outcomes
12.6 Gap Reconciliation — Feed-gap-to-backfill orchestration for the approved `drop_and_reconcile` policy

**13. Local Storage** — Official local file storage façade for validated normalized CSV/Parquet records
13.1 Tools
13.2 Atomic Writer — Temporary-write, atomic-commit, collision, overwrite, and failed-artifact quarantine behavior
13.3 Manifests — Local storage metadata manifests, immutable-file freshness checks, and redistribution constraints

**14. Cache** — Cache limits, TTLs, workflow-specific stale behavior, and cacheability policy
14.1 Policy
14.2 Service — Cache key construction, reads, writes, stale detection, and source-fetch-safe failure behavior
14.3 Invalidation — Automatic invalidation when data, normalization, schema, or source revision provenance changes
14.4 Tools — Destructive cache-clear public façade, dry-run-first and approved-root constrained

**15. Calendar** — Internal future `MarketCalendarProvider` extension point
15.1 Provider
15.2 Tools — Current configured market-hours and normalized trading-session façade

**16. Synthetic** — Official deterministic synthetic data generation façade with bounded direct payloads
16.1 Tools
16.2 Generators — Seeded GBM Phase 1 synthetic-series generation, independent from external data sources

**17. Examples** — Runnable examples demonstrate safe usage and standard envelopes without changing production state beyond explicit…
17.1 Data Examples — DATA-EX-001

**18. Documentation And Quality** — Architecture, operational documentation, source catalog, test commands, lint/typecheck configuration, and release…
18.1 Implementation Handoff Record — DATA-EX-012

---

## Phase 3 : Indicator Library

_Deterministic indicator contracts, registry, formulas, builtins, runtime, incremental state, cache, and audit._


**1. Documentation** — Documentation and governance evidence only
1.1 Design Standards — Governance documentation for scope tiers, no-lookahead, naming, fixtures, validation, and custom-indicator promotion
1.2 Usage And Configuration — Executable-facing API and configuration documentation
1.3 Acceptance Checklist — Acceptance evidence for the typed contract slice
1.4 Package And Scope — Ownership, dependency, typing, and package-distribution documentation
1.5 Requirement Traceability — Identifier registry for functional and non-functional traceability
1.6 Scope Tiers — Core/optional/future decision record
1.7 Trend Indicator Guide — Formula, API, session, data-integrity, and MTF usage examples
1.8 Incremental State Guide — State, idempotency, ordering, and operating policy documentation
1.9 Cache And Slo Guide — Stable cache/API/operating-policy documentation
1.10 Audit Mode — Audit entry, tamper evidence, and metadata guide

**2. CI** — Build and release-engineering boundary for package metadata, dependency locking, supply-chain evidence, SBOM, signing,…
2.1 Release Policy — Build/release engineering policy outside runtime calculations
2.2 Pyproject — Packaging and repeatable benchmark environment declaration

**3. Indicators** — Public Indicator Library boundary
3.1 Init — Public gate with no additional file-specific behavior
3.2 API — Public import surface and API contract composition

**4. Contracts** — Canonical type and serialization boundary for indicator requests, results, manifests, states, ports, policies, and…
4.1 Protocol — Structural protocol and batch input/output contract
4.2 Numeric Policy — Formula-neutral numeric semantics and test tolerance contract
4.3 Result — Non-mutating result joining and deterministic collision behavior
4.4 Models — Configuration model for data, precision, modes, limits, and optional extension controls
4.5 Manifest — Canonical calculation identity and reproducibility manifest
4.6 Errors — Typed deterministic indicator error catalog
4.7 State — Typed state, update, and serialization protocol contract

**5. Registry** — Approved-indicator catalog and lifecycle-governance boundary
5.1 Registry — Approved indicator catalog and conformance admission
5.2 Capability Matrix — Registry-derived mode and eligibility reporting
5.3 Deprecation — Versioned lifecycle decision and enforcement
5.4 Conformance — Custom indicator admission, prohibited-operation checks, and promotion evidence

**6. Validation** — Fail-fast validation boundary for input shape, parameters, provenance, microstructure, naming, mutation, and…
6.1 Provenance — Provenance, corporate-action, and source-policy validation
6.2 Composition — Acyclic composition plus quality/provenance propagation
6.3 Pipeline — Validation gate that completes before output or state replacement
6.4 Mutation Guard — Input identity snapshots and official mutation detection
6.5 Parameters — Formula-independent parameter/naming validation
6.6 Microstructure — Quote and spread integrity gate

**7. Timing** — No-lookahead, UTC, calendar, warmup, symbol-alignment, and availability-time boundary
7.1 Availability — Availability metadata and strategy-facing gating
7.2 Warmup — Data-port request contract plus alignment preconditions
7.3 Calendar — Session-aware temporal normalization and gap semantics
7.4 Alignment — Validated external data-port consumption and multi-source timing alignment

**8. Formulas** — Pure formula specifications and reusable numerical kernels
8.1 Specifications — Versioned formula tables and golden-fixture change policy

**9. Builtins** — Official built-in batch indicator implementations and their thin, deterministic adapters to formula kernels
9.1 Init — Registry-backed built-in implementation registration and public mapping
9.2 Trend — Official pure trend calculations
9.3 Volatility — Official pure volatility calculations and facade wrappers
9.4 Momentum — Official pure momentum calculations

**10. Runtime** — Calculation orchestration boundary
10.1 Settings — Validated runtime policy configuration
10.2 Backends — Backend-neutral parity and fallback orchestration
10.3 Executor — Controls result-or-error behavior around validated computation
10.4 Out Of Core — Bounded-memory, warmup-continuous computation path
10.5 Observability — Decorator/adapter boundary for metrics, spans, feature selection, and comparisons
10.6 Resource Guard — Monotonic deadline and quota guard
10.7 Access Control — Access decision gate before privileged calculation
10.8 Benchmarks — Benchmark definitions and evaluation without calculation changes

**11. Incremental** — Incremental and streaming state transition boundary
11.1 Init — No new behavior
11.2 Symbol Mapping — Mapping-aware continuity/reset decision
11.3 State Codec — Resumable state codec and bounded accumulator contract
11.4 Updater — Warmup state consumption and output visibility policy
11.5 Concurrency — Single-owner mutation and immutable read snapshots
11.6 Accumulator — No additional file-specific functional behavior

**12. Cache** — Optional cache-port and cache-key boundary
12.1 Init — No additional file-specific functional behavior
12.2 Service — Strict/best-effort cache wrapper around pure calculations
12.3 Keys — Canonical keys and dependency invalidation derivation
12.4 Adapter — Physical cache adapter coordination and safe degradation

**13. Audit** — Optional audit-emission boundary
13.1 Service — Manifest-based audit entry creation and sink delegation
13.2 Policy — Fail-closed policy gate before production audit mode

**14. Indicators (Tests)** — Verification boundary
14.1 Test Import Safety — Test location for package import and foundation behavior
14.2 Test Registry Contracts — Verification of registry operations, lifecycle, capability claims, and public convenience wrappers
14.3 Test Contracts — Cross-cutting contract, parity, mutation, provenance, and property verification
14.4 Test Error Contracts — Error-mode, numeric, collision, composition, and integration validation
14.5 Test Base Math — Formula, availability, MTF, quality, and integration tests
14.6 Test Builtins Imports — Import and foundation behavior verification
14.7 Test Trend Indicators — Golden, cross-library, naming, and property tests
14.8 Test Volatility Indicators — Golden, pathological-data, and non-negativity verification
14.9 Test Reference Outputs — Fixture pinning and cross-validation deviation control
14.10 Test Incremental Imports — Import and package foundation verification
14.11 Test Incremental State — Strict typing, compatibility, and corruption test coverage
14.12 Test Accumulators — Foundation test location
14.13 Test Cache Imports — Foundation test location
14.14 Test Dependency Regressions — Full correctness/determinism/no-lookahead/cache/benchmark gate
14.15 Test Cache Adapter — Cache key, atomicity, degrade, performance, corporate-action, SLO, and access checks
14.16 Test Audit Trail — Audit completeness, integrity, append-only, and calculation-parity tests

---

## Phase 4 : Strategy Service

_Signal-only strategy contracts, registry, runtime, execution handoff, sandbox, and governance._


**1. Documentation** — Own strategy-domain operating knowledge, mandatory documentation status, and document references
1.1 OPERATING MANUAL — Human-readable operating manual and formal documentation checklist

**2. Package Gateway** — Expose only approved Strategy Service entry points and types
2.1 Init — Explicit import and `__all__` gatekeeper only
2.2 Public API — Thin, typed public wrappers

**3. Contracts** — Define immutable, versioned domain contracts and declarations exchanged between Strategy and its approved consumers
3.1 Enums — Stable string enums for lifecycle, environment, timing, concurrency, data policy, microstructure state, and deterministic Strategy-domain…
3.2 Models — Typed request, signal, intent, state, diagnostics, and manifest dataclasses/models
3.3 Declarations — Strategy-declared assumptions and metadata for liquidity, risk, execution, portfolio interaction, health, regulatory posture, data policy,…

**4. Registry** — Manage approved immutable strategy metadata, version identity, capability declarations, registration validation,…
4.1 Models — Registry entry, version constraint, immutable artifact, capability, approval evidence, and strategy-manifest models
4.2 Catalog — Validated immutable registry catalog
4.3 Resolver — Deterministic strategy reference, version-constraint, approved-module, and allowlisted-artifact resolution before any implementation…
4.4 Lifecycle — Lifecycle status and promotion-evidence eligibility checks
4.5 Provenance — Build, artifact, dependency, configuration, model, and source-provenance hash verification for replayability and invalidation

**5. Validation** — Fail closed before strategy evaluation by validating configurations, request data, readiness, security properties,…
5.1 Config — Schema validation, defaulting, migration compatibility, payload bounds, and configuration-injection rejection
5.2 Readiness — Strategy input, indicator warmup/readiness, declared data requirement, and lifecycle readiness validation before strategy hooks run
5.3 Market Data — Market-data schema, freshness, point-in-time, timezone, sequencing, duplication, revision, clock-drift, and declared missing-data policy…

**6. Timing** — Enforce no-lookahead, bar-availability, signal-timing, and point-in-time decision constraints before a signal becomes a…
6.1 Availability — Closed-bar timing policy, availability filtering, higher-timeframe closure, and deterministic signal alignment
6.2 Point In Time — Point-in-time snapshots, data-latency tolerance, revision exclusion, stable decision clocks, and atomic lookahead rejection

**7. Runtime** — Coordinate bounded strategy-local state, intent lineage, read-only dependency interaction, failure policy,…
7.1 Resource Policy — Validated strategy profile limits and declarations for latency, CPU, memory, queues, checkpoint size, diagnostics, dependency calls, and…
7.2 State — Strategy-local decision-state model, serialization, isolation, and checkpoint-safe state transitions
7.3 State Transaction — Atomic per-event strategy-local state transition and deterministic rollback coordination
7.4 Lineage — Deterministic decision IDs, intent IDs, idempotency keys, monotonic sequence allocation, parent-child lineage, and immutable provenance…
7.5 Dependency Boundary — Coordination wrapper for injected read-only data, indicator, simulation, and state ports
7.6 Failure Policy — Deterministic escalation, disablement, retry/no-retry, timeout, quarantine, skip-decision, and fail-run classification
7.7 Checkpoints — Strategy-local checkpoint creation and compatibility validation
7.8 Cancellation — External hard-kill acceptance, isolated strategy-session stop request, local pending-intent cancellation, and final safe diagnostic…

**8. Execution** — Execute registered strategy decision logic in vectorized or event-driven modes, emitting only canonical signals, local…
8.1 Output Boundary — The final Strategy Service output guard
8.2 Vectorized — Batch-only vectorized indicator and signal generation with closed-bar shifting, fixed decision clock, atomic lookahead rejection, and no…
8.3 Worker Boundary — Typed boundary for orchestration-provided isolated worker execution
8.4 Hooks — Typed hook dispatch table and deterministic hook ordering for initialization, event processing, checkpoint/restore, errors, and shutdown
8.5 Event Runtime — Stateful event-strategy session that accepts only approved event inputs and immutable/read-only external snapshots
8.6 Event Dispatch — Bounded event queue, deterministic sequence ordering, explicit reentrancy/single-thread declarations, asynchronous compatibility checks,…

**9. Errors** — Translate Strategy-domain validation, dependency, timing, lifecycle, resource, sandbox, and internal failures into…
9.1 Codes — Strategy error-code catalog references and validation only
9.2 Mapping — Boundary-level mapping from lower-level Data, Indicator, Simulator, and sandbox failures to safe, deterministic Strategy-domain diagnostics

**10. Sandbox** — Fail closed on arbitrary code and unsafe runtime capabilities, while defining the future contract for explicitly…
10.1 Entry Gate — Early strategy input gate that rejects raw Python/source-code payloads and accepts only registry references, validated configurations, or…
10.2 Policy — Future-enabled sandbox metadata validation: approvals, expiry, allowed capabilities/imports, denied capabilities, resource limits, and…
10.3 Security — Secret prohibition, rationale/checkpoint/diagnostic redaction validation, debug payload bounds, and safe security-rejection journal event…

**11. Observability** — Attach redacted, structured evidence, tracing, metrics, and performance data at boundaries without contaminating…
11.1 Diagnostics — Structured diagnostic schemas and builders with request/correlation/run/strategy identifiers, safe payload bounds, and governed/fail-closed…
11.2 Metrics — Metric definition and emission adapters for decision counts, intent outcomes, data quality, lookahead, validation, checkpoint size, and…

**12. Governance** — Represent strategy governance evidence and declarations for consumption by approved Risk, Simulation, Analytics, Live,…
12.1 Validation Artifacts — Immutable validation/optimization evidence package model and reproducibility validation
12.2 Build Artifacts — Build pipeline evidence, typed quality-gate outcome, dependency/SBOM metadata, and immutable artifact verification contracts
12.3 Policies — Declarative calibration, performance review, shadow/A-B/canary, kill, recovery, regulatory, data failover, documentation retention, and…

**13. Verification** — Prove every Strategy requirement, public contract, boundary, deterministic error, lifecycle, no-lookahead, performance,…
13.1 tests/services/strategies/ — Requirement-mapped unit, contract, property, fuzz, replay, snapshot, mutation, performance, stress, chaos, memory, concurrency, and…
13.2 TRACEABILITY MATRIX — Builder-handoff coverage ledger mapping requirements to modules, tests, examples, ADRs, applicability, acceptance criteria, and approved…

---

## Phase 5 : Risk Governance

_Fail-closed risk policy, sizing, exposure, correlation, tail-risk, stress, feasibility, governance, and audit._


**1. Readiness** — Proves that Phase 5 starts only with canonical dependencies, explicit scope boundaries, safe fixtures, documented mode…
1.1 Phase Readiness — Institutional foundation, dependencies, and pre-implementation readiness

**2. Models** — Defines the canonical, serializable contracts that cross the Risk boundary
2.1 Contracts — Canonical risk contracts and public decision package
2.2 Serialization — Risk model serialization and contract verification

**3. Config** — Owns validated policy-profile configuration and stable configuration identity
3.1 Schema — Risk configuration profiles and strict schemas
3.2 Loader — Configuration loading and reproducibility identity

**4. Policy** — Resolves policy-as-code deterministically across approved scopes and validates governed override requests
4.1 Resolver — Policy-as-code resolution
4.2 Overrides — Governed policy overrides

**5. Regime** — Assesses current market operating conditions using supplied, freshness-qualified evidence
5.1 Assessor — Market regime gate
5.2 Validation — Regime failure semantics and verification

**6. Limits** — Runs deterministic, ordered, fail-closed limit checks and returns a traceable aggregate
6.1 Contracts — Deterministic limit contracts
6.2 Checks — Deterministic individual limit checks
6.3 Engine — Limit aggregation and stable decision input

**7. Sizing** — Calculates policy-bounded trade size from risk evidence
7.1 Contracts — Position sizing contracts
7.2 Calculators — Volatility-based and policy-bounded sizing

**8. Exposure** — Decomposes FX proposals and portfolio positions into currency legs and concentration measures
8.1 FX Legs — FX currency-leg decomposition
8.2 Aggregation — Currency exposure aggregation and limits input

**9. Correlation** — Produces reproducible closed-bar correlation and cluster-risk evidence from injected time series
9.1 Returns — Return construction and alignment
9.2 Engine — Correlation and clustered portfolio risk

**10. Tail Risk** — Calculates portfolio VaR and Expected Shortfall/CVaR from canonical positions, returns, covariance, and policy inputs
10.1 Contracts — Tail-risk contracts
10.2 VaR — Portfolio Value at Risk
10.3 Expected Shortfall — Expected Shortfall / CVaR as stronger tail-risk control

**11. Stress** — Evaluates registered deterministic stress scenarios against supplied portfolio evidence
11.1 Contracts — Stress-test contracts and scenario registry
11.2 Engine — Stress scenario evaluation

**12. Feasibility** — Evaluates available margin, drawdown controls, liquidity, and order feasibility after portfolio risk and before final…
12.1 Margin — Margin and leverage risk
12.2 Drawdown — Drawdown Governor
12.3 Execution Gate — Execution risk gate

**13. Governance** — Reviews risk-budget allocation proposals across strategy, symbol, currency, and portfolio scopes
13.1 Allocation — Allocation governance
13.2 Lifecycle — Strategy and live lifecycle governance
13.3 Kill Switch — Risk kill switches

**14. Governor** — Coordinates all required Risk engines in a fixed order, synthesizes a single deterministic decision, and requests…
14.1 Governor — RiskGovernor orchestration and decision synthesis

**15. Audit** — Creates tamper-evident, redacted audit records and bounded approval tokens
15.1 Events — Tamper-evident risk audit trail
15.2 Tokens — Risk decision approval tokens

**16. Storage** — Defines repository ports and controlled persistence adapters for risk state, decisions, audits, policies, kill…
16.1 Ports — Risk persistence ports
16.2 In Memory — In-memory storage implementation and persistence verification

**17. Reports** — Builds redacted, evidence-only risk reports and emits observability data without recalculating risk or opening broker…
17.1 Builder — Evidence-only reports and observability

**18. Risk** — Acts as the import and export gate for the domain
18.1 Init — Risk package initialization and public registry containment

**19. Tools** — Exposes only approved, JSON-safe Risk tool contracts
19.1 Official — Official risk tools

---

## Phase 6 : Analytics Service

_Read-only performance analytics: metrics, statistics, benchmarks, scorecards, reports, and dashboards._


**1. Analytics** — Official Analytics Service public boundary: exposes only approved high-level, read-only analytics capabilities
1.1 Init — Public import gate
1.2 Tool API — Official high-level tool wrappers: validate envelopes, invoke read-only services, and return standard envelopes

**2. Contracts** — Typed contract capability: owns versioned analytics models, catalogs, warnings, schemas, and JSON-safe contracts
2.1 Models — Versioned canonical analytics dataclasses/models: inputs, reports, metric results, warnings, quality flags, lineage, and metadata
2.2 Metric Catalog — Metric Definition Catalog, formula metadata, units, defaults, samples, tolerances, and schema compatibility declarations
2.3 Warnings — Warning and quality-flag models, ordered severities, catalog entries, and non-binding decision labels
2.4 Serialization — Canonical JSON safety, Decimal normalization, schema-version handling, and deterministic hashing inputs

**3. Registry** — Public capability governance: owns export classification, tool catalog synchronization, and decorator attachment
3.1 Analytics Registry — Registry of official tools, metric kernel visibility, stability, agent/API eligibility, aliases, and deprecation status

**4. Adapters** — Canonical input capability: converts approved upstream result/journal contracts into validated Analytics inputs
4.1 Protocols — Typed upstream result contracts and deterministic source-to-canonical adapter protocol
4.2 Canonicalize — Conversion of backtest, paper, live, portfolio, optimization, and normalized results into canonical TradingResult
4.3 Journal Adapters — Canonical simulation-journal and live-journal translation through one event/result model

**5. Metrics** — Deterministic metric calculation capability: derives trade, equity, drawdown, risk, ratio, and efficiency facts
5.1 Exports — Explicitly named compatibility aliases that avoid collisions between common, metrics, distributions, benchmark, and ratios namespaces
5.2 Position Exposure — Read-only position-size, gross/net exposure, open-PnL, exposure-duration, and margin-utilization calculations
5.3 Trade Outcomes — Closed-trade filtering, outcomes, streaks, win/loss rates, PnL summaries, and outcome entropy
5.4 R Multiples — R-multiple derivation, declared-risk preference, proxy warning behavior, and R-space metrics
5.5 Costs — Spread, slippage, commission, swap, and transaction-cost impact calculations
5.6 Efficiency — MAE/MFE, exposure, capital, exit, position-size, and return-efficiency metrics
5.7 Time Analysis — Trade duration, market-presence, calendar/session bucketing, and time-in-market calculations
5.8 PnL — Profit/loss, adjusted/select PnL, CAGR/CMGR, run-up, and return-over-drawdown calculations
5.9 Curves — Closed-trade balance/equity curve construction and normalized curve utilities
5.10 Equity Returns — Equity-return transformations, resampling, annualization, period returns, and equity summary metrics
5.11 Drawdown — Underwater series, drawdown episodes, recovery, duration, and drawdown-based ratio calculations
5.12 Risk — Volatility, downside risk, VaR/CVaR/expected shortfall, exposure, and risk-of-ruin metrics
5.13 Ratios — Sharpe, Sortino, Omega, profit factor, payoff, tracking, and other performance ratios
5.14 Aggregate — Pure aggregators that compose metric groups from canonical data without persistence or network calls

**6. Statistics** — Statistical evidence capability: derives distributions, resampling uncertainty, multiple-testing, and overfit evidence
6.1 Multiple Testing — White’s Reality Check, PBO, walk-forward degradation, and multiple-comparison corrections
6.2 Distributions — Distribution summaries, moments, tail diagnostics, outliers, histogram, Q-Q, and model-fit data
6.3 Resampling — Seeded permutation, bootstrap, confidence intervals, and uncertainty/probability calculations

**7. Benchmarks** — Benchmark comparison capability: aligns comparable return streams and derives benchmark-relative facts
7.1 Alignment — UTC normalization and deterministic alignment of strategy, benchmark, and FX conversion series
7.2 Metrics — Beta, alpha, R-squared, tracking error, information ratio, batting average, and benchmark metrics

**8. Scorecards** — Non-binding interpretation capability: organizes report evidence into quality context without governance authority
8.1 Quality — Non-binding strategy-quality score and assessment computed only from validated AnalyticsReport evidence
8.2 Labels — Separation and labeling of facts, warnings, caveats, non-binding recommendations, governance exclusions, and promotion blockers

**9. Reports** — Report composition capability: assembles complete, reproducible, in-memory AnalyticsReport artifacts
9.1 Sections — Metric-section orchestration, section criticality, skipped/failed/degraded metadata, and partial-report behavior
9.2 Hashes — Canonical, deterministic report/input/config/ledger/curve/benchmark hash creation and reproducibility lineage
9.3 Formatters — In-memory report rows, human-readable summaries, Markdown/JSON text payloads

**10. Dashboards** — Presentation-payload capability: projects validated report sections into bounded chart/table DTOs
10.1 Overview — Build versioned UI/API overview payloads from validated report sections only
10.2 Truncation — Deterministic chart downsampling/truncation with preserved semantic points and metadata

**11. Boundaries** — Cross-cutting safety boundary: applies validation, envelopes, observability, limits, caching, and redaction outside…
11.1 Request Validation — Public request IDs, input size, timestamp, numeric, schema, and tool-contract validation before metric work begins
11.2 Envelopes — Standard success/error envelopes, safe structured errors, no non-finite values, and metadata assembly
11.3 Limits — Configuration-backed limits for data, memory, runtime, statistics, dashboard points, and response size
11.4 Redaction — Central sensitive-key/value redaction for all public inputs, logs, warnings, errors, and output metadata

**12. Documentation** — Documentation artifacts: rendered catalogs, contracts, examples, ownership rules, and compatibility policy
12.1 Catalogs — Rendered Metric Definition Catalog, Official Analytics Tool Catalog, warning/quality-flag catalog, compatibility policy, and examples

**13. Analytics (Services)** — Verification capability: requirement-to-test traceability and public-boundary contract verification
13.1 Test Requirement Traceability — Machine-readable requirement-to-test coverage and public-registry/catalog synchronization tests

---

## Phase 7 : Trading Service

_Broker execution boundary and order lifecycle._


**1. Live Order Executor & Broker Integration** — Core broker order-lifecycle boundary
1.1 Order Lifecycle — Submit market/pending orders, modify and cancel pending orders, close positions fully or partially
1.2 Kill-Switch & Shutdown — Halt new trades, cancel active orders, optional flatten, and graceful shutdown order-stop
1.3 MQL5 Alignment — Align order types, request fields, and fill policies (FOK/IOC/Return) with MQL5 trade contracts
1.4 Trace Propagation — Propagate correlation, trace, and request IDs across all requests, responses, and events

**2. Input Parameter Validation & Readiness** — Fail-closed pre-trade validation boundary
2.1 Request Validation — Validate symbols, volumes, prices, SL/TP geometry, margin, expiration, broker constraints, and malicious payloads
2.2 Precision Normalization — Normalize prices, volumes, and SL/TP to broker decimal precision and volume-step rules before routing
2.3 Dealing Mode & Session — Cache account dealing mode and validate market-session eligibility for the requested action
2.4 Execution Readiness — Aggregate connectivity, market, permission, margin, and rate-limit readiness checks before execution
2.5 Idempotency & Serialization — Compute idempotency keys and serialize requests within each (account, symbol) scope
2.6 Fail-Closed — Fail closed on invalid readiness, active kill-switch, or blocked startup reconciliation gate

**3. Trade Reporting & Journal Sinks** — Reporting and telemetry boundary
3.1 Partial Fills — Return partial-fill details to the Strategy/Risk caller rather than auto-chasing
3.2 Reports & Alerts — Generate trading reports with validation warnings and alerting rules
3.3 Telemetry & Redaction — Propagate trace context through broker calls; redact secrets, credentials, and tokens from all output

**4. Position & Order Reconciliation Engine** — Broker/internal state reconciliation boundary
4.1 State Retrieval — Retrieve account, position, pending-order, historical-order/deal, and terminal information
4.2 Drift Detection — Detect missing/mismatched records and produce reconciliation summaries
4.3 Reconciliation Gate — Run on startup, unknown-outcome errors, and schedule; block trading until initial pass succeeds
4.4 Unknown-Outcome Safety — Prevent unsafe retries, enforce broker-call timeouts, and P1-alert on drift beyond thresholds
4.5 Resilience Tests — Chaos tests for broker disconnections and delayed adapter responses

**5. Rate Throttling & Pre-Check Gates** — Outbound-call protection boundary
5.1 Rate Limiting — Per-provider token-bucket rate limiting on all outbound broker calls with utilization warnings
5.2 Graceful Shutdown — Allow in-flight requests to resolve within a configurable timeout window

**6. Persistent Trade Journal & Order Store** — Durable trade-state and idempotency boundary
6.1 Idempotency Store — Key generation, duplicate detection/rejection, TTL/lifecycle, and collision protection
6.2 State Compare & Metrics — Compare TradeStore against broker state; track latency, failure, drift, and idempotency metrics
6.3 Shutdown Flush & Recovery — Flush reconciliation/idempotency state on shutdown; E2E recovery tests for network drops

**7. Domain Exception Handling & Error Routing** — Broker-error normalization boundary
7.1 Error Classification — Map broker errors to standard internal/MQL5-retcode-compatible transient vs permanent codes
7.2 Retry & Circuit Breaker — Retry-with-backoff for idempotent operations and circuit breakers around broker adapters

**8. Operations & Compliance** — Operational assurance boundary
8.1 Simulator Integration — High-fidelity integration tests using the local simulator adapter for deterministic regression

**9. Broker Routing & Provider Boundary (Hardening)** — Execution-provider abstraction boundary
9.1 Routing Ownership — Move broker routing out of routes into a service/integration boundary; routes call governed services only
9.2 Provider Contracts — Adopt Phase 1.5 broker/execution/account/order provider and TradeStore contracts across MT5, cTrader, Binance, simulator, paper, shadow
9.3 Deterministic Mapping — Map broker errors to deterministic internal codes; keep canonical IDs with raw broker IDs as metadata only
9.4 Config-Only Switching — Prove the same caller can route simulated, paper, or live requests by provider configuration only

---

## Phase 8 : Simulator Engine

_Deterministic backtest engine: market, execution, broker profiles, portfolio, costs, controls, journal, reporting._


**1. Documentation** — Documentation-only capability that explains simulator behaviour, validity limits, operational procedures, traceability,…
1.1 Design Manual — Simulator design manual and operating procedures
1.2 Config Reference — Versioned reference for configuration classes, enums, defaults, bounds, and behavior
1.3 Reproducibility — Reproducibility and point-in-time guide
1.4 Ownership And Scope — Ownership, non-goals, and deferred scope
1.5 Error Taxonomy — Human-readable catalogue of deterministic SIM_* codes and diagnostic interpretation
1.6 Traceability — Traceability and required non-implementation declarations
1.7 Vendor Governance — Third-party data, broker profile, plugin, license, revision, retention, and supplier governance procedures

**2. Simulator** — Public package gatekeeper
2.1 Init — Public import gate

**3. API** — Official callable-tool boundary
3.1 Tools — Tool-wrapper input normalisation, authorization boundary, arbitrary-code rejection, standard envelope production, and delegation to…

**4. Contracts** — Stable typed contracts, enums, error catalogues, ports, and serialization rules shared by simulator capabilities
4.1 Models — Simulator models and immutable configuration
4.2 Enums — Canonical enums and lifecycle values
4.3 Errors — SIM_* error taxonomy
4.4 Extensions — Extension-point contracts for deferred enterprise capabilities without making them mandatory Phase 1 dependencies

**5. Validation** — Fail-closed pre-execution validation of requests, configuration, strategy references, data authority, data quality, and…
5.1 Config Validator — Simulator, resume, and realism configuration validation
5.2 Strategy Validator — Strategy reference and sandbox eligibility validation
5.3 Data Quality — Dataset quality and data-authority validation
5.4 Schema Validator — Input schema and payload safety validation
5.5 Parameters — Simulator parameter validation

**6. Orchestration** — Coordinates bounded run lifecycle, scheduling, worker recovery, cancellation, checkpoint/resume, and cross-capability…
6.1 Backtest Orchestrator — Coordinates deterministic run stages: validation, data preparation, indicator/signal readiness, tick construction, engine execution,…
6.2 Scheduler — Bounded scheduling and worker lifecycle
6.3 Checkpoints — Checkpoint and resume safety
6.4 Worker Recovery — Worker failure recovery and poison-pill quarantine

**7. Engine** — Deterministic canonical event processing and authoritative in-memory simulation state transitions
7.1 Event Driven Execution — Canonical event-driven execution
7.2 State — Authoritative engine state and read-only snapshots
7.3 Tick Batching — Tick-batching boundary proof

**8. Integration** — Adapts approved strategy and indicator outputs into a no-lookahead executable signal timeline
8.1 Strategy Adapter — Approved strategy and signal integration

**9. Market** — Constructs canonical tick, order-book, calendar, data-manifest, gap, and market-data views from injected Data-domain…
9.1 Tick Factory — Canonical tick stream construction
9.2 Synthetic Ticks — Deterministic synthetic tick generation
9.3 Order Book — Read-only order-book snapshots, depth validity, crossing/locking diagnostics, and book-derived executable price inputs
9.4 Calendar — Market calendar, gaps, halts, and session state
9.5 FX Conversion — FX rate resolution and cross-rate safety

**10. Execution** — Applies broker-profile-compatible order lifecycle, matching, fill, advanced-order, and order-lineage semantics in…
10.1 Orders — Order contracts and lifecycle transitions
10.2 Matching — Matching, fill policies, and IOC remainder handling
10.3 Advanced Orders — Advanced order types and repricing
10.4 Lifecycle — Pending and protective order lifecycle

**11. Broker Profiles** — Defines versioned, immutable broker/symbol profiles and parity fixtures
11.1 Profiles — Versioned broker profile contracts

**12. Portfolio** — Maintains simulated account, position, balance, equity, conversion, margin, liquidation, corporate-action, and…
12.1 Accounting — Account, balance, equity, and PnL accounting
12.2 Positions — Position lifecycle and netting/hedging
12.3 Margin — Margin, leverage, and liquidation controls
12.4 Corporate Actions — Corporate-action and optional asset-class lifecycle effects

**13. Costs** — Pure cost/realism kernels for spreads, liquidity, slippage, latency, commission, swaps, borrow fees, and their…
13.1 Spread — Variable and fixed spread simulation
13.2 Slippage — Slippage calculation, cap/floor validation, adverse-selection policy, partial-fill interaction, and slippage diagnostics
13.3 Commission — Commission and broker/exchange fee models
13.4 Swap — Swap, carry, and funding costs
13.5 Slippage — Slippage realism model
13.6 Latency — Execution latency model
13.7 Liquidity — Liquidity depth, market impact, and capacity

**14. Controls** — Replays injected simulator-only risk, compliance, regulatory, market-halt, and kill-switch effects without owning…
14.1 Simulated Risk — Simulation of injected risk-rule, position-size, correlation/concentration, portfolio-kill-switch, and risk-evidence effects only
14.2 Compliance — Compliance, halt, and regulatory replay effects

**15. Journal** — Append-only, tamper-evident run journal, artifact manifest, retention, lineage, and audit-evidence persistence boundary
15.1 Append Only — Append-only journal records and integrity
15.2 Artifacts — Safe artifact paths, atomic writes, checksums, retention tier attachment, failure preservation, and artifact-root controls
15.3 Manifest — Run and journal manifest evidence
15.4 Retention — Artifact and journal retention
15.5 Artifacts — Artifact storage and failure-evidence preservation

**16. Reporting** — Transforms completed run snapshots and journal evidence into metrics, scorecards, realism disclosures, JSON/Markdown…
16.1 Metrics — Deterministic run and scorecard metrics
16.2 Scorecard — Realism classification and promotion scorecard
16.3 Realism — Realism labels and limitations
16.4 Renderers — JSON/Markdown reports and visualization payloads

**17. Operations** — Cross-cutting operational controls: telemetry, quota enforcement, environment certification, security wrappers, canary…
17.1 Instrumentation — Observability decorators and run telemetry
17.2 Quotas — Resource quota and deadline enforcement
17.3 Environment — Environment drift and benchmark certification
17.4 Security — Security, authorization, and redaction wrapper
17.5 Canary — Optional canary divergence analysis

**18. Verification** — Parity, replay, provider-contract, and promotion-verification adapters and fixtures
18.1 MT5 Parity — MT5 execution parity verification
18.2 Provider Contracts — Dependency provider contract verification

**19. Simulator (Services)**
19.1 Test Requirements — Requirement, contract, and regression test suite
19.2 Test Import Safety — Import-safety tests

**20. Simulator (Tests)**
20.1 Test Requirements — Requirement, contract, and regression test suite
20.2 Test Import Safety — Import-safety tests
20.3 Run Simulator Examples — Runnable, focused example functions demonstrating only public simulator capabilities and standard envelopes

---

## Phase 9 : Optimization Service

_Parameter optimization: algorithms, time-series splits, robustness, execution, persistence, and evidence._


**1. Optimization** — Optimization domain package and intentional public tool registry
1.1 Init — Import-safe public registry and foundation declarations

**2. API** — Official AI/API optimization tool boundary
2.1 Tool Boundary — Official optimization tool envelopes and request packaging

**3. Contracts** — Typed domain contracts, ports, and errors
3.1 Models — Optimization domain models and canonical result contracts
3.2 Ports — Repository, execution adapter, and orchestration interfaces
3.3 Errors — Deterministic optimization error taxonomy
3.4 Init — Contracts package foundation declaration

**4. Config** — Validated execution configuration and resource policy
4.1 Execution Profiles — Resource caps, monotonic timeouts, and execution profiles

**5. Validation** — Pre-execution safety and input validation
5.1 Preflight — Preflight validation and safe constraint evaluation

**6. Core** — Pure optimization identity, ranking, scoring, and assessment kernels
6.1 Canonicalization — Canonical parameter-space and candidate hashing
6.2 Candidates — Candidate lifecycle, ranking, and stability analysis
6.3 Scoring — Objective scoring, multi-objective fitness, and deterministic Pareto selection
6.4 Anti Overfit — Anti-overfitting gates and advisory readiness caveats

**7. Algorithms** — Candidate search methods and algorithm-neutral coordination
7.1 Runner — Search-run coordination and algorithm-neutral summaries
7.2 Grid — Grid search and strict iterator expansion
7.3 Random Search — Random, Sobol, and Latin Hypercube search
7.4 Bayesian — Bayesian parameter optimization
7.5 Genetic — Genetic/evolutionary algorithm search
7.6 Init — Algorithms package foundation declaration

**8. Time Series** — Chronological validation splits and walk-forward analysis
8.1 Splits — Leakage-resistant time-series splitting
8.2 Walk Forward — Walk-forward optimization and fold analysis

**9. Robustness** — Robustness, Monte Carlo, scenario, and compliance evidence
9.1 Requests — Robustness request packaging
9.2 Monte Carlo — Monte Carlo simulation, bootstrap, and uncertainty evidence
9.3 Scenario Simulations — Parametric and account-path scenario simulations
9.4 Prop Firm — Prop-firm compliance evidence
9.5 Init — Robustness package foundation declaration

**10. Execution** — Adapter-mediated candidate execution, task dispatch, and progress
10.1 Strategy Loader — Strategy-class resolution
10.2 Backtest Adapter — Single-candidate backtest execution adapter
10.3 Orchestrator — Background tasks, isolated work units, pruning, and deterministic parallel aggregation
10.4 Progress — Progress tracking and parallel performance analysis
10.5 Init — Execution package foundation declaration

**11. Persistence** — Repository-mediated state, checkpoints, cache, and artifact durability
11.1 Repository — Run-state repository contract and idempotent workflow persistence
11.2 Checkpoints — Checkpoint, recovery, and atomic artifact lifecycle
11.3 Candidate Cache — Candidate cache invalidation

**12. Evidence** — Evidence composition, handoffs, chart-ready payloads, and reporting
12.1 Packages — Evidence packages, capacity disclosure, and handoff payloads
12.2 Reports — Evidence-only optimization reporting

**13. Portfolio** — Periodic portfolio optimization support without allocation mutation
13.1 Periodic — Periodic portfolio optimization support

---

## Phase 10 : Live Runtime

_Live trading runtime: config, gates, execution, state, reconciliation, monitoring, security, and promotion._


**1. Live** — Expose only intentional, documented live-domain callable metadata and route integrations while preventing import-time…
1.1 Init — Package scope, import safety, and explicit public boundary
1.2 Contracts — Standard envelope, tool contract, traceability, and side-effect classification
1.3 Tool Registry — Intentional live tool registry and contract catalog

**2. State** — Declare persistence contracts and persistence-related safety requirements without owning schemas, migrations, database…
2.1 Ports — Persistence ports and fail-closed persistence prerequisites
2.2 Manager — Live runtime state and position views
2.3 Idempotency — Live idempotency before mutation

**3. Config** — Load, validate, and expose live runtime settings and secret references without exposing resolved secrets or enabling…
3.1 Models — Validated fail-closed live configuration model
3.2 Loader — Configuration parsing and startup validation
3.3 Secrets — Secret-reference resolution and prohibited raw-secret handling
3.4 Notifications — Safe live notifications
3.5 Security Profile — Mandatory broker communication security gate

**4. Runtime** — Own the safe Live session lifecycle, runtime status, shutdown ordering, recovery diagnostics, and consumer-facing…
4.1 Session Manager — Safe session startup, shutdown, recovery, and runtime events
4.2 Coordination — Bounded queue and conflict coordination contract
4.3 Cost Control — Request, workflow, and session cost budgets
4.4 Signal Processor — Approved signal-to-live-candidate transformation

**5. Gates** — Serve as strict middleware for `route="live"` shared Trading actions by evaluating deterministic, fail-closed…
5.1 Pipeline — Canonical live route gate order and fail-closed behavior
5.2 Policy Matrix — Governance-owned action policy matrix consumption
5.3 Approval — Approval context validation
5.4 Readiness — Readiness, freshness, and state-authority validation
5.5 Kill Switch — Governed kill-switch enforcement and recovery
5.6 Audit And Compensation — Pre-mutation evidence and controlled compensation boundary

**6. Execution** — Coordinate a gate-approved shared Trading action without implementing separate order/position business behavior or an…
6.1 Coordinator — Live action coordination through shared Trading contracts
6.2 Broker Capability Validation — Approved broker capability, response validation, and retry-safe mapping
6.3 Response Classifier — Broker response and side-effect outcome classification
6.4 Shadow — Shadow execution and expected-versus-realized evidence
6.5 Reporting — Evidence-only live report packaging

**7. Reconciliation** — Reconcile internal Live projections against normalized broker truth and govern the authority state after mismatches or…
7.1 Service — Broker-truth reconciliation lifecycle
7.2 Snapshots And Compare — Broker truth normalization and discrepancy comparison
7.3 Authority And Retry Guard — Unknown-outcome authority state and retry guard

**8. Monitoring** — Observe Live health and safety evidence without implementing dashboards, websockets, or UI workflows
8.1 Service — Live operational monitoring aggregation
8.2 Tool Health — Exported live tool health monitoring
8.3 Timeouts And Staleness — Workflow timeout and stale-state monitoring
8.4 Operational Signals — Ingestion, incidents, latency, and snapshot signals

**9. Security** — Map only finite, shared error taxonomy values into structured Live errors without duplicating base exceptions
9.1 Error Mapping — Shared error inheritance and finite Live error taxonomy
9.2 Redaction Boundary — Recursive secret and private-payload redaction

**10. Promotion** — Centralize unresolved owner-decision and production-activation blockers so absence of an approved decision fails closed
10.1 Preconditions — Production activation preconditions and mandatory operational policy evidence

**11. Live (Services)** — Verify every Live requirement through isolated normal, edge, invalid, fail-closed, schema, logging, regression,…
11.1 Test Requirement Traceability — Requirement traceability and coverage enforcement
11.2 Test Live Contracts And Safety — Mandatory Live contract, safety, resilience, and redaction tests

---

## Phase 11 : UI & API Gateway

_FastAPI gateway and web UI: contracts, governance, idempotency, middleware, security, streaming, routes, components._


**1. API**
1.1 Init — API package readiness gate
1.2 Main — Canonical application entry point
1.3 Archive — Gateway composition and optional route safety
1.4 Lifespan — Application lifecycle and safe resource coordination

**2. Contracts** — Versioned request/response/stream DTOs, catalog metadata, and deterministic transport error mappings
2.1 Route Catalog — Route catalog and public capability classification
2.2 DTOs — Boundary DTO validation and standard response envelopes
2.3 Streaming — Stream envelopes, heartbeat, backpressure, and cleanup contract
2.4 Versioning — Version and deprecation compatibility policy
2.5 Pagination — Pagination and response-boundary policy
2.6 Errors — Deterministic transport error translation

**3. Clients**
3.1 Protocols — Service delegation boundary

**4. Dependencies**
4.1 Operator — Operator dependency registry

**5. Config**
5.1 Settings — Gateway configuration and bounded-resource policy

**6. Governance**
6.1 Writes — Governed mutation transport preconditions

**7. Idempotency**
7.1 Repository — Idempotency storage and conflict-safe replay

**8. Middleware**
8.1 Init — Middleware foundation properties
8.2 Redaction — Secret redaction middleware
8.3 Intent — Operator intent classification middleware
8.4 Operator Auth — Operator authorization and protected route enforcement

**9. Security**
9.1 Authentication — User authentication and operator-role enforcement

**10. Streaming**
10.1 Manager — Shared streaming runtime behavior

**11. Routes** — Thin HTTP/WebSocket adapters that validate, authorize, delegate through approved clients/orchestrators, and translate…
11.1 Init — Routing package foundation
11.2 Health — Health endpoints
11.3 Operator — Governed operator command surface
11.4 Operator Stream — Operator event stream route
11.5 Risk — Risk service delegation
11.6 Chat — AI chat, retention, action-draft, and page-context routes
11.7 Sqx — SQX routes
11.8 Backtests — Backtest routes
11.9 Optimization — Optimization routes
11.10 Edge Lab — Edge Lab routes
11.11 Dashboard — Dashboard routes
11.12 Docs — Documentation and import safety routes
11.13 Data — Market-data symbol route
11.14 Auth — Authentication routes foundation
11.15 Settings — Settings management routes
11.16 Strategies — Strategy catalog and live-session strategy routes
11.17 Simulator — Simulator routes
11.18 Live — Live execution control routes

**12. Lib**
12.1 Contracts — UI contract drift prevention

**13. API (Lib)**
13.1 Agentic API — Agentic API client boundary
13.2 Domain Clients — Frontend domain client registry

**14. Governance (Lib)**
14.1 Governed Write — Governed write preflight

**15. Telemetry**
15.1 API Telemetry — Frontend observability and stale-data signaling

**16. Context**
16.1 Page Context — Page context providers and hooks

**17. Layout**
17.1 App Shell — Accessible base layout

**18. Documentation**
18.1 Documentation — Documentation UI components

**19. Strategies**
19.1 Strategy Workspace — Strategy UI workflow

**20. Edge Lab**
20.1 Edge Lab Workspace — Edge Lab UI workflow

**21. Performance**
21.1 Performance Workspace — Performance UI workflow

**22. Operator**
22.1 Operator Controls — Operator emergency and manual controls

**23. Chat**
23.1 AI Chat — AI chat components and client hooks

**24. Dashboard**
24.1 Dashboard — Dashboard components

**25. Simulator**
25.1 Simulator Workspace — Simulation UI workflow

**26. Live**
26.1 Live Workspace — Live UI workflow

**27. Auth**
27.1 Auth Forms — Authentication components

**28. App**
28.1 Route Manifest — Frontend route hierarchy

**29. Components**
29.1 Boundaries — No-domain-logic UI boundary

**30. UI** — Traceability, contract verification, CI gates, examples, documentation, and release evidence
30.1 package.json and tests/ — UI quality gates and traceability

**31. Documentation (2)** — Publish route contracts, examples, API-version/deprecation guidance, stream policies, governance preflight behavior,…
31.1 Route Contract Catalog — Human-readable derivative of the machine-readable `RouteContract` catalog, including…

---

## Phase 12 : Research / Edge Lab

_Research studies: contracts, policies, metrics, features, market-structure and unsupervised studies, reports._


**1. Research** — Public, import-safe research façade and controlled export boundary
1.1 Init — Import Safety, Lazy Namespace, and Public Export Gate
1.2 Service — Official Research Service Tools and Read-Only Workflow Coordination
1.3 Test Plan — Requirement Traceability, Test Gate, Documentation, and Usage-Example Obligations

**2. Contracts** — Versioned, immutable data contracts used across the research service boundary
2.1 Config — Research Workflow, Data, Cleaning, and Resource Configuration
2.2 Models — Core Models, Dataset Contracts, Metrics, and Research Result Types
2.3 Envelopes — Standard Research Envelope and Public Failure Semantics
2.4 Errors — Research Error Taxonomy and Insufficient-Sample Policy
2.5 Catalog — Public Capability Catalog, Contract-First Gate, and Builder Handoff Controls

**3. Policies** — Cross-cutting policy boundaries that constrain research without contaminating mathematical kernels
3.1 Resource Limits — Bounded Research Resource Use and Performance Claims
3.2 Advisory Guard — Read-Only Advisory Boundary and Governed-Action Blocking
3.3 Redaction — Artifact Masking, Secret Avoidance, and Safe Serialization
3.4 Observability — Research Observability, Redacted Logging, and Failure Events
3.5 Reproducibility — Reproducibility Metadata and Deterministic Seed Policy

**4. Core** — Deterministic preparation of trustworthy research datasets from canonical data inputs
4.1 Preparation — Dataset Validation, Cleaning, Preparation, Provenance, and Atomic Research Inputs
4.2 Enrichment — Research Dataset Enrichment and Session Tagging
4.3 Leakage — Leakage Prevention, Chronological Splits, and Data-Snooping Diagnostics
4.4 Sessions — Session Hours, Session Labels, and Seasonality

**5. Metrics** — Deterministic calculation of normalized core research metrics
5.1 Models — Core Metric Contracts and Calculator Protocol
5.2 Calculators — Core Research Metric Calculators
5.3 Registry — Metric Registry

**6. Features** — Pure feature engineering primitives used for research evidence and never as hidden execution controls
6.1 Returns — Returns, Momentum, and Forward Research Labels
6.2 Volatility — Volatility, Range, and Bollinger-Style Features
6.3 Market Structure — Market-Structure and Regime Feature Engineering

**7. Studies** — Evidence-generating study orchestration using pure kernels
7.1 Eds — Event Dependency Studies and Session Edge Discovery
7.2 Null Hypothesis — Null Hypothesis Testing, Bootstrap, Permutation, and Random Shuffling
7.3 Session Strategies — Session Breakout, Session Fade, and Edge Classification

**8. Market Structure** — Reproducible directional market-structure research, calibration, and advisory fit evidence
8.1 Classification — Market-Structure Classification and Resolution
8.2 Calibration — Market-Structure Calibration and Ranking
8.3 Profiles — Market-Structure Profiles, Stability, Robustness, and Advisory Evidence

**9. Unsupervised** — Reproducible unsupervised exploratory research with labelled outputs and advisory-only interpretations
9.1 Service — Unsupervised Research Orchestration
9.2 Pca — Principal Component Analysis and Interpretable Risk Factors
9.3 Clustering — Feature-Space Clustering, Cluster Outcomes, and Advisory Signal Adaptation
9.4 Insights — Unsupervised Insight Reports

**10. Providers** — Optional external research-feed integration isolated from deterministic research kernels
10.1 Protocols — Optional External Provider Contract
10.2 Forexfactory — ForexFactory News and Instrument Page Retrieval

**11. Interactive** — Notebook and analyst convenience helpers built on core contracts, with no external trading authority
11.1 Calendar — Interactive Calendar, Sentiment, and Advisory News Windows
11.2 Analysis — Interactive Research Metrics and Hypothesis Diagnostics

**12. Adapters** — Documented public-contract adapters to other domains
12.1 Analytics — Analytics Metric Adapters for Research

**13. Reports** — Report compilation, profile-scorecard construction, masking, and controlled artifact export
13.1 Rendering — Research Report Rendering and Edge-Lab Scorecard Compilation
13.2 Persistence — Artifact Persistence, Hashing, Atomic Writes, and Report Export

**14. Governance** — Defines the incremental implementation boundary between lightweight Research Core and full Edge Lab
14.1 Layers — Lightweight Research Core Dependency and Full Edge Lab Boundary

---

## Phase 13 : Conversation AI Layer

_Conversational assistant: contracts, config, security, persistence, context, orchestration, providers, streaming._


**1. Conversation** — Public domain gate: exposes the approved Conversation service surface, capability metadata, and no accidental function…
1.1 Init — Package export boundary and import safety
1.2 Catalog — Capability documentation, usage contracts, and traceability catalog

**2. Contracts** — Typed cross-component contracts: models, ports, errors, and stream envelopes that let the domain remain…
2.1 Models — Conversation, action-draft, retention, and prompt result models
2.2 Errors — Documented conversation error contracts
2.3 Ports — Persistence and external-collaboration ports
2.4 Events — Stream event envelope contracts

**3. Config** — Validated runtime configuration: all limits, retention rules, provider behavior, and observability settings are…
3.1 Models — Conversation configuration and retention policy schemas
3.2 Loader — Environment-driven model configuration

**4. Security** — Security boundary: redaction, prompt-injection defense, tool permissions, and draft-only action policy before any…
4.1 Redaction — Payload redaction and normalization
4.2 Tool Permissions — Tool permission registry and read-only evidence admission
4.3 Prompt Injection — Prompt-injection defense and retrieval boundary

**5. Persistence** — Durable conversation storage boundary: repository contracts, SQLite implementation, atomic transactions, locks,…
5.1 SQLite Repository — Atomic SQLite persistence and concurrency control
5.2 Time Codec — UTC time encoding for persistence

**6. Services** — Business services: durable thread, message, retention, memory, and action-draft operations orchestrated through…
6.1 Conversation Service — Thread lifecycle, message persistence, export, and ownership-aware API
6.2 Retention Service — Retention lifecycle, legal hold, archival, and purge rules
6.3 Memory Service — Deterministic durable memory summaries
6.4 Action Drafts — Draft-only governed action artifacts

**7. Context** — Ephemeral page and system context: route-aware UI context construction and compact, auditable prompt layers with no…
7.1 Init — Conversation context package foundation
7.2 Page Context — Compact page context and DOM/state extraction
7.3 Assembler — Canonical context-provider aggregation
7.4 System Context — Structured governance system context
7.5 Prompt Builder — Layered, auditable prompt composition

**8. Orchestration** — Conversation turn coordination: CEO workflow sequencing, planner delegation, read-only tool evidence, and no-mutation…
8.1 Readonly Tools — Read-only tool planning and evidence execution
8.2 Ceo Gateway — CEO chat gateway and deterministic turn workflow

**9. Governance** — Conversation-only action boundary: turns chat requests into draft-only governed proposals and points users to direct…
9.1 Action Boundary — Draft-only governed-action boundary

**10. Providers** — Provider boundary: typed model-stream capability contracts and runtime provider selection behind a stable internal…
10.1 Protocol — AI model provider client interface
10.2 Openai Compatible — OpenAI-compatible, Gemini, and Ollama streaming adapter

**11. Streaming** — Streaming boundary: event shaping, deterministic fallback, backpressure, cancellation, and final turn completion…
11.1 Fallback — Provider-disabled and pre-token deterministic fallback
11.2 Manager — Stream management, cancellation, and final result handling

**12. Observability** — Cross-cutting observability boundary: redacted metrics/audit/latency collection around coordination and provider calls…
12.1 Boundaries — Telemetry, audit, latency, and redaction wrappers
