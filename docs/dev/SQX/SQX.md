# StrategyQuant X Build 144 → HaruQuantAI — Unified Specification

## Reconciled UI reconstruction, research-engine design, compatibility analysis, and build-ready product specification

| Field | Value |
|---|---|
| Document status | Merged and reconciled implementation planning baseline |
| Evidence freeze | 2026-09-04 |
| Donor build inspected | StrategyQuant X Ultimate Build 144.2953 |
| Target | HaruQuantAI, brownfield integration |
| Target repository | `C:\Users\rharu\AppDev\HaruquantAI` |
| Source analyses merged | `CodexSQX.md` and `GeminiSQX.md` |
| Intended readers | Product, architecture, backend, frontend, QA, and plugin developers |
| Scope | Strategy research workbench, data management, generation/search, visual strategy editing, result analysis, portfolio construction, automation, compatibility, and extension tooling |

> This is a clean-room product and interface specification derived from current public documentation, an installed licensed runtime, and HaruQuantAI's own contracts. It is not a request to copy StrategyQuant source code, proprietary algorithms, branding, private data, license checks, or binary formats.

This unified edition retains every substantive topic and claim group from both source analyses. Supported details are promoted into the normative specification; useful but unverified details are retained as explicit clean-room target proposals; contradicted details remain visible in a reconciliation ledger instead of being silently copied or silently dropped.

---

## 1. Decision summary

HaruQuantAI should reproduce the **workflow grammar and user outcomes** of StrategyQuant X (SQX), not its legacy Angular/Electron/Java implementation. The result must be a family of independently owned Dockview widgets and domain plugins that happen to compose into an SQX-like workbench.

The primary product loop is:

```mermaid
flowchart LR
    D[Market data and profiles] --> S[Define strategy space]
    S --> B[Generate or edit strategies]
    B --> T[Backtest and retest]
    T --> R[Rank and robustness-test]
    R --> O[Optimize and walk forward]
    O --> A[Analyze results]
    A --> P[Compose portfolios]
    P --> X[Export or continue research]
    A --> B
    P --> R
```

### 1.1 Non-negotiable brownfield decisions

| Decision | Required treatment |
|---|---|
| Product surface | SQX becomes a first-class HaruQuantAI workbench assembled from dockable widgets; it is not a separate SPA hidden in an iframe. |
| Plugin architecture | Every independently deployable capability and every public widget has one declared feature owner, manifest, lifecycle, capability requirements, tests, and removal story. |
| Domain ownership | Strategy, Research, Simulator, Analytics, Portfolio, Orchestration, Data/Catalogue, Plugins, Workspace, Interfaces, and UI keep their existing boundaries. |
| Interfaces boundary | `app/services/interfaces` only authenticates, validates wire DTOs, resolves public capabilities, translates errors, and transports events. It must not calculate metrics, read domain tables, manipulate files, or contain research logic. |
| Backend runtime | Keep Python 3.14, Pydantic v2, Uvicorn, SQLite metadata, and Parquet/Arrow bulk artifacts. Do not create a parallel platform merely to imitate SQX. |
| HTTP framework | HaruQuantAI currently exposes a raw ASGI adapter. FastAPI may be adopted only through a separately approved transport migration; this feature does not require or authorize that migration. |
| Frontend runtime | Use the existing Next.js 15 + React 19 application and Dockview 7. Vite is a test/build dependency in the repository, not the application shell. |
| Styling | Use current design tokens and component conventions. Tailwind is not currently a dependency and is not required for parity. |
| Tables | First prove existing table primitives. Add TanStack Table/Virtual only if the grid spike demonstrates a material gap and dependency review approves it. |
| Charts | Reuse `lightweight-charts` for market/time-series views. Add one lazy-loaded analytical engine only for capabilities it cannot provide, especially heatmaps and 3D surfaces. |
| Streaming | Use idempotent HTTP commands plus resumable SSE for run progress, logs, and result availability. WebSockets are deferred unless a genuinely bidirectional interaction is demonstrated. |
| Layout persistence | Dockview layout is presentation state. It must never become the authoritative record of a project, strategy, run, databank, or portfolio. |
| Legacy `.sqx` | Treat as an imported Workspace artifact handled by an isolated importer plugin. Never decode it in Interfaces or mutate the original. |
| Existing data work | Reuse `data.browse-reference@1` and `data.import-quantdata@1`; do not rebuild QuantDataManager inside the SQX feature. |
| Numerical truth | The backend domain capability is authoritative for simulations, metrics, ranking, and portfolio math. The browser may format or downsample but may not recompute canonical values. |

### 1.2 What “parity” means

Parity has four levels:

1. **Workflow parity:** a user can complete the same research outcome.
2. **Information parity:** decisions can be made from equivalent controls, state, warnings, and outputs.
3. **Interaction parity:** navigation, docking, grids, keyboard access, progress, comparison, and drill-down feel coherent and efficient.
4. **Visual affinity:** familiar density and hierarchy without copying protected artwork, trade dress, or obsolete layout mechanics.

Pixel-for-pixel cloning, undocumented numerical equivalence, and binary compatibility with every historical SQX artifact are explicitly outside the initial definition of done.

---

## 2. Method, evidence, and confidence

### 2.1 Evidence legend

Every claim that could drive implementation uses one of these evidence grades:

| Tag | Meaning | Implementation use |
|---|---|---|
| `[L]` | Observed directly in the running licensed Build 144.2953 UI | Strong current-surface evidence, still subject to license/edition conditions |
| `[A]` | Found in shipped Build 144.2953 non-executable assets, configuration, examples, or inspected fixtures | Strong inventory/schema evidence; reachability and runtime behavior may still need live validation |
| `[B]` | Traced in shipped Build 144.2953 compiled classes, serializers, or implementation snippets through static inspection | Strong build-specific implementation evidence; still requires black-box tests for observable parity and must not be treated as permission to copy donor code |
| `[R]` | Observed in the current HaruQuantAI repository | Brownfield implementation truth at the evidence freeze |
| `[D]` | Current official StrategyQuant documentation or changelog | Safe functional evidence; reconcile with current runtime where they differ |
| `[H]` | Historical official manual or extension guide | Useful superset or precedent, not proof of current default behavior |
| `[I]` | HaruQuantAI implementation inference or recommendation | A target decision, not a donor-product fact |
| `[U]` | Unresolved; needs an explicit runtime capture, sample file, or product decision | Must not silently become an acceptance criterion |
| `[P]` | Proposal carried forward from `GeminiSQX.md` | Preserved for completeness; it is not evidence and must be paired with `[I]`, `[U]`, or a supporting evidence tag |

### 2.2 Research sources

The evidence pass used:

- The licensed application at `C:\StrategyQuantX144`, including the live UI and readable static web assets. No private strategy data, credentials, license material, or executable code was copied.
- HaruQuantAI's root `AGENTS.md`, contracts, manifests, feature registry, composition engine, Interfaces adapter, UI package manifest, widget contracts, and implemented data capabilities.
- Current official pages including [Download](https://strategyquant.com/download/), [What's new](https://strategyquant.com/whatsnew/), [Program layout](https://strategyquant.com/doc/strategyquant/program-layout/), [Builder](https://strategyquant.com/doc/strategyquant/builder/), [Builder layout](https://strategyquant.com/doc/strategyquant/builder-layout/), and [Portfolio Composer](https://strategyquant.com/doc/strategyquant/portfolio-composer/).
- Focused official documentation linked in the source index at the end of this document.

### 2.3 Evidence cautions

- The installed edition is **Ultimate** and the license can reveal controls that other editions hide. Edition gating must be represented as capabilities or entitlements, not hard-coded by label.
- Some shipped assets are shared across SQX, standalone QuantDataManager, hidden tools, and legacy views. Presence in a bundle does not prove a normal user can navigate to it.
- Text and configuration schemas show control inventory but do not establish proprietary algorithm semantics. Compiled-class evidence is tagged `[B]` separately from asset evidence `[A]`.
- Old documentation is sometimes more detailed than current pages. Historical-only controls are marked `[H]` and require validation before implementation.
- Build 144 is the current public final build at the evidence freeze: the official download page lists **144.2953, released 20 May 2026**. `[D]`

### 2.4 Confidence by area

| Area | Confidence | Reason |
|---|---:|---|
| Global shell and module navigation | High | Live observation plus shipped module registration |
| Builder/Retester/Optimizer setting taxonomy | High | Current shipped configuration plugins and official docs |
| Databank actions and Results tab registry | High | Current shipped menus/tab registrations plus docs |
| Data Manager grids, profiles, and sources | High | Current QDM shell, controllers, templates, and official pages |
| Portfolio Composer/Master workflows | High | Current assets and current documentation |
| AlgoWizard high-level flow | High | Live Build 144 observation |
| Generator and evolutionary control schema | High | Shipped settings expose generations, population/islands, migration, crossover/mutation, decimation, restart, fresh-blood, and fitness controls [A] |
| Build 144 genetic internals traced in §36.10 | High, build-specific | Current classes establish the wired RNG/selection/crossover/mutation, ring migration, decimation, fingerprint pruning, and indexed optimization operators [B] |
| Complete generator/search parity | Unknown | Initialization, every plugin/custom block, AI behavior, historical variants, and several proposed algorithms remain incomplete [U] |
| AlgoWizard sampled archive/XML schema | High for inspected fixtures | Current examples establish the archive envelope, rule/event tree, typed items/blocks/parameters, variables, data bindings, and common actions [A] |
| AlgoWizard common built-in comparator semantics | High, build-specific | Shipped Java snippets establish six-decimal normalization, exact-after-rounding equality, strict crossover boundaries, and opposite mappings [B] |
| AlgoWizard plugin/custom-node and AI semantics | Medium/unknown | Complete behavioral parity across every block, plugin, AI action, and version still requires differential simulation [A][U] |
| .sqx ZIP/member topology | High for inspected Build 144 fixtures | Multiple local archives establish variant-dependent member sets [A] |
| .sqx common XML/result outer hierarchy | High for 32 inspected fixtures | Current fixtures establish the visible structures; embedded/Base64 payload semantics remain unresolved [A][U] |
| .sqx format-11 order-stream framing | High for inspected implementation | Current serializer/deserializer establishes Java framing, seven metadata integers, string cache, and EOF-delimited records [B] |
| .sqx binary decoding and full-fidelity writing | Low/unknown | Sampled files and implementation inspection disprove a fixed-record prototype; format-version dispatch and donor reopen tests remain outstanding [A][B][U] |
| Neural Network Trainer registration and shell | High | Hidden module/task registration and shared workbench settings are shipped [A] |
| Neural Network Trainer operational capability | Contradicted in inspected build | The task start is a no-op, status is always zero, and databank methods return null [B] |
| Future neural model semantics | Proposed | Detailed ML behavior is retained only as an optional target design [P][I] |
| Grid Control UI and polling behavior | High | Current controller exposes Local Grid, exact job grids, and a 3-second refresh [A] |
| Grid Test local UI stress harness | High | Current controller exposes exact controls and 20/30/40 ms mutation timers [A] |
| Grid Test network/cluster benchmarking | Contradicted | The controller is a local sqGrid mutation harness and contains no worker/network measurement path [A] |

---

## 3. Product boundary and release baseline

### 3.1 Current donor baseline

The observed title is `StrategyQuant X Ultimate Build 144 ...`; the footer reports `Build 144.2953`. `[L]` The public release record matches it. `[D]`

Build 144 publicly adds the following material capabilities: custom HTML/JavaScript result-analysis plugins, Volume Profile/TPO analysis, a first MCP implementation, direct MT5 data import, an enhanced installer and Data Manager CLI, Trades by Close Type analysis, databank correlation through Custom Analysis, and additional Monte Carlo manipulation methods. `[D]`

Relevant immediately preceding changes are:

| Build | Evidence-backed change |
|---|---|
| 143 | AlgoWizard was rewritten with AI-assisted strategy creation. `[D]` |
| 142 | Portfolio Composer automatic weighting, direct databank correlation filtering, StockPicker open drawdown, VWAP, and processor-priority options. `[D]` |
| 141 | Portfolio Composer and Broker Profiles. `[D]` |

### 3.2 Donor implementation topology—not a target design

The installation contains an Electron/Chromium desktop shell, a Java runtime/backend, an older AngularJS web shell, a newer Vue-based Results implementation, AlgoWizard assets, Monaco editor assets, and several chart libraries. `[A]`

HaruQuantAI must **not** reproduce these implementation seams. In particular:

- no iframe-per-module shell;
- no global mutable web namespace;
- no direct browser-to-domain socket protocol;
- no static switch that becomes an undeclared plugin registry;
- no mixing of data access, simulation, and presentation in a controller;
- no acceptance test based on private SQX messages, classes, or file paths.

### 3.3 In-scope product surfaces

| Surface | Initial parity target | Notes |
|---|---|---|
| Getting Started | Functional affinity | HaruQuantAI onboarding and templates, not SQ branding |
| Builder | Full workflow | Strategy generation/evolution workbench |
| Retester | Full workflow | Batch reevaluation and robustness orchestration |
| Optimizer | Full workflow | Simple, sequential, WFO, and WFM orchestration |
| Databanks | Full workflow | Analytics-owned result membership, views, actions, and comparison |
| Results | Full decision parity | Overview, trades, equity, analyses, robustness, configuration, and code |
| Portfolio Master | Full workflow | Portfolio search/construction |
| Portfolio Composer | Full workflow | Manual and automatic weighting/evaluation |
| Data Manager | Integrate existing capabilities | Extend existing QDM-like slice rather than duplicate it |
| Custom Projects | Full workflow | Durable task graph and run history |
| AlgoWizard | Staged workflow | Visual strategy editing first; AI assistance behind a capability |
| Code Editor | Staged/advanced | Plugin and strategy-source editing with sandboxed compilation/testing |
| Grid Control | Operational view | Observe and control authorized jobs |
| Debug Console | Developer-only | Structured logs with redaction and permissions |
| SQ4Business | Conditional/deferred | Commercial packaging/export is a distinct product decision |
| Volume/Market Profile | Plugin-gated | Analytics/chart add-on |
| Neural Network Trainer | Deferred `[U]` | Requires supported-surface validation and domain contract |
| Grid Test | Internal only `[U]` | Do not expose without a product owner and security review |

---

## 4. Information architecture and global shell

### 4.1 Observed primary navigation

| Order | Module | Section | Condition |
|---:|---|---|---|
| 0 | Getting started | Primary | Default |
| 20 | Builder | Primary | Default |
| 30 | Retester | Primary | Default |
| 40 | Optimizer | Primary | Professional entitlement in shipped registration |
| 50 | Portfolio Master | Primary | Default |
| 51 | Portfolio Composer | Primary | Default |
| 10 | Data Manager | Secondary | Default |
| 20 | Custom Projects | Secondary | Professional entitlement in shipped registration |
| 31 | AlgoWizard | Secondary | Default |
| 50 | SQ 4 Business | Secondary | Hidden/edition-controlled registration; visible in the inspected license |

The top utility area exposes Debug Console, Code Editor, Grid Control, Volume & Market Profile Addon, and Settings. `[L][A]`

### 4.2 Target workbench composition

The SQX experience should be a saved **workspace template**, not a monolithic widget. `[I]`

```mermaid
flowchart TB
    W[HaruQuantAI Dockview workspace]
    W --> N[SQX navigator widget]
    W --> C[Context-sensitive command bar]
    W --> E[Editor/settings widgets]
    W --> G[Databank/grid widgets]
    W --> R[Result-analysis widgets]
    W --> J[Runs/logs widget]
    W --> P[Portfolio widgets]
    W --> D[Existing data-manager widgets]
```

Default template layout:

```text
┌──────────────────────────────── context command bar ────────────────────────────────┐
│ navigator │ editor / settings / task canvas                                         │
│           ├──────────────────────────────────────────────────────────────────────────┤
│           │ databank or result tabs                         │ inspector / run status │
└───────────┴─────────────────────────────────────────────────┴────────────────────────┘
```

Users may split, float, move, maximize, close, and reopen panels. Each panel must preserve its own transient UI state, while references to projects, strategies, runs, and artifacts remain stable domain IDs.

### 4.3 Observed shell chrome

- Collapsible left navigation with per-application progress badges. `[L][A]`
- Main content host with a conditional Results overlay in the donor implementation. `[A]`
- Footer links/status for Build, Documentation, Support, Report Bug / Suggest Feature, and About. `[L][A]`
- Settings menu for Configuration, Benchmark, Remote access, MCP Server, SMTP server, Language, Skin, Zoom/fullscreen, website/help/support, license update, About, Reload UI, and Exit. `[L][A]`

HaruQuantAI remains the outer shell. Contextual progress belongs in the global Jobs surface and relevant widget headers; donor footer/navigation items should map to host-owned commands instead of being duplicated inside the workspace.

### 4.4 Shell requirements

| ID | Requirement | Acceptance |
|---|---|---|
| SHELL-001 | Register each SQX-facing panel through a widget manifest. | No SQX component is reachable only by adding a case to `WidgetContentHost.tsx`; the manifest is the declared source of capabilities, placement, subscriptions, and effects. |
| SHELL-002 | Provide an “SQX Research” workspace template. | Opening the template creates the default dock arrangement without duplicating any domain object. |
| SHELL-003 | Support compact and expanded navigation. | Labels remain accessible by tooltip and screen reader when collapsed. |
| SHELL-004 | Show capability/entitlement gating before navigation. | Unavailable features are either omitted or shown with an actionable explanation; no dead module opens. |
| SHELL-005 | Provide global command discovery. | Search can find modules, commands, projects, runs, strategies, databanks, and help links the caller is authorized to see. |
| SHELL-006 | Surface long-running work globally. | Active, paused, queued, failed, and completed runs remain observable when their originating widget is closed. |
| SHELL-007 | Preserve keyboard and focus semantics across docks. | Tab order, focus restoration, Alt+Arrow docking shortcuts, escape behavior, and modal focus traps pass automated and manual accessibility checks. |
| SHELL-008 | Keep layout recovery safe. | A malformed or obsolete layout falls back to the SQX template; it never deletes projects or run state. |
| SHELL-009 | Provide contextual documentation and diagnostics. | Help opens the correct HaruQuantAI page; diagnostics export contains versions and redacted trace IDs, never secrets or private market data. |

### 4.5 Global settings inventory

Observed configuration categories are **Global, CPU, Performance, Memory, Databanks, Optimizations, and Troubleshooting**. `[A]`

| Category | Observed controls to represent | Target ownership |
|---|---|---|
| Global | sound, file chooser view/sort memory, MT5 netting control-order visibility, custom header/footer, default result view | Workspace/UI preferences, except trading semantics |
| CPU | all/single/reserved/custom core modes, maximum cores, high process priority | Orchestration resource policy |
| Performance | metric units, percent/pips display, separate computation controls | Analytics presentation plus domain metric policy |
| Memory | automatic/parallel/G1-like runtime choice in donor, maximum memory, discard unfilled pending orders, cleanup cadence | Do not clone JVM choices; expose HaruQuant resource/cache budgets instead |
| Databanks | automatic synchronization, store chart data | Analytics artifact policy |
| Optimizations | retain 3D optimization data | Research artifact-retention policy |
| Troubleshooting | browser GPU acceleration, memory protection threshold, debug logging | UI/runtime diagnostics; no invented CUDA compute toggle |

Additional dialogs expose remote access, MCP server details, SMTP settings/test, language, skin, zoom/fullscreen, license/about/support, reload, and exit. `[A]` HaruQuantAI should map only relevant outcomes to its settings and plugin system; license and desktop-exit behavior are host concerns.

Adjacent observed dialog controls are: `[L][A]`

- Remote access: allow/deny, server URL, and optional password.
- MCP Server: current server URL plus connection instructions for Claude Code/Desktop in the donor; target wording and clients are host-owned.
- SMTP: server, port, SSL, username, password, sender address, test recipient, Send Test, and Save.
- Appearance/onboarding: language, skin/theme, zoom/fullscreen, and intro-walkthrough preference.
- Volume/Market Profile: add-on/license information in the donor; target uses plugin capability discovery.

---

## 5. Shared research-workbench grammar

Builder, Retester, Optimizer, Portfolio Master, and Custom Projects share a recognizable project structure: a header, configuration cards, a bottom databank area, and top-level **Progress / Full settings / Results** modes. `[A]`

### 5.1 Run lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Validating: Start
    Validating --> Queued: valid
    Validating --> Draft: invalid
    Queued --> Running
    Running --> Pausing: pause requested
    Pausing --> Paused: checkpoint reached
    Paused --> Queued: resume
    Running --> Stopping: stop requested
    Paused --> Stopping: stop requested
    Running --> Completed
    Running --> Failed
    Stopping --> Stopped
    Completed --> [*]
    Failed --> [*]
    Stopped --> [*]
```

Every run must pin:

- capability and provider versions;
- input artifact IDs and content hashes;
- data-series version and broker/instrument/session profile versions;
- strategy/configuration revision;
- random seed or seed policy;
- metric/ranking definition versions;
- requested resource budget;
- caller, request ID, trace ID, and timestamps.

### 5.2 Shared engine panel

| Group | Functional inventory |
|---|---|
| Configuration | New/reset; load; save; save as; named presets; Forex, Futures, and StockPicker defaults where appropriate |
| Execution | Validate; start; pause; resume; stop; retry failed; run from checkpoint where supported |
| Telemetry | phase, elapsed, ETA, accepted/rejected counts, throughput, queue position, worker allocation, memory/cache pressure |
| Logs | structured severity, timestamp, phase, worker, strategy/run reference, search, filter, copy, clear local view, export redacted diagnostics |
| Progress views | numeric summary, time series, acceptance funnel, task-manager visual, worker/job view |
| Safety | unsaved-change warning, incompatible-config warning, stale-data warning, stop confirmation only when work cannot checkpoint safely |

### 5.3 Shared run requirements

| ID | Requirement | Acceptance |
|---|---|---|
| RUN-001 | Starting work creates an immutable run record before execution. | A returned run ID resolves after refresh and records pinned inputs and versions. |
| RUN-002 | Command submission is idempotent. | Replaying an identical start request with the same idempotency key never starts a second run. |
| RUN-003 | Progress is resumable. | Reconnecting with the last SSE cursor yields all subsequent events in order or an explicit resync instruction. |
| RUN-004 | Pause and stop are domain commands. | UI closure or SSE disconnect does not pause or stop work. |
| RUN-005 | Partial output is typed and visibly incomplete. | Consumers cannot mistake a preview/checkpoint for a committed final databank result. |
| RUN-006 | Configuration validation is capability-owned. | The browser displays domain errors at field and summary level; it does not reproduce calculation rules. |
| RUN-007 | Resource limits fail safely. | Exceeded budgets transition to a typed state with retained diagnostics and recoverable checkpoints where supported. |
| RUN-008 | Run deletion is governed. | Removing a run uses retention policy and reference checks; deleting a row in the UI cannot orphan shared artifacts. |
| RUN-009 | Reproducibility is inspectable. | “Reproduce run” shows changed/missing providers, data, and profiles before it creates a new run. |
| RUN-010 | Logs are redacted. | Secret values, authorization headers, private file paths, and raw credentials never appear in UI logs or exports. |

---

## 6. Builder

### 6.1 User outcome

Builder defines a strategy search space, generates candidates through random or evolutionary methods, backtests them, rejects invalid/weak candidates, and commits accepted strategies into an Analytics-owned databank. `[D][A]`

### 6.2 Full settings taxonomy

| Order | Tab | Required content |
|---:|---|---|
| 5 | What to build | strategy type, direction, symmetry, entry/exit architecture, search method, stop-loss/profit-target policy |
| 6 | Parts to improve | entry, order, exit, long/short branches, keep/replace/add behavior, advanced exits |
| 7 | Genetic options | generations, islands, population, decimation, fresh blood, deduplication, restart/stagnation policies |
| 10 | Data | engine, primary/additional charts, symbol/group, timeframe, date/sample bands, precision and costs |
| 20 | Trading options | session/range restrictions, maximum trades, reserved bars, gap behavior, chart-data retention |
| 30 | Building blocks | signal/indicator/order/exit catalog, enablement, weights, parameter distributions and external timeframes |
| 35 | ATM | named advanced trade-management exit rules and editor |
| 50 | Money management | starting capital, sizing method, and typed method properties |
| 60 | Cross checks | ordered robustness/retest pipeline |
| 70 | Ranking | databank limits, fitness, weighted criteria, custom analysis, rejection, similarity and correlation |
| 100 | Notes | project notes and provenance annotations |

### 6.3 Detailed control inventory

#### What to build

- Modes: simple strategy, multi-timeframe strategy, strategy from template, and improve existing strategy. `[A]`
- Direction: long and short, long only, short only; independent or symmetric entry/exit branches. `[A]`
- Architecture families observed in the donor include SQX signals, fuzzy logic, and legacy SQ3-style patterns. `[A]` HaruQuantAI should expose registered architectures, not donor brand labels. `[I]`
- Search method: random generation or genetic evolution. `[A]`
- Stop-loss and profit-target policies: required/optional/disabled, fixed distance, ATR-derived, indicator-derived, and parameter ranges. `[A]`
- Condition count, period ranges, maximum complexity, and template constraints must be validated by the Strategy domain.

#### Parts to improve

- Selectable long/short entry conditions, entry order, exit conditions, and exit order.
- Per-part behavior: retain, replace, randomize, or add; honor symmetry rules.
- Advanced exits can be preserved, replaced, or separately edited.

#### Genetic options

- Generation count, population per island, number of islands, initial population source, and source databank.
- Decimation and survival policy, fresh-blood percentage, duplicate elimination, weak-individual replacement cadence.
- Last-generation databank retention.
- Continuous evolution and restart after stagnation.
- Explicit seed policy and deterministic replay in HaruQuantAI.

#### Data

- Simulation engine/provider.
- Primary chart and zero or more additional charts, each with symbol/group and timeframe.
- Date range with reset-to-available action.
- In-sample, validation, and out-of-sample bands with named presets and a visual timeline.
- Precision/model selection, commission, swap, spread, slippage, and minimum-distance policy.
- Profile selectors must resolve versioned Data/Catalogue objects; controls must not embed cost formulas.

#### Trading options

- End-of-day and Friday close behavior.
- Allowed trading time range and session profile.
- Maximum simultaneous/total trades according to the selected simulator semantics.
- Reserved bars and warm-up requirements.
- Gap-handling policy.
- Retain chart data toggle as a result-artifact policy, not a UI cache toggle.

#### Building blocks

- Catalog sections for signals, indicators, stop/limit entries, exit types, and registered plugin nodes.
- Enable/disable, weight, parameter editor, allowed-values editor, parameter calibration, random-choice policy, save/load preset.
- Per-block external timeframe where supported.
- Search, filter by category/provider/compatibility, select all/none, and explain why an incompatible block is unavailable.

#### ATM and money management

- Define/edit named exit rules through the Strategy-owned ATM schema.
- Select initial capital, sizing method, and method-specific typed properties.
- Units, bounds, broker/instrument constraints, and compounding semantics must be explicit.
- Retester/Optimizer overrides never mutate the source Strategy revision.

#### Ranking and acceptance

- Maximum retained strategies and optional stop condition.
- Fitness target and ordered/weighted criteria with direction and normalization.
- Custom analysis stages and automatic rejection filters.
- Similarity/deduplication policy.
- Portfolio-correlation threshold and tie-break policy.
- Walk-forward and robustness qualification thresholds.

#### Cross-check pipeline

Observed ordering is:

1. Monte Carlo trade manipulation.
2. Monte Carlo retest.
3. What-if simulations.
4. Retest on additional markets.
5. Retest with higher precision.
6. Walk-Forward Matrix.
7. Walk-Forward Optimization.
8. Optimization Profile / System Parameter Permutation.
9. Sequential Optimization. `[A]`

The target must store this as an ordered, typed pipeline of plugin contributions; it must not encode display labels as execution behavior.

### 6.4 Builder requirements

| ID | Requirement | Acceptance |
|---|---|---|
| BLD-001 | Author a valid, versioned strategy-space specification. | Save produces a Strategy-owned revision and reopening it preserves all typed constraints. |
| BLD-002 | Resolve blocks from the public catalog. | Every node records provider/version; missing providers are reported before start. |
| BLD-003 | Preview the effective search space. | UI shows constrained parameters, estimated combinatorial scale, exclusions, and conflicts without claiming an exact runtime forecast. |
| BLD-004 | Support random and evolutionary generation providers. | Both conform to the same Research run contract and produce provenance-equivalent candidates. |
| BLD-005 | Apply backtest, rejection, ranking, and cross-check stages in declared order. | Run details show stage transitions and the reason each candidate was accepted or rejected. |
| BLD-006 | Deduplicate candidates by a documented canonical identity. | Equivalent ASTs are not stored twice unless the user explicitly retains distinct provenance. |
| BLD-007 | Commit accepted candidates atomically. | Databank membership references committed strategy/result artifacts only after the stage succeeds. |
| BLD-008 | Preserve run reproducibility. | Same compatible provider set, data versions, config, and seeds yields a replayable run; deviations are disclosed. |
| BLD-009 | Make rejection explainable. | The user can aggregate and drill into validation, simulation, filter, similarity, and resource rejection reasons. |
| BLD-010 | Never execute generated strategy code in the UI process. | All compilation/execution occurs in an authorized, isolated domain provider. |

---

## 7. Retester

Retester reevaluates selected strategies or a source databank against changed data, precision, costs, markets, robustness methods, or ranking rules without editing the source revisions. `[D][A]`

### 7.1 Settings

| Order | Tab | Difference from Builder |
|---:|---|---|
| 0 | What to retest | file/databank/source selection and selection scope |
| 10 | Data | same profile/date/sample concepts; may add alternate markets |
| 20 | Trading options | simulation restrictions and chart retention |
| 35 | ATM | override/retain advanced management policy |
| 50 | Money management | retain or override sizing/capital policy |
| 60 | Cross checks | selected robustness stages |
| 70 | Ranking | target databank/filter policy |
| 100 | Notes | run rationale and annotations |

### 7.2 Retester requirements

| ID | Requirement | Acceptance |
|---|---|---|
| RET-001 | Select strategies from artifact, databank, saved query, or explicit IDs. | The run records the resolved immutable strategy set, not only the mutable query. |
| RET-002 | Keep source strategies immutable. | Overrides produce run configuration or new revisions; the source hash is unchanged. |
| RET-003 | Batch against one or more data contexts. | Results identify the exact symbol, timeframe, sample, cost, and precision context. |
| RET-004 | Support automatic retest pipelines. | A saved ordered pipeline can be invoked from Builder, Databank, or Custom Projects through the same capability. |
| RET-005 | Compare baseline and retest outcomes. | Delta columns use canonical metric versions and distinguish missing/non-comparable values. |
| RET-006 | Route passed/failed results deterministically. | Membership rules and rejection reasons are committed atomically and visible in run history. |
| RET-007 | Allow cancellation at strategy/stage boundaries. | Completed items remain typed partial output; cancelled items are never labeled failed. |

---

## 8. Optimizer

Optimizer searches parameter combinations for an existing strategy using simple optimization, sequential optimization, Walk-Forward Optimization (WFO), or Walk-Forward Matrix (WFM). `[D][A]`

### 8.1 Configuration inventory

- Source: strategy file/artifact or databank selection.
- Method: simple, sequential, WFO, or WFM.
- Data and trading options share the versioned profile model.
- Date/sample and window/run configuration.
- Result scope: all, passing, or best candidates.
- Optional stable-area/stability filter.
- Parameter table: selected, parameter name, original value, start, stop, step, type, and calculated combinations.
- Automatic preset/distribution action.
- Ranking and notes.

### 8.2 Optimizer requirements

| ID | Requirement | Acceptance |
|---|---|---|
| OPT-001 | Derive optimizable parameters from a Strategy-owned revision. | Unsupported or dependent parameters are explained and cannot be silently coerced. |
| OPT-002 | Validate ranges and combination count before execution. | Empty, invalid, explosive, and precision-losing ranges produce actionable validation. |
| OPT-003 | Separate search method from simulation semantics. | Research chooses combinations; Simulator evaluates them through a versioned capability. |
| OPT-004 | Support simple, sequential, WFO, and WFM run plans. | Each plan has a typed schema and can be serialized, versioned, cloned, and diffed. |
| OPT-005 | Stream aggregate progress without flooding the client. | Events are coalesced; grid rows/results are fetched by page or artifact chunk. |
| OPT-006 | Retain enough surface data for selected visualizations. | Artifact policy declares whether full points, top-N, aggregates, or no 3D data are retained. |
| OPT-007 | Explain stability classification. | PASS/FAIL and stable regions link to versioned thresholds and underlying observations. |
| OPT-008 | Protect against overfitting presentation. | IS/OOS/validation are visually distinct and cannot be merged into a single unlabeled score. |
| OPT-009 | Promote an outcome through an explicit revision action. | Selecting an optimized configuration never overwrites the base strategy silently. |
| OPT-010 | Export reproducible optimization evidence. | Export contains plan, parameter grid, samples, metrics, provider versions, and artifact hashes. |

---

## 9. Databanks

A databank is an **Analytics-owned membership and query view over strategies and their results**, not a Workspace folder and not a table owned by Interfaces. `[I]`

### 9.1 Observed interaction inventory

- Multiple databank tabs with databank count, strategy count, record count, and selected count.
- Saved column views: Choose View and Manage Views.
- Sort, filter, select, multi-select, virtual scroll, resize/reorder/pin columns, and refresh/synchronize.
- Double-click a strategy to open Results.
- Load `.sqx` and save/export in product-supported formats.
- Delete selected, clear membership, move/copy between databanks, and create a databank.
- Retest selected.
- Rename strategies, edit parameters, set notes, select passed/failed, compare strategies, and run custom analysis.
- Filter by correlation.
- Merge strategies/portfolios, merge walk-forward results, split portfolios, and send to Portfolio Composer or Master.

### 9.2 Export inventory

Observed menu targets include SQ4/SQ3 strategy files, HTML, PDF, CSV, trade lists, MetaTrader 4, MetaTrader 5, MultiCharts/EasyLanguage, JForex, pseudocode, and XML. `[A]` Python and NinjaTrader are not evidenced as current built-in targets and must not be promised without a registered generator plugin.

### 9.3 Column model

Columns are dynamic plugin contributions organized into saved views. A historical official superset includes Generation, Fitness, Symbol, Timeframe, Net Profit, Trades, Win %, Profit Factor, Sharpe, R Expectancy, Annual %, Stability, Symmetry, Drawdown, Win/Loss, and Return/Drawdown. `[H]`

Target column descriptors must include:

```text
column_id, owner_feature, schema_version, label_key, value_type,
unit/format, nullable, sortable, filter_operators, aggregation,
precision, provenance_field, compatibility_predicate
```

### 9.4 Databank requirements

| ID | Requirement | Acceptance |
|---|---|---|
| DBK-001 | Create, rename, archive, clone, and delete databank definitions through Analytics capabilities. | Referential checks and governed-delete outcomes are explicit. |
| DBK-002 | Add/remove/copy/move members atomically. | Partial multi-item failure returns per-item typed outcomes and an overall transaction policy. |
| DBK-003 | Provide server-side cursor paging, sort, and filter. | One million rows remain navigable without loading all records into browser memory. |
| DBK-004 | Support dynamic typed columns and saved views. | Unknown/missing plugin columns degrade visibly and do not corrupt the saved view. |
| DBK-005 | Keep selection stable across pages. | Selection is identity-based; bulk action shows resolved count and exclusions before execution. |
| DBK-006 | Open Results by stable result ID. | Sorting/filtering cannot cause double-click to open a different row. |
| DBK-007 | Run comparison and custom analysis as jobs. | Expensive analysis uses idempotent commands and progress streams, not UI loops. |
| DBK-008 | Make correlation filtering explainable. | The retained member, removed member, coefficient/method, sample, threshold, and tie-break policy are inspectable. |
| DBK-009 | Export via registered target capabilities. | UI lists only compatible generators; export records target/version/options and output artifact. |
| DBK-010 | Isolate legacy import. | Raw `.sqx` becomes an immutable Workspace artifact; an importer plugin emits typed strategies/results plus a compatibility report. |

---

## 10. Results and strategy analysis

Results is a plugin-extensible analysis workspace over an immutable simulation/result bundle. It must support side-by-side panels and cross-filtering without letting a view redefine canonical metrics. `[I]`

### 10.1 Observed tab registry

The current shipped registry orders these views: `[A]`

| Order | View | Availability/context |
|---:|---|---|
| 0 | Walk-Forward Results | WFO/WFM result |
| 10 | Overview | General |
| 11 | Optimization profile | Optimization result |
| 11 | SP overview | StockPicker result |
| 12 | System Parameter Permutation | SPP result |
| 12 | Sequential Optimization Results | Sequential result |
| 20 | List of trades | Result with trades |
| 30 | Equity chart | General |
| 40 | Trade analysis | General |
| 50 | Trades on chart | Result with market series |
| 55 | Profile chart | Compatible profile data/add-on |
| 60 | Monte Carlo tests | Robustness result |
| 70 | Portfolio correlation | Multi-strategy result |
| 80 | Strategy config | General |
| 99 | Log | Portfolio Composer context |
| 99 | StockPicker log | StockPicker context |
| 99 | Explore | Conditional analysis |
| 100 | Source Code | Compatible generator target |
| 999 | Automatic computation simulations | Internal/derived computation view |
| 1000+ | User Result Analysis plugins | Dynamically contributed HTML/JS panels |

The target should not duplicate the numeric ordering. It should use manifest `placement` plus stable view IDs and deterministic tie-breaking. `[I]`

### 10.2 Overview

- Selectable report template.
- Headline result identity, strategy revision, run/sample/data context, warning badges, and provenance.
- Metric groups for performance, risk, trade distribution, stagnation, and robustness.
- Documented metrics include net profit, pips, annual return/CAGR, Sharpe, Profit Factor, Return/Drawdown, win rate, drawdown, expectancy, R Expectancy, SQN, trade count, and stagnation. `[D]`
- Export/print of a server-generated, versioned report artifact.

Requirements:

| ID | Requirement | Acceptance |
|---|---|---|
| RES-OV-001 | Render metric cards from typed metric descriptors. | Unit, period, sample, precision, null reason, definition version, and owner are inspectable. |
| RES-OV-002 | Distinguish canonical, derived, and presentation-only values. | A user cannot confuse an estimated UI aggregate with an authoritative stored metric. |
| RES-OV-003 | Warn on stale/incomplete results. | Partial, superseded, missing-artifact, and incompatible-plugin states are prominent and machine-testable. |
| RES-OV-004 | Support report templates as plugin contributions. | An unavailable template falls back safely without changing the underlying result. |

### 10.3 List of trades

Observed controls include data/direction/sample selectors, view management, export, and inclusion of expired orders. `[A]`

Minimum columns are identity, open/close timestamps, direction, symbol, quantity, entry/exit price, stop/target context, fees, swap, slippage, gross/net P&L, pips/points, bars/duration, exit reason, MAE, MFE, sample, and strategy/run references. Exact availability depends on the simulator schema.

| ID | Requirement | Acceptance |
|---|---|---|
| RES-TRD-001 | Page and filter trades server-side. | Large result sets do not require full download; cursor and filter state survive a refresh. |
| RES-TRD-002 | Preserve trade identity across grids and charts. | Selecting a row highlights the same trade in equity, market chart, and analysis panels. |
| RES-TRD-003 | Export the requested projection. | Export declares filters, columns, units, timezone, schema version, and result hash. |
| RES-TRD-004 | Explain missing values. | Unsupported MAE/MFE, absent tick path, and synthetic fills render as typed unavailability, not zero. |

### 10.4 Equity chart

Observed controls: `[A]`

- X-axis by trade or time.
- Optional benchmark symbol and normalization.
- Drawdown series in money, percent, pips, open money, open percent, or off.
- Volume as automatic, size, money, or off.
- Daily aggregation, ATR, trend overlay.
- Markers by daily or MAE/MFE mode, or off.
- Stagnation variants, point display, crosshair, and refresh.

Target behavior:

- `lightweight-charts` renders equity, balance, benchmark, price, volume, and synchronized crosshair/time ranges.
- The server returns canonical series or documented downsampled levels; the UI never derives trade accounting.
- Large series use level-of-detail chunks and worker-based decoding/downsampling.
- Every visible line has a unit, sample, legend state, and accessible summary.

### 10.5 Trade analysis

Observed period basis is open or close time. The yearly table includes Period, Net Profit, Profit Factor, number of trades, and win percentage. Up to twelve selectable chart panels can be configured. `[A]`

Required panel families are distribution by time, duration, direction, size, profit/loss, close type, consecutive outcomes, excursion, and other registered Analytics contributions. Build 144 specifically documents **Trades by Close Type**. `[D]`

### 10.6 Trades on chart

The view requires symbol selection, indicator visibility, grid/zoom controls, price/ticket/P&L annotations, previous/next trade navigation, OHLC inspection, indicator values, and a trade-detail panel. `[A]`

Market and trade series must share the exact timezone/calendar transform. When the backing market series is missing, the view offers an authorized data-resolution action rather than drawing against a similar series.

### 10.7 Walk-forward and optimization surfaces

#### Walk-Forward Matrix

- PASS/FAIL and score summary.
- Matrix of OOS percentage by run count, selected-cell detail, and metric selector.
- 3D point, bar, surface, and top views; stability and display options. `[A]`
- Target adds an accessible 2D heatmap/table as the primary representation; 3D is an optional linked view.

#### Optimization profile

- Totals for all, profitable, losing, and zero outcomes.
- Profitability, average performance, uniformity, top-profit, and standard-deviation checks.
- X/Y/Z parameter and metric selectors; point/bar/surface/top display.
- The donor view reports a first-500 display constraint and an optimization-profile-levels dialog. `[A]` The target should page/sample explicitly and disclose the sampling rule.

#### Sequential Optimization

- PASS/FAIL, sequence/step summary, selected parameters, and stable-area charts.

#### System Parameter Permutation

- Median properties, statistic selector, distribution/percentile views, and source-plan provenance.

### 10.8 Monte Carlo and robustness

- Test-method selector, scenario/simulation count, seed policy, and robustness thresholds.
- Summary percentiles and failure probability with compatible equity/drawdown distributions.
- Link each simulation family to the exact perturbation definition and baseline.
- Build 144 documents new manipulation methods including block randomization, parameter jitter, and degraded execution. `[D]` Implement equivalent concepts through registered Simulator/Research plugins; do not copy proprietary implementations.

### 10.9 Portfolio correlation

Observed controls include correlation basis, target measure, negative-correlation handling, empty-period handling, compute/stop/progress, a matrix, overlapping-trades analysis, details, and save. `[A]`

The result must pin return frequency, calendar alignment, missing-period policy, correlation method, sample, and version. Matrix cells drill into paired series and overlapping trades without silently changing the population.

### 10.10 Strategy configuration and source

- Configuration compares current and backtest-time settings, highlights differences, and offers an explicit Apply action. `[A]`
- Apply must create or update a Strategy-owned revision after optimistic-lock validation; it cannot mutate a result.
- Observed source targets are pseudocode, MetaTrader 4, MetaTrader 5, EasyLanguage/MultiCharts, and XML. `[A]`
- Each generator is a capability with a version, compatibility predicate, options schema, diagnostics, and output artifact.

### 10.11 Result-analysis plugin sandbox

Build 144 supports user-created HTML/JavaScript result-analysis tabs. `[D]` HaruQuantAI already plans plugin-owned result panels and must enforce:

| Control | Required policy |
|---|---|
| Isolation | Sandboxed frame or isolated renderer boundary; no same-origin privilege with the host |
| Data | Read-only, explicit result projection; no direct database, filesystem, or token access |
| Messaging | Versioned host bridge with allow-listed commands and payload validation |
| Network | Denied by default; allow-list requires explicit plugin permission |
| CSP | No unsafe host script execution; packaged assets and nonce/hash policy |
| Limits | CPU/time/memory/event-rate and result-size budgets |
| Lifecycle | Declare compatible result schemas, panel version, migration, disable, and uninstall behavior |
| Failure | Panel crash is contained; host offers diagnostics and reset without affecting the result |

### 10.12 Result workspace requirements

| ID | Requirement | Acceptance |
|---|---|---|
| RES-001 | Resolve visible tabs from result type and plugin compatibility. | A deterministic manifest query produces the same ordered view set for the same capability snapshot. |
| RES-002 | Synchronize selections across compatible panels. | Strategy, sample, trade, time range, and parameter selection use typed UI events, not hidden global state. |
| RES-003 | Keep metrics provenance visible. | Every decision-grade number can reveal definition, version, input result, and sample. |
| RES-004 | Support comparison. | Two or more compatible results can be aligned with explicit missing/incompatible values and no implicit currency conversion. |
| RES-005 | Scale series and grids. | Initial useful content meets the performance budget without materializing full trade/equity arrays in React state. |
| RES-006 | Provide accessible chart alternatives. | Each chart has keyboard focus, textual summary, data table/export, and non-color state cues. |
| RES-007 | Persist view state as presentation state. | Reopening restores panels/controls but cannot alter result content. |
| RES-008 | Export provenance-complete reports. | Generated report includes result hash, strategy revision, data/profile versions, metric definitions, and warnings. |
| RES-009 | Contain plugin failure. | A faulty custom panel cannot block built-in results or access unauthorized host data. |
| RES-010 | Avoid false precision. | Sampling, downsampling, approximation, and unavailable series are disclosed in UI and export. |

---

## 11. Portfolio Master and Portfolio Composer

### 11.1 Portfolio Composer

Observed commands are Load, Save, Save portfolio, Delete, Clear, Move up/down, and Add Buy & Hold. The primary grid contains strategies and weights. Configuration covers full/limited data, capital/leverage, money-management consistency, and automatic computation with model, fitness, simulation count, and risk-free assumptions. Results and a log are available. `[A][D]`

| ID | Requirement | Acceptance |
|---|---|---|
| PFC-001 | Add strategies/results by stable reference. | Duplicate, missing, incompatible-currency, overlapping-capital, and sample issues are explained before computation. |
| PFC-002 | Edit and normalize weights. | Raw and normalized weights are both visible; normalization policy is explicit and reproducible. |
| PFC-003 | Add a Buy & Hold benchmark. | Benchmark uses a pinned series, instrument profile, currency policy, and sample. |
| PFC-004 | Configure capital, leverage, and sizing consistency. | Validation is Portfolio-owned and prevents ambiguous mixing of strategy sizing semantics. |
| PFC-005 | Compute combined performance asynchronously. | A run ID, progress, result artifact, warnings, and provenance are persisted. |
| PFC-006 | Offer registered weighting/search models. | Model schema, objectives, constraints, risk-free input, provider version, and seed policy are recorded. |
| PFC-007 | Reorder for presentation without changing math. | Row order affects only display unless the selected model explicitly declares order sensitivity. |
| PFC-008 | Promote a composition to a versioned portfolio. | Save creates a Portfolio-owned revision; recomputation produces a new result. |

### 11.2 Portfolio Master

Portfolio Master searches candidate combinations through brute-force or genetic methods. Observed settings include genetic configuration, date/sample/reverse selection, minimum and maximum strategy counts, maximum portfolios, ranking, sector maximums, source/target databanks, selected-only scope, capital/money-management override, and correlation conditions. `[A]`

| ID | Requirement | Acceptance |
|---|---|---|
| PFM-001 | Resolve a candidate universe from an immutable databank query. | The run records exact result/strategy IDs after filters and selection are resolved. |
| PFM-002 | Apply typed eligibility constraints. | Strategy count, sector, symbol, sample, correlation, capital, and compatibility failures are itemized. |
| PFM-003 | Support brute-force and evolutionary search providers. | Both emit the same portfolio-candidate contract and provenance fields. |
| PFM-004 | Rank on registered portfolio metrics. | Objective, direction, weights, constraints, and metric versions are inspectable. |
| PFM-005 | Bound combinatorial work. | Estimate, budget, maximum candidates/results, and stop policy must be accepted before start. |
| PFM-006 | Commit selected candidates to a target databank or portfolio set. | Output membership is atomic and distinguishable from intermediate candidates. |
| PFM-007 | Analyze correlation with explicit alignment. | Frequency, missing periods, currencies, negative handling, and method are pinned. |
| PFM-008 | Preserve per-strategy and combined evidence. | Portfolio results link back to every constituent strategy result and weighting revision. |

---

## 12. Data Manager integration

Data Manager is not a new SQX-owned data subsystem. It is a workbench over existing and extended Data/Catalogue capabilities. HaruQuantAI already implements `data.browse-reference@1`, `data.import-quantdata@1`, and a transport slice under `observe-market-reference`. `[I]`

### 12.1 Ribbon and sources

Observed ribbon groups are Home (standalone QDM only), Data sources, Export, Tools, Instruments and Sessions, External indicators (SQX), Stock groups (SQX), and Broker profiles. `[A]`

Observed source plugins are Dukascopy, TickDownloader, Files, SQ Equity, SQ Futures, Darwinex, Crypto, Yahoo, and MT5. Crypto choices include Binance, Binance Coin-M, Binance USDT-M, Bitfinex, Poloniex, and Coinbase Pro. `[A]`

Target connectors must be independently permissioned plugins. A source appearing here is an inventory item, not authorization to implement or access it.

### 12.2 Data-series grid

Observed columns: `[A]`

| Column | Semantics |
|---|---|
| Symbol Name | User-facing series identity |
| Instrument | Catalogue instrument reference |
| Broker profile | Versioned costs/session/timezone profile |
| Underlying Symbol | Provider symbol mapping |
| Timeframe | Series aggregation |
| Timezone | Stored/display calendar context |
| Date from / Date to | Coverage bounds |
| Total Days | Coverage summary |
| Total Records | Stored observation count |
| Source | Connector/import lineage |
| Bar type | Time/tick/other supported aggregation |
| Data type | Forex/futures/stock/etc. classification |
| Hide | Presentation visibility |
| Progress/actions | Current job state and row commands |

The current HaruQuantAI transport already exposes capability discovery, series, instruments, brokers, symbols, bars, quotes, reference sync, quality, timezone clone, export, download/config, batch, and import under `/api/v1/data/*`. `[R]`

### 12.3 View, edit, and quality analysis

- View metadata and series statistics.
- Data tab with pageable observations.
- Chart tab with market-series visualization.
- Analyze quality tab covering gaps, spikes, invalid OHLC, timeline, and issue details.
- Edit, delete, hide/skip, refresh/synchronize, clone timezone, export, and provider-specific download/import.
- Quality fixes must be explicit transformations that produce lineage; viewing an issue must never alter data.

### 12.4 Instruments

Observed columns are Instrument, Description, Broker profile, Point value, Pip/Tick size, Pip/Tick step, Default spread, Default slippage, Commissions, Swap, Data type, Order size multiplier, and Order size step. The standalone QDM view omits commission and swap columns. `[A]`

Operations include add, clone, edit, mass edit, search/filter, import, and guarded delete. Sector, exchange, and country fields are also present in the current controller model. `[A]`

### 12.5 Sessions

The session list shows Session Name and Broker profile. A session contains ordered elements with Start day, Start time, End day, End time, and end-of-day/close flag (`SEOC` in the shipped grid), plus a Monday-to-Friday shortcut. `[A]`

### 12.6 Broker profiles

Observed broker columns are Name, Description, Postfix, Timezone, Customized stocks, Customized instruments, and Customized sessions. Standalone QDM omits customized stocks. `[A]`

Profiles support add/edit/clone/delete, stock lists where applicable, instruments, sessions, and XML import/export. Default/system profiles are protected. Timezone changes are constrained when stored data already uses a profile. `[A]`

### 12.7 Stock groups

The shipped stock-group grid includes Name, Count, Description, Number of symbols, Downloaded, Ready to use?, Data from, and Data to. `[A]` Operations include add/edit, edit stocks, CSV/XML exchange, update/download data, and guarded delete. System groups are protected.

### 12.8 External indicators

Observed operations include add/edit/delete, import, define a new format, recognize, and view. `[A]` In HaruQuantAI, imported indicators must become versioned Data/Strategy plugin artifacts with a compatibility and security report, never executable UI content.

### 12.9 Global transfer control

The donor exposes total transfer progress with pause all, continue all, stop all, and settings. `[A]` The target Jobs widget should show per-connector and aggregate state while keeping each command scoped and authorized.

### 12.10 Data requirements

| ID | Requirement | Acceptance |
|---|---|---|
| DAT-001 | Reuse the existing reference-data boundary. | SQX widgets call public data capabilities through Interfaces; no second instrument/broker/session store is created. |
| DAT-002 | Version data and profile inputs used by research. | A historical run remains resolvable after profiles or series are updated. |
| DAT-003 | Keep bulk bars out of SQLite. | SQLite stores metadata/lineage; Arrow/Parquet artifacts store bulk series under atomic commit rules. |
| DAT-004 | Validate source-specific configuration in the connector owner. | Interfaces never contains provider URLs, parsing logic, or credential handling. |
| DAT-005 | Make quality rules versioned. | Gaps/spikes/OHLC findings record rule, threshold, calendar, series version, and status. |
| DAT-006 | Make fixes non-destructive. | Repair creates a new artifact/version and lineage edge; original evidence remains retained by policy. |
| DAT-007 | Support pageable preview and chart levels. | Preview bounds and downsampling are declared; full files are not sent to the browser. |
| DAT-008 | Govern delete and clone. | Impact analysis covers runs, strategies, exports, aliases, and profiles before mutation. |
| DAT-009 | Protect credentials and licensed feeds. | Secrets remain in the platform secret facility; logs/events expose only redacted connector identities. |
| DAT-010 | Preserve import/export manifests. | Source, schema, timezone, delimiter/format, checksum, record counts, warnings, and output paths/artifacts are inspectable. |

---

## 13. Custom Projects

Custom Projects is a durable Orchestration-owned task graph, not a macro recorded in the browser. `[I]` The observed gallery offers new/open project cards and task/databank/strategy counts. The editor has a left task flow and shared configuration/results surfaces. `[A]`

### 13.1 Task-flow actions

- Add task; clone below or at end; rename; delete.
- Copy configuration from/to tasks; mass apply compatible configuration.
- Reorder; enable/disable.
- Run from here; run this only; run the whole project.
- Switch between visual and text flow representations where useful.

### 13.2 Observed task catalog

| Category | Task types |
|---|---|
| Research | Build, Optimize, Retest, Filtering, Automatic Retest, Automatic Portfolio Builder, Create Portfolio, Custom Analysis, Neural Network Trainer `[U]` |
| Configuration/data | Apply Mass Config, Update Data, Load Files, Save Files, Clear Databanks |
| Control flow | Wait, Stop/Start, Go To Task |
| Integration | External Script, Notification |
| Maintenance/observability | Delete File, Log Databank Stats |

### 13.3 Go To and conditions

Observed condition dimensions include cycle count, duration, activated/evaluated count, result count, and runtime. `[A]` The target must make loops finite by construction or require an explicit budget/stop condition.

### 13.4 Orchestration requirements

| ID | Requirement | Acceptance |
|---|---|---|
| PRJ-001 | Store a versioned typed task graph. | Nodes, edges, schemas, enabled state, capability versions, and UI coordinates are separately represented. |
| PRJ-002 | Validate before publish/run. | Missing capabilities, incompatible schemas, unreachable nodes, unbounded cycles, and invalid resource budgets are reported. |
| PRJ-003 | Separate project draft from run instance. | Editing a project after start never changes an active run. |
| PRJ-004 | Support run whole/from-here/only with explicit input resolution. | The planned node set and reused/skipped outputs are previewed before start. |
| PRJ-005 | Keep domain tasks delegated to their owners. | Build invokes Research, simulation invokes Simulator, portfolios invoke Portfolio, and data tasks invoke Data capabilities. |
| PRJ-006 | Make utility tasks sandboxed. | External scripts, file operations, and notifications require declared permissions, bounded inputs, redacted logs, and audited outcomes. |
| PRJ-007 | Preserve per-node attempts and artifacts. | Retry creates an attempt record and never overwrites prior diagnostics. |
| PRJ-008 | Implement condition evaluation deterministically. | Condition inputs and evaluation version are stored; branches are replayable. |
| PRJ-009 | Bound loops and budgets. | Cycle, time, result, compute, and storage limits can stop a project with a typed reason. |
| PRJ-010 | Support safe cloning and mass configuration. | Compatibility is schema-based; incompatible fields are listed and never silently dropped. |
| PRJ-011 | Expose run history and lineage. | Project → run → node attempt → domain run → artifact can be navigated in both directions. |
| PRJ-012 | Recover after restart. | Durable state resumes or terminates according to provider checkpoint policy; browser state is irrelevant. |

---

## 14. AlgoWizard

The observed Build 144 AlgoWizard (version 1.8.87 in the UI) exposes an Editor ribbon with New, Files, Examples, Undo, Redo, Source code, Backtest results, and AI Wizard. Its empty state offers New Strategy, Load from file, Random groups, and Custom blocks. `[L]`

Observed example cards include EMA Cross, Inside Bar Breakout, Grid Example 1, Range Breakout, Bearish Divergence, Trail Stop by EA, Trail Stop by Lowest, Buy Dips, Mean Reversion, and Breakout. `[L]` Target examples must be original HaruQuantAI templates with tested provenance and educational intent.

### 14.1 Target editor model

- Strategy AST is the source of truth.
- Canvas/tree/form/source representations are projections of the same versioned AST.
- Undo/redo is local edit history until save; saved revisions remain immutable/auditable.
- Nodes come from the registered Strategy block-catalog capability and plugin contributions, and carry typed ports, constraints, defaults, compatibility, help, and generator mappings.
- Invalid graphs remain editable but cannot run or generate code; validation explains exact nodes/edges.
- Backtest results launch a Simulator run against the current saved or explicitly snapshotted draft.
- AI assistance proposes a patch/diff with rationale and constraints. It never directly publishes, executes, or overwrites a strategy.

### 14.2 AlgoWizard requirements

| ID | Requirement | Acceptance |
|---|---|---|
| AW-001 | Create, load, edit, and version a typed strategy AST. | Visual and structured-source round trips preserve semantics for supported nodes. |
| AW-002 | Provide node discovery and insertion. | Search/category/provider filters and compatibility explanations work by keyboard and pointer. |
| AW-003 | Validate incrementally. | Errors identify node/port/path and block run/export only where necessary. |
| AW-004 | Support grouped/random/custom block constructs. | Each construct serializes to the public AST and records its plugin owner. |
| AW-005 | Generate preview/source through Strategy capabilities. | UI never embeds target-language generation rules. |
| AW-006 | Launch a backtest with a pinned draft snapshot. | Unsaved edits are either saved as a revision or explicitly snapshotted and identified in the result. |
| AW-007 | Make AI edits reviewable. | Proposal appears as a structured diff; accept/reject is granular and user-confirmed. |
| AW-008 | Protect proprietary and secret content. | AI requests show data-sharing scope and exclude credentials, private files, and strategy data outside the selected context. |
| AW-009 | Keep examples migration-safe. | Example schema and required providers are versioned; incompatible examples open read-only with a report. |
| AW-010 | Meet canvas accessibility needs. | A complete tree/form alternative supports all semantic edits without drag-only interaction. |

---

## 15. Code Editor and extension development

### 15.1 Observed surface

The shipped editor provides Create New; Save/Save As/Save All; Undo/Redo; Compile All/Compile/Fix Imports; Find in Files; Test Indicators; and Import/Export Extensions. It includes a searchable/collapsible navigator, open-file tabs and dirty state, split editing, locked standard snippets, and bottom log/search panels. Monaco assets are shipped. `[A]`

Observed categories include code, snippets, SQ, blocks, indicators, databank/trade columns, money management, Monte Carlo, and custom analysis. `[A]`

### 15.2 Indicator Tester

Observed actions are New, Load, Save, Save As, Add New Test, Start, Stop, refresh indicators, choose engine, reserve bars, choose test-data folder, get help, and download tests. `[A]`

Observed test-grid columns are Indicator, Test file name, Exists?, Test parameters, Decimals, Test result, and row action. The error grid is Time, SQ value, and Value from file. `[A]`

### 15.3 Target safety and ownership

- The editor is an advanced/developer widget contributed by Plugins/Strategy UI, dynamically loading Monaco only when opened.
- Files shown are plugin/workspace artifacts exposed by capabilities, never arbitrary host filesystem paths.
- Compile, fix imports, tests, and packaging execute in a sandboxed plugin toolchain with CPU, memory, time, filesystem, and network limits.
- Standard/built-in sources are read-only unless explicitly forked into a user plugin.
- Diagnostics use stable file/artifact IDs and ranges; saved outputs are immutable package artifacts.
- Installation is a separate signed/verified lifecycle action; a successful compilation does not auto-enable a plugin.

### 15.4 Requirements

| ID | Requirement | Acceptance |
|---|---|---|
| CED-001 | Browse only authorized plugin/workspace resources. | Path traversal and arbitrary drive access are rejected by the owning capability. |
| CED-002 | Preserve dirty state and conflict detection. | External revision changes produce a three-way compare; save never silently overwrites. |
| CED-003 | Compile/test asynchronously in isolation. | Resource limits, diagnostics, toolchain version, input hash, and output artifact are recorded. |
| CED-004 | Search without leaking other plugins. | Results are permission- and package-scoped with capped payloads. |
| CED-005 | Import extensions through quarantine. | Manifest/schema/signature/permission/compatibility scans complete before preview or install. |
| CED-006 | Export reproducible packages. | Package contains manifest, compatible contracts, resources, hashes, and build metadata; secrets are excluded. |
| CED-007 | Compare indicator values deterministically. | Engine/data/profile/version/decimal policy are pinned and discrepancies are pageable/exportable. |
| CED-008 | Keep compile logs safe. | Output is structured, bounded, redacted, and cannot inject host markup. |

---

## 16. Operational, developer, and conditional surfaces

### 16.1 Grid Control / Jobs

The observed Grid Control has Local Grid selection and refreshes roughly every three seconds. `[A]` Its grids are:

| State | Columns |
|---|---|
| In progress | Job ID, Job group ID, Type, Status, Created, Started, Run time, Progress |
| Waiting | Job ID, Job group ID, Type, Created |
| Finished | Job ID, Job group ID, Type, Created, Started, Duration, Status/error detail |

Target requirements:

- unify research, simulation, data, export, plugin-build, and portfolio jobs by public job reference;
- show local/remote worker pools only when an Orchestration capability declares them;
- use SSE rather than polling where supported, with a bounded snapshot fallback;
- authorize pause/stop/retry/inspect per job;
- separate user-facing failure reason from redacted diagnostics;
- never expose raw worker commands or secrets.

### 16.2 Debug Console

Developer-only structured event/log view with component, feature, request, trace, run/job, severity, and timestamp filters. Copy/export is redacted. Production default is off; retention and access are policy-controlled.

### 16.3 Benchmark

The donor settings menu exposes a Benchmark command, but its current detailed controls were not validated in the live pass. `[L][U]` HaruQuantAI should expose only a host-owned, reproducible performance diagnostic with named hardware/runtime/dataset and exportable measurements; it is not part of strategy performance analysis.

### 16.4 Volume and Market Profile

The inspected shell exposes a Volume & Market Profile Addon entry and a license/promotion popup. `[L][A]` Build 144 documents Volume Profile and TPO. `[D]` Target implementation is an Analytics/Strategy plugin set with chart layers, derived-series contracts, and compatibility flags—not a global license popup.

### 16.5 SQ4Business

This surface is hidden/edition-controlled in the shipped registration but visible for the inspected license. `[L][A]` Its source registers tabs General, EA Parameters, Trading Options, Resources, Build, and Progress. `[A]`

Observed inventory:

- General: logo (recommended 200×200), name, strategy file, copyright, link, version, EA comment, description.
- EA Parameters and Trading Options: show/hide/value policies.
- Resources: add, browse, delete.
- Build: MQL4/MQL5; unlocked, demo, fixed-size, date/account restrictions; account grid with use, name/number, demo-only, postfix, and valid-until.
- Progress: build jobs, start/pause/stop, log, output folder.

This is **not** part of core research parity. Shipping compiled/license-restricted trading artifacts requires a separate security, legal, signing, secrets, and commercial-entitlement design. Initial UI may show a capability-gated placeholder only after a product decision.

### 16.6 Getting Started

The observed home includes trial/license status, quick-start generation cards for Forex/Futures/StockPicker, advanced workflow cards, What's New, onboarding videos/steps, AlgoCloud/news/knowledge links, and support links. `[L]`

The current onboarding labels cover Platform Overview, Choose Your Market, Data Settings & Import, Using AI Strategy Templates, Generating Strategies, Robustness Testing Validation, Choosing Best Strategy, Deploying Strategy, and Portfolio Construction. Advanced workflow cards observed include Nasdaq breakout, Gold breakout, and GBPJPY breakout variants. `[L]`

The right-side resources include AlgoCloud, Latest News, Knowledge Base, and quick links to the manual, forum, YouTube, contact/support portal, roadmap, SQ Pilot, and Discord. `[L]`

HaruQuantAI should instead provide:

- environment/capability health;
- create/open research workspace;
- original market-specific starter templates;
- data-readiness and profile checks;
- recent projects/runs/results;
- documentation and risk disclosure;
- extension/plugin discovery;
- no donor news, license upsell, branding, or external community links by default.

### 16.7 Hidden/internal modules

Shipped assets reference Results overlay, Neural Network Trainer, Grid Test, Task Manager, and other development/test applications. `[A]` They are not parity commitments. A surface requires a named HaruQuantAI owner, public capability, threat model, manifest, tests, and product approval before exposure.

---

## 17. Modal, drawer, and confirmation registry

This registry is deliberately exhaustive to the current evidence ceiling. A target interaction may become a modal, side sheet, popover, full widget, or inline editor after accessibility review; matching the donor's overlay mechanism is not required.

### 17.1 Global and shell

| Interaction | Target purpose/state requirements |
|---|---|
| About | Host/build/plugin versions, legal notices, diagnostics copy |
| Configuration | Categorized platform and workbench settings with owner and restart effect |
| Remote access | Host-owned enablement, address, authentication, exposure warning, test |
| MCP Server | Host-owned endpoint/status/instructions; no raw secret display |
| SMTP | Notification-provider settings, SSL/TLS, secret reference, sender, test recipient/result |
| Settings | Language, theme/skin, zoom, onboarding preferences |
| Export format | Registered format, options schema, destination/artifact, overwrite policy |
| Start build | Effective configuration summary, estimate/budget, warnings, idempotent submit |
| Move databank | Source/target, resolved count, conflict policy, atomicity |
| Volume & Market Profile Addon | Capability status and plugin discovery; no donor licensing flow |
| Data subscription | Connector/entitlement status; host/plugin policy |
| Custom Project Notification | Channel, condition, recipient reference, template, test, secret-safe preview |
| Confirm / Error / Options | Reusable accessible primitives with typed severity and action |
| Update | Host/plugin update policy, version compatibility, changelog, restart plan |
| Promo | Omit from core product; plugin discovery may use host-approved catalog UI |
| AlgoWizard Examples | Searchable compatible template gallery with provenance |

### 17.2 Databank and Results

| Interaction | Key content |
|---|---|
| Rename databank | current/new name, conflict validation |
| Rename custom analysis | stable plugin ID plus display label |
| Filter by correlation | method, metric/series, period alignment, threshold, tie-break, preview |
| Rename selected strategies | pattern/template, sequence, collision preview, resolved IDs |
| Loading records | cancellable paging/import progress; no blocking spinner without state |
| New databank | name, description, schema/view, membership source |
| Merge strategies | selected revisions, conflict/leg rules, target strategy preview |
| Copy selected to Retester | resolved selection, target/new run config |
| Save | target artifact type, options, provenance, overwrite/version policy |
| Compare last settings of two strategies | aligned typed diff, missing/incompatible fields |
| Strategy parameters | typed parameter form, source revision, validation, new revision action |
| Run custom analysis over databank | plugin/version, options, population, estimate, output columns/artifact |
| Set note | note text, scope, author/time, audit policy |
| Optimization profile levels | thresholds/levels, preview, accessibility-safe palette |
| Correlation detail | pair identity, aligned series, method, sample, coefficient, caveats |
| Overlapping trades detail | paired trades, overlap rule, time alignment, export |
| Custom indicators platform prompt | required target/platform and compatibility explanation |
| Terminal configuration | export target settings; secrets stored by reference |
| Walk-forward display options | metric, axes, ranges, sampling, colors, 2D/3D mode |
| Create Result Analysis plugin | template, manifest, permissions, compatible schema, sandbox warning |
| New resources | resource type, name, immutable artifact upload/reference |
| Symbol differences | source/target mapping diff and explicit resolution |
| Resolve custom resources | missing plugin resources, compatibility choices, report |
| Resolve project resources | unresolved artifact/capability refs and substitution policy |

### 17.3 Builder and setting editors

| Interaction | Key content |
|---|---|
| Strategy accepted statistics | counts/rates by stage, time window, drill-down |
| Strategy dismissal statistics | typed reason funnel, stage, provider, examples |
| Total test times per elements | block/element cost distribution and caveats |
| How to add configuration | create/load/copy/preset choices |
| Text project flow | accessible textual graph/sequence |
| Visual project flow | node graph with keyboard alternative |
| Fitness evolution | generation/island series, chosen metric, sample/seed |
| Define / Modify exit | exit AST/rule form and validation |
| Correlation settings | method/alignment/threshold/negative/missing policy |
| Genetic settings | populations, islands, generations, selection/mutation/restart and seed |
| Commission settings | profile reference or typed rate/rules with units |
| Edit parameter / block | schema-driven form, allowed distribution and constraints |
| Edit possible options | included values/ranges and incompatibilities |
| Cross-check settings | plugin schema, position, budget, pass/fail policy |
| Add new log statistics | registered metric/aggregation/format |
| Automatic preset parameter distribution | proposed ranges with diff/accept |
| Configure automatic filter | predicate tree, sample, preview counts |
| Fit portfolio correlation | population, alignment, threshold, action |
| What-to-build additional settings | architecture/provider-specific schema |
| Calibrate indicators | data sample, method, bounds, preview and apply diff |

### 17.4 Custom Projects

| Interaction | Key content |
|---|---|
| Modify symbols bulk | resolved tasks, mapping, compatible fields, preview |
| Add / Rename project | identity, display name, description, concurrency/audit state |
| Copy config from tasks | source, compatible targets, field diff, exclusions |
| Copy config to tasks | target set, overwrite policy, validation report |
| Add / Rename task | type/capability, name, insertion point, default config |

### 17.5 Data Manager

| Group | Interactions evidenced |
|---|---|
| Core data | Clone timezone; Export data CSV; New file format; MT4 FXT/HST export; MT5 export; View data; Add BMF Futures Data; Delete data; Edit symbol |
| Stock groups | Add/edit Stock group; Edit stocks; import/export/update controls |
| Broker profiles | Add/edit broker profile; Edit broker stocks; import instruments/session XML |
| External indicators | Add; Edit; Delete; Import; New format; Recognize; View |
| Instruments | Clone; Add; Edit; Mass edit |
| Sessions | Clone; Session template; Session element; Monday–Friday generation |
| Crypto | Add/download source, exchange/symbol/timeframe/date choices |
| Darwinex | Add; Identify; disclaimer; download; import |
| Dukascopy | Add; Identify; CDN disclaimer; source disclaimer; download |
| Files | Add symbol; application import; import; new format; mass import |
| MT5 | Installation/account/path selection and import |
| SQ Equity | Add and conditions |
| SQ Futures | Add and conditions |
| TickDownloader | Import |
| Yahoo | Add and download |

Every provider disclaimer, credential, destination, and legal acknowledgement belongs to the connector or host permission boundary, not to a generic SQX modal.

### 17.6 Code Editor

| Interaction | Key content |
|---|---|
| Export extensions | packages, dependencies, manifest, destination, diagnostics |
| Import completed | scan/compatibility report and staged install action |
| Overwrite confirmation | immutable revision/fork options; explicit target |
| Modify indicator parameters | typed inputs, shift, defaults, units |
| Indicator tester errors | pageable Time / platform value / reference value rows |
| Indicator tester | configuration, engine, data folder/artifact, tests, progress |
| New test | indicators, test file, parameters, decimals |
| Clone | resource identity and destination package |
| Create new | registered template/type and package location |
| Find in files | scope, query/options, bounded results |
| New directory / New file / Rename file | package-scoped validated resource operation |

### 17.7 Portfolio and SQ4Business

- Buy and Hold Strategy: instrument/series, sample, capital, fees, rebalance/hold semantics, benchmark label.
- SQ4Business: Add Category, Confirm, File Picker, MetaTrader paths, Parameter Settings, Parameter Variables, and Welcome. `[A]` These remain deferred with the parent surface.

### 17.8 Overlay requirements

| ID | Requirement | Acceptance |
|---|---|---|
| MOD-001 | Use one accessible overlay foundation. | Focus trap/restore, escape policy, labeled title/description, scroll lock, and screen-reader announcements are tested. |
| MOD-002 | Preserve typed draft state. | Closing a destructive or long form warns on changes; a harmless chooser can dismiss safely. |
| MOD-003 | Keep domain validation authoritative. | Client validation improves latency; server capability errors remain visible at field and summary level. |
| MOD-004 | Make destructive scope concrete. | Confirmation names object type, count, dependencies, reversibility, and retained artifacts. |
| MOD-005 | Prevent nested-modal traps. | Resource selection and details use drawers/routes or replace the active layer with a back path. |
| MOD-006 | Support deep links where valuable. | Strategy/result/config detail can open as a docked panel; transient confirms are not URL state. |

---

## 18. Grid and table registry

### 18.1 Common grid contract

All decision-grade grids require:

- stable row IDs and schema-versioned column IDs;
- server-side cursor paging for unbounded collections;
- typed sort/filter operators and null semantics;
- keyboard navigation, range/multi-select, visible focus, and announced selection counts;
- column resize/reorder/pin/visibility and named view persistence;
- virtualized rows and, where necessary, columns;
- deterministic bulk-action resolution with exclusion preview;
- empty, loading, partial, stale, error, and permission-denied states;
- export of the server-resolved query, not only currently rendered rows;
- safe text rendering with no plugin HTML injection.

### 18.2 Major grids

| Grid | Core columns/shape | Scale strategy |
|---|---|---|
| Databank strategies | Dynamic metric/provenance columns | Cursor paging + virtual rows/columns + saved views |
| Trades | Typed trade schema | Cursor paging, query projection, downloadable Parquet/CSV artifact |
| Optimization combinations | parameter tuple, metrics, sample, state | Aggregates/top-N first, pageable full artifact |
| Walk-forward matrix | run count × OOS percentage, metric/status | Windowed matrix + accessible table |
| Correlation matrix | strategy × strategy coefficient/status | Tiled symmetric matrix, lazy pair details |
| Portfolio constituents | strategy/result, weight, capital/risk fields | Client editing for small set; server validation |
| Portfolio candidates | composition, metrics, rank, constraints | Cursor paging over committed candidates |
| Data series | QDM columns listed in §12.2 | Server paging/filter; progress events by stable row ID |
| Bars/quotes preview | time, OHLCV/tick fields, quality flags | Bounded window only; Arrow chunk or JSON page |
| Instruments | profile and trading metadata | Server filter/page; guarded batch edit |
| Broker profiles | identity/timezone/customization counts | Small catalog; optimistic locking |
| Sessions/elements | profile list plus ordered day/time elements | Small catalog; explicit order/version |
| Stock groups | identity/readiness/coverage/count | Server counts; member list paged |
| Indicator tests | indicator/file/parameters/decimals/result | Job-backed updates; error details paged |
| Jobs | IDs, group, type, timestamps, status/progress | SSE updates + snapshot/paging history |
| Project runs/node attempts | graph node, attempt, domain run, state, timestamps | Cursor history + lineage links |

### 18.3 Grid performance budgets

| Measure | Initial target |
|---|---:|
| First useful grid content on warm local data | p95 ≤ 1.0 s |
| Filter/sort response for indexed metadata query | p95 ≤ 750 ms |
| Scroll interaction | 55+ FPS on reference hardware for typical columns |
| Browser resident row objects | bounded window; never proportional to full collection |
| SSE row-update rate | coalesced to ≤ 10 visual batches/s/widget by default |
| Bulk selection | identity/query token; no client array of one million IDs |

These are proposed service objectives `[I]`; the implementation task must establish reference hardware, dataset fixtures, and measured baselines before treating them as release SLAs.

---

## 19. Chart and visualization registry

### 19.1 Donor evidence

Shipped assets reference a custom SQ4 stock chart, an equity chart implementation, Chart.js 2.8, ApexCharts, and newer Results views. Optimization and walk-forward surfaces include 3D point/bar/surface modes. `[A]` This diversity is evidence of needed chart types, not a reason to copy the library stack.

### 19.2 Target engine map

| Visualization | Default target | Notes |
|---|---|---|
| Candlestick/OHLC, volume, indicators, trade markers | Existing `lightweight-charts` 5.2 | Synchronized panes/crosshair/time scale; custom primitives where justified |
| Equity, balance, benchmark, drawdown, rolling metrics | `lightweight-charts` | Server-provided series, LOD chunks |
| Small distributions and categorical charts | Accessible SVG/canvas component | Avoid a heavyweight engine for simple bars/histograms |
| Year/month/time heatmaps | SVG/canvas heatmap | Keyboard/table alternative |
| Correlation matrix | Tiled canvas/SVG matrix | Symmetry-aware loading, pair drill-down |
| Walk-forward matrix | 2D heatmap/table primary | Accessible and analytically superior default |
| Optimization/WFM 3D | One lazy-loaded engine after spike | Candidate: Apache ECharts + `echarts-gl`, or Plotly.js; select one, not both |
| Volume Profile/TPO | Analytics-owned derived layers on market chart | Plugin-gated; validate performance and price-bin semantics |
| Project/task graph | Purpose-built accessible graph/canvas | Text/tree alternative is mandatory |

Do not adopt low-level Three.js as the default analytical API. If the 3D spike cannot meet bundle, accessibility, GPU stability, and interaction budgets, ship the 2D heatmap and table first.

### 19.3 Chart contract

Each series descriptor carries:

```text
series_id, result/artifact_id, schema_version, metric_id,
unit, currency, timezone/calendar, sample, aggregation,
point_count, level_of_detail, min/max, null policy,
provenance, generated_at, stale state
```

### 19.4 Chart requirements

| ID | Requirement | Acceptance |
|---|---|---|
| CHR-001 | Never compute canonical trading metrics in the chart component. | Chart transforms are limited to view coordinates, formatting, and declared visual LOD. |
| CHR-002 | Synchronize by typed domain coordinates. | Time, trade index, parameter tuple, and strategy pair are distinct selection types. |
| CHR-003 | Disclose sampling/downsampling. | Legend/details/export state exact, aggregated, sampled, or partial status. |
| CHR-004 | Provide accessible equivalents. | Keyboard navigation, summary, high-contrast palette, non-color encodings, and data table/export are available. |
| CHR-005 | Bound client work. | Decode/downsample occurs in a worker where needed; React state holds view windows, not full arrays. |
| CHR-006 | Handle timezone and gaps explicitly. | Trading sessions, missing bars, DST, and synthetic gaps are not visually conflated. |
| CHR-007 | Degrade without GPU acceleration. | Core 2D analyses remain functional; 3D can fall back to heatmap/table. |

---

## 20. End-to-end workflows

### 20.1 Generate and qualify strategies

1. User opens the SQX Research workspace template.
2. Data readiness resolves a versioned series, instrument, broker, session, and sample profile.
3. User creates or selects a Strategy-space revision and building-block set.
4. Builder validates capability availability, combinations, costs, budgets, and output databank.
5. Start submits one idempotent Research run; the UI observes progress over SSE.
6. Research requests Simulator evaluations, applies registered ranking/cross-check stages, and records rejection reasons.
7. Accepted results commit to an Analytics databank atomically.
8. Selecting a row opens Results; panels resolve through compatible plugin manifests.
9. User promotes a candidate to Retester, Optimizer, AlgoWizard, or portfolio work without copying hidden state.

### 20.2 Retest for robustness

1. Resolve source strategies from selected rows or a saved query.
2. Preview exact IDs, baseline results, alternate data contexts, methods, budgets, and target membership policy.
3. Run the ordered retest/cross-check plan.
4. Inspect pass/fail/rejection deltas and robustness panels.
5. Commit passing membership or a new result set; source strategies remain unchanged.

### 20.3 Optimize and promote

1. Select a strategy revision and optimizable parameters.
2. Define ranges and inspect combination scale.
3. Select Simple, Sequential, WFO, or WFM plus samples and retention policy.
4. Run and observe aggregates; fetch full points only on demand.
5. Inspect 2D matrix/profile and optional 3D views.
6. Promote a chosen parameter set to a new Strategy revision and optionally retest it.

### 20.4 Compose a portfolio

1. Send strategies/results from a databank to Portfolio Composer or define a Portfolio Master universe.
2. Resolve currency, calendar, capital, sizing, sample, and correlation compatibility.
3. Set weights manually or select a registered optimizer/search model.
4. Run Portfolio simulation and inspect combined equity, drawdown, composition, correlation, and constituent provenance.
5. Save a versioned portfolio and result; optionally add a benchmark or export a supported target.

### 20.5 Automate a research project

1. Create a project draft and add typed tasks.
2. Connect data, builder, retest, filter, optimize, portfolio, notification, and control-flow tasks.
3. Validate resources, capabilities, cycles, data contracts, permissions, and budgets.
4. Publish a project revision and start a run.
5. Observe node attempts and domain runs globally.
6. Retry or resume according to checkpoint rules; changes require a new project/run revision.
7. Navigate lineage from final portfolio back to every task, run, strategy, profile, and data artifact.

### 20.6 Extend analysis safely

1. Create/fork a plugin package from an approved template.
2. Declare result schema compatibility, panel contribution, permissions, and resources.
3. Edit and compile in the sandbox; run tests against synthetic fixtures.
4. Preview the panel with a read-only result projection.
5. Package, scan, install, and enable as separate audited actions.
6. A crash or uninstall removes only the contribution; underlying results and core views remain intact.

---

## 21. HaruQuantAI domain and capability map

### 21.1 Ownership matrix

| Product concern | Owning domain | Public capability families already declared in contracts |
|---|---|---|
| Strategy AST, block catalog, templates, chart config, versioning, code generation | Strategy | `strategy.define-ast`, `catalog-blocks`, `configure-charts`, `version-strategies`, `edit-templates`, `exchange-strategies`, `define-architectures`, `define-indicators`, `model-atm-exits`, `extend-plugin-nodes`, `generate-code`, `generate-mql5`, `generate-targets` |
| Generation, evolution, optimization, robustness, walk-forward, research budgets | Research | `research.run-research`, `test-robustness`, `optimize-parameters`, `validate-walk-forward`, `generate-strategies`, `evolve-strategies`, `accept-research`, `govern-research-budgets`, `research-stockpickers`, `assist-research-ai`, `research-neural-models`, `score-portfolio-fitness`, `monitor-market-drift` |
| Backtest engine, fills, costs, exits, indicators, result commit, perturbations | Simulator | `simulator.configure-engine`, `model-precision`, `simulate-orders`, `calculate-costs`, `manage-exits`, `run-indicators`, `commit-results`, `cache-evaluations`, `calculate-profiles`, `perturb-inputs`, `distribute-evaluations`, `simulate-stockpickers` |
| Databanks, result queries, metrics, trades, custom panels, correlation-style analysis | Analytics | `analytics.databank-membership`, `query-results`, `interpret-results`, `analyze-trades`, `exchange-results`, `bulk-databank`, `match-results`, `custom-panels`, `qualify-operations` |
| Portfolio composition, correlation, simulation, search, risk, optimization, merge | Portfolio | `portfolio.compose-portfolios`, `analyze-correlation`, `simulate-portfolios`, `search-portfolios`, `analyze-portfolio-risk`, `optimize-markowitz`, `merge-portfolios`, `extend-portfolio-methods` |
| Projects, tasks, conditions, utility/domain tasks, run history, training | Orchestration | `orchestration.define-projects`, `run-tasks`, `evaluate-conditions`, `run-domain-tasks`, `run-utility-tasks`, `track-run-history`, `train-networks` |
| Data series, quality, imports, instruments, brokers, sessions, profiles | Data/Catalogue | Existing `data.browse-reference@1`, `data.import-quantdata@1`, plus contract-owned extensions |
| Extension manifests, contributions, lifecycle, sandbox, result panels | Plugins | `plugins.declare-manifests`, `register-contributions`, `manage-lifecycle`, `sandbox-permissions`, `isolate-analysis`, `render-result-panels`, `maintain-compatibility` |
| Artifact identity, paths, layout/profile references where applicable | Workspace | Workspace public artifact/layout capabilities only |
| HTTP/SSE/OpenAPI/CLI/MCP translation | Interfaces | Cohesive transport features resolving the above capabilities |
| Docking, forms, tables, charts, commands, view state | UI features | Widget manifests requiring public capabilities |

Capability keys above are shown without version suffix where the contract family contains multiple/versioned operations. Implementation tasks must use the exact contract declarations in the repository, not copy strings from this planning table.

### 21.2 Current implementation reality

| State | Current truth |
|---|---|
| Implemented/reusable | Dockview workspace, React/Next shell, `lightweight-charts`, feature registry/composition, plugin runtime foundations, Interfaces raw ASGI/SSE patterns, `data.browse-reference@1`, `data.import-quantdata@1` |
| Contract planned but provider work remains | Most Strategy, Research, Simulator, Analytics, Portfolio, and Orchestration families required for SQX parity |
| UI work remains | SQX-specific manifests/widgets, shared research components, settings editors, databank/results/portfolio/project surfaces |
| Explicitly unresolved | Legacy `.sqx` semantics, commercial packaging, detailed AlgoWizard AI behavior, neural training surface, 3D engine choice |

This gap is important: **a declared contract is not an implemented service**. UI development must use contract fixtures/mocks only behind an explicit feature flag until a real provider passes its capability conformance tests.

#### Implementation-state audit at the evidence freeze

`Yes` means directly supported by repository evidence; `Partial` means some reusable work exists but the SQX path is not complete; `No` means absent for the required parity slice; `Unverified` means presence must not be inferred. `[R]`

| Capability area | Contract declared | Provider code | Entry point | Interfaces/gateway | UI wired | E2E verified | Notes |
|---|---|---|---|---|---|---|---|
| Reference data browsing/management | Yes | Yes | Yes | Yes | Partial | Partial/unverified for full QDM parity | Reuse `data.browse-reference@1` and `observe-market-reference`; reconcile Catalogue ownership |
| QDM v4.2 `.dat` import | Yes | Yes | Yes | Import route present | Partial/unverified | Provider tests exist; full UI E2E unverified | Narrow M1/tick format, not strategy `.sqx` |
| Strategy authoring/exchange/codegen | Yes | No for SQX parity | No required provider registration | No cohesive SQX gateway | No | No | Contracts are planning assets only |
| Simulator/backtest | Yes | No for SQX parity | No | No | No | No | Must precede decision-grade Results/Builder |
| Research Builder/Retester/Optimizer | Yes | No for SQX parity | No | No | No | No | Do not assign to Agentic or Interfaces |
| Analytics Databank/Results | Yes | No for SQX parity | No | No | No | No | Databanks are not Workspace-owned |
| Portfolio Composer/Master | Yes | No for SQX parity | No | No | No | No | Pending provider/gateway/UI work |
| Orchestration Custom Projects | Yes | No for SQX parity | No | No | No | No | Run/task graph provider required |
| Plugin manifests/sandbox/result panels | Yes | Partial folders | No plugin entry points observed | Unverified | No SQX panel host | No | Runtime activation must be proved, not assumed |
| Dockview workspace shell | UI contracts present | Yes | N/A | N/A | Yes | Partial | Static registration and layout-recovery gaps remain |

Repository drift to resolve in Phase 0:

- `docs/PROJECT.md` and parts of `docs/ARCHITECTURE.md` overstate completed domain services and refer to deleted `app/services/api`; current transport lives in `app/services/interfaces`.
- The Interfaces README describes seven registered features while `observe-market-reference` is an additional registered slice.
- Plugin implementation folders do not establish runtime availability without registered entry points and a composition/E2E check.
- Universal-storage documentation and the DuckDB-backed market-data-store implementation need one explicit authority and migration policy.

### 21.3 Dependency direction

```mermaid
flowchart LR
    UI[UI widget feature] --> IF[Interfaces public transport]
    IF --> CAP[FeatureContext capability resolution]
    CAP --> STR[Strategy]
    CAP --> RES[Research]
    CAP --> SIM[Simulator]
    CAP --> ANA[Analytics]
    CAP --> POR[Portfolio]
    CAP --> ORC[Orchestration]
    CAP --> DAT[Data / Catalogue]
    CAP --> PLG[Plugins]
    STR -. public contracts .-> CAP
    RES -. public contracts .-> CAP
    SIM -. public contracts .-> CAP
    ANA -. public contracts .-> CAP
```

Forbidden arrows include UI → database, Interfaces → domain tables/files, Research → Simulator implementation imports, Analytics → Strategy implementation imports, and plugin panels → host globals.

### 21.4 Feature registration

New providers follow repository truth:

- declare a `FeatureSpec` and manifest;
- register through the package entry-point mechanism in `pyproject.toml`;
- bind/resolve public capabilities through `ServiceRegistry`/`FeatureContext`;
- keep package `__init__.py` files empty;
- include a focused README, configuration schema, tests, health/degraded behavior, and uninstall/removal impact;
- fail closed with `CAPABILITY_UNAVAILABLE` when a required provider is absent.

The current reference points are `app/kernel/feature.py`, `app/kernel/registry.py`, `app/composition/engine.py`, and the existing feature entry points in `pyproject.toml`.

---

## 22. Proposed feature and widget decomposition

Names below are planning names, not pre-approved repository IDs.

### 22.1 Backend feature slices

| Proposed slice | Owner | Responsibility |
|---|---|---|
| strategy definition | Strategy | AST/revisions/validation/catalog/templates |
| strategy exchange | Strategy | clean import/export adapters and compatibility reports |
| strategy generators | Strategy | target code/pseudocode/XML artifacts |
| simulation engine | Simulator | deterministic evaluation and trade/result artifacts |
| research generation | Research | random/evolutionary candidate orchestration |
| research robustness | Research | cross-check plans and qualification |
| parameter optimization | Research | simple/sequential/WFO/WFM plans |
| result/databank service | Analytics | result query, membership, columns, comparisons, exports |
| trade/result analysis | Analytics | metric/series/panel projections |
| portfolio construction | Portfolio | composer, search, correlation, simulation, risk |
| project runner | Orchestration | versioned graphs, plans, node attempts, history |
| analysis panel runtime | Plugins | manifest, sandbox, bridge, lifecycle |
| data reference manager | Data/Catalogue | extend existing implementation only where contracts require |

### 22.2 Interfaces slices

Do not create one feature per route. Use a small number of cohesive boundary adapters that resolve domain capabilities. Existing `observe-market-reference` remains the data boundary. Contract gaps already identify concepts such as `interfaces.operate-research@1`, `interfaces.operate-portfolios@1`, and `interfaces.edit-projects@1`; exact names/scopes must be ratified through the repository contract process.

Likely cohesive adapters:

- strategy authoring/exchange;
- research and simulation operations;
- analytics/databank/result observation;
- portfolio operations;
- project authoring/runs;
- plugin development/lifecycle.

### 22.3 UI widget manifest catalog

| Widget type (proposal) | Natural owner | Required capabilities | Default placement |
|---|---|---|---|
| `sqx-navigator` | Workspace UI | capability discovery, recent resources | left |
| `strategy-editor` | Strategy UI | define/version/catalog/generate | center |
| `strategy-search-space` | Strategy/Research UI boundary owner | strategy definition + research validation | center |
| `research-settings` | Research UI | research plans, budgets | center |
| `run-monitor` | Orchestration UI | job/run observation and control | bottom/right |
| `databank-grid` | Analytics UI | membership/query/bulk operations | bottom/center |
| `result-overview` | Analytics UI | interpret/query results | center |
| `trade-list` | Analytics UI | analyze/query trades | bottom |
| `equity-chart` | Analytics UI | result series | center |
| `trade-analysis` | Analytics UI | analysis panels | center |
| `trades-on-chart` | Analytics + Data UI owner | result trades + market series | center |
| `robustness-results` | Research UI | robustness/WF/optimization results | center |
| `portfolio-composer` | Portfolio UI | compose/simulate/optimize | center |
| `portfolio-search` | Portfolio UI | search/correlation/risk | center |
| `project-editor` | Orchestration UI | define/validate projects | center |
| `project-runs` | Orchestration UI | run history/node attempts | bottom/right |
| `data-manager` | Data UI | existing browse/import/quality capabilities | center |
| `plugin-code-editor` | Plugins UI | authorized resources/build/test/lifecycle | center |
| `result-plugin-frame` | Plugins UI | render isolated analysis panel | center |

Before adding new widget-type strings, audit existing `WIDGET_TYPES` entries such as strategies, optimization, portfolio, data, and analytics. Reuse them only when ownership and lifecycle match; do not overload a generic type to bypass a manifest.

### 22.4 Widget manifest contract

The existing manifest model already supports feature ID, widget type/version, title/description, required/optional capabilities, placement/dimensions, commands, subscriptions (`sse`/`poll`), effects, accessibility, and removal. SQX work should extend this model only for demonstrated gaps such as typed cross-widget selection channels or layout-template contributions.

Manifests do **not** currently self-register. Until a separately tested registry refactor lands, every new widget type must be added consistently to `WIDGET_TYPES` and its Zod schema, `WidgetContentHost`, the sidebar/catalogue, and the SQX workspace template. Each step needs a provider-missing and plugin-removal test.

Each widget README must state:

- user outcome and non-goals;
- feature owner and capability dependencies;
- authoritative vs presentation state;
- commands/effects and authorization;
- event/subscription schemas;
- loading/empty/error/degraded states;
- performance/data-volume assumptions;
- accessibility contract;
- test fixtures and removal behavior.

---

## 23. Transport and API plan

### 23.1 Preserve the current envelope

Do not introduce an SQX-specific response wrapper. The current `app/contracts/interfaces/models.py` contract remains authoritative:

```text
ApiResponse
  status
  message
  data
  error
  metadata
  schema_version

ApiError
  code
  message
  details
  request_id
  trace_id
  retryable

ApiMetadata
  contract_version
  schema_id
  request_id
  route
  operation
  trace_id
  side_effect = none | read | write | governed_write | stream
  duration_ms
  timestamp
  stale / stale_reason
  next_cursor
  page_size
  idempotency_replayed
```

The stream envelope is `StreamEvent` with sequence, request/trace IDs, route, event type (`heartbeat`, `payload`, `error`), timestamp, payload/error, cursor, and schema version.

The existing typed client already uses cookies, CSRF for writes, request/trace/idempotency headers, Zod validation, a bounded GET retry, fetch-based SSE, `Last-Event-ID`, and abort handling. SQX features extend these patterns rather than create a second client.

### 23.2 Command/query/event rule

| Operation | Transport | Response |
|---|---|---|
| Small read/query | HTTP GET/POST query | Immediate typed page/resource |
| Small validated mutation | HTTP POST/PATCH/DELETE | Immediate committed resource/version or typed conflict |
| Long-running command | HTTP POST | `202 Accepted` with job/domain-run reference and replay metadata |
| Progress/log/result availability | SSE | Ordered resumable events; snapshot/resync path |
| Pause/resume/stop/retry | HTTP command | New desired/accepted state; observed state follows by SSE |
| Large export/download | HTTP command then artifact/download endpoint | Immutable artifact reference, checksum, expiry/access policy |
| Truly bidirectional session `[U]` | Separate contract decision | WebSocket only after security, lifecycle, client, and manifest support |

The current asynchronous job contract does not include a `PAUSED` state. Pause/resume parity therefore requires an explicit domain/wire evolution and compatibility tests; the UI must not infer paused state from lack of progress.

### 23.3 Proposed resource-oriented route families

These are route shapes for design review, not permission to bypass contract ratification.

| Route family | Representative operations | Resolved owner |
|---|---|---|
| `/api/v1/strategies` | list/create definitions; revisions; validate; diff; templates; compatible blocks | Strategy |
| `/api/v1/strategies/{id}/exports` | start code/format export; inspect artifact | Strategy |
| `/api/v1/research/plans` | create/version/validate Builder, Retester, optimization, robustness plans | Research |
| `/api/v1/research/runs` | start/list/inspect/reproduce | Research |
| `/api/v1/research/runs/{id}/commands` | pause/resume/stop/retry typed commands | Research/Orchestration boundary |
| `/api/v1/research/runs/{id}/events` | progress/log/accepted/rejected/result events | Research observation |
| `/api/v1/simulations/configurations` | validate/version effective simulation config | Simulator |
| `/api/v1/simulations/runs` | explicit backtest/retest evaluation command and result reference | Simulator |
| `/api/v1/databanks` | definitions, views, member queries and governed bulk operations | Analytics |
| `/api/v1/results` | metadata, metrics, series descriptors, compatible panels, comparisons | Analytics |
| `/api/v1/results/{id}/trades` | pageable/filterable trade query | Analytics |
| `/api/v1/results/{id}/series/{series_id}` | bounded LOD/chunk retrieval | Analytics |
| `/api/v1/portfolios` | definitions/revisions/constituents | Portfolio |
| `/api/v1/portfolio-runs` | compose/search/simulate/optimize/correlate | Portfolio |
| `/api/v1/projects` | graph definitions/revisions/validation | Orchestration |
| `/api/v1/project-runs` | plan/start/history/node attempts/commands/events | Orchestration |
| `/api/v1/plugins` | manifests, compatible contributions, staged lifecycle operations | Plugins |
| `/api/v1/data/*` | reuse current series/catalogue/bars/quality/import/export/batch boundary | Data/Catalogue |

Avoid action-heavy routes such as one endpoint for every ribbon button. Commands should use typed discriminated payloads only where they share ownership, authorization, lifecycle, and response semantics.

### 23.4 Query design

Collection queries need:

```text
cursor, page_size, stable_sort[], filter_expression,
projection/columns[], include[], snapshot_token,
capability/schema version
```

- `page_size` respects the current envelope limit (currently no more than 200).
- Sort includes a stable identity tie-breaker.
- Filter expressions are a versioned AST, never raw SQL or executable text.
- A snapshot token prevents page drift for mutable collections.
- Bulk selection can use a server-issued query-selection token plus explicit inclusions/exclusions.
- Expired cursors/tokens return a typed resync outcome.

### 23.5 Job/event payload minimum

| Event | Minimum data |
|---|---|
| accepted | job/run IDs, capability snapshot, queued state, submitted timestamp |
| phase_changed | phase ID/label, state, ordinal/total where known |
| progress | completed/total where meaningful, rate, ETA confidence, coalescing timestamp |
| item_outcome | item ID, accepted/rejected/failed/cancelled, reason code, result reference where committed |
| warning | typed code, scope, user-safe detail, action if any |
| log | severity, component/provider, phase, safe message, trace link |
| artifact_available | artifact ID, kind, schema, completeness, checksum/size metadata |
| terminal | final state, committed outputs, counts, warnings, failure/cancellation summary |
| resync_required | snapshot endpoint/token and reason |

### 23.6 Authentication, authorization, and mutation gates

- Cookie/session authentication and CSRF enforcement remain host responsibilities.
- Every mutation declares `write` or `governed_write`, requires request and trace IDs, and supports idempotency where replay is possible.
- Revision edits use an optimistic-concurrency token such as an ETag/revision ID.
- File/source connectors, notifications, scripts, remote access, MCP, code builds, and custom panels require scoped permissions.
- The recorded session/authentication enforcement gap (G2) must be closed before governed SQX writes ship.
- Interfaces receives secret **references** only where a domain request requires one; it never returns secret material to widgets.
- A provider removal or permission revocation must yield `CAPABILITY_UNAVAILABLE`/typed denial, not fallback to an untrusted implementation.

### 23.7 Interfaces prohibition checklist

An Interfaces feature must not:

- import a domain implementation package;
- open SQLite/DuckDB or issue SQL;
- read/write Parquet, `.sqx`, `.dat`, source code, reports, or arbitrary paths;
- calculate P&L, drawdown, correlation, fitness, fills, or ranking;
- generate strategies or target code;
- orchestrate multi-step research beyond translating one public capability request;
- own retention, migration, reconciliation, or business retry rules;
- trust plugin/browser HTML.

---

## 24. Persistence, artifacts, and object lifecycles

### 24.1 Storage responsibilities

| Data class | Storage pattern | Owner |
|---|---|---|
| Definitions, revisions, lifecycle state, configuration metadata, indexes, audit decisions | SQLite through domain-owned repositories/tables and shared storage discipline | Owning domain |
| Bars, ticks, equity curves, large trade ledgers, indicator output, parameter surfaces, Monte Carlo samples | Immutable Arrow/Parquet or another approved artifact schema | Owning Data/Simulator/Analytics/Research domain |
| Plugin/source packages, reports, exports, imported raw files | Workspace artifact store with content hash and permission metadata | Workspace plus producing/consuming domain |
| UI layout, panel sizes, transient filters | Browser/workspace presentation store | UI/Workspace presentation feature |
| Secrets | Existing secret facility/reference only | Host/Workspace security owner |

UI and Interfaces own no durable business data.

Repository documentation and implementation currently show a storage tension: universal-storage guidance and the DuckDB-backed market-data-store path are not fully reconciled. SQX must consume the Data capability and add no third storage pattern. Phase 0 must document the accepted storage authority, locking, migration, and backup rules.

### 24.2 Artifact publication protocol

```mermaid
sequenceDiagram
    participant D as Domain provider
    participant T as Temporary artifact
    participant A as Artifact store
    participant C as Domain catalogue
    D->>T: write schema + data + manifest
    D->>T: flush and fsync
    D->>D: validate counts, schema, checksum
    D->>A: atomic promote/rename
    D->>C: commit metadata and lineage
    C-->>D: committed artifact reference
    D-->>D: emit artifact_available
```

If catalogue commit fails after promotion, reconciliation finds the unreferenced artifact. If writing/validation/promotion fails, no catalogue row points to partial data.

### 24.3 Required artifact manifest

```text
artifact_id, artifact_kind, owner_feature, schema_id/version,
content_hash, byte_size, record/point_count, created_at,
producer capability/provider/version, input artifact hashes,
strategy/config/project/portfolio revision refs as applicable,
series/profile/calendar/timezone/currency/precision context,
seed policy/value, completeness, warnings,
retention class, access scope
```

### 24.4 Object lifecycle table

| Object | Lifecycle | Immutability and deletion rule |
|---|---|---|
| Strategy definition/revision | draft → validated → published → superseded/archived | Published revision immutable; delete is governed by run/result/export references |
| Research plan/revision | draft → validated → published → superseded/archived | Run pins one revision; later edits never change it |
| Research run | accepted → queued → running → terminal; optional paused/checkpoint states after contract change | Inputs immutable; terminal state append-only; retention governs artifacts |
| Simulation configuration/result | draft/versioned config → evaluation → committed result → superseded/retained | Result immutable; correction creates a new result/version |
| Databank | active → archived → deleted | Definition mutable by revision/concurrency; membership operations audited; member artifacts remain independently owned |
| Databank view | draft/saved → updated → deleted | Presentation/query schema only; missing columns degrade safely |
| Metric definition/value | registered/versioned → computed → superseded | Values retain definition version and result hash |
| Portfolio definition/revision/result | draft → validated/published → simulated → archived | Definition revisions and results immutable once referenced |
| Project graph/revision | draft → validated → published → superseded/archived | Run pins graph revision and capability snapshot |
| Project/task run | planned → accepted/queued/running → terminal | Attempts append-only; retry creates a new attempt |
| Market series/version | ingesting → validated/available → superseded/quarantined/retired | Historical run references keep the exact version resolvable by policy |
| Import/export artifact | staged → scanned/validated → accepted/rejected → retained/expired | Raw import never mutates; derived objects link to report and hash |
| Plugin package/version | staged → scanned → installed → enabled/disabled → uninstalled | Capability withdrawal does not silently delete retained domain data |

### 24.5 Legacy files

- `data.import-quantdata@1` is for the version-pinned QuantDataManager v4.2 M1/tick `.dat` workflow already implemented. It is not a general strategy `.sqx` parser.
- Legacy strategy exchange is already shaped in contracts as `ExchangeStrategiesRequest(operation="IMPORT_LEGACY")` with a Workspace artifact ID.
- An isolated importer plugin scans and interprets the artifact, emits typed Strategy/Analytics objects, and produces a compatibility report listing imported, approximated, skipped, and unsupported elements.
- The original artifact is immutable. No donor executable/library is loaded into HaruQuantAI, and no license check is circumvented.
- Export compatibility is a separate capability per supported schema/version; round-trip equivalence must be fixture-tested.

### 24.6 Recovery and retention

- Every long run has a documented checkpoint boundary and restart policy: resume, retry stage, or fail safely.
- Cancellation stops future work, drains/terminates workers safely, labels completed outputs as partial or committed, and cleans temporary artifacts.
- Retention applies independently to logs, previews, checkpoints, committed results, raw imports, and exports.
- Removing a provider disables new resolution; it does not rewrite historical provenance or delete data outside an explicit governed removal plan.
- Backup/restore tests must cover metadata plus artifact consistency, not SQLite alone.

---

## 25. Frontend implementation plan

### 25.1 Current-stack truth

| Concern | Current target repository |
|---|---|
| Application | Next.js 15.1.x |
| UI runtime | React/ReactDOM 19 |
| Language | TypeScript |
| Docking | Dockview core/react 7.0.x |
| Charts | `lightweight-charts` 5.2.x |
| Icons | Lucide React |
| Runtime validation | Zod |
| Client state | Zustand available |
| Test tooling | Vitest/Vite tooling |
| Not currently present | Tailwind, TanStack Table/Virtual, Monaco package, ECharts, Plotly, Three.js |

Node 26 can be the validated runtime target if the repository/toolchain support it, but the production build remains Next.js. Any new dependency requires a measured spike, bundle/security/license review, owner, and removal plan.

### 25.2 State separation

| State | Location |
|---|---|
| Authoritative object/run/result | Domain service; queried by ID/version |
| Server collection snapshot/query | Typed request cache scoped to widget/resource |
| Cross-widget selection | Small typed UI event channel with stable IDs |
| Form draft | Widget-local state; save produces domain revision |
| Run progress | SSE-derived observer state; recoverable from snapshot |
| Layout/panel preferences | Dockview/UI persistence only |
| Secrets/files/data payloads | Never in layout params, localStorage, or Zustand |

### 25.3 Dockview work items

Current behavior deserves dedicated remediation tasks:

- new panels default around 580×440 instead of enforcing manifest dimensions;
- expand/restore can lose or flatten the prior split arrangement;
- an unknown/removed widget type can invalidate a saved layout rather than degrade one panel;
- widget params are opaque and need strict per-type validation/migration;
- static eager imports in `WidgetContentHost.tsx` are unsuitable for Monaco, 3D engines, large-grid code, and plugin frames.

Required fixes:

| ID | Requirement | Acceptance |
|---|---|---|
| UI-DCK-001 | Version and migrate each widget config and workspace template. | Old/unknown fields are handled deterministically with a visible recovery report. |
| UI-DCK-002 | Recover unknown widgets individually. | One removed plugin yields an “Unavailable widget” panel; the rest of the layout loads. |
| UI-DCK-003 | Enforce safe parameter schemas. | Only stable IDs and view preferences persist; payloads/secrets are rejected. |
| UI-DCK-004 | Respect manifest size/placement constraints. | First open and reset layout use declared dimensions and allowed positions. |
| UI-DCK-005 | Preserve expand/restore topology. | Automated round trip restores the exact previous split/floating structure. |
| UI-DCK-006 | Lazy-load heavy widgets. | Opening core shell does not download editor, 3D, or plugin-runtime bundles. |

### 25.4 Contextual commands

Do not recreate SQX's outer navigation rail inside a panel. HaruQuantAI remains the shell. Each owning widget can contribute context commands such as New, Load, Save, Validate, Start, Pause, Stop, Export, Compare, and Help. Commands resolve current selection and capability state; disabled controls expose a reason.

### 25.5 Shared component candidates

- `CapabilityGate` and degraded-state panel.
- `ResourcePicker` for strategy/result/databank/project/data/profile/artifact IDs.
- `RevisionBadge`, provenance popover, and diff viewer.
- Schema-driven field renderer with units/ranges/dependencies.
- `RunCommandBar`, progress summary, stage funnel, structured log.
- Virtual/cursor grid shell and named-view manager.
- Result panel host and typed cross-panel selection bus.
- Time/sample-band editor.
- Metric selector/formatter and warning badges.
- Artifact export/download control.
- Accessible matrix/heatmap and chart/table switcher.

Sharing a component does not transfer domain ownership. Domain-specific schemas and commands remain in their owning feature.

### 25.6 Proposed UI package shape

```text
app/ui/src/widgets/<cohesive-widget>/
  README.md
  manifest.ts
  config.ts
  feature.tsx
  index.ts
  components/
  hooks/
  contracts/
  __tests__/

app/ui/src/workspaces/templates/
  sqx-research-workspace.ts

app/ui/src/shared/research-ui/
  schema-fields/
  run-controls/
  grids/
  charts/
  provenance/
```

`shared/research-ui` contains presentation primitives only. It must not become a hidden business service or import domain feature internals.

### 25.7 React lifecycle rules

- React Strict Mode must not start two jobs, install two subscriptions, or duplicate writes.
- Effects are abortable and clean up SSE, observers, workers, chart instances, and timers.
- Start/write commands originate from explicit user actions and carry one generated idempotency key per logical intent.
- Widget unmount cancels observations only, not domain work.
- Reopen resolves a snapshot and resumes from the last safe cursor.
- Stale responses are discarded by resource/revision/request identity.

---

## 26. Backend implementation plan

### 26.1 Package pattern

```text
app/contracts/<domain>/
  models.py
  ports.py
  capabilities.py
  errors.py
  wire/
    schema.json

app/services/<domain>/<feature>/
  README.md
  manifest.py
  config.py
  feature.py
  <focused implementation modules>.py

app/services/interfaces/<cohesive-boundary>/
  README.md
  gateway.py
  manifest.py
  feature.py

tests/services/<domain>/<feature>/
tests/contracts/<domain>/
tests/architecture/
```

This is a pattern, not a mandate to create empty scaffolding. Add a slice only when it delivers a tested public capability.

### 26.2 Recommended delivery slice

Each backend feature should include:

1. Contract/schema tests and canonical fixtures.
2. Provider implementation behind public ports.
3. Domain repository/artifact handling with migrations and recovery.
4. Manifest, health, startup/shutdown, capability registration, and provider-removal behavior.
5. Focused unit/property/golden tests.
6. One cohesive Interfaces projection using current envelope/auth/idempotency/concurrency/SSE patterns.
7. UI integration only after fail-closed and degraded fixtures exist.

### 26.3 Numerical correctness gates

Simulator and Analytics work must establish golden fixtures for:

- no look-ahead and bar/tick availability;
- order timing, stop/limit gaps, partial/ambiguous fills, expiry, and netting/hedging policy;
- spread, slippage, commission, swap, minimum distance, and rounding;
- session calendars, holidays, DST, timezones, missing data, and reserved bars;
- long/short accounting, quantity/point value, currencies and conversions;
- equity/balance/open P&L/drawdown/stagnation;
- metric definitions and sample boundaries;
- deterministic random seeds and distributed evaluation ordering.

No UI parity claim can substitute for these domain tests.

### 26.4 Distributed work

`simulator.distribute-evaluations` and Orchestration worker concepts may support local or remote execution, but the first release should treat distribution as provider policy. Contracts need idempotent work units, leases/heartbeats, capability/version matching, cancellation, duplicate-result suppression, artifact upload, and deterministic aggregation. Grid Control observes these records; it does not schedule them itself.

---

## 27. Master functional traceability matrix

The module-specific requirements above define detailed behavior. This matrix binds the highest-risk user controls to ownership, records, persistence, failure modes, evidence, and a release test.

| FR ID | Screen/control and behavior | Owner / capability | Input → output record | Persistence owner | Failure/degraded state | Evidence | Acceptance test |
|---|---|---|---|---|---|---|---|
| FR-STR-001 | AlgoWizard/Builder saves validated AST revision | Strategy / define AST + version | draft AST → strategy revision | Strategy | invalid nodes; missing block provider; conflict | `[A][I]` | Round-trip fixture and optimistic-conflict test |
| FR-STR-002 | Block chooser resolves compatible nodes/parameters | Strategy / catalog blocks | context + filters → typed block descriptors | Strategy/Plugins | missing/disabled provider | `[A][I]` | Provider-removal and schema golden tests |
| FR-STR-003 | Source/export selector generates supported artifact | Strategy / generate target | revision + target/options → artifact + diagnostics | Strategy/Workspace | unsupported node/target; compile error | `[A][D]` | Golden export and incompatibility fixtures |
| FR-RES-001 | Builder Start launches reproducible run | Research / generate/evolve strategies | plan rev + pinned inputs → research run | Research | validation, budget, capability unavailable | `[A][D][I]` | Idempotent start and full provenance assertion |
| FR-RES-002 | Cross-check editor stores ordered plugin pipeline | Research / test robustness | pipeline draft → plan revision | Research | incompatible order/schema/provider | `[A][D]` | Serialization, reorder, removal, migration tests |
| FR-RES-003 | Optimizer validates parameter grid and runs method | Research / optimize parameters | strategy rev + plan → run/surface artifacts | Research | invalid range; too large; cancelled/partial | `[A][D]` | Method fixtures and bounded-combination test |
| FR-RES-004 | WFO/WFM classifies stability with provenance | Research / validate walk-forward | run outputs + policy → qualification artifact | Research | insufficient windows/data; incompatible metric | `[A][D]` | Golden matrix and threshold-boundary tests |
| FR-SIM-001 | Backtest evaluates one strategy/config/data context | Simulator / simulate orders | strategy + config + data versions → result bundle | Simulator | bad data/profile; engine error; cancelled | `[D][I]` | Deterministic no-lookahead/fill/cost suite |
| FR-SIM-002 | Retest applies perturbation/precision method | Simulator / perturb inputs/model precision | baseline + method/seed → scenario results | Simulator | unsupported precision/method; partial | `[A][D]` | Seed replay and perturbation provenance test |
| FR-ANA-001 | Databank query pages/sorts/filters dynamic columns | Analytics / query results | query + snapshot → result page | Analytics | expired cursor; missing column plugin; stale snapshot | `[A][D]` | 1M-row benchmark fixture and cursor correctness |
| FR-ANA-002 | Bulk move/copy/delete resolves stable population | Analytics / bulk databank | selection token + command → per-item outcomes | Analytics | conflicts; referenced item; partial policy | `[A][I]` | Page-independent selection and atomicity tests |
| FR-ANA-003 | Results Overview returns canonical metrics/provenance | Analytics / interpret results | result ID + projection → metric descriptors | Analytics | missing definition/artifact; incompatible version | `[A][D]` | Metric golden and null-reason tests |
| FR-ANA-004 | Trade list and charts share trade selection | Analytics / analyze trades | result/query/selection → trade page/series | Analytics | missing market series; too-large projection | `[A][D]` | Cross-panel identity and timezone tests |
| FR-ANA-005 | Correlation filter explains retained/removed pairs | Analytics / match/qualify results | population + policy → decision artifact | Analytics | insufficient overlap; undefined coefficient | `[A][D]` | Alignment/tie-break golden tests |
| FR-ANA-006 | Custom result panel receives read-only projection | Plugins + Analytics / render panel/custom panels | manifest + result projection → isolated panel session | Plugins | CSP/permission/schema/crash | `[A][D][I]` | Hostile panel and crash-containment tests |
| FR-POR-001 | Composer saves weighted portfolio revision | Portfolio / compose portfolios | constituents + weights/policy → portfolio rev | Portfolio | invalid sum/currency/sizing/sample | `[A][D]` | Normalization and conflict tests |
| FR-POR-002 | Composer simulates combined portfolio | Portfolio / simulate portfolios | portfolio rev + model → portfolio result | Portfolio | missing constituent result; budget/cancel | `[A][D]` | Constituent lineage and accounting fixtures |
| FR-POR-003 | Master searches constrained combinations | Portfolio / search portfolios | universe snapshot + constraints → candidates | Portfolio | combinatorial budget; no eligible candidates | `[A]` | Bound estimate, deterministic seed, stop tests |
| FR-ORC-001 | Project editor publishes validated graph | Orchestration / define projects | graph draft → project revision | Orchestration | cycle/schema/capability/permission error | `[A][D][I]` | Graph validation and migration fixtures |
| FR-ORC-002 | Run whole/from-here/only creates immutable plan | Orchestration / run tasks | project rev + start scope → project run | Orchestration | missing input; stale outputs; capability removed | `[A][D]` | Plan preview and post-edit isolation test |
| FR-ORC-003 | Go To/condition evaluates deterministically | Orchestration / evaluate conditions | condition + state snapshot → branch decision | Orchestration | unbounded loop; missing measure | `[A]` | Boundary/cycle/budget and replay tests |
| FR-DAT-001 | Data grid observes existing reference catalogue | Data/Catalogue / browse reference | cursor/filter → series/profile page | Data/Catalogue | stale/missing provider; quality warning | `[A][I]` | Existing capability conformance + UI contract test |
| FR-DAT-002 | Import QDM `.dat` through pinned importer | Data / import quantdata | Workspace artifact + options → series + report | Data/Workspace | wrong version/corrupt/path violation | `[I]` | v4.2 golden, corrupt, containment tests |
| FR-DAT-003 | Quality analysis creates versioned findings/fixes | Data / browse/quality capability | series version + rule set → findings/new version | Data | unsupported fix; conflict; partial | `[A][D][I]` | Gap/spike/OHLC rule and non-destructive repair tests |
| FR-PLG-001 | Extension import scans before installation | Plugins / lifecycle/sandbox | package artifact → scan report/staged version | Plugins/Workspace | signature/schema/permission/incompatibility | `[A][I]` | Malicious package and permission tests |
| FR-PLG-002 | Code compile/test runs outside browser/Interfaces | Plugins / isolate analysis | source package + toolchain → diagnostics/artifact | Plugins/Workspace | timeout/resource/network/filesystem denial | `[A][I]` | Sandbox escape and resource-limit tests |
| FR-IF-001 | Long command returns one job reference | Interfaces / cohesive operation | wire request → `ApiResponse<JobRef>` | None | auth/CSRF/schema/idempotency/capability error | `[I]` | Contract, auth, replay and fail-closed tests |
| FR-IF-002 | Progress SSE resumes after disconnect | Interfaces / observation | cursor + auth → ordered `StreamEvent`s | None | cursor expired; sequence gap; resync | `[I]` | Disconnect/replay/gap/expiry tests |
| FR-UI-001 | SQX template composes domain widgets | Workspace/UI manifests | template + IDs → Dockview layout | UI only | unknown widget/config migration | `[I]` | Layout round-trip and provider-removal E2E |
| FR-UI-002 | Databank/trade grids stay bounded | Analytics UI | query page/events → virtualized viewport | UI only | slow page; stale snapshot; stream burst | `[I]` | Defined 100k/1M benchmark and memory profile |
| FR-UI-003 | Charts disclose LOD and provide table fallback | Analytics UI | series descriptors/chunks → interactive view | UI only | GPU disabled; sampled/partial; missing series | `[A][I]` | Accessibility, fallback, and LOD-label tests |
| FR-UI-004 | Closing a widget never cancels domain work | All UI owners | unmount → observer cleanup only | UI only | reconnect/resync needed | `[I]` | Strict Mode/unmount/reopen E2E |

---

## 28. Non-functional requirements

### 28.1 Performance and scale

| ID | Requirement |
|---|---|
| NFR-P-001 | Establish named reference hardware and canonical small/medium/large fixtures before setting release thresholds. |
| NFR-P-002 | Keep query memory proportional to page/window, not collection size. |
| NFR-P-003 | Stream event summaries and fetch large artifacts by page/chunk; never emit a result matrix as thousands of per-cell SSE events. |
| NFR-P-004 | Cache by immutable IDs/hashes and capability versions; invalidate mutable catalogue queries explicitly. |
| NFR-P-005 | Lazy-load optional editor, 3D, plugin-frame, and advanced-analysis bundles. |
| NFR-P-006 | Record phase timing, queue delay, evaluation rate, artifact I/O, memory pressure, and error codes with trace/run IDs. |

### 28.2 Reliability

| ID | Requirement |
|---|---|
| NFR-R-001 | No catalogue entry points to a partial artifact. |
| NFR-R-002 | Retried commands cannot duplicate a run or governed mutation. |
| NFR-R-003 | Provider startup failure degrades only dependent features and produces actionable health data. |
| NFR-R-004 | Application restart preserves terminal history and either resumes or safely terminates active runs per policy. |
| NFR-R-005 | Layout corruption or plugin removal cannot corrupt domain data or prevent the rest of the workspace from loading. |

### 28.3 Security and privacy

| ID | Requirement |
|---|---|
| NFR-S-001 | Enforce least privilege for connectors, scripts, notifications, code builds, exports, remote access, MCP, and custom panels. |
| NFR-S-002 | Treat imported packages, HTML/JS, CSV, XML, strategy files, and logs as hostile input. |
| NFR-S-003 | Prevent formula injection in CSV-compatible exports and script/markup injection in grids/logs/reports. |
| NFR-S-004 | Keep credentials and secret values out of client state, event payloads, logs, traces, artifacts, and layout persistence. |
| NFR-S-005 | Audit governed writes with actor, request/trace, capability/provider, target revisions, decision, and outcome. |
| NFR-S-006 | Bind downloads to authorization, immutable artifact identity, content type/disposition, and bounded expiry where applicable. |

### 28.4 Accessibility and internationalization

| ID | Requirement |
|---|---|
| NFR-A-001 | Meet WCAG 2.2 AA for core workflows. |
| NFR-A-002 | All ribbon/toolbar, docking, graph, grid, tab, modal, and chart tasks have keyboard-complete operation. |
| NFR-A-003 | Focus survives asynchronous updates and returns predictably after panel/modal closure. |
| NFR-A-004 | State never depends on color alone; matrices/3D plots have 2D table alternatives. |
| NFR-A-005 | Units, currencies, dates, timezones, decimal separators, and metric labels are explicit and locale-safe. |
| NFR-A-006 | User content and translated labels do not become stable IDs, capability keys, or stored query fields. |

### 28.5 Financial/research integrity

- Prominently label simulated/hypothetical performance and avoid investment-advice language.
- Preserve IS/validation/OOS identity through every result, metric, grid, chart, and export.
- Disclose survivorship, data gaps, substitutions, benchmarks, and cost assumptions.
- Prevent silent use of future data, current profile values, or updated strategies in historical runs.
- Do not present optimizer or AI output as guaranteed, recommended, or live-trading-ready.

---

## 29. Delivery roadmap and exit gates

### Phase 0 — Ratify the platform seams

Deliver:

- implementation-state matrix for each required capability: contract declared, provider present, entry point registered, gateway mounted, UI wired, E2E verified;
- close or explicitly gate authentication/session issue G2;
- reconcile universal-storage guidance with the current DuckDB market-data path;
- correct documentation drift from deleted `app/services/api` to `app/services/interfaces`;
- reconcile Interfaces README registered-feature count with `observe-market-reference`;
- verify Plugins entry-point/runtime activation rather than inferring it from folders;
- approve pause/resume job-state evolution;
- approve evidence-based dependency spikes and target performance fixtures.

Exit gate: architecture tests, wire contracts, security boundary, storage authority, job lifecycle, and first vertical-slice ADRs are approved. No SQX governed write ships before this gate.

### Phase 1 — Read-only workbench and existing data reuse

Deliver:

- SQX workspace template, navigator, safe layout migrations, capability gates;
- existing Data Manager/reference/quality views using current data capabilities;
- read-only strategy/result/databank fixtures through ratified contracts;
- base cursor grid, provenance, metric formatting, equity/time-series components;
- run/job observer with synthetic SSE fixtures.

Exit gate: provider-removal, stale/error, layout recovery, large-grid, accessibility, and stream-reconnect tests pass without a production research provider.

### Phase 2 — Simulator and result truth

Deliver:

- strategy/config/data contracts sufficient for deterministic backtest;
- Simulator provider, result/trade/equity artifacts, Analytics query/metric provider;
- Overview, trade list, equity chart, trade analysis, trades-on-chart, config/source-compatible views;
- report/export baseline.

Exit gate: golden fill/cost/calendar/no-lookahead/metric tests pass; result provenance and artifact recovery are complete.

### Phase 3 — Retester and robustness

Deliver:

- Retester source resolution and batch evaluation;
- Monte Carlo/what-if/additional-market/higher-precision plugin pipeline;
- pass/fail routing, comparison, rejection explanations;
- robustness result panels.

Exit gate: deterministic seed replay, cancellation/partial results, ordered pipeline migration, and target membership tests pass.

### Phase 4 — Builder generation/evolution

Deliver:

- Strategy AST/catalog/templates/ATM and search-space editor;
- random/evolutionary Research providers, ranking, rejection, similarity/dedup;
- Builder progress/funnel/logs and committed Databank flow.

Exit gate: reproducibility, provider compatibility/removal, budget enforcement, atomic acceptance, and rejection explainability pass.

### Phase 5 — Optimization and walk-forward

Deliver:

- simple and sequential optimization;
- WFO/WFM and SPP plans/results;
- parameter grids, 2D heatmaps/profiles, stability rules;
- optional 3D engine only if the spike meets its gate.

Exit gate: method golden fixtures, IS/OOS integrity, retained-surface policy, sampling disclosure, and promotion-to-revision tests pass.

### Phase 6 — Portfolios

Deliver:

- Portfolio Composer manual weighting and simulation;
- correlation and risk analyses;
- Portfolio Master search and registered weighting/optimization methods;
- portfolio result panels and lineage.

Exit gate: currency/calendar/capital/sizing fixtures, combination budgets, correlation alignment, and constituent provenance pass.

### Phase 7 — Custom Projects

Deliver:

- typed project editor, complete core task catalog, validation, conditions/loops;
- durable project runner, node attempts, history, resume/retry;
- sandboxed utility tasks and notification integration.

Exit gate: crash recovery, graph/version immutability, bounded-loop, permission, retry, and lineage E2E tests pass.

### Phase 8 — AlgoWizard, plugin developer tools, and custom panels

Deliver:

- accessible visual/tree/form Strategy editor and original templates;
- AI patch proposal flow behind a capability and privacy gate;
- sandboxed Code Editor/Indicator Tester;
- custom Results panel SDK, CSP bridge, packaging/scanning/lifecycle.

Exit gate: AST round trip, Strict Mode, AI-review, sandbox escape, hostile panel, CSP, permission, and uninstall tests pass.

### Phase 9 — Compatibility and optional products

Candidates:

- isolated legacy `.sqx` importer/exporter based on approved fixtures and legal review;
- Volume Profile/TPO plugin pack;
- SQ4Business-like packaging after separate commercial/security design;
- neural research surface only after a supported contract and product owner;
- remote/distributed grid providers.

Exit gate is feature-specific. None blocks the core research workbench.

---

## 30. Verification matrix

| Layer | Mandatory checks |
|---|---|
| Contracts | JSON/schema golden tests, backward/forward compatibility, enum/state evolution, exact error mapping |
| Architecture | no private cross-feature imports; manifest/entry-point discovery; fail-closed removal; lifecycle cleanup; empty `__init__.py` policy |
| Interfaces | authentication, CSRF, authorization, request/trace IDs, idempotency replay, optimistic concurrency, page/cursor limits, envelope validation |
| SSE | disconnect/reconnect, `Last-Event-ID`, duplicate, out-of-order, sequence gap, expired cursor, resync, heartbeat, terminal/error, abort cleanup |
| Persistence | migrations, locks, crash during write/promote/catalogue commit, orphan reconciliation, backup/restore, governed delete, retention |
| Simulator | deterministic fills/costs/rounding, no look-ahead, DST/timezone/calendar, gaps, netting/hedging, seed replay, distributed duplicate suppression |
| Analytics | metric golden fixtures, null/undefined semantics, sample alignment, correlation, trade analysis, export projection/round trip |
| Research | search-space validation, dedup identity, ranking/rejection, stage order, budgets, cancellation/partial, WFO/WFM/optimization fixtures |
| Portfolio | weight normalization, capital/leverage/sizing, currencies, calendars, benchmark, correlation, constituent lineage |
| Orchestration | graph validation, cycles/budgets, whole/from-here/only plans, condition replay, retries, crash recovery, utility permissions |
| UI lifecycle | React Strict Mode one logical start/subscription, abort/unmount/reopen, stale response, provider removal/degradation |
| Dockview | version migrations, corrupt layouts, unknown widget, plugin uninstall, dimensions, float/split/maximize, expand/restore, keyboard docking |
| Grids | stable identity, cursor drift, sort/filter/nulls, selection across pages, bulk tokens, saved views, 100k–1M fixtures, memory/scroll metrics |
| Charts | LOD correctness/disclosure, synchronized selections, timezone/gaps, GPU-off fallback, accessible summaries/tables, export |
| Plugins | CSP, hostile HTML/JS, postMessage validation, navigation/download/network blocking, secret isolation, quotas, crash/uninstall |
| Accessibility | ribbons, tabs, grids, modals, focus restore, live announcements, contrast, zoom/reflow, graph alternative, correlation/3D alternative |
| Build | Python 3.14 checks; Node 26 compatibility; Next production build; typecheck; focused unit/integration tests; Playwright critical workflows |

### 30.1 Critical Playwright workflows

1. Recover an old layout, open the SQX template, and handle a missing optional provider.
2. Inspect data readiness, choose a versioned series/profile, and open quality findings.
3. Edit/save/validate a Strategy revision and launch a deterministic backtest.
4. Disconnect/reconnect mid-run and verify no duplicate command or missed terminal event.
5. Query a large databank, select across pages, retest, inspect rejection reasons, and open the correct result.
6. Optimize a strategy, inspect a matrix/profile, and promote a new revision without overwriting the base.
7. Compose and save a portfolio with correlation/sample warnings.
8. Publish/run a project, retry one node, restart the host, and verify lineage/history.
9. Load a hostile custom analysis plugin and confirm isolation while built-in Results continues working.
10. Complete every core workflow by keyboard with chart/table alternatives.

---

## 31. Risks, open decisions, and explicit non-claims

### 31.1 Primary risks

| Risk | Consequence | Mitigation/gate |
|---|---|---|
| Contracts mistaken for implementations | UI built against nonexistent behavior | Phase 0 six-state implementation matrix and conformance tests |
| Simulator semantic drift | Attractive but wrong research results | Golden numerical suite before Builder/Optimizer |
| Interfaces becomes a service layer | Boundary erosion and untestable ownership | Architecture imports/tests and transport-only review checklist |
| Bulk data reaches browser/SQLite | Memory, latency, corruption | Cursor/chunk/Parquet contracts and benchmarks |
| Plugin HTML/code escapes | Secret/data/host compromise | Separate sandbox, CSP bridge, hostile fixtures, default-deny permissions |
| Layout stores domain payload | stale/secret/irrecoverable state | Strict widget config schemas and stable IDs only |
| Legacy import scope expands silently | Legal, compatibility, maintenance risk | Isolated plugin, fixtures, compatibility report, explicit formats |
| Optimization encourages overfitting | Misleading decisions | sample integrity, robustness evidence, warnings, reproducible configs |
| Optional chart/editor dependencies dominate bundle | Slow core UX and supply-chain risk | lazy-load spikes, one engine per gap, removal plan |
| Documentation/code drift | Wrong paths and false status | repository-truth audit as Phase 0 gate |

### 31.2 Decisions still required

1. Exact minimum viable Strategy AST and supported execution semantics.
2. Which declared capability families receive first provider implementations and in what slices.
3. Whether FastAPI migration is a platform initiative; SQX does not decide it.
4. Pause/resume/checkpoint wire states and backward compatibility.
5. Canonical storage authority where current documentation and DuckDB implementation differ.
6. Grid primitive: extend existing implementation or approve TanStack after a benchmark spike.
7. 3D engine: ECharts GL, Plotly, or no 3D initial release.
8. Monaco/package toolchain dependency and sandbox technology.
9. Supported code-export targets and licensing/toolchain requirements.
10. Approved legacy `.sqx` versions and fidelity target.
11. AI provider/data-sharing/retention policy for AlgoWizard.
12. Commercial scope of SQ4Business, remote grid, MCP, notifications, and data connectors.

### 31.3 Explicit non-claims

This specification does **not** claim:

- pixel-perfect or literally complete discovery of every licensed/hidden SQX path;
- that presence in a shipped asset proves a control works in every Build 144 edition;
- that historical documentation describes current defaults;
- that Strategy, Research, Simulator, Analytics, Portfolio, Orchestration, or Plugins providers are currently production-ready in HaruQuantAI;
- arbitrary `.dat` compatibility beyond the pinned importer, or `.sqx` compatibility before fixture work;
- a general CUDA research toggle—the observed GPU option concerns browser acceleration/memory protection;
- Python or NinjaTrader as current SQX built-in code targets;
- TradeStation/TrueData or other data sources not separately evidenced here;
- “convert to Parquet” as a donor command—Parquet is a target persistence decision;
- a direct `app/services/api`/FastAPI service hierarchy;
- a WebSocket requirement;
- any fixed port, private default data, user strategy, credential, or proprietary algorithm;
- measured performance until the reference fixtures/hardware benchmark is run.

---

## 32. Definition of done

The core SQX workbench is done only when:

- the workspace is composed from independently owned, manifest-declared widgets;
- every visible control resolves a public capability or is presentation-only and labeled as such;
- Strategy/Research/Simulator/Analytics/Portfolio/Orchestration/Data/Plugins ownership matches §21;
- Interfaces contains transport translation only and fails closed when providers disappear;
- deterministic simulation and canonical metric golden suites pass;
- long-running commands are idempotent, recoverable, observable through resumable SSE, and provenance-complete;
- definitions, plans, runs, results, portfolios, projects, data versions, and artifacts follow the lifecycles in §24;
- Databank/trade/result grids and charts meet measured scale budgets without whole-dataset client loading;
- Dockview layouts migrate and recover from corrupt/unknown/removed widgets without domain-data impact;
- accessibility tests cover keyboard, focus, announcements, tables, charts, matrices, and task graphs;
- plugin/code/custom-panel boundaries pass hostile-input and secret-isolation tests;
- critical end-to-end workflows in §30.1 pass on Python 3.14 and the approved Node/Next production toolchain;
- documentation states actual provider/entry-point/gateway/UI/E2E status and contains no placeholder or unsupported parity claim.

---

## 33. Official source index

### Release and orientation

- [StrategyQuant X download and current build](https://strategyquant.com/download/)
- [What's new in StrategyQuant](https://strategyquant.com/whatsnew/)
- [Build 143 AlgoWizard/AI article](https://strategyquant.com/blog/strategyquant-build-143-ai-that-builds-your-trading-strategies/)
- [Build 142 article](https://strategyquant.com/blog/strategyquant-build-142-whats-new/)
- [Program layout](https://strategyquant.com/doc/strategyquant/program-layout/)
- [Settings](https://strategyquant.com/doc/strategyquant/settings/)

### Builder, testing, and optimization

- [Builder](https://strategyquant.com/doc/strategyquant/builder/)
- [Builder layout](https://strategyquant.com/doc/strategyquant/builder-layout/)
- [Genetic options](https://strategyquant.com/doc/strategyquant/genetic-options/)
- [Islands evolution](https://strategyquant.com/blog/islands-evolution-in-strategyquant-4/)
- [Strategy templates](https://strategyquant.com/doc/strategyquant/strategy-templates/)
- [Random groups](https://strategyquant.com/doc/strategyquant/random-groups/)
- [OppositeBlocks configuration](https://strategyquant.com/doc/strategyquant/use-oppositeblocks-configuration-to-control-the-negation/)
- [Data settings](https://strategyquant.com/doc/strategyquant/data/)
- [Trading options](https://strategyquant.com/doc/strategyquant/trading-options/)
- [Building blocks](https://strategyquant.com/doc/strategyquant/building-blocks/)
- [Cross checks and robustness tests](https://strategyquant.com/doc/strategyquant/cross-checks-robustness-tests/)
- [Ranking options](https://strategyquant.com/doc/strategyquant/ranking-options/)
- [Automatic Retest](https://strategyquant.com/doc/strategyquant/automatic-retest/)
- [Simple Optimization](https://strategyquant.com/doc/strategyquant/simple-optimization/)
- [Walk-Forward Optimization](https://strategyquant.com/doc/strategyquant/walk-forward-optimization/)
- [Walk-Forward Matrix](https://strategyquant.com/doc/strategyquant/walk-forward-matrix/)
- [Sequential Optimization](https://strategyquant.com/doc/strategyquant/sequential-optimization/)

### Databanks and Results

- [Databank](https://strategyquant.com/doc/strategyquant/databank/)
- [Results Overview](https://strategyquant.com/doc/strategyquant/results-overview/)
- [Strategy analysis metrics](https://strategyquant.com/doc/strategyquant/strategy-analysis-metrics/)
- [List of trades](https://strategyquant.com/doc/strategyquant/results-list-of-trades/)
- [Equity chart](https://strategyquant.com/doc/strategyquant/results-equity-chart/)
- [Trade analysis](https://strategyquant.com/doc/strategyquant/results-trade-analysis/)
- [Strategy correlation](https://strategyquant.com/doc/strategyquant/results-strategy-correlation/)
- [Trades on chart](https://strategyquant.com/doc/strategyquant/results-trades-on-chart/)
- [Strategy config](https://strategyquant.com/doc/strategyquant/results-strategy-config/)
- [Source code](https://strategyquant.com/doc/strategyquant/results-source-code/)
- [Correlation filter programming example](https://strategyquant.com/doc/programming-for-sq/filter-by-correlation-plugin-example/)

### Portfolios, projects, AI, and extensions

- [Portfolio Composer](https://strategyquant.com/doc/strategyquant/portfolio-composer/)
- [Custom Projects introduction](https://strategyquant.com/doc/strategyquant/introduction-to-custom-projects/)
- [Custom Projects concepts](https://strategyquant.com/doc/strategyquant/custom-projects-main-concepts/)
- [Go To task](https://strategyquant.com/doc/strategyquant/go-to-task/)
- [SQ AI introduction](https://strategyquant.com/blog/sq-ai-introduction/)
- [Custom blocks](https://strategyquant.com/doc/strategyquant/custom-blocks/)
- [Historical Extending SQX guide (PDF)](https://strategyquant.com/wp-content/uploads/2018/12/Extending_SQX.pdf)
- [Historical StrategyQuant Help (PDF)](https://strategyquant.com/downloads/StrategyQuant_Help.pdf)

### Data Manager

- [QuantDataManager](https://strategyquant.com/quantdatamanager/)
- [QuantDataManager what's new](https://strategyquant.com/quantdatamanager/whats-new/)
- [Broker Profiles](https://strategyquant.com/doc/strategyquant/broker-profiles/)
- [Historical data quality discussion](https://strategyquant.com/blog/historical-data-sources-quality-data-means-quality-backtest/)
- [Data Manager CLI](https://strategyquant.com/doc/cli-command-line/data-manage-data/)
- [Import to MetaTrader 5](https://strategyquant.com/doc/quantdatamanager/how-to-import-data-to-metatrader-5/)
- [Memory configuration](https://strategyquant.com/doc/strategyquant/starting-sq-with-more-memory/)

### Local evidence anchors

The implementation team may reproduce the evidence pass from the licensed installation without copying code:

- `C:\StrategyQuantX144\internal\web\SQUANT\index.html` — shell/module preload topology.
- `C:\StrategyQuantX144\internal\web\QDM\index.html` — standalone Data Manager shell.
- `C:\StrategyQuantX144\internal\web\common\Batch1\libs.js` — shipped registrations, labels, grids, dialogs, and controller behavior.
- `C:\StrategyQuantX144\internal\web\GRIDCONTROL\layout\LayoutCtrl.js` — job-grid columns and refresh behavior.
- `C:\StrategyQuantX144\internal\electron\StrategyQuantX_ui.exe` — desktop shell version metadata only.

- <code>C:\StrategyQuantX144\internal\web\GRIDTEST\layout\LayoutCtrl.js</code> and <code>layout\views\layout.html</code> — local grid stress controls, dimensions, and timers.
- <code>C:\StrategyQuantX144\internal\plugins\TaskBuild\TaskBuild.jar</code> and <code>internal\libs\SQTradingLib.jar</code> — Build 144 genetic wiring and class-behavior evidence listed in §36.10.
- <code>C:\StrategyQuantX144\internal\plugins\SettingsGeneticOptions\</code> — current bounds/defaults and stored genetic settings.
- <code>C:\StrategyQuantX144\internal\web\AlgoWizard\examples\EMACross.sqx</code> and <code>assets\InitialStrategy.xml</code> — sampled archive/XML hierarchy and node vocabulary.
- <code>C:\StrategyQuantX144\internal\extend\Snippets\SQ\Blocks\Comparisons\</code> — source-available comparator and opposite-node behavior summarized in §37.2.1.
- <code>C:\StrategyQuantX144\internal\plugins\LoaderSQ4\LoaderSQ4.jar</code> — archive loader/member-role and protected-variant evidence.
- <code>C:\StrategyQuantX144\internal\plugins\PortfolioComposer\StrSingleAsset.sqx</code> — compact format-11 orders-stream fixture.
- <code>C:\StrategyQuantX144\internal\web\SQXBUSINESS\Sample Project\SampleStrategy1.sqx</code> — format-7 and multi-result archive variant.
- <code>C:\StrategyQuantX144\internal\plugins\TaskNeuralNetworkTrainer\</code> and <code>internal\web\NEURALNETWORK\</code> — hidden neural scaffold and no-op task evidence.

Static assets are implementation evidence `[A]`, not reusable source. Runtime screenshots/captures should be stored only if they exclude private data and license/credential details and comply with project policy.

---

## 34. Handoff checklist for the first implementation task

Before coding the first vertical slice, its owner must answer:

1. What exact user outcome is delivered end to end?
2. Which capability contract/version is authoritative?
3. Is a provider present, registered, gateway-mounted, UI-wired, and E2E-verified?
4. Which inputs/revisions/artifacts are pinned, and who owns persistence?
5. What are the command, response, event, idempotency, concurrency, and cancellation semantics?
6. What happens if the provider/plugin/data/artifact disappears or is incompatible?
7. What numerical, schema, migration, security, scale, accessibility, and lifecycle fixtures prove the slice?
8. How is the feature disabled/uninstalled without corrupting retained data or layouts?
9. Which evidence tags support the product behavior, and which details remain `[U]`?
10. Does the implementation preserve HaruQuantAI as the shell and Interfaces as a strict bridge?

Only then should a focused feature task move from planning to implementation.

---

## 35. Merge contract and reconciliation policy

This section makes the merge auditable. The full source analysis in CodexSQX.md remains the normative spine of this file. Every substantive contribution from GeminiSQX.md receives one—and only one—of the following dispositions:

| Disposition | Meaning | Normative effect |
|---|---|---|
| **Retained** | Supported by current runtime, shipped assets, repository truth, or current official documentation | May drive implementation subject to the stated evidence tag |
| **Corrected** | The underlying topic is valid, but names, ownership, semantics, or confidence were inaccurate | The corrected form is normative; the original claim remains traceable in §44 |
| **Reclassified** | Useful clean-room product or algorithm design without proof that SQX implements it | Optional HaruQuantAI design input, always tagged [P][I] or [P][U] |
| **Falsified/superseded** | Direct evidence contradicts the claim or the proposal violates current HaruQuantAI architecture | Must not be implemented as stated; retained only in the reconciliation ledger |

“Nothing dropped” therefore means **complete semantic accounting**, not blind duplication of a known-wrong parser, invented current-state claim, or unsupported proprietary-algorithm assertion. The source-heading coverage ledger in §45 accounts for the entire Gemini document; the original Codex sections 1–34 are retained directly in this unified document.

### 35.1 Current state, donor evidence, target requirement, and design option

These four layers must remain visibly separate in issues, ADRs, code comments, and acceptance tests:

| Layer | Question answered | Allowed tags |
|---|---|---|
| HaruQuantAI current state | What is implemented and registered now? | [R] |
| SQX donor evidence | What is visible or structurally present in Build 144.2953? | [L], [A], [B], [D], [H] |
| HaruQuantAI target requirement | What must the product do? | [I], supported where possible by evidence |
| Optional design | How might a provider implement the requirement? | [P][I] or [P][U] |

A precise donor field name does not establish the underlying implementation algorithm. Conversely, a hidden or incomplete donor surface can still provide high-confidence evidence of registration and layout while providing low-confidence evidence of functional behavior.

### 35.2 Merge-wide requirements

| ID | Requirement |
|---|---|
| SQX-MRG-001 | Every donor/current-state assertion MUST carry an evidence tag or be explicitly labeled unresolved. |
| SQX-MRG-002 | Every carried-forward proposal MUST carry [P] and MUST NOT be represented as evidence by itself. |
| SQX-MRG-003 | Domain ownership MUST follow current HaruQuantAI contracts even where a source analysis proposed a different directory. |
| SQX-MRG-004 | Unsupported detail MAY remain as a research spike, but MUST NOT become a parity acceptance criterion. |
| SQX-MRG-005 | A contradicted claim MUST remain discoverable in §44 with the evidence-based replacement. |
| SQX-MRG-006 | CodexSQX.md and GeminiSQX.md are immutable inputs to this merge. Future changes occur in this file or in a new reviewed successor. |

---

## 36. Generator and search engine dossier

The earlier low-confidence row conflated two different questions. Build 144 exposes a rich, high-confidence generator **configuration vocabulary**, and selected implementation mechanics can be investigated independently. That does not make every generic genetic-programming technique described in the Gemini analysis an SQX fact.

### 36.1 Evidence-backed evolutionary controls

The installed Builder settings establish the following control surface. Ranges/defaults are fixture values, not recommended HaruQuantAI defaults. [A]

| Control | Observed range or choices | Observed default/example | Contract implication |
|---|---:|---:|---|
| Maximum generations | 1–100,000 | 10 | Positive bounded integer |
| Population per island | 5–50,000 | 5 | Resource estimate must multiply by active islands |
| Crossover probability | 0–100% | 50% | Store as an explicit probability, not an inferred mode |
| Mutation probability | 0–100% | 20% | Store separately from crossover |
| Number of islands | 1–100 | 10 | Provider advertises whether island execution is supported |
| Migration cadence | Every 3–100 generations | 50 | No topology is implied by this field alone |
| Migration rate | 0–20% | 20% | Exact source/target replacement policy is versioned provider metadata |
| Decimation coefficient | 1–10 | 1 | See §36.6; UI wording, not an assumed binary algorithm |
| Replace similar strategies | Toggle | true | Current engine behavior is fingerprint-based; see §36.10 |
| Replace weakest | Toggle | true | Enables periodic fresh-blood replacement |
| Replace weakest fraction | 5/10/15/20/25/30% | 10% | Part of fresh-blood controls |
| Weakest-replacement cadence | 1–500 generations | 2 | Must be disabled explicitly when unused |
| Restart on finish | Toggle | true | Finish and stagnation are independent policies |
| Restart on stagnation | Toggle | true | Provider records the fitness basis and restart event |
| Stagnation window | 3–500 generations | 30 | Restart and finish policies remain separate |
| Stagnation fitness basis | IS, IST, or ISV | Configuration-dependent | Segment metric used to detect stagnation |
| Stored IST/ISV ratio | Percentage | 50 in inspected settings service | Not visible in inspected Genetic Options HTML; segment boundaries and leakage rules must be explicit |

The shipped configuration also exposes restart-on-stagnation, restart-on-finish, replace-similar, fresh-blood, ranking/fitness, acceptance filters, data segmentation, and “parts to improve” controls. [A]

Decimation’s user-facing behavior is sufficiently clear to specify: request approximately K × as many filter-passing candidates as the retained population and keep the best candidates for population seeding. The exact order and cost of syntactic checks, coarse simulation, ranking, and deduplication remain provider-versioned semantics. [A][U]

### 36.2 Normalized strategy genome proposal

The following grammar is retained from the Gemini analysis as a **clean-room HaruQuantAI representation option**, not a claim about SQX internals. [P][I]

~~~text
Strategy :=
  EntryRules
  + ExitRules
  + OrderConfiguration
  + MoneyManagement

ConditionTree :=
  Condition
  | AND(ConditionTree, ConditionTree)
  | OR(ConditionTree, ConditionTree)
  | NOT(ConditionTree)

Condition :=
  Compare<T>(TypedExpression<T>, Operator<T>, TypedExpression<T>)

OrderConfiguration :=
  Market | Stop(trigger) | Limit(trigger)
  + optional stop-loss
  + optional profit-target
  + optional break-even/trailing/time exit
~~~

The initial port type set may include Boolean, PriceLevel, PriceDelta, OscillatorLevel, Volume, IntegerBarShift, Duration, SymbolRef, Direction, Size, and OrderIntent. [P][I] Each node descriptor MUST declare input and output types, parameter schema, evaluation clock, lookback, missing-data behavior, determinism, symmetry transform, and code-generation support.

Typed ports prevent many invalid connections, but they do **not** guarantee successful execution: data can be missing, provider capabilities unavailable, periods invalid for the sample, arithmetic undefined, or broker/simulator constraints violated. Validation therefore has four stages: schema, graph/type, data-context, and simulator preflight.

### 36.3 Long/short symmetry

Symmetry is retained as an explicit Strategy-domain transformation rather than a collection of UI conditionals. [P][I]

~~~text
mirror(GreaterThan)       = LessThan
mirror(CrossesAbove)      = CrossesBelow
mirror(LongDirection)     = ShortDirection
mirror(Price - Delta)     = Price + Delta
~~~

Constants and indicators MUST use node-provider-supplied mirror rules. For example, mapping RSI < 30 to RSI > 70 is a possible descriptor rule, not a universal arithmetic convention. Users can select symmetric generation or independently defined long and short logic; the latter expands the search space and must be visible in budget estimates.

### 36.4 Search-provider catalogue

The following catalogue retains all four engines described by Gemini while stating their actual status:

| Provider/mode | Target behavior | Evidence status |
|---|---|---|
| Random construction | Sample valid strategy graphs subject to grammar, enabled blocks, depth/size budgets, parameter ranges, and constraints | Random generation is a product requirement; Full, Grow, and Ramped Half-and-Half are candidate policies [P][I] |
| Island evolutionary search | Evolve multiple populations with configurable island count, migration cadence/rate, mutation, crossover, restarts, and fresh blood | Controls plus current ring topology/replacement mechanics are high-confidence for Build 144 [A]; target providers still declare their semantics |
| Seeded/custom improvement | Freeze, preserve-or-replace, append, or regenerate selected subgraphs of an existing strategy | “Parts to improve” is evidenced [A]; AST patch behavior is a target contract [I] |
| Parameter search | Evaluate Cartesian products for bounded discrete spaces and optionally use a continuous/evolutionary provider for larger spaces | Grid/WFO/WFM workflows are evidenced; SBX and polynomial mutation remain candidates [P][I] |

Candidate random-tree policies retained for experimentation are:

- **Full:** extend every non-terminal branch to the selected depth.
- **Grow:** allow a terminal at any valid depth.
- **Ramped half-and-half:** distribute initial candidates across depth tiers and Full/Grow policies.

Gemini’s maximum-depth example of 2–6 is retained as an experiment range, not a current SQX bound. [P][U]

The Gemini estimate of 5,000–20,000 evaluations per minute is preserved only as a benchmark hypothesis. [P][U] Throughput depends on data length, precision, block cost, language/runtime, cache state, worker count, and acceptance filters; no release target may cite that range without a reproducible fixture.

For seeded improvement, the normalized operations are:

| Operation | Target semantics |
|---|---|
| Keep existing | Lock the selected subtree against generation operators |
| Keep or regenerate | Retain the subtree or replace it according to an explicit probability |
| Keep and extend | Combine the existing subtree with a generated compatible subtree through a chosen logical/composition node |
| Regenerate | Replace the subtree with a newly generated compatible subtree |

For parameter search, the earlier limits of at most 100,000 Cartesian combinations and a WFM example spanning window sizes 10–50 and OOS percentages 10–40% are retained as planning examples only. [P][U] The real run validator calculates cardinality and resource cost from the chosen parameter/window descriptors and an approved budget.

### 36.5 Candidate selection, crossover, and mutation library

These mechanisms are retained as provider options. They are not all mandatory, and support MUST be capability-advertised and recorded in the run manifest. [P][I]

| Family | Candidate algorithms | Required safeguards |
|---|---|---|
| Selection | deterministic elitism; tournament; roulette/fitness-proportionate; rank selection | Stable tie-breaks, negative-fitness transformation, seed capture, no hidden survivorship rule |
| Structural crossover | compatible-node subtree swap; module-level entry/exit/order/MM exchange | Type compatibility, depth/node limits, immutable parents, full revalidation |
| Parameter crossover | discrete uniform/arithmetic; optional SBX for real vectors | Bounds, step snapping, unit preservation |
| Structural mutation | subtree replacement; node/operator replacement; logical inversion | Compatible return type, maximum depth, node availability |
| Parameter mutation | bounded resampling; discrete step; optional Gaussian jitter; optional polynomial mutation | Deterministic PRNG, bounds, precision and unit preservation |

Gemini’s narrower crossover probability example of 50–80% and mutation example of 10–30% are retained as experimental priors; the actual Build 144 UI accepts 0–100% for each and defaults to 50%/20%. [A][P]

For a fitness-proportionate selector with potentially negative raw scores, a provider can define

\[
P(s_i)=\frac{g(f_i)}{\sum_j g(f_j)}
\]

where g is a recorded non-negative transform. A tournament provider records tournament size, winner policy, replacement policy, and tie-break rule. The Gemini ranges k=3..7 and winner probability 0.75..1.0 are retained as examples only. [P][U]

A compatible-node crossover MUST:

1. choose a seeded parent/node selection path;
2. construct the set of donor nodes compatible by declared port type and context;
3. select deterministically from that set under the run seed;
4. swap/copy immutable subtrees;
5. enforce graph depth, node-count, lookback, and data-capability budgets; and
6. rerun schema, graph/type, data-context, and simulator preflight validation.

Candidate bounded Gaussian mutation is:

\[
\theta'=\operatorname{snap}\left(\operatorname{clip}\left(\theta+\mathcal{N}(0,\sigma^2(b-a)^2),a,b\right),\mathrm{step}\right)
\]

with σ, bounds, step, rounding, unit, and seed recorded. [P][I]

### 36.6 Decimation and generation-zero seeding

A clean-room provider MAY implement the following retained candidate pipeline. [P][I]

~~~mermaid
flowchart LR
    A[Generate candidates] --> B[Schema/type validation]
    B --> C[Static invalidity checks]
    C --> D[Budgeted coarse simulation]
    D --> E[Acceptance filters]
    E --> F[Deduplicate and rank]
    F --> G[Seed population/islands]
~~~

For target retained population N, M islands, and decimation coefficient K, the candidate budget MAY be K × M × N. The provider must say whether K counts generated candidates, simulator-completed candidates, or filter-passing candidates; the donor UI wording points toward filter-passing candidates, so those meanings cannot be silently interchanged. [A][P][U]

Retained candidate checks include self-comparisons/tautologies, impossible lookbacks, zero-trade results, and a configurable minimum trade count. Gemini’s example minimum of 10 trades is illustrative, not a default. [P][I]

### 36.7 Stagnation, validation partitions, and diversity

The configuration proves that stagnation restarts, finish restarts, IST/ISV partitioning, replace-similar, and weakest replacement are meaningful product concepts. [A] Provider mechanics must be recorded rather than inferred.

A candidate stagnation signal is:

\[
\Delta f=f_{\mathrm{best}}(g)-f_{\mathrm{best}}(g-G_{\mathrm{stag}})
\]

with a restart when improvement remains below a defined tolerance. [P][I] The earlier 80% random/20% mutated reseed split is retained as an experiment, not an observed rule. [P][U]

IST and ISV MUST be time-ordered, non-overlapping segments with an explicit boundary, timezone, warm-up policy, and leakage protection. [I] Gemini’s “set fitness to zero when ISV is negative” is preserved as a candidate penalty policy, not a fixed requirement. [P][U]

Candidate diversity signals retained for provider experiments are:

- phenotype distance from a versioned return/equity vector correlation;
- genotype distance from canonical AST tokens or tree-edit distance;
- duplicate hashes over canonical normalized graphs;
- periodic replacement of the weakest fraction; and
- novelty injection from independently seeded random generation.

Correlation direction, missing periods, resampling, and threshold semantics MUST be explicit. A Levenshtein distance over an unstable serialization is not acceptable as a canonical diversity metric.

### 36.8 Filter, fitness, and multi-objective stages

The build pipeline MUST keep hard acceptance from ranking:

~~~mermaid
flowchart LR
    A[Candidate AST] --> B[Authoritative simulation]
    B --> C[Versioned metrics]
    C --> D{All acceptance rules pass?}
    D -- No --> E[Reject with reason codes]
    D -- Yes --> F[Score/rank]
    F --> G[Population selection]
    F --> H[Destination databank]
~~~

Gemini’s example filter values—150 trades, profit factor 1.30, maximum drawdown 20%, return/drawdown 2.5, and OOS profit factor 1.10—are retained as **illustrative form values only**. [P][I] No threshold is a universal default.

Candidate scalar objectives include net-profit/max-drawdown, Sharpe, Calmar, SQN, and a weighted metric formula. All metric values and normalization functions come from versioned Analytics descriptors; Research consumes them and cannot redefine their formulas. [I]

| Candidate objective | Reference expression retained from prior analysis | Required qualification |
|---|---|---|
| Net profit / maximum drawdown | NetProfit ÷ MaxDrawdown | Currency, sign, zero-drawdown and segment policy |
| Sharpe | mean(excess return) ÷ standard deviation × square-root annualization | Return interval, risk-free series, annualization count and zero variance |
| Calmar | CAGR ÷ maximum drawdown percentage | Lookback, CAGR convention, drawdown sign and zero case |
| SQN | square-root(trade count) × mean trade ÷ trade standard deviation | Trade unit, sample/population deviation and minimum count |

\[
F_{\mathrm{weighted}}(s)=\sum_{i=1}^{m}w_i\Phi_i(M_i(s)),\qquad \sum_i w_i=1
\]

Optional multi-objective providers may implement dominance and Pareto-front ranking:

\[
A\succ B\iff(\forall i,\ f_i(A)\ge f_i(B))\land(\exists j,\ f_j(A)>f_j(B))
\]

NSGA-II-style non-dominated sorting and crowding distance are retained as one candidate, not an evidenced SQX requirement. [P][I]

### 36.9 Reproducibility and ownership

Every generated candidate and accepted strategy MUST be traceable to:

- generator provider/version and node-catalog revisions;
- parent strategy IDs and exact operator lineage;
- master seed plus deterministic child-seed derivation;
- data artifacts, symbol/timeframe/session/timezone, precision, costs, and warm-up;
- generation/island/member indexes;
- filters, metric definitions, objective/weights, and tie-breaks;
- worker/runtime version and numerical-policy fingerprint; and
- cancellation/checkpoint state.

The earlier proposed app/services/agentic/generate_strategies/ path is superseded. [P][R] Strategy owns the AST/catalog/validation/code-generation contracts; Research owns generation/evolution/optimization policy; Simulator owns authoritative evaluation; Analytics owns metrics/ranking definitions; Orchestration owns durable jobs/checkpoints; Interfaces only transports commands and events.

### 36.10 Build 144 genetic internals — high, build-specific confidence

Inspection of the current task and trading-library classes narrows the prior “unknown” area materially. These details describe the inspected Build 144 implementation; they are evidence for behavioral fixtures, not authorization to copy code or a promise that every version/plugin behaves identically. [B]

| Mechanic | Directly supported behavior |
|---|---|
| Builder wiring | GeneticBuildEngine#getGPSettings wires MersenneTwisterRng, TournamentSelection, NodeCrossover, and NodeMutation |
| Tournament selection | Fixed tournament size 3 and selection probability 0.8 in the currently wired selector |
| Population model | GPGenerationalEngine manages per-island evolution and decimation |
| Migration | Directed ring: island i sends to i+1 and the last wraps to 0 |
| Migrant selection | First floor(population × migrationRate) members of the sorted population; at least one when migration is non-zero |
| Migrant reception | Capped by inbox size and 20% of receiving population; replacement loop also prevents replacing more than half |
| Fresh blood | Periodic replacement of weakest population members is implemented |
| Similarity pruning | Integer getFingerprint() identity is used; zero-fitness candidates are removed and at most two candidates with the same fingerprint are retained |
| Structural crossover | Generated Item/Param structures are exchanged; Items match by return type; Params check key, type, random ID, and range compatibility |
| Crossover points | Current ceiling is two; an operation chooses one or two points |
| Structural/parameter mutation | Selected generated objects are regenerated/replaced by generated ID using configured ranges; this does not establish Gaussian jitter |
| Template generation | Random, Same, Opposite, and Negated placeholder-driven replacement is implemented by strategy/template generators |
| Optimization crossover | OptimizationIndexesCrossover swaps contiguous ranges of short-array combination indexes |
| Optimization mutation | OptimizationIndexesMutation replaces selected genes with a random integer in [0, combinationsCount) |

The evidence anchors are:

- internal\plugins\TaskBuild\TaskBuild.jar — GeneticBuildEngine#getGPSettings;
- internal\libs\SQTradingLib.jar — TournamentSelection, GPGenerationalEngine, NodeCrossover, NodeMutation, StrategyGenerator, StrategyTemplateGenerator, OptimizationIndexesCrossover, and OptimizationIndexesMutation; and
- SettingsWhatToBuild and SettingsGeneticOptions assets for the UI/schema bounds. [A][B]

Only “Genetic evolution” and “Random generation” appear as current Build Mode choices. [A] Seeded “parts to improve” remains a setting/workflow, not a proven third top-level Build Mode. RouletteWheelSelection exists in the library but is not wired or exposed by the inspected Builder, so it remains unavailable current-surface evidence rather than a selectable requirement. [B]

The stored trainingValidationRatio value defaults to 50 in the inspected settings service, but it is not exposed in the inspected Genetic Options HTML. It must be described as a stored/internal value, not a visible current control. [A]

These findings explicitly supersede the following donor attributions while preserving them as optional HaruQuantAI research ideas: Full/Grow/Ramped Half-and-Half initialization; tunable tournament size 3–7; rank selection; NSGA-II; real-vector/SBX/polynomial operators; Gaussian jitter; correlation/Levenshtein duplicate detection; fixed 80/20 restart reseeding; and universal arithmetic opposite transforms. [B][P]

---

## 37. AlgoWizard schema and node-semantics dossier

### 37.1 What the current fixture establishes

The installed internal\web\AlgoWizard\examples\EMACross.sqx is a ZIP archive with META-INF/MANIFEST.MF and strategy_Portfolio.xml. Its XML establishes the following sampled Build 144 vocabulary. [A]

~~~text
StrategyFile (Version="3.9.130")
├── options (strategy name, engine, version, date)
└── Strategy (allowRandom, name, engine, negateRules)
    ├── Note / Description
    ├── MoneyManagement
    ├── GlobalSLPT
    ├── Rules
    │   └── Events
    │       ├── Event key="OnBarUpdate"
    │       │   ├── Rule type="Signal"
    │       │   └── Rule type="IfThen"
    │       ├── Event key="OnInit"
    │       └── Event key="OnDeinit"
    ├── Variables
    └── Datas
~~~

Within the sample, rule graphs use nested Item, Block, Param, Formula, If, Then, and signal-variable elements. Nodes carry keys, names, return types, categories, control metadata, parameter values, and variable references. Variables use stable identifiers and can include type, default value, external visibility, minimum, maximum, and step. Data entries bind a chart, symbol, and timeframe. [A]

The Gemini XML example is retained as a useful normalized illustration, but it is **not canonical source XML**: it changed dates and keys, flattened the signal wrapper, used namespaced EMA keys not present in this fixture, and changed block-key nesting. Implementations must build adapters from real fixtures, not copy that synthetic example.

### 37.2 Sampled node vocabulary and confidence

| Category | Fixture-backed examples | What is safe to specify |
|---|---|---|
| Events | OnBarUpdate, OnInit, OnDeinit | Event identity and containment are high-confidence; exact scheduling is simulator/provider-versioned |
| Rules | Signal, IfThen, everyTick property | Signal assignment and conditional action sequencing are structurally supported |
| Logic | AND, Not, BooleanVariable; broader catalogs expose OR-like composition | N-ary/ordered graph representation with explicit short-circuit policy |
| Comparison | CrossesAbove, CrossesBelow; catalogued comparison nodes | Two-sample cross semantics are plausible but must be verified for equality/missing-value boundaries |
| Indicators/data | EMA plus chart/computed-from/period/shift metadata; broader block catalogue | Descriptor-driven nodes, never a hard-coded closed enum |
| Orders | EnterAtMarket, EnterAtStop, EnterAtLimit, ClosePosition | Typed order-intent nodes whose execution is Simulator-owned |
| Exit decorators | stop loss, profit target, break-even, trailing stop, exit-after-bars fields | Parameter shapes are supported; trigger timing and fill behavior need simulator fixtures |
| Variables | UUID-like reference, type, value, external flag, bounds and step | Stable parameter registry and optimizer eligibility |
| Data | main/additional chart, symbol and timeframe references | Stable data-binding IDs resolved through Data/Catalogue |

Additional current enums materially strengthen the structural model: timing values OnBarOpen and OnEveryTick; rule types IfThen, IfThenElse, ActionOnly, Signal, and SignalFuzzy; return types order, none, boolean, price, price range, price number, and number; generation types normal, random, same, and opposite; and placeholders Random, SameCondition, NegatedCondition, SameValue, OppositeValue, RandomCondition, RandomValue, and RandomActions. [A]

Current exit formula keys include SLPT.FixedValue, SLPT.PctValue, SLPT.ATRBasedValue, SLPT.ValueFromFormula, SLPT.PriceLevel, and SLPT.None. Pending-order fields in current examples use #BarsValid# and #ReplaceExisting#, not the earlier proposed #Expiration# field. [A]

The catalog evidence supports OnBarUpdate, OnInit, and OnDeinit; a separate OnTick event is not established. Timing is represented through values/properties such as OnBarOpen, OnEveryTick, and everyTick. Therefore “once at completed bar” versus “every tick” MUST be an explicit clock policy verified by fixtures rather than inferred from the event name. [A]

### 37.2.1 Direct comparator semantics

Shipped extension snippets provide high-confidence Build 144 behavior for common comparisons. [B]

| Node | Verified behavior |
|---|---|
| IsGreater / IsLower | Numeric operands are rounded to six decimal places before strict comparison |
| IsGreaterOrEqual / IsLowerOrEqual | Six-decimal normalization followed by inclusive comparison |
| Equals / NotEquals | Exact equality/inequality after six-decimal rounding; not an unspecified epsilon |
| CrossesAbove | Prior left is strictly less than prior right, and current left is strictly greater than current right |
| CrossesBelow | Prior left is strictly greater than prior right, and current left is strictly less than current right |
| Opposite mapping | OppositeBlock annotations explicitly pair counterpart nodes |

These findings correct Gemini’s inclusive prior crossover boundaries and unspecified float-epsilon claim. The exact six-decimal policy is a donor fixture target, not necessarily the desired numerical policy for every HaruQuantAI provider.

Current canonical keys in inspected assets/fixtures commonly include AND, EMA or talib_EMA, BooleanVariable, Equals, EnterAtMarket, EnterAtStop, EnterAtLimit, ClosePosition, and SetStopLoss. The prior namespaced keys such as SQ.Conditions.Logical.AND and SQ.Blocks.Indicators.EMA are normalized examples, not canonical donor identifiers. Signals use a signal element carrying a variable reference beneath signals; MoneyManagement examples use a Method/Params shape. [A]

### 37.2.2 Action and parameter map

| Action/family | Sampled or target parameters | Confidence boundary |
|---|---|---|
| EnterAtMarket | symbol, direction, size formula, magic/strategy reference, comment, allow duplicate trades, exit decorators | Common shape is fixture-backed [A]; exact field availability varies |
| EnterAtStop / EnterAtLimit | market-entry fields plus price formula, #BarsValid#, #ReplaceExisting# | Current keys are fixture-backed [A]; fill/expiry behavior is Simulator-owned |
| ClosePosition | symbol, direction/position selector, magic/strategy reference, full or partial size | Close action is evidenced; partial-size semantics need fixtures |
| Exit after bars | bar count and evaluation clock | Field family evidenced; off-by-one/clock semantics unresolved |
| Move stop to break-even | activation range/level plus optional added offset | Field family evidenced; ratchet/gap behavior unresolved |
| Stop loss / profit target | None, fixed value, percentage, ATR-based value, value from formula, or price level where supported | Formula-key family is evidenced [A] |
| Trailing stop | range/level formula, activation and update policy where advertised | Requires node/provider descriptor and simulator fixture |
| Variable | stable ID, name, type, value, makeExternal, optional min/max/step | Fixture-backed [A] |
| Data binding | stable ID, symbol, chart and timeframe | Fixture-backed [A] |

Direction codes, size formula keys, units, and magic-number behavior MUST be adapter/provider metadata. The earlier illustrative Long=1, Short=−1, Any=0 mapping is retained as a hypothesis until verified for each action/schema version. [P][U]

### 37.3 Normalized HaruQuantAI AST

HaruQuantAI should represent the meaning independently of donor XML. [I]

~~~json
{
  "schemaVersion": 1,
  "strategyId": "strategy-ref",
  "catalogRevision": "sha256:…",
  "dataBindings": [{"id": "main", "symbolId": "…", "timeframe": "H1"}],
  "parameters": [
    {"id": "fast", "type": "integer", "value": 50, "optimizable": true, "min": 10, "max": 100, "step": 5}
  ],
  "events": [{
    "event": "bar_update",
    "clock": "bar_close",
    "rules": [{
      "kind": "if_then",
      "condition": {"node": "crosses_above", "inputs": [{"node": "ema", "periodRef": "fast"}, {"node": "ema", "periodRef": "slow"}]},
      "actions": [{"node": "enter_market", "direction": "long", "size": {"node": "global_mm"}}]
    }]
  }]
}
~~~

The JSON is a target example [I], not donor serialization. Actual contracts should use typed models and immutable versioned artifacts rather than accepting arbitrary JSON.

### 37.4 Runtime semantics that require explicit contracts

| Semantic | Required definition |
|---|---|
| Crosses above/below | Samples used, equality boundary, missing values, timeframe alignment, and intra-bar behavior |
| Numeric equality | Exact/decimal/tolerance policy and unit compatibility |
| AND/OR/NOT | Evaluation order, short-circuit behavior, missing/unknown boolean policy |
| Indicator | Warm-up, seed, lookback, missing bars, session boundaries, adjusted data, numerical precision |
| Market/stop/limit entry | Submission clock, price source, queue/fill model, slippage, gaps, expiration, duplicate positions |
| Stop loss/profit target | Trigger side, same-bar collision policy, gap fill, currency/pips/percent/ATR units |
| Break-even/trailing | Activation source, update cadence, ratchet rule, offset, rounding and priority |
| Close/partial close | Direction selector, position matching, fraction/quantity rounding, over-close behavior |
| External parameter | Target-language name/type/range, stability across export/import, optimizer eligibility |

The Build 144 comparator behavior in §37.2.1 is high-confidence donor evidence. Gemini’s alternative inclusive crossover boundary and epsilon model are retained only as corrected claims in §44. Pending-order validity, ATR exits, partial closes, and trailing activation still require Simulator contracts and golden fixtures before they become normative target semantics.

### 37.5 Editor topology additions

The target visual editor should expose:

- separate long entry, long exit, short entry, and short exit/event sections;
- add-rule, group, negate, duplicate, delete, undo/redo, validation, and navigation actions;
- typed drag/drop or command-palette insertion from the node catalogue;
- market, stop, limit, close, break-even, trailing, time-exit, and plugin action nodes when advertised;
- an inspector showing units, default, current value, external/optimizable flag, min/max/step, expression/formula source, and validation errors;
- a parameter table that can promote literal values into stable variables without changing semantics;
- source-code and backtest-result companions, plus a read-only donor-XML diagnostic view for imported artifacts; and
- symmetry preview showing generated/mirrored short logic before the user accepts it.

Partial exits, scale-in/out, Python previews, and live indicator execution are retained as plugin-gated target possibilities, not current donor parity. [P][I]

### 37.6 Code generation

Observed donor targets remain pseudocode, MQL4, MQL5, EasyLanguage/MultiCharts, and XML. [L][A] Python and NinjaTrader generators from the prior analysis are preserved only as optional HaruQuantAI Strategy plugins. [P][I] Code output MUST identify unsupported nodes, target/provider version, parameter mapping, clock assumptions, and semantic deviations; it MUST never silently approximate an unsupported construct.

### 37.7 AlgoWizard verification matrix

| Test family | Required cases |
|---|---|
| Archive/XML fixtures | Minimal EMACross, result-bearing AlgoWizard samples, multiple StrategyFile versions, unknown elements |
| Graph conversion | XML → normalized AST → canonical internal encoding with stable IDs and a loss report |
| Node semantics | crosses equality boundaries, bar/tick clocks, missing bars, multi-timeframe alignment, indicator warm-up |
| Action semantics | market/stop/limit, gap fills, SL/PT same-bar conflict, break-even, trailing, time exit, partial close |
| Variables | external flag, typed defaults, min/max/step, renamed variables, broken/duplicate references |
| Editor | undo/redo, drag/drop keyboard equivalent, invalid connection rejection, symmetry preview, large graphs |
| Code generation | golden source snapshots plus target compile/test where a toolchain is licensed and available |

---

## 38. Legacy .sqx compatibility and migration dossier

### 38.1 Fixture-derived archive variants

Build 144 fixtures establish that .sqx is a ZIP/JAR-style container, but there is no single mandatory member tree. [A]

| Fixture class | Inspected example | Observed members |
|---|---|---|
| Minimal AlgoWizard strategy | internal\web\AlgoWizard\examples\EMACross.sqx | META-INF/MANIFEST.MF, strategy_Portfolio.xml |
| AlgoWizard strategy with results | internal\web\AlgoWizard\examples\breakout.sqx | Manifest, settings.xml, strategy XML, lastSettings.xml, one result dailyEquity.bin, orders.bin, version.txt |
| SQXBusiness sample | internal\web\SQXBUSINESS\Sample Project\SampleStrategy1.sqx | Manifest, settings, strategy, last settings, Portfolio/Main/HigherPrecision/AdditionalMarket daily-equity members, orders, version |
| Retester result | user\projects\Retester\databanks\Results\ES_H1_8101411175.sqx | Manifest, settings, strategy, last settings, Portfolio/Main/AdditionalMarket daily equity, orders, version |
| Robustness-rich result | Optimizer/Retester result fixtures | Additional RobustnessOriginalOrders.bin, Monte Carlo simulation order files, and result-specific paths |

Entry names can contain spaces, brackets, colons, symbols, and test labels. The importer MUST normalize neither names nor order until the artifact class and signature rules are understood.

### 38.2 XML and settings evidence

Current settings fixtures expose ResultsGroup, Fitnesses, ValuesMap, SettingsMap, and a Base64 value labelled SQStats version="2", alongside simulation/trading/session/cost settings. [A] This establishes an outer schema only. The Base64 payload is opaque until decoded through a separately reviewed, fixture-backed format adapter.

The importer should parse manifest and XML into:

- archive/member inventory and hashes;
- donor/build/schema identifiers;
- normalized strategy AST plus raw-source references;
- settings with known typed fields and an unknown-field bag;
- result topology and opaque binary-member metadata; and
- warnings, losses, unsupported fields, and required plugins.

All XML parsing MUST disable external entities and DTD/network resolution.

### 38.3 Binary forensic result

Direct inspection found at least two top-level orders.bin version markers:

- SQOrderFileFormat:11 in current AlgoWizard, Portfolio Composer, Optimizer, and Retester fixtures; and
- SQOrderFileFormat:7 in the shipped SQXBusiness sample. [A]

Both start with Java serialization magic AC ED 00 05 in the inspected files, followed by block-data framing, a UTF marker, additional header/metadata, and then format-specific content. Nested robustness/Monte Carlo order members can use a different compact structure and may omit the marker entirely. [A]

The earlier Gemini prototype assumed that a 32-bit record count immediately follows SQOrderFileFormat:11 and that every order is a fixed 116-byte record. Actual bytes disprove that assumption: zero/header metadata appears at the assumed count location while the archive contains non-empty result data. The proposed SQXArchiveReader/SQXArchiveWriter is therefore retained only as a **falsified prototype**, not code to port. [P][A]

### 38.3.1 Traced Build 144 reader/writer behavior

The evidence corpus contained 32 local .sqx archives. Observed StrategyFile versions include 3.9.130, 3.9.132, and 3.9.133; observed version.txt content is 1. [A] A reader MUST dispatch from detected structure/version rather than hard-code 3.9.130.

The current SQ4 loader accepts sq4, sqw, and sqx extensions, uses ZIP/JAR handling, checks encrypted and broker-locked variants, and has paths for strategy XML, settings, orders, results/daily equity, optimization profiles, last settings, and cross-check data. The current result FileHandler writes corresponding container members. [B] These facts raise confidence in member roles, but encrypted/broker-locked compatibility still needs product/legal policy and fixtures.

The inspected format-11 OrdersList serializer writes:

1. UTF marker SQOrderFileFormat:11;
2. seven integers used as format/cache metadata;
3. a string cache; and
4. order records until stream EOF. [B]

The real record stream mixes cached strings, integers, bytes, floats, longs, shorts, booleans, and additional fields. It is not the proposed sequence of int64 ticket/magic values and float64 prices. This framing is high-confidence for the inspected implementation, while exhaustive field meaning and historical formats remain low/unknown.

For completeness, the falsified prototype’s proposed business-field set was: ticket ID; order type; open time/price; close time/price; stop loss; take profit; size; commission; swap; net profit; profit in pips; magic number; MAE; MFE; and comment. It proposed order codes 0=buy, 1=sell, 2=buy stop, 3=sell stop, 4=buy limit, and 5=sell limit. [P][U] These remain useful normalized trade-schema candidates, but none of their claimed bit offsets, integer widths, float widths, ordering, count placement, or comment framing is accepted as an on-wire specification.

Observed manifests contain Manifest-Version: 1.0; the earlier Created-By and Strategy-Version manifest fields were not present in the inspected corpus. [A] Any future adapter must preserve unknown manifest attributes rather than assume this minimal set is universal.

### 38.4 Compatibility levels

| Level | Meaning | Release gate |
|---|---|---|
| C0 — Inspect | Safely list members, sizes, hashes, manifest/XML versions, and opaque sections | Malformed/hostile archive suite passes |
| C1 — Strategy import | Convert a supported strategy XML variant to the normalized AST with a loss report | Semantic AST fixtures and manual review pass |
| C2 — Result import | Decode selected settings, trades/equity/results for declared format versions | Cross-check against donor-visible values |
| C3 — Preserving rewrite | Modify supported XML while preserving unknown allowed members byte-for-byte | Donor reopen plus unknown-member checks pass |
| C4 — Semantic export | Produce a new archive the supported donor build opens with equivalent strategy/settings semantics | Donor reload/backtest comparison passes |
| C5 — Broad compatibility | Pass a declared artifact-class/version matrix | Legal/product approval and corpus exit gate |

“Full fidelity” MUST always name its level, artifact class, build range, unsupported members, and validation evidence. Bit-identical ZIP bytes are not the primary goal because timestamps, compression, entry order, and signatures can differ without semantic loss; opaque-member byte preservation and donor reopenability are stronger practical gates.

### 38.5 Isolated importer design

The existing Strategy exchange contract accepts an authorized Workspace artifact reference for legacy import. [R] The importer therefore runs behind an isolated Strategy/plugin provider:

~~~mermaid
flowchart LR
    A[Workspace artifact ID] --> B[Policy and size check]
    B --> C[Quarantined archive inspector]
    C --> D[Variant/version detector]
    D --> E[XML/settings adapters]
    D --> F[Optional binary adapters]
    E --> G[Normalized Strategy artifact]
    F --> H[Normalized result artifacts]
    C --> I[Opaque-member vault]
    G --> J[Compatibility report]
    H --> J
    I --> J
~~~

Interfaces transports the request and report only; it MUST NOT open ZIPs, parse XML, decode binaries, or write domain tables.

### 38.6 Discovery and safety protocol

The corpus MUST include minimal strategies, AlgoWizard strategies, Builder results, Retester results, Optimizer/WFO/WFM results, robustness/Monte Carlo results, portfolios, multiple engines, format markers 7 and 11, empty/no-trade artifacts, plugins, non-ASCII names, and deliberately malformed inputs. [I]

Import tests MUST cover:

- ZIP slip, absolute paths, alternate separators, duplicate names, case collisions, symlinks, nested archives, decompression bombs, member/count/ratio limits, and truncated CRCs;
- XXE/DTD/entity expansion, encoding confusion, deep XML, schema drift, unknown elements, and duplicate IDs;
- unknown binary versions, truncated block framing, impossible lengths/counts, NaN/infinity, integer overflow, and resource exhaustion;
- stable hashes, immutable originals, opaque-member retention, cancellation, timeout, and cleanup;
- semantic import → export → donor reopen for each advertised compatibility cell; and
- normalized AST evaluation against golden simulator fixtures, never only XML textual equality.

### 38.7 Required output report

Every import/export returns a durable report containing artifact hash, detected archive class and versions, parsed members, preserved opaque members, ignored members, normalized entities, warnings, losses, unsupported constructs, code-generation limitations, plugin requirements, and verification status. An import with losses may be reviewable, but cannot be presented as full-fidelity success.

---

## 39. Neural research workbench

### 39.1 Observed donor state

Build 144 ships a hidden NEURALNETWORK module registered as “Neural Network Trainer,” a NeuralNetworkTrainer task type, a shared dashboard/databank shell, and generic settings for Data, Options, Rankings, and Notes. [A] Its task XML contains an empty Databanks element. The inspected task returns immediately from start(), reports running status as zero, and returns null for used/output databanks. [B] This is a nonfunctional scaffold in the inspected build. No current evidence establishes a functioning MLP, TCN, LSTM/GRU, feature-engineering pipeline, optimizer, ROC screen, or model export.

Confidence is therefore **high for registration/shell** and **low for functional/model semantics**. The detailed Gemini material is preserved below as an optional HaruQuantAI Research provider concept, not donor parity. [P][I]

### 39.2 Optional feature pipeline

Candidate feature families:

| Family | Examples retained from prior analysis | Contract requirements |
|---|---|---|
| Price/stationarity | returns, log returns, optional fractional differentiation | Fit only on training history; store transform parameters and truncation |
| Oscillators | normalized RSI, CCI, stochastic %K/%D | Descriptor/version, lookback, scale, missing policy |
| Trend | EMA slope normalized by ATR, MACD histogram/price | No future bars; explicit timeframe alignment |
| Volatility | ATR/close, realized volatility, optional Garman–Klass ratio | Session and OHLC assumptions recorded |
| Volume/profile | volume features, distance to POC/VAH/VAL normalized by ATR | Capability-gated because profile data may be unavailable |
| Context | symbol, session, regime, spread/cost state | Prevent identity leakage and unstable categorical mappings |

Fractional differencing

\[
(1-B)^d X_t=\sum_{k=0}^{\infty}(-1)^k {d\choose k}X_{t-k}
\]

is one optional transform. Gemini’s d=0.4, search range 0.35..0.65, and ADF p<0.01 are experiment examples, not defaults. [P][U]

Every preprocessing step MUST be a fitted, versioned artifact. Train/validation/test segments reuse training-fitted scalers; they never fit on future/OOS data.

### 39.3 Optional target labeling

The retained triple-barrier proposal defines upper/lower price barriers and a time horizon from a decision time t₀. [P][I]

\[
p_{up}=p_0+k_{pt}\operatorname{ATR}(t_0),\quad
p_{down}=p_0-k_{sl}\operatorname{ATR}(t_0),\quad
t_1=t_0+H
\]

The label is the first barrier touched: long, short, or timeout/neutral. A production labeler MUST define same-bar upper/lower collisions, bid/ask versus midpoint, gaps, session closes, missing bars, horizon inclusivity, volatility snapshot, class mapping, and cost assumptions. Gemini’s 24-bar horizon is an example only.

### 39.4 Optional model and training catalogue

| Component | Retained candidates | Status |
|---|---|---|
| Model | MLP; TCN; optional LSTM/GRU | Provider options [P][I], not donor facts |
| Hidden activation | Leaky ReLU with optional batch/layer normalization and dropout | Hyperparameterized |
| Output | binary/multiclass classification, regression, or calibrated score | Must match a versioned label/decision contract |
| Loss | cross entropy; focal loss for class imbalance; regression losses | Gemini’s focal γ=2 is an example |
| Optimizer | AdamW or SGD-family | Gemini’s LR 1e-3, weight decay 1e-4, cosine schedule are examples |
| Regularization | dropout, weight decay, early stopping | Gemini’s dropout 0.2 and patience 15 are examples |
| Validation | purged/embargoed time-series folds plus final untouched OOS | Mandatory leakage guard |

The retained MLP reference applies affine transforms, normalization, Leaky-ReLU hidden activations, optional dropout, and a softmax output:

\[
h_1=\operatorname{LeakyReLU}(\operatorname{Norm}(W_1x+b_1)),\qquad
h_l=\operatorname{Dropout}(\operatorname{LeakyReLU}(\operatorname{Norm}(W_lh_{l-1}+b_l)))
\]

\[
\hat y=\operatorname{Softmax}(W_{\mathrm{out}}h_L+b_{\mathrm{out}})
\]

The retained focal-loss reference is

\[
\mathcal{L}_{\mathrm{focal}}=-\alpha_t(1-p_t)^\gamma\log(p_t)
\]

with Gemini’s γ=2 only an example. [P][I]

For the prior single-stack TCN example, the retained receptive-field estimate is

\[
R=1+\sum_{l=0}^{L-1}(K-1)2^l
\]

For a real TCN, the recorded receptive field must be computed from actual kernels, dilations, layers, repeats and residual blocks; the simplified expression is only valid for a specific stack. Inference MUST use causal inputs and prove that no future-padding path exists.

### 39.5 Workbench UI

If a neural provider is installed, the workbench can add:

- dataset/data-binding and feature-selection panels;
- label definition and class-balance preview;
- architecture/layer editor with parameter count and receptive-field preview;
- training controls, resource budget, seed, checkpoint, stop/resume, and early-stopping state;
- epoch curves for training/validation loss and registered metrics;
- ROC/PR and AUC where statistically appropriate, confusion matrix, calibration, threshold analysis, and per-class support;
- permutation/SHAP-like feature importance only when the provider declares the method and sampling assumptions;
- fold/window timeline showing purge, embargo, validation, and untouched OOS segments;
- model-card, lineage, reproducibility, limitations, and export compatibility; and
- result/databank routing through normal Research and Analytics capabilities.

### 39.6 Portable inference

The prior NumPy feed-forward example is retained as a conceptual export shape, not production code. [P][I] A portable model package MUST contain a versioned graph/operator set, ordered features, preprocessing parameters, tensor shapes/dtypes, weights, activation/output semantics, threshold policy, numerical tolerance, and test vectors. “Zero dependency” means the target runtime embeds only supported primitive operators; it does not excuse missing numerical or security review.

Its exact example pipeline is preserved as a non-default test vector: standardize each feature as (x−mean)/scale; apply affine hidden layers with Leaky-ReLU slope 0.01; compute numerically stabilized softmax by subtracting the maximum logit; map output indexes [0,1,2] to [short, neutral, long]; emit long or short only when its probability is at least 0.55; otherwise emit neutral. [P][U] Production class order and thresholds belong in the signed model package rather than source-code constants.

MQL4/MQL5 and Python inference are separate code-generation plugins. A model cannot be advertised for a target until exported predictions match the authoritative provider on golden vectors within declared tolerances.

### 39.7 Ownership and acceptance

Research owns feature/label/model/training contracts; Data supplies immutable input artifacts; Simulator performs strategy-level evaluation; Analytics computes registered metrics; Strategy embeds a validated inference node or generated target code; Orchestration owns training jobs/checkpoints; Interfaces transports commands/events; UI renders state. [R][I]

Minimum acceptance requires deterministic reruns under captured seeds, temporal leakage tests, train-only preprocessing, fold-boundary tests, class-support reporting, model-card generation, checkpoint recovery, resource cancellation, inference parity vectors, and comparison against simple baselines. The hidden donor task alone does not justify implementation priority.

---

## 40. Grid Control, Grid Test, and distributed execution

### 40.1 Grid Control — exact shipped surface

The hidden Grid Control module is a high-confidence operational UI. It exposes a single selectable node label, Local grid, and polls gridControl/getData every 3,000 ms while active. [A]

| Grid | Columns | Widths in shipped grid |
|---|---|---|
| In progress | Job ID; Job group ID; Type; Status; Created; Started; Run time; Progress | 240, 120, 80, 80, 140, 140, 80, remainder |
| Waiting | Job ID; Job group ID; Type; Created | 240, 120, 80, remainder |
| Finished | Job ID; Job group ID; Type; Created; Started; Duration; Status | 240, 120, 80, 140, 140, 80, remainder |

Type renders as Continuous or One time; running status renders as Waiting or Running; unknown progress renders N/A; finished rows are success/error styled; an error action opens message detail. [A] No current asset proves remote node registration, IP/port editing, or an “Add Node” modal.

For HaruQuantAI, this view maps to Orchestration job groups and workers. The UI consumes typed summaries and authorized control commands; it does not own scheduler state.

### 40.2 Grid Test — exact shipped surface

Grid Test is a local legacy sqGrid component stress/demo harness, not a distributed-compute benchmark. [A]

| Element | Shipped behavior |
|---|---|
| Canvas | 500 × 300 px grid in the shipped view |
| Counter | “Rows in grid,” refreshed every 50 ms |
| Columns | ID (100 px); First col (200 px, custom comparator); Second col (200 px, numeric sort) |
| Controls | Start/Stop test; Select All; Select None; Clear; Add 100 rows |
| Add loop | Appends a synthetic row every 20 ms |
| Remove loop | Removes a random row every 30 ms |
| Change loop | Mutates a random row and change counter every 40 ms |
| Interaction | Column-specific click/double-click demonstrations |

The useful target lesson is a repeatable high-churn grid benchmark covering insert/remove/update, selection, custom/numeric sorting, event dispatch, row identity, and counters. Clear/remove operations do not prove immediate garbage collection or freedom from memory leaks; those require profiling. It is a developer harness, not a customer navigation module.

### 40.3 HaruQuantAI grid benchmark

The target grid spike should extend that lesson safely:

- fixed-seed operation stream for reproducible add/remove/update churn;
- 10k, 100k, and 1M-row fixtures with realistic result-column widths;
- selection, range selection, keyboard navigation, sorting, filtering, column resize/reorder, pinned columns, and export;
- frame-time p50/p95/p99, long tasks, memory, DOM node count, update latency, and leak detection;
- offscreen virtualization and accessibility semantics;
- clean stop/unmount with no pending timer, worker, listener, or request; and
- comparison of the existing table primitive against any proposed virtual-grid dependency.

### 40.4 Distributed worker pool — target design only

Gemini’s remote-cluster design is retained as a future Orchestration provider concept. [P][I] It is not evidence about Grid Test or the current Local Grid controller.

~~~mermaid
stateDiagram-v2
    [*] --> Registered
    Registered --> Healthy
    Healthy --> Draining
    Healthy --> Offline
    Healthy --> Quarantined
    Draining --> Offline
    Offline --> Healthy
    Quarantined --> Healthy
~~~

Candidate worker records include worker ID, endpoint/transport identity, authenticated principal, runtime/provider versions, CPU/memory capacity, supported capabilities, active leases, heartbeat time, health, drain/quarantine reason, and labels. Secrets and raw credentials never enter layout state or logs.

A job protocol must define:

1. immutable input artifact references and hashes;
2. capability/runtime/numerical compatibility matching;
3. lease token, attempt, deadline, and heartbeat;
4. idempotent accept/start/checkpoint/complete/fail/cancel transitions;
5. content-addressed output publication before result commit;
6. retry and duplicate-completion arbitration;
7. cancellation and drain behavior; and
8. audit events with redacted failure detail.

The baseline remains idempotent HTTP commands plus resumable SSE. [R][I] A bidirectional WebSocket endpoint is a separate transport ADR, not implied by worker distribution.

The earlier endpoint names POST /api/v1/grid/nodes/register, POST /api/v1/grid/data, and WS /api/v1/grid/stream are preserved as superseded sketches. [P][U] The resource-oriented route design in §23.3 and ratified Orchestration contracts determine final paths. Likewise, its WAITING, RUNNING, FINISHED_SUCCESS, and FINISHED_ERROR labels map to normalized queued/running/succeeded/failed job states rather than becoming a second lifecycle enum.

The prior flow—dispatch compatible chunks, use worker-local immutable data caches, emit heartbeat/progress, publish filtered strategy/trade artifacts, and aggregate them into Analytics databanks—is retained as the target outcome. [P][I] TCP/WebSocket transport, GPU workers, a fixed 3-second heartbeat, and raw full stack traces are not defaults; failure details must be redacted and authorized.

### 40.5 Distributed diagnostic proposal

Network round-trip latency, serialization throughput, market-data transfer, strategy evaluations per core, cache hit rate, queue wait, lease renewal, artifact upload, and checkpoint recovery are useful **future diagnostics** retained from Gemini. [P][I] They belong to a dedicated worker benchmark/observability feature, not Grid Test. Each metric needs a fixture, payload size, clock source, warm-up, sample count, percentile definition, environment fingerprint, and target before it can gate a release.

---

## 41. Merged UI, metric, and workflow enrichments

This section collects useful field-level and interaction detail that was more explicit in GeminiSQX.md. It extends—not replaces—the complete surface specifications, modal registry, grid registry, chart registry, and workflows in §§3–20.

### 41.1 Shell and execution header

The target SQX workspace may show the current project, active module/workbench, run state, elapsed time, throughput, queue state, accepted/rejected counts, and resource-budget summary. [P][I] These are contextual panels within the HaruQuantAI shell, not proof of one donor-global toolbar.

CPU usage, memory, worker count, and provider health are appropriate operational telemetry. Browser GPU acceleration/memory-protection settings observed in SQX do **not** establish CUDA/OpenCL research execution. [A] A hardware/license indicator may be represented only through HaruQuantAI capabilities, entitlements, and health—not copied donor licensing chrome.

### 41.2 Builder detail catalogue

| Area | Retained detail | Classification |
|---|---|---|
| Dashboard | generation, evaluated/accepted/rejected totals, elapsed/ETA, throughput, best/current fitness, stop reason | Target run-summary requirements [I] |
| Visual telemetry | minimum/mean/maximum fitness lines, island comparison, diversity heatmap, resource telemetry | Optional diagnostic panels [P][I] |
| What to build | direction/symmetry, entries/exits, market/stop/limit actions, SL/PT, break-even, trailing, time exits | Core schema; exact tab placement follows current setting taxonomy [A][I] |
| Genetic options | generations, population/islands, migration, crossover, mutation, restart, decimation, fresh blood | Evidence-backed control family [A]; semantics in §36 |
| Data | selected timeframe, M1-derived precision path, real ticks, additional chart/symbol/timeframe bindings | UI vocabulary is supported; authoritative precision semantics are Simulator-owned [A][I] |
| Building blocks | price/market data, comparisons, logical nodes, indicators, order/action, stop/target, money-management and plugin groups | Non-exhaustive descriptor catalogue [A][I] |
| Money management | fixed size; fixed-balance-percent risk; account-percent risk; fixed amount; stock sizing by price; min/max/step | Current examples plus target typed schema [A][I] |
| Optional sizing | volatility/risk-parity-like sizing | Plugin proposal, not established donor Builder behavior [P][U] |
| Cross checks | trade-order reshuffle, skip trades, spread/slippage variation, price/data perturbation, higher precision, additional markets/timeframes | Method-specific plugins with version, seed, sample count, cost, and direction [A][I] |
| Filtering | ordered acceptance conditions, AND grouping, reason codes, destination databank | Core requirement; threshold values are user plans, not defaults [I] |
| Ranking | single metric, weighted formula, optional Pareto/provider ranking | Metric descriptors and normalization versions required [I] |
| Notes | hypothesis, rationale, author, change/build notes, links and audit history | Added plan metadata [P][I] |

Sessions and time rules belong with trading/data execution settings even if a prior sketch placed them under “What to Build.” Named databanks such as “High Performers” and “Passed Robustness” remain illustrative user-created names rather than factory defaults.

### 41.3 Databank metric-column candidates

In addition to the core fields already specified, the registered column catalogue should be able to expose:

- pin/star or review state;
- net/gross profit and gross loss;
- trade count, average trade, win/loss rates, average win/loss, payoff;
- profit factor, Sharpe, Sortino, Calmar/MAR, SQN and return/drawdown;
- maximum/average drawdown, drawdown percentage and drawdown duration;
- CAGR/annualized return and monthly/annual consistency;
- long/short breakdown;
- IS, OOS, IST, ISV and combined segment metrics;
- robustness, walk-forward, stability, correlation/similarity and custom-plugin metrics; and
- created/updated time, source plan/run/provider version, symbol/timeframe/engine and tags.

Each column is a registered Analytics descriptor with value type, unit/currency, direction, missing state, aggregation, formatter, sort semantics, metric-definition version, and required capability. [I] This is a catalogue, not the default visible grid.

Databank actions retained from Gemini include inspect, compare, retest, optimize, edit, duplicate, move/copy, tag, pin, delete, export, generate code, and send to another workflow. Actions appear only when capabilities and compatible selections are present. JSON, Python, and NinjaTrader exports are optional plugins; they are not current SQX-target claims.

### 41.4 Results default composition

A useful default Result workspace can use a compact scorecard above dockable analysis panels:

~~~text
Strategy / revision / run / segment status
Net profit | Return/DD | Sharpe | Trades | Win rate | Profit factor
Maximum DD | CAGR | SQN | OOS/IS comparison | Robustness status
~~~

This layout is a target composition [P][I], not a pixel claim.

#### Overview metric families

Retained candidates include net/gross profit/loss, CAGR, return/drawdown, maximum and average drawdown, Ulcer Index, Sharpe, Sortino, Calmar/MAR, SQN, profit factor, trades, win/loss rate, average/largest win/loss, average trade, consecutive win/loss streaks, exposure, long/short contribution, and segment comparisons. All definitions remain versioned Analytics metrics; unavailable data renders explicitly.

#### Equity and periodic series

The chart registry should allow balance/equity, drawdown, benchmark, long/short, IS/OOS/window markers, periodic-return bars, rolling Sharpe, rolling volatility, and user-selected reference series. [P][I] No benchmark is hard-coded to the S&P 500. Every overlay declares calendar, resampling, currency, timezone, alignment, missing-data and normalization policy.

#### Trade list additions

Candidate fields include trade number/ID, order/position IDs, direction, symbol, size, entry/exit time and price, stop/target, commission/swap/slippage, profit in currency/pips/percent/R, cumulative balance/equity, maximum adverse/favorable excursion, bars held, elapsed duration, entry/exit signal or rule ID, segment, and exit reason. Fields appear only when emitted authoritatively by Simulator.

#### Trade-analysis panels

Built-in Analytics panels may cover weekday, hour/session, month/year, duration, direction, entry/exit reason, P&L distribution, excursion, consecutive outcomes, symbol/timeframe, and parameter bucket. Every panel is a manifest-registered analysis and can be extended by a sandboxed result plugin.

#### Optimization profile

The primary accessible views remain a sortable table and 2D heatmap. If a 3D engine passes the dependency/performance spike, the surface adds pan, zoom, keyboard/camera reset, rotation, hover/focus detail, color-scale legend, plateau/cliff inspection, and export. [P][I] A 3D view never becomes the only way to inspect a parameter surface.

#### Robustness and walk-forward

Robustness visualizations may include percentile bands/fan charts, distribution/box/violin views, pass/fail matrices, risk-of-ruin curves, sensitivity heatmaps, and worst-case tables. Percentile direction MUST follow the selected metric; “95th percentile is conservative” is not generally valid.

Walk-forward results may include window timelines, IS→OOS parameter transitions, per-window metrics, efficiency ratios such as WFE/WFEI when registered, stability clusters, aggregate versus worst-window results, and anchored/rolling comparisons. Gemini’s 50% efficiency threshold remains an example, not a universal rule. [P][U]

#### Configuration and source

The Result workspace adds a raw read-only structured configuration view beside the typed “run versus current configuration” diff. Source views retain observed targets; unsupported compilation/execution is never implied by a code tab.

### 41.5 Portfolio enhancements

The Portfolio Master/Composer specification retains:

- strategy-selection tables with compatible metric and metadata columns;
- correlation matrices over explicitly defined daily/periodic returns;
- portfolio equity, drawdown, contribution, exposure, concentration and scenario views;
- manual weights and provider options for equal, metric-proportional, inverse-volatility/risk-parity-like, minimum-variance, maximum-Sharpe/Markowitz-like and constrained optimization;
- minimum/maximum weights, gross/net exposure, turnover, leverage, asset/group caps and cash treatment;
- result comparison before/after weighting; and
- portfolio export or handoff through capability-specific generators.

Only observed/official weighting behaviors are donor parity. Risk parity, minimum variance, maximum Sharpe, unified EA, and Python export remain target plugin possibilities [P][I] until supported by a concrete provider.

The optional **portfolio diversification ratio** is also retained. A provider that advertises it MUST define the inputs and convention; the standard long-only form is

\[
DR(w)=\frac{\sum_i w_i\sigma_i}{\sqrt{w^\mathsf{T}\Sigma w}}
\]

where `w` is the weight vector, `σᵢ` is each strategy's volatility, and `Σ` is the aligned-return covariance matrix. Gemini described this as a “Sharpe improvement metric”; that description is not adopted because diversification ratio and Sharpe-ratio change measure different things. If both are shown, the product MUST label and compute them separately, with window, frequency, missing-data, cash, and annualization policies recorded. [P][I]

### 41.6 Data Manager additions and correction

The merged Data Manager vocabulary includes instruments, symbols, brokers/providers, timeframes, sessions/timezones, local/remote data sources, import/export, download/update, clone/merge, validation/repair, gap/duplicate/outlier inspection, and bulk operations. [A][D]

Parquet conversion is a HaruQuantAI artifact-storage choice, not an observed donor QDM command. [R][I] The Data Manager consumes Data/Catalogue capabilities and may offer an export-to-Parquet action only when a target provider actually implements it.

### 41.7 Custom Projects

The visual project editor retains a durable task-graph model with domain tasks, utilities, branches/conditions, retry/cancel policy, run history, inputs/outputs and databank/artifact handoffs. Candidate task types include load/import strategies, build/generate, retest, robustness, optimize, walk-forward, filter/sort, merge/move/copy, portfolio construction, export, script/plugin task, notification and neural training when installed.

Email, desktop, webhook, Slack-like or other notification channels are provider/plugin options [P][I], not assumed built-ins. Conditions must operate on typed prior-task outputs and registered metrics rather than arbitrary browser expressions.

### 41.8 Code Editor and extension tooling

Current evidence supports an SQ extension/snippet-oriented, predominantly Java surface and an Indicator Tester. [A] Rich editing may include syntax highlighting, completion, diagnostics, navigation, search, diff, build/test output, template creation, and controlled extension packaging. Monaco exists in donor assets but is not a current HaruQuantAI dependency.

Python editing, live-chart indicator execution, and multi-language project templates remain optional extension-provider features [P][I]. They require sandboxing, dependency policy, resource limits, filesystem/network permissions, reproducible builds, signed outputs and no arbitrary execution from a Results code pane.

### 41.9 Additional interaction and modal needs

The complete registry in §17 remains authoritative. Gemini’s additional names are accounted for as follows:

| Prior modal/dialog idea | Merged disposition |
|---|---|
| Manage Columns | Retained as grid column chooser/preset editor |
| Edit Filter / Acceptance Condition | Retained as typed condition editor with metric metadata |
| Strategy Properties | Retained as strategy metadata/revision dialog |
| Chart Settings | Retained as chart/overlay/axis/segment settings |
| Import/Export Data | Retained through governed Data workflows |
| Add Custom Task / Task Properties | Retained in Custom Projects |
| Symbol/Trading Session editor | Retained under Catalogue/Data ownership |
| Quality Analysis dialog | Corrected: may be a docked tab/panel rather than a modal |
| Connect/Add Grid Node | Reclassified as a future distributed-provider administration flow |
| Application Settings GPU/CUDA toggle | Corrected to observed browser GPU/memory settings; compute provider settings are separate |

Every destructive dialog names the affected entity count, scope, retention/recovery behavior, and irreversible effects. Every long-running dialog returns a job reference and remains resumable outside the modal.

---

## 42. Architecture and implementation reconciliation

### 42.1 Corrected decision ledger

| Prior analysis claim or sketch | Repository/evidence truth | Unified decision |
|---|---|---|
| “Next.js + Vite” application | Next.js 15/React 19 is the application; Vite is test tooling through Vitest [R] | Keep the Next application; do not create a Vite shell |
| Tailwind, TanStack Table/Virtual, Monaco, ECharts/Plotly, Three.js are current stack | They are absent from the current UI dependencies [R] | Treat each as an optional ADR/spike; reuse current primitives first |
| FastAPI routers are the current Interfaces architecture | Current boundary is a raw ASGI adapter and remains framework-neutral [R] | Preserve endpoint intent through typed gateways; no incidental framework migration |
| WebSockets are the baseline event channel | Current contracts/widgets support HTTP with SSE or polling [R] | Commands over HTTP; resumable ordered SSE for progress/logs; WebSocket requires an ADR |
| Builder/Optimizer/robustness belong to Agentic | Current capability ownership is Strategy + Research + Simulator [R] | Use those owners; no Agentic shadow domain |
| Backtesting belongs to Trading | Simulator owns simulated execution [R] | Trading remains live execution policy; Simulator owns research simulation |
| Databanks belong to Workspace | Analytics owns result membership/query/metrics; Workspace owns artifacts [R] | Keep semantic ownership separate from artifact custody |
| Custom Projects belong to Agentic | Orchestration owns project/task execution [R] | Use durable Orchestration graphs/jobs |
| .sqx parsing belongs directly in Workspace/Data or Interfaces | Existing Strategy exchange accepts a Workspace artifact and calls for an isolated importer [R] | Strategy/plugin importer; no parsing in Interfaces |
| Python/NinjaTrader are observed donor code targets | Current evidence supports pseudocode, MT4, MT5, EasyLanguage/MultiCharts and XML [L][A] | Python/NinjaTrader remain optional target plugins |
| Code Editor is a Java-and-Python IDE | Current shipped extension corpus is predominantly Java; Python is unproven [A] | Secure extension workbench first; Python only through a real provider |
| OpenCL/CUDA generator toggle is observed | Browser GPU acceleration/memory protection is observed, not research CUDA [A] | Compute acceleration is a separate provider capability |
| QDM offers Parquet conversion | Parquet is a HaruQuantAI storage decision, not evidenced donor UI [R] | Offer only if a Data export provider exists |
| Grid Test benchmarks network/cluster speed | It is a local sqGrid mutation harness [A] | Keep it developer-only; create a separate distributed benchmark if needed |
| Grid Control proves remote IP/port node management | Current controller exposes only Local grid [A] | Remote administration is future Orchestration design |
| Per-widget Zustand stores may own results/settings | Browser state is presentation-only [R] | Persist authoritative state in owning backend domains |
| registerCustomWatermark registers Dockview panels | It does not constitute a dynamic panel/plugin registry [R] | Implement a real manifest discovery/registration path |
| Exact bit-identical .sqx export is the initial goal | Multiple variants and opaque Java streams make that unproven [A] | Use the C0–C5 maturity levels in §38 |

### 42.2 Corrected domain decomposition

~~~mermaid
flowchart TB
    UI[UI / Dockview widgets] --> IF[Interfaces: HTTP + SSE translation]
    IF --> S[Strategy: AST, catalog, edit, code generation, exchange]
    IF --> R[Research: build, evolve, optimize, robustness, neural]
    IF --> SIM[Simulator: authoritative backtests and perturbations]
    IF --> AN[Analytics: databanks, metrics, trades, result panels]
    IF --> P[Portfolio: construction, correlation, weighting, risk]
    IF --> O[Orchestration: projects, jobs, workers, checkpoints]
    S --> W[Workspace artifact custody]
    R --> D[Data / Catalogue inputs]
    SIM --> D
    AN --> W
    O --> W
    PL[Plugins] --> S
    PL --> R
    PL --> AN
~~~

Interfaces authenticates, validates wire DTOs, resolves public capabilities, applies transport concerns, maps errors, and streams ordered events. It does not calculate metrics, parse archives, query domain tables directly, compile strategies, manage workers, or simulate trades.

### 42.3 Proposed feature/package placement

The following is a **logical placement plan**, not a claim that provider packages already exist. [I]

| Concern | Contract/capability owner | Candidate provider feature |
|---|---|---|
| Strategy AST and node descriptors | app/contracts/strategy | one cohesive define/edit/catalog provider or narrowly split providers after contract review |
| Legacy strategy exchange | Strategy + Plugins, consuming Workspace artifact IDs | isolated legacy-sqx importer/exporter |
| Generation/evolution | app/contracts/research | generate/evolve provider consuming Strategy and Simulator capabilities |
| Robustness/optimization/WFO/WFM | Research | separate cohesive research providers where lifecycle/removal differs |
| Simulation | app/contracts/simulator | authoritative engine and perturbation providers |
| Databanks/results/metrics | app/contracts/analytics | result store/query, metric registry and analysis-panel providers |
| Portfolio | app/contracts/portfolio | compose/search/simulate/risk providers |
| Projects/jobs/workers | app/contracts/orchestration | project graph, scheduler/checkpoint and optional distributed-worker providers |
| Transport | app/services/interfaces | cohesive research/portfolio/project gateways rather than one feature per route |
| Widgets | app/ui/src/widgets/<feature>/ | one owner per widget, manifest plus full host registration |

Every feature follows the repository pattern: README with state/ownership, data-only manifest, strict configuration, lifecycle feature/provider, public capability implementation, focused tests, entry-point registration, composition verification, gateway wiring, UI wiring, and removal story. Empty/package initializer constraints remain unchanged.

### 42.4 Interfaces bridge pattern

The FastAPI example in Gemini is retained for its **transport intent** only: validate a typed request, resolve the capability, return the standard envelope/job reference, and stream progress separately. [P][I] Framework decorators, direct imports of research implementations, locally calculated results, background tasks started from route code, and private file access are superseded.

Its app/services/interfaces/observe_builder/ placement and POST /api/v1/builder/start route are retained as superseded sketches. [P][U] The unified design uses a cohesive research gateway and resource-oriented plan/run/command routes from §23.3, with the current public capability key and DTOs rather than the proposed Agentic models.

Required transport properties:

- public versioned DTOs and frozen response/error envelopes;
- authentication/session and CSRF enforcement for governed writes;
- idempotency keys for start/cancel/import/export commands;
- prompt job-reference responses rather than long-held HTTP requests;
- resumable SSE with monotonic sequence/cursor, Last-Event-ID, bounded replay and gap recovery;
- capability-unavailable and version-incompatible errors that fail closed;
- signed/authorized artifact downloads; and
- trace/request IDs propagated to domain commands and events.

### 42.5 Dockview integration correction

HaruQuantAI currently has a static widget union, static rendering switch, static sidebar/templates, eager imports, and declarative manifests that are not yet dynamically discovered/enforced. [R] The SQX plan therefore includes an explicit host evolution:

1. add or evolve narrowly named widget types without repurposing existing domains;
2. migrate persisted layout schemas before any rename/removal;
3. register every widget in the type schema, host, catalogue/sidebar, workspace template and tests;
4. make manifest capability requirements executable/fail-closed;
5. lazy-load heavy editors, result analyzers, large grids and optional 3D/neural surfaces;
6. extend widget references deliberately for strategyId, resultId, databankId, projectId and portfolioId;
7. consume manifest placement/minimum dimensions rather than always opening at 580×440; and
8. preserve split layout across expand/restore instead of flattening the workspace.

Dockview layout and Zustand state contain only presentation identifiers/preferences. Strategy definitions, runs, results, datasets, logs, models, portfolios and projects remain backend-owned.

### 42.6 Dependency gates

| Need | Baseline | Gate for a new dependency |
|---|---|---|
| Market/equity charts | lightweight-charts | Add analytical charting only for heatmap/3D/statistical gaps |
| Large grids | Existing table primitives | Benchmark 100k–1M rows before TanStack or another virtualization layer |
| Code editing | Existing text/editor primitives | Monaco or alternative only after bundle, CSP, worker and accessibility review |
| Styling | Existing design tokens/CSS modules | Tailwind only through an explicit UI-system decision |
| 3D | 2D table/heatmap remains authoritative | Three.js/Plotly/ECharts only after lazy-load and interaction spike |
| ML runtime | Provider-defined server runtime | No frontend ML dependency unless an offline inference requirement is approved |

### 42.7 Current implementation-state honesty

Contracts exist for Strategy, Research, Simulator, Analytics, Portfolio, and Orchestration, but their provider service directories/entry points are not all present in the current checkout. [R] Plugin folders also do not imply registered providers. A specification or manifest must never call a capability “implemented” until provider code, entry point, composition, gateway, UI and E2E evidence all exist.

The Data storage documentation/current-provider discrepancy—architecture references authoritative sidecars plus SQLite catalog while the current market-data store describes Parquet plus DuckDB manifest catalog—is an explicit reconciliation gate. SQX consumes the ratified Data capability and does not introduce a third storage truth.

---

## 43. Integrated roadmap and verification addendum

The main roadmap in §29 remains normative. The following gates incorporate Gemini’s additional generator, AST, neural, distributed-grid, and archive work while correcting its dependency order.

### 43.1 Delivery sequence

| Gate | Deliverable | Exit evidence |
|---|---|---|
| M0 — Evidence freeze | Versioned fixture inventory, claim ledger, legal/product position on legacy compatibility | Hashes, provenance, no private/license data, approved scope |
| M1 — Contract foundation | Ratified Strategy, Research, Simulator, Analytics, Portfolio, Orchestration and Interfaces slices needed by the first workflow | Contract tests, capability ownership, error/event/idempotency semantics |
| M2 — UI host foundation | Manifest enforcement, persisted-layout migrations, lazy loading, large-grid spike, SQX workspace template | Typecheck/build, focused widget/Dockview tests, accessibility baseline |
| M3 — Strategy/AlgoWizard vertical | Descriptor catalogue, normalized AST, visual editor, one simple strategy, authoritative backtest and Result view | Golden node/action fixtures, edit→simulate→inspect E2E |
| M4 — Random generation | Deterministic random provider with budgets, filters, lineage and databank routing | Seed repeatability, invalid-graph rejection, cancellation and scale tests |
| M5 — Build 144 genetic reference | Tournament, compatible-node crossover/mutation, islands/ring migration, decimation, restarts and fingerprint policy as a clean-room behaviorally tested provider | Operator unit/property tests and small deterministic population traces |
| M6 — Results/robustness | Virtual databanks, metric registry, trades/equity/analysis, Retester and selected robustness methods | Numerical goldens, missing-state tests, large-result benchmarks |
| M7 — Optimizer/WFO/WFM | Discrete optimizer, sequential/WFO/WFM orchestration and accessible profile views | Cartesian-count tests, window-boundary/leakage fixtures, checkpoint recovery |
| M8 — Portfolio and projects | Composer/Master plus durable project graphs and job history | Correlation/weight/risk goldens, resume/retry/cancel and artifact lineage |
| M9 — Legacy compatibility C0/C1 | Safe archive inspection plus selected strategy XML import | Security corpus, loss reports, normalized AST comparison |
| M10 — Legacy result/export spikes | Selected C2–C4 cells only after format adapters and donor reopen tests | Compatibility matrix with explicit unsupported cells |
| M11 — Optional providers | Neural research workbench and/or distributed workers | Separate ADR, provider contracts, threat model, deterministic fixtures |
| M12 — Hardening | Performance, accessibility, security, migrations, uninstall/removal, docs and operational readiness | Full release checklist and rollback rehearsal |

This order supersedes the earlier plan to build UI/full-fidelity export before authoritative Simulator/Analytics foundations.

### 43.2 Required automated suites

| Suite | Required assertions |
|---|---|
| Generator configuration | Bounds/default fixture parsing, invalid combinations, resource estimates, plan serialization |
| Generator operators | Fixed-seed tournament trace; compatible/incompatible crossover; one/two crossover points; mutation bounds; ring migration; decimation; weakest replacement; fingerprint duplicate policy |
| Generator properties | Type-valid children, immutable parents, depth/node budgets, deterministic seed derivation, no silent unsupported nodes |
| Strategy AST | Schema/graph/data-context validation, stable canonical hashing, variables, data bindings, symmetry descriptors, unknown/plugin nodes |
| AlgoWizard semantics | Six-decimal comparisons, strict crossover boundaries, event clocks, order/exit collision policy, XML loss reports |
| Simulator/Analytics | Execution, costs, metrics, segments, rankings, distributions and numerical tolerances |
| Archive security | ZIP/XML/binary abuse cases from §38.6 |
| Archive compatibility | All 32 baseline fixtures inventoried; selected XML/version adapters; unknown-member preservation; donor reopen where allowed |
| Databank/grid | 10k/100k/1M rows, sorting/filtering/selection/export, high-churn 20/30/40-style operation stream, memory and unmount cleanup |
| Neural | Leakage, train-only fitting, fold purge/embargo, determinism, checkpoint/resume, inference parity, class support and model card |
| Distributed jobs | lease expiry, duplicate completion, retry, drain, quarantine, cancellation, checkpoint, incompatible worker and artifact failure |
| Interfaces | auth/CSRF, idempotency, envelope/error mapping, SSE ordering/resume/gap, capability unavailable, download authorization |
| UI | schema migrations, Dockview restore/expand/popout, Strict Mode duplicate-effect protection, loading/partial/stale/error/unavailable, keyboard and screen-reader behavior |
| Lifecycle | enable/disable/uninstall/reinstall, retained data, immutable migration history, unavailable provider and stale layout references |

Suggested future test filenames from Gemini are preserved only as planning labels—strategy archive, AST, generator and grid-worker fixture suites—not as evidence that those files exist now. [P][I]

### 43.3 Manual verification

Manual release testing must cover:

1. Create/edit a simple strategy, inspect generated code support, run it, and explain every metric from lineage.
2. Run random and genetic builds; stop, resume where supported, compare deterministic traces, and inspect rejected-candidate reasons.
3. Retest selected strategies with higher precision/additional market/perturbation methods and verify method-specific assumptions.
4. Optimize and walk-forward a strategy, inspect table/2D profile and optional 3D view, and verify window boundaries.
5. Build and compare a portfolio, change weights/constraints, and inspect correlation/contribution/risk.
6. Compose and resume a Custom Project with a failed task, retry, condition branch, and artifact handoff.
7. Import each advertised .sqx class; review warnings/losses; preserve the original; reopen any exported artifact in the declared donor build.
8. Exercise Grid Control and the developer Grid Test under sustained churn; verify stop/unmount and no leaks.
9. If installed, train a neural baseline with leakage probes and compare portable inference against golden vectors.
10. Disable/uninstall each optional provider and confirm truthful unavailable states with retained data/layout recovery.

### 43.4 Additional definition-of-done checks

- Every Gemini heading has a destination/disposition in §45.
- Every numeric default/range is evidence-backed or explicitly labeled an example.
- The current/donor/target/proposal layers are never mixed without labels.
- No source target, algorithm, grid capability, neural capability, or archive fidelity is overstated.
- All original Codex requirement IDs remain present.
- New requirement IDs are unique.
- Markdown headings, tables, links, Mermaid/fenced blocks and anchors validate.
- CodexSQX.md and GeminiSQX.md remain byte-unchanged, and only SQX.md is the intended new report.

---

## 44. Superseded, corrected, and retained-claim ledger

This ledger is intentionally explicit so that disputed Gemini content is accounted for rather than disappearing from the merge.

| Prior claim or detail | Disposition | Evidence-based unified treatment |
|---|---|---|
| Next.js and Vite are both the production application stack | Corrected | Next.js/React is the app; Vite is test tooling [R] |
| Tailwind, TanStack, Monaco, ECharts/Plotly and Three.js are already installed | Corrected | They are dependency candidates only [R][P] |
| FastAPI routes are the current Interfaces implementation | Corrected | Current boundary is raw ASGI/framework-neutral; retain typed route intent [R] |
| WebSocket command/event bridge is the baseline | Corrected | HTTP commands plus resumable SSE; WebSocket needs an ADR [R][I] |
| Builder/Optimizer/robustness belong to Agentic | Superseded | Strategy/Research/Simulator own them [R] |
| Simulation belongs to Trading | Superseded | Simulator owns research simulation [R] |
| Databanks belong to Workspace | Superseded | Analytics owns result semantics; Workspace owns artifacts [R] |
| Custom Projects belong to Agentic | Superseded | Orchestration owns projects/jobs [R] |
| Direct .sqx parsing in Workspace/Data/Interfaces | Superseded | Isolated Strategy/plugin importer consumes Workspace artifact IDs [R][I] |
| Production UI contains a global project/run/GPU/license toolbar exactly as sketched | Reclassified | Useful target telemetry concepts; exact global donor layout unproven [P][I] |
| CUDA/OpenCL generator toggle is observed | Falsified as donor claim | Browser GPU/memory settings are observed; compute acceleration is separate [A] |
| Builder dashboard has fitness-range chart, diversity heatmap and GPU telemetry | Reclassified | Optional HaruQuantAI diagnostics, not proven current donor widgets [P][I] |
| Genetic build exposes tournament/roulette selection choices | Corrected | Current Builder wires fixed tournament 3/0.8; roulette class exists but is not wired/exposed [A][B] |
| Tournament size is tunable from 3–7 | Falsified for inspected wiring | Fixed size 3 in current selector [A] |
| Full/Grow/Ramped Half-and-Half is the current random initializer | Unverified | Retained as a provider experiment [P][U] |
| Complete generator achieves 5k–20k strategies/minute | Unverified | Benchmark hypothesis only [P][U] |
| All generator details are unknown | Corrected | Controls and enumerated Build 144 internals in §36.10 are high-confidence [A] |
| Island migration is merely speculative | Corrected | Directed ring and current replacement caps are traced for Build 144 [A] |
| Similarity pruning uses returns correlation plus AST Levenshtein distance | Falsified for Build 144 | Current GP engine uses integer fingerprint identity and duplicate caps [B] |
| Gaussian parameter jitter is current mutation | Falsified for traced mutation | Current mutation regenerates selected generated objects by ID/range [A] |
| Real-vector SBX and polynomial mutation power current optimizer | Falsified for traced indexed operators | Current traced operators use short-array combination indexes and bounded random gene replacement [A] |
| NSGA-II/Pareto selection is current SQX behavior | Unverified | Optional clean-room multi-objective provider [P][I] |
| Restart reseeding is exactly 80% random/20% mutated | Unverified | Retained experiment; current restart controls are evidenced [A][P] |
| Negative ISV universally zeroes fitness | Unverified | Optional versioned penalty policy [P][U] |
| Symmetry universally maps RSI 30 to 70 | Corrected | Opposites are block/provider-defined; no universal arithmetic transform [A][I] |
| AlgoWizard has a canonical OnTick event | Corrected | Current event/timing evidence uses OnBarUpdate plus OnEveryTick/everyTick [A] |
| Gemini’s XML is canonical literal Build 144 XML | Falsified | It is a synthetic normalized example; real fixtures supply keys/nesting [A] |
| Canonical keys use the SQ.Conditions/SQ.Blocks namespaces shown | Corrected | Current fixtures commonly use AND, EMA/talib_EMA, BooleanVariable, Equals, etc. [A] |
| CrossesAbove/Below use inclusive prior boundaries | Falsified | Current snippets use strict prior and strict current comparisons after six-decimal normalization [B] |
| Floating equality uses an unspecified epsilon | Corrected | Current Equals uses exact equality after six-decimal rounding [B] |
| Pending orders use #Expiration# | Corrected | Current examples use #BarsValid# and #ReplaceExisting# [A] |
| ATR exit key is SLPT.AtrMultiple | Corrected | Current key is SLPT.ATRBasedValue [A] |
| Python makeExternal/config export is evidenced | Unverified | makeExternal is evidenced for generated EA inputs; Python is plugin-gated [A][P] |
| Every .sqx has one fixed member tree | Falsified | Strategy-only and result-rich archive variants differ [A] |
| Every strategy is schema version 3.9.130 | Falsified | Local corpus includes 3.9.130, .132 and .133 [A] |
| Manifests contain Created-By and Strategy-Version | Not observed | Inspected manifests contain Manifest-Version: 1.0 [A] |
| orders.bin is a flat 116-byte-record format with immediate count | Falsified | Java serialization/block framing, metadata integers, string cache and mixed fields are traced [A][B] |
| The Gemini Python reader/writer is full fidelity | Falsified | It can return zero for non-empty format-11 files and omits variant members [A][B][P] |
| Bit-exact new ZIP serialization is the first compatibility goal | Superseded | Use C0–C5 semantic/opaque-preservation/reopen gates [I] |
| Binary SQStats is decoded by the proposed implementation | Unverified | Only the outer Base64 SQStats version=2 structure is evidenced [A][U] |
| Neural Trainer implements MLP/TCN/LSTM, triple barrier and model export | Falsified as current donor behavior | Current hidden task is a no-op scaffold; retain the design in §39 [A][B][P] |
| Grid Test measures RPC/network/worker throughput | Falsified | It is a local 500×300 sqGrid churn harness [A] |
| Clear/remove proves instant memory purge/no leaks | Corrected | It removes rows; memory behavior requires profiling [A][I] |
| Grid Control proves remote nodes and Add Node/IP/port management | Unverified | Current UI exposes Local grid only; remote design is optional [A][P] |
| QDM exposes Parquet conversion | Unverified as donor behavior | Parquet is a HaruQuantAI target storage/export option [R][I] |
| Current donor code targets include Python and NinjaTrader | Unverified | Observed targets are pseudocode, MT4/5, EasyLanguage/MultiCharts and XML [L][A] |
| Code Editor is a Java/Python IDE with live-chart execution | Partially reclassified | Java-oriented extension surface/Indicator Tester evidenced; Python/live execution need providers [A][P] |
| Risk parity, minimum variance, maximum Sharpe and unified EA/Python portfolio export are fixed donor features | Reclassified | Useful optional Portfolio providers/generators [P][I] |
| Portfolio diversification ratio is a Sharpe-improvement metric | Corrected | Preserve diversification ratio as an optional, explicitly defined metric and report Sharpe change separately [P][I] |
| Notification channels and arbitrary branched DAG semantics are fixed built-ins | Reclassified | Typed Orchestration graph plus channel plugins [P][I] |
| registerCustomWatermark is a complete Dockview panel registry | Falsified as architecture | Implement actual manifest discovery/host integration [R][I] |
| Widget-local Zustand can own durable results/settings | Superseded | Presentation state only; domain services are authoritative [R] |
| UI/full-fidelity export should precede simulation/analytics foundations | Superseded | Integrated roadmap uses contract and numerical foundations first [I] |

---

## 45. Full source-heading coverage ledger

This is the completeness proof for the merge. “Retained” can mean the original content was already stronger in §§1–34; “expanded” points to new merged material; “reclassified/corrected” points to the sections that preserve the idea without repeating an error.

### 45.1 Source-document preservation

| Source | Coverage in this file | Status |
|---|---|---|
| CodexSQX.md | Its complete specification is the direct base of §§1–34; only title/metadata and the confidence table were strengthened | Retained |
| GeminiSQX.md | Every heading is mapped below; every unique claim group is retained, corrected, reclassified, or falsified in §44 | Fully accounted |

### 45.2 Gemini executive and architecture headings

| Gemini heading | Unified destination | Disposition |
|---|---|---|
| Recreating StrategyQuantX UI in Python / FastAPI & Node / TypeScript | Title; §§1, 21–26, 42 | Corrected from stack prescription to brownfield specification |
| Executive Summary | §§1, 3, 21, 35, 42 | Retained/corrected |
| 1. System Boundary & Brownfield Integration into HaruQuantAI | §§1.1, 21–26, 42 | Retained; repository ownership is authoritative |
| Core Architecture Governance Invariants | §§1.1, 21.3–21.4, 23.7, 24, 42 | Retained and strengthened |
| 4.1 Backend Domain Decomposition | §§21–24, 26, 42.2–42.3 | Corrected |
| 4.2 Interfaces Domain Bridge Pattern | §§23, 42.4 | Intent retained; FastAPI/direct ownership corrected |
| 4.3 Frontend Architecture: Spatial Composability with Dockview | §§4, 22.3–22.4, 25, 42.5–42.6 | Retained and brownfield-corrected |
| 4.4 Distributed Grid Computing Cluster Engine | §§26.4, 40.4–40.5 | Reclassified as optional Orchestration design |
| A. Wire Protocol & Service Endpoints | §§23, 40.4, 42.4 | Corrected to HTTP/SSE baseline |
| 4.5 Full-Fidelity .sqx Container Import/Export | §§24.5, 38 | Expanded and confidence-corrected |
| A. Forensic Binary Layout of orders.bin | §§38.3–38.3.1, 44 | Falsified fixed-record layout; traced framing retained |
| B. Structure of settings.xml & Base64 SQStats | §§38.2–38.3.1 | Retained with opaque-payload boundary |
| C. Python SQXArchiveReader & SQXArchiveWriter | §§38.3–38.7, 44 | Prototype retained as falsified; safe architecture replaces it |
| 5. Proposed Project File Structure | §§22, 25.6, 26.1, 42.3 | Corrected to actual domain/package rules |

### 45.3 Gemini UI-extraction headings

| Gemini heading | Unified destination | Disposition |
|---|---|---|
| 2. Complete StrategyQuantX UI Extraction | §§3–20, 41 | Retained and expanded |
| 2.1 Application Shell & Global Layout | §4; §41.1 | Retained; unproven global controls reclassified |
| 2.2 App 1: Builder Workbench | §§5–6; §§36, 41.2–41.3 | Retained and expanded |
| A. Dashboard Header & Execution Stats | §§5.2–5.3, 6, 41.1–41.2 | Retained |
| B. Engine Dashboard View | §§5.2, 6, 41.2 | Optional visual telemetry reclassified |
| C. Settings Tabs | §§6.2–6.4, 36.1, 41.2 | Retained with field-level expansion |
| D. Strategy Databank System | §9; §41.3 | Retained and expanded |
| 2.3 Strategy Results & Inspection Engine | §10; §41.4 | Retained and expanded |
| Sub-View 1: Overview | §§10.2, 41.4 | Retained and expanded |
| Sub-View 2: Equity Chart | §§10.4, 19, 41.4 | Retained; benchmark is user-selected |
| Sub-View 3: Trade List | §§10.3, 18.2, 41.4 | Retained and expanded |
| Sub-View 4: Trade Analysis | §§10.5, 19, 41.4 | Retained and expanded |
| Sub-View 5: Optimization Profile | §§10.7, 19, 41.4 | Retained with accessible 2D baseline |
| Sub-View 6: Robustness Tests | §§10.8, 19, 41.4 | Retained; percentile direction corrected |
| Sub-View 7: Walk-Forward Results | §§10.7, 41.4 | Retained; 50% threshold reclassified |
| Sub-View 8: Source Code | §§10.10, 37.6, 41.4 | Retained; targets corrected |
| Sub-View 9: Strategy Config | §§10.10, 41.4 | Retained; raw read-only view added |
| 2.4 AlgoWizard Studio | §14; §37 | Retained and materially expanded |
| 2.5 Optimizer Workbench | §8; §§10.7, 36.4–36.5 | Retained; unsupported genetic operators reclassified |
| 2.6 Retester Workbench | §7; §§10.8, 41.2 | Retained |
| 2.7 Portfolio Master & Composer | §11; §41.5 | Retained; extra weighting modes plugin-gated |
| 2.8 QuantDataManager | §12; §41.6 | Retained; Parquet donor claim corrected |
| 2.9 TaskManager / Custom Projects | §13; §41.7 | Retained; notification channels plugin-gated |
| 2.10 Code Editor | §15; §41.8 | Retained; Python/live execution reclassified |
| 2.11 Neural Network Trainer | §16.7; §39 | Registration retained; functionality corrected |
| A. Architecture & Training Controls | §§39.4–39.6 | Reclassified as optional target design |
| 2.12 Grid Control & Distributed Cluster Computing | §§16.1, 40.1, 40.4 | Local UI retained; distribution separated |
| Table Columns & Field Specifications | §40.1 | Retained exactly for current grids |
| 2.13 Grid Test Latency & Throughput Benchmark Sandbox | §§16.7, 40.2–40.3 | Corrected to local grid stress harness |
| Operational Diagnostics | §§40.3, 40.5 | Reclassified into separate target benchmarks |
| 2.14 Complete Inventory of Modals & Dialogues | §17; §41.9 | Retained; verified registry remains authoritative |

### 45.4 Gemini generator, AlgoWizard, and neural headings

| Gemini heading | Unified destination | Disposition |
|---|---|---|
| 3. Complete Generator & Search Algorithms Engine Specification | §36 | Split into evidenced Build 144 mechanics and candidate provider designs |
| 3.1 Genome Representation: STGP AST | §§36.2–36.3, 37.3 | Reclassified as normalized clean-room AST design |
| A. Grammatical Specification | §36.2 | Retained and corrected to descriptor-extensible grammar |
| B. Type Safety Invariant | §36.2 | Retained; “guarantees execution” claim corrected |
| C. Deterministic Strategy Symmetry Engine | §36.3; §36.10 | Retained; transformations made provider-defined |
| 3.2 The 4 Core Generator & Search Engines | §36.4 | All four concepts retained with evidence status |
| Engine 1: Pure Random Generation | §36.4 | Product mode retained; Full/Grow/RHH reclassified |
| Engine 2: Island Model Genetic Programming | §§36.1, 36.4, 36.10 | Promoted for traced Build 144 ring behavior |
| Engine 3: Custom Strategy Genetic Improvement | §36.4 | Parts-to-improve retained; third Build Mode claim corrected |
| Engine 4: Walk-Forward Matrix & Optimization Search | §§8, 10.7, 36.4–36.5 | Grid/WFM retained; SBX/polynomial reclassified |
| 3.3 Population Synthesis & Decimation | §§36.1, 36.6, 36.10 | Retained; exact candidate-count meaning qualified |
| Decimation Formulation | §36.6 | Retained as candidate contract with UI ambiguity exposed |
| 3.4 Genetic Operators | §§36.5, 36.10 | Traced operators promoted; generic library retained as options |
| 1. Selection Operators | §§36.5, 36.10 | Tournament promoted; roulette/rank qualified |
| 2. Recombination Operators | §§36.5, 36.10 | Compatible node/index crossover promoted; SBX optional |
| 3. Mutation Operators | §§36.5, 36.10 | Generated-object/index mutation promoted; Gaussian optional |
| 3.5 Evolutionary Dynamics, Stagnation & Diversity | §§36.7, 36.10 | Retained and evidence-split |
| A. Stagnation Detection & Automatic Restarts | §36.7 | Controls retained; 80/20 formula reclassified |
| B. Multi-Stage In-Sample Partitioning | §§36.1, 36.7 | Stored ratio retained; penalty policy reclassified |
| C. Anti-Crowding & Fresh Blood | §§36.7, 36.10 | Weakest/fingerprint behavior promoted; correlation/edit-distance optional |
| 3.6 Multi-Metric Objective Fitness & Filtering | §36.8 | Retained with Analytics ownership |
| Stage 1: Hard Filtering Gate | §36.8 | Retained; numeric thresholds labeled examples |
| Stage 2: Objective Fitness Scoring | §36.8 | Retained; metric formulas are versioned Analytics definitions |
| Stage 3: Multi-Objective Pareto/NSGA-II | §36.8 | Retained as optional provider design |
| 3.7 Python Implementation Pattern | §§36.9, 42.3 | Ownership/path corrected; intent retained |
| 3.8 AlgoWizard Detailed Node Semantics & AST | §37 | Retained and evidence-corrected |
| A. Canonical XML Document Structure | §§37.1–37.3 | Synthetic example reclassified; fixture map retained |
| B. Detailed Node Semantics & Execution Rules | §§37.2–37.7 | Common comparators promoted; remaining semantics gated |
| 3.9 Neural Network Model Architecture | §39 | Entire design retained as optional Research provider |
| A. Feature Engineering & Preprocessing | §39.2 | Retained with leakage/lineage requirements |
| B. Triple-Barrier Target Labelling | §39.3 | Retained as optional labeler with collision semantics |
| C. Network Topologies & Hyperparameters | §39.4 | Retained as provider options/examples |
| D. Zero-Dependency Model Export & Inference | §39.6 | Concept retained; sample code replaced by versioned package contract |

### 45.5 Gemini roadmap and verification headings

| Gemini heading | Unified destination | Disposition |
|---|---|---|
| 6. Phased Implementation Roadmap | §§29, 43 | Retained and dependency-corrected |
| Phase 1: Core Contracts & Interfaces Foundation | §§29 phases 0–2, 43 M0–M1 | Retained; providers precede gateways |
| Phase 2: Dockview Shell & Virtual Databank Grid | §§25, 29 phase 1, 43 M2 | Retained |
| Phase 3: Builder Dashboard & Settings Panels | §§6, 29 phase 4, 43 M3–M5 | Retained after numerical foundation |
| Phase 4: Results & Forensic Inspection | §§10, 29 phases 1–3, 43 M3/M6 | Retained |
| Phase 5: AlgoWizard & Full-Fidelity .sqx IO | §§14, 29 phases 8–9, 38, 43 M3/M9/M10 | Split; editor before compatibility, export gated |
| Phase 6: Optimizer, WFM & 3D Surface | §§8, 10.7, 19, 29 phase 5, 43 M7 | Retained; 3D optional |
| Phase 7: Neural, Grid Cluster & TaskManager DAG | §§13, 39–40, 43 M8/M11 | Retained as staged/optional providers |
| Phase 8: Hardening, Polish & Verification | §§28, 30–32, 43 M12 | Retained and strengthened |
| 7. Verification Plan | §§30, 32, 43.2–43.4 | Retained and expanded |
| Automated Verification | §§30, 43.2 | Retained with corrected archive/operator tests |
| Manual Verification | §§30.1, 43.3 | Retained and expanded |

### 45.6 Unique-detail outcome summary

| Topic raised by the user | What changed in this unified file |
|---|---|
| Generator/search algorithms | Confidence split; exact Build 144 controls and traced genetic mechanics are high-confidence, while RHH/NSGA-II/SBX and other generic designs remain explicit proposals |
| .sqx full-fidelity import/export | ZIP/XML/member and format-11 framing knowledge promoted; fixed 116-byte parser rejected; C0–C5 compatibility ladder added |
| AlgoWizard detailed node semantics | Fixture schema, enums, canonical keys, exit fields and source-available comparator semantics promoted; plugin/AI/exhaustive semantics remain bounded |
| Neural Network Trainer | Registration/shell promoted to high; current operation identified as a no-op scaffold; all detailed ML ideas preserved as an optional design |
| Grid Test | Exact 500×300 grid, controls and 20/30/40/50 ms behavior promoted to high; network/cluster interpretation rejected and retained as a separate benchmark proposal |

The merge is complete only while this ledger remains synchronized with future edits. Any new claim must either cite evidence, declare itself a target decision, or remain explicitly unresolved.
