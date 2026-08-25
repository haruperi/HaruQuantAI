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

The deliberate exception is the UI-first workstation stage. D-UI is constructed early against ratified contracts and truthful mocks so the product shape is visible from the beginning; formal D-UI completion occurs only after the real provider domains and Interfaces are available.

---

## 2. Why the implementation model changed

The waterfall model is chosen for this repository for four reasons:

1. **Conceptual completeness.** When reverse engineering or comparing StrategyQuantX behavior, newly discovered capabilities can be incorporated into the currently active domain instead of being deferred into unrelated future increments.
2. **Reduced architectural drift.** Domain boundaries, contracts, persistence, feature removability, and failure semantics are settled together before downstream consumers rely on them.
3. **Junior-executor safety.** The planner can freeze one complete domain specification and then issue small, concrete feature tasks without repeatedly reopening partially completed features across many increments.
4. **Execution parity.** Runtime Risk, Trading, and Simulator have a strict dependency relationship: HaruQuantAI uses one Trading-owned business execution lifecycle, while Simulator and Broker Connectivity provide route-specific execution authority mechanics. Completing these domains in dependency order avoids implementing a parallel simulation trading model.

This is not classic “integrate everything at the end” waterfall. **Integration happens after every domain.** The active domain is connected to all earlier real providers and the corresponding UI surfaces are de-mocked as soon as truthful provider evidence exists.

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

This file intentionally does **not** reproduce all 549 FR checkboxes. The previous duplication made the scheduling document a second mutable requirement registry and increased drift risk. Feature and FR status, evidence, and exact ordering remain in each authoritative domain README. This document records only cross-domain sequencing and domain-completion gates.

Existing completed evidence is not discarded by this rewrite. Completed `FR-*`, `FEAT-*`, whole-app contract-authoring, Composition logging, Workspace, Plugins, Interfaces, and UI-shell evidence remains authoritative where it is already recorded in the owning README, implementation, and tests.

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

A downstream optional integration is not allowed to force a completed upstream domain to remain “Partial.” The upstream domain must expose the required optional capability port and prove its own absent/provider-fixture behavior. The real cross-domain integration is verified when the downstream provider is later completed.

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
| 1 | UI-first Workstation Construction | Build the complete workstation surface against generated contracts and truthful dev mocks; D-UI remains formally open. |
| 2 | `D-WS` Workspace | Finish the complete Workspace domain and freeze it. |
| 3 | `D-PLUG` Plugins | Finish plugin lifecycle, isolation, contributions, compatibility, and removal. |
| 4 | `D-CAT` Catalogue | Finish instruments, provider mappings, sessions/calendars, trading rules, universes, currencies, and exchange. |
| 5 | `D-BRK` Broker Connectivity | Finish provider profiles, environment/session isolation, reads/events, transport, certification, and safe unavailable behavior. |
| 6 | `D-DATA` Data | Finish historical/live/external data, quality, versions, connectors, scenarios/news/events, retention, alignment, and run binding. |
| 7 | `D-STRAT` Strategy | Finish the complete typed strategy language, editors/templates, indicators, ATM, code generation, MQL5, other targets, and plugin extension contracts. |
| 8 | `D-RISK` Runtime Risk | Finish all Runtime Risk behavior before Trading. Portfolio-aware paths use an optional capability contract and provider fixtures; core Risk never hard-depends on Portfolio. |
| 9 | `D-TRD` Trading | Finish the single canonical business execution lifecycle and all SIM/PAPER/DEMO/LIVE route semantics before Simulator. |
| 10 | `D-SIM` Simulator | Finish deterministic simulation as the SIM/PAPER execution authority, using the Trading/Risk lifecycle rather than a parallel business trading model. |
| 11 | `D-ANA` Analytics | Finish result/databank/trade/operational analytics over canonical committed execution/result evidence. |
| 12 | `D-RES` Research | Finish robustness, optimization, walk-forward, Builder/evolution, acceptance, AI/neural, drift, and research control. |
| 13 | `D-PORT` Portfolio | Finish portfolio construction/simulation/search/risk/Markowitz/merge methods, then prove real Portfolio -> optional Runtime Risk integration without reopening core Risk ownership. |
| 14 | `D-ORCH` Orchestration | Finish durable projects/tasks/conditions/domain delegation/utilities/history/training workflows over the completed business domains. |
| 15 | `D-IFACE` Interfaces | Finish HTTP/events/CLI/MCP/research/project/portfolio/trading/admin gateways against the completed application capability set. |
| 16 | `D-UI` Finalization and Complete-System Integration | Remove remaining mocks, finish every D-UI feature, run all system workflows, hosted/local parity, and final release gates. |

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
```

`Broker Connectivity` is deliberately early. Data consumes broker/provider evidence, Runtime Risk consumes broker/account evidence, and Trading should be designed against its real external execution-authority boundary before Simulator implements the simulated authority. Completing Broker early does **not** enable live trading; operational mutation remains disabled by default and release-gated.

---

## 6. Stage 0 — Preserve the implemented foundation

**Status:** Baseline implemented; preserve and extend only through approved contracts/composition mechanisms.

Preserve:

- `app/contracts/` as the physical public application/domain contract boundary;
- `app/kernel/` composability primitives;
- `app/composition/` discovery, dependency resolution, effects, lifecycle, replacement, readiness, diagnostics, and structured logging;
- Python `haruquantai.features` discovery;
- strict TOML configuration;
- capability snapshots and exact removal semantics.

Already completed foundation work includes Composition-owned structured logging and whole-app contract authoring/generation. Their existing evidence remains valid and shall not be recreated as new product features.

**Exit gate:** Existing architecture/composition/contracts/removal suites remain green and no later stage introduces a second lifecycle, registry, effect framework, or private cross-domain implementation import.

---

## 7. Stage 1 — UI-first workstation construction

**Status:** Horizontal exception; does not constitute formal D-UI completion.

The UI is intentionally first because it defines the workstation experience and gives every later domain a concrete consumer to integrate with.

Stage 1 shall:

1. preserve the already implemented D-UI compose shell and existing D-IFACE/Workspace/Plugins foundation evidence;
2. finish the typed widget registry/host, Dockview adapter, layout schema, temporal context, generated-client boundary, accessibility/focus foundation, and dev-only mock provider;
3. construct the complete planned feature-owned widget surface against ratified generated contracts;
4. label every mock-derived dataset, result, metric, event, readiness state, and trading view as non-authoritative;
5. ensure mock-backed behavior claims **no backend FR completion** merely because the visual workflow exists;
6. make every widget capability-aware so missing/removable providers produce explicit unavailable/degraded states;
7. retain exact cleanup/removal and temporal subscription disposal behavior.

Formal D-UI completion remains Stage 16 because `Interfaces -> UI` is the real dependency direction. Stage 1 is therefore a presentation/construction exception, not a false dependency claim.

---

## 8. Stage 2 — Workspace

Complete every Workspace feature in the authoritative [Workspace README](../../app/services/workspace/README.md).

Existing completed Workspace features remain completed. The active stage closes the remaining Workspace capability set, including worker distribution and hosted-workspace behavior, so later domains can rely on one stable workspace/job/artifact/runtime substrate.

**Special gate:** local and hosted behavior may be implemented now but hosted release can remain separately gated by `PROJECT.md`. Implementation order does not equal deployment enablement order.

---

## 9. Stage 3 — Plugins

Complete every Plugins feature in the authoritative [Plugins README](../../app/services/plugins/README.md).

Existing manifest/contribution work remains valid. Finish lifecycle replacement, sandbox/permission boundaries, analysis isolation, result panels, compatibility, secrets, and physical-removal behavior before product domains begin depending on extension points.

---

## 10. Stage 4 — Catalogue

Complete every Catalogue feature in the authoritative [Catalogue README](../../app/services/catalogue/README.md).

Catalogue becomes the stable authority for instruments, provider identities/mappings, sessions/calendars, trading rules, cost definitions, universes, and currency topology before Broker/Data/Trading consumers are implemented.

---

## 11. Stage 5 — Broker Connectivity

Complete every Broker Connectivity feature in the authoritative [Broker README](../../app/services/broker/README.md).

Broker Connectivity owns transport/provider truth only. It does not own risk admission or the Trading business lifecycle.

Required completion characteristics:

- certified provider capability contracts;
- environment/account/session isolation;
- provider state reads and normalized events;
- order transport with accepted/rejected/unknown classification;
- no blind retry after uncertain mutation outcome;
- credential and provider internals confined to the adapter boundary;
- demo/live mutation disabled unless the independent operational release gates authorize it.

Its early implementation supplies real provider/account evidence to Data and Risk and a real external execution-authority boundary to Trading.

---

## 12. Stage 6 — Data

Complete every Data feature in the authoritative [Data README](../../app/services/data/README.md).

This stage includes the complete planned Data domain rather than only historical onboarding: ingestion, QuantData, ticks, quality, aggregation, retention, alignment, profile sources, external indicators, run data binding, connectors, synthetic scenarios, news, live events, and lineage.

De-mock all UI data surfaces whose complete provider set now exists.

---

## 13. Stage 7 — Strategy

Complete every Strategy feature in the authoritative [Strategy README](../../app/services/strategy/README.md).

The Strategy domain is intentionally finished in one conceptual pass: AST/types, block catalogue, charts, versioning, templates, exchange/import, architectures/random groups, indicators, ATM, deterministic code generation, MQL5 parity tooling, additional target contracts, and plugin nodes.

When StrategyQuantX comparison reveals a useful Strategy-owned capability, resolve it here before declaring the domain complete rather than scheduling it as an unrelated later increment.

---

## 14. Stage 8 — Runtime Risk

Complete every Runtime Risk feature in the authoritative [Runtime Risk README](../../app/services/risk/README.md).

Runtime Risk is the non-bypassable admission authority for executable Trading actions, including simulation-parity execution where configured.

### Portfolio independence rule

Portfolio is **not** a hard prerequisite of Runtime Risk.

Portfolio-aware allocation/budget features must be fully implemented at this stage against:

- versioned optional Portfolio capability contracts;
- deterministic provider fixtures/conformance doubles;
- explicit absent-provider behavior.

The physical absence of `D-PORT` must leave base Risk and single-strategy/account admission healthy. When Portfolio becomes real at Stage 13, that stage proves the production Portfolio<->Risk integration without redefining Risk ownership or reopening the completed core domain.

---

## 15. Stage 9 — Trading

Complete every Trading feature in the authoritative [Trading README](../../app/services/trading/README.md).

The governing invariant is:

> **One Trading lifecycle, multiple execution authorities.**

Trading owns canonical executable-plan normalization, operation/order/position lifecycle semantics, common business/risk gate order, authority selection, idempotency, receipt classification, protections, reconciliation, journals, ledgers, and public action behavior.

At this stage:

- `DEMO`/`LIVE` authority behavior integrates with the already-completed Broker domain but remains release-disabled unless operational gates authorize it;
- `SIM`/`PAPER` authority ports are implemented and verified with deterministic authority conformance fixtures because the real Simulator provider is the next stage;
- absence of Simulator must make only Simulator-backed authority routes unavailable, not break Broker-backed Trading behavior;
- Trading must not contain Simulator matching/fill mechanics or Broker SDK/provider transport.

Trading is declared complete before Simulator so the Simulator cannot invent a parallel business execution model.

---

## 16. Stage 10 — Simulator

Complete every Simulator feature in the authoritative [Simulator README](../../app/services/simulator/README.md).

Simulator owns deterministic authority mechanics and result production, including run manifests, engine/precision profiles, scheduler time, matching, intrabar behavior, spread/slippage/commission/swap models, checkpoints, perturbation, distribution, Stockpicker/profile simulation, and parity evidence.

Simulator does **not** own a competing canonical trading lifecycle.

Any retained `SimOrder`, `SimFill`, `SimPosition`, or `SimTrade` records are authority/result-scoped evidence. Canonical business order/deal/position state remains Trading-owned. Executable simulation actions must traverse the common Runtime Risk -> Trading path and return Simulator authority evidence through the versioned execution-authority boundary.

**Mandatory integration gate:** prove that replacing the execution authority changes matching/time/transport mechanics but not the Trading business state machine or common risk-gate sequence.

---

## 17. Stage 11 — Analytics

Complete every Analytics feature in the authoritative [Analytics README](../../app/services/analytics/README.md).

Analytics operates on committed Simulator/Trading evidence and owns databanks, metrics, result interpretation, trade analysis, comparisons, bulk membership, custom panels, and operational qualification. It must not reconstruct a second execution authority or silently reinterpret unresolved Trading state as final execution truth.

---

## 18. Stage 12 — Research

Complete every Research feature in the authoritative [Research README](../../app/services/research/README.md).

This is one complete research-factory stage: manual/repeatable research runs, robustness, Monte Carlo/scenarios, optimization, walk-forward, Builder/evolution, acceptance, budgets, Stockpicker, AI assistance, neural research, portfolio-fitness scoring, and drift/intelligence.

The Simulator/Analytics substrate is already complete, so StrategyQuantX-inspired research concepts can be evaluated and incorporated without reopening the engine foundation for every incremental research feature.

---

## 19. Stage 13 — Portfolio

Complete every Portfolio feature in the authoritative [Portfolio README](../../app/services/portfolio/README.md).

After the domain itself passes its completion gate, run the deferred real optional-integration proof against the already-completed Runtime Risk domain:

- Portfolio allocation/exposure/rebalance evidence is accepted only through the ratified optional capability boundary;
- removing Portfolio withdraws only portfolio-aware Risk capability;
- single-strategy/account Runtime Risk and Trading remain healthy;
- no reverse implementation import or direct foreign-state write is introduced.

This verification is a cross-domain integration gate, not a second Risk implementation stage.

---

## 20. Stage 14 — Orchestration

Complete every Orchestration feature in the authoritative [Orchestration README](../../app/services/orchestration/README.md).

By this point all core business domains exist, so project graphs, durable task attempts/checkpoints, domain delegation, utility/notification tasks, history, and network-training orchestration can be built against stable capabilities instead of placeholder product behavior.

---

## 21. Stage 15 — Interfaces

Complete every Interfaces feature in the authoritative [Interfaces README](../../app/services/interfaces/README.md).

Early D-IFACE foundation work remains valid. This stage finishes the real HTTP/events/CLI/MCP/research/project/portfolio/trading/admin gateway set against completed domains and proves transport semantic parity, capability withdrawal, authentication/authorization, pagination/concurrency/idempotency, and physical removal.

Interfaces must delegate business behavior; they do not become a second application/domain policy layer.

---

## 22. Stage 16 — Final D-UI completion and system integration

Complete every User Interface feature in the authoritative [UI README](../../app/ui/README.md).

Stage 16 retires the horizontal exception:

1. remove every remaining production dependency on `app/ui/src/mocks/`;
2. connect every feature-owned widget to real D-IFACE/public capabilities;
3. prove spatial layout, temporal context, stale/gap/resync, accessibility, keyboard/focus, error, unavailable, replacement, and live-removal behavior;
4. execute all system workflows from the UI and through equivalent nonvisual/automation interfaces;
5. verify local/hosted contract parity where the hosted profile is enabled;
6. run the complete release/removal/NFR matrix.

D-UI is **DOMAIN COMPLETE — FROZEN BASELINE** only here.

---

## 23. Cross-domain integration rule

A completed domain is not casually reopened because a later provider appears.

Instead:

- earlier domains expose exact versioned required/optional capability contracts;
- required dependencies must exist before domain completion;
- future optional providers are tested with fixtures and explicit absence behavior;
- when the real downstream provider is implemented, its stage owns the production integration proof;
- any discovered incompatibility is treated as an explicit contract change with versioning/migration, not an undocumented backdoor edit.

This preserves domain waterfall discipline without sacrificing HaruQuantAI's spatiotemporal composability.

---

## 24. UI de-mock rule

Stage 1 may build any UI workflow against the dev-only mock provider, but mocks carry no business-authority claim.

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

HaruQuantAI implementation is complete only when:

1. Stage 0 foundation guarantees remain green;
2. all 15 authoritative domain READMEs report every planned feature/FR complete with executable evidence;
3. all public contracts and generated clients are version-consistent;
4. every domain passed its domain completion/removal gate in waterfall order;
5. the unified Runtime Risk -> Trading -> execution-authority architecture is proven for SIM/PAPER/DEMO/LIVE without a parallel Simulator business lifecycle;
6. all twelve system workflows pass;
7. all applicable system NFR and release gates pass;
8. every mock provider is absent from production behavior;
9. local/hosted and interface parity gates pass where applicable;
10. no unresolved architecture decision, duplicate requirement registry, hidden fallback, or unowned public behavior remains.

The intended end state is not merely “all code written.” It is a chain of completed, independently removable, contract-stable domain baselines whose composition reproduces the complete HaruQuantAI product.