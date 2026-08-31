# Domain Migration Plan — V2 Behavioral Donor → V3 Architecture

**Status:** Active coordination plan
**Pilot domain:** D-DATA
**Migration model:** Domain-by-domain brownfield migration
**Last audited:** 2026-08-27
**V3 audit baseline:** `ae63687b4d1cb94b3f27cd6fcbf047eef970c663`
**V2 donor baseline:** `828de8cb9546d31f91af762d3ab8adc6b1640bbd`

---

## 1. Purpose

HaruQuantAI V3 is no longer to be treated as a primarily greenfield product-domain implementation. The implementation strategy is now **domain-by-domain brownfield migration**.

HaruQuantAI V3 remains the active system and architectural authority. HaruQuantAI-V2 is a pinned behavioral donor used to recover proven algorithms, workflows, domain semantics, tests, fixtures, and implementation lessons where they remain valuable.

The governing rule is:

> **Migrate behavior, not architecture.**

The migration process therefore does **not** copy V2 service structure into V3. Each V2 behavior is first inventoried and classified, then reshaped into the feature packages, public contracts, capability boundaries, lifecycle rules, durable-state ownership, and composability model already defined by V3.

This document serves two purposes:

1. define the reusable migration procedure for every V2 → V3 domain migration; and
2. define the first complete migration audit and migration sequence for the pilot domain, **D-DATA**.

No Data production-code migration is performed by this document.

---

## 2. Normative authority and precedence

When a donor implementation conflicts with V3, the following authority order applies:

1. `docs/PROJECT.md` — system/domain scope and cross-domain ownership;
2. `docs/ARCHITECTURE.md` — structural/runtime/composability constraints;
3. the target V3 domain README — feature ownership, FR semantics, dependencies, exclusions, and completion status;
4. `docs/dev/feature_implementation_pipeline.md` — mandatory per-feature implementation/evidence procedure;
5. `docs/dev/IMPLEMENTATION_ORDER.md` — implementation sequencing authority;
6. V3 public contracts under `app/contracts/`;
7. V2 donor behavior and tests.

V2 is authoritative only as evidence of what previously worked. It is never authoritative for V3 package layout, dependency direction, public types, lifecycle, capability selection, state ownership, or provider architecture.

---

## 3. Non-goals and prohibited migration shortcuts

The following are explicitly out of scope:

- replacing HaruQuantAI V3 with HaruQuantAI-V2;
- swapping repository contents or histories;
- copying `HaruQuantAI-V2/app/services/data/` wholesale into V3;
- making V3 conform to the V2 service/package structure;
- preserving V2 global/shared registries simply because callers already exist;
- preserving direct sibling/foreign implementation imports;
- importing V2 public DTOs/types into V3 public APIs;
- preserving provider-SDK leakage across V3 domain boundaries;
- retaining import-time registration, I/O, task creation, or connections;
- retaining unrestricted `asyncio.create_task()` lifecycle behavior;
- carrying V2 persistence/runtime-store architecture forward without explicit V3 ownership analysis;
- treating a copied module or passing donor test as proof of V3 completion;
- changing Data production code as part of this planning task;
- restarting the pure-greenfield strategy without an explicit future decision.

---

## 4. Universal domain-migration procedure

Every domain migration must use the following procedure. A phase may be lightweight for a small feature, but none may be silently skipped.

| Phase | Name | Required work | Required exit evidence |
|---|---|---|---|
| 0 | Freeze donor baseline | Pin V2 commit; pin V3 baseline; record authoritative V3 docs; forbid moving donor references during the migration unit. | Baseline SHAs and authority list recorded. |
| 1 | Inventory V2 behavior | Enumerate donor packages/modules/classes/functions, public entry points, consumers, providers, state, persistence, side effects, and tests. | Donor inventory with behavior summaries and test references. |
| 2 | Map V2 behavior to V3 Feature/FR registry | Map useful behavior to one V3 feature and its FRs; flag behaviors with no valid V3 owner. | Behavior → feature/FR mapping. |
| 3 | Classify KEEP / ADAPT / REWRITE / DROP | Classify each migration unit using the rubric in Section 5. | Decision plus rationale for every considered unit. |
| 4 | Analyze contract and dependency gaps | Compare donor inputs/outputs/dependencies against existing V3 contracts/capabilities. Determine contract reuse/extension and correct owning domains. | Gap register; no unowned public records/dependencies. |
| 5 | Define target structural decomposition | Define target feature package, focused implementation modules, manifests/config/features, public contract usage, state/artifact ownership. | Target path map satisfying architecture rules. |
| 6 | Migrate features incrementally | Implement one atomic V3 feature/migration slice at a time following `feature_implementation_pipeline.md`. | Feature-local implementation with no unplanned cross-feature coupling. |
| 7 | Adapt state/persistence/artifacts | Replace donor state/store assumptions with explicit V3 feature ownership, immutable versions/provenance where required, and retention rules. | State/artifact ownership documented and tested. |
| 8 | Add composability/lifecycle/removal semantics | Put reversible effects in `FeatureScope`; use managed runtime tasks; add activation, readiness, replace/drain/retire/removal semantics. | Lifecycle/removal/replacement evidence. |
| 9 | Port behavioral tests and usage examples | Preserve donor invariants, adapt tests to V3 contracts, and add feature/contract/usage evidence. | Behavioral parity evidence plus V3 architecture evidence. |
| 10 | Verify cross-domain integration | Test through public contracts/capabilities against actual upstream/downstream boundaries. | Integration tests without implementation imports. |
| 11 | Remove superseded legacy implementations | Delete temporary adapters/dead migration scaffolding when all callers use V3 contracts. | No active dependency on donor runtime code or obsolete adapters. |
| 12 | Domain completion audit | Reconcile README FRs/status, contracts, implementations, state ownership, tests, examples, quality, architecture/import boundaries. | Domain audit proving every in-scope FR is implemented and compliant. |

### 4.1 Atomicity rule

A migration PR/task should be small enough to answer all of the following unambiguously:

- Which V3 feature owns the migrated behavior?
- Which FRs are advanced?
- Which donor behavior is preserved?
- Which donor architecture is deliberately discarded?
- Which public contracts are used or changed?
- Which side effects/state are owned by the feature?
- Which donor tests were preserved or replaced?
- Can the feature be removed/replaced without leaving hidden effects?

If these questions cannot be answered clearly, the migration unit is too broad.

---

## 5. Classification rubric

### KEEP

Use when the donor behavior and implementation are already largely pure, deterministic, correctly bounded, and compatible with V3 after trivial namespace/type adaptation.

`KEEP` never means copying a V2 package structure or public API unchanged. Even KEEP behavior must enter V3 through the V3 feature package and public contracts.

### ADAPT

Use when the implementation or algorithm is valuable but requires V3 contract types, feature packaging, capability resolution, state ownership, lifecycle, persistence, or dependency changes.

This is expected to be the most common classification.

### REWRITE

Use when the intended behavior remains valid but the donor implementation is too coupled to V2 globals, providers, lifecycle, persistence, orchestration, SDK types, or ownership assumptions to migrate safely.

Behavioral tests and fixtures should still be reused as specifications where possible.

### DROP

Use when the donor responsibility is obsolete, duplicated, belongs to another V3 domain, conflicts with current V3 semantics, or exists only to support removed V2 architecture.

`DROP from D-DATA` may mean **re-home to another V3 domain**, not necessarily delete the behavior from the product.

---

## 6. Donor handling policy

### 6.1 Direct inspection, not a `.migration/` donor copy

The V2 donor must be inspected directly from `haruperi/HaruQuantAI-V2` at the pinned donor SHA.

Do **not** create `.migration/v2-data/` as a shadow copy of the donor.

Reasons:

- the pinned Git commit already provides an immutable donor baseline;
- a second copy can silently diverge from the audited donor;
- a local donor subtree can become an accidental import/runtime dependency;
- duplicated source obscures whether a later change came from V2 or from the migration itself;
- feature-level migration commits should contain only intentional V3 code, tests, fixtures, and documentation.

A donor test fixture or algorithm may be copied into its final V3 destination **after** classification, with provenance noted in the migration task/commit. The V2 runtime package itself must never become a V3 dependency.

### 6.2 Temporary compatibility adapters

Temporary adapters are allowed only when all of the following hold:

- the adapter lives in V3, not in a copied V2 runtime tree;
- it exposes/consumes V3 public contracts;
- it does not enable new callers to depend on a legacy API;
- it does not bypass capability resolution or import a foreign feature implementation;
- it has an explicit removal criterion and migration status;
- it is removed no later than Phase 11 for the owning migration scope.

Compatibility code that becomes an indefinite second architecture is prohibited.

---

## 7. D-DATA pilot audit

### 7.1 V3 physical state at the audit baseline

At V3 commit `ae63687b4d1cb94b3f27cd6fcbf047eef970c663`:

```text
app/services/data/
├── README.md
└── __init__.py
```

There are no Data production feature packages yet. The current service README is therefore the semantic target rather than evidence of existing implementation.

V3 already contains the Data public-contract package:

```text
app/contracts/data/
├── __init__.py
├── capabilities.py
├── errors.py
├── models.py
└── ports.py
```

The contracts define capability keys and provider protocols for all fourteen planned Data features. These contracts are strong starting points, but migration must still verify that each donor behavior can be represented without leaking V2/provider-specific types.

### 7.2 V3 authoritative Data feature/FR registry

| Order | Feature | Package | Capability | Authoritative FRs | Current status |
|---:|---|---|---|---|---|
| 1 | F-DATA-01 | `historical_acquisition` | `data.ingest-history` | FR-DATA-01 | Planned |
| 2 | F-DATA-02 | `connector_sync` | `data.sync-connectors` | FR-DATA-02, FR-DATA-33 | Planned |
| 3 | F-DATA-03 | `quantdata_import` | `data.import-quantdata` | FR-DATA-03A, 03B, 03C, 32A, 32B | Planned |
| 4 | F-DATA-04 | `tick_normalization` | `data.normalize-ticks` | FR-DATA-04 | Planned |
| 5 | F-DATA-05 | `quality_resolution` | `data.resolve-quality` | FR-DATA-05, FR-DATA-06 | Planned |
| 6 | F-DATA-06 | `bar_aggregation` | `data.aggregate-bars` | FR-DATA-07 | Planned |
| 7 | F-DATA-07 | `retention_management` | `data.manage-retention` | FR-DATA-08, FR-DATA-22 | Planned |
| 8 | F-DATA-08 | `time_alignment` | `data.align-series` | FR-DATA-09 | Planned |
| 9 | F-DATA-09 | `data_profiling` | `data.prepare-profiles` | FR-DATA-13, 14, 15, 16, 19, 20 | Planned |
| 10 | F-DATA-10 | `external_indicators` | `data.import-indicators` | FR-DATA-17, FR-DATA-18 | Planned |
| 11 | F-DATA-11 | `run_binding` | `data.bind-run-data` | FR-DATA-21, 22A, 22B, 23A, 23B | Planned |
| 12 | F-DATA-12 | `scenario_generation` | `data.generate-scenarios` | FR-DATA-24, 25, 26, 27, 28 | Planned |
| 13 | F-DATA-13 | `market_news` | `data.track-market-news` | FR-DATA-29, 30, 31 | Planned |
| 14 | F-DATA-14 | `market_streaming` | `data.stream-market-events` | FR-DATA-34 | Planned |

The exact V3 capability constants are:

```text
data.ingest-history
data.sync-connectors
data.import-quantdata
data.normalize-ticks
data.resolve-quality
data.aggregate-bars
data.manage-retention
data.align-series
data.prepare-profiles
data.import-indicators
data.bind-run-data
data.generate-scenarios
data.track-market-news
data.stream-market-events
```

### 7.3 V2 Data implementation inventory

The donor at `828de8cb9546d31f91af762d3ab8adc6b1640bbd` is not a single narrow market-data service. It is a broad subsystem containing acquisition, datasets, persistence, quality, time/session data, research sources, synthetic data, replay/runtime stores, jobs, evidence, and migration infrastructure.

The audited implementation inventory is:

| V2 path | Implementation surface | Migration significance |
|---|---|---|
| `app/services/data/__init__.py` | Large facade exporting settings/limits, history, datasets, snapshots/lineage, market events, integrity, calendar/sessions, SQX, synthetic generation, transformations, jobs/evidence/migrations, and deletion helpers. | Do not reproduce. Inventory of legacy public behavior only. |
| `app/services/data/_settings.py` | Legacy Data settings. | Mine defaults/constraints; map to feature-local config or composition config. |
| `app/services/data/_limits.py` | Legacy limits/bounds. | ADAPT useful bounds into feature-owned config/validation. |
| `app/services/data/_shared/` | `failure_injection.py`, `io.py`. | Test utility / low-level helper candidates; no shared-global carry-forward. |
| `app/services/data/alignment/` | `contracts.py`, `errors.py`, `normaliser.py`, README. | Strong donor for F-DATA-08. |
| `app/services/data/contracts/` | Legacy contracts for data jobs, dataset registry, economic calendar, evidence, job lineage, market data, market events, time sessions. | Specification evidence only; V3 contracts remain authoritative. |
| `app/services/data/data_jobs/` | API/config/errors/idempotency/interfaces/manager/models. | Generic job orchestration is not target Data architecture; useful idempotency semantics may be reused through owning runtime/composition mechanisms. |
| `app/services/data/datasets/` | locator, manager, manifest, models, registry, validation. | Useful dataset/version/validation behavior; global registry/manager architecture must be rewritten. |
| `app/services/data/economic_calendar/` | API/config/DuckDB store/errors/importers/interfaces/offsets/session guard/types/validator. | Calendar/session semantics are useful, but Catalogue is authoritative for canonical market calendar/timezone identity in V3. |
| `app/services/data/evidence/` | data contracts, duality guard, manager, models, narrative digest, parity probe, state. | Primarily governance/evidence infrastructure; only feature-specific provenance/parity behavior should migrate into Data. |
| `app/services/data/integrity/` | models, service, source. | Strong donor for F-DATA-05 and portions of F-DATA-07. |
| `app/services/data/market_data/` | API/config/errors/free sources/history/jobs/backtest materializer/manager/models/providers/research data/router/runtime/types. | Major donor for F-DATA-01, F-DATA-11 and F-DATA-14 semantics; routing/provider/session architecture must be reassigned. |
| `app/services/data/market_events/` | API/compression/config/errors/interfaces/manager/models plus internal tests. | Candidate donor for event/news/stream integrity and compression, subject to semantic split between F-DATA-13 and F-DATA-14. |
| `app/services/data/migrations/` | Legacy migration core plus Data-jobs, economic-calendar/event-definition, market-reference, research-source, runtime-store and related migration modules. | Do not migrate as active D-DATA capability. Historical upgrade knowledge only. |
| `app/services/data/persistence/` | dataset snapshot, lineage, store. | Reuse provenance/versioning behavior where compatible; rewrite ownership/store architecture. |
| `app/services/data/replay/` | engine, models, readers. | Replay execution belongs outside D-DATA; data-reading/binding semantics may inform F-DATA-11. |
| `app/services/data/runtime_stores/` | base runtime-store abstraction and InfluxDB store. | Runtime-state store architecture is not automatically D-DATA durable truth; re-home or drop. |
| `app/services/data/sources/` | free/research source implementations. | Provider-specific behavior may inform F-DATA-01/F-DATA-10/F-DATA-13 but must respect provider ownership. |
| `app/services/data/sqx_source/` | adapters/config/database/history/instrument sync/interfaces/models/MT5 bar sync/MT5 tick sync/paths/reference sync/schema/service/store/symbol-info sync. | Strong donor for F-DATA-03 and parts of F-DATA-02; identity truth must move behind Catalogue contracts. |
| `app/services/data/synthetic_data/` | API/copula/generator/models/shock/timeframe/timeframe alignment. | Strong donor for F-DATA-12. |
| `app/services/data/time_sessions/` | API/day-bar policy/DuckDB store/errors/interfaces/loader/manager/models/validator. | Useful session/time semantics; canonical identity/calendar ownership belongs to Catalogue. |
| `app/services/data/transformation/` | engines/errors/models/pandas engine/polars engine/registry/tick derivation plus README. | Strong donor for F-DATA-04, F-DATA-06 and portions of F-DATA-08. |

This inventory is intentionally **behavioral**, not a proposed V3 tree. No V2 directory above is approved as a V3 package merely because it exists in the donor.

### 7.4 Donor maturity and test evidence

V2 has substantial Data-specific evidence rather than only production modules. Audited test areas include:

- unit tests for tick derivation and transformation behavior;
- timestamp/temporal/alignment tests;
- synthetic generator, copula, timeframe-alignment, and shock tests;
- SQX history/import/reference/symbol synchronization tests;
- market-data history, manager/router/runtime/free-source tests;
- persistence snapshot/lineage/store tests;
- dataset registry/manager/manifest/validation tests;
- integrity tests;
- economic-calendar and time-session tests;
- data-jobs, evidence, and migration tests;
- market-events tests;
- component/integration/structural/usage-feature/workflow evidence around the Data subsystem.

Representative donor test path already verified during this audit:

```text
tests/data/unit/test_tick_derivation.py
```

The presence of tests does **not** automatically make a donor subsystem KEEP. Test maturity proves behavioral knowledge; V3 architecture compliance is assessed separately.

---

## 8. D-DATA ownership corrections and re-homing decisions

Several V2 responsibilities are useful but do not belong to the V3 Data domain as implemented in V2.

| V2 responsibility | D-DATA decision | Correct V3 ownership/boundary |
|---|---|---|
| Broker/provider transport and connection/session lifecycle | DROP from Data implementation; preserve behavioral needs | Broker Connectivity capability and composition. |
| Generic provider selection/router | DROP from feature implementation | Composer/provider selection. |
| Instrument/symbol identity truth and aliases | ADAPT consumers, do not own truth | Catalogue contracts/capabilities. |
| Canonical trading calendar/timezone/session identity | ADAPT consumers, do not own canonical truth | Catalogue. |
| Generic data-job orchestration | DROP from Data package architecture | Composition/orchestration/runtime mechanisms; Data feature may expose its own operation only. |
| Legacy platform/domain migration orchestration | DROP | Development/migration tooling, not product D-DATA capability. |
| Replay execution | DROP from Data | Simulator/runtime execution domain; D-DATA may bind/read immutable data. |
| Orders/positions/account runtime state | DROP | Trading/Broker/Runtime Risk owning contracts. |
| Generic runtime-store abstraction | DROP/REHOME | Owning runtime domain or platform persistence layer after separate design decision. |
| Global dataset registry/singleton manager | REWRITE | Explicit feature-owned durable artifact/version metadata and public contracts. |
| Economic-news source ingestion | ADAPT only when it satisfies F-DATA-13 | Data market-news feature, with provider boundaries and stable normalized identity. |
| Research-source framework | Split by semantics | F-DATA-10/F-DATA-13 only where exact FRs match; Research domain otherwise. |
| Generic evidence/duality infrastructure | DROP/REHOME | Test/governance/observability infrastructure; retain only Data-specific provenance rules. |
| SQX symbol/reference synchronization | ADAPT | F-DATA-03/F-DATA-02 use Catalogue resolution; no private competing identity registry. |
| Dataset snapshots/lineage | ADAPT | F-DATA-07/F-DATA-11 feature-owned artifact/version/provenance model. |

---

## 9. V2 behavior → V3 Data migration matrix

`Status = Audited` means the migration decision is planned, **not** that V3 production code exists.

| V2 path/module/class/function | Existing behavior | Current consumers/dependencies | Existing tests/evidence | V3 owning feature | V3 FRs | Decision | Target V3 path | Required contracts | Required capability dependencies | State/persistence changes | Composability changes | Tests to preserve/add | Migration order | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|
| `transformation/tick_derivation.py::derive_ticks`, `derive_tick_records` | Deterministic tick derivation for MT5 quoted FX and LAST/VOLUME semantics, timestamp/order/value validation | Transformation models/types; no network required | `tests/data/unit/test_tick_derivation.py` and transformation tests | F-DATA-04 `tick_normalization` | FR-DATA-04 | **KEEP algorithm / ADAPT boundary** | `app/services/data/tick_normalization/` focused implementation module | Existing `TickNormalizationProvider` and Data models/errors; extend only if an FR cannot be expressed | None for normal in-memory use; optional Catalogue semantics only where README permits | No persistence required | Package as removable feature; no import effects; capability published via feature lifecycle | Port all donor tick cases; add provider/manifest/config/feature/removal tests | 1 | Audited |
| `alignment/normaliser.py` + alignment contracts/errors | Canonical timestamp normalization and alignment rules | Legacy alignment contracts/time assumptions | Alignment/temporal tests | F-DATA-08 `time_alignment` | FR-DATA-09 | **ADAPT** | `app/services/data/time_alignment/` | Existing `TimeAlignmentProvider` + V3 Data models | Catalogue canonical timezone/calendar where required | No hidden registry; explicit inputs/results | Capability resolution; feature-local config; removal evidence | Preserve timestamp/DST/gap cases; add Catalogue-boundary tests | 2 | Audited |
| `synthetic_data/generator.py`, `copula.py`, `shock.py`, `timeframe*.py` | Synthetic scenarios, dependence/correlation, shocks, timeframe handling | NumPy/data models; legacy configs | Synthetic unit/integration tests | F-DATA-12 `scenario_generation` | FR-DATA-24..28 | **ADAPT** | `app/services/data/scenario_generation/` | Existing `ScenarioGenerationProvider` + typed scenario models | None beyond typed input; Catalogue only if explicit identity resolution is needed | Scenario provenance/version metadata explicit; deterministic seed recorded | Pure computation behind feature capability; no global RNG/state | Preserve deterministic seed, PSD/correlation, shock/timeframe cases; add provenance tests | 3 | Audited |
| `integrity/service.py`, `integrity/source.py`, integrity models | Detect/resolve source/data integrity problems | Legacy dataset/source abstractions | Integrity tests | F-DATA-05 `quality_resolution` | FR-DATA-05, 06 | **ADAPT** | `app/services/data/quality_resolution/` | Existing `QualityResolutionProvider`; V3 quality/provenance models | Optional Catalogue instrument semantics | Replace hidden/global source state with typed source lineage and explicit repair result | Feature-local reversible resources only | Preserve gap/corruption/source-precedence cases; add lineage/dedup contract tests | 4 | Audited |
| `transformation/pandas_engine.py`, `polars_engine.py`, transformation registry portions | Dataframe transformations/resampling/aggregation | Pandas/Polars and legacy engine registry | Transformation tests | F-DATA-06 `bar_aggregation` and F-DATA-08 | FR-DATA-07, 09 | **ADAPT** | `bar_aggregation/` and `time_alignment/` focused modules | `BarAggregationProvider`, `TimeAlignmentProvider` | Catalogue calendar/timezone where semantic | No generic engine registry as durable/global state | Engine choice feature-local/configured; composer remains provider authority | Preserve OHLCV aggregation and boundary cases; multi-timeframe/calendar tests | 5 | Audited |
| `market_data/history.py` | Bounded historical retrieval/completion behavior | Legacy providers/router/config | History tests | F-DATA-01 `historical_acquisition` | FR-DATA-01 | **ADAPT** | `app/services/data/historical_acquisition/` | `HistoricalAcquisitionProvider` + V3 request/result/provenance types | Broker or Plugin acquisition capability; Catalogue symbol resolution | Persist explicit version/provenance through V3-owned artifacts; no provider store leakage | Connection lifecycle remains upstream; Data owns only request/normalize/persist workflow | Preserve range/completeness/provider-error cases; add capability-boundary tests | 6 | Audited |
| `market_data/providers/*`, router/session portions | Provider SDK routing, connector calls, selection | Broker/provider SDKs and global router assumptions | Provider/router tests | F-DATA-01 only as dependency, not implementation owner | FR-DATA-01 | **REWRITE/DROP from Data** | Broker/Plugin/composition owning packages; Data has no direct SDK adapter | Broker/Plugin public contracts | Broker/Plugin capabilities | No Data-owned connector sessions | Composer selects providers; feature resolves capability | Reuse behavioral provider tests in owning domain; add Data integration mocks/contracts | 6 | Audited |
| `sqx_source/history.py`, `mt5_bar_sync.py`, `mt5_tick_sync.py`, import/adapters | SQX/DuckDB history and tab-separated MT5 data import behavior | DuckDB/filesystem/SQX schema | SQX history/import tests | F-DATA-03 `quantdata_import` | FR-DATA-03A/B/C, 32A/B | **ADAPT** | `app/services/data/quantdata_import/` | Existing `QuantDataImportProvider` + import models | Catalogue identity/strategy resolution | Store imported artifacts with V3 provenance/version identity; no donor service singleton | File/database handles opened in feature scope; no import-time DB state | Preserve parsing, last-unclosed-row, bar/tick/schema cases; add lifecycle/rollback tests | 7 | Audited |
| `sqx_source/instrument_sync.py`, `reference_sync.py`, `symbol_info_sync.py` | Reconcile symbols/reference metadata | SQX DB and legacy symbol stores | SQX reference/symbol tests | F-DATA-02/F-DATA-03 consumer behavior | FR-DATA-02, 03A/B/C, 33 | **ADAPT + ownership split** | `connector_sync/` orchestration plus Catalogue-owned identity contracts | Data connector-sync port; Catalogue lookup/identify/update contracts | Catalogue; Broker/Plugin as source | Data does not create a competing canonical identity store | Resolve/publish through capabilities; replace/drain semantics for regulated feature | Preserve reconciliation/rename cases; add Catalogue truth-authority tests | 8 | Audited |
| `time_sessions/*` | Session loading/validation/day-bar rules and persistent session records | DuckDB/session manager | Time-session tests | F-DATA-02/F-DATA-06/F-DATA-08 consumers | FR-DATA-02, 07, 09, 33 | **ADAPT semantics / REHOME truth** | Catalogue calendar/session capability; small Data adapters only where needed | Catalogue contracts, Data request models | Catalogue | Remove Data-owned canonical calendar/session DB | Data reacts to Catalogue/provider changes rather than owning truth | Port validation/DST/day-bar cases to Catalogue and Data integration tests | 8 | Audited |
| `economic_calendar/*` | Calendar import/validation/offset/session guard/storage | Provider imports, DuckDB | Economic-calendar tests | F-DATA-13 only for market-news facts; otherwise Catalogue/calendar owner | FR-DATA-29..31 only where news/event semantics match | **SPLIT: ADAPT/REHOME** | `market_news/` for normalized news; Catalogue for canonical market calendar | Market-news contracts plus Catalogue contracts | Provider capability/config; Catalogue identity | News raw+normalized retention explicit; calendar truth not duplicated | Managed provider resources/tasks in feature scope | Preserve parsing/update/dedup semantics applicable to news; rehome session tests | 9 | Audited |
| `datasets/manifest.py`, `validation.py`, locator/model behavior | Dataset metadata, validation, location/manifests | Global registry/manager, filesystem/store | Dataset tests | F-DATA-07 and F-DATA-11 | FR-DATA-08, 21, 22, 22A/B, 23A/B | **ADAPT** | `retention_management/` and `run_binding/` focused artifact modules | V3 Data artifact/run-binding models | Catalogue identity; execution-profile contract for run binding | Replace global registry with immutable artifact/version IDs and explicit owner metadata | No process-global registry; handles/resources scoped | Preserve manifest/validation cases; add immutable-version and deletion-protection tests | 10 | Audited |
| `persistence/dataset_snapshot.py`, `lineage.py` | Snapshots and lineage/provenance | Legacy persistence/store | Persistence tests | F-DATA-07/F-DATA-11 | FR-DATA-08, 21, 22, 22A/B, 23A/B | **ADAPT** | Feature-owned artifact/lineage modules under retention/run_binding | V3 Data version/provenance/run-binding contracts | None beyond owning capability dependencies | Immutable versions; retention cannot remove bound data; provenance explicit | Durable cleanup only after safe replacement/drain | Preserve snapshot/lineage invariants; add bound-artifact protection tests | 10 | Audited |
| `persistence/store.py` | Legacy storage abstraction/implementation | Filesystem/database assumptions | Store tests | F-DATA-07/F-DATA-11 infrastructure | same | **REWRITE** | Focused storage adapter selected by owning feature/config; public surface remains contracts | Internal storage protocol only if needed; public V3 Data contracts unchanged | Composition config; no foreign impl import | Explicit ownership and atomicity; avoid generic global service store | Open/close via FeatureScope; replacement-safe | Port failure/atomicity tests rather than API shape | 10 | Audited |
| `integrity/*` compression behavior and `market_events/compression.py` | Compression/space-management helpers | Dataset/event formats | Integrity/event tests | F-DATA-07 `retention_management` | FR-DATA-08, 22 | **ADAPT** | `app/services/data/retention_management/` focused modules | `RetentionManagementProvider` + artifact metadata | Maintenance authorization/retention state | Compression/partitioning linked to owned artifact versions | Cleanup is reversible or deferred until replacement health is proven | Preserve compression/cleanup cases; add protected-version tests | 11 | Audited |
| `market_data/backtest_materializer.py` + dataset snapshot/lineage behavior | Materialize deterministic data for runs/backtests | Dataset/persistence/market data | Materializer/persistence tests | F-DATA-11 `run_binding` | FR-DATA-21, 22A/B, 23A/B | **ADAPT** | `app/services/data/run_binding/` | `RunBindingProvider` + execution-profile/run-binding public contracts | Catalogue; execution-profile owner; retention availability | Immutable run-data binding; preserve exact artifact/version/provenance | No replay execution in feature; bounded materialization resources | Preserve repeatability/lookback/materialization cases; add immutable binding tests | 12 | Audited |
| `replay/engine.py` | Replays data into an execution loop | Replay models/readers/runtime consumers | Replay tests | Not D-DATA execution owner | — | **DROP/REHOME** | Simulator/runtime domain | Simulator/runtime contracts | D-DATA run-binding/read capability | Data only exposes bound/readable data | Lifecycle belongs to Simulator | Move execution tests; retain reader/binding invariants in Data tests | — | Audited |
| `market_data/research_data.py`, `sources/research/*` | Research-source retrieval/series preparation | External/research providers | Research/free-source tests | F-DATA-09/F-DATA-10 only where FR semantics match | FR-DATA-13..20 | **ADAPT selectively** | `data_profiling/`, `external_indicators/`; Research domain otherwise | Profiling/indicator ports and typed series | Catalogue; configured provider if required | Version enrichment outputs/provenance; no provider globals | Provider lifecycle scoped; no generic research router | Preserve useful transformations/provider fixtures; add exact FR tests | 13 | Audited |
| Correlation/pair/statistical utilities embedded in donor research/data workflows | Statistical profiling behavior | Numeric stack, symbol metadata | Research/profile tests where present | F-DATA-09 `data_profiling` | FR-DATA-13,14,15,16,19,20 | **ADAPT** | `app/services/data/data_profiling/` | `DataProfilingProvider` and profile result models | Catalogue symbol mapping | Export/version analytics explicitly; no trading execution state | Pure computation where possible | Correlation/cointegration/Hurst/alias/triangle/profile tests per README | 13 | Audited |
| Donor external-source indicator retrieval where semantics match configured indicator enrichment | Fetch/align external time series | External provider/client | Source tests | F-DATA-10 `external_indicators` | FR-DATA-17,18 | **REWRITE/ADAPT selectively** | `app/services/data/external_indicators/` | `ExternalIndicatorsProvider`; provider-specific types private | Catalogue target-series resolution; configured provider | Persist/version enrichment provenance | Connections/tasks feature-scoped; provider selection explicit | Add XAUUSD/configurable indicator, deterministic enrichment/version tests | 14 | Audited |
| `market_events/*` normalized event models/manager semantics | Event normalization, update/dedup/compression | Event providers and stores | Internal market-events tests | F-DATA-13 `market_news` when representing news/events | FR-DATA-29,30,31 | **ADAPT** | `app/services/data/market_news/` | `MarketNewsProvider` + V3 news models/events | Catalogue identity; configured provider | Preserve raw + normalized, stable identity, revision/provenance, retention | Provider resources/tasks managed by feature; no global manager | Dedup/update/stable-ID/provider-failure/retention tests | 15 | Audited |
| `market_data/runtime.py` and stream-like event behavior | Runtime market-data delivery | Legacy provider/router/runtime state | Runtime/market-data tests | F-DATA-14 `market_streaming` | FR-DATA-34 | **REWRITE boundary / ADAPT event semantics** | `app/services/data/market_streaming/` | `MarketStreamingProvider`, `MarketStreamEvent` | Broker Connectivity streaming; Catalogue identity | Streaming is not durable truth unless explicitly recorded by another feature | Broker owns connection; Data owns normalization/gap/sequence/cancel/drain semantics; managed tasks only | Reconnect/gap/sequence/cancellation/drain/replacement tests | 16 | Audited |
| `data_jobs/*` | Generic job scheduling/manager/idempotency | Legacy managers/state | Data-job tests | No standalone D-DATA feature | — | **DROP/REHOME** | Composition/orchestration/runtime infrastructure | Owning runtime contracts | Feature capability invocation | No generic Data job registry | Managed work through V3 runtime mechanisms | Preserve idempotency semantics only where feature-specific | — | Audited |
| `runtime_stores/*` | Generic runtime store + InfluxDB implementation | Runtime consumers | Runtime-store/migration evidence | Not automatically D-DATA | — | **DROP/REHOME** | Owning runtime/platform infrastructure after separate design | Owning contracts | Owning runtime capabilities | Do not make D-DATA owner of orders/positions/account/runtime truth | Lifecycle owned by consuming domain | Rehome relevant store tests | — | Audited |
| `evidence/*` | Parity/evidence/duality/narrative state | Generic evidence framework | Evidence tests | Cross-cutting, not a Data feature | — | **DROP/REHOME; retain specific provenance invariants** | Test/governance/observability infrastructure | Existing V3 testing/observability contracts as applicable | N/A | No duplicate evidence datastore in Data | N/A | Use as migration parity methodology where useful | — | Audited |
| `migrations/*` | Upgrades legacy Data schemas/subsystems | Legacy V2 state/layout | Migration tests | Not product D-DATA capability | — | **DROP from runtime migration target** | No V3 Data feature package | N/A | N/A | Historical migration knowledge only | N/A | No need to port unless a real V3 deployed-state migration is later required | — | Audited |

---

## 10. Contract and dependency gap register

### GAP-DATA-01 — Existing V3 Data contracts are the default, not V2 contracts

The fourteen V3 provider protocols and capability constants already exist. Every migration task must first try to express donor behavior through them.

**Decision:** do not copy `V2/app/services/data/contracts/` into V3.

If an existing V3 request/result cannot express an authoritative README FR, extend `app/contracts/data/` intentionally and update contract tests. Do not extend a public contract merely to preserve a legacy V2 call signature.

### GAP-DATA-02 — Catalogue identity/calendar contracts are prerequisite boundaries

V2 Data owns or stores symbol/reference/session/calendar facts in several places. V3 Data is not allowed to become a second canonical identity system.

**Required resolution:** F-DATA-01/02/03/06/08/09/11/13/14 must consume Catalogue public contracts for canonical instrument identity, symbol mapping, and calendar/timezone semantics where their README requires those facts.

If the required Catalogue contract is absent, add/extend the **Catalogue-owned contract** before implementing the dependent Data behavior.

### GAP-DATA-03 — Broker/provider transport must not leak into Data

V2 market-data routers/providers and connector synchronization combine Data and transport responsibilities.

**Required resolution:** network/session/SDK capabilities live behind Broker Connectivity or Plugin contracts. Data receives typed records/results/capabilities; provider SDK objects must not appear in Data public contracts.

### GAP-DATA-04 — Durable artifact/version model replaces global dataset registry assumptions

V2 dataset/persistence managers contain reusable behavior but are organized around legacy registries/stores.

**Required resolution:** establish explicit V3 ownership for dataset versions, provenance, lineage, retention protection, and run bindings before F-DATA-07/F-DATA-11 implementation. Bound run data must be immutable and protected from retention cleanup.

### GAP-DATA-05 — F-DATA-10 has weaker direct donor coverage

V2 contains research/free-source machinery, but that does not prove the exact current FR-DATA-17/18 external-indicator workflow already exists in a V3-compatible form.

**Decision:** treat provider fixtures/parsing/alignment as donor material, but plan F-DATA-10 as selective ADAPT/REWRITE rather than assuming a direct port.

### GAP-DATA-06 — F-DATA-13 and F-DATA-14 must be semantically separated

V2 `market_events`/runtime behavior spans persisted events, provider events, and live runtime data.

**Decision:**

- F-DATA-13 owns normalized market-news/event collection, raw/normalized retention, updates, dedup, stable identity, provenance;
- F-DATA-14 owns live bid/ask/trade streaming normalization, sequence/gap/reconnect semantics, cancellation, drain, and handoff;
- Broker owns the underlying live connection/transport.

### GAP-DATA-07 — Generic V2 jobs/managers cannot become hidden V3 orchestration

Feature work that needs asynchronous execution must use V3 managed feature/runtime mechanisms.

**Decision:** reuse idempotency/retry semantics where valuable, but do not migrate the V2 generic Data-job manager as a second orchestrator.

---

## 11. Target V3 structural decomposition

The target remains the feature structure already mandated by V3:

```text
app/services/data/
├── README.md
├── __init__.py
├── historical_acquisition/
├── connector_sync/
├── quantdata_import/
├── tick_normalization/
├── quality_resolution/
├── bar_aggregation/
├── retention_management/
├── time_alignment/
├── data_profiling/
├── external_indicators/
├── run_binding/
├── scenario_generation/
├── market_news/
└── market_streaming/
```

Each feature package uses the standard shape:

```text
<feature>/
├── README.md
├── __init__.py       # empty or docstring-only
├── manifest.py
├── config.py
├── feature.py
└── focused implementation modules
```

The matrix in Section 9 identifies donor behaviors that may populate focused implementation modules. It does **not** authorize nested recreation of V2 managers/registries/services.

---

## 12. D-DATA migration order

The Data migration should not follow V2 directory order. It should minimize architectural uncertainty and build outward from deterministic behavior.

### Wave A — Pure/deterministic transformation foundation

1. **F-DATA-04 Tick Normalization**
2. **F-DATA-08 Time Alignment**
3. **F-DATA-12 Scenario Generation**
4. **F-DATA-05 Quality Resolution**
5. **F-DATA-06 Bar Aggregation**

Why first: these provide the strongest behavioral donors with the least provider/lifecycle/state coupling. They prove the brownfield method while exercising V3 contracts, feature packaging, and removability.

### Wave B — Acquisition and identity-dependent ingestion

6. **F-DATA-01 Historical Acquisition**
7. **F-DATA-02 Connector Sync**
8. **F-DATA-03 QuantData Import**

Why next: these depend on Catalogue and Broker/Plugin boundaries and therefore should start only after the pure feature migration pattern is proven and missing upstream contracts are explicit.

### Wave C — Durable artifact lifecycle

9. **F-DATA-07 Retention Management**
10. **F-DATA-11 Run Binding**

Why next: these require the artifact/version/provenance ownership model to be settled. Implementing them earlier would risk copying V2 global registry/store assumptions.

### Wave D — Analytical/enrichment/event ingestion

11. **F-DATA-09 Data Profiling**
12. **F-DATA-10 External Indicators**
13. **F-DATA-13 Market News**

Why next: these can reuse the stable Data artifacts and identity mappings established by earlier waves while keeping Research/provider responsibilities separated.

### Wave E — Live streaming

14. **F-DATA-14 Market Streaming**

Why last: this has the greatest runtime lifecycle and upstream Broker-readiness coupling. It must prove reconnect/gap/sequence/cancellation/drain/replacement behavior without taking ownership of the broker connection.

---

## 13. State, persistence, and artifact migration rules

The following rules apply to every Data migration task:

1. A V2 store/manager/registry is never adopted merely because its schema or tests are mature.
2. Durable state must have an explicit owning V3 feature/domain.
3. Public durable identities must use V3 public contracts, not V2 model classes.
4. Dataset/run artifacts that affect reproducibility must be immutable or version-addressed.
5. Provenance must record enough source/config/version information to reproduce or explain a result.
6. Run-bound data cannot be silently replaced by retention or connector resynchronization.
7. F-DATA-07 may delete/compress only artifacts it is authorized to manage and only after protection/binding rules are evaluated.
8. Feature replacement follows install → health → publish → drain → cleanup. Irreversible cleanup cannot precede a healthy published replacement.
9. External DB/filesystem/network handles must be acquired/released through feature lifecycle mechanisms.
10. Process-global mutable registries from V2 are not migration targets.

---

## 14. Test and evidence migration strategy

Passing copied V2 tests is necessary behavioral evidence where applicable, but never sufficient for V3 acceptance.

Each migrated feature must build an evidence stack from the following layers:

### 14.1 Donor behavior parity

- port relevant V2 unit tests or convert them into V3 contract-level tests;
- preserve edge cases, validation rules, ordering, determinism, error semantics, and fixtures that encode mature behavior;
- explicitly document any intentionally changed behavior.

### 14.2 V3 feature tests

- config parsing/validation;
- manifest metadata/dependencies;
- provider protocol behavior;
- feature activation/readiness;
- failure handling;
- feature-local state/artifact ownership.

### 14.3 Composability evidence

For every Regulated Data feature:

- no registration/I/O/task/connection on import;
- managed tasks only;
- reversible side effects in `FeatureScope`;
- activation failure cleanup;
- removal cleanup;
- replacement health before publication;
- drain/cancellation where in-flight work exists;
- rollback before irreversible cleanup.

### 14.4 Contract and cross-domain tests

- consumers use `app/contracts/` only;
- no sibling/foreign implementation imports;
- Catalogue identity/calendar authority respected;
- Broker/Plugin transport hidden behind capability contracts;
- provider-specific SDK types do not escape into public Data contracts.

### 14.5 Usage examples

Each feature receives focused usage evidence demonstrating its V3 public capability. Examples must not teach callers to instantiate a foreign implementation directly.

### 14.6 Repository quality gates

At each implementation task completion:

```text
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy .
uv run --frozen pytest
```

plus the repository's architecture/import-linter/composability/removal checks required by the implementation pipeline.

---

## 15. Explicit D-DATA exclusions

The pilot migration must not silently absorb the following into Data:

- broker connection/session ownership;
- broker/provider SDK public types;
- plugin discovery/lifecycle;
- composer provider selection;
- canonical instrument identity ownership;
- canonical catalogue/calendar/session identity ownership;
- platform migration orchestration;
- generic job orchestration;
- generic runtime stores;
- replay/simulation execution;
- orders, positions, account or portfolio runtime truth;
- generic Research-domain workflows that do not satisfy a Data FR;
- V2 global registries/managers as V3 architectural primitives.

---

## 16. Resolved pilot questions

### Q1. Copy V2 into `.migration/v2-data/` or inspect directly?

**Resolved:** inspect the donor directly at pinned SHA `828de8cb9546d31f91af762d3ab8adc6b1640bbd`. Do not create a donor copy.

### Q2. What is the current V2 Data inventory?

**Resolved:** Section 7.3 records the audited donor surface. It spans alignment, contracts, jobs, datasets, calendar/sessions, evidence, integrity, market data/events, persistence, replay/runtime stores, sources, SQX, synthetic generation, transformations, and legacy migrations.

### Q3. Which donor pieces are mature/well-tested?

**Resolved:** the strongest direct evidence exists around deterministic transformations/tick derivation, alignment/time rules, synthetic generation, SQX ingestion/synchronization, market-data history, dataset/persistence/lineage, integrity, calendar/sessions, and market-events behavior. Maturity is assessed per migration unit, not granted to the subsystem as a whole.

### Q4. How does donor behavior map to the fourteen V3 features?

**Resolved:** Section 9 is the initial behavior-to-feature/FR migration matrix. Every V3 feature has either a strong donor, a selective donor, or an explicit rewrite/gap decision.

### Q5. Which V2 Data responsibilities belong elsewhere?

**Resolved:** Section 8 re-homes identity/calendar truth to Catalogue, transport to Broker/Plugins, provider selection to composition, replay execution to Simulator/runtime, generic jobs to runtime/orchestration mechanisms, and generic runtime/evidence infrastructure to its correct owner.

### Q6. Which V2 types should be replaced versus requiring new contracts?

**Resolved:** existing V3 Data contracts are the first choice. V2 public types are never imported as V3 public contracts. Extend V3 Data contracts only for authoritative Data FR gaps. Cross-domain records must be defined by the owning V3 domain.

### Q7. What persistence/storage is reusable?

**Resolved:** reuse algorithms, serialization/validation ideas, lineage/provenance invariants, and tested atomicity behavior where useful. Do not automatically reuse the V2 store/registry architecture. F-DATA-07/F-DATA-11 must use explicit immutable versions/bindings/provenance and feature-owned cleanup semantics.

### Q8. What is the Data migration order?

**Resolved:** Section 12 defines five dependency waves beginning with F-DATA-04 and ending with F-DATA-14.

### Q9. How much compatibility code is acceptable?

**Resolved:** only thin V3-side adapters with V3 public contracts, no new legacy callers, no donor runtime dependency, no boundary bypass, and an explicit deletion criterion.

### Q10. When should `IMPLEMENTATION_ORDER.md` change?

**Resolved:** revise it **after this migration plan is accepted/landed and before the first Data production migration PR/task begins**. The revision should preserve its role as sequencing authority while changing the implementation method from greenfield construction to domain-by-domain brownfield migration. This planning task deliberately does not edit that file.

---

## 17. Coordination with `IMPLEMENTATION_ORDER.md`

`docs/dev/IMPLEMENTATION_ORDER.md` remains the current sequencing authority, but its greenfield framing is now stale relative to this approved migration strategy.

The next documentation-only coordination update should:

- state that product domains are implemented through the universal migration procedure in this document whenever a V2 behavioral donor exists;
- keep V3 dependency ordering authoritative;
- make D-DATA the pilot migration;
- avoid treating existing UI sequence position as a reason to finish UI before the approved Data pilot;
- point each domain stage to its domain-specific migration matrix in this document or future split-out domain annexes.

This update must occur before production Data migration begins so the two development authorities do not contradict each other.

---

## 18. First atomic Data migration task

### DATA-MIG-001 — F-DATA-04 Tick Normalization

This is the first production migration task to execute **after** the migration-plan/implementation-order coordination is accepted.

**Goal:** migrate the proven deterministic V2 tick-derivation behavior into the V3 F-DATA-04 feature boundary without importing V2 architecture.

**Donor:**

```text
HaruQuantAI-V2@828de8cb9546d31f91af762d3ab8adc6b1640bbd
app/services/data/transformation/tick_derivation.py
```

**Target:**

```text
app/services/data/tick_normalization/
├── README.md
├── __init__.py
├── manifest.py
├── config.py
├── feature.py
└── <focused tick-normalization implementation module(s)>
```

**Authoritative ownership:**

- Feature: F-DATA-04
- Capability: `data.normalize-ticks`
- FR: FR-DATA-04
- Existing public port: `TickNormalizationProvider`

**Behavior to preserve:**

- MT5 quoted-FX bid/ask normalization/derived price semantics;
- LAST/VOLUME semantics where applicable;
- real/tick volume handling represented by the current V3 contract model;
- deterministic record ordering;
- timestamp validation;
- finite-price validation;
- non-negative size/volume validation;
- existing donor error/edge-case expectations where still consistent with the V3 README.

**Architecture constraints:**

- no network/provider SDK dependency;
- no persistence;
- no Data sibling implementation imports;
- no globals/registries;
- no import-time side effects;
- no unmanaged tasks;
- public inputs/outputs use V3 Data contracts;
- Catalogue lookup only if an explicit semantic requirement cannot be represented by the typed request itself.

**Required tests/evidence:**

- port/adapt `tests/data/unit/test_tick_derivation.py` behavior cases;
- V3 provider protocol tests;
- config/manifest/feature tests;
- activation/removal/replacement cleanup tests appropriate to a pure feature;
- architecture/import-boundary test coverage;
- focused usage example through the V3 capability/public contract;
- Ruff, formatting, strict mypy, pytest, architecture/import-linter, composability/removal gates.

**Explicitly excluded from DATA-MIG-001:**

- bar aggregation;
- time alignment beyond typed timestamp validation needed by FR-DATA-04;
- persistence/datasets;
- Broker integration;
- provider routing;
- historical acquisition;
- retention;
- live streaming;
- changes to unrelated domains.

**Completion condition:** F-DATA-04 behavior is demonstrably equivalent or intentionally improved relative to the audited donor cases, while the implementation is native to V3 contracts, feature structure, lifecycle, and removability rules.

---

## 19. Domain completion audit checklist

D-DATA is complete only when all items below are true:

- [ ] All fourteen V3 Data features have a final migration classification and implementation disposition.
- [ ] Every authoritative Data FR is mapped to implemented behavior and evidence.
- [ ] No V3 Data implementation imports a V2 runtime module.
- [ ] No Data feature imports a sibling or foreign feature implementation.
- [ ] Cross-domain calls use public contracts/capability resolution.
- [ ] Catalogue remains canonical for identity/calendar/timezone facts.
- [ ] Broker/Plugin layers remain owners of connector transport/SDK lifecycle.
- [ ] All public Data records/protocols/capability keys live in `app/contracts/data/` or the correct owning-domain contract package.
- [ ] Data `__init__.py` files remain empty or docstring-only.
- [ ] No feature performs registration/I/O/task/connection work at import time.
- [ ] Managed async and `FeatureScope` ownership are proven for features with runtime work/resources.
- [ ] Durable artifact/state ownership is explicit.
- [ ] Run-bound data is immutable/version-addressed and protected from retention cleanup.
- [ ] Replacement/removal/drain behavior is tested for Regulated features.
- [ ] Relevant V2 behavioral tests/fixtures have been ported or intentionally superseded.
- [ ] V3 feature, contract, composition, lifecycle, removal, architecture and cross-domain tests pass.
- [ ] Usage examples exist for all public Data capabilities.
- [ ] Ruff, formatting, strict mypy, pytest, architecture/import-linter and repository quality gates pass.
- [ ] Temporary compatibility adapters are removed.
- [ ] Obsolete V2-only responsibilities are re-homed or explicitly dropped.
- [ ] `app/services/data/README.md` statuses and verification evidence accurately reflect reality.
- [ ] A final D-DATA migration audit confirms there is no duplicate legacy architecture hiding behind the V3 feature facade.

---

## 20. Applying this method to later domains

After D-DATA reaches completion, this document must be reviewed for process defects discovered during the pilot. Only then should the same method be applied systematically to the remaining V3 domains.

For each later domain:

1. pin its V2 donor baseline;
2. audit its exact donor behavior/test surface;
3. map behavior to the authoritative V3 Feature/FR registry;
4. classify KEEP/ADAPT/REWRITE/DROP;
5. correct V2 ownership drift instead of perpetuating it;
6. establish contract/state/composability gaps;
7. migrate in dependency-safe atomic feature units;
8. complete the domain audit before declaring the migration finished.

The purpose of the brownfield strategy is to reuse proven engineering work **without reintroducing the architectural debt that V3 was designed to remove**.
