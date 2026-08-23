# HaruQuantAI Agile Implementation Order

> **Status:** Outcome-driven product-delivery sequence; composability foundation already implemented
> **Architecture baseline:** `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and authoritative domain READMEs
> **Inventory:** 3 non-domain shared modules, 15 business domains, 142 planned features, 549 business FRs, and 33 retained shared-foundation trace IDs (`FR-KERN-*`)
> **Last updated:** 2026-08-23

## 1. How to use this file

This document schedules delivery; it does not restate or weaken product behavior. `PROJECT.md` owns system scope, cross-domain workflows, system NFRs, and phase gates. `ARCHITECTURE.md` owns universal structural/runtime constraints. Each owning package README remains the sole feature/FR registry and acceptance authority.

The sequence is agile in the strict sense used here: every increment produces a demonstrable vertical outcome through the UI, while preserving headless contract parity and feature removability.

- Preserve the implemented `app/kernel/` and `app/composition/` runtime plus the `app/contracts/` boundary. Product work extends them through contract-first vertical slices, with public gateways implemented as removable D-IFACE features.
- Implement the displayed requirement slices in order within an increment unless the documented dependency graph proves two slices independent.
- A feature may span increments. A heading marked **Partial** advances only the listed requirements and does not complete the feature.
- Every business `FR-*` checkbox appears exactly once, in the earliest increment where its full acceptance evidence can pass.
- Every product `FEAT-*` completion checkbox appears exactly once, beside that feature's final requirement slice.
- Mark a requirement complete only after appending executable evidence in the form `— evidence: path/to/file:line` and passing its owning README acceptance conditions.
- Mark a feature complete only after all its requirement slices, contracts, configuration, lifecycle, dependency, failure, documentation, leak, interface where applicable, and physical-removal gates pass.
- UI work starts in Increment 1. Each increment verifies loading, empty, stale, unavailable, error, interaction, accessibility, contract-parity, and removal behavior as applicable.
- A demo checkpoint proves usable progress; it never changes an unfinished feature from `Partial` to complete.
- A later increment may begin on an independent capability lane, but no consumer requirement may pass before its hard prerequisite or the prerequisite's earlier ordered slice in the same increment.
- A phase or advanced capability releases only after its applicable `PROJECT.md` phase gate passes; increment placement never waives a safety, determinism, parity, isolation, or recovery requirement.

### Completion notation

```text
##### 2.3 Partial — FEAT-EXAMPLE-BROAD_FEATURE
1. [ ] FR-EXAMPLE-EARLY_BEHAVIOR

##### 7.4 [ ] FEAT-EXAMPLE-BROAD_FEATURE
1. [ ] FR-EXAMPLE-FINAL_BEHAVIOR
```

When completed:

```text
1. [x] FR-EXAMPLE-EARLY_BEHAVIOR — evidence: tests/example/test_behavior.py:42
```

## 2. Authoritative domain inventory

Kernel and Composition are implemented non-domain runtime modules; Contracts is the specified shared boundary populated incrementally by real feature slices. “First increment” means the first planned product work in the domain, not domain completion.

| First increment | Domain | Features | Business FRs | Authoritative document |
|---:|---|---:|---:|---|
| 1 | `D-WS` Workspace | 6 | 18 | [Workspace README](../../app/services/workspace/README.md) |
| 1 | `D-PLUG` Plugins | 7 | 9 | [Plugins README](../../app/services/plugins/README.md) |
| 1 | `D-IFACE` Interfaces | 7 | 30 | [Interfaces README](../../app/services/interfaces/README.md) |
| 1 | `D-UI` User Interface | 17 | 99 | [User Interface README](../../app/ui/README.md) |
| 2 | `D-CAT` Catalogue | 7 | 14 | [Catalogue README](../../app/services/catalogue/README.md) |
| 2 | `D-DATA` Data | 14 | 47 | [Data README](../../app/services/data/README.md) |
| 3 | `D-STRAT` Strategy | 13 | 47 | [Strategy README](../../app/services/strategy/README.md) |
| 4 | `D-SIM` Simulator | 12 | 45 | [Simulator README](../../app/services/simulator/README.md) |
| 4 | `D-ANA` Analytics | 9 | 38 | [Analytics README](../../app/services/analytics/README.md) |
| 6 | `D-RES` Research | 13 | 51 | [Research README](../../app/services/research/README.md) |
| 7 | `D-PORT` Portfolio | 8 | 24 | [Portfolio README](../../app/services/portfolio/README.md) |
| 7 | `D-ORCH` Orchestration | 7 | 33 | [Orchestration README](../../app/services/orchestration/README.md) |
| 10 | `D-BRK` Broker Connectivity | 7 | 28 | [Broker Connectivity README](../../app/services/broker/README.md) |
| 10 | `D-RISK` Runtime Risk | 7 | 30 | [Runtime Risk README](../../app/services/risk/README.md) |
| 10 | `D-TRD` Trading | 8 | 36 | [Trading README](../../app/services/trading/README.md) |

## 3. Increment and phase map

| Increment | Product outcome | Phase relationship |
|---:|---|---|
| 0 | Preserve executable composability foundation | Foundation evidence; not a claim that every Phase 0 product gate is complete |
| 1 | Executable Product Shell and Local Workspace | Foundation-preserving product slice; prepares Phase 1 |
| 2 | Catalogue and Historical-Data Onboarding | Phase 1 input foundation |
| 3 | Typed Strategy Authoring | Phase 1 authoring slice |
| 4 | First Deterministic Backtest and Results | Phase 1 execution and analytics slice |
| 5 | MQL5 Code Generation and Parity | Completes the Phase 1 target-parity path |
| 6 | Reproducible Research Factory | Phase 2 release slice |
| 7 | Portfolio and Project Workflows | Phase 3 portfolio/project/automation slice |
| 8 | Extensions, Additional Targets, and Advanced Compute | Phase 3 extensions plus independently gated Phase 4 capabilities |
| 9 | Synthetic, News, Live-Event, and Drift Evidence | Independently gated Phase 4 evidence capabilities |
| 10 | Governed Broker, Risk, and Trading Operations | Optional Phase 5 governed-operations slice |
| 11 | Hosted Workspace Boundary and Final Release | Hosted Phase 4 capability plus complete release matrix |

## 4. Agile vertical implementation sequence

### Increment 0 — Implemented composability foundation (preserve)

**Status:** Composability substrate complete; structured-logging hardening is the first pending delivery prerequisite.

**Purpose:** Freeze the proven composability substrate as the baseline for every product increment; extend it without reimplementing or bypassing it.

**Vertical path:** `Feature specification → contracts → composition → D-IFACE gateway where required → provider/consumer/state evidence`

**UI demo checkpoint:** This is a preservation increment rather than a new UI slice. Verify that Composition readiness, capability, feature, and failure diagnostics remain available for the Increment 1 D-IFACE/UI shell to project.

**Exit gate:** Existing architecture, composition, feature-documentation, lifecycle, replacement, and removal suites remain green. The structured-logging task below must pass before Increment 1 product work starts.

Implemented evidence includes:

1. Independent capability, feature-specification, context/scope, registry, graph, reconciliation, event, task, state, and replacement primitives.
2. Python `haruquantai.features` discovery plus explicit test/embedded registration.
3. Strict TOML feature/provider configuration, readiness profiles, file watching, and serialized composition mutation.
4. Direct Composition runtime diagnostics for readiness, active capabilities, feature state, dependency failures, replacement, and cleanup evidence.
5. Business-neutral test fixtures proving provider/consumer dependency binding, state declarations, and removal without registering product features.
6. Dependency loss, ambiguity, cycle, rollback, runtime-failure, LIFO cleanup, repeated lifecycle, replacement, documentation-drift, import-boundary, and removal tests.

#### Foundation task 0.1 — [ ] Composition-owned structured logging

This is non-domain runtime infrastructure, not a product `FEAT-*` or business `FR-*`. It implements the logging substrate required by `NFR-OBS-001`, `NFR-OBS-005`, and `NFR-OBS-009` without introducing a shared logger singleton or a fifth shared module.

1. [ ] Add `app/composition/logging.py` for structured formatting, levels, deterministic redaction, correlation context, retention integration, bounded diagnostic capture, and lifecycle-safe handler cleanup — evidence: path:line
2. [ ] Configure logging from `app/main.py` before the composition engine begins runtime work, and close owned handlers during shutdown — evidence: path:line
3. [ ] Use `logger = logging.getLogger(__name__)` only in modules with workflow, lifecycle, I/O, state-transition, retry, decision, or failure boundaries; pure contracts, DTOs, deterministic helpers, trivial accessors, and high-frequency numerical modules remain log-free unless required — evidence: path:line
4. [ ] Prove structured schema, correlation propagation, redaction, bounded capture/retention behavior, no duplicate handlers, repeated startup/shutdown cleanup, and secret-safe failure output — evidence: path:line

Do not recreate `app/contracts/kernel/`, YAML component manifests, `CompositionContext`, per-FR runtime registrations, domain registries, or another backend lifecycle/effect framework. D-UI uses the documented TypeScript/React feature variant and consumes public capability state.

### Increment 1 — Executable Product Shell and Local Workspace

**Phase alignment:** Foundation-preserving product slice; prepares Phase 1

**Scope:** 42 business FRs across 15 feature slices; 7 feature completion gates and 8 partial slices.

**Purpose:** Deliver the first usable application immediately: a secured local workspace, capability-aware public gateway, bounded plugin contribution declarations, and an accessible React shell with truthful diagnostics.

**Vertical path:** `Launcher → Workspace → D-IFACE capability/readiness gateway → D-UI shell`

**UI demo checkpoint:** Launch React, authenticate locally, open or diagnose a workspace, navigate the shell, inspect capability/readiness state, preserve a draft/layout preference, and observe explicit unavailable/error states.

**Exit gate:** The UI starts without waiting for later domains; workspace/configuration/recovery and gateway failures are visible, keyboard focus is deterministic, and deleting any participating feature leaves the remaining substrate healthy.

#### `D-WS` — [Workspace](../../app/services/workspace/README.md)

##### 1.1 [ ] `FEAT-WS-MANAGE_WORKSPACES`

1. [ ] `FR-WS-INITIALIZE_WORKSPACE`
2. [ ] `FR-WS-MIGRATE_WORKSPACE_SCHEMA`
3. [ ] `FR-WS-FENCE_WORKSPACE_WRITERS`
4. [ ] `FR-WS-RECOVER_WORKSPACE_STATE`
5. [ ] `FR-WS-BACKUP_WORKSPACE`

##### 1.2 [ ] `FEAT-WS-CONFIGURE_RUNTIME`

1. [ ] `FR-WS-CONFIGURE_WORKSPACE`
2. [ ] `FR-WS-ENFORCE_STORAGE_GUARDS`
3. [ ] `FR-WS-CONFIGURE_SERVER_RUNTIME`
4. [ ] `FR-WS-PUBLISH_RUNTIME_SUPPORT`

##### 1.3 [ ] `FEAT-WS-SECURE_LOCAL_ACCESS`

1. [ ] `FR-WS-ISSUE_LOCAL_SESSION`
2. [ ] `FR-WS-REPORT_SYSTEM_READINESS`

##### 1.4 [ ] `FEAT-WS-BUILD_DIAGNOSTICS`

1. [ ] `FR-WS-BUILD_DIAGNOSTIC_BUNDLE`

#### `D-PLUG` — [Plugins](../../app/services/plugins/README.md)

##### 1.5 [ ] `FEAT-PLUG-DECLARE_MANIFESTS`

1. [ ] `FR-PLUG-DECLARE_PLUGIN_MANIFESTS`

##### 1.6 [ ] `FEAT-PLUG-REGISTER_CONTRIBUTIONS`

1. [ ] `FR-PLUG-REGISTER_PLUGIN_CONTRIBUTIONS`

#### `D-IFACE` — [Interfaces](../../app/services/interfaces/README.md)

##### 1.7 Partial — `FEAT-IFACE-SERVE_API_EVENTS`

1. [ ] `FR-IFACE-SERVE_VERSIONED_API`
2. [ ] `FR-IFACE-ENFORCE_CONCURRENCY_TOKENS`
3. [ ] `FR-IFACE-DEDUPLICATE_MUTATIONS`
4. [ ] `FR-IFACE-REPLAY_INTERFACE_EVENTS`
5. [ ] `FR-IFACE-TRACK_ASYNC_JOBS`
6. [ ] `FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS`
7. [ ] `FR-IFACE-EVOLVE_API_COMPATIBLY`

##### 1.8 Partial — `FEAT-IFACE-AUTOMATE_COMMANDS`

1. [ ] `FR-IFACE-DELEGATE_APPLICATION_CALLS`
2. [ ] `FR-IFACE-TRACK_DURABLE_COMMANDS`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 1.9 [ ] `FEAT-UI-COMPOSE_SHELL`

1. [ ] `FR-UI-ASSEMBLE_SHELL`
2. [ ] `FR-UI-DISCOVER_WORKSPACES`
3. [ ] `FR-UI-SWITCH_WORKSPACES`
4. [ ] `FR-UI-SHOW_CAPABILITY_STATE`
5. [ ] `FR-UI-RESTORE_ROUTE`

##### 1.10 Partial — `FEAT-UI-START_WORK`

1. [ ] `FR-UI-PRESENT_HOME`
2. [ ] `FR-UI-SHOW_PRODUCT_NEWS`

##### 1.11 Partial — `FEAT-UI-MANAGE_LAYOUTS`

1. [ ] `FR-UI-PERSIST_LAYOUTS`
2. [ ] `FR-UI-RESTORE_LAYOUTS`
3. [ ] `FR-UI-SCALE_VIEWS`

##### 1.12 Partial — `FEAT-UI-EDIT_INPUTS`

1. [ ] `FR-UI-PRESERVE_DRAFTS`

##### 1.13 Partial — `FEAT-UI-MONITOR_WORK`

1. [ ] `FR-UI-TRACK_PROGRESS`
2. [ ] `FR-UI-STREAM_ACTIVITY`
3. [ ] `FR-UI-PRESENT_FAILURES`

##### 1.14 Partial — `FEAT-UI-ADMINISTER_SYSTEM`

1. [ ] `FR-UI-SET_APPEARANCE`
2. [ ] `FR-UI-CONFIGURE_CLIENT`
3. [ ] `FR-UI-MANAGE_LICENSE`

##### 1.15 Partial — `FEAT-UI-ENSURE_ACCESS`

1. [ ] `FR-UI-MANAGE_FOCUS`
2. [ ] `FR-UI-DISTINGUISH_STATE`

### Increment 2 — Catalogue and Historical-Data Onboarding

**Phase alignment:** Phase 1 input foundation

**Scope:** 50 business FRs across 19 feature slices; 18 feature completion gates and 1 partial slices.

**Purpose:** Make real, immutable market inputs manageable from the UI before strategy or simulation work begins.

**Vertical path:** `D-UI data/input slices → Catalogue → Data ingestion/quality/versioning → Workspace artifacts`

**UI demo checkpoint:** Create or import catalogue definitions, import historical data, inspect mappings/sessions/quality/lineage, resolve findings, export a pinned version, and bind valid input data.

**Exit gate:** A user can prepare trustworthy pinned data entirely from the UI; incomplete, ambiguous, or invalid input never publishes a committed version.

#### `D-CAT` — [Catalogue](../../app/services/catalogue/README.md)

##### 2.1 [ ] `FEAT-CAT-CATALOG_INSTRUMENTS`

1. [ ] `FR-CAT-DEFINE_INSTRUMENTS`
2. [ ] `FR-CAT-VERSION_INSTRUMENTS`
3. [ ] `FR-CAT-PROTECT_REFERENCED_VERSIONS`

##### 2.2 [ ] `FEAT-CAT-MAP_PROVIDERS`

1. [ ] `FR-CAT-MAP_BROKER_SYMBOLS`
2. [ ] `FR-CAT-MAP_PROVIDER_IDENTITIES`

##### 2.3 [ ] `FEAT-CAT-DEFINE_SESSIONS`

1. [ ] `FR-CAT-DEFINE_TRADING_SESSIONS`
2. [ ] `FR-CAT-DEFINE_MARKET_CALENDARS`
3. [ ] `FR-CAT-PREVIEW_TRADING_INTERVALS`

##### 2.4 [ ] `FEAT-CAT-DEFINE_TRADING_RULES`

1. [ ] `FR-CAT-ROUND_ORDER_VALUES`
2. [ ] `FR-CAT-RESOLVE_TRADING_COSTS`

##### 2.5 [ ] `FEAT-CAT-MANAGE_UNIVERSES`

1. [ ] `FR-CAT-VERSION_UNIVERSES`
2. [ ] `FR-CAT-TIMEBOUND_UNIVERSE_MEMBERS`

##### 2.6 [ ] `FEAT-CAT-CONVERT_CURRENCIES`

1. [ ] `FR-CAT-CONVERT_CURRENCIES`

##### 2.7 [ ] `FEAT-CAT-EXCHANGE_CATALOGUE`

1. [ ] `FR-CAT-EXCHANGE_CATALOGUE_DEFINITIONS`

#### `D-DATA` — [Data](../../app/services/data/README.md)

##### 2.8 [ ] `FEAT-DATA-INGEST_HISTORY`

1. [ ] `FR-DATA-REGISTER_DATA_CONNECTIONS`
2. [ ] `FR-DATA-IMPORT_CSV_DATA`
3. [ ] `FR-DATA-PUBLISH_DATA_VERSIONS`
4. [ ] `FR-DATA-PIN_DATA_PROVENANCE`
5. [ ] `FR-DATA-REPORT_IMPORT_COUNTS`

##### 2.9 [ ] `FEAT-DATA-IMPORT_QUANTDATA`

1. [ ] `FR-DATA-DISCOVER_QUANTDATA_SERIES`
2. [ ] `FR-DATA-DECODE_QUANTDATA_FILES`
3. [ ] `FR-DATA-SYNC_QUANTDATA_CATALOGUE`
4. [ ] `FR-DATA-RECORD_QUANTDATA_LINEAGE`

##### 2.10 [ ] `FEAT-DATA-NORMALIZE_TICKS`

1. [ ] `FR-DATA-PRESERVE_TICK_FIELDS`

##### 2.11 [ ] `FEAT-DATA-RESOLVE_QUALITY`

1. [ ] `FR-DATA-DETECT_DATA_QUALITY`
2. [ ] `FR-DATA-RESOLVE_QUALITY_FINDINGS`
3. [ ] `FR-DATA-VALIDATE_OHLC_BARS`
4. [ ] `FR-DATA-ORDER_MARKET_ROWS`
5. [ ] `FR-DATA-LOCK_DATA_PUBLICATION`

##### 2.12 [ ] `FEAT-DATA-AGGREGATE_BARS`

1. [ ] `FR-DATA-AGGREGATE_TIMEFRAMES`
2. [ ] `FR-DATA-RECORD_AGGREGATION_LINEAGE`
3. [ ] `FR-DATA-DEFINE_CUSTOM_TIMEFRAMES`

##### 2.13 [ ] `FEAT-DATA-MANAGE_RETENTION`

1. [ ] `FR-DATA-PREVIEW_DATA_COVERAGE`
2. [ ] `FR-DATA-EXPORT_DATA_SERIES`
3. [ ] `FR-DATA-COLLECT_REACHABLE_ARTIFACTS`

##### 2.14 [ ] `FEAT-DATA-ALIGN_SERIES`

1. [ ] `FR-DATA-ALIGN_EXTERNAL_SERIES`
2. [ ] `FR-DATA-DEFINE_ALIGNMENT_POLICY`

##### 2.15 [ ] `FEAT-DATA-PREPARE_PROFILES`

1. [ ] `FR-DATA-VALIDATE_PROFILE_SOURCE`

##### 2.16 [ ] `FEAT-DATA-IMPORT_INDICATORS`

1. [ ] `FR-DATA-IMPORT_INDICATOR_VALUES`

##### 2.17 [ ] `FEAT-DATA-BIND_RUN_DATA`

1. [ ] `FR-DATA-BIND_COMMITTED_DATA`
2. [ ] `FR-DATA-VALIDATE_PRECISION_INPUTS`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 2.18 [ ] `FEAT-UI-EDIT_INPUTS`

1. [ ] `FR-UI-RENDER_FIELDS`
2. [ ] `FR-UI-VALIDATE_INPUT`
3. [ ] `FR-UI-RESOLVE_CONFLICTS`
4. [ ] `FR-UI-CONFIRM_IMPACT`

##### 2.19 Partial — `FEAT-UI-MANAGE_DATA`

1. [ ] `FR-UI-BROWSE_DATASETS`
2. [ ] `FR-UI-IMPORT_DATA`
3. [ ] `FR-UI-EXPORT_DATA`
4. [ ] `FR-UI-EDIT_INSTRUMENTS`
5. [ ] `FR-UI-EDIT_SESSIONS`

### Increment 3 — Typed Strategy Authoring

**Phase alignment:** Phase 1 authoring slice

**Scope:** 33 business FRs across 11 feature slices; 9 feature completion gates and 2 partial slices.

**Purpose:** Add a UI-driven typed strategy language and immutable editing workflow over the proven catalogue/data foundation.

**Vertical path:** `D-UI typed editors → Strategy validation/versioning → Catalogue/Data contracts`

**UI demo checkpoint:** Create, edit, validate, version, clone, import/export, and restore a strategy draft using canonical typed blocks and settings.

**Exit gate:** The UI and server validator agree on the canonical strategy version; invalid types, blocks, shifts, or conflicts cannot be published.

#### `D-STRAT` — [Strategy](../../app/services/strategy/README.md)

##### 3.1 [ ] `FEAT-STRAT-DEFINE_AST`

1. [ ] `FR-STRAT-REPRESENT_TYPED_AST`
2. [ ] `FR-STRAT-DEFINE_AST_NODES`
3. [ ] `FR-STRAT-DEFINE_AST_TYPES`
4. [ ] `FR-STRAT-DESCRIBE_BLOCKS`

##### 3.2 [ ] `FEAT-STRAT-CATALOG_BLOCKS`

1. [ ] `FR-STRAT-SUPPORT_STRATEGY_NODES`
2. [ ] `FR-STRAT-DEFINE_PARAMETER_DOMAINS`
3. [ ] `FR-STRAT-CATALOG_REFERENCE_BLOCKS`

##### 3.3 [ ] `FEAT-STRAT-CONFIGURE_CHARTS`

1. [ ] `FR-STRAT-CATALOG_BUILTIN_BLOCKS`
2. [ ] `FR-STRAT-CONFIGURE_TRADE_DIRECTIONS`
3. [ ] `FR-STRAT-DEFINE_SERIES_SHIFTS`

##### 3.4 [ ] `FEAT-STRAT-VERSION_STRATEGIES`

1. [ ] `FR-STRAT-VERSION_STRATEGY_DRAFTS`
2. [ ] `FR-STRAT-NORMALIZE_STRATEGY_AST`
3. [ ] `FR-STRAT-VALIDATE_STRATEGIES`

##### 3.5 [ ] `FEAT-STRAT-EDIT_TEMPLATES`

1. [ ] `FR-STRAT-DEFINE_STRATEGY_TEMPLATES`
2. [ ] `FR-STRAT-EDIT_STRATEGIES_VISUALLY`
3. [ ] `FR-STRAT-FILTER_COMPATIBLE_BLOCKS`
4. [ ] `FR-STRAT-SNAPSHOT_BACKTEST_DRAFT`
5. [ ] `FR-STRAT-DEFINE_SEARCH_PARAMETERS`
6. [ ] `FR-STRAT-CONSTRAIN_TEMPLATE_GRAMMAR`

##### 3.6 [ ] `FEAT-STRAT-EXCHANGE_STRATEGIES`

1. [ ] `FR-STRAT-EXCHANGE_NATIVE_STRATEGIES`
2. [ ] `FR-STRAT-ISOLATE_LEGACY_IMPORTS`
3. [ ] `FR-STRAT-IMPORT_LEGACY_STRATEGIES`

##### 3.7 [ ] `FEAT-STRAT-DEFINE_ARCHITECTURES`

1. [ ] `FR-STRAT-DEFINE_STRATEGY_ARCHITECTURES`
2. [ ] `FR-STRAT-DEFINE_RANDOM_GROUPS`
3. [ ] `FR-STRAT-MAP_OPPOSITE_BLOCKS`

##### 3.8 [ ] `FEAT-STRAT-DEFINE_INDICATORS`

1. [ ] `FR-STRAT-DEFINE_EXTERNAL_INDICATORS`

##### 3.9 [ ] `FEAT-STRAT-MODEL_ATM_EXITS`

1. [ ] `FR-STRAT-MODEL_ATM_EXITS`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 3.10 Partial — `FEAT-UI-MANAGE_LAYOUTS`

1. [ ] `FR-UI-MANAGE_TABS`

##### 3.11 Partial — `FEAT-UI-AUTHOR_STRATEGIES`

1. [ ] `FR-UI-EDIT_STRATEGY_TREE`
2. [ ] `FR-UI-BROWSE_BLOCKS`
3. [ ] `FR-UI-CONFIGURE_STRATEGY`
4. [ ] `FR-UI-VALIDATE_STRATEGY`
5. [ ] `FR-UI-USE_STRATEGY_EXAMPLES`

### Increment 4 — First Deterministic Backtest and Results

**Phase alignment:** Phase 1 execution and analytics slice

**Scope:** 80 business FRs across 19 feature slices; 14 feature completion gates and 5 partial slices.

**Purpose:** Close the first end-to-end product loop early: strategy plus data produces a deterministic committed result that is immediately inspectable in the UI.

**Vertical path:** `D-UI author/test → Simulator → Analytics → D-IFACE queries/events → D-UI results/databank`

**UI demo checkpoint:** Run a pinned backtest, observe truthful progress, inspect metrics/equity/trades/charts, use nonvisual alternatives, save/query a databank view, and export source-linked results.

**Exit gate:** Repeated execution produces the required deterministic evidence; only reconciled committed results appear as final, and the complete manual loop is usable from the UI.

#### `D-SIM` — [Simulator](../../app/services/simulator/README.md)

##### 4.1 [ ] `FEAT-SIM-CONFIGURE_ENGINE`

1. [ ] `FR-SIM-BUILD_RUN_MANIFEST`
2. [ ] `FR-SIM-PIN_RUN_INPUTS`
3. [ ] `FR-SIM-PROCESS_EVENT_STREAM`
4. [ ] `FR-SIM-ENFORCE_CLOSED_INPUTS`
5. [ ] `FR-SIM-DEFINE_ENGINE_SEMANTICS`
6. [ ] `FR-SIM-VERSION_ENGINE_PROFILES`

##### 4.2 [ ] `FEAT-SIM-MODEL_PRECISION`

1. [ ] `FR-SIM-MODEL_INTRABAR_PATH`
2. [ ] `FR-SIM-SIMULATE_FROM_M1`
3. [ ] `FR-SIM-APPLY_CUSTOM_SPREAD`
4. [ ] `FR-SIM-APPLY_RECORDED_SPREAD`

##### 4.3 [ ] `FEAT-SIM-SIMULATE_ORDERS`

1. [ ] `FR-SIM-JOURNAL_SIMULATION_EVENTS`
2. [ ] `FR-SIM-VALIDATE_MARKET_ORDERS`
3. [ ] `FR-SIM-PROCESS_PENDING_ORDERS`
4. [ ] `FR-SIM-PROCESS_STOP_LIMITS`
5. [ ] `FR-SIM-MODEL_POSITION_ACCOUNTING`
6. [ ] `FR-SIM-TRACK_ENTRY_IDENTITIES`

##### 4.4 [ ] `FEAT-SIM-CALCULATE_COSTS`

1. [ ] `FR-SIM-CALCULATE_POSITION_SIZE`
2. [ ] `FR-SIM-REJECT_INVALID_SIZE`
3. [ ] `FR-SIM-APPLY_SPREAD`
4. [ ] `FR-SIM-APPLY_SLIPPAGE`
5. [ ] `FR-SIM-APPLY_COMMISSION`
6. [ ] `FR-SIM-APPLY_SWAP_FINANCING`
7. [ ] `FR-SIM-RECONCILE_TRADING_COSTS`

##### 4.5 [ ] `FEAT-SIM-MANAGE_EXITS`

1. [ ] `FR-SIM-APPLY_STOP_TARGET`
2. [ ] `FR-SIM-APPLY_DYNAMIC_EXITS`
3. [ ] `FR-SIM-RESOLVE_EXIT_COLLISIONS`
4. [ ] `FR-SIM-ENFORCE_TRADING_SCHEDULE`
5. [ ] `FR-SIM-DEFINE_RESULT_SEGMENTS`
6. [ ] `FR-SIM-ENFORCE_TRADE_RESTRICTIONS`
7. [ ] `FR-SIM-EXECUTE_ATM_STATE`
8. [ ] `FR-SIM-ALLOCATE_PARTIAL_EXITS`
9. [ ] `FR-SIM-GENERATE_ATM_SCENARIOS`

##### 4.6 [ ] `FEAT-SIM-RUN_INDICATORS`

1. [ ] `FR-SIM-ISOLATE_INDICATOR_STATE`

##### 4.7 [ ] `FEAT-SIM-COMMIT_RESULTS`

1. [ ] `FR-SIM-COMMIT_SIMULATION_RESULT`
2. [ ] `FR-SIM-CHECKPOINT_SIMULATION`
3. [ ] `FR-SIM-PRESERVE_PARTIAL_RESULTS`
4. [ ] `FR-SIM-COMPARE_EXECUTION_RESULTS`
5. [ ] `FR-SIM-STREAM_BATCH_PROGRESS`

##### 4.8 [ ] `FEAT-SIM-CACHE_EVALUATIONS`

1. [ ] `FR-SIM-CACHE_EVALUATIONS`

#### `D-ANA` — [Analytics](../../app/services/analytics/README.md)

##### 4.9 [ ] `FEAT-ANA-DATABANK_MEMBERSHIP`

1. [ ] `FR-ANA-CREATE_DATABANK`
2. [ ] `FR-ANA-LINK_STRATEGY_RESULT`
3. [ ] `FR-ANA-MODIFY_DATABANK_ITEMS`
4. [ ] `FR-ANA-VERSION_DATABANK_MUTATIONS`
5. [ ] `FR-ANA-DEFINE_MEMBERSHIP_POLICY`
6. [ ] `FR-ANA-ADMIT_DATABANK_ITEMS`

##### 4.10 [ ] `FEAT-ANA-QUERY_RESULTS`

1. [ ] `FR-ANA-QUERY_RESULTS_TABLE`
2. [ ] `FR-ANA-VERSION_SAVED_VIEWS`
3. [ ] `FR-ANA-EVALUATE_FORMULAS_SAFELY`
4. [ ] `FR-ANA-DEFINE_CORRELATION_POLICY`
5. [ ] `FR-ANA-BOUND_RESULT_QUERIES`

##### 4.11 [ ] `FEAT-ANA-INTERPRET_RESULTS`

1. [ ] `FR-ANA-APPLY_RESULT_SCOPE`
2. [ ] `FR-ANA-SHOW_RESULT_OVERVIEW`
3. [ ] `FR-ANA-LIST_RESULT_TRADES`
4. [ ] `FR-ANA-CALCULATE_METRICS`
5. [ ] `FR-ANA-CATALOG_METRICS`
6. [ ] `FR-ANA-ALIGN_RESULT_COMPARISONS`

##### 4.12 [ ] `FEAT-ANA-ANALYZE_TRADES`

1. [ ] `FR-ANA-DOWNSAMPLE_EQUITY_SERIES`
2. [ ] `FR-ANA-SHOW_RUN_MANIFEST`
3. [ ] `FR-ANA-COMPARE_BENCHMARK_EQUITY`
4. [ ] `FR-ANA-NORMALIZE_BENCHMARK`
5. [ ] `FR-ANA-ANALYZE_TRADE_TIMING`
6. [ ] `FR-ANA-RECONSTRUCT_CHART_TRADES`

##### 4.13 [ ] `FEAT-ANA-EXCHANGE_RESULTS`

1. [ ] `FR-ANA-EXPORT_RESULT_ROWS`
2. [ ] `FR-ANA-PACKAGE_RESULT_ARTIFACTS`
3. [ ] `FR-ANA-IMPORT_EXTERNAL_RESULTS`

#### `D-IFACE` — [Interfaces](../../app/services/interfaces/README.md)

##### 4.14 Partial — `FEAT-IFACE-SERVE_API_EVENTS`

1. [ ] `FR-IFACE-PAGE_INTERFACE_QUERIES`
2. [ ] `FR-IFACE-QUERY_DATABANK_RESULTS`

##### 4.15 Partial — `FEAT-IFACE-AUTOMATE_COMMANDS`

1. [ ] `FR-IFACE-PROVIDE_NONVISUAL_CHARTS`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 4.16 [ ] `FEAT-UI-AUTHOR_STRATEGIES`

1. [ ] `FR-UI-TEST_STRATEGY`

##### 4.17 Partial — `FEAT-UI-OPERATE_DATABANKS`

1. [ ] `FR-UI-QUERY_DATABANKS`
2. [ ] `FR-UI-CONFIGURE_COLUMNS`
3. [ ] `FR-UI-SELECT_DATABANK_ROWS`
4. [ ] `FR-UI-OPEN_DATABANK_RESULT`

##### 4.18 Partial — `FEAT-UI-EXPLORE_RESULTS`

1. [ ] `FR-UI-SUMMARIZE_RESULTS`
2. [ ] `FR-UI-PLOT_EQUITY`
3. [ ] `FR-UI-LIST_TRADES`
4. [ ] `FR-UI-PLOT_TRADES`
5. [ ] `FR-UI-ANALYZE_TRADES`
6. [ ] `FR-UI-EXPORT_RESULTS`

##### 4.19 Partial — `FEAT-UI-ENSURE_ACCESS`

1. [ ] `FR-UI-PROVIDE_DATA_ALTERNATIVES`

### Increment 5 — MQL5 Code Generation and Parity

**Phase alignment:** Completes the Phase 1 target-parity path

**Scope:** 21 business FRs across 5 feature slices; 2 feature completion gates and 3 partial slices.

**Purpose:** Move deterministic Codegen and MQL5 parity ahead of the research factory, as required by the Phase 1 release gate.

**Vertical path:** `Strategy version → deterministic Codegen → MetaEditor boundary → Simulator/Analytics parity → D-UI source diagnostics`

**UI demo checkpoint:** Generate an MQL5 package, inspect source and diagnostics, compile against the approved toolchain, and compare target results with the native run.

**Exit gate:** The advertised MQL5 path compiles and satisfies identity, dependency, artifact, and parity gates; unsupported targets remain unadvertised.

#### `D-STRAT` — [Strategy](../../app/services/strategy/README.md)

##### 5.1 [ ] `FEAT-STRAT-GENERATE_CODE`

1. [ ] `FR-STRAT-REGISTER_CODE_TARGETS`
2. [ ] `FR-STRAT-GENERATE_CODE_DETERMINISTICALLY`
3. [ ] `FR-STRAT-EMBED_CODE_MANIFEST`
4. [ ] `FR-STRAT-LOWER_TYPED_VALUES`
5. [ ] `FR-STRAT-DESCRIBE_EMITTER_CAPABILITIES`
6. [ ] `FR-STRAT-SHARE_TARGET_SEMANTICS`
7. [ ] `FR-STRAT-GENERATE_PSEUDOCODE`
8. [ ] `FR-STRAT-ADVERTISE_COMPATIBLE_TARGETS`

##### 5.2 [ ] `FEAT-STRAT-GENERATE_MQL5`

1. [ ] `FR-STRAT-GENERATE_MQL5_TARGET`
2. [ ] `FR-STRAT-INVOKE_METAEDITOR`
3. [ ] `FR-STRAT-PARSE_COMPILER_DIAGNOSTICS`
4. [ ] `FR-STRAT-VERIFY_MQL5_COMPILE`
5. [ ] `FR-STRAT-COMPARE_MQL5_RESULTS`
6. [ ] `FR-STRAT-STORE_CODE_ARTIFACTS`
7. [ ] `FR-STRAT-PACKAGE_TARGET_CODE`
8. [ ] `FR-STRAT-MAP_ORDER_IDENTITIES`
9. [ ] `FR-STRAT-ISOLATE_INDICATOR_FRAGMENTS`

#### `D-IFACE` — [Interfaces](../../app/services/interfaces/README.md)

##### 5.3 Partial — `FEAT-IFACE-AUTOMATE_COMMANDS`

1. [ ] `FR-IFACE-AUTOMATE_CODE_GENERATION`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 5.4 Partial — `FEAT-UI-EXPLORE_RESULTS`

1. [ ] `FR-UI-INSPECT_SOURCE`

##### 5.5 Partial — `FEAT-UI-EDIT_CODE`

1. [ ] `FR-UI-NAVIGATE_CODE`
2. [ ] `FR-UI-SEARCH_CODE`

### Increment 6 — Reproducible Research Factory

**Phase alignment:** Phase 2 release slice

**Scope:** 54 business FRs across 15 feature slices; 14 feature completion gates and 1 partial slices.

**Purpose:** Add robustness, optimization, walk-forward, Builder/evolution, acceptance, budgets, bulk databank workflows, and research UI over the trusted manual loop.

**Vertical path:** `D-UI research/databank → D-IFACE preview/bulk gateways → Research → Simulator/Analytics`

**UI demo checkpoint:** Preview and admit a bounded research run, pause/resume it, inspect progress and robustness evidence, filter results, perform pinned bulk actions, and compare accepted/rejected candidates.

**Exit gate:** Research runs are reproducible across interruption and recovery; budgets, seeds, partitions, acceptance decisions, and bulk scopes are pinned and visible.

#### `D-ANA` — [Analytics](../../app/services/analytics/README.md)

##### 6.1 [ ] `FEAT-ANA-BULK_DATABANK`

1. [ ] `FR-ANA-PIN_BULK_SELECTION`
2. [ ] `FR-ANA-TRANSFER_DATABANK_ITEMS`
3. [ ] `FR-ANA-PRESERVE_REFERENCED_ARTIFACTS`

##### 6.2 [ ] `FEAT-ANA-MATCH_RESULTS`

1. [ ] `FR-ANA-MATCH_RESULT_FINGERPRINTS`

#### `D-RES` — [Research](../../app/services/research/README.md)

##### 6.3 [ ] `FEAT-RES-RUN_RESEARCH`

1. [ ] `FR-RES-RUN_MANUAL_BACKTEST`
2. [ ] `FR-RES-PREVIEW_RESEARCH_INPUTS`
3. [ ] `FR-RES-CONTROL_RESEARCH_RUNS`
4. [ ] `FR-RES-REPORT_RESEARCH_PROGRESS`
5. [ ] `FR-RES-COMMIT_RESEARCH_RESULTS`
6. [ ] `FR-RES-DUPLICATE_RESEARCH_SETTINGS`
7. [ ] `FR-RES-CLASSIFY_RESEARCH_FAILURES`
8. [ ] `FR-RES-SUBMIT_RESEARCH_BATCHES`

##### 6.4 [ ] `FEAT-RES-TEST_ROBUSTNESS`

1. [ ] `FR-RES-PIN_RETEST_INPUTS`
2. [ ] `FR-RES-UPGRADE_RETEST_PRECISION`
3. [ ] `FR-RES-TEST_ADDITIONAL_MARKETS`
4. [ ] `FR-RES-PERTURB_TRADE_HISTORY`
5. [ ] `FR-RES-PERTURB_SIMULATION_INPUTS`
6. [ ] `FR-RES-SUMMARIZE_MONTE_CARLO`
7. [ ] `FR-RES-RUN_SCENARIO_ANALYSIS`
8. [ ] `FR-RES-PERMUTE_SYSTEM_PARAMETERS`

##### 6.5 [ ] `FEAT-RES-OPTIMIZE_PARAMETERS`

1. [ ] `FR-RES-OPTIMIZE_SEQUENTIALLY`
2. [ ] `FR-RES-OPTIMIZE_SIMPLE_PARAMETERS`
3. [ ] `FR-RES-OPTIMIZE_PARAMETER_GRID`

##### 6.6 [ ] `FEAT-RES-VALIDATE_WALK_FORWARD`

1. [ ] `FR-RES-DEFINE_WALKFORWARD_WINDOWS`
2. [ ] `FR-RES-EXECUTE_WALK_FORWARD`
3. [ ] `FR-RES-STITCH_WALKFORWARD_RESULTS`
4. [ ] `FR-RES-EVALUATE_WALKFORWARD_MATRIX`
5. [ ] `FR-RES-CALCULATE_WALKFORWARD_METRICS`

##### 6.7 [ ] `FEAT-RES-GENERATE_STRATEGIES`

1. [ ] `FR-RES-GENERATE_VALID_STRATEGIES`
2. [ ] `FR-RES-DEFINE_BUILDER_SEARCH`
3. [ ] `FR-RES-CALIBRATE_PARAMETER_RANGES`
4. [ ] `FR-RES-DETECT_STRATEGY_DUPLICATES`
5. [ ] `FR-RES-CONSTRAIN_RANDOM_GROUPS`

##### 6.8 [ ] `FEAT-RES-EVOLVE_STRATEGIES`

1. [ ] `FR-RES-IMPROVE_STRATEGY_AST`
2. [ ] `FR-RES-CONFIGURE_GENETIC_SEARCH`
3. [ ] `FR-RES-CHECKPOINT_GENETIC_SEARCH`
4. [ ] `FR-RES-MUTATE_ATM_ONLY`

##### 6.9 [ ] `FEAT-RES-ACCEPT_RESEARCH`

1. [ ] `FR-RES-DEFINE_ACCEPTANCE_PIPELINE`
2. [ ] `FR-RES-RECORD_CANDIDATE_REJECTIONS`

##### 6.10 [ ] `FEAT-RES-GOVERN_RESEARCH_BUDGETS`

1. [ ] `FR-RES-ENFORCE_RESEARCH_BUDGETS`
2. [ ] `FR-RES-PROMOTE_RESEARCH_CANDIDATES`
3. [ ] `FR-RES-DESCRIBE_RESEARCH_METHODS`
4. [ ] `FR-RES-COMPARE_RESEARCH_BATCHES`

#### `D-IFACE` — [Interfaces](../../app/services/interfaces/README.md)

##### 6.11 Partial — `FEAT-IFACE-SERVE_API_EVENTS`

1. [ ] `FR-IFACE-PIN_BULK_REQUESTS`

##### 6.12 [ ] `FEAT-IFACE-OPERATE_RESEARCH`

1. [ ] `FR-IFACE-PREVIEW_RESEARCH_RUNS`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 6.13 [ ] `FEAT-UI-RUN_RESEARCH`

1. [ ] `FR-UI-SELECT_RESEARCH_MODE`
2. [ ] `FR-UI-CONFIGURE_RESEARCH`
3. [ ] `FR-UI-PREVIEW_RESEARCH`
4. [ ] `FR-UI-CONTROL_RESEARCH`
5. [ ] `FR-UI-COMPARE_RESEARCH`
6. [ ] `FR-UI-REUSE_RESEARCH_SETTINGS`

##### 6.14 [ ] `FEAT-UI-OPERATE_DATABANKS`

1. [ ] `FR-UI-FILTER_DATABANKS`
2. [ ] `FR-UI-RUN_BULK_ACTIONS`

##### 6.15 [ ] `FEAT-UI-EXPLORE_RESULTS`

1. [ ] `FR-UI-INSPECT_ROBUSTNESS`

### Increment 7 — Portfolio and Project Workflows

**Phase alignment:** Phase 3 portfolio/project/automation slice

**Scope:** 77 business FRs across 22 feature slices; 21 feature completion gates and 1 partial slices.

**Purpose:** Compose portfolios and durable project graphs through the UI while preserving equivalent HTTP, CLI, and MCP semantics.

**Vertical path:** `D-UI portfolio/project → D-IFACE gateways → Portfolio/Orchestration → owning domain capabilities`

**UI demo checkpoint:** Build and compare a portfolio, define and validate a project graph, run/resume tasks, inspect checkpoints/history, and invoke the same workflow through an automation adapter.

**Exit gate:** Portfolio and project outputs are versioned and reproducible; retries do not duplicate effects, bounded cycles remain bounded, and UI/HTTP/CLI/MCP semantic parity passes.

#### `D-PORT` — [Portfolio](../../app/services/portfolio/README.md)

##### 7.1 [ ] `FEAT-PORT-COMPOSE_PORTFOLIOS`

1. [ ] `FR-PORT-VERSION_PORTFOLIOS`
2. [ ] `FR-PORT-VALIDATE_PORTFOLIO_ADMISSION`
3. [ ] `FR-PORT-COMPOSE_PORTFOLIOS_MANUALLY`

##### 7.2 [ ] `FEAT-PORT-ANALYZE_CORRELATION`

1. [ ] `FR-PORT-VERSION_CORRELATION_INPUTS`
2. [ ] `FR-PORT-COMPUTE_CORRELATION_MATRICES`

##### 7.3 [ ] `FEAT-PORT-SIMULATE_PORTFOLIOS`

1. [ ] `FR-PORT-SIMULATE_AGGREGATE_PORTFOLIOS`
2. [ ] `FR-PORT-CONVERT_PORTFOLIO_CURRENCIES`
3. [ ] `FR-PORT-APPLY_ALLOCATION_METHODS`
4. [ ] `FR-PORT-SCHEDULE_REBALANCING`
5. [ ] `FR-PORT-ENFORCE_EXPOSURE_LIMITS`
6. [ ] `FR-PORT-RESOLVE_SHARED_INSTRUMENTS`

##### 7.4 [ ] `FEAT-PORT-SEARCH_PORTFOLIOS`

1. [ ] `FR-PORT-DEFINE_PORTFOLIO_SEARCH`
2. [ ] `FR-PORT-REJECT_INFEASIBLE_SEARCHES`
3. [ ] `FR-PORT-OPTIMIZE_PORTFOLIO_OBJECTIVES`
4. [ ] `FR-PORT-CHECKPOINT_PORTFOLIO_SEARCH`
5. [ ] `FR-PORT-VERSION_PORTFOLIO_CHANGES`

##### 7.5 [ ] `FEAT-PORT-ANALYZE_PORTFOLIO_RISK`

1. [ ] `FR-PORT-REPORT_PORTFOLIO_RESULTS`
2. [ ] `FR-PORT-DEFINE_PORTFOLIO_METRICS`
3. [ ] `FR-PORT-EXPORT_PORTFOLIO_RESULTS`
4. [ ] `FR-PORT-CALCULATE_PORTFOLIO_RISK`

##### 7.6 [ ] `FEAT-PORT-OPTIMIZE_MARKOWITZ`

1. [ ] `FR-PORT-OPTIMIZE_MARKOWITZ_PORTFOLIOS`

##### 7.7 [ ] `FEAT-PORT-MERGE_PORTFOLIOS`

1. [ ] `FR-PORT-MERGE_PORTFOLIO_STRATEGIES`
2. [ ] `FR-PORT-SPLIT_PORTFOLIO_STRATEGIES`

#### `D-ORCH` — [Orchestration](../../app/services/orchestration/README.md)

##### 7.8 [ ] `FEAT-ORCH-DEFINE_PROJECTS`

1. [ ] `FR-ORCH-DEFINE_PROJECT_GRAPHS`
2. [ ] `FR-ORCH-DECLARE_TASK_CONTRACTS`
3. [ ] `FR-ORCH-DEFINE_TASK_TRANSITIONS`
4. [ ] `FR-ORCH-PIN_PROJECT_RUNS`

##### 7.9 [ ] `FEAT-ORCH-RUN_TASKS`

1. [ ] `FR-ORCH-DEFINE_TASK_STATES`
2. [ ] `FR-ORCH-RETRY_TASKS_IDEMPOTENTLY`
3. [ ] `FR-ORCH-FENCE_TASK_LEASES`
4. [ ] `FR-ORCH-VERSION_TASK_ATTEMPTS`
5. [ ] `FR-ORCH-VERSION_TASK_CHECKPOINTS`
6. [ ] `FR-ORCH-COMMIT_TASK_OUTPUTS`
7. [ ] `FR-ORCH-SCOPE_PROJECT_VARIABLES`
8. [ ] `FR-ORCH-REPORT_PROJECT_PROGRESS`

##### 7.10 [ ] `FEAT-ORCH-EVALUATE_CONDITIONS`

1. [ ] `FR-ORCH-TYPE_PROJECT_VARIABLES`
2. [ ] `FR-ORCH-EVALUATE_PROJECT_EXPRESSIONS`

##### 7.11 [ ] `FEAT-ORCH-RUN_DOMAIN_TASKS`

1. [ ] `FR-ORCH-DELEGATE_DOMAIN_TASKS`
2. [ ] `FR-ORCH-PIN_TASK_SELECTIONS`
3. [ ] `FR-ORCH-SYNC_PROJECT_DATA`
4. [ ] `FR-ORCH-PIN_PORTFOLIO_INPUTS`
5. [ ] `FR-ORCH-COMPILE_CONTROL_TRANSITIONS`

##### 7.12 [ ] `FEAT-ORCH-RUN_UTILITY_TASKS`

1. [ ] `FR-ORCH-RUN_APPROVED_EXECUTABLES`
2. [ ] `FR-ORCH-MANAGE_WORKSPACE_TASKS`
3. [ ] `FR-ORCH-EVALUATE_DURATION_CONDITIONS`
4. [ ] `FR-ORCH-CONFIGURE_NOTIFICATION_CHANNELS`
5. [ ] `FR-ORCH-RENDER_NOTIFICATION_TEMPLATES`
6. [ ] `FR-ORCH-MANAGE_NOTIFICATION_SESSIONS`
7. [ ] `FR-ORCH-ENFORCE_NOTIFICATION_LIMITS`
8. [ ] `FR-ORCH-DELIVER_DESKTOP_NOTIFICATIONS`
9. [ ] `FR-ORCH-DELIVER_EMAIL_NOTIFICATIONS`
10. [ ] `FR-ORCH-DELIVER_TELEGRAM_NOTIFICATIONS`
11. [ ] `FR-ORCH-DELIVER_SMS_NOTIFICATIONS`
12. [ ] `FR-ORCH-SEND_PROJECT_NOTIFICATIONS`

##### 7.13 [ ] `FEAT-ORCH-TRACK_RUN_HISTORY`

1. [ ] `FR-ORCH-RETAIN_PROJECT_HISTORY`

#### `D-IFACE` — [Interfaces](../../app/services/interfaces/README.md)

##### 7.14 [ ] `FEAT-IFACE-SERVE_API_EVENTS`

1. [ ] `FR-IFACE-SERVE_PROJECT_API`

##### 7.15 [ ] `FEAT-IFACE-AUTOMATE_COMMANDS`

1. [ ] `FR-IFACE-SUPPORT_MCP_OPERATIONS`
2. [ ] `FR-IFACE-PRESERVE_MCP_NEUTRALITY`
3. [ ] `FR-IFACE-PUBLISH_AUTOMATION_SCHEMAS`

##### 7.16 [ ] `FEAT-IFACE-EDIT_PROJECTS`

1. [ ] `FR-IFACE-VISUALIZE_PROJECT_GRAPHS`

##### 7.17 [ ] `FEAT-IFACE-OPERATE_PORTFOLIOS`

1. [ ] `FR-IFACE-OPERATE_PORTFOLIO_BUILDER`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 7.18 [ ] `FEAT-UI-START_WORK`

1. [ ] `FR-UI-RESUME_RECENT_WORK`
2. [ ] `FR-UI-LAUNCH_SHORTCUTS`

##### 7.19 [ ] `FEAT-UI-EDIT_PROJECTS`

1. [ ] `FR-UI-MANAGE_PROJECTS`
2. [ ] `FR-UI-EDIT_TASKS`
3. [ ] `FR-UI-EDIT_PROJECT_GRAPH`
4. [ ] `FR-UI-COMPARE_PROJECTS`
5. [ ] `FR-UI-CONTROL_PROJECTS`
6. [ ] `FR-UI-INSPECT_PROJECTS`

##### 7.20 [ ] `FEAT-UI-COMPOSE_PORTFOLIOS`

1. [ ] `FR-UI-SELECT_CONSTITUENTS`
2. [ ] `FR-UI-EDIT_PORTFOLIO`
3. [ ] `FR-UI-INSPECT_CORRELATION`
4. [ ] `FR-UI-RUN_PORTFOLIO`
5. [ ] `FR-UI-COMPARE_PORTFOLIOS`

##### 7.21 [ ] `FEAT-UI-MONITOR_WORK`

1. [ ] `FR-UI-CONTROL_JOBS`
2. [ ] `FR-UI-NOTIFY_OUTCOMES`

##### 7.22 Partial — `FEAT-UI-ADMINISTER_SYSTEM`

1. [ ] `FR-UI-MANAGE_UPDATES`

### Increment 8 — Extensions, Additional Targets, and Advanced Compute

**Phase alignment:** Phase 3 extensions plus independently gated Phase 4 capabilities

**Scope:** 50 business FRs across 27 feature slices; 25 feature completion gates and 2 partial slices.

**Purpose:** Add isolated plugins, view contributions, additional code targets, distributed workers, Stockpicker/profile methods, AI assistance, neural research, and other advanced capabilities without destabilizing the core loop.

**Vertical path:** `Plugin/package or advanced request → isolation/admission → owning capability → scoped UI contribution/result`

**UI demo checkpoint:** Install, replace, and remove a constrained contribution; exercise an applicable advanced capability; verify scoped UI cleanup, compatibility diagnostics, and local-reference equivalence where required.

**Exit gate:** Each advanced lane passes its own isolation/parity/removal gate; no stable workflow depends on an experimental capability, and removing an extension leaves built-in workflows usable.

#### `D-PLUG` — [Plugins](../../app/services/plugins/README.md)

##### 8.1 [ ] `FEAT-PLUG-MANAGE_LIFECYCLE`

1. [ ] `FR-PLUG-REPLACE_PLUGINS_TRANSACTIONALLY`

##### 8.2 [ ] `FEAT-PLUG-SANDBOX_PERMISSIONS`

1. [ ] `FR-PLUG-ISOLATE_PLUGIN_EXECUTION`
2. [ ] `FR-PLUG-RESTRICT_PLUGIN_SECRETS`

##### 8.3 [ ] `FEAT-PLUG-ISOLATE_ANALYSIS`

1. [ ] `FR-PLUG-PASS_ARTIFACT_HANDLES`

##### 8.4 [ ] `FEAT-PLUG-RENDER_RESULT_PANELS`

1. [ ] `FR-PLUG-SANDBOX_RESULT_PANELS`

##### 8.5 [ ] `FEAT-PLUG-MAINTAIN_COMPATIBILITY`

1. [ ] `FR-PLUG-VALIDATE_PLUGIN_PACKAGES`
2. [ ] `FR-PLUG-DECLARE_PLUGIN_COMPATIBILITY`

#### `D-STRAT` — [Strategy](../../app/services/strategy/README.md)

##### 8.6 [ ] `FEAT-STRAT-EXTEND_PLUGIN_NODES`

1. [ ] `FR-STRAT-IDENTIFY_PLUGIN_NODES`
2. [ ] `FR-STRAT-CALCULATE_VOLUME_PROFILES`

##### 8.7 [ ] `FEAT-STRAT-GENERATE_TARGETS`

1. [ ] `FR-STRAT-IMPLEMENT_CODE_TARGETS`

#### `D-ANA` — [Analytics](../../app/services/analytics/README.md)

##### 8.8 [ ] `FEAT-ANA-CUSTOM_PANELS`

1. [ ] `FR-ANA-RUN_CUSTOM_ANALYSIS`
2. [ ] `FR-ANA-DECLARE_RESULT_PANELS`

#### `D-PORT` — [Portfolio](../../app/services/portfolio/README.md)

##### 8.9 [ ] `FEAT-PORT-EXTEND_PORTFOLIO_METHODS`

1. [ ] `FR-PORT-REGISTER_PORTFOLIO_METHODS`

#### `D-WS` — [Workspace](../../app/services/workspace/README.md)

##### 8.10 [ ] `FEAT-WS-DISTRIBUTE_WORKERS`

1. [ ] `FR-WS-REGISTER_WORKER_CAPABILITIES`
2. [ ] `FR-WS-SECURE_REMOTE_WORKERS`
3. [ ] `FR-WS-SCHEDULE_DATA_LOCALITY`
4. [ ] `FR-WS-VERIFY_ARTIFACT_TRANSFER`

#### `D-DATA` — [Data](../../app/services/data/README.md)

##### 8.11 [ ] `FEAT-DATA-SYNC_CONNECTORS`

1. [ ] `FR-DATA-IMPLEMENT_CONNECTOR_LIFECYCLE`
2. [ ] `FR-DATA-PLAN_INCREMENTAL_SYNC`
3. [ ] `FR-DATA-VERSION_DATA_TRANSFORMS`
4. [ ] `FR-DATA-CONNECT_DATA_PROVIDERS`
5. [ ] `FR-DATA-PROTECT_CONNECTOR_SECRETS`

#### `D-SIM` — [Simulator](../../app/services/simulator/README.md)

##### 8.12 [ ] `FEAT-SIM-CALCULATE_PROFILES`

1. [ ] `FR-SIM-CALCULATE_VOLUME_PROFILES`

##### 8.13 [ ] `FEAT-SIM-PERTURB_INPUTS`

1. [ ] `FR-SIM-PERTURB_SIMULATION`

##### 8.14 [ ] `FEAT-SIM-DISTRIBUTE_EVALUATIONS`

1. [ ] `FR-SIM-DISTRIBUTE_SIMULATION`

##### 8.15 [ ] `FEAT-SIM-SIMULATE_STOCKPICKERS`

1. [ ] `FR-SIM-SIMULATE_STOCKPICKER`
2. [ ] `FR-SIM-DEFINE_STOCKPICKER_TIMING`
3. [ ] `FR-SIM-ENFORCE_DAILY_STOCKPICKER`

#### `D-RES` — [Research](../../app/services/research/README.md)

##### 8.16 [ ] `FEAT-RES-RESEARCH_STOCKPICKERS`

1. [ ] `FR-RES-RESEARCH_STOCKPICKER`

##### 8.17 [ ] `FEAT-RES-ASSIST_RESEARCH_AI`

1. [ ] `FR-RES-DRAFT_AI_STRATEGIES`
2. [ ] `FR-RES-GOVERN_AI_IMPROVEMENTS`
3. [ ] `FR-RES-PROTECT_AI_INPUTS`

##### 8.18 [ ] `FEAT-RES-RESEARCH_NEURAL_MODELS`

1. [ ] `FR-RES-GOVERN_NEURAL_RESEARCH`

##### 8.19 [ ] `FEAT-RES-SCORE_PORTFOLIO_FITNESS`

1. [ ] `FR-RES-SCORE_PORTFOLIO_FITNESS`

#### `D-ORCH` — [Orchestration](../../app/services/orchestration/README.md)

##### 8.20 [ ] `FEAT-ORCH-TRAIN_NETWORKS`

1. [ ] `FR-ORCH-TRAIN_NEURAL_NETWORKS`

#### `D-IFACE` — [Interfaces](../../app/services/interfaces/README.md)

##### 8.21 [ ] `FEAT-IFACE-ADMINISTER_CAPABILITIES`

1. [ ] `FR-IFACE-ADMINISTER_COMPONENTS`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 8.22 [ ] `FEAT-UI-MANAGE_LAYOUTS`

1. [ ] `FR-UI-COMPOSE_PANELS`

##### 8.23 Partial — `FEAT-UI-MANAGE_DATA`

1. [ ] `FR-UI-SYNC_DATA`

##### 8.24 [ ] `FEAT-UI-EDIT_CODE`

1. [ ] `FR-UI-EDIT_CODE_TABS`
2. [ ] `FR-UI-MANAGE_CODE_FILES`
3. [ ] `FR-UI-SHOW_CODE_DIAGNOSTICS`
4. [ ] `FR-UI-TEST_EXTENSIONS`

##### 8.25 [ ] `FEAT-UI-ADMINISTER_SYSTEM`

1. [ ] `FR-UI-SET_LANGUAGE`
2. [ ] `FR-UI-ADMINISTER_CAPABILITIES`

##### 8.26 Partial — `FEAT-UI-ENSURE_ACCESS`

1. [ ] `FR-UI-PRESERVE_USABILITY`

##### 8.27 [ ] `FEAT-UI-EXTEND_VIEWS`

1. [ ] `FR-UI-DECLARE_VIEW_CONTRIBUTIONS`
2. [ ] `FR-UI-VALIDATE_VIEW_CONTRIBUTIONS`
3. [ ] `FR-UI-SCOPE_VIEW_EFFECTS`
4. [ ] `FR-UI-REPLACE_VIEW_PROVIDERS`
5. [ ] `FR-UI-REMOVE_VIEW_CONTRIBUTIONS`

### Increment 9 — Synthetic, News, Live-Event, and Drift Evidence

**Phase alignment:** Independently gated Phase 4 evidence capabilities

**Scope:** 21 business FRs across 4 feature slices; 4 feature completion gates and 0 partial slices.

**Purpose:** Introduce nonhistorical and live evidence with explicit provenance, freshness, bounded buffering, replay, and classification.

**Vertical path:** `Source adapter → Data normalization/versioning → Research drift/intelligence → D-UI data/monitoring states`

**UI demo checkpoint:** Generate a classified scenario, query point-in-time news, reconnect/replay a live feed, and inspect drift/freshness without confusing synthetic or stale evidence with observed authority.

**Exit gate:** Synthetic, revised, live, stale, and replayed evidence remain distinguishable, bounded, lineage-complete, and incapable of silently altering historical authority.

#### `D-DATA` — [Data](../../app/services/data/README.md)

##### 9.1 [ ] `FEAT-DATA-GENERATE_SCENARIOS`

1. [ ] `FR-DATA-CONFIGURE_SYNTHETIC_MODEL`
2. [ ] `FR-DATA-GENERATE_SYNTHETIC_SERIES`
3. [ ] `FR-DATA-TRANSFORM_SCENARIO_DATA`
4. [ ] `FR-DATA-CLASSIFY_SYNTHETIC_DATA`

##### 9.2 [ ] `FEAT-DATA-TRACK_MARKET_NEWS`

1. [ ] `FR-DATA-RECORD_NEWS_OBSERVATIONS`
2. [ ] `FR-DATA-VERSION_NEWS_REVISIONS`
3. [ ] `FR-DATA-QUERY_MARKET_NEWS`
4. [ ] `FR-DATA-PROJECT_TRADE_RESTRICTIONS`
5. [ ] `FR-DATA-GOVERN_NETWORK_IMPORTS`

##### 9.3 [ ] `FEAT-DATA-STREAM_MARKET_EVENTS`

1. [ ] `FR-DATA-NORMALIZE_LIVE_EVENTS`
2. [ ] `FR-DATA-TRACK_FEED_STATE`
3. [ ] `FR-DATA-ORDER_LIVE_EVENTS`
4. [ ] `FR-DATA-BOUND_EVENT_BUFFERS`
5. [ ] `FR-DATA-RECONNECT_MARKET_FEEDS`
6. [ ] `FR-DATA-RECORD_MARKET_REPLAYS`

#### `D-RES` — [Research](../../app/services/research/README.md)

##### 9.4 [ ] `FEAT-RES-MONITOR_MARKET_DRIFT`

1. [ ] `FR-RES-CONSUME_MARKET_INTELLIGENCE`
2. [ ] `FR-RES-ANALYZE_SEASONALITY`
3. [ ] `FR-RES-ANALYZE_MARKET_STRUCTURE`
4. [ ] `FR-RES-DETECT_PERFORMANCE_DRIFT`
5. [ ] `FR-RES-CLASSIFY_DRIFT_STATE`
6. [ ] `FR-RES-RECORD_INTELLIGENCE_LINEAGE`

### Increment 10 — Governed Broker, Risk, and Trading Operations

**Phase alignment:** Optional Phase 5 governed-operations slice

**Scope:** 119 business FRs across 27 feature slices; 27 feature completion gates and 0 partial slices.

**Purpose:** Add disabled-by-default paper/demo/live operations through certified Broker transport, fail-closed Runtime Risk, Trading reconciliation, operational analytics, and safety-complete UI controls.

**Vertical path:** `D-UI confirmed intent → D-IFACE trading gateway → Trading → Runtime Risk → selected authority → reconciliation/analytics → D-UI`

**UI demo checkpoint:** Create an explicitly bound non-live session, inspect readiness, preview and confirm an action, exercise approval/kill-switch behavior, classify the receipt, reconcile authority state, and inspect the audit trail.

**Exit gate:** No adapter or UI route bypasses Risk or Trading; unknown outcomes block blind retry, kill-switch and stale-evidence cases fail closed, and live enablement remains a separate owner decision.

#### `D-BRK` — [Broker Connectivity](../../app/services/broker/README.md)

##### 10.1 [ ] `FEAT-BRK-DECLARE_CAPABILITIES`

1. [ ] `FR-BRK-IDENTIFY_PROVIDER_PROFILE`
2. [ ] `FR-BRK-DECLARE_OPERATION_CAPABILITIES`
3. [ ] `FR-BRK-RETURN_BROKER_RESULTS`
4. [ ] `FR-BRK-PAGE_PROVIDER_HISTORY`
5. [ ] `FR-BRK-HIDE_PROVIDER_INTERNALS`

##### 10.2 [ ] `FEAT-BRK-CONFIGURE_PROVIDERS`

1. [ ] `FR-BRK-OPERATE_MT5_PROFILE`
2. [ ] `FR-BRK-OPERATE_API_PROFILES`
3. [ ] `FR-BRK-ENFORCE_READ_ONLY`

##### 10.3 [ ] `FEAT-BRK-ISOLATE_ENVIRONMENTS`

1. [ ] `FR-BRK-ISOLATE_BROKER_ENVIRONMENTS`
2. [ ] `FR-BRK-SEPARATE_EXECUTION_AUTHORITIES`
3. [ ] `FR-BRK-BLOCK_BLIND_RETRIES`
4. [ ] `FR-BRK-CLOSE_ADAPTER_RESOURCES`

##### 10.4 [ ] `FEAT-BRK-MANAGE_SESSIONS`

1. [ ] `FR-BRK-DEFINE_CONNECTION_STATES`
2. [ ] `FR-BRK-ASSESS_SESSION_READINESS`
3. [ ] `FR-BRK-RESOLVE_SESSION_CREDENTIALS`
4. [ ] `FR-BRK-RECONNECT_SESSIONS`

##### 10.5 [ ] `FEAT-BRK-READ_PROVIDER_STATE`

1. [ ] `FR-BRK-READ_ACCOUNT_BALANCES`
2. [ ] `FR-BRK-READ_TRADING_STATE`
3. [ ] `FR-BRK-READ_MARKET_STATE`
4. [ ] `FR-BRK-NORMALIZE_PROVIDER_EVENTS`

##### 10.6 [ ] `FEAT-BRK-TRANSPORT_ORDERS`

1. [ ] `FR-BRK-VALIDATE_TRANSPORT_REQUEST`
2. [ ] `FR-BRK-CORRELATE_PROVIDER_OPERATIONS`
3. [ ] `FR-BRK-CLASSIFY_TRANSPORT_OUTCOME`
4. [ ] `FR-BRK-VALIDATE_ORDER_POLICIES`
5. [ ] `FR-BRK-JOURNAL_PROVIDER_WRITES`

##### 10.7 [ ] `FEAT-BRK-CERTIFY_ADAPTERS`

1. [ ] `FR-BRK-TEST_ADAPTER_CONFORMANCE`
2. [ ] `FR-BRK-CERTIFY_BROKER_WRITES`
3. [ ] `FR-BRK-VERSION_ADAPTER_CERTIFICATION`

#### `D-RISK` — [Runtime Risk](../../app/services/risk/README.md)

##### 10.8 [ ] `FEAT-RISK-DEFINE_RISK_CONTRACTS`

1. [ ] `FR-RISK-DEFINE_DECISION_STATES`
2. [ ] `FR-RISK-VERSION_RISK_PROFILES`
3. [ ] `FR-RISK-PIN_RISK_PROVENANCE`
4. [ ] `FR-RISK-VALIDATE_SOURCE_EVIDENCE`

##### 10.9 [ ] `FEAT-RISK-CALCULATE_RISK`

1. [ ] `FR-RISK-CALCULATE_RISK_SNAPSHOT`
2. [ ] `FR-RISK-INCLUDE_PENDING_EXPOSURE`
3. [ ] `FR-RISK-CALCULATE_POSITION_SIZE`
4. [ ] `FR-RISK-VALIDATE_STOP_LOSS`

##### 10.10 [ ] `FEAT-RISK-CONTROL_KILL_SWITCH`

1. [ ] `FR-RISK-DEFINE_KILL_SCOPES`
2. [ ] `FR-RISK-CHECK_KILL_SWITCH`
3. [ ] `FR-RISK-AUTHORIZE_KILL_TRANSITIONS`
4. [ ] `FR-RISK-AUDIT_KILL_TRANSITIONS`

##### 10.11 [ ] `FEAT-RISK-GOVERN_ADMISSION`

1. [ ] `FR-RISK-BIND_PROPOSED_ACTION`
2. [ ] `FR-RISK-EVALUATE_RISK_GOVERNOR`
3. [ ] `FR-RISK-RETURN_RISK_DECISION`
4. [ ] `FR-RISK-RETURN_NO_TRADE`
5. [ ] `FR-RISK-PREVENT_EXECUTION_EFFECTS`

##### 10.12 [ ] `FEAT-RISK-MANAGE_APPROVALS`

1. [ ] `FR-RISK-BIND_HUMAN_APPROVAL`
2. [ ] `FR-RISK-SIGN_APPROVAL_TOKENS`
3. [ ] `FR-RISK-CONSUME_APPROVAL_ATOMICALLY`
4. [ ] `FR-RISK-RESERVE_RISK_CAPACITY`
5. [ ] `FR-RISK-BIND_CAPACITY_RESERVATION`

##### 10.13 [ ] `FEAT-RISK-GOVERN_ALLOCATIONS`

1. [ ] `FR-RISK-ASSESS_STRATEGY_ELIGIBILITY`
2. [ ] `FR-RISK-REVIEW_PORTFOLIO_ALLOCATION`
3. [ ] `FR-RISK-AUTHORIZE_ALLOCATION_BUDGET`
4. [ ] `FR-RISK-VALIDATE_PORTFOLIO_BUDGET`

##### 10.14 [ ] `FEAT-RISK-AUDIT_RISK_DECISIONS`

1. [ ] `FR-RISK-REVALIDATE_RISK_AUTHORITY`
2. [ ] `FR-RISK-RUN_RISK_SCENARIOS`
3. [ ] `FR-RISK-REPORT_RISK_DECISIONS`
4. [ ] `FR-RISK-CHAIN_AUDIT_RECORDS`

#### `D-TRD` — [Trading](../../app/services/trading/README.md)

##### 10.15 [ ] `FEAT-TRD-MANAGE_TRADING_SESSIONS`

1. [ ] `FR-TRD-DEFINE_TRADING_MODES`
2. [ ] `FR-TRD-BIND_TRADING_SESSION`
3. [ ] `FR-TRD-DEFINE_SESSION_STATES`
4. [ ] `FR-TRD-DEFINE_LOGICAL_OPERATION`
5. [ ] `FR-TRD-DEFINE_OPERATION_STATES`

##### 10.16 [ ] `FEAT-TRD-VALIDATE_TRADE_PLANS`

1. [ ] `FR-TRD-BIND_TRADE_PLAN`
2. [ ] `FR-TRD-IDENTIFY_MANUAL_ACTIONS`
3. [ ] `FR-TRD-VALIDATE_TRADING_READINESS`
4. [ ] `FR-TRD-OBTAIN_RISK_AUTHORITY`
5. [ ] `FR-TRD-RECHECK_DISPATCH_AUTHORITY`

##### 10.17 [ ] `FEAT-TRD-ACCOUNT_OPERATIONS`

1. [ ] `FR-TRD-PROJECT_OPERATIONAL_ACCOUNTS`
2. [ ] `FR-TRD-VALUE_OPERATIONAL_ACCOUNTS`
3. [ ] `FR-TRD-RECONCILE_OPERATIONAL_LEDGER`
4. [ ] `FR-TRD-POST_ACCOUNT_ADJUSTMENTS`

##### 10.18 [ ] `FEAT-TRD-DISPATCH_ORDERS`

1. [ ] `FR-TRD-SELECT_EXECUTION_AUTHORITY`
2. [ ] `FR-TRD-NORMALIZE_TRADE_PLAN`
3. [ ] `FR-TRD-STAGE_DISPATCH_EVIDENCE`
4. [ ] `FR-TRD-DISPATCH_ONCE`
5. [ ] `FR-TRD-CLASSIFY_DISPATCH_RECEIPTS`

##### 10.19 [ ] `FEAT-TRD-RECONCILE_TRADING`

1. [ ] `FR-TRD-RECONCILE_TRADING_STATE`
2. [ ] `FR-TRD-TRUST_EXECUTION_DEALS`
3. [ ] `FR-TRD-BLOCK_BLIND_RETRY`
4. [ ] `FR-TRD-RECOVER_TRADING_SESSION`
5. [ ] `FR-TRD-RECORD_RECONCILIATION_FINDINGS`

##### 10.20 [ ] `FEAT-TRD-MANAGE_PROTECTIONS`

1. [ ] `FR-TRD-OWN_PROTECTIVE_ORDERS`
2. [ ] `FR-TRD-VALIDATE_PROTECTION_CHANGES`
3. [ ] `FR-TRD-ALLOCATE_PROTECTED_QUANTITY`
4. [ ] `FR-TRD-RECOVER_PROTECTIVE_ORDERS`

##### 10.21 [ ] `FEAT-TRD-JOURNAL_EXECUTION`

1. [ ] `FR-TRD-JOURNAL_TRADING_EVENTS`
2. [ ] `FR-TRD-PIN_EXECUTION_PROVENANCE`
3. [ ] `FR-TRD-BALANCE_TRANSACTION_LEDGER`
4. [ ] `FR-TRD-EXPORT_EXECUTION_EVIDENCE`

##### 10.22 [ ] `FEAT-TRD-EXECUTE_PUBLIC_ACTIONS`

1. [ ] `FR-TRD-ROUTE_PUBLIC_ACTIONS`
2. [ ] `FR-TRD-GOVERN_BULK_ACTIONS`
3. [ ] `FR-TRD-QUERY_TRADING_STATE`
4. [ ] `FR-TRD-ENFORCE_ACTION_PARITY`

#### `D-IFACE` — [Interfaces](../../app/services/interfaces/README.md)

##### 10.23 [ ] `FEAT-IFACE-OPERATE_TRADING`

1. [ ] `FR-IFACE-MANAGE_TRADING_SESSIONS`
2. [ ] `FR-IFACE-SHOW_TRADING_READINESS`
3. [ ] `FR-IFACE-PREVIEW_TRADING_ACTIONS`
4. [ ] `FR-IFACE-OPERATE_EMERGENCY_CONTROLS`
5. [ ] `FR-IFACE-STREAM_TRADING_EVENTS`
6. [ ] `FR-IFACE-DISPLAY_MARKET_DATA`
7. [ ] `FR-IFACE-DISPLAY_OPERATOR_ANALYTICS`
8. [ ] `FR-IFACE-ENFORCE_TRANSPORT_PARITY`

#### `D-ANA` — [Analytics](../../app/services/analytics/README.md)

##### 10.24 [ ] `FEAT-ANA-QUALIFY_OPERATIONS`

1. [ ] `FR-ANA-BUILD_OPERATIONAL_JOURNAL`
2. [ ] `FR-ANA-MEASURE_PLAN_ADHERENCE`
3. [ ] `FR-ANA-SUMMARIZE_BEHAVIOR`
4. [ ] `FR-ANA-ANALYZE_EMERGENCY_RESPONSE`
5. [ ] `FR-ANA-QUALIFY_OPERATORS`
6. [ ] `FR-ANA-EXPORT_OPERATIONAL_ANALYTICS`

#### `D-UI` — [User Interface](../../app/ui/README.md)

##### 10.25 [ ] `FEAT-UI-MANAGE_DATA`

1. [ ] `FR-UI-ADMINISTER_DATA`

##### 10.26 [ ] `FEAT-UI-OPERATE_TRADING`

1. [ ] `FR-UI-MANAGE_TRADING_SESSIONS`
2. [ ] `FR-UI-SHOW_TRADING_READINESS`
3. [ ] `FR-UI-PREVIEW_TRADING_ACTION`
4. [ ] `FR-UI-COMMIT_TRADING_ACTION`
5. [ ] `FR-UI-OPERATE_KILL_SWITCH`
6. [ ] `FR-UI-WATCH_TRADING_EVENTS`
7. [ ] `FR-UI-WATCH_MARKETS`
8. [ ] `FR-UI-INSPECT_OPERATOR_ANALYTICS`

##### 10.27 [ ] `FEAT-UI-ENSURE_ACCESS`

1. [ ] `FR-UI-OPERATE_BY_KEYBOARD`
2. [ ] `FR-UI-LABEL_CONTROLS`

### Increment 11 — Hosted Workspace Boundary and Final Release

**Phase alignment:** Hosted Phase 4 capability plus complete release matrix

**Scope:** 2 business FRs across 1 feature slices; 1 feature completion gates and 0 partial slices.

**Purpose:** Replace local-only trust assumptions with hosted isolation/authorization while retaining identical domain contracts, then run every applicable release gate.

**Vertical path:** `Hosted client → authorized workspace boundary → same public capabilities/domains → isolated storage/workers`

**UI demo checkpoint:** Run an approved representative workflow in local and hosted modes and compare contract behavior, isolation, artifacts, events, and recovery.

**Exit gate:** Cross-workspace isolation and authorization pass; all 142 feature gates, 549 business requirements, retained foundation guarantees, workflows, removal paths, and applicable phase/NFR gates are green.

#### `D-WS` — [Workspace](../../app/services/workspace/README.md)

##### 11.1 [ ] `FEAT-WS-HOST_WORKSPACES`

1. [ ] `FR-WS-ISOLATE_HOSTED_WORKSPACES`
2. [ ] `FR-WS-AUTHORIZE_HOSTED_WORKSPACES`

## 5. Final completion gate

Implementation is complete only when every Increment 0 preservation gate remains green, all 142 unique feature completion checkboxes and all 549 unique business-FR checkboxes above are complete with executable `path:line` evidence, all 33 retained shared-foundation guarantees remain passing, and:

1. Every one of the 15 domains starts or degrades independently and advertises only compatible public capabilities or UI contributions.
2. Every shared-module guarantee, domain, feature, responsibility, and FR passes its applicable cold-start, dependency-change, live-removal, reinstall, failed-activation, replacement, leak, and deletion-build checks.
3. All twelve system workflows and every applicable phase/release gate in `PROJECT.md` pass with pinned manifests and no hidden fallback.
4. Simulator and generated-target parity, deterministic replay, persistence recovery, and distributed/local equivalence fixtures pass where applicable.
5. UI workflows remain operable throughout delivery and pass applicable keyboard, focus, semantics, nonvisual-data, loading, stale, unavailable, error, contract-parity, and browser/integration evidence.
6. Broker, Runtime Risk, and Trading remain disabled by default and pass sandbox/testnet, approval, kill-switch, unknown-outcome, reconciliation, protection, ledger, and audit gates before operational release.
7. Hosted and local modes preserve the same public contracts and pass cross-workspace isolation and authorization.
8. No requirement is considered implemented solely because related code, tests, databases, migrations, or UI screens exist; its current owning acceptance contract must pass.
