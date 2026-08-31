# Composition Runtime

> **Package:** `app/composition/`
> **Category:** Non-domain shared substrate
> **Status:** `Implemented`

## Purpose

`app/composition/` applies application policy around the independent kernel. It discovers installed features, validates desired configuration, selects providers, reports readiness, watches configuration, and serializes high-level runtime mutations.

## Implemented ownership

- `FeatureDiscoverer` loading the `haruquantai.features` Python entry-point group plus explicit test/embedded registration.
- Strict TOML `AppConfig` with `[application]`, `[features]`, `[providers]`, and `[logging]` tables.
- Deployment-profile readiness for `offline`, `research`, `backtest`, and `live`.
- `CompositionEngine` orchestration over kernel registry/graph/reconciler/event primitives.
- Serialized configuration reload, provider selection, runtime-failure recovery, and transactional feature replacement.
- Configuration-file watching and code-aligned runtime diagnostics.
- Structured logging infrastructure (`app/composition/logging.py`), versioned JSON Lines schema, deterministic secret redaction with SHA-256 fingerprints, contextvars correlation context, bounded diagnostic capture/expiry, rotating file logging, and owned handler lifecycle management.

## Boundary

`app/composition/` may import `app/kernel/` and `app/contracts/`; it never imports `app/services/`. It does not own the service registry, dependency graph, `FeatureContext`, `FeatureScope`, event bus, state declarations, or replacement models—those are kernel primitives.

Features are not discovered through domain registries or YAML manifests. Each installed feature is an independent Python entry point and supplies a validated `FeatureSpec` from its `manifest.py`. Feature dependencies/effects use `FeatureContext`; composition chooses provider bindings and invokes reconciliation.

## Failure and mutation rules

Entry-point/package errors, capability dependency errors, blocked reasons, cleanup errors, runtime-task failures, and replacement outcomes remain distinct diagnostics. Configuration reload and explicit replacement share one mutation lock. Pre-commit replacement failure retains the old generation; post-commit consumer/cleanup failure is reported as committed but degraded.

The authoritative procedural detail is the [Feature Implementation Pipeline](../../docs/dev/feature_implementation_pipeline.md).

---

## Normative Composition Specification

The stable `§x.y` labels below are preserved for cross-document references. They are authoritative here and no longer identify sections in `docs/PROJECT.md`.

### §6.3 — Feature specifications, capabilities, discovery, and configuration

`manifest.py` exports a `FeatureSpec` with exactly these architectural fields:

| Field | Meaning |
|---|---|
| `feature_id` | Stable `FEAT-*` configuration and diagnostic identity |
| `domain` | Lowercase semantic owner |
| `provides` | Capabilities the mounted provider bundle must publish exactly |
| `requires` | Required capabilities that gate activation |
| `optional` | Optional capabilities available through explicit optional lookup |
| `conflicts` | Feature IDs that cannot be active together |
| `description` | Human-readable purpose |
| `state` | Optional persistent-state declaration |
| `config_keys` | Exact accepted feature configuration keys |

A `CapabilityKey` has a lowercase name and positive major version; its formatted identifier is `<name>@<major>`, normally `<domain>.<capability>@<major>`. The key does not contain a schema hash, implementation hash, permission set, or full semantic version. Those belong in the relevant application contract or reproducibility evidence.

`FeatureDiscoverer` loads installed `haruquantai.features` entry points with `importlib.metadata` and also supports explicit registration for tests/embedded composition. A failing entry point is isolated and reported without crashing unrelated discovery.

D-UI does not use `FeatureSpec` or Python discovery. Its typed manifests declare stable `FEAT-UI-*` identity, capability dependencies, contributions, configuration, and removal metadata; the UI composition bridge consumes public capability snapshots and withdraws only the affected view contribution when a dependency disappears.

Application desired state is strict TOML with only `[application]`, `[features]`, `[providers]`, and optional `[logging]` top-level tables. Supported profiles are `offline`, `research`, `backtest`, and `live`. Each `[features.FEAT-*]` table declares `enabled` and either inline feature keys or a nested `.config` table, never both. `[providers]` maps a capability identifier to the selected provider feature ID. The optional `[logging]` table defines `level`, `console`, `file_path`, `max_bytes`, `backup_count`, and `capture_capacity`. Unknown profiles, sections, keys, invalid IDs, and ambiguous unselected providers fail explicitly.

### §6.5 — Dependency resolution, activation, reconciliation, removal, and replacement

- The dependency graph rejects required cycles. Optional-only cycles do not gate activation.
- Exactly one compatible provider binds automatically. Multiple candidates without a valid `[providers]` selection block the consumer.
- Mount is staged in a fresh scope. The provider bundle must exactly match `FeatureSpec.provides`; only then is it atomically published.
- Mount/config/provider-publication failure closes the staged scope, publishes no partial provider, and records `FAILED_START`.
- Enablement, configuration, selected-provider, provider arrival/removal, and runtime-failure changes reconcile the exact transitive affected consumer closure in dependency order.
- Optional provider arrival/removal remounts the consumer so its committed dependency view never changes underneath a running instance.
- Configuration reload and explicit replacement share one mutation lock, preventing overlapping feature mounts.
- An unexpected `context.spawn()` task failure withdraws the owner capabilities, records `FAILED_RUNTIME`, publishes `FeatureRuntimeFailedEvent`, reconciles dependents, and preserves unrelated branches.
- Explicit replacement requires the same provided-capability set, mounts and health-checks a shadow generation, optionally quiesces/drains the old feature, then atomically swaps registry bindings.
- Any pre-commit replacement failure closes the shadow scope and retains the old generation. Post-commit consumer-remount or old-scope cleanup failure is reported as committed but degraded, not rolled back.
- Physical removal deletes the feature package, feature-local tests, entry point, and Import Linter module entry in an isolated copy, then proves stale desired state becomes `MISSING` while unrelated features continue.

### §6.6 — Interfaces, readiness, plugins, and diagnostics

`RuntimeStatus`, `CompositionEngine.get_status()`, and the capability registry expose profile readiness, missing profile capabilities, active features/capabilities and owner generations, feature states, blocked reasons, package/capability errors, runtime failures, replacement reports, effects, and cleanup errors. The launcher may serialize this state for local diagnostics. Product-facing HTTP, SSE, CLI, MCP, and automation projections are removable D-IFACE features and must not become a second runtime model.

Trusted installed Python feature distributions run in process through `haruquantai.features` and receive normal `FeatureContext` lifecycle ownership. Untrusted plugins, scripts, connectors, compilers, AI tools, and native extensions remain a different product boundary: they execute in supervised processes/containers and exchange public wire contracts and artifact handles. Installing an in-process feature grants trusted-code authority and cannot satisfy an untrusted-plugin isolation requirement.

### §6.7 — Structured logging, correlation, redaction, and retention substrate

`app/composition/logging.py` provides the non-domain runtime logging substrate for `NFR-OBS-001`, `NFR-OBS-005`, and `NFR-OBS-009`:

- **Schema & Configuration:** Emits deterministic JSON Lines records with schema version `1`, record-created UTC ISO timestamps, level, logger name, event identifier, message, a per-record correlation snapshot, structured fields, and sanitized exception metadata. Reformatting one fixed `LogRecord` is byte-identical. `LoggingConfig(level, console, file_path, max_bytes, backup_count, capture_capacity)` accepts the case-insensitive application levels `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`; byte, backup, and capture bounds must all be strictly positive.
- **Correlation Propagation:** `bind_correlation(**kwargs)` manages context-local correlation dimensions via `contextvars.ContextVar` that automatically propagate across `asyncio` task contexts and restore cleanly on exit. Supported standard dimensions include `request_id`, `correlation_id`, `causation_id`, `reconciliation_id`, `workspace_id`, `component_id`, `job_id`, `run_id`, `task_id`, `strategy_id`, `result_id`, `generation`, and `operation_id`.
- **Deterministic Redaction & Bounds:** Sensitive keys fingerprint their complete scalar or canonically serialized compound values as `[REDACTED:sha256:{digest[:8]}]`. Recognized password, token, API-key, JWT, and Bearer text is redacted before truncation. The shared sanitizer converts mappings, sequences, sets, non-finite numbers, cycles, and unsupported objects to deterministic JSON-safe forms before console, file, or capture use. Private safety bounds are 4,096 characters per text value, 64 mapping/collection items, nesting depth 8, and 32,768 UTF-8 bytes per encoded record; oversized records become schema-valid bounded summaries with a fingerprint of omitted sanitized content.
- **Retention & Diagnostic Capture:** `DiagnosticCaptureHandler` retains at most `capture_capacity` active records and the same number of recent expired IDs. `is_expired(diagnostic_id)` is true only for a recently evicted or explicitly cleared issued ID; active and never-issued IDs return false, and IDs forgotten from the bounded expiry history become unknown. Optional `RotatingFileHandler` provides size-based rotation with strictly positive byte and backup bounds. Durable referenced-log pinning remains pending system work.
- **Owned Handler Lifecycle:** `configure_logging()` constructs a new tagged `_haruquantai_owned` generation transactionally before replacing the prior owned generation. Failed setup leaves the previous generation, foreign handlers, and logger level intact. The returned `LoggingHandle` removes, flushes, and closes only its active generation, restores the logger state that preceded the first owned generation, and retains at most 16 stage/type-only cleanup diagnostics. The launcher reports those diagnostics through one unattached, immediately closed structured stderr handler. Repeated or stale-handle close is safe, and global `logging.shutdown()` is never called.
- **Safe Runtime Metadata:** Launcher and watcher events use deterministic configuration-path references rather than raw caller-supplied paths. Successful `--status` output remains one JSON document on stdout; owned operational records use stderr, rotating files, or bounded capture.
- **Primary Executable Command:** `uv run python -m app.composition.logging`
- **Named Harness Scenarios:**
  - `Scenario 1 (NFR-OBS-001)`: Structured JSON formatting and level filtering.
  - `Scenario 2 (NFR-OBS-001)`: Async/nested correlation context propagation and reset.
  - `Scenario 3 (NFR-OBS-009)`: Deterministic secret redaction and SHA-256 fingerprinting.
  - `Scenario 4 (NFR-OBS-005)`: Bounded diagnostic capture and explicit eviction expiry.
  - `Scenario 5 (NFR-OBS-005)`: Owned handler lifecycle, non-interference, and idempotent cleanup.
- **Exclusions:** Kernel, Contracts, and service packages never import Composition for logging; they use standard-library `logger = logging.getLogger(__name__)`. This module is an implemented foundation for applicable portions of `NFR-OBS-001`, `NFR-OBS-005`, and `NFR-OBS-009`, not requirement-level completion. Stable product failure envelopes, metrics, differential evidence, causal product events, durable referenced-log storage, distributed tracing, and product-wide emission remain separate pending work.
