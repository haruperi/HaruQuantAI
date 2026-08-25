# HaruQuantAI Domain Waterfall Implementation Order

> **Status:** UI-first, dependency-ordered domain waterfall; composability foundation already implemented
> **Architecture baseline:** `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/EXECUTION_PARITY.md`, and authoritative domain READMEs
> **Inventory:** 3 non-domain shared modules, 15 business domains, 142 planned features, 549 business FRs, and 33 retained shared-foundation trace IDs (`FR-KERN-*`)
> **Last updated:** 2026-08-25

## 1. Purpose

This document schedules implementation. It does not duplicate or weaken product behavior.

- `docs/PROJECT.md` owns system scope, cross-domain workflows, system NFRs, dependency direction, and release gates.
- `docs/ARCHITECTURE.md` owns universal structural/runtime constraints.
- `docs/EXECUTION_PARITY.md` owns the ratified one-Trading-lifecycle / multiple-execution-authorities rule where Trading, Runtime Risk, Simulator, and Broker Connectivity interact.
- Each owning package README remains the sole feature/FR registry, implementation sequence, and acceptance authority for its domain.

The previous Agile increment plan intentionally distributed broad features across multiple product increments. That model is replaced by a **domain waterfall** because HaruQuantAI is being completed domain-by-domain, with substantial StrategyQuantX-inspired reverse engineering and gap discovery performed while the owning conceptual area is still open.

The governing rule is:

> **Waterfall between domains; incremental implementation inside each domain.**

A domain is not left partially implemented merely to create an early vertical product slice. Once a domain becomes the active waterfall stage, its complete target registry is reviewed, implemented, verified, integrated with every already-available dependency, and frozen as a completed baseline before the next domain begins.

The deliberate exception is the UI-first workstation stage. D-UI is constructed early against ratified contracts and truthful mocks so the product shape is visible from the beginning; formal D-UI completion occurs as the real provider domains and Interfaces become available.

---

## 2. Why the implementation model changed

The waterfall model is chosen for this repository for four reasons:

1. **Conceptual completeness.** When reverse engineering or comparing StrategyQuantX behavior, newly discovered capabilities can be incorporated into the currently active domain instead of being deferred into unrelated future increments.
2. **Reduced architectural drift.** Domain boundaries, contracts, persistence, feature removability, and failure semantics are settled together before downstream consumers rely on them.
3. **Junior-executor safety.** The planner can freeze one complete domain specification and then issue small, concrete feature tasks without repeatedly reopening partially completed features across many increments.
4. **Execution parity.** Runtime Risk, Trading, and Simulator have a strict dependency relationship: HaruQuantAI uses one Trading-owned business execution lifecycle, while Simulator and Broker Connectivity provide route-specific execution authority mechanics. Completing these domains in dependency order avoids implementing a parallel simulation trading model.

This is not classic “integrate everything at the end” waterfall. **Integration happens after every domain.** The active domain is connected to all earlier real dependencies and the corresponding UI surfaces are de-mocked as soon as truthful provider evidence exists.

---

## 3. Scheduling hierarchy

Implementation planning uses this hierarchy:

```text
Stage
  -> Domain
      -> Feature
          -> Functional Requirement
```

- **Stage** is the cross-domain waterfall position defined by this file.
- **Domain** is one of the 15 product domains and is completed before moving to the next stage, except for the explicit UI-first horizontal exception.
- **Feature** is the removable implementation/acceptance unit defined by the owning README.
- **Functional Requirement** is the product behavior and traceability unit defined by the owning README.

Existing completed evidence is preserved. Completed `FR-*`, `FEAT-*`, whole-app contract-authoring, Composition logging, Workspace, Plugins, Interfaces, and UI-shell evidence remains authoritative where it is already recorded in the owning README, implementation, and tests.

---

## 4. Universal domain workflow

Every dedicated domain stage follows the same internal workflow.

### Phase A — Domain discovery and gap analysis

1. Read the complete authoritative README and all applicable system/architecture sections.
2. Compare the domain target against the current implementation, previous HaruQuant versions where useful, StrategyQuantX concepts where useful, and the current UI contract surface.
3. Record missing capabilities, duplicated ownership, invalid dependency assumptions, and specification gaps before coding.
4. Resolve cross-domain ownership questions in `PROJECT.md`/architecture documentation before implementation.

### Phase B — Implementation-ready specification freeze

1. Reconcile the domain purpose, owns/does-not-own boundaries, contracts, persistence, workflows, feature registry, FRs, failures, and removal behavior.
2. Reconcile shared contract schemas and generated clients where the public boundary changes.
3. Order all domain features by internal dependency.
4. Confirm every feature has a deterministic completion path and no unresolved architecture decision.

“Freeze” means **implementation-ready baseline**, not “never change again.” A later discovered defect can reopen the baseline through the normal change process, but downstream work must not silently redefine the domain.

### Phase C — Incremental feature implementation

Implement the domain feature-by-feature in the owning README's dependency order. Each feature task must include, where applicable:

- implementation steps small enough for a lower-reasoning executor;
- focused unit tests;
- feature integration and dependency-change tests;
- executable usage examples in the designated domain-logic module;
- failure, rollback, lifecycle, leak, reinstall, replacement, and physical-removal evidence;
- Ruff formatting/linting;
- strict mypy;
- affected documentation and contract generation;
- a focused Git commit with an explicit commit message.

### Phase D — Immediate integration and UI de-mock

After the domain's real capabilities exist:

1. integrate them with every already-completed upstream domain;
2. replace corresponding dev-only mock UI data/commands with real capability connections where the required provider set is now complete;
3. verify UI loading, empty, stale, unavailable, error, interaction, accessibility, temporal-context, and removal behavior;
4. run the relevant cross-domain workflow slice and contract-parity tests;
5. keep mocks only for capabilities whose actual provider is in a later waterfall stage.

A later domain is not allowed to force a completed earlier domain to remain “Partial.” If a future domain contributes evidence to an earlier receiver, the earlier domain must be completed against its own receiver-owned contract plus deterministic self-contained evidence fixtures and explicit missing-evidence behavior. The later domain then proves production integration when it can produce that evidence for real.

### Phase E — Domain completion gate

A domain may be marked **DOMAIN COMPLETE — FROZEN BASELINE** only when:

1. every domain `FEAT-*` and `FR-*` in its authoritative README is complete with executable evidence;
2. all public contracts, capability keys, configuration, migrations, persistence, and failure envelopes are implemented and version-consistent;
3. focused unit, integration, lifecycle, failure, replacement, leak, and physical-removal suites pass;
4. usage examples execute successfully;
5. applicable UI surfaces are de-mocked against all currently available real providers;
6. applicable cross-domain workflows pass against already-completed domains;
7. Ruff, formatting, strict mypy, contract generation/checks, and applicable architecture/documentation checks pass;
8. no implementation TODO remains inside the domain target registry;
9. deleting the domain/feature packages produces the documented graceful capability loss rather than unrelated application failure;
10. the complete repository gate required for the approved change boundary passes before the baseline is declared complete.

Only after this gate does the next waterfall domain begin.

---

## 5. Ratified waterfall order

| Stage | Target | Completion intent |
| ---: | --- | --- |
| 0 | Shared Foundation: Contracts -> Kernel -> Composition | Preserve implemented composability substrate and ratified whole-app contracts; no product-domain completion claim. |
| 1 | `D-UI` User Interface & Workstation Construction | Build the complete workstation surface, typed widget host, and all 17 feature-owned UI surfaces against generated contracts and dev mocks. |
| 2 | `D-WS` Workspace | Finish the complete Workspace domain and freeze it. |
| 3 | `D-PLUG` Plugins | Finish plugin lifecycle, isolation, contributions, compatibility, removal, and de-mock plugin UI views/extensions. |
| 4 | `D-CAT` Catalogue | Finish instruments, provider mappings, sessions/calendars, trading rules, universes, currencies, exchange, and de-mock instrument/session editors. |
| 5 | `D-BRK` Broker Connectivity | Finish provider profiles, environment/session isolation, reads/events, transport, certification, safe unavailable behavior, and de-mock broker admin. |
| 6 | `D-DATA` Data | Finish historical/live/external data, quality, versions, connectors, scenarios/news/events, retention, alignment, run binding, and de-mock dataset management. |
| 7 | `D-STRAT` Strategy | Finish typed strategy language, editors/templates, indicators, ATM, code generation, MQL5, targets, and de-mock strategy authoring/code workspaces. |
| 8 | `D-RISK` Runtime Risk | Finish Runtime Risk domain before Trading. Portfolio-aware paths use receiver-owned Risk contracts plus self-contained Portfolio evidence fixtures. |
| 9 | `D-TRD` Trading | Finish single canonical business execution lifecycle across SIM/PAPER/DEMO/LIVE routes, and de-mock live trading operations console & keyboard controls. |
| 10 | `D-SIM` Simulator | Finish deterministic simulation as SIM/PAPER execution authority, and de-mock backtest execution, equity curve, trade lists, and data alternatives. |
| 11 | `D-ANA` Analytics | Finish result/databank/trade/operational analytics over canonical committed execution evidence, and de-mock databank queries, filtering, and trade analysis. |
| 12 | `D-RES` Research | Finish robustness, optimization, walk-forward, Builder/evolution, acceptance, AI/neural, drift, and de-mock research factory. |
| 13 | `D-PORT` Portfolio | Finish portfolio construction/simulation/search/risk/Markowitz/merge methods, and de-mock portfolio studio. |
| 14 | `D-ORCH` Orchestration | Finish durable projects/tasks/conditions/delegation/utilities/history/training, and de-mock project automation canvas, job control, and recent work. |
| 15 | `D-IFACE` Interfaces | Finish HTTP/events/CLI/MCP/research/project/portfolio/trading/admin gateways, and de-mock capability administration. |
| 16 | Final System Integration & Complete-System Release Gate | Remove remaining mocks, run all system workflows, verify hosted/local parity, and pass final release gates across the completed product. |

The critical execution core is:

```text
Catalogue
   -> Broker Connectivity
   -> Data
   -> Strategy
   -> Runtime Risk
   -> Trading
   -> Simulator
   -> Analytics
   -> Research
   -> Portfolio
   -> Orchestration
   -> Interfaces
   -> System Integration
```

---

## 6. Ordered waterfall sequence

### Stage 0 — Shared Foundation: Contracts -> Kernel -> Composition (Preserve)

**Status:** Composability substrate preserved; the Composition logging foundation is complete for the applicable portions of `NFR-OBS-001`, `NFR-OBS-005`, and `NFR-OBS-009`. System-wide observability completion remains pending later product increments.

**Scope:** 33 retained foundation trace IDs across Kernel, Composition, Logging, and whole-app contract authoring.

**Purpose:** Freeze the proven composability substrate as the baseline for every product increment; extend it without reimplementing or bypassing it.

**Vertical path:** `Feature specification → contracts → composition → D-IFACE gateway where required → provider/consumer/state evidence`

**Exit gate:** Existing architecture, composition, feature-documentation, lifecycle, replacement, and removal suites remain green. The structured-logging task below must pass before Stage 1 product work starts.

Implemented evidence includes:

1. Independent capability, feature-specification, context/scope, registry, graph, reconciliation, event, task, state, and replacement primitives.
2. Python `haruquantai.features` discovery plus explicit test/embedded registration.
3. Strict TOML feature/provider configuration, readiness profiles, file watching, and serialized composition mutation.
4. Direct Composition runtime diagnostics for readiness, active capabilities, feature state, dependency failures, provider conflicts, replacement rollback, and memory/task leak freedom.
5. In-process SQLite schema/write-lock isolation, structured WAL connection cleanup, deterministic rollback, and migration-ledger idempotence.
6. Clean component shutdown with explicit resource/subscription disposal, thread termination, unregistration reversals, and signal handling.

#### Foundation Logging Tasks

1. [X] Add `app/composition/logging.py` for structured formatting, levels, deterministic redaction, correlation context, retention integration, bounded diagnostic capture, and lifecycle-safe handler cleanup — evidence: app/composition/logging.py:319, app/composition/logging.py:492, app/composition/logging.py:595, app/composition/logging.py:663, app/composition/logging.py:852
2. [X] Configure logging from `app/main.py` before the composition engine begins runtime work, and close owned handlers during shutdown — evidence: app/main.py:112, app/main.py:207
3. [X] Use `logger = logging.getLogger(__name__)` only in modules with workflow, lifecycle, I/O, state-transition, retry, decision, or failure boundaries; pure contracts, DTOs, deterministic helpers, trivial accessors, and high-frequency numerical modules remain log-free unless required — evidence: app/main.py:21, app/composition/discovery.py:12, app/composition/engine.py:30, app/composition/watcher.py:15
4. [X] Prove structured schema, correlation propagation, redaction, bounded capture/retention behavior, no duplicate handlers, repeated startup/shutdown cleanup, and secret-safe failure output — evidence: tests/composition/test_logging.py:43, tests/composition/test_hot_reconfiguration.py:513, tests/test_main.py:144, tests/test_main.py:164

#### Foundation task 1.0 — Whole-app contract authoring

This is non-domain runtime infrastructure, not a product `FEAT-*` or business `FR-*`. It populates the shared contract boundary before any mock-backed UI slice is built, so mocks implement ratified contracts instead of inventing shapes. Contracts are authored from the owning domain READMEs (the semantic authorities) and may be revised by later real feature slices through their documented change processes.

**Completion evidence (task 1.0):** all 15 owner READMEs now carry their ratified `Ratified v1 public records and capabilities` catalogues; the 16 namespaces under `app/contracts/` implement the inventoried records and capability bundles as strict frozen Pydantic v2 wire models (compatibility-frozen v1 process classes unchanged; additive `<Record>Wire` projections); `scripts/generate_contracts.py` deterministically emits the 16 `wire/schema.json` documents and 17 TypeScript modules (byte-reproducible, `--check` wired into `scripts/ci_check.py` and `app/ui/package.json`); the handwritten `ui_contracts.ts` mirror is deleted with all nine consumers migrated; and `tests/contracts/` (213 focused tests) proves inventory parity, round-trips, versions, generation determinism, and import boundaries. No product `FEAT-*`/`FR-*` status changed.

1. [X] Enumerate every cross-boundary contract requirement from the 15 business-domain READMEs plus the existing `app/contracts/ui/` package, and record the owner, consumers, and version for each. — evidence: `app/contracts/README.md` §§4.1–4.15 inventory reconciled 1:1 by `tests/contracts/test_contract_inventory.py::test_readme_record_counts_match_registries` (486 items, zero removals).
2. [X] Author the Python/Pydantic definitions and wire schemas into `app/contracts/<owner>/` packages for all listed contracts, including the 17 versioned UI feature capability ports and their request/result/failure/event unions. — evidence: `app/contracts/{workspace,catalogue,data,strategy,simulator,analytics,research,portfolio,orchestration,interfaces,ui,plugins,broker,risk,trading}/` plus `app/contracts/common/`; 17-UI-port surface verified by `tests/contracts/test_ui_contracts.py`; strictness/frozen verified by `tests/contracts/test_contract_inventory.py::test_registered_models_are_frozen_and_strict`.
3. [X] Regenerate the TypeScript clients and types under `app/ui/src/contracts/generated/` from the new contracts and verify the existing generation flow stays the sole source (no hand-written public wire contracts under `app/ui/`). — evidence: `scripts/generate_contracts.py` (write/`--check`); 33 artifacts byte-identical across consecutive checks per `tests/contracts/test_contract_generation.py`; `ui_contracts.ts` deleted (zero references repo-wide); `npm --prefix app/ui run typecheck`, `test`, and `build` pass against the generated barrel.
4. [X] Prove contract-roundtrip parity (schema validation, versioning, and generated-type equality) and update `app/contracts/README.md` to reflect the complete public contract inventory. — evidence: `tests/contracts/test_contract_roundtrip.py` (33 fixtures across every owner: JSON round-trip, extra field rejection, frozen mutation), `tests/contracts/test_contract_versions.py` (schema-version and key/major integrity), `tests/contracts/test_contract_boundaries.py`; `app/contracts/README.md` status header reconciled to the implemented wire-contract state.

---

### Stage 1 — User Interface (D-UI) & Workstation Construction

**Authority:** [User Interface README](../../app/ui/README.md)

**Scope:** 1 foundation task (`1.01`), 1 completed feature (`1.1`), 16 UI mock-build features (`1.2` to `1.17`, totaling 16 completable `FR-UI-*` checkboxes plus 78 mock-build lines).

**Purpose:** Deliver the complete mock-backed UI surface in one coordinated pass: a secured local workspace, capability-aware public gateway, bounded plugin/widget contribution declarations, an accessible React workstation with truthful diagnostics, and every remaining `FEAT-UI-*` feature-owned widget surface built against the dev-only mock capability provider so later backend increments integrate and verify directly from the frontend.

**Vertical path:** `Contract authoring (task 1.0) → workstation architecture foundation (task 1.01) → Launcher → Workspace → D-IFACE capability/readiness gateway → D-UI widget host/canvas → ordered feature-owned widgets on mock capability data`

**UI demo checkpoint:** Launch React, authenticate locally, create a blank workspace or apply a versioned template, add/remove/dock/tab/split/resize/minimize/maximize compatible widget instances, inspect capability/readiness and explicit time-domain state, preserve a draft/layout preference, and walk through every mock-backed feature surface with mock-derived data visibly labeled non-authoritative.

**Exit gate:** The UI starts without waiting for later domains; workspace/configuration/recovery and gateway failures are visible, keyboard focus is deterministic, every `FR-UI-*` behavior exists either as a completed checkbox with acceptance evidence or as a mock-build line with its de-mock stage recorded, mock data is visibly labeled non-authoritative, and deleting any participating feature leaves the remaining substrate healthy.

**De-mock gate:** Initial mock construction baseline — establishes all 17 feature-owned widget surfaces against `app/ui/src/mocks/`.

##### 1.01 [x] Foundation task — D-UI spatiotemporal workstation foundation

This ordered non-FR foundation enables the existing 17 D-UI feature slices; it creates no product feature or FR ID and cannot mark `FEAT-UI-MANAGE_LAYOUTS`, `FEAT-UI-EXTEND_VIEWS`, or any other feature complete by itself.

1. [x] Implement the typed widget registry/host so every widget type names exactly one owning `FEAT-UI-*`, validates manifest/configuration/state-schema metadata, reverses lifecycle effects exactly once, and derives runtime state without a second product registry. — evidence: tests/ui/unit/test_spatiotemporal_foundation.py:28, app/ui/src/runtime/__tests__/widget_registry.test.ts:6
2. [x] Pin and integrate the then-verified `dockview-react` version behind a HaruQuantAI-owned adapter; implement blank workspaces, versioned templates, add/remove/dock/tab/split/resize/minimize/maximize, bounded layout persistence, migration, dirty-close resolution, and explicit missing/incompatible-widget restoration. — evidence: tests/ui/unit/test_spatiotemporal_foundation.py:44, tests/ui/unit/test_spatiotemporal_foundation.py:84, app/ui/src/workspaces/__tests__/dockview_adapter.test.tsx:11, app/ui/src/workspaces/__tests__/layout_serializer.test.ts:11
3. [x] Implement explicit selection and temporal presentation contexts for live, delayed, historical, playback, simulation, and job-event sources with source/clock identity, timestamp, sequence/cursor order, stale/gap/resync, incompatible-domain failure, bounded coalescing, and exact subscription disposal. — evidence: tests/ui/unit/test_spatiotemporal_foundation.py:106, app/ui/src/context/__tests__/temporal.test.tsx:13, app/ui/src/context/__tests__/selection.test.tsx:9
4. [x] Establish the generated-client boundary, dev-only mock provider, accessibility/focus foundation, widget catalogue, and target `app/ui/src/widgets/<widget>/` convention without copying HaruQuantAI-V2 source or handwritten contracts. — evidence: app/ui/src/accessibility/__tests__/focus_manager.test.tsx:9, app/ui/src/mocks/__tests__/mock_provider.test.ts:7
5. [x] Prove focused component behavior plus cross-widget/workspace integration, browser Dockview interaction, layout round-trip/migration, temporal synchronization, accessibility, cold/live removal, failed replacement rollback, and listener/timer/subscription leak freedom before dependent widget slices proceed. — evidence: tests/ui/unit/test_spatiotemporal_foundation.py:165, app/ui/src/runtime/__tests__/widget_registry.test.ts:75, app/ui/src/runtime/__tests__/widget_registry.test.ts:99

##### 1.1 [x] `FEAT-UI-COMPOSE_SHELL`

1. [X] `FR-UI-ASSEMBLE_SHELL` — evidence: tests/ui/unit/test_compose_shell.py:84, app/ui/src/features/compose_shell/__tests__/compose_shell.test.tsx:24
2. [X] `FR-UI-DISCOVER_WORKSPACES` — evidence: tests/ui/unit/test_compose_shell.py:107, app/ui/src/features/compose_shell/__tests__/compose_shell.test.tsx:48
3. [X] `FR-UI-SWITCH_WORKSPACES` — evidence: tests/ui/unit/test_compose_shell.py:146, app/ui/src/features/compose_shell/__tests__/compose_shell.test.tsx:102
4. [X] `FR-UI-SHOW_CAPABILITY_STATE` — evidence: tests/ui/unit/test_compose_shell.py:163, app/ui/src/features/compose_shell/__tests__/compose_shell.test.tsx:149
5. [X] `FR-UI-RESTORE_ROUTE` — evidence: tests/ui/unit/test_compose_shell.py:246, app/ui/src/features/compose_shell/__tests__/compose_shell.test.tsx:189

##### 1.2 Partial — `FEAT-UI-START_WORK`

1. [X] `FR-UI-PRESENT_HOME` — evidence: tests/ui/unit/test_start_work.py:102, app/ui/src/widgets/home/__tests__/home.test.tsx:80
2. [X] `FR-UI-SHOW_PRODUCT_NEWS` — evidence: tests/ui/unit/test_start_work.py:138, app/ui/src/widgets/product_news/__tests__/product_news.test.tsx:70
3. `FR-UI-RESUME_RECENT_WORK` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.8)
4. `FR-UI-LAUNCH_SHORTCUTS` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.8)

##### 1.3 [ ] `FEAT-UI-MANAGE_LAYOUTS`

1. [ ] `FR-UI-PERSIST_LAYOUTS`
2. [ ] `FR-UI-RESTORE_LAYOUTS`
3. [ ] `FR-UI-SCALE_VIEWS`
4. [ ] `FR-UI-COMPOSE_PANELS`
5. [ ] `FR-UI-MANAGE_TABS`

##### 1.4 Partial — `FEAT-UI-EDIT_INPUTS`

1. [ ] `FR-UI-PRESERVE_DRAFTS`
2. `FR-UI-RENDER_FIELDS` (mock build; completes at Stage 6 Data de-mock gate — 6.15)
3. `FR-UI-VALIDATE_INPUT` (mock build; completes at Stage 6 Data de-mock gate — 6.15)
4. `FR-UI-RESOLVE_CONFLICTS` (mock build; completes at Stage 6 Data de-mock gate — 6.15)
5. `FR-UI-CONFIRM_IMPACT` (mock build; completes at Stage 6 Data de-mock gate — 6.15)

##### 1.5 Partial — `FEAT-UI-MONITOR_WORK`

1. [ ] `FR-UI-TRACK_PROGRESS`
2. [ ] `FR-UI-STREAM_ACTIVITY`
3. [ ] `FR-UI-PRESENT_FAILURES`
4. `FR-UI-CONTROL_JOBS` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.10)
5. `FR-UI-NOTIFY_OUTCOMES` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.10)

##### 1.6 Partial — `FEAT-UI-ADMINISTER_SYSTEM`

1. [ ] `FR-UI-SET_APPEARANCE`
2. [ ] `FR-UI-CONFIGURE_CLIENT`
3. [ ] `FR-UI-MANAGE_LICENSE`
4. `FR-UI-MANAGE_UPDATES` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.11)
5. `FR-UI-SET_LANGUAGE` (mock build; completes at Stage 3 Plugins de-mock gate — 3.10)
6. `FR-UI-ADMINISTER_CAPABILITIES` (mock build; completes at Stage 15 Interfaces de-mock gate — 15.8)

##### 1.7 Partial — `FEAT-UI-ENSURE_ACCESS`

1. [ ] `FR-UI-MANAGE_FOCUS`
2. [ ] `FR-UI-DISTINGUISH_STATE`
3. `FR-UI-PROVIDE_DATA_ALTERNATIVES` (mock build; completes at Stage 10 Simulator de-mock gate — 10.15)
4. `FR-UI-PRESERVE_USABILITY` (mock build; completes at Stage 3 Plugins de-mock gate — 3.11; locale-expansion acceptance requires `FR-UI-SET_LANGUAGE`)
5. `FR-UI-OPERATE_BY_KEYBOARD` (mock build; completes at Stage 9 Trading de-mock gate — 9.10)
6. `FR-UI-LABEL_CONTROLS` (mock build; completes at Stage 9 Trading de-mock gate — 9.10)

##### 1.8 Partial — `FEAT-UI-MANAGE_DATA` (mock build)

1. `FR-UI-BROWSE_DATASETS` (mock build; completes at Stage 6 Data de-mock gate — 6.16)
2. `FR-UI-IMPORT_DATA` (mock build; completes at Stage 6 Data de-mock gate — 6.16)
3. `FR-UI-EXPORT_DATA` (mock build; completes at Stage 6 Data de-mock gate — 6.16)
4. `FR-UI-EDIT_INSTRUMENTS` (mock build; completes at Stage 4 Catalogue de-mock gate — 4.8)
5. `FR-UI-EDIT_SESSIONS` (mock build; completes at Stage 4 Catalogue de-mock gate — 4.8)
6. `FR-UI-SYNC_DATA` (mock build; completes at Stage 6 Data de-mock gate — 6.16; requires `FEAT-DATA-SYNC_CONNECTORS` and Orchestration)
7. `FR-UI-ADMINISTER_DATA` (mock build; completes at Stage 5 Broker Connectivity de-mock gate — 5.8; requires Broker Connectivity)

##### 1.9 Partial — `FEAT-UI-AUTHOR_STRATEGIES` (mock build)

1. `FR-UI-EDIT_STRATEGY_TREE` (mock build; completes at Stage 7 Strategy de-mock gate — 7.14)
2. `FR-UI-BROWSE_BLOCKS` (mock build; completes at Stage 7 Strategy de-mock gate — 7.14)
3. `FR-UI-CONFIGURE_STRATEGY` (mock build; completes at Stage 7 Strategy de-mock gate — 7.14)
4. `FR-UI-VALIDATE_STRATEGY` (mock build; completes at Stage 7 Strategy de-mock gate — 7.14)
5. `FR-UI-USE_STRATEGY_EXAMPLES` (mock build; completes at Stage 7 Strategy de-mock gate — 7.14)
6. `FR-UI-TEST_STRATEGY` (mock build; completes at Stage 10 Simulator de-mock gate — 10.13; requires Simulator and Analytics)

##### 1.10 Partial — `FEAT-UI-OPERATE_DATABANKS` (mock build)

1. `FR-UI-QUERY_DATABANKS` (mock build; completes at Stage 11 Analytics de-mock gate — 11.10)
2. `FR-UI-CONFIGURE_COLUMNS` (mock build; completes at Stage 11 Analytics de-mock gate — 11.10)
3. `FR-UI-SELECT_DATABANK_ROWS` (mock build; completes at Stage 11 Analytics de-mock gate — 11.10)
4. `FR-UI-OPEN_DATABANK_RESULT` (mock build; completes at Stage 11 Analytics de-mock gate — 11.10)
5. `FR-UI-FILTER_DATABANKS` (mock build; completes at Stage 11 Analytics de-mock gate — 11.10)
6. `FR-UI-RUN_BULK_ACTIONS` (mock build; completes at Stage 11 Analytics de-mock gate — 11.10)

##### 1.11 Partial — `FEAT-UI-EXPLORE_RESULTS` (mock build)

1. `FR-UI-SUMMARIZE_RESULTS` (mock build; completes at Stage 10 Simulator de-mock gate — 10.14)
2. `FR-UI-PLOT_EQUITY` (mock build; completes at Stage 10 Simulator de-mock gate — 10.14)
3. `FR-UI-LIST_TRADES` (mock build; completes at Stage 10 Simulator de-mock gate — 10.14)
4. `FR-UI-PLOT_TRADES` (mock build; completes at Stage 10 Simulator de-mock gate — 10.14)
5. `FR-UI-ANALYZE_TRADES` (mock build; completes at Stage 11 Analytics de-mock gate — 11.11)
6. `FR-UI-EXPORT_RESULTS` (mock build; completes at Stage 11 Analytics de-mock gate — 11.11)
7. `FR-UI-INSPECT_SOURCE` (mock build; completes at Stage 7 Strategy de-mock gate — 7.16)
8. `FR-UI-INSPECT_ROBUSTNESS` (mock build; completes at Stage 12 Research de-mock gate — 12.15)

##### 1.12 Partial — `FEAT-UI-EDIT_CODE` (mock build)

1. `FR-UI-NAVIGATE_CODE` (mock build; completes at Stage 7 Strategy de-mock gate — 7.15)
2. `FR-UI-SEARCH_CODE` (mock build; completes at Stage 7 Strategy de-mock gate — 7.15)
3. `FR-UI-EDIT_CODE_TABS` (mock build; completes at Stage 3 Plugins de-mock gate — 3.9)
4. `FR-UI-MANAGE_CODE_FILES` (mock build; completes at Stage 3 Plugins de-mock gate — 3.9)
5. `FR-UI-SHOW_CODE_DIAGNOSTICS` (mock build; completes at Stage 3 Plugins de-mock gate — 3.9)
6. `FR-UI-TEST_EXTENSIONS` (mock build; completes at Stage 3 Plugins de-mock gate — 3.9)

##### 1.13 Partial — `FEAT-UI-RUN_RESEARCH` (mock build)

1. `FR-UI-SELECT_RESEARCH_MODE` (mock build; completes at Stage 12 Research de-mock gate — 12.14)
2. `FR-UI-CONFIGURE_RESEARCH` (mock build; completes at Stage 12 Research de-mock gate — 12.14)
3. `FR-UI-PREVIEW_RESEARCH` (mock build; completes at Stage 12 Research de-mock gate — 12.14)
4. `FR-UI-CONTROL_RESEARCH` (mock build; completes at Stage 12 Research de-mock gate — 12.14)
5. `FR-UI-COMPARE_RESEARCH` (mock build; completes at Stage 12 Research de-mock gate — 12.14)
6. `FR-UI-REUSE_RESEARCH_SETTINGS` (mock build; completes at Stage 12 Research de-mock gate — 12.14)

##### 1.14 Partial — `FEAT-UI-EDIT_PROJECTS` (mock build)

1. `FR-UI-MANAGE_PROJECTS` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.9)
2. `FR-UI-EDIT_TASKS` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.9)
3. `FR-UI-EDIT_PROJECT_GRAPH` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.9)
4. `FR-UI-COMPARE_PROJECTS` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.9)
5. `FR-UI-CONTROL_PROJECTS` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.9)
6. `FR-UI-INSPECT_PROJECTS` (mock build; completes at Stage 14 Orchestration de-mock gate — 14.9)

##### 1.15 Partial — `FEAT-UI-COMPOSE_PORTFOLIOS` (mock build)

1. `FR-UI-SELECT_CONSTITUENTS` (mock build; completes at Stage 13 Portfolio de-mock gate — 13.9)
2. `FR-UI-EDIT_PORTFOLIO` (mock build; completes at Stage 13 Portfolio de-mock gate — 13.9)
3. `FR-UI-INSPECT_CORRELATION` (mock build; completes at Stage 13 Portfolio de-mock gate — 13.9)
4. `FR-UI-RUN_PORTFOLIO` (mock build; completes at Stage 13 Portfolio de-mock gate — 13.9)
5. `FR-UI-COMPARE_PORTFOLIOS` (mock build; completes at Stage 13 Portfolio de-mock gate — 13.9)

##### 1.16 Partial — `FEAT-UI-OPERATE_TRADING` (mock build)

1. `FR-UI-MANAGE_TRADING_SESSIONS` (mock build; completes at Stage 9 Trading de-mock gate — 9.9)
2. `FR-UI-SHOW_TRADING_READINESS` (mock build; completes at Stage 9 Trading de-mock gate — 9.9)
3. `FR-UI-PREVIEW_TRADING_ACTION` (mock build; completes at Stage 9 Trading de-mock gate — 9.9)
4. `FR-UI-COMMIT_TRADING_ACTION` (mock build; completes at Stage 9 Trading de-mock gate — 9.9)
5. `FR-UI-OPERATE_KILL_SWITCH` (mock build; completes at Stage 9 Trading de-mock gate — 9.9)
6. `FR-UI-WATCH_TRADING_EVENTS` (mock build; completes at Stage 9 Trading de-mock gate — 9.9)
7. `FR-UI-WATCH_MARKETS` (mock build; completes at Stage 9 Trading de-mock gate — 9.9)
8. `FR-UI-INSPECT_OPERATOR_ANALYTICS` (mock build; completes at Stage 9 Trading de-mock gate — 9.9)

##### 1.17 Partial — `FEAT-UI-EXTEND_VIEWS` (mock build)

1. `FR-UI-DECLARE_VIEW_CONTRIBUTIONS` (mock build; completes at Stage 3 Plugins de-mock gate — 3.8)
2. `FR-UI-VALIDATE_VIEW_CONTRIBUTIONS` (mock build; completes at Stage 3 Plugins de-mock gate — 3.8)
3. `FR-UI-SCOPE_VIEW_EFFECTS` (mock build; completes at Stage 3 Plugins de-mock gate — 3.8)
4. `FR-UI-REPLACE_VIEW_PROVIDERS` (mock build; completes at Stage 3 Plugins de-mock gate — 3.8)
5. `FR-UI-REMOVE_VIEW_CONTRIBUTIONS` (mock build; completes at Stage 3 Plugins de-mock gate — 3.8)


---

### Stage 2 — Workspace (D-WS)

**Authority:** [Workspace README](../../app/services/workspace/README.md)


**Scope:** 18 business FRs across 6 feature slices.


**Purpose:** Manage workspace lifecycle, runtime configuration, local/hosted access, diagnostic bundles, distributed worker pools, and isolated storage/database fences.


**Vertical path:** `CLI/Launcher/UI → Workspace lifecycle/storage → SQLite WAL isolation → diagnostic capture`


**UI demo checkpoint:** Initialize, configure, backup, and restore workspaces, inspect readiness/diagnostics, and verify process isolation.


**Exit gate:** Workspace schema migrations are idempotent; multi-process writer fencing prevents database corruption; local and hosted workspace isolation pass.


**De-mock gate:** None — Workspace connects directly to shell/runtime.


##### 2.1 [x] `FEAT-WS-MANAGE_WORKSPACES`

1. [X] `FR-WS-INITIALIZE_WORKSPACE` — evidence: tests/services/workspace/workspace_lifecycle/test_workspace_lifecycle.py:53
2. [X] `FR-WS-MIGRATE_WORKSPACE_SCHEMA` — evidence: tests/services/workspace/workspace_lifecycle/test_workspace_lifecycle.py:102
3. [X] `FR-WS-FENCE_WORKSPACE_WRITERS` — evidence: tests/services/workspace/workspace_lifecycle/test_workspace_lifecycle.py:120
4. [X] `FR-WS-RECOVER_WORKSPACE_STATE` — evidence: tests/services/workspace/workspace_lifecycle/test_workspace_lifecycle.py:177
5. [X] `FR-WS-BACKUP_WORKSPACE` — evidence: tests/services/workspace/workspace_lifecycle/test_workspace_lifecycle.py:210

##### 2.2 [x] `FEAT-WS-CONFIGURE_RUNTIME`

1. [X] `FR-WS-CONFIGURE_WORKSPACE` — evidence: tests/services/workspace/runtime_configuration/test_runtime_configuration.py:64
2. [X] `FR-WS-ENFORCE_STORAGE_GUARDS` — evidence: tests/services/workspace/runtime_configuration/test_runtime_configuration.py:109
3. [X] `FR-WS-CONFIGURE_SERVER_RUNTIME` — evidence: tests/services/workspace/runtime_configuration/test_runtime_configuration.py:148
4. [X] `FR-WS-PUBLISH_RUNTIME_SUPPORT` — evidence: tests/services/workspace/runtime_configuration/test_runtime_configuration.py:214

##### 2.3 [x] `FEAT-WS-SECURE_LOCAL_ACCESS`

1. [X] `FR-WS-ISSUE_LOCAL_SESSION` — evidence: tests/services/workspace/local_access_health/test_local_access_health.py:49
2. [X] `FR-WS-REPORT_SYSTEM_READINESS` — evidence: tests/services/workspace/local_access_health/test_local_access_health.py:136

##### 2.4 [x] `FEAT-WS-BUILD_DIAGNOSTICS`

1. [X] `FR-WS-BUILD_DIAGNOSTIC_BUNDLE` — evidence: tests/services/workspace/diagnostic_bundle/test_diagnostic_bundle.py:90

##### 2.5 [ ] `FEAT-WS-DISTRIBUTE_WORKERS`

1. [ ] `FR-WS-REGISTER_WORKER_CAPABILITIES`
2. [ ] `FR-WS-SECURE_REMOTE_WORKERS`
3. [ ] `FR-WS-SCHEDULE_DATA_LOCALITY`
4. [ ] `FR-WS-VERIFY_ARTIFACT_TRANSFER`

##### 2.6 [ ] `FEAT-WS-HOST_WORKSPACES`

1. [ ] `FR-WS-ISOLATE_HOSTED_WORKSPACES`
2. [ ] `FR-WS-AUTHORIZE_HOSTED_WORKSPACES`

---

### Stage 3 — Plugins (D-PLUG)

**Authority:** [Plugins README](../../app/services/plugins/README.md)


**Scope:** 9 domain FRs across 7 feature slices plus 11 de-mock FRs across 4 UI feature slices.


**Purpose:** Manage plugin manifests, contributions, lifecycle, sandboxed execution, isolation, compatibility, and UI view extensions.


**Vertical path:** `Plugin manifest/package → sandbox runtime → contribution registry → D-UI view contributions`


**UI demo checkpoint:** Install, discover, replace, and remove an isolated plugin; verify view contributions, code tabs, and localized labels dynamically reflect state.


**Exit gate:** Sandboxed plugins cannot access unauthorized resources; live plugin replacement reverses subscriptions cleanly; removing a plugin gracefully degrades contributed UI panels without crashes.


**De-mock gate:** `FEAT-UI-EXTEND_VIEWS` (3.8: all five requirements), `FEAT-UI-EDIT_CODE` (3.9: `FR-UI-EDIT_CODE_TABS`, `FR-UI-MANAGE_CODE_FILES`, `FR-UI-SHOW_CODE_DIAGNOSTICS`, `FR-UI-TEST_EXTENSIONS`), `FEAT-UI-ADMINISTER_SYSTEM` (3.10: `FR-UI-SET_LANGUAGE`), and `FEAT-UI-ENSURE_ACCESS` (3.11: `FR-UI-PRESERVE_USABILITY`) switch from `app/ui/src/mocks/` to live Plugin capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 3.1 [x] `FEAT-PLUG-DECLARE_MANIFESTS`

1. [X] `FR-PLUG-DECLARE_PLUGIN_MANIFESTS` — evidence: tests/services/plugins/manifests/test_plugin_manifests.py:53

##### 3.2 [x] `FEAT-PLUG-REGISTER_CONTRIBUTIONS`

1. [X] `FR-PLUG-REGISTER_PLUGIN_CONTRIBUTIONS` — evidence: tests/services/plugins/contributions/test_plugin_contributions.py:34

##### 3.3 [ ] `FEAT-PLUG-MANAGE_LIFECYCLE`

1. [ ] `FR-PLUG-REPLACE_PLUGINS_TRANSACTIONALLY`

##### 3.4 [ ] `FEAT-PLUG-SANDBOX_PERMISSIONS`

1. [ ] `FR-PLUG-ISOLATE_PLUGIN_EXECUTION`
2. [ ] `FR-PLUG-RESTRICT_PLUGIN_SECRETS`

##### 3.5 [ ] `FEAT-PLUG-ISOLATE_ANALYSIS`

1. [ ] `FR-PLUG-PASS_ARTIFACT_HANDLES`

##### 3.6 [ ] `FEAT-PLUG-RENDER_RESULT_PANELS`

1. [ ] `FR-PLUG-SANDBOX_RESULT_PANELS`

##### 3.7 [ ] `FEAT-PLUG-MAINTAIN_COMPATIBILITY`

1. [ ] `FR-PLUG-VALIDATE_PLUGIN_PACKAGES`
2. [ ] `FR-PLUG-DECLARE_PLUGIN_COMPATIBILITY`

#### `D-UI` — User Interface De-mock Gates (Stage 3)


##### 3.8 [ ] `FEAT-UI-EXTEND_VIEWS`

1. [ ] `FR-UI-DECLARE_VIEW_CONTRIBUTIONS`
2. [ ] `FR-UI-VALIDATE_VIEW_CONTRIBUTIONS`
3. [ ] `FR-UI-SCOPE_VIEW_EFFECTS`
4. [ ] `FR-UI-REPLACE_VIEW_PROVIDERS`
5. [ ] `FR-UI-REMOVE_VIEW_CONTRIBUTIONS`

##### 3.9 [ ] `FEAT-UI-EDIT_CODE`

1. [ ] `FR-UI-EDIT_CODE_TABS`
2. [ ] `FR-UI-MANAGE_CODE_FILES`
3. [ ] `FR-UI-SHOW_CODE_DIAGNOSTICS`
4. [ ] `FR-UI-TEST_EXTENSIONS`

##### 3.10 [ ] `FEAT-UI-ADMINISTER_SYSTEM`

1. [ ] `FR-UI-SET_LANGUAGE`

##### 3.11 [ ] `FEAT-UI-ENSURE_ACCESS`

1. [ ] `FR-UI-PRESERVE_USABILITY`

---

### Stage 4 — Catalogue (D-CAT)

**Authority:** [Catalogue README](../../app/services/catalogue/README.md)


**Scope:** 14 domain FRs across 7 feature slices plus 2 de-mock FRs across 1 UI feature slice.


**Purpose:** Manage financial instruments, multi-provider and broker symbol mappings, trading sessions/calendars, trading rules, dynamic universes, currency conversion, and catalogue interchange.


**Vertical path:** `D-UI data/catalogue → Catalogue service → Session/Calendar engine → Universe definitions`


**UI demo checkpoint:** Define instruments, inspect provider symbol mappings, edit trading sessions and holiday calendars, create dynamic asset universes, and exchange definitions via JSON/YAML.


**Exit gate:** All instrument definitions validate against asset-class constraints; currency conversion handles cross-rates deterministically; trading sessions enforce correct market-open/close boundaries.


**De-mock gate:** `FEAT-UI-MANAGE_DATA` (4.8: `FR-UI-EDIT_INSTRUMENTS`, `FR-UI-EDIT_SESSIONS`) switches from `app/ui/src/mocks/` to live Catalogue capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 4.1 [ ] `FEAT-CAT-CATALOG_INSTRUMENTS`

1. [ ] `FR-CAT-DEFINE_INSTRUMENTS`
2. [ ] `FR-CAT-VERSION_INSTRUMENTS`
3. [ ] `FR-CAT-PROTECT_REFERENCED_VERSIONS`

##### 4.2 [ ] `FEAT-CAT-MAP_PROVIDERS`

1. [ ] `FR-CAT-MAP_BROKER_SYMBOLS`
2. [ ] `FR-CAT-MAP_PROVIDER_IDENTITIES`

##### 4.3 [ ] `FEAT-CAT-DEFINE_SESSIONS`

1. [ ] `FR-CAT-DEFINE_TRADING_SESSIONS`
2. [ ] `FR-CAT-DEFINE_MARKET_CALENDARS`
3. [ ] `FR-CAT-PREVIEW_TRADING_INTERVALS`

##### 4.4 [ ] `FEAT-CAT-DEFINE_TRADING_RULES`

1. [ ] `FR-CAT-ROUND_ORDER_VALUES`
2. [ ] `FR-CAT-RESOLVE_TRADING_COSTS`

##### 4.5 [ ] `FEAT-CAT-MANAGE_UNIVERSES`

1. [ ] `FR-CAT-VERSION_UNIVERSES`
2. [ ] `FR-CAT-TIMEBOUND_UNIVERSE_MEMBERS`

##### 4.6 [ ] `FEAT-CAT-CONVERT_CURRENCIES`

1. [ ] `FR-CAT-CONVERT_CURRENCIES`

##### 4.7 [ ] `FEAT-CAT-EXCHANGE_CATALOGUE`

1. [ ] `FR-CAT-EXCHANGE_CATALOGUE_DEFINITIONS`

#### `D-UI` — User Interface De-mock Gates (Stage 4)


##### 4.8 [ ] `FEAT-UI-MANAGE_DATA`

1. [ ] `FR-UI-EDIT_INSTRUMENTS`
2. [ ] `FR-UI-EDIT_SESSIONS`

---

### Stage 5 — Broker Connectivity (D-BRK)

**Authority:** [Broker Connectivity README](../../app/services/broker/README.md)


**Scope:** 28 domain FRs across 7 feature slices plus 1 de-mock FR across 1 UI feature slice.


**Purpose:** Manage broker profiles, environment/session isolation, read-only state/events, order transport, adapter certification suites, and safe offline behavior.


**Vertical path:** `Broker adapter → Session/Environment isolation → Read state / Order transport → Certified adapter boundary`


**UI demo checkpoint:** Configure broker connections, verify environment isolation (Demo vs Live), inspect provider readiness/health, and view adapter certification reports.


**Exit gate:** Live trading remains disabled by default; broker adapters pass the certification suite; session disconnection triggers fail-closed safety without data loss.


**De-mock gate:** `FEAT-UI-MANAGE_DATA` (5.8: `FR-UI-ADMINISTER_DATA`) switches from `app/ui/src/mocks/` to live Broker capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 5.1 [ ] `FEAT-BRK-DECLARE_CAPABILITIES`

1. [ ] `FR-BRK-IDENTIFY_PROVIDER_PROFILE`
2. [ ] `FR-BRK-DECLARE_OPERATION_CAPABILITIES`
3. [ ] `FR-BRK-RETURN_BROKER_RESULTS`
4. [ ] `FR-BRK-PAGE_PROVIDER_HISTORY`
5. [ ] `FR-BRK-HIDE_PROVIDER_INTERNALS`

##### 5.2 [ ] `FEAT-BRK-CONFIGURE_PROVIDERS`

1. [ ] `FR-BRK-OPERATE_MT5_PROFILE`
2. [ ] `FR-BRK-OPERATE_API_PROFILES`
3. [ ] `FR-BRK-ENFORCE_READ_ONLY`

##### 5.3 [ ] `FEAT-BRK-ISOLATE_ENVIRONMENTS`

1. [ ] `FR-BRK-ISOLATE_BROKER_ENVIRONMENTS`
2. [ ] `FR-BRK-SEPARATE_EXECUTION_AUTHORITIES`
3. [ ] `FR-BRK-BLOCK_BLIND_RETRIES`
4. [ ] `FR-BRK-CLOSE_ADAPTER_RESOURCES`

##### 5.4 [ ] `FEAT-BRK-MANAGE_SESSIONS`

1. [ ] `FR-BRK-DEFINE_CONNECTION_STATES`
2. [ ] `FR-BRK-ASSESS_SESSION_READINESS`
3. [ ] `FR-BRK-RESOLVE_SESSION_CREDENTIALS`
4. [ ] `FR-BRK-RECONNECT_SESSIONS`

##### 5.5 [ ] `FEAT-BRK-READ_PROVIDER_STATE`

1. [ ] `FR-BRK-READ_ACCOUNT_BALANCES`
2. [ ] `FR-BRK-READ_TRADING_STATE`
3. [ ] `FR-BRK-READ_MARKET_STATE`
4. [ ] `FR-BRK-NORMALIZE_PROVIDER_EVENTS`

##### 5.6 [ ] `FEAT-BRK-TRANSPORT_ORDERS`

1. [ ] `FR-BRK-VALIDATE_TRANSPORT_REQUEST`
2. [ ] `FR-BRK-CORRELATE_PROVIDER_OPERATIONS`
3. [ ] `FR-BRK-CLASSIFY_TRANSPORT_OUTCOME`
4. [ ] `FR-BRK-VALIDATE_ORDER_POLICIES`
5. [ ] `FR-BRK-JOURNAL_PROVIDER_WRITES`

##### 5.7 [ ] `FEAT-BRK-CERTIFY_ADAPTERS`

1. [ ] `FR-BRK-TEST_ADAPTER_CONFORMANCE`
2. [ ] `FR-BRK-CERTIFY_BROKER_WRITES`
3. [ ] `FR-BRK-VERSION_ADAPTER_CERTIFICATION`

#### `D-UI` — User Interface De-mock Gates (Stage 5)


##### 5.8 [ ] `FEAT-UI-MANAGE_DATA`

1. [ ] `FR-UI-ADMINISTER_DATA`

---

### Stage 6 — Data (D-DATA)

**Authority:** [Data README](../../app/services/data/README.md)


**Scope:** 47 domain FRs across 14 feature slices plus 8 de-mock FRs across 2 UI feature slices.


**Purpose:** Handle historical ingestion, QuantData/CSV import, tick normalization, quality resolution, bar aggregation, retention policies, series alignment, connectors, scenario generation, market news, and event streaming.


**Vertical path:** `Data source/connector → Tick normalization → Bar aggregation → Quality resolution → Pinned data cache`


**UI demo checkpoint:** Import historical data (CSV/QuantData), inspect data quality/gaps, configure timeframes and custom bars, generate market scenarios, and stream live events.


**Exit gate:** Bar aggregation matches tick precision; quality resolver flags bad ticks and gaps deterministically; historical data partitions are immutable and verifiable.


**De-mock gate:** `FEAT-UI-EDIT_INPUTS` (6.15: `FR-UI-RENDER_FIELDS`, `FR-UI-VALIDATE_INPUT`, `FR-UI-RESOLVE_CONFLICTS`, `FR-UI-CONFIRM_IMPACT`) and `FEAT-UI-MANAGE_DATA` (6.16: `FR-UI-BROWSE_DATASETS`, `FR-UI-IMPORT_DATA`, `FR-UI-EXPORT_DATA`, `FR-UI-SYNC_DATA`) switch from `app/ui/src/mocks/` to live Data capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 6.1 [ ] `FEAT-DATA-INGEST_HISTORY`

1. [ ] `FR-DATA-REGISTER_DATA_CONNECTIONS`
2. [ ] `FR-DATA-IMPORT_CSV_DATA`
3. [ ] `FR-DATA-PUBLISH_DATA_VERSIONS`
4. [ ] `FR-DATA-PIN_DATA_PROVENANCE`
5. [ ] `FR-DATA-REPORT_IMPORT_COUNTS`

##### 6.2 [ ] `FEAT-DATA-IMPORT_QUANTDATA`

1. [ ] `FR-DATA-DISCOVER_QUANTDATA_SERIES`
2. [ ] `FR-DATA-DECODE_QUANTDATA_FILES`
3. [ ] `FR-DATA-SYNC_QUANTDATA_CATALOGUE`
4. [ ] `FR-DATA-RECORD_QUANTDATA_LINEAGE`

##### 6.3 [ ] `FEAT-DATA-NORMALIZE_TICKS`

1. [ ] `FR-DATA-PRESERVE_TICK_FIELDS`

##### 6.4 [ ] `FEAT-DATA-RESOLVE_QUALITY`

1. [ ] `FR-DATA-DETECT_DATA_QUALITY`
2. [ ] `FR-DATA-RESOLVE_QUALITY_FINDINGS`
3. [ ] `FR-DATA-VALIDATE_OHLC_BARS`
4. [ ] `FR-DATA-ORDER_MARKET_ROWS`
5. [ ] `FR-DATA-LOCK_DATA_PUBLICATION`

##### 6.5 [ ] `FEAT-DATA-AGGREGATE_BARS`

1. [ ] `FR-DATA-AGGREGATE_TIMEFRAMES`
2. [ ] `FR-DATA-RECORD_AGGREGATION_LINEAGE`
3. [ ] `FR-DATA-DEFINE_CUSTOM_TIMEFRAMES`

##### 6.6 [ ] `FEAT-DATA-MANAGE_RETENTION`

1. [ ] `FR-DATA-PREVIEW_DATA_COVERAGE`
2. [ ] `FR-DATA-EXPORT_DATA_SERIES`
3. [ ] `FR-DATA-COLLECT_REACHABLE_ARTIFACTS`

##### 6.7 [ ] `FEAT-DATA-ALIGN_SERIES`

1. [ ] `FR-DATA-ALIGN_EXTERNAL_SERIES`
2. [ ] `FR-DATA-DEFINE_ALIGNMENT_POLICY`

##### 6.8 [ ] `FEAT-DATA-PREPARE_PROFILES`

1. [ ] `FR-DATA-VALIDATE_PROFILE_SOURCE`

##### 6.9 [ ] `FEAT-DATA-IMPORT_INDICATORS`

1. [ ] `FR-DATA-IMPORT_INDICATOR_VALUES`

##### 6.10 [ ] `FEAT-DATA-BIND_RUN_DATA`

1. [ ] `FR-DATA-BIND_COMMITTED_DATA`
2. [ ] `FR-DATA-VALIDATE_PRECISION_INPUTS`

##### 6.11 [ ] `FEAT-DATA-SYNC_CONNECTORS`

1. [ ] `FR-DATA-IMPLEMENT_CONNECTOR_LIFECYCLE`
2. [ ] `FR-DATA-PLAN_INCREMENTAL_SYNC`
3. [ ] `FR-DATA-VERSION_DATA_TRANSFORMS`
4. [ ] `FR-DATA-CONNECT_DATA_PROVIDERS`
5. [ ] `FR-DATA-PROTECT_CONNECTOR_SECRETS`

##### 6.12 [ ] `FEAT-DATA-GENERATE_SCENARIOS`

1. [ ] `FR-DATA-CONFIGURE_SYNTHETIC_MODEL`
2. [ ] `FR-DATA-GENERATE_SYNTHETIC_SERIES`
3. [ ] `FR-DATA-TRANSFORM_SCENARIO_DATA`
4. [ ] `FR-DATA-CLASSIFY_SYNTHETIC_DATA`

##### 6.13 [ ] `FEAT-DATA-TRACK_MARKET_NEWS`

1. [ ] `FR-DATA-RECORD_NEWS_OBSERVATIONS`
2. [ ] `FR-DATA-VERSION_NEWS_REVISIONS`
3. [ ] `FR-DATA-QUERY_MARKET_NEWS`
4. [ ] `FR-DATA-PROJECT_TRADE_RESTRICTIONS`
5. [ ] `FR-DATA-GOVERN_NETWORK_IMPORTS`

##### 6.14 [ ] `FEAT-DATA-STREAM_MARKET_EVENTS`

1. [ ] `FR-DATA-NORMALIZE_LIVE_EVENTS`
2. [ ] `FR-DATA-TRACK_FEED_STATE`
3. [ ] `FR-DATA-ORDER_LIVE_EVENTS`
4. [ ] `FR-DATA-BOUND_EVENT_BUFFERS`
5. [ ] `FR-DATA-RECONNECT_MARKET_FEEDS`
6. [ ] `FR-DATA-RECORD_MARKET_REPLAYS`

#### `D-UI` — User Interface De-mock Gates (Stage 6)


##### 6.15 [ ] `FEAT-UI-EDIT_INPUTS`

1. [ ] `FR-UI-RENDER_FIELDS`
2. [ ] `FR-UI-VALIDATE_INPUT`
3. [ ] `FR-UI-RESOLVE_CONFLICTS`
4. [ ] `FR-UI-CONFIRM_IMPACT`

##### 6.16 [ ] `FEAT-UI-MANAGE_DATA`

1. [ ] `FR-UI-BROWSE_DATASETS`
2. [ ] `FR-UI-IMPORT_DATA`
3. [ ] `FR-UI-EXPORT_DATA`
4. [ ] `FR-UI-SYNC_DATA`

---

### Stage 7 — Strategy (D-STRAT)

**Authority:** [Strategy README](../../app/services/strategy/README.md)


**Scope:** 47 domain FRs across 13 feature slices plus 8 de-mock FRs across 3 UI feature slices.


**Purpose:** Define the typed strategy AST, building block catalogue, chart configurations, strategy versioning, template editing, interchange (JSON/XML), indicator engine, ATM exit rules, and multi-target code generation (MQL5, Python, C++).


**Vertical path:** `D-UI strategy editor → Typed Strategy AST → Validator/Versioning → Deterministic Codegen (MQL5/Python/C++)`


**UI demo checkpoint:** Build and edit strategies visually via AST blocks, validate logic rules, configure indicators/ATM exits, and generate clean MQL5 / Python source code.


**Exit gate:** Strategy AST is strictly typed and validates all inputs; code generation produces deterministic, compilable MQL5 / Python code; versioning preserves strategy lineage without mutation.


**De-mock gate:** `FEAT-UI-AUTHOR_STRATEGIES` (7.14: `FR-UI-EDIT_STRATEGY_TREE`, `FR-UI-BROWSE_BLOCKS`, `FR-UI-CONFIGURE_STRATEGY`, `FR-UI-VALIDATE_STRATEGY`, `FR-UI-USE_STRATEGY_EXAMPLES`), `FEAT-UI-EDIT_CODE` (7.15: `FR-UI-NAVIGATE_CODE`, `FR-UI-SEARCH_CODE`), and `FEAT-UI-EXPLORE_RESULTS` (7.16: `FR-UI-INSPECT_SOURCE`) switch from `app/ui/src/mocks/` to live Strategy capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 7.1 [ ] `FEAT-STRAT-DEFINE_AST`

1. [ ] `FR-STRAT-REPRESENT_TYPED_AST`
2. [ ] `FR-STRAT-DEFINE_AST_NODES`
3. [ ] `FR-STRAT-DEFINE_AST_TYPES`
4. [ ] `FR-STRAT-DESCRIBE_BLOCKS`

##### 7.2 [ ] `FEAT-STRAT-CATALOG_BLOCKS`

1. [ ] `FR-STRAT-SUPPORT_STRATEGY_NODES`
2. [ ] `FR-STRAT-DEFINE_PARAMETER_DOMAINS`
3. [ ] `FR-STRAT-CATALOG_REFERENCE_BLOCKS`

##### 7.3 [ ] `FEAT-STRAT-CONFIGURE_CHARTS`

1. [ ] `FR-STRAT-CATALOG_BUILTIN_BLOCKS`
2. [ ] `FR-STRAT-CONFIGURE_TRADE_DIRECTIONS`
3. [ ] `FR-STRAT-DEFINE_SERIES_SHIFTS`

##### 7.4 [ ] `FEAT-STRAT-VERSION_STRATEGIES`

1. [ ] `FR-STRAT-VERSION_STRATEGY_DRAFTS`
2. [ ] `FR-STRAT-NORMALIZE_STRATEGY_AST`
3. [ ] `FR-STRAT-VALIDATE_STRATEGIES`

##### 7.5 [ ] `FEAT-STRAT-EDIT_TEMPLATES`

1. [ ] `FR-STRAT-DEFINE_STRATEGY_TEMPLATES`
2. [ ] `FR-STRAT-EDIT_STRATEGIES_VISUALLY`
3. [ ] `FR-STRAT-FILTER_COMPATIBLE_BLOCKS`
4. [ ] `FR-STRAT-SNAPSHOT_BACKTEST_DRAFT`
5. [ ] `FR-STRAT-DEFINE_SEARCH_PARAMETERS`
6. [ ] `FR-STRAT-CONSTRAIN_TEMPLATE_GRAMMAR`

##### 7.6 [ ] `FEAT-STRAT-EXCHANGE_STRATEGIES`

1. [ ] `FR-STRAT-EXCHANGE_NATIVE_STRATEGIES`
2. [ ] `FR-STRAT-ISOLATE_LEGACY_IMPORTS`
3. [ ] `FR-STRAT-IMPORT_LEGACY_STRATEGIES`

##### 7.7 [ ] `FEAT-STRAT-DEFINE_ARCHITECTURES`

1. [ ] `FR-STRAT-DEFINE_STRATEGY_ARCHITECTURES`
2. [ ] `FR-STRAT-DEFINE_RANDOM_GROUPS`
3. [ ] `FR-STRAT-MAP_OPPOSITE_BLOCKS`

##### 7.8 [ ] `FEAT-STRAT-DEFINE_INDICATORS`

1. [ ] `FR-STRAT-DEFINE_EXTERNAL_INDICATORS`

##### 7.9 [ ] `FEAT-STRAT-MODEL_ATM_EXITS`

1. [ ] `FR-STRAT-MODEL_ATM_EXITS`

##### 7.10 [ ] `FEAT-STRAT-GENERATE_CODE`

1. [ ] `FR-STRAT-REGISTER_CODE_TARGETS`
2. [ ] `FR-STRAT-GENERATE_CODE_DETERMINISTICALLY`
3. [ ] `FR-STRAT-EMBED_CODE_MANIFEST`
4. [ ] `FR-STRAT-LOWER_TYPED_VALUES`
5. [ ] `FR-STRAT-DESCRIBE_EMITTER_CAPABILITIES`
6. [ ] `FR-STRAT-SHARE_TARGET_SEMANTICS`
7. [ ] `FR-STRAT-GENERATE_PSEUDOCODE`
8. [ ] `FR-STRAT-ADVERTISE_COMPATIBLE_TARGETS`

##### 7.11 [ ] `FEAT-STRAT-GENERATE_MQL5`

1. [ ] `FR-STRAT-GENERATE_MQL5_TARGET`
2. [ ] `FR-STRAT-INVOKE_METAEDITOR`
3. [ ] `FR-STRAT-PARSE_COMPILER_DIAGNOSTICS`
4. [ ] `FR-STRAT-VERIFY_MQL5_COMPILE`
5. [ ] `FR-STRAT-COMPARE_MQL5_RESULTS`
6. [ ] `FR-STRAT-STORE_CODE_ARTIFACTS`
7. [ ] `FR-STRAT-PACKAGE_TARGET_CODE`
8. [ ] `FR-STRAT-MAP_ORDER_IDENTITIES`
9. [ ] `FR-STRAT-ISOLATE_INDICATOR_FRAGMENTS`

##### 7.12 [ ] `FEAT-STRAT-EXTEND_PLUGIN_NODES`

1. [ ] `FR-STRAT-IDENTIFY_PLUGIN_NODES`
2. [ ] `FR-STRAT-CALCULATE_VOLUME_PROFILES`

##### 7.13 [ ] `FEAT-STRAT-GENERATE_TARGETS`

1. [ ] `FR-STRAT-IMPLEMENT_CODE_TARGETS`

#### `D-UI` — User Interface De-mock Gates (Stage 7)


##### 7.14 [ ] `FEAT-UI-AUTHOR_STRATEGIES`

1. [ ] `FR-UI-EDIT_STRATEGY_TREE`
2. [ ] `FR-UI-BROWSE_BLOCKS`
3. [ ] `FR-UI-CONFIGURE_STRATEGY`
4. [ ] `FR-UI-VALIDATE_STRATEGY`
5. [ ] `FR-UI-USE_STRATEGY_EXAMPLES`

##### 7.15 [ ] `FEAT-UI-EDIT_CODE`

1. [ ] `FR-UI-NAVIGATE_CODE`
2. [ ] `FR-UI-SEARCH_CODE`

##### 7.16 [ ] `FEAT-UI-EXPLORE_RESULTS`

1. [ ] `FR-UI-INSPECT_SOURCE`

---

### Stage 8 — Runtime Risk (D-RISK)

**Authority:** [Runtime Risk README](../../app/services/risk/README.md)


**Scope:** 30 domain FRs across 7 feature slices.


**Purpose:** Define pre-trade and runtime risk contracts, risk calculations, deterministic kill-switch controls, order admission, human approvals, allocation governance, and cryptographically chained audit trails.


**Vertical path:** `Proposed trade action → Runtime Risk Governor → Kill-switch check → Capacity/Approval check → Admission decision`


**UI demo checkpoint:** Configure risk limits, trigger/reset kill switches, manage manual approval tokens, and inspect risk audit records.


**Exit gate:** All trade admission decisions are strictly evaluated against active limits; kill switch immediately halts new order submissions; audit logs are immutable and tamper-evident.


**De-mock gate:** None — Runtime Risk connects directly into Trading and D-IFACE gateways.


##### 8.1 [ ] `FEAT-RISK-DEFINE_RISK_CONTRACTS`

1. [ ] `FR-RISK-DEFINE_DECISION_STATES`
2. [ ] `FR-RISK-VERSION_RISK_PROFILES`
3. [ ] `FR-RISK-PIN_RISK_PROVENANCE`
4. [ ] `FR-RISK-VALIDATE_SOURCE_EVIDENCE`

##### 8.2 [ ] `FEAT-RISK-CALCULATE_RISK`

1. [ ] `FR-RISK-CALCULATE_RISK_SNAPSHOT`
2. [ ] `FR-RISK-INCLUDE_PENDING_EXPOSURE`
3. [ ] `FR-RISK-CALCULATE_POSITION_SIZE`
4. [ ] `FR-RISK-VALIDATE_STOP_LOSS`

##### 8.3 [ ] `FEAT-RISK-CONTROL_KILL_SWITCH`

1. [ ] `FR-RISK-DEFINE_KILL_SCOPES`
2. [ ] `FR-RISK-CHECK_KILL_SWITCH`
3. [ ] `FR-RISK-AUTHORIZE_KILL_TRANSITIONS`
4. [ ] `FR-RISK-AUDIT_KILL_TRANSITIONS`

##### 8.4 [ ] `FEAT-RISK-GOVERN_ADMISSION`

1. [ ] `FR-RISK-BIND_PROPOSED_ACTION`
2. [ ] `FR-RISK-EVALUATE_RISK_GOVERNOR`
3. [ ] `FR-RISK-RETURN_RISK_DECISION`
4. [ ] `FR-RISK-RETURN_NO_TRADE`
5. [ ] `FR-RISK-PREVENT_EXECUTION_EFFECTS`

##### 8.5 [ ] `FEAT-RISK-MANAGE_APPROVALS`

1. [ ] `FR-RISK-BIND_HUMAN_APPROVAL`
2. [ ] `FR-RISK-SIGN_APPROVAL_TOKENS`
3. [ ] `FR-RISK-CONSUME_APPROVAL_ATOMICALLY`
4. [ ] `FR-RISK-RESERVE_RISK_CAPACITY`
5. [ ] `FR-RISK-BIND_CAPACITY_RESERVATION`

##### 8.6 [ ] `FEAT-RISK-GOVERN_ALLOCATIONS`

1. [ ] `FR-RISK-ASSESS_STRATEGY_ELIGIBILITY`
2. [ ] `FR-RISK-REVIEW_PORTFOLIO_ALLOCATION`
3. [ ] `FR-RISK-AUTHORIZE_ALLOCATION_BUDGET`
4. [ ] `FR-RISK-VALIDATE_PORTFOLIO_BUDGET`

##### 8.7 [ ] `FEAT-RISK-AUDIT_RISK_DECISIONS`

1. [ ] `FR-RISK-REVALIDATE_RISK_AUTHORITY`
2. [ ] `FR-RISK-RUN_RISK_SCENARIOS`
3. [ ] `FR-RISK-REPORT_RISK_DECISIONS`
4. [ ] `FR-RISK-CHAIN_AUDIT_RECORDS`

---

### Stage 9 — Trading (D-TRD)

**Authority:** [Trading README](../../app/services/trading/README.md)


**Scope:** 36 domain FRs across 8 feature slices plus 10 de-mock FRs across 2 UI feature slices.


**Purpose:** Deliver the single canonical business execution lifecycle across SIM, PAPER, DEMO, and LIVE routes, trade plan validation, account operations, order dispatch, reconciliation, protective orders, and execution journaling.


**Vertical path:** `D-UI trading intent → Trading session → Risk admission → Selected execution authority → Execution journal`


**UI demo checkpoint:** Start/stop trading sessions, preview and submit trade plans, monitor orders/positions, trigger emergency protections, and inspect the transactional ledger.


**Exit gate:** Execution parity is strictly enforced across SIM, PAPER, DEMO, and LIVE; unknown broker outcomes block blind retries; transaction ledger balances to zero discrepancy.


**De-mock gate:** `FEAT-UI-OPERATE_TRADING` (9.9: all eight requirements) and `FEAT-UI-ENSURE_ACCESS` (9.10: `FR-UI-OPERATE_BY_KEYBOARD`, `FR-UI-LABEL_CONTROLS`) switch from `app/ui/src/mocks/` to live Trading capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 9.1 [ ] `FEAT-TRD-MANAGE_TRADING_SESSIONS`

1. [ ] `FR-TRD-DEFINE_TRADING_MODES`
2. [ ] `FR-TRD-BIND_TRADING_SESSION`
3. [ ] `FR-TRD-DEFINE_SESSION_STATES`
4. [ ] `FR-TRD-DEFINE_LOGICAL_OPERATION`
5. [ ] `FR-TRD-DEFINE_OPERATION_STATES`

##### 9.2 [ ] `FEAT-TRD-VALIDATE_TRADE_PLANS`

1. [ ] `FR-TRD-BIND_TRADE_PLAN`
2. [ ] `FR-TRD-IDENTIFY_MANUAL_ACTIONS`
3. [ ] `FR-TRD-VALIDATE_TRADING_READINESS`
4. [ ] `FR-TRD-OBTAIN_RISK_AUTHORITY`
5. [ ] `FR-TRD-RECHECK_DISPATCH_AUTHORITY`

##### 9.3 [ ] `FEAT-TRD-ACCOUNT_OPERATIONS`

1. [ ] `FR-TRD-PROJECT_OPERATIONAL_ACCOUNTS`
2. [ ] `FR-TRD-VALUE_OPERATIONAL_ACCOUNTS`
3. [ ] `FR-TRD-RECONCILE_OPERATIONAL_LEDGER`
4. [ ] `FR-TRD-POST_ACCOUNT_ADJUSTMENTS`

##### 9.4 [ ] `FEAT-TRD-DISPATCH_ORDERS`

1. [ ] `FR-TRD-SELECT_EXECUTION_AUTHORITY`
2. [ ] `FR-TRD-NORMALIZE_TRADE_PLAN`
3. [ ] `FR-TRD-STAGE_DISPATCH_EVIDENCE`
4. [ ] `FR-TRD-DISPATCH_ONCE`
5. [ ] `FR-TRD-CLASSIFY_DISPATCH_RECEIPTS`

##### 9.5 [ ] `FEAT-TRD-RECONCILE_TRADING`

1. [ ] `FR-TRD-RECONCILE_TRADING_STATE`
2. [ ] `FR-TRD-TRUST_EXECUTION_DEALS`
3. [ ] `FR-TRD-BLOCK_BLIND_RETRY`
4. [ ] `FR-TRD-RECOVER_TRADING_SESSION`
5. [ ] `FR-TRD-RECORD_RECONCILIATION_FINDINGS`

##### 9.6 [ ] `FEAT-TRD-MANAGE_PROTECTIONS`

1. [ ] `FR-TRD-OWN_PROTECTIVE_ORDERS`
2. [ ] `FR-TRD-VALIDATE_PROTECTION_CHANGES`
3. [ ] `FR-TRD-ALLOCATE_PROTECTED_QUANTITY`
4. [ ] `FR-TRD-RECOVER_PROTECTIVE_ORDERS`

##### 9.7 [ ] `FEAT-TRD-JOURNAL_EXECUTION`

1. [ ] `FR-TRD-JOURNAL_TRADING_EVENTS`
2. [ ] `FR-TRD-PIN_EXECUTION_PROVENANCE`
3. [ ] `FR-TRD-BALANCE_TRANSACTION_LEDGER`
4. [ ] `FR-TRD-EXPORT_EXECUTION_EVIDENCE`

##### 9.8 [ ] `FEAT-TRD-EXECUTE_PUBLIC_ACTIONS`

1. [ ] `FR-TRD-ROUTE_PUBLIC_ACTIONS`
2. [ ] `FR-TRD-GOVERN_BULK_ACTIONS`
3. [ ] `FR-TRD-QUERY_TRADING_STATE`
4. [ ] `FR-TRD-ENFORCE_ACTION_PARITY`

#### `D-UI` — User Interface De-mock Gates (Stage 9)


##### 9.9 [ ] `FEAT-UI-OPERATE_TRADING`

1. [ ] `FR-UI-MANAGE_TRADING_SESSIONS`
2. [ ] `FR-UI-SHOW_TRADING_READINESS`
3. [ ] `FR-UI-PREVIEW_TRADING_ACTION`
4. [ ] `FR-UI-COMMIT_TRADING_ACTION`
5. [ ] `FR-UI-OPERATE_KILL_SWITCH`
6. [ ] `FR-UI-WATCH_TRADING_EVENTS`
7. [ ] `FR-UI-WATCH_MARKETS`
8. [ ] `FR-UI-INSPECT_OPERATOR_ANALYTICS`

##### 9.10 [ ] `FEAT-UI-ENSURE_ACCESS`

1. [ ] `FR-UI-OPERATE_BY_KEYBOARD`
2. [ ] `FR-UI-LABEL_CONTROLS`

---

### Stage 10 — Simulator (D-SIM)

**Authority:** [Simulator README](../../app/services/simulator/README.md)


**Scope:** 45 domain FRs across 12 feature slices plus 6 de-mock FRs across 3 UI feature slices.


**Purpose:** Provide deterministic backtesting and order simulation as the SIM/PAPER execution authority, precision fill models, execution cost calculations, authority-side exit mechanics, indicators, result commit/checkpointing, evaluation caching, and stockpicker simulation.


**Vertical path:** `Strategy AST + Pinned Data → Simulation Engine → Fill models & Costs → Trading/Risk lifecycle → Committed backtest results`


**UI demo checkpoint:** Run high-speed backtests, inspect precision fill logs, examine equity curves and trade lists, and test input perturbations.


**Exit gate:** Repeated backtests on identical data yield byte-identical results; fill models accurately simulate slippage, spread, and commissions; evaluations are cached idempotently.


**De-mock gate:** `FEAT-UI-AUTHOR_STRATEGIES` (10.13: `FR-UI-TEST_STRATEGY`), `FEAT-UI-EXPLORE_RESULTS` (10.14: `FR-UI-SUMMARIZE_RESULTS`, `FR-UI-PLOT_EQUITY`, `FR-UI-LIST_TRADES`, `FR-UI-PLOT_TRADES`), and `FEAT-UI-ENSURE_ACCESS` (10.15: `FR-UI-PROVIDE_DATA_ALTERNATIVES`) switch from `app/ui/src/mocks/` to live Simulator capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 10.1 [ ] `FEAT-SIM-CONFIGURE_ENGINE`

1. [ ] `FR-SIM-BUILD_RUN_MANIFEST`
2. [ ] `FR-SIM-PIN_RUN_INPUTS`
3. [ ] `FR-SIM-PROCESS_EVENT_STREAM`
4. [ ] `FR-SIM-ENFORCE_CLOSED_INPUTS`
5. [ ] `FR-SIM-DEFINE_ENGINE_SEMANTICS`
6. [ ] `FR-SIM-VERSION_ENGINE_PROFILES`

##### 10.2 [ ] `FEAT-SIM-MODEL_PRECISION`

1. [ ] `FR-SIM-MODEL_INTRABAR_PATH`
2. [ ] `FR-SIM-SIMULATE_FROM_M1`
3. [ ] `FR-SIM-APPLY_CUSTOM_SPREAD`
4. [ ] `FR-SIM-APPLY_RECORDED_SPREAD`

##### 10.3 [ ] `FEAT-SIM-SIMULATE_ORDERS`

1. [ ] `FR-SIM-JOURNAL_SIMULATION_EVENTS`
2. [ ] `FR-SIM-VALIDATE_MARKET_ORDERS`
3. [ ] `FR-SIM-PROCESS_PENDING_ORDERS`
4. [ ] `FR-SIM-PROCESS_STOP_LIMITS`
5. [ ] `FR-SIM-MODEL_POSITION_ACCOUNTING`
6. [ ] `FR-SIM-TRACK_ENTRY_IDENTITIES`

##### 10.4 [ ] `FEAT-SIM-CALCULATE_COSTS`

1. [ ] `FR-SIM-CALCULATE_POSITION_SIZE`
2. [ ] `FR-SIM-REJECT_INVALID_SIZE`
3. [ ] `FR-SIM-APPLY_SPREAD`
4. [ ] `FR-SIM-APPLY_SLIPPAGE`
5. [ ] `FR-SIM-APPLY_COMMISSION`
6. [ ] `FR-SIM-APPLY_SWAP_FINANCING`
7. [ ] `FR-SIM-RECONCILE_TRADING_COSTS`

##### 10.5 [ ] `FEAT-SIM-MANAGE_EXITS`

1. [ ] `FR-SIM-APPLY_STOP_TARGET`
2. [ ] `FR-SIM-APPLY_DYNAMIC_EXITS`
3. [ ] `FR-SIM-RESOLVE_EXIT_COLLISIONS`
4. [ ] `FR-SIM-ENFORCE_TRADING_SCHEDULE`
5. [ ] `FR-SIM-DEFINE_RESULT_SEGMENTS`
6. [ ] `FR-SIM-ENFORCE_TRADE_RESTRICTIONS`
7. [ ] `FR-SIM-EXECUTE_ATM_STATE`
8. [ ] `FR-SIM-ALLOCATE_PARTIAL_EXITS`
9. [ ] `FR-SIM-GENERATE_ATM_SCENARIOS`

##### 10.6 [ ] `FEAT-SIM-RUN_INDICATORS`

1. [ ] `FR-SIM-ISOLATE_INDICATOR_STATE`

##### 10.7 [ ] `FEAT-SIM-COMMIT_RESULTS`

1. [ ] `FR-SIM-COMMIT_SIMULATION_RESULT`
2. [ ] `FR-SIM-CHECKPOINT_SIMULATION`
3. [ ] `FR-SIM-PRESERVE_PARTIAL_RESULTS`
4. [ ] `FR-SIM-COMPARE_EXECUTION_RESULTS`
5. [ ] `FR-SIM-STREAM_BATCH_PROGRESS`

##### 10.8 [ ] `FEAT-SIM-CACHE_EVALUATIONS`

1. [ ] `FR-SIM-CACHE_EVALUATIONS`

##### 10.9 [ ] `FEAT-SIM-CALCULATE_PROFILES`

1. [ ] `FR-SIM-CALCULATE_VOLUME_PROFILES`

##### 10.10 [ ] `FEAT-SIM-PERTURB_INPUTS`

1. [ ] `FR-SIM-PERTURB_SIMULATION`

##### 10.11 [ ] `FEAT-SIM-DISTRIBUTE_EVALUATIONS`

1. [ ] `FR-SIM-DISTRIBUTE_SIMULATION`

##### 10.12 [ ] `FEAT-SIM-SIMULATE_STOCKPICKERS`

1. [ ] `FR-SIM-SIMULATE_STOCKPICKER`
2. [ ] `FR-SIM-DEFINE_STOCKPICKER_TIMING`
3. [ ] `FR-SIM-ENFORCE_DAILY_STOCKPICKER`

#### `D-UI` — User Interface De-mock Gates (Stage 10)


##### 10.13 [ ] `FEAT-UI-AUTHOR_STRATEGIES`

1. [ ] `FR-UI-TEST_STRATEGY`

##### 10.14 [ ] `FEAT-UI-EXPLORE_RESULTS`

1. [ ] `FR-UI-SUMMARIZE_RESULTS`
2. [ ] `FR-UI-PLOT_EQUITY`
3. [ ] `FR-UI-LIST_TRADES`
4. [ ] `FR-UI-PLOT_TRADES`

##### 10.15 [ ] `FEAT-UI-ENSURE_ACCESS`

1. [ ] `FR-UI-PROVIDE_DATA_ALTERNATIVES`

---

### Stage 11 — Analytics (D-ANA)

**Authority:** [Analytics README](../../app/services/analytics/README.md)


**Scope:** 38 domain FRs across 9 feature slices plus 8 de-mock FRs across 2 UI feature slices.


**Purpose:** Manage databank membership, result queries/views, result interpretation and comparisons, trade and benchmark analysis, result interchange, bulk databank operations, similarity matching, custom panels, and operational journals.


**Vertical path:** `Committed backtest/live results → Analytics engine → Databank storage → Query/Filter/View API → D-UI explorer`


**UI demo checkpoint:** Query and filter databanks, compare strategy results side-by-side, analyze trade distributions and drawdown profiles, and export databank packages.


**Exit gate:** Databank filters and column calculations are deterministic; result comparisons accurately calculate correlations and statistical metrics; bulk actions are atomic.


**De-mock gate:** `FEAT-UI-OPERATE_DATABANKS` (11.10: all six requirements) and `FEAT-UI-EXPLORE_RESULTS` (11.11: `FR-UI-ANALYZE_TRADES`, `FR-UI-EXPORT_RESULTS`) switch from `app/ui/src/mocks/` to live Analytics capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 11.1 [ ] `FEAT-ANA-DATABANK_MEMBERSHIP`

1. [ ] `FR-ANA-CREATE_DATABANK`
2. [ ] `FR-ANA-LINK_STRATEGY_RESULT`
3. [ ] `FR-ANA-MODIFY_DATABANK_ITEMS`
4. [ ] `FR-ANA-VERSION_DATABANK_MUTATIONS`
5. [ ] `FR-ANA-DEFINE_MEMBERSHIP_POLICY`
6. [ ] `FR-ANA-ADMIT_DATABANK_ITEMS`

##### 11.2 [ ] `FEAT-ANA-QUERY_RESULTS`

1. [ ] `FR-ANA-QUERY_RESULTS_TABLE`
2. [ ] `FR-ANA-VERSION_SAVED_VIEWS`
3. [ ] `FR-ANA-EVALUATE_FORMULAS_SAFELY`
4. [ ] `FR-ANA-DEFINE_CORRELATION_POLICY`
5. [ ] `FR-ANA-BOUND_RESULT_QUERIES`

##### 11.3 [ ] `FEAT-ANA-INTERPRET_RESULTS`

1. [ ] `FR-ANA-APPLY_RESULT_SCOPE`
2. [ ] `FR-ANA-SHOW_RESULT_OVERVIEW`
3. [ ] `FR-ANA-LIST_RESULT_TRADES`
4. [ ] `FR-ANA-CALCULATE_METRICS`
5. [ ] `FR-ANA-CATALOG_METRICS`
6. [ ] `FR-ANA-ALIGN_RESULT_COMPARISONS`

##### 11.4 [ ] `FEAT-ANA-ANALYZE_TRADES`

1. [ ] `FR-ANA-DOWNSAMPLE_EQUITY_SERIES`
2. [ ] `FR-ANA-SHOW_RUN_MANIFEST`
3. [ ] `FR-ANA-COMPARE_BENCHMARK_EQUITY`
4. [ ] `FR-ANA-NORMALIZE_BENCHMARK`
5. [ ] `FR-ANA-ANALYZE_TRADE_TIMING`
6. [ ] `FR-ANA-RECONSTRUCT_CHART_TRADES`

##### 11.5 [ ] `FEAT-ANA-EXCHANGE_RESULTS`

1. [ ] `FR-ANA-EXPORT_RESULT_ROWS`
2. [ ] `FR-ANA-PACKAGE_RESULT_ARTIFACTS`
3. [ ] `FR-ANA-IMPORT_EXTERNAL_RESULTS`

##### 11.6 [ ] `FEAT-ANA-BULK_DATABANK`

1. [ ] `FR-ANA-PIN_BULK_SELECTION`
2. [ ] `FR-ANA-TRANSFER_DATABANK_ITEMS`
3. [ ] `FR-ANA-PRESERVE_REFERENCED_ARTIFACTS`

##### 11.7 [ ] `FEAT-ANA-MATCH_RESULTS`

1. [ ] `FR-ANA-MATCH_RESULT_FINGERPRINTS`

##### 11.8 [ ] `FEAT-ANA-CUSTOM_PANELS`

1. [ ] `FR-ANA-RUN_CUSTOM_ANALYSIS`
2. [ ] `FR-ANA-DECLARE_RESULT_PANELS`

##### 11.9 [ ] `FEAT-ANA-QUALIFY_OPERATIONS`

1. [ ] `FR-ANA-BUILD_OPERATIONAL_JOURNAL`
2. [ ] `FR-ANA-MEASURE_PLAN_ADHERENCE`
3. [ ] `FR-ANA-SUMMARIZE_BEHAVIOR`
4. [ ] `FR-ANA-ANALYZE_EMERGENCY_RESPONSE`
5. [ ] `FR-ANA-QUALIFY_OPERATORS`
6. [ ] `FR-ANA-EXPORT_OPERATIONAL_ANALYTICS`

#### `D-UI` — User Interface De-mock Gates (Stage 11)


##### 11.10 [ ] `FEAT-UI-OPERATE_DATABANKS`

1. [ ] `FR-UI-QUERY_DATABANKS`
2. [ ] `FR-UI-CONFIGURE_COLUMNS`
3. [ ] `FR-UI-SELECT_DATABANK_ROWS`
4. [ ] `FR-UI-OPEN_DATABANK_RESULT`
5. [ ] `FR-UI-FILTER_DATABANKS`
6. [ ] `FR-UI-RUN_BULK_ACTIONS`

##### 11.11 [ ] `FEAT-UI-EXPLORE_RESULTS`

1. [ ] `FR-UI-ANALYZE_TRADES`
2. [ ] `FR-UI-EXPORT_RESULTS`

---

### Stage 12 — Research (D-RES)

**Authority:** [Research README](../../app/services/research/README.md)


**Scope:** 51 domain FRs across 13 feature slices plus 7 de-mock FRs across 2 UI feature slices.


**Purpose:** Power strategy generation (Builder), evolutionary improvement, parameter optimization, robustness testing (Monte Carlo, multi-market, slippage), walk-forward matrix validation, acceptance criteria, budget governance, stockpicker research, AI/neural models, portfolio fitness, and market drift detection.


**Vertical path:** `Research configuration & budget → Generation/Optimization engine → Parallel Simulator tasks → Acceptance filter → Databank commit`


**UI demo checkpoint:** Launch Builder/evolutionary strategy search, run Monte Carlo and Walk-Forward tests, monitor research resource budgets, and inspect market drift alerts.


**Exit gate:** Strategy generation and optimization runs are reproducible from seeds; budget governance enforces hard CPU/memory limits; robustness test metrics match mathematical definitions.


**De-mock gate:** `FEAT-UI-RUN_RESEARCH` (12.14: all six requirements) and `FEAT-UI-EXPLORE_RESULTS` (12.15: `FR-UI-INSPECT_ROBUSTNESS`) switch from `app/ui/src/mocks/` to live Research capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 12.1 [ ] `FEAT-RES-RUN_RESEARCH`

1. [ ] `FR-RES-RUN_MANUAL_BACKTEST`
2. [ ] `FR-RES-PREVIEW_RESEARCH_INPUTS`
3. [ ] `FR-RES-CONTROL_RESEARCH_RUNS`
4. [ ] `FR-RES-REPORT_RESEARCH_PROGRESS`
5. [ ] `FR-RES-COMMIT_RESEARCH_RESULTS`
6. [ ] `FR-RES-DUPLICATE_RESEARCH_SETTINGS`
7. [ ] `FR-RES-CLASSIFY_RESEARCH_FAILURES`
8. [ ] `FR-RES-SUBMIT_RESEARCH_BATCHES`

##### 12.2 [ ] `FEAT-RES-TEST_ROBUSTNESS`

1. [ ] `FR-RES-PIN_RETEST_INPUTS`
2. [ ] `FR-RES-UPGRADE_RETEST_PRECISION`
3. [ ] `FR-RES-TEST_ADDITIONAL_MARKETS`
4. [ ] `FR-RES-PERTURB_TRADE_HISTORY`
5. [ ] `FR-RES-PERTURB_SIMULATION_INPUTS`
6. [ ] `FR-RES-SUMMARIZE_MONTE_CARLO`
7. [ ] `FR-RES-RUN_SCENARIO_ANALYSIS`
8. [ ] `FR-RES-PERMUTE_SYSTEM_PARAMETERS`

##### 12.3 [ ] `FEAT-RES-OPTIMIZE_PARAMETERS`

1. [ ] `FR-RES-OPTIMIZE_SEQUENTIALLY`
2. [ ] `FR-RES-OPTIMIZE_SIMPLE_PARAMETERS`
3. [ ] `FR-RES-OPTIMIZE_PARAMETER_GRID`

##### 12.4 [ ] `FEAT-RES-VALIDATE_WALK_FORWARD`

1. [ ] `FR-RES-DEFINE_WALKFORWARD_WINDOWS`
2. [ ] `FR-RES-EXECUTE_WALK_FORWARD`
3. [ ] `FR-RES-STITCH_WALKFORWARD_RESULTS`
4. [ ] `FR-RES-EVALUATE_WALKFORWARD_MATRIX`
5. [ ] `FR-RES-CALCULATE_WALKFORWARD_METRICS`

##### 12.5 [ ] `FEAT-RES-GENERATE_STRATEGIES`

1. [ ] `FR-RES-GENERATE_VALID_STRATEGIES`
2. [ ] `FR-RES-DEFINE_BUILDER_SEARCH`
3. [ ] `FR-RES-CALIBRATE_PARAMETER_RANGES`
4. [ ] `FR-RES-DETECT_STRATEGY_DUPLICATES`
5. [ ] `FR-RES-CONSTRAIN_RANDOM_GROUPS`

##### 12.6 [ ] `FEAT-RES-EVOLVE_STRATEGIES`

1. [ ] `FR-RES-IMPROVE_STRATEGY_AST`
2. [ ] `FR-RES-CONFIGURE_GENETIC_SEARCH`
3. [ ] `FR-RES-CHECKPOINT_GENETIC_SEARCH`
4. [ ] `FR-RES-MUTATE_ATM_ONLY`

##### 12.7 [ ] `FEAT-RES-ACCEPT_RESEARCH`

1. [ ] `FR-RES-DEFINE_ACCEPTANCE_PIPELINE`
2. [ ] `FR-RES-RECORD_CANDIDATE_REJECTIONS`

##### 12.8 [ ] `FEAT-RES-GOVERN_RESEARCH_BUDGETS`

1. [ ] `FR-RES-ENFORCE_RESEARCH_BUDGETS`
2. [ ] `FR-RES-PROMOTE_RESEARCH_CANDIDATES`
3. [ ] `FR-RES-DESCRIBE_RESEARCH_METHODS`
4. [ ] `FR-RES-COMPARE_RESEARCH_BATCHES`

##### 12.9 [ ] `FEAT-RES-RESEARCH_STOCKPICKERS`

1. [ ] `FR-RES-RESEARCH_STOCKPICKER`

##### 12.10 [ ] `FEAT-RES-ASSIST_RESEARCH_AI`

1. [ ] `FR-RES-DRAFT_AI_STRATEGIES`
2. [ ] `FR-RES-GOVERN_AI_IMPROVEMENTS`
3. [ ] `FR-RES-PROTECT_AI_INPUTS`

##### 12.11 [ ] `FEAT-RES-RESEARCH_NEURAL_MODELS`

1. [ ] `FR-RES-GOVERN_NEURAL_RESEARCH`

##### 12.12 [ ] `FEAT-RES-SCORE_PORTFOLIO_FITNESS`

1. [ ] `FR-RES-SCORE_PORTFOLIO_FITNESS`

##### 12.13 [ ] `FEAT-RES-MONITOR_MARKET_DRIFT`

1. [ ] `FR-RES-CONSUME_MARKET_INTELLIGENCE`
2. [ ] `FR-RES-ANALYZE_SEASONALITY`
3. [ ] `FR-RES-ANALYZE_MARKET_STRUCTURE`
4. [ ] `FR-RES-DETECT_PERFORMANCE_DRIFT`
5. [ ] `FR-RES-CLASSIFY_DRIFT_STATE`
6. [ ] `FR-RES-RECORD_INTELLIGENCE_LINEAGE`

#### `D-UI` — User Interface De-mock Gates (Stage 12)


##### 12.14 [ ] `FEAT-UI-RUN_RESEARCH`

1. [ ] `FR-UI-SELECT_RESEARCH_MODE`
2. [ ] `FR-UI-CONFIGURE_RESEARCH`
3. [ ] `FR-UI-PREVIEW_RESEARCH`
4. [ ] `FR-UI-CONTROL_RESEARCH`
5. [ ] `FR-UI-COMPARE_RESEARCH`
6. [ ] `FR-UI-REUSE_RESEARCH_SETTINGS`

##### 12.15 [ ] `FEAT-UI-EXPLORE_RESULTS`

1. [ ] `FR-UI-INSPECT_ROBUSTNESS`

---

### Stage 13 — Portfolio (D-PORT)

**Authority:** [Portfolio README](../../app/services/portfolio/README.md)


**Scope:** 24 domain FRs across 8 feature slices plus 5 de-mock FRs across 1 UI feature slice.


**Purpose:** Enable portfolio composition, correlation analysis, aggregate simulation and constraints, automatic portfolio search, risk analysis, Markowitz mean-variance optimization, portfolio merge/split, and research method plugins.


**Vertical path:** `Constituent strategies → Portfolio correlation/aggregation → Markowitz optimizer → Portfolio backtest → D-UI Portfolio Studio`


**UI demo checkpoint:** Construct multi-strategy portfolios, inspect correlation matrices, run Markowitz optimization, analyze combined drawdowns, and export merged strategies.


**Exit gate:** Correlation calculations are mathematically verified; Markowitz optimization handles singularity and constraints robustly; aggregate portfolio equity equals constituent sum.


**De-mock gate:** `FEAT-UI-COMPOSE_PORTFOLIOS` (13.9: all five requirements) switches from `app/ui/src/mocks/` to live Portfolio capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 13.1 [ ] `FEAT-PORT-COMPOSE_PORTFOLIOS`

1. [ ] `FR-PORT-VERSION_PORTFOLIOS`
2. [ ] `FR-PORT-VALIDATE_PORTFOLIO_ADMISSION`
3. [ ] `FR-PORT-COMPOSE_PORTFOLIOS_MANUALLY`

##### 13.2 [ ] `FEAT-PORT-ANALYZE_CORRELATION`

1. [ ] `FR-PORT-VERSION_CORRELATION_INPUTS`
2. [ ] `FR-PORT-COMPUTE_CORRELATION_MATRICES`

##### 13.3 [ ] `FEAT-PORT-SIMULATE_PORTFOLIOS`

1. [ ] `FR-PORT-SIMULATE_AGGREGATE_PORTFOLIOS`
2. [ ] `FR-PORT-CONVERT_PORTFOLIO_CURRENCIES`
3. [ ] `FR-PORT-APPLY_ALLOCATION_METHODS`
4. [ ] `FR-PORT-SCHEDULE_REBALANCING`
5. [ ] `FR-PORT-ENFORCE_EXPOSURE_LIMITS`
6. [ ] `FR-PORT-RESOLVE_SHARED_INSTRUMENTS`

##### 13.4 [ ] `FEAT-PORT-SEARCH_PORTFOLIOS`

1. [ ] `FR-PORT-DEFINE_PORTFOLIO_SEARCH`
2. [ ] `FR-PORT-REJECT_INFEASIBLE_SEARCHES`
3. [ ] `FR-PORT-OPTIMIZE_PORTFOLIO_OBJECTIVES`
4. [ ] `FR-PORT-CHECKPOINT_PORTFOLIO_SEARCH`
5. [ ] `FR-PORT-VERSION_PORTFOLIO_CHANGES`

##### 13.5 [ ] `FEAT-PORT-ANALYZE_PORTFOLIO_RISK`

1. [ ] `FR-PORT-REPORT_PORTFOLIO_RESULTS`
2. [ ] `FR-PORT-DEFINE_PORTFOLIO_METRICS`
3. [ ] `FR-PORT-EXPORT_PORTFOLIO_RESULTS`
4. [ ] `FR-PORT-CALCULATE_PORTFOLIO_RISK`

##### 13.6 [ ] `FEAT-PORT-OPTIMIZE_MARKOWITZ`

1. [ ] `FR-PORT-OPTIMIZE_MARKOWITZ_PORTFOLIOS`

##### 13.7 [ ] `FEAT-PORT-MERGE_PORTFOLIOS`

1. [ ] `FR-PORT-MERGE_PORTFOLIO_STRATEGIES`
2. [ ] `FR-PORT-SPLIT_PORTFOLIO_STRATEGIES`

##### 13.8 [ ] `FEAT-PORT-EXTEND_PORTFOLIO_METHODS`

1. [ ] `FR-PORT-REGISTER_PORTFOLIO_METHODS`

#### `D-UI` — User Interface De-mock Gates (Stage 13)


##### 13.9 [ ] `FEAT-UI-COMPOSE_PORTFOLIOS`

1. [ ] `FR-UI-SELECT_CONSTITUENTS`
2. [ ] `FR-UI-EDIT_PORTFOLIO`
3. [ ] `FR-UI-INSPECT_CORRELATION`
4. [ ] `FR-UI-RUN_PORTFOLIO`
5. [ ] `FR-UI-COMPARE_PORTFOLIOS`

---

### Stage 14 — Orchestration (D-ORCH)

**Authority:** [Orchestration README](../../app/services/orchestration/README.md)


**Scope:** 33 domain FRs across 7 feature slices plus 11 de-mock FRs across 4 UI feature slices.


**Purpose:** Deliver project workflows, task execution engine, condition evaluation, domain delegation, external utilities, neural network training, and execution run history.


**Vertical path:** `D-UI project graph / CLI → Orchestration engine → Task dependency DAG → Domain execution → Checkpoints & Run history`


**UI demo checkpoint:** Create visual project workflows, chain automated tasks (ingest -> build -> test -> deploy), pause/resume execution, and inspect run histories.


**Exit gate:** Project task graphs execute in topological order without race conditions; task failure triggers configured rollback/retry; execution history is durably logged.


**De-mock gate:** `FEAT-UI-START_WORK` (14.8: `FR-UI-RESUME_RECENT_WORK`, `FR-UI-LAUNCH_SHORTCUTS`), `FEAT-UI-EDIT_PROJECTS` (14.9: all six requirements), `FEAT-UI-MONITOR_WORK` (14.10: `FR-UI-CONTROL_JOBS`, `FR-UI-NOTIFY_OUTCOMES`), and `FEAT-UI-ADMINISTER_SYSTEM` (14.11: `FR-UI-MANAGE_UPDATES`) switch from `app/ui/src/mocks/` to live Orchestration capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 14.1 [ ] `FEAT-ORCH-DEFINE_PROJECTS`

1. [ ] `FR-ORCH-DEFINE_PROJECT_GRAPHS`
2. [ ] `FR-ORCH-DECLARE_TASK_CONTRACTS`
3. [ ] `FR-ORCH-DEFINE_TASK_TRANSITIONS`
4. [ ] `FR-ORCH-PIN_PROJECT_RUNS`

##### 14.2 [ ] `FEAT-ORCH-RUN_TASKS`

1. [ ] `FR-ORCH-DEFINE_TASK_STATES`
2. [ ] `FR-ORCH-RETRY_TASKS_IDEMPOTENTLY`
3. [ ] `FR-ORCH-FENCE_TASK_LEASES`
4. [ ] `FR-ORCH-VERSION_TASK_ATTEMPTS`
5. [ ] `FR-ORCH-VERSION_TASK_CHECKPOINTS`
6. [ ] `FR-ORCH-COMMIT_TASK_OUTPUTS`
7. [ ] `FR-ORCH-SCOPE_PROJECT_VARIABLES`
8. [ ] `FR-ORCH-REPORT_PROJECT_PROGRESS`

##### 14.3 [ ] `FEAT-ORCH-EVALUATE_CONDITIONS`

1. [ ] `FR-ORCH-TYPE_PROJECT_VARIABLES`
2. [ ] `FR-ORCH-EVALUATE_PROJECT_EXPRESSIONS`

##### 14.4 [ ] `FEAT-ORCH-RUN_DOMAIN_TASKS`

1. [ ] `FR-ORCH-DELEGATE_DOMAIN_TASKS`
2. [ ] `FR-ORCH-PIN_TASK_SELECTIONS`
3. [ ] `FR-ORCH-SYNC_PROJECT_DATA`
4. [ ] `FR-ORCH-PIN_PORTFOLIO_INPUTS`
5. [ ] `FR-ORCH-COMPILE_CONTROL_TRANSITIONS`

##### 14.5 [ ] `FEAT-ORCH-RUN_UTILITY_TASKS`

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

##### 14.6 [ ] `FEAT-ORCH-TRACK_RUN_HISTORY`

1. [ ] `FR-ORCH-RETAIN_PROJECT_HISTORY`

##### 14.7 [ ] `FEAT-ORCH-TRAIN_NETWORKS`

1. [ ] `FR-ORCH-TRAIN_NEURAL_NETWORKS`

#### `D-UI` — User Interface De-mock Gates (Stage 14)


##### 14.8 [ ] `FEAT-UI-START_WORK`

1. [ ] `FR-UI-RESUME_RECENT_WORK`
2. [ ] `FR-UI-LAUNCH_SHORTCUTS`

##### 14.9 [ ] `FEAT-UI-EDIT_PROJECTS`

1. [ ] `FR-UI-MANAGE_PROJECTS`
2. [ ] `FR-UI-EDIT_TASKS`
3. [ ] `FR-UI-EDIT_PROJECT_GRAPH`
4. [ ] `FR-UI-COMPARE_PROJECTS`
5. [ ] `FR-UI-CONTROL_PROJECTS`
6. [ ] `FR-UI-INSPECT_PROJECTS`

##### 14.10 [ ] `FEAT-UI-MONITOR_WORK`

1. [ ] `FR-UI-CONTROL_JOBS`
2. [ ] `FR-UI-NOTIFY_OUTCOMES`

##### 14.11 [ ] `FEAT-UI-ADMINISTER_SYSTEM`

1. [ ] `FR-UI-MANAGE_UPDATES`

---

### Stage 15 — Interfaces (D-IFACE)

**Authority:** [Interfaces README](../../app/services/interfaces/README.md)


**Scope:** 30 domain FRs across 7 feature slices plus 1 de-mock FR across 1 UI feature slice.


**Purpose:** Expose public HTTP REST, WebSocket event streaming, CLI, MCP, and operator gateways across research, projects, portfolios, capability administration, and trading.


**Vertical path:** `External HTTP/WS/CLI/MCP client → Gateway security & validation → Public domain capabilities → Event broadcasting`


**UI demo checkpoint:** Test all REST endpoints via Swagger/OpenAPI, stream real-time events over WebSocket, execute CLI commands, and connect MCP tools.


**Exit gate:** HTTP, WebSocket, CLI, and MCP gateways maintain strict semantic parity; concurrency tokens prevent lost updates; event streaming recovers from disconnections without dropped messages.


**De-mock gate:** `FEAT-UI-ADMINISTER_SYSTEM` (15.8: `FR-UI-ADMINISTER_CAPABILITIES`) switches from `app/ui/src/mocks/` to live Interfaces capability connections here; each checkbox below completes only with UI↔backend contract-parity evidence.


##### 15.1 [ ] `FEAT-IFACE-SERVE_API_EVENTS`

1. [X] `FR-IFACE-SERVE_VERSIONED_API` — evidence: tests/services/interfaces/api_events/test_api_events.py:34
2. [X] `FR-IFACE-ENFORCE_CONCURRENCY_TOKENS` — evidence: tests/services/interfaces/api_events/test_api_events.py:74
3. [X] `FR-IFACE-DEDUPLICATE_MUTATIONS` — evidence: tests/services/interfaces/api_events/test_api_events.py:106
4. [X] `FR-IFACE-REPLAY_INTERFACE_EVENTS` — evidence: tests/services/interfaces/api_events/test_api_events.py:189
5. [X] `FR-IFACE-TRACK_ASYNC_JOBS` — evidence: tests/services/interfaces/api_events/test_api_events.py:241
6. [X] `FR-IFACE-VALIDATE_ARTIFACT_DOWNLOADS` — evidence: tests/services/interfaces/api_events/test_api_events.py:307
7. [X] `FR-IFACE-EVOLVE_API_COMPATIBLY` — evidence: tests/services/interfaces/api_events/test_api_events.py:415
8. [ ] `FR-IFACE-PAGE_INTERFACE_QUERIES`
9. [ ] `FR-IFACE-QUERY_DATABANK_RESULTS`
10. [ ] `FR-IFACE-PIN_BULK_REQUESTS`
11. [ ] `FR-IFACE-SERVE_PROJECT_API`

##### 15.2 [x] `FEAT-IFACE-AUTOMATE_COMMANDS`

1. [X] `FR-IFACE-DELEGATE_APPLICATION_CALLS` — evidence: tests/services/interfaces/cli_mcp_automation/test_cli_mcp_automation.py:27
2. [X] `FR-IFACE-TRACK_DURABLE_COMMANDS` — evidence: tests/services/interfaces/cli_mcp_automation/test_cli_mcp_automation.py:127
3. [ ] `FR-IFACE-PROVIDE_NONVISUAL_CHARTS`
4. [ ] `FR-IFACE-AUTOMATE_CODE_GENERATION`
5. [ ] `FR-IFACE-SUPPORT_MCP_OPERATIONS`
6. [ ] `FR-IFACE-PRESERVE_MCP_NEUTRALITY`
7. [ ] `FR-IFACE-PUBLISH_AUTOMATION_SCHEMAS`

##### 15.3 [ ] `FEAT-IFACE-OPERATE_RESEARCH`

1. [ ] `FR-IFACE-PREVIEW_RESEARCH_RUNS`

##### 15.4 [ ] `FEAT-IFACE-EDIT_PROJECTS`

1. [ ] `FR-IFACE-VISUALIZE_PROJECT_GRAPHS`

##### 15.5 [ ] `FEAT-IFACE-OPERATE_PORTFOLIOS`

1. [ ] `FR-IFACE-OPERATE_PORTFOLIO_BUILDER`

##### 15.6 [ ] `FEAT-IFACE-ADMINISTER_CAPABILITIES`

1. [ ] `FR-IFACE-ADMINISTER_COMPONENTS`

##### 15.7 [ ] `FEAT-IFACE-OPERATE_TRADING`

1. [ ] `FR-IFACE-MANAGE_TRADING_SESSIONS`
2. [ ] `FR-IFACE-SHOW_TRADING_READINESS`
3. [ ] `FR-IFACE-PREVIEW_TRADING_ACTIONS`
4. [ ] `FR-IFACE-OPERATE_EMERGENCY_CONTROLS`
5. [ ] `FR-IFACE-STREAM_TRADING_EVENTS`
6. [ ] `FR-IFACE-DISPLAY_MARKET_DATA`
7. [ ] `FR-IFACE-DISPLAY_OPERATOR_ANALYTICS`
8. [ ] `FR-IFACE-ENFORCE_TRANSPORT_PARITY`

#### `D-UI` — User Interface De-mock Gates (Stage 15)


##### 15.8 [ ] `FEAT-UI-ADMINISTER_SYSTEM`

1. [ ] `FR-UI-ADMINISTER_CAPABILITIES`
---

### Stage 16 — Final System Integration and Complete-System Release Gate

**Authority:** [`docs/PROJECT.md`](../../docs/PROJECT.md) and [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)

**Scope:** Complete repository-wide integration, mock retirement, multi-domain workflows, hosted/local parity, and release criteria.

**Purpose:** Complete the final end-to-end integration across all 15 business domains, verify full retirement of the dev mock provider, validate hosted/local parity, and pass all system workflows and release criteria.

**Vertical path:** `Complete React Workstation → Live D-IFACE gateways → All 15 Production Domains → Verified Storage/Execution`

**UI demo checkpoint:** Run full end-to-end trading workflows (data onboarding -> strategy design -> backtesting -> optimization -> portfolio creation -> live trading session) in both local and hosted environments.

**Exit gate:** All 142 features and 549 business FRs pass; zero references to `app/ui/src/mocks/` remain in production builds; all 12 system workflows in `docs/PROJECT.md` pass green.

**De-mock gate:** Final — the mock capability provider must be fully retired by this point (final completion gate item 9): no production bundle imports `app/ui/src/mocks/` and the folder is deletable without touching production behavior.

**Completion gates:**

1. **Mock Provider Retirement:** Verify no production bundle imports `app/ui/src/mocks/`, the folder is deletable without affecting production behavior, and all 17 D-UI widget surfaces connect to live backend capabilities.
2. **End-to-End System Workflows:** Verify all twelve multi-domain workflows defined in `docs/PROJECT.md` execute successfully from the React workstation.
3. **Execution Parity Verification:** Verify deterministic equivalence across SIM, PAPER, DEMO, and LIVE routes according to `docs/EXECUTION_PARITY.md`.
4. **Cross-Workspace Isolation:** Verify hosted and local modes preserve identical public contracts and pass multi-user isolation checks.
5. **Physical Removability & Degradation:** Verify that removing any optional domain or plugin results in clean, documented graceful degradation without runtime crashes.

---

## 23. Cross-domain integration rule

A completed domain is not casually reopened because a later domain begins producing compatible evidence.

Instead:

- required dependencies must exist before domain completion;
- earlier receiver domains define exact versioned request/evidence contracts for future producer data when such interaction is needed;
- those receiver contracts are tested with deterministic self-contained evidence fixtures and explicit missing-evidence behavior;
- the later producer domain's stage owns the production integration proof that it emits and submits conforming evidence;
- any discovered incompatibility is an explicit contract change with versioning/migration, not an undocumented backdoor edit.

This preserves domain waterfall discipline without sacrificing HaruQuantAI's spatiotemporal composability or creating artificial runtime dependency cycles.

---

## 24. UI de-mock rule

Stage 1 builds the initial UI workstation surfaces against the dev-only mock provider, but mocks carry no business-authority claim.

After each domain stage:

1. identify all UI ports whose complete real provider set now exists;
2. migrate those ports from mock to real generated client/capability bindings;
3. preserve explicit unavailable behavior when the owning feature/domain is removed;
4. add UI<->backend contract-parity evidence;
5. delete obsolete mock fixtures when no remaining UI workflow depends on them.

No mock-derived result may be presented as authoritative backtest, research, risk, broker, or trading evidence.

---

## 25. Release order is not implementation order

The domain waterfall controls **implementation dependency**, not automatic deployment enablement.

In particular:

- Broker Connectivity is implemented at Stage 5 but broker writes remain gated.
- Runtime Risk and Trading are implemented before Simulator because Simulator depends on their common execution semantics.
- `LIVE` remains disabled by default regardless of how early Trading code is complete.
- hosted, distributed, AI, neural, additional-target, and operational capabilities still require every applicable `PROJECT.md` release gate before they are advertised/enabled.

A completed implementation may therefore remain intentionally unavailable in a release profile until its independent safety/parity gate passes.

---

## 26. Final completion gate

Implementation is complete only when every Stage 0 foundation guarantee remains green, all 142 unique feature completion checkboxes and all 549 unique business-FR checkboxes above are complete with executable `path:line` evidence, all 33 retained shared-foundation guarantees remain passing, and:

1. Every one of the 15 domains starts or degrades independently and advertises only compatible public capabilities or UI contributions.
2. Every shared-module guarantee, domain, feature, responsibility, and FR passes its applicable cold-start, dependency-change, live-removal, reinstall, failed-activation, replacement, leak, and deletion-build checks.
3. All twelve system workflows and every applicable phase/release gate in `PROJECT.md` pass with pinned manifests and no hidden fallback.
4. Simulator and generated-target parity, deterministic replay, persistence recovery, and distributed/local equivalence fixtures pass where applicable.
5. UI workflows remain operable throughout delivery and pass applicable keyboard, focus, semantics, nonvisual-data, loading, stale, unavailable, error, contract-parity, and browser/integration evidence.
6. Broker, Runtime Risk, and Trading remain disabled by default and pass sandbox/testnet, approval, kill-switch, unknown-outcome, reconciliation, protection, ledger, and audit gates before operational release.
7. Hosted and local modes preserve the same public contracts and pass cross-workspace isolation and authorization.
8. No requirement is considered implemented solely because related code, tests, databases, migrations, or UI screens exist; its current owning acceptance contract must pass.
9. The mock capability provider is fully retired: no production bundle imports `app/ui/src/mocks/`, the folder is deletable without touching production behavior, and every mock-build line that reached its de-mock increment has contract-parity evidence at the increment holding its completion checkbox.
10. The intended end state is not merely “all code written.” It is a chain of completed, independently removable, contract-stable domain baselines whose composition reproduces the complete HaruQuantAI product.
