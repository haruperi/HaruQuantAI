# Implementation Plan: StrategyQuant X Clean-Room Product Specification

> **Task ID:** `DOC-SQX-001`
> **Iteration:** `1`
> **Branch:** `main`
> **Baseline Commit:** `f9fcd14`

This plan covers evidence collection and documentation only. It does not authorize
implementation of the documented product features, external trading, credential use,
or publication of proprietary artifacts.

---

### User Review Required

> [!IMPORTANT]
> The documentation will keep three independent dimensions explicit:
>
> 1. **Reference behavior** — what StrategyQuant X build `144.2953` does.
> 2. **Evidence confidence** — `Confirmed`, `High confidence`, `Medium confidence`,
>    `Low confidence`, or `Unverified`, plus `observed`, `inferred`, or `speculative`.
> 3. **HaruQuantAI implementation state** — `Missing`, `Partial`, or `Completed`.
>
> A behavior observed in StrategyQuant X will therefore not be marked `Completed` in
> HaruQuantAI unless repository code and tests prove that status. Gateway's existing
> implemented behavior will be preserved and distinguished from newly specified work.

> [!IMPORTANT]
> The clean-room boundary permits public documentation, black-box observations, local
> metadata/resources, schemas, templates, and decompiled output as evidence. It forbids
> copying proprietary expression into the reimplementation specification. Decompiled
> code will be treated as fallible evidence, reduced to externally testable contracts,
> and corroborated before supporting a `Confirmed` conclusion.

> [!IMPORTANT]
> The user-provided target stack is normative for HaruQuantAI. Java, Electron, Swing,
> Jetty, and other technologies found in the StrategyQuant X installation will be
> recorded only as reference-product evidence, not adopted automatically.

> [!IMPORTANT]
> Dynamic analysis, when static/public evidence is insufficient, will be bounded to
> read-only or disposable test workflows. It will not place trades, connect real broker
> accounts, alter licenses, transmit credentials, or intentionally modify personal
> projects/data. Product-generated logs and settings will be treated as sensitive.

### Open Questions

> [!NOTE]
> - NONE. The supplied scope, target version, domain model, target stack, and clean-room
>   constraints are sufficient to begin after owner approval.

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal:** Replace the generic project documentation and skeletal
  domain registries with a source-backed, implementation-ready clean-room specification
  of StrategyQuant X, mapped into HaruQuantAI's 17 fixed domains and target stack.
- **Reference target:** StrategyQuant X build `144.2953`. The local folder name is
  `C:\SQX_144_2953_win_20260601`; the official download page identifies build
  `144.2953` as released on 20 May 2026. The local June 1 folder date will be recorded
  as packaging/install context, not as the upstream release date.
- **Primary audience:** Technical product, architecture, quantitative-engineering, and
  implementation teams performing an independent clean-room reimplementation.
- **Knowledge depth:** Deep. Completion requires product-, module-, component-,
  algorithm-, data-, runtime-, and validation-level coverage, with material unknowns
  and validation protocols stated rather than guessed.
- **Research mode:** Descriptive specification after a bounded exploratory inventory.
  Canonical sources are ranked: exact-version reproducible behavior and local artifacts;
  version-relevant official documentation; bundled public examples/help; then secondary
  context. Search snippets are discovery only, never final evidence.
- **Ratified Requirements:**
  - Document system purpose, actors, screens, modules, workflows, state machines,
    errors, validation, algorithms, formulas, data/storage formats, interfaces,
    integrations, runtime topology, background jobs, exports, and non-functional
    behavior.
  - Recover initialization, ordering, rounding, comparison, precision, gating,
    rejection, retry, and failure semantics wherever evidence supports them.
  - Inspect the plugin/snippet system, internal XML strategy representation, Java
    snippet contracts, and FreeMarker export templates without reproducing proprietary
    source expression.
  - Map every material capability to exactly one of the 17 owner domains:
    `workspace`, `persistence`, `brokers`, `data`, `indicator`, `strategy`, `risk`,
    `analytics`, `trading`, `simulator`, `optimization`, `robustness`, `portfolio`,
    `research`, `gateway`, `ui`, and `agentic`.
  - Preserve the repository's modular-monolith rules: pure contracts, feature ownership,
    capability-based collaboration, managed effects, and persistence boundaries.
  - Define build-ready feature registries, requirement IDs, public capability contracts,
    configuration/limits, state semantics, acceptance tests, and removal behavior.
  - Include diagrams for system architecture, domain dependencies, major data/event
    flows, and cross-domain workflows when they materially clarify relationships.
  - Record evidence source, method, confidence, finding type, limitations, assumptions,
    unknowns, and suggested validation for each major finding.
- **Completion criteria:**
  - `docs/PROJECT.md` describes the complete target product and cross-domain workflows.
  - `docs/ARCHITECTURE.md` defines the requested target stack and universal clean-room
    runtime, persistence, numerical, isolation, and deployment constraints.
  - Every domain README contains a non-placeholder feature/requirement registry and
    normative domain specification at the strength supported by evidence.
  - No target behavior is mislabeled as implemented, no material claim lacks evidence
    or an explicit unknown, and no proprietary source expression or secret is copied.
  - Cross-file ownership, IDs, dependencies, terminology, and implementation statuses
    are internally consistent.
- **Usage Evidence:** This is a documentation-only task and creates no backend feature;
  therefore a new `tests/examples/` usage harness is not applicable. The deliverable's
  operational evidence is a set of deterministic acceptance-test specifications and
  validation matrices embedded in the owning domain READMEs.
- **Report surface:** The repository Markdown documentation suite is the requested
  durable technical report. No separate HTML, dashboard, or hosted report will be
  created unless the owner requests one later.

## 2. Files Read (Audit Trail)

### Repository authority and templates

- [AGENTS.md](../AGENTS.md) — contributor authority, plan/approval/walkthrough gates,
  write constraints, and verification requirements.
- [implementation-plan.md](templates/implementation-plan.md) — mandatory eight-section
  plan structure and `ALLOWED_WRITE_PATHS` contract.
- [walkthrough.md](templates/walkthrough.md) — required post-implementation handoff.
- [PROJECT.md](PROJECT.md) — current generic system scope, status vocabulary,
  composition workflows, and system verification authority.
- [ARCHITECTURE.md](ARCHITECTURE.md) — current modular-monolith invariants, lifecycle,
  persistence, and verification boundaries.
- [feature_implementation_pipeline.md](dev/feature_implementation_pipeline.md) — named
  authoritative implementation controls referenced by the repository constitution.
- [domain_implementation_audit.md](dev/domain_implementation_audit.md) — domain audit
  and status/evidence expectations referenced by the repository constitution.

### Existing domain registries

- [Workspace README](../app/services/workspace/README.md) — job/settings/licensing and
  notification boundary; currently a `Missing` scaffold.
- [Persistence README](../app/services/persistence/README.md) — infrastructure,
  databank, membership, ranking, and move/copy boundary; currently a scaffold.
- [Brokers README](../app/services/brokers/README.md) — external-provider adapter and
  availability boundary; currently a scaffold.
- [Data README](../app/services/data/README.md) — instruments, sessions, datasets,
  imports, providers, and quality boundary; currently a scaffold.
- [Indicator README](../app/services/indicator/README.md) — deterministic indicators
  and building blocks boundary; currently a scaffold.
- [Strategy README](../app/services/strategy/README.md) — strategy representation,
  generation, evolution, authoring, and export boundary; scaffold read in full.
- [Risk README](../app/services/risk/README.md) — sizing, stops, targets, trailing,
  break-even, and scale-out boundary; currently a scaffold.
- [Analytics README](../app/services/analytics/README.md) — metric registry, equity,
  drawdown, trades, and reporting boundary; currently a scaffold.
- [Trading README](../app/services/trading/README.md) — shared execution-session and
  execution-policy boundary; currently a scaffold.
- [Simulator README](../app/services/simulator/README.md) — backtest, matching, fills,
  costs, account state, and precision boundary; currently a scaffold.
- [Optimization README](../app/services/optimization/README.md) — parameter ranges,
  trials, search, sequential optimization, and schedules boundary; scaffold.
- [Robustness README](../app/services/robustness/README.md) — stress, Monte Carlo,
  walk-forward, acceptance, and verdict boundary; currently a scaffold.
- [Portfolio README](../app/services/portfolio/README.md) — membership, weights,
  correlation, shared capital, and portfolio artifacts boundary; scaffold.
- [Research README](../app/services/research/README.md) — ordered tasks, routing,
  loops, and reproducible research pipelines boundary; currently a scaffold.
- [Gateway README](../app/services/gateway/README.md) — implemented FastAPI/Uvicorn
  feature, contracts, tests, and current normative endpoints; read in full.
- [UI README](../app/services/ui/README.md) — workstation composition boundary;
  currently a scaffold.
- [Agentic README](../app/services/agentic/README.md) — AI/LLM boundary; scaffold.

### Initial local-install evidence inspected

- `C:\SQX_144_2953_win_20260601\` — top-level executables, embedded runtime,
  installation folders, bundled PDF, and configuration files.
- `internal\plugins\` — 193 top-level plugin directories, including application shells,
  builders, retesters, optimization, cross-checks, data sources, results, task settings,
  servlets, portfolio tools, and exporters.
- `internal\libs\` — 261 JARs in the install overall, including SQ domain libraries,
  Jetty, SQLite JDBC, H2, FreeMarker, Apache POI, Reactor, Artemis, TA-Lib, and UI/runtime
  dependencies; dependency presence is evidence, not proof of exercised behavior.
- `internal\ctemplate\` — XML building-block, event, condition, action, parameter-set,
  money-management, and wizard configuration resources.
- `internal\web\` — embedded web applications for Builder, Retester, Optimizer,
  Results, AlgoWizard, Portfolio tools, Task Manager, Data Manager, and related screens.
- `internal\web\SQWIZARD\branding\global\config.xml` — building-block metadata,
  parameter constraints, display/help text, and strategy editor schema evidence.
- `internal\plugins\Task*\task*.xml` — workflow task schemas and defaults for build,
  retest, optimize, routing, filtering, notifications, files, and automated portfolios.
- `StrategyQuantX.config` and `sqcli.config` — Java launch options and 4 GiB initial heap.
- `user\` and `internal\license.db` — existence and high-level layout only; content is
  excluded from research unless separately proven to be non-sensitive bundled sample data.

### Initial official/public evidence inspected

- [StrategyQuant download page](https://strategyquant.com/download) — build `144.2953`
  and 20 May 2026 release date.
- [What's new in StrategyQuant](https://strategyquant.com/whatsnew/) — build 144 feature
  context, including custom result analysis, volume profile/TPO, and initial MCP support.
- [Programming introduction](https://strategyquant.com/doc/programming-for-sq/introduction-2/)
  — plugin/snippet distinction, Java snippets, internal XML representation, and
  FreeMarker translation model.
- [Adding indicators and signals](https://strategyquant.com/doc/programming-for-sq/adding-indicators-and-signals/)
  — bar-update contracts, initialization behavior, CCI formula details, rounded signal
  comparison, and parameter annotations.
- [Cross checks](https://strategyquant.com/doc/strategyquant/cross-checks-automated-strategy-robustness-tests/)
  — ordered robustness funnel, dismissal gating, higher-precision retest, and cost impact.
- [Envelopes indicator](https://strategyquant.com/doc/programming-for-sq/adding-envelopes-indicator-step-by-step/)
  — XML block representation and per-target FreeMarker call templates.
- `C:\SQX_144_2953_win_20260601\Extending_SQX.pdf` — bundled official extension guide;
  identified for full extraction during execution.

## 3. Proposed Changes & Implementation Order

### Research and evidence normalization

- `[ANALYZE]` Local installation — build a bounded artifact inventory by file role,
  archive/package, plugin, UI surface, configuration, schema, template, and runtime unit.
- `[ANALYZE]` Java/JAR metadata — enumerate manifests, packages, public symbols, class
  relationships, and call/dependency evidence. Decompile only targeted classes needed to
  close behavioral contracts; record tool/version and uncertainty.
- `[ANALYZE]` Web resources — reconstruct screen inventory, navigation, form fields,
  tables, charts, job progress, and local HTTP/WebSocket/servlet contracts from readable
  assets and bounded black-box observations.
- `[ANALYZE]` XML/snippet/template resources — recover configuration schemas, strategy
  representation, initialization/rounding/comparison rules, generation grammars, and
  export transformations at a clean-room behavioral level.
- `[ANALYZE]` Storage/runtime evidence — identify database/file formats, processes,
  ports, worker/thread behavior, queues, scheduling, recovery, logging, and resource
  lifecycle without opening credential or personal-data payloads.
- `[VERIFY]` Official/public documentation — corroborate every major product contract,
  record version/date/applicability, and retain contradictions or version drift explicitly.
- `[OBSERVE]` Bounded dynamic workflows — launch only when needed to close material gaps;
  exercise bundled/sample projects and safe edge cases, observe UI/process/files/network,
  and avoid real external mutations.

### System-level documentation

- `[MODIFY]` [docs/PROJECT.md](PROJECT.md) — replace generic product framing with the
  HaruQuantAI system purpose, 17-domain registry, actors, end-to-end workflows, external
  systems, system requirements, target delivery phases, evidence/status model, and
  system definition of done. Keep domain internals in owning READMEs.
- `[MODIFY]` [docs/ARCHITECTURE.md](ARCHITECTURE.md) — retain valid modular-monolith
  invariants and add the ratified React/FastAPI/Python/NumPy/Numba/SQLite/Parquet target
  topology; define process, lifecycle, job ledger, IPC, WebSocket, numerical determinism,
  persistence, external adapter, security, and deployment constraints.

### Domain specifications

- `[MODIFY]` [Workspace README](../app/services/workspace/README.md) — jobs, scheduler,
  pause/resume/cancel/recovery, settings, licensing/editions, logs, notifications, and
  operational state machines.
- `[MODIFY]` [Persistence README](../app/services/persistence/README.md) — SQLite and
  artifact infrastructure, databanks, reference memberships, deduplication, ranking,
  dismissal, copy/move, schemas, and retention.
- `[MODIFY]` [Brokers README](../app/services/brokers/README.md) — actual provider
  profiles/adapters, capability discovery, connection/session contracts, failure modes,
  and MT5/cTrader target boundaries without trading policy.
- `[MODIFY]` [Data README](../app/services/data/README.md) — instruments, sessions,
  calendars, time zones, OHLCV/ticks, imports, providers, transformations, data quality,
  futures/corporate actions, and Parquet dataset contracts.
- `[MODIFY]` [Indicator README](../app/services/indicator/README.md) — indicator registry,
  series/buffer semantics, warm-up/initialization, rounding, caching, update contracts,
  custom indicator interfaces, and verified formulas.
- `[MODIFY]` [Strategy README](../app/services/strategy/README.md) — canonical strategy
  AST/model, events/rules/actions/parameters/templates, generation grammar, genetic
  evolution, AlgoWizard, snippets, XML, and export configuration.
- `[MODIFY]` [Risk README](../app/services/risk/README.md) — position sizing, policy,
  stops/targets, trailing, break-even, scale-outs, rounding, constraints, and failure cases.
- `[MODIFY]` [Analytics README](../app/services/analytics/README.md) — one metric registry,
  formulas and conventions, equity/drawdown/trade analysis, projections, reports,
  precision, denominators, and export contracts.
- `[MODIFY]` [Trading README](../app/services/trading/README.md) — shared order/position
  state machines, execution-session boundary, authorization, reconciliation, idempotency,
  and simulator/demo/live policy semantics.
- `[MODIFY]` [Simulator README](../app/services/simulator/README.md) — backtest event model,
  precision modes, matching/fills, spread/slippage/commission/margin, account/trade
  lifecycle, multi-symbol ordering, and reproducibility.
- `[MODIFY]` [Optimization README](../app/services/optimization/README.md) — parameter
  spaces, exhaustive/random/genetic trials, objective/scoring contracts, sequential
  optimization, walk-forward schedules, cancellation, and artifacts.
- `[MODIFY]` [Robustness README](../app/services/robustness/README.md) — ordered cross-check
  funnel, Monte Carlo variants, perturbations, additional markets, higher precision,
  walk-forward/WFM, acceptance gates, verdicts, and early rejection.
- `[MODIFY]` [Portfolio README](../app/services/portfolio/README.md) — membership and
  weights, correlation, portfolio search, shared capital/margin, constraints, and clear
  artifact-type semantics.
- `[MODIFY]` [Research README](../app/services/research/README.md) — project/task graph,
  routing, jump/wait/loop conditions, reproducibility, run evidence, automation, and
  recovery semantics.
- `[MODIFY]` [Gateway README](../app/services/gateway/README.md) — preserve verified
  implemented endpoints; specify business-logic-free REST/OpenAPI/WebSocket/SSE/auth,
  DTO, pagination, error, versioning, and UI orchestration boundaries needed by domains.
- `[MODIFY]` [UI README](../app/services/ui/README.md) — screen/navigation inventory,
  Dockview workspace, tables/charts, forms, progress/notifications, accessibility,
  saved layouts, and domain-owned visual contribution contracts.
- `[MODIFY]` [Agentic README](../app/services/agentic/README.md) — optional LLM providers,
  tool contracts, structured outputs, evidence/context, guardrails, approvals, token
  budgets, and strict separation from deterministic quantitative authority.

### Delivery record

- `[NEW]` [docs/walkthrough.md](walkthrough.md) — post-execution summary, evidence and
  verification results, deviations/residuals, working-tree status, and proposed commit
  message, following the repository template.

### Sequential Implementation Order

1. Freeze the source/version boundary and create a research charter/evidence-ID scheme.
2. Inventory local artifacts and official pages; classify evidence by source role and access.
3. Analyze public behavior and user workflows first, then external interfaces and data.
4. Analyze modules/dependencies, algorithms, background processing, extensions, UI,
   performance, security, and packaging in the user's priority order.
5. Use bounded dynamic tests only for material gaps left by static and official evidence.
6. Draft the system domain map and cross-domain workflows in `docs/PROJECT.md`.
7. Draft universal target constraints and topology in `docs/ARCHITECTURE.md`.
8. Populate domain READMEs in dependency order: Data/Indicator/Strategy/Risk/Trading/
   Simulator/Analytics, then Optimization/Robustness/Portfolio, then Workspace/
   Persistence/Research/Brokers/Gateway/UI/Agentic, reconciling cross-domain contracts.
9. Perform an evidence review: unsupported claims, citation mismatches, contradictions,
   version drift, causality overreach, clean-room leakage, and missing validation tests.
10. Run documentation and repository verification, then author `docs/walkthrough.md`.

## 4. Dependencies and Contracts

- **Repository authorities:** `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`,
  `docs/dev/feature_implementation_pipeline.md`, and each owning domain README remain
  authoritative in their declared scopes.
- **Target-stack contracts:** React/TypeScript/Vite/Tailwind and Dockview own client
  composition; FastAPI/Pydantic/Uvicorn own transport; framework-independent Python
  feature modules own policy; NumPy/Numba own numerical kernels; SQLite owns
  transactional state; Parquet/PyArrow own bulk numerical artifacts; processes and
  bounded IPC queues own background work; WebSocket is the primary bidirectional event
  channel; SSE is optional and justified per endpoint.
- **Boundary rule:** Gateway and UI orchestrate but do not calculate quantitative results.
  Brokers connect but do not own trading decisions. Simulator produces execution facts;
  Analytics computes metrics from those facts. Robustness owns acceptance verdicts but
  delegates simulation and optimization work through typed capabilities.
- **Contract form:** Each cross-domain operation will specify request/result DTOs,
  capability keys, events, idempotency/cancellation semantics, validation, error taxonomy,
  versioning, and availability behavior. Proposed Python symbol names will be generic and
  clean-room safe.
- **Persistence boundary:** Schemas, SQL, migrations, and transactions remain in
  `app/services/persistence/<domain>.py`; domain READMEs describe semantic ownership and
  public repository contracts rather than authorize direct connections.
- **Evidence contract:** Every major finding carries source locator, method, finding type,
  confidence, version applicability, limitations/contradictions, and a validation test or
  explicit statement that no further test is required.
- **External evidence:** Only official StrategyQuant sources will establish intended
  product behavior. Third-party libraries' own official documentation may establish
  library semantics, but dependency presence alone will not prove SQX behavior.

## 5. Blockers, Risks, and Trade-offs

- **Scale risk:** The install contains more than 9,000 internal files, 193 plugin
  directories, 261 JARs, and thousands of templates/scripts. Exhaustiveness will be
  defined by a recorded artifact boundary and coverage matrix, not by claiming every byte
  was semantically reconstructed.
- **Version drift:** Many official programming pages predate build 144. Findings from
  older docs require exact-version local corroboration or a reduced confidence level.
- **Decompiler uncertainty:** Optimizations, obfuscation, synthetic constructs, missing
  metadata, and renaming can distort recovered code. Important contracts require a second
  source or reproducible behavior.
- **Behavioral side effects:** Launching the product may update logs, settings, caches,
  or license state. Dynamic work will use backed-up/disposable state where feasible and
  will record mutations; no destructive cleanup will be performed without authorization.
- **Sensitive/local data:** `license.db`, user projects, strategies, datasets, logs, and
  credentials may be personal or secret. They are excluded by default; only filenames,
  schemas, or explicitly bundled sample fixtures may be used when safe.
- **Network risk:** Product startup may contact licensing, update, telemetry, data, or
  broker services. Network observation will be passive or locally isolated; no external
  mutation or credential submission is authorized.
- **Numerical parity risk:** Formula names alone are insufficient. Warm-up, missing data,
  ordering, time zones, floating-point precision, tick/bar policy, rounding, comparison,
  random seeds, and rejection order must be specified or marked unresolved.
- **Documentation/code mismatch:** Existing repository changes are uncommitted and
  Gateway is implemented while other domains are scaffolds. Documentation will preserve
  verified code truth and report conflicts instead of normalizing them silently.
- **Breadth versus certainty:** It is preferable to leave a precise `Unverified` row with
  a reproducible test protocol than to fill a requested area with unsupported detail.

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In Scope:**
  - Static inspection of the named local installation and its bundled documentation.
  - Targeted archive, manifest, symbol, configuration, resource, schema, string,
    dependency, class-hierarchy, control-flow, and data-flow analysis.
  - Official/public StrategyQuant documentation relevant to build 144 behavior.
  - Safe black-box and grey-box observation needed to close material contract gaps.
  - Clean-room algorithms expressed as formulas, pseudocode, invariants, fixtures, and
    acceptance tests rather than copied proprietary implementation.
  - The requested system/architecture/domain Markdown documentation and walkthrough.
- **Out of Scope / Non-Goals:**
  - Implementing any specified HaruQuantAI feature or changing Python/TypeScript code.
  - Copying proprietary Java/JavaScript/template source or vendor-specific identifiers
    when a generic behavioral term suffices.
  - Circumventing licensing, authentication, encryption, access controls, or technical
    protection measures.
  - Reading or publishing credentials, license contents, personal strategies/projects,
    or private market data.
  - Connecting real broker accounts, placing/cancelling orders, purchasing data, or
    changing external services.
  - Claiming byte-for-byte, performance, or numerical parity without reproducible tests.
  - Selecting implementation libraries beyond the user's ratified stack unless a real
    architectural blocker is documented for owner decision.

## 7. Verification Plan

### Evidence and documentation checks

- Confirm build/version sources and record retrieval date and local artifact identifiers.
- Validate every material finding against at least one primary source; high-impact
  algorithm/runtime claims require corroboration or an explicit lower confidence.
- Search all edited documents for unresolved scaffold tokens such as `[feature]`,
  `[DOM]`, `[Purpose]`, `[Requirement]`, `[setting]`, and placeholder IDs.
- Check that every feature/requirement ID is unique, every cross-domain dependency names
  a public contract, and every workflow participant has exactly one owning domain.
- Check that each domain README contains source/method/confidence/validation evidence and
  does not mark unimplemented work as completed.
- Check relative Markdown links and local source locators; open sampled official links.
- Inspect every Mermaid diagram for ownership direction and consistency with the prose.
- Review terminology for proprietary-name leakage and normalize names unless the vendor
  term is necessary to identify evidence or interoperability.

### Automated Tests

- Documentation-focused checks:
  ```powershell
  git diff --check -- docs/PROJECT.md docs/ARCHITECTURE.md app/services/*/README.md docs/walkthrough.md
  rg -n "\[(feature|DOM|Purpose|Requirement|setting|capability-name|ProtocolName)" docs/PROJECT.md docs/ARCHITECTURE.md app/services/*/README.md
  ```
- Candidate repository qualification, run once after documentation is complete:
  ```powershell
  uv run python scripts/ci_check.py
  ```
- Any failure caused by the pre-existing dirty worktree will be isolated and reported;
  it will not be silently fixed outside the approved documentation paths.

### Usage Evidence Run

- No new runtime feature is implemented. Instead, execute or specify bounded reference
  scenarios for: strategy generation/filtering, low-to-high precision retest, Monte Carlo,
  walk-forward, optimization, portfolio assembly, research task routing, export, job
  pause/resume/cancel/recovery, and gateway/UI progress events.
- Where execution is unsafe or unavailable, label the scenario `Not executed` and retain
  its inputs, expected observations, pass criteria, and required environment.

### Quality Pipeline

- Full verification suite:
  ```powershell
  uv run python scripts/ci_check.py
  ```

### Manual Verification

- Owner reviews the completed walkthrough, evidence limitations, status semantics, and
  proposed commit message before authorizing any Git commit.

## 8. Rollback & Contingency

1. Preserve the pre-existing dirty worktree and record hashes of every allowed file before
   editing during execution.
2. If a documentation approach proves invalid, restore only the files changed by this task
   from those recorded copies; never reset the repository or discard unrelated changes.
3. If dynamic analysis changes installation state, list the exact changed files. Do not
   delete or overwrite them automatically; request owner direction for restoration.
4. If a required source is unavailable, keep the affected contract `Unverified`, document
   the access gap and validation protocol, and continue with independent areas.
5. If official and local evidence conflict, preserve both observations with version scope
   and do not select one silently.

```text
ALLOWED_WRITE_PATHS:
- docs/implementation-plan.md
- docs/PROJECT.md
- docs/ARCHITECTURE.md
- docs/walkthrough.md
- app/services/workspace/README.md
- app/services/persistence/README.md
- app/services/brokers/README.md
- app/services/data/README.md
- app/services/indicator/README.md
- app/services/strategy/README.md
- app/services/risk/README.md
- app/services/analytics/README.md
- app/services/trading/README.md
- app/services/simulator/README.md
- app/services/optimization/README.md
- app/services/robustness/README.md
- app/services/portfolio/README.md
- app/services/research/README.md
- app/services/gateway/README.md
- app/services/ui/README.md
- app/services/agentic/README.md
END_ALLOWED_WRITE_PATHS:
```
