# UI

> **Package:** `app/ui/`
> **Status:** `Partial`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-UI`

This README is the domain's single source of truth for its boundary, feature and FR registry,
domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence,
and deletion behavior. Reference-product evidence is a requirement source, never implementation
evidence. Only the repository-backed frontend foundation is `Partial`; authoritative backend
integration and the remaining product behavior are not complete.

`PROJECT.md` owns system scope and cross-domain behavior. `ARCHITECTURE.md` owns universal
structure and runtime constraints. `AGENTS.md` owns contributor workflow. The
[Feature Implementation Pipeline](../../docs/dev/feature_implementation_pipeline.md) owns the
complete single-file feature delivery checklist.

## Code-aligned implementation convention

The UI keeps the same public-contract and lifecycle boundaries while following its existing
React/TypeScript structure:

```text
app/ui/
|-- README.md
|-- package.json
|-- src/
|-- shell.tsx
|-- screens/
|-- components/
|-- stores/
|-- services/
`-- docs/

app/contracts/ui.py
app/services/persistence/ui.py
app/ui/tests/<feature>/
tests/examples/16_ui.py
```

Each visual feature is a cohesive component/store/service contribution with typed props, stable
entity identities, bounded effects, explicit cleanup, and colocated tests. Cross-boundary DTOs,
errors, events, and capability keys remain in `app/contracts/ui.py`; generated API types may
mirror but never redefine those semantics.

The client never executes SQL. Server-owned records are authoritative; local persistence is
limited to versioned layout, theme, drafts, and bounded view/cache state. Frontend usage evidence
lives in component/Vitest/Playwright scenarios; Python examples apply only to backend UI
contributions if any are introduced.

---

## 1. Purpose and boundary

### Purpose

Compose the accessible research workstation from domain-owned data and actions while preserving honest mock/live state, stable identity, and responsive long-running workflows.

### Owns

- Navigation, application shell, Dockview workspaces, forms, tables, charts, dialogs, progress, notifications, and accessibility.
- Typed client adapters, view state, drafts, selection, saved layout, theme, and presentation formatting.
- Visual contribution points that never absorb quantitative business logic.

### Does not own

- Authoritative jobs, strategies, simulations, metrics, persistence, or broker operations.
- Claimed pixel/native parity without visual reference evidence.

### Shared contracts


The public boundary is `app/contracts/ui.py`; private implementation imports are forbidden.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Partial | `ui.shell@1` | `ShellContribution` | `1` | Navigation, project header, theme, settings, notifications |
| Partial | `ui.research_workspace@1` | `ResearchWorkspace` | `1` | Builder with improve-existing mode, Retester, Optimizer and databanks |
| Partial | `ui.results_workspace@1` | `ResultsWorkspace` | `1` | Linked overview, trades, charts, source, robustness |
| Partial | `ui.data_manager@1` | `DataManagerView` | `1` | Data source, import, instrument and quality screens |
| Partial | `ui.algo_wizard@1` | `AlgoWizardView` | `1` | Rule-tree authoring and export surfaces |
| Partial | `ui.portfolio_workspace@1` | `PortfolioWorkspace` | `1` | Portfolio Master and Composer screens |
| Partial | `ui.custom_projects@1` | `CustomProjectView` | `1` | Project graph and task-manager screens |
| Missing | `ui.trading_dashboard@1` | `TradingDashboard` | `1` | Live execution, order management, and kill-switch dashboard |
| Missing | `ui.optimization_surface@1` | `OptimizationSurface` | `1` | Interactive 3D parameter optimization surface visualization |

### Persisted-state ownership


Semantic state remains feature-owned although storage mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Partial | `ui.v1` | `FEAT-UI-SHELL` and registry peers | `localStorage mock; target server/SQLite` | Explicit reference-safe policy | `ui.shell@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-UI-SHELL` | Navigation, project header, theme, settings, notifications | `app/ui/src/shell.tsx` | `ui.shell@1` | `gateway.application@1` | Partial |
| `FEAT-UI-RESEARCH` | Builder with improve-existing mode, Retester, Optimizer and databanks | `app/ui/src/research_workspace.tsx` | `ui.research_workspace@1` | `gateway.rest@1`, `gateway.streams@1` | Partial |
| `FEAT-UI-RESULTS` | Linked overview, trades, charts, source, robustness | `app/ui/src/results_workspace.tsx` | `ui.results_workspace@1` | `analytics.metrics@1` | Partial |
| `FEAT-UI-DATA` | Data source, import, instrument and quality screens | `app/ui/src/domains/data/DataManager.tsx` | `ui.data_manager@1` | `data.datasets@1` | Partial |
| `FEAT-UI-AUTHORING` | Rule-tree authoring and export surfaces | `app/ui/src/algo_wizard.tsx` | `ui.algo_wizard@1` | `strategy.authoring@1` | Partial |
| `FEAT-UI-PORTFOLIO` | Portfolio Master and Composer screens | `app/ui/src/portfolio_workspace.tsx` | `ui.portfolio_workspace@1` | `portfolio.definitions@1` | Partial |
| `FEAT-UI-PROJECTS` | Project graph and task-manager screens | `app/ui/src/custom_projects.tsx` | `ui.custom_projects@1` | `research.projects@1` | Partial |
| `FEAT-UI-TRADING` | Live broker monitoring, open positions, and kill switch UI | `app/ui/src/domains/trading/TradingDashboard.tsx` | `ui.trading_dashboard@1` | `gateway.rest@1` | Missing |
| `FEAT-UI-3DSURFACE` | Interactive 3D parameter optimization surface viewer | `app/ui/src/domains/optimization/OptimizationSurface.tsx` | `ui.optimization_surface@1` | `gateway.rest@1` | Missing |

Dependencies use versioned public contracts. Removing a contribution withdraws only its capability;
required consumers become attributed `BLOCKED`, optional operations return unavailable, and
retained state is not purged.

---

## 3. Domain workflows


### `WF-UI-RESEARCH` — Configure, run, and inspect a research job

- **Lead owner:** `FEAT-UI-RESEARCH`
- **Participants:** Shell, typed API client, job stream, stable tables, Dockview result panels, charts, notifications.
- **Input boundary:** Validated draft settings and selected immutable entities.
- **Output boundary:** Job receipt/progress, synchronized result identity, recoverable view state, accessible status.
- **Failure boundary:** Validation stays located; disconnect shows stale/reconnect state; server truth wins conflicts; mock operations remain labeled.
- **Acceptance:** `ATW-UI-RESEARCH-001`

### `WF-UI-DATA-SOURCES` — Configure and manage research datasets

- **Lead owner:** `FEAT-UI-DATA`
- **Participants:** Data Manager presentation, typed dataset capability, browser-safe file boundary, progress and notifications.
- **Input boundary:** Explicit provider/import configuration, selected dataset identities, contained browser files, and user-confirmed destructive intent.
- **Output boundary:** Validated mock configuration, bounded simulated operation state, or a safely rejected request with a located error.
- **Failure boundary:** Missing selection, invalid configuration, unsupported files, unavailable providers, cancellation, and dependency conflicts remain distinct; partial output is never presented as complete.
- **Acceptance:** `ATW-UI-DATA-SOURCES-001`

---

## 4. Feature specifications


This representative card applies to every registry entry; exact algorithms and states are in Section 9.

### `shell.tsx` — `FEAT-UI-SHELL`

> **Feature ID:** `FEAT-UI-SHELL`
> **Status:** `Partial`
> **Owner module:** `app/ui/src/shell.tsx`

#### Purpose

Provide navigation, project header, theme, settings, notifications without absorbing another feature's responsibility.

#### Capability declarations

- **Provides:** `ui.shell@1`
- **Requires:** `gateway.application@1`
- **Optional / operation-gated:** absence is explicit; no silent substitution.

#### Configuration and limits

Configuration is immutable, typed, versioned, and bounded. Reference sample values are not defaults.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Partial | `schema_version` | positive integer | `1` | Reject incompatible versions |
| Partial | `operation_timeout_s` | finite seconds | operation-specific | Positive and bounded |
| Partial | `resource_limit` | positive integer | deployment-specific | Reject unbounded/nonpositive |

#### Runtime effects and cleanup

| Effect | Acquisition | Cleanup / failure behavior |
| --- | --- | --- |
| Capability/contribution | Managed feature scope | Withdraw with scope |
| Task/subscription/resource | Managed lifecycle API | Reverse-order close; failed start unwinds |
| Durable mutation | Focused persistence/API protocol | Roll back; partial output remains unpublished |

#### Persistent state

- **Domain persistence module:** `app/services/persistence/ui.py`
- **Namespace:** `ui.v1`
- **Schema version:** `1` initially; forward migration only
- **Retention and purge:** explicit and reference-safe; removal never implicitly purges.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Partial | `shell.tsx` | Navigation, project header, theme, settings, notifications; configuration, service, lifecycle, immutable specification, factory/contribution | `ShellContribution` |
| Partial | `research_workspace.tsx` | Builder with improve-existing mode, Retester, Optimizer and databanks; configuration, service, lifecycle, immutable specification, factory/contribution | `ResearchWorkspace` |
| Partial | `results_workspace.tsx` | Linked overview, trades, charts, source, robustness; configuration, service, lifecycle, immutable specification, factory/contribution | `ResultsWorkspace` |
| Partial | `src/domains/data/DataManager.tsx` | Data source, import, instrument and quality screens; provider menus, configuration dialogs, direct dataset actions, bounded progress, and mock-only safety | `DataManager` |
| Partial | `src/domains/data/dataSourceRibbon.ts` | Typed provider-command, dialog, nested-exchange, and contextual-action inventory | `dataSourceProviders`, `dataSourceContextActions` |
| Partial | `algo_wizard.tsx` | Rule-tree authoring and export surfaces; configuration, service, lifecycle, immutable specification, factory/contribution | `AlgoWizardView` |
| Partial | `portfolio_workspace.tsx` | Portfolio Master and Composer screens; configuration, service, lifecycle, immutable specification, factory/contribution | `PortfolioWorkspace` |
| Partial | `custom_projects.tsx` | Project graph and task-manager screens; configuration, service, lifecycle, immutable specification, factory/contribution | `CustomProjectView` |
| Partial | `tests/examples/16_ui.py` | Offline primary-purpose evidence | one named scenario per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Partial | `FR-UI-001` | Stable IDs preserve selection under sort/filter/virtualization and streamed updates. | Component/E2E tests |
| Partial | `FR-UI-002` | Every long action has idle/running/paused/cancelling/terminal/error/reconnect states. | State tests |
| Partial | `FR-UI-003` | Dock layout is schema-versioned, persisted, migratable, and safely resettable. | Layout tests |
| Partial | `FR-UI-004` | Keyboard, focus, labels, announcements, reduced motion, and non-color status meet WCAG 2.2 AA. | Automated/manual a11y |
| Partial | `FR-UI-005` | The Data sources workspace provides a **Dukascopy data** menu with actions to add new Dukascopy symbols, download data for existing Dukascopy symbols, and view data-usage information. Adding a symbol supports instrument selection, Tick or M1 data, broker profile, and an optional data-name postfix. Downloading supports a date range, existing-data handling, and available download modes. | Component/E2E tests |
| Partial | `FR-UI-006` | The Data sources workspace provides a **TickDownloader import** action that accepts TickDownloader data files, displays the symbols available for import, accepts an optional data-name postfix, validates required selections, and starts a simulated import operation. | Component/E2E tests |
| Partial | `FR-UI-007` | The Data sources workspace provides **File import** actions to create a data symbol, import one file, import multiple files, and import data exported by a supported research-data application. Applicable configuration includes instrument, bar timestamp convention, timezone, timeframe, column mapping, separator, date format, skipped rows and columns, error policy, existing-symbol policy, and optional postfix. | Component/E2E tests |
| Partial | `FR-UI-008` | The Data sources workspace provides an **Equity data** search that displays matching ticker, name, exchange, type, and available-range information; configures the resulting dataset; presents applicable usage conditions; and adds selected datasets. A direct action updates previously added Equity datasets. | Component/E2E tests |
| Partial | `FR-UI-009` | The Data sources workspace provides a **Futures data** search that displays matching ticker, name, exchange, and available-range information; configures bar timestamp and timezone handling; presents applicable usage conditions; and adds selected datasets. A direct action updates previously added Futures datasets. | Component/E2E tests |
| Partial | `FR-UI-010` | The Data sources workspace provides **Darwinex Tick Data** actions to add available symbols, import symbols from Darwinex data files, and download additional history for existing datasets. Adding supports broker-profile selection, an optional postfix, and explicit instrument identification when automatic mapping is unavailable. | Component/E2E tests |
| Partial | `FR-UI-011` | The Data sources workspace provides **Crypto data** actions for Binance spot, Binance Coin-M, Binance USDT-M, Bitfinex, Poloniex, and Coinbase Pro. A user can choose an exchange, select and configure symbols, add them, and download additional history for existing Crypto datasets over a selected date range. | Component/E2E tests |
| Partial | `FR-UI-012` | The Data sources workspace provides **Yahoo data** actions to add one or more Yahoo symbols with an optional postfix and to download additional history for existing Yahoo datasets over a selected date range. | Component/E2E tests |
| Partial | `FR-UI-013` | The Data sources workspace provides the active SQX **MT5 import** workflow: MT5-like installation-folder metadata selection, explicit symbol fetch, categorized search/filter/selection, six date presets, broker profile, postfix, M1 definitions, automatic duplicate numbering, persistent simulated coverage, shared progress/actions and trailing status. Commented source/precision controls and native terminal/price access are excluded. | Component/E2E tests |
| Partial | `FR-UI-014` | **Update all** starts a simulated update for every eligible dataset. **Update selected** remains clickable and prompts for a dataset when none is selected; an update requires selected eligible datasets. Both expose truthful running, paused, completed, cancelled, and failure states. | State/E2E tests |
| Partial | `FR-UI-015` | **Mass delete** requires a selection and asks whether to remove selected dataset definitions or retain definitions while clearing data. A dependency warning is required before an operation that can disrupt derived-dataset updates. | Component/E2E tests |
| Partial | `FR-UI-016` | **Save** requires selected datasets and produces a browser-safe JSON definition export simulation. **Load** accepts a versioned JSON definition file, validates its kind, schema, values, and conflicting identities before application, and never reports a partial load as complete. | Component/E2E tests |
| Partial | `FR-UI-017` | Every Data sources menu, nested menu, dialog, confirmation, and long action has an accessible name, keyboard operation, Escape handling, invoking-control focus restoration, located validation errors, and non-color state. | E2E/manual a11y |
| Partial | `FR-UI-018` | Until authoritative provider capabilities exist, every provider download, import, update, save, and load is identified as a simulation and cannot contact providers, transmit credentials, mutate native application data, or imply successful market-data acquisition. | Negative E2E tests |
| Partial | `FR-UI-019` | Every Data sources dropdown command uses a purpose-specific icon: add-symbol commands use an add cue; searches use search; downloads use cloud download; single-file, multi-file, folder, application, and terminal imports use distinct file or source cues; information uses an information cue; updates use refresh; and each Crypto exchange choice uses a distinct exchange cue. Shape remains meaningful without color, text labels remain authoritative, and restrained color reinforces action categories without replacing accessible names. | Inventory/E2E tests |
| Partial | `FR-UI-020` | The Data sources workspace displays a full-width dataset table without an Available data sidebar. After the selection checkbox, columns appear in this order: Symbol Name, Instrument, Broker profile, Underlying Symbol, Timeframe, Timezone, Date from, Date to, Total Days, Total Records, Source, Bar type, Data type, Hide. Above the table, provide Filter items, data-source, data-type, stock-group, and broker-profile filters followed by the matching record count. Symbol Name supports ascending and descending sorting; selecting all affects visible rows. Display an empty-result message when filters match no rows and an em dash for unavailable metadata. Total Days counts inclusive calendar days between the displayed dates. The current sample data supports instrument-category filtering; stock-group and broker-profile filters remain disabled until configured, and Hide is a session-local flag. | E2E tests |
| Implemented | `FR-UI-021` | Switching among Data sources, Export, and Tools preserves the same dataset table, its filters, sorting, selection, and session-local Hide flags. Export provides the three active SQX workflows: Export to CSV with persisted custom formats and bounded browser CSV downloads, Export MT4 (FXT & HST) with specification loading and an explicitly non-native mock manifest, and Export to MT5 data (99% test) with source-dependent spread controls and overwrite confirmation. All jobs use the shared progress strip, pause/resume/stop actions, persistence, and the trailing Status column. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-022` | The Data Manager Tools toolbar contains exactly two actions in order: Clone to timezone, identified by a globe with a clock, and View & Analyze, identified by a candlestick chart. Clone to timezone validates the shared selection, prevents recursive clones, persists derived definitions and settings, and uses the shared progress controls and trailing Status column. View & Analyze provides virtualized deterministic data, chart, and quality views with persisted edits/deletions and discard confirmation. Both workflows retain the HaruQuantAI theme and state across reloads. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-023` | Data Manager provides separate Instruments and Sessions tabs. Instruments implements Add, Clone, Mass Edit, Mass Delete, Save, and Load. Sessions implements Add, Clone, Mass Delete, Save, and Load with the active SQX template editor, nested session-hours editor, Add Mon-Fri generation, broker postfixes, unsaved-change handling, dependency-safe deletion, and versioned Sessions JSON import/export conflict behavior. All state is browser-local and survives reload. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-024` | Instruments provides working Filter items, All data types, and All broker profiles controls above a selectable reactive table. Columns follow this order: Instrument, Description, Broker profile, Point value, Pip/Tick size, Pip/Tick step, Default spread, Default slippage, Commissions, Swap, Data type, Order size mult., Order size step, followed by row actions. Sorting, combined filters, visible-row select-all, double-click Edit, and trailing row deletion operate on the persisted shared catalogue. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-025` | Sessions provides working Filter items and All broker profiles controls above a full-width persisted table. Rows contain selection, Session Name, Broker profile, flexible space, and far-right delete. Search covers names and broker names, broker filtering works, visible-row select-all preserves hidden selections, double-click opens Edit, and row deletion uses the shared dependency-safe confirmation. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-026` | External indicators implements Add/Edit/Help, timestamped data import with reusable formats and persistent progress, metadata-only MQ4 recognition, View & Analyze, clear/delete, and versioned definition JSON Save/Load conflict handling. The seven actions follow active SQX registration order. The reactive table provides search, return-type filtering, visible select-all, double-click Edit, row delete, record metadata, and trailing job status. Definitions, imported records, formats, and jobs survive reload in validated browser-local state. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-027` | Stock groups implements Add/Edit metadata, historical member editing, bounded CSV replacement import, meaningful `GroupStocks.json` export, automatic local data updates with pause/reload/resume/stop, inline readiness updates, protected-group-aware mass deletion, and versioned `Groups.json` Save/Load conflict handling. The audited six actions and eight data columns are fully stateful; file-import groups synchronize into validated versioned persistence and generated Equity rows appear across Data sources, Export, and Tools. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-028` | Broker profiles implements Add/Edit with Stockpicker and MT4/5 settings, broker-aware stock membership and CSV import/JSON export, selected Instruments/Sessions JSON import with postfix and conflict handling, automatic persisted data updates with shared pause/reload/resume/stop, dependency-safe mass deletion, and versioned `Brokers.json` Save/Load conflict handling. The eight audited actions and seven data columns are fully stateful; customized counts derive from effective records and profile changes propagate to existing broker selectors. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Partial | `FR-UI-029` | Data Manager provides a Log tab after Broker profiles. Hide the action ribbon and progress strip on this tab and fill the remaining workspace with a bordered, scrollable log area. Display Log at the upper left and Clear log at the upper right. Show timestamped simulated operation transitions, retaining at most 500 entries during the mounted Data Manager session. Clear log removes displayed entries without stopping work; subsequent transitions can add entries. An unused or cleared log stays blank. | E2E tests |
| Partial | `FR-UI-030` | All nine Data sources provider icons and five contextual action icons use distinct or purpose-consistent accent colors while retaining their shapes and text labels. All toolbar buttons remain enabled and keyboard reachable. Clicking Update selected, Mass delete, or Save without selected datasets displays Select at least one dataset first and does not start an operation or open its dialog. | E2E tests |
| Implemented | `FR-UI-031` | The global Settings gear opens the audited command menu in its registered group order. Configuration provides Global, CPU, Performance, Memory, Databanks, Optimizations, and Troubleshooting tabs with validated draft/save behavior. Benchmark, Remote access, MCP Server, SMTP server, Language, Skin, Zoom/fullscreen, local support notices, Update license, About, Reload UI, and Exit expose complete browser-safe interactions. Secrets remain dialog-local, external/native effects are explicitly simulated, and preferences migrate older persisted state. Redundant standalone Theme/Help controls and the development-only Feature Profile selector are omitted from the header; Full is the normal UI fixture and Starter remains test-only policy state. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-032` | The header exposes Debug Console, Grid Control, and Volume & Market Profile actions in reference order before Settings, while omitting the duplicate Code Editor top action. Debug Console provides bounded category/text-filtered mock logs and Clear; Grid Control classifies current jobs into running/waiting/finished tables with manual and three-second display refresh plus error detail; Volume Profile presents inactive-addon information and safe local notices for unavailable commercial actions. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-033` | The application sidebar collapses from its 190 px labelled layout to a 49 px icon rail using matching line-and-chevron controls. Application icons, accessible names, tooltips, active state, and navigation remain available while labels, group headings, and the home shortcut hint are hidden. The preference is stored in the versioned application settings and survives reload. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |
| Implemented | `FR-UI-034` | Every rendered product label uses HaruQuantAI. Provider labels omit the legacy `SQ` prefix, the default broker is `Default`, and persisted legacy display strings are normalized before validation. Compatibility identifiers and lower-case browser-storage keys remain stable. Commercial reference links are replaced by truthful local mock notices. | Unit/E2E tests; `docs/dev/evidence/reimplementation.json` |

#### Removal behavior

Withdraw the capability and managed effects while retaining schema-readable artifacts. Dependent
operations return attributed unavailable; reinstall requires schema/version compatibility.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Partial | `ARCH-001` | TypeScript remains strict and presentation never redefines domain semantics. | Typecheck and contract tests |
| Partial | `ARCH-002` | Effects, subscriptions, charts, and streams have explicit cleanup. | Component lifecycle tests |
| Partial | `ARCH-003` | Server entities use stable IDs through sort/filter/virtualization. | Table/selection tests |
| Partial | `ARCH-004` | Public backend semantics originate in `app/contracts/ui.py` and generated API schemas. | Contract checks |
| Partial | `ARCH-005` | Domain calculations do not live in React components or client stores. | Review and boundary tests |
| Partial | `ARCH-006` | Local persistence is schema-versioned view state, never authoritative business truth. | Migration/corruption tests |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-UI-001` | React/TypeScript/Vite/Tailwind, Dockview, TanStack Table/Virtual, and Lightweight Charts are target stack. | Frontend | E-T01 |
| Open | `DEC-UI-002` | Pixel parity is unverified because native screenshots were unavailable. | Visual parity | Approved screenshot baselines |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; installed names and
sample values are not runtime proof.

---

## 7. Tests and definition of done

### Local execution and verification

```bash
# Development server (http://127.0.0.1:3000)
npm install
npm run dev

# Frontend verification suite
npm run typecheck
npm test
npm run build
npm run preview
```

### Demonstration scenarios

- **Builder:** Edit full settings, return to Progress, Start, Pause, Resume, Stop, then inspect Results.
- **Databanks:** Select multiple virtualized rows and copy/move between Results and Retest candidates.
- **Results:** Select a strategy and compare Overview, Trade list, Equity, Drawdown, Robustness, and optimization projections.
- **Optimizer:** Switch between Simple, Sequential, Walk-Forward, and WF Matrix to reveal applicable controls.
- **AlgoWizard:** Select a rule, remove it, add a configured block, and save the mock revision.
- **Portfolio Composer:** Change member weights/capital and run the shared-capital simulation.
- **Custom Projects:** Enable tasks and run the ordered workflow.
- **Data Manager:** Open each named provider menu and configuration dialog, exercise nested Crypto exchange choices, select datasets, run update/pause/resume/stop, review the mass-delete dependency warning, and open browser-safe save/load flows without producing an external provider request.

Workspace state is stored under local storage key `sqx-recreation-v1`. Open **Configuration → Mock developer tools → Reset fixture workspace** to restore deterministic seeds.

### Frontend evidence

- [Clean-room reimplementation ledger](../../docs/dev/evidence/reimplementation.json)

### Verification boundaries

```text
app/ui/src/**/*.test.ts
app/ui/src/**/*.test.tsx
app/ui/e2e/
docs/dev/evidence/reimplementation.json
|-- domains/trading/TradingDashboard.tsx
`-- domains/optimization/OptimizationSurface.tsx
```

Editing uses explicit affected paths with `--no-cov`; the full candidate gate remains
`uv run python scripts/ci_check.py`.

- [ ] Stable feature and requirement IDs have one owner.
- [ ] Typed API contracts and feature contribution boundaries exist.
- [ ] Rendering and imports have no network, timer, or subscription side effects.
- [ ] Happy, invalid, empty, loading, error, reconnect, conflict, and cleanup tests pass.
- [ ] Virtualized selection, linked results, layout migration, and accessibility tests pass.
- [ ] Playwright flows and approved visual baselines cover every primary surface.
- [ ] Domain status reflects repository evidence, not reference-product evidence.
- [ ] Architecture and full qualification gates pass.

---

## 8. Change process

1. Update this README and identify the exact feature/requirement scope.
2. Update `app/contracts/ui.py` and generated client types first when the boundary changes.
3. Implement one cohesive screen/component/store/service contribution under `app/ui/src`.
4. Keep server-owned records outside client persistence; version any layout/view-state change.
5. Update component tests, Playwright flow, and the coverage/parity/mock ledgers.
6. Verify cleanup, keyboard/focus behavior, removal, and affected screens.
7. Run frontend checks plus the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

Baseline E-R01 confirms a broad deterministic mock frontend: shell/theme/settings/notifications; Builder controls and progress, including improve-existing mode; Retester; Optimizer; virtualized databanks; linked results with Lightweight Charts; Data Manager; AlgoWizard; portfolio screens; custom projects; extensions; localStorage schema sqx-recreation-v1. It must be described as a research simulator, not engine parity. Partial gaps are authoritative backend/engine integration, dedicated retester controls, specialized robustness/3D/correlation renderers, arbitrary CSV mapping, proprietary formats, Dockview geometry persistence, complete undo/redo, comprehensive Playwright/visual baselines, and all native/provider/compiler/remote/MCP/SMTP/license/live operations. Interrupted mock jobs remain in last persisted state, not silently completed. Server-owned records replace localStorage as truth; client caches/view state remain bounded. Virtual rows and charts must preserve identity and dispose listeners/resources.

## Dukascopy Add Data popup (2026-09-19)

`FEAT-UI-DATA-DUKASCOPY-ADD` implements the Add Dukascopy data portion of
`FR-UI-005` in `src/domains/data/DukascopyAddDialog.tsx`, with catalogue contracts
in `dukascopy.ts` and mock definition state in `dataManagerStore.ts`.
The overall Data Manager and backend capabilities remain Partial.

The exact donor catalogue is tracked at `data/market/dukascopy/dukascopy.csv`
and bundled as a raw Vite import. All 725 symbols retain source ordering, grouping,
names, date availability and numeric metadata. No external installation or provider
is required at runtime. The versioned `sqx-data-manager-v1` browser namespace stores
mock definitions and optional mock broker profiles (maximum 10,000 and 100).
Save validates selection, consent, mappings and collisions before writing storage;
storage failure leaves existing state untouched. Definitions have empty downloaded
ranges and zero records. Actual downloads and broker profile management are separate
capabilities. Default broker inventory is empty, so only Default appears normally.

Evidence: `src/domains/data/dukascopy.test.ts` and
`tests/data-manager-dukascopy.spec.ts`; see [coverage details](../../docs/dev/evidence/reimplementation.json).
Frontend scenarios replace a Python usage example for this frontend-only change.

The Dukascopy popup inherits the application font and active dark/light theme.
SQX remains the reference for its frame/body arrangement and behavior, not skin.

## Dukascopy download workflow (2026-09-19)

`FEAT-UI-DATA-DUKASCOPY-DOWNLOAD` implements the download portion of `FR-UI-005`
using `DukascopyDownloadDialog.tsx`, `dukascopyDownload.ts`, and download state in
`dataManagerStore.ts`. It provides six date presets, two redownload policies, three
provider/CDN modes, the CDN disclaimer, trial confirmation and eligible-row selection.
The SQX structure uses the application typography and current dark/light theme.

The separate `sqx-data-download-v1` namespace stores one current mock job, completed
simulation intervals and chosen mode. Original add-data v1 definitions and fixture
history remain unchanged. On reload an interrupted running job is exposed as paused.
A component-owned timer advances running jobs only while Data Manager is mounted;
Pause/Resume/Stop and storage failure are explicit states. Mode changes deterministic
simulation speed. One synthetic sample per calendar day is used solely as mock metadata;
this is not provider tick or M1 history. Missing-only deduplicates previously simulated
intervals; overwrite regenerates the requested interval without deleting outside coverage.

The native controller's mixed-source filtering defect is not reproduced. Only eligible
Dukascopy rows are targeted. Starter is an explicit trial UI fixture; Full uses CDN by
default. QuantDataManager-only purchase UI is outside this SQX feature. Whole Data Manager
and backend capability status remain Partial. Evidence: `dukascopyDownload.test.ts` and
`tests/data-manager-dukascopy-download.spec.ts`; see the coverage register.

## TickDownloader import (2026-09-19)

`FEAT-UI-DATA-TICKDOWNLOADER-IMPORT` implements the frontend portion of FR-UI-006 in
`TickDownloaderImportDialog.tsx`, with metadata discovery in `tickDownloader.ts` and
mock lifecycle in `dataManagerStore.ts`. The dialog follows SQX's read-only installation
selector, single-column checkbox grid, postfix and Close/Start import controls while
inheriting HaruQuantAI's theme and typography.

Directory discovery uses browser relative paths: installation/tickdata subdirectories,
or immediate subdirectories when a data folder is selected directly. File contents and
absolute filesystem paths are neither read nor persisted. Limits are 20,000 selected
files, 1,000 symbols per import and 10,000 mock definitions. Folder cancellation does
not discard the previous in-memory selection. Empty folders absent from FileList cannot
be discovered. A new import after reload requires selecting the folder again.

`useTickDownloader` stores definitions, folder label, postfix and one metadata-only job
in `sqx-tickdownloader-v1`. Running jobs recover paused; resumes continue the synthetic
metadata simulation without claiming renewed file access. Progress, pause/resume/stop
and failure use the shared Data Manager bar, and row statuses use the blank trailing
column. No duplicate status panel is introduced. Completed definitions retain empty
history dates and zero actual records: no tick decoder or backend import exists.

Evidence is `tickDownloader.test.ts` and `tests/data-manager-tickdownloader.spec.ts`.
See [coverage register](../../docs/dev/evidence/reimplementation.json). Overall Data Manager remains Partial.

Dukascopy fast modes now require an all-profile confirmation explaining limited symbol
availability and standard fallback. Mock jobs persist per-target resolved modes; unknown
CDN availability uses standard simulation. No live capability manifest is available.

Dukascopy Data Disclaimer now opens the installed SQX provider disclaimer with its four
original paragraphs and Close controls, using the active HaruQuantAI theme.

File import > Add symbol now has source-derived settings, broker/instrument selection,
nested Add instrument with commission/swap configuration and explanation, persisted mock
file definitions/custom instruments, and cross-provider symbol collision checks. See
[coverage](../../docs/dev/evidence/reimplementation.json) for source evidence and explicit mock limitations.

File import now includes the source-backed single-file and Mass import dialogs. Single-file
import targets a selected File record and provides preview, column mapping, custom format
CRUD, strict row validation and stop/ignore policies. Folder import supports instrument
settings, postfix, overwrite/skip/numbered copies and persisted/filterable stock groups.
Imports share the existing progress controls and trailing status column. Application-data
migration was removed at owner request.

Files are read locally as bounded UTF-8 text. The mock persists normalized timestamps/counts,
not a real price series. Known timestamps deduplicate; unknown seeded coverage stays opaque.
A job resumes after reload in paused state, committing each file atomically. See
[file import coverage](../../docs/dev/evidence/reimplementation.json) for limits, source trace and evidence gaps.

Equity / Futures now use source-derived two-stage search/add dialogs, including exchange,
ticker/name/exact search, continuous futures, eligibility, result sorting/selection, postfix,
bar timestamp/timezone settings and the nested source usage conditions. They follow the app theme.
The catalogues and subscriptions are explicit offline fixtures (Full/Starter scenarios), since
SQX obtains these from backend responses. Add creates empty definitions, with shared progress,
pause/resume/stop and persisted recovery. See [SQ data coverage](../../docs/dev/evidence/reimplementation.json).

Darwinex now includes source-backed Add data (328-symbol donor catalogue), conditional broker
instrument mapping, folder import and selected-record download dialogs. The app theme is retained.
Folder discovery follows SQX's direct `log.gz` rules using local metadata; compressed ticks are not
decoded. Add/import records start empty; downloads use synthetic calendar-day coverage. All three
flows share persisted progress and trailing statuses. Full/Starter exercises the two download license
states as a mock policy. See [Darwinex coverage](../../docs/dev/evidence/reimplementation.json) for source trace and gaps.

## Crypto data workflows (2026-09-20)

`FEAT-UI-DATA-CRYPTO` implements all seven Crypto dropdown popup variants for `FR-UI-011`:
Binance spot, Binance Coin-M, Binance USDT-M, Bitfinex, Poloniex and Coinbase Pro Add dialogs,
plus Download data for existing Crypto records. The shared SQX Add structure is retained with each
exact title, a Symbol-only checkbox table, filter, provider-specific timeframe list, postfix,
free-data confirmation and Close/Save behavior. HaruQuantAI supplies the modal frame, font and
active dark/light theme.

SQX bundles no Crypto catalog. Its six compiled provider plugins fetch their current lists from
public exchange APIs. This frontend uses bounded offline fixtures with provider-native symbol forms
and clearly labels them as mocks; it makes no exchange request and does not claim current listings.
New definitions have zero bars. The versioned `sqx-crypto-data-v1` namespace stores definitions,
one mock job and synthetic date intervals. Running work reloads paused; pause/resume/stop/failure/
completion use the shared Data Manager progress bar and the unlabeled trailing Status column.

Download filters mixed selections to Crypto rows, rejects clones and work already in progress,
provides all six SQX date presets and missing-only/overwrite policies, and updates only selected
synthetic coverage. One sample per calendar day is metadata, not market data. Cross-provider name
reservations and active-operation guards include Crypto. Evidence is `crypto.test.ts` and
`tests/data-manager-crypto.spec.ts`; see [Crypto coverage](../../docs/dev/evidence/reimplementation.json) for all seven
stable feature entries and evidence gaps. Overall Data Manager and `FR-UI-011` remain Partial until
backend and live-provider integration exist.

## Yahoo data workflows (2026-09-20)

`FEAT-UI-DATA-YAHOO` implements both Yahoo dropdown popups for `FR-UI-011`. The ribbon now uses
the exact local Yahoo `y!` asset and the concise label `Yahoo`. Add Yahoo data accepts the SQX
comma, semicolon or newline ticker syntax, resolves a bounded offline catalogue, applies an optional
postfix and creates empty D1 records. Download Yahoo data filters mixed selections to eligible Yahoo
records and supplies the six SQX date presets plus missing-only and overwrite behavior.

The `sqx-yahoo-data-v1` namespace stores definitions, synthetic date intervals and one mock job.
Running work reloads paused; all lifecycle states use the shared Data Manager progress bar and the
trailing Status column. The implementation makes no Yahoo request and does not claim current
listings or prices. See [Yahoo coverage](../../docs/dev/evidence/reimplementation.json) for the source trace, stable feature
entries and evidence gaps.
