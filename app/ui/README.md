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
| Partial | `ui.research_workspace@1` | `ResearchWorkspace` | `1` | Builder, Improver, Retester, Optimizer and databanks |
| Partial | `ui.results_workspace@1` | `ResultsWorkspace` | `1` | Linked overview, trades, charts, source, robustness |
| Partial | `ui.data_manager@1` | `DataManagerView` | `1` | Data source, import, instrument and quality screens |
| Partial | `ui.algo_wizard@1` | `AlgoWizardView` | `1` | Rule-tree authoring and export surfaces |
| Partial | `ui.portfolio_workspace@1` | `PortfolioWorkspace` | `1` | Portfolio Master and Composer screens |
| Partial | `ui.custom_projects@1` | `CustomProjectView` | `1` | Project graph and task-manager screens |

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
| `FEAT-UI-RESEARCH` | Builder, Improver, Retester, Optimizer and databanks | `app/ui/src/research_workspace.tsx` | `ui.research_workspace@1` | `gateway.rest@1`, `gateway.streams@1` | Partial |
| `FEAT-UI-RESULTS` | Linked overview, trades, charts, source, robustness | `app/ui/src/results_workspace.tsx` | `ui.results_workspace@1` | `analytics.metrics@1` | Partial |
| `FEAT-UI-DATA` | Data source, import, instrument and quality screens | `app/ui/src/domains/data/DataManager.tsx` | `ui.data_manager@1` | `data.datasets@1` | Partial |
| `FEAT-UI-AUTHORING` | Rule-tree authoring and export surfaces | `app/ui/src/algo_wizard.tsx` | `ui.algo_wizard@1` | `strategy.authoring@1` | Partial |
| `FEAT-UI-PORTFOLIO` | Portfolio Master and Composer screens | `app/ui/src/portfolio_workspace.tsx` | `ui.portfolio_workspace@1` | `portfolio.definitions@1` | Partial |
| `FEAT-UI-PROJECTS` | Project graph and task-manager screens | `app/ui/src/custom_projects.tsx` | `ui.custom_projects@1` | `research.projects@1` | Partial |

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
| Partial | `research_workspace.tsx` | Builder, Improver, Retester, Optimizer and databanks; configuration, service, lifecycle, immutable specification, factory/contribution | `ResearchWorkspace` |
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
| Partial | `FR-UI-008` | The Data sources workspace provides an **SQ Equity data** search that displays matching ticker, name, exchange, type, and available-range information; configures the resulting dataset; presents applicable usage conditions; and adds selected datasets. A direct action updates previously added SQ Equity datasets. | Component/E2E tests |
| Partial | `FR-UI-009` | The Data sources workspace provides an **SQ Futures data** search that displays matching ticker, name, exchange, and available-range information; configures bar timestamp and timezone handling; presents applicable usage conditions; and adds selected datasets. A direct action updates previously added SQ Futures datasets. | Component/E2E tests |
| Partial | `FR-UI-010` | The Data sources workspace provides **Darwinex Tick Data** actions to add available symbols, import symbols from Darwinex data files, and download additional history for existing datasets. Adding supports broker-profile selection, an optional postfix, and explicit instrument identification when automatic mapping is unavailable. | Component/E2E tests |
| Partial | `FR-UI-011` | The Data sources workspace provides **Crypto data** actions for Binance spot, Binance Coin-M, Binance USDT-M, Bitfinex, Poloniex, and Coinbase Pro. A user can choose an exchange, select and configure symbols, add them, and download additional history for existing Crypto datasets over a selected date range. | Component/E2E tests |
| Partial | `FR-UI-012` | The Data sources workspace provides **Yahoo data** actions to add one or more Yahoo symbols with an optional postfix and to download additional history for existing Yahoo datasets over a selected date range. | Component/E2E tests |
| Partial | `FR-UI-013` | The Data sources workspace provides an **MT5 import** workflow with installed or portable source selection, installation-file selection, symbol discovery and filtering, date range, Tick or M1 precision, broker profile, optional postfix, validation, and simulated import progress. | Component/E2E tests |
| Partial | `FR-UI-014` | **Update all** starts a simulated update for every eligible dataset. **Update selected** remains clickable and prompts for a dataset when none is selected; an update requires selected eligible datasets. Both expose truthful running, paused, completed, cancelled, and failure states. | State/E2E tests |
| Partial | `FR-UI-015` | **Mass delete** requires a selection and asks whether to remove selected dataset definitions or retain definitions while clearing data. A dependency warning is required before an operation that can disrupt derived-dataset updates. | Component/E2E tests |
| Partial | `FR-UI-016` | **Save** requires selected datasets and produces a browser-safe XML definition export simulation. **Load** accepts an XML definition file, validates supported schema and conflicting identities before application, and never reports a partial load as complete. | Component/E2E tests |
| Partial | `FR-UI-017` | Every Data sources menu, nested menu, dialog, confirmation, and long action has an accessible name, keyboard operation, Escape handling, invoking-control focus restoration, located validation errors, and non-color state. | E2E/manual a11y |
| Partial | `FR-UI-018` | Until authoritative provider capabilities exist, every provider download, import, update, save, and load is identified as a simulation and cannot contact providers, transmit credentials, mutate native application data, or imply successful market-data acquisition. | Negative E2E tests |
| Partial | `FR-UI-019` | Every Data sources dropdown command uses a purpose-specific icon: add-symbol commands use an add cue; searches use search; downloads use cloud download; single-file, multi-file, folder, application, and terminal imports use distinct file or source cues; information uses an information cue; updates use refresh; and each Crypto exchange choice uses a distinct exchange cue. Shape remains meaningful without color, text labels remain authoritative, and restrained color reinforces action categories without replacing accessible names. | Inventory/E2E tests |
| Partial | `FR-UI-020` | The Data sources workspace displays a full-width dataset table without an Available data sidebar. After the selection checkbox, columns appear in this order: Symbol Name, Instrument, Broker profile, Underlying Symbol, Timeframe, Timezone, Date from, Date to, Total Days, Total Records, Source, Bar type, Data type, Hide. Above the table, provide Filter items, data-source, data-type, stock-group, and broker-profile filters followed by the matching record count. Symbol Name supports ascending and descending sorting; selecting all affects visible rows. Display an empty-result message when filters match no rows and an em dash for unavailable metadata. Total Days counts inclusive calendar days between the displayed dates. The current sample data supports instrument-category filtering; stock-group and broker-profile filters remain disabled until configured, and Hide is a session-local flag. | E2E tests |
| Partial | `FR-UI-021` | Switching among Data sources, Export, and Tools preserves the same dataset table, its filters, sorting, selection, and session-local Hide flags. Export displays three clearly labeled targets: Export CSV with a spreadsheet icon, Export MT4 (FXT & HST) with a terminal-download icon, and Export MT5 with a candlestick-chart icon. Icon styling must preserve these export targets. The current buttons identify the targets; export execution remains unimplemented. | E2E tests |
| Partial | `FR-UI-022` | The Data Manager Tools toolbar contains exactly two actions in order: Clone to timezone, identified by a globe with a clock, and View & Analyze, identified by a candlestick chart. These labels identify timezone conversion of a cloned dataset and inspection of dataset history and quality. The current controls expose the intended actions; execution remains unimplemented. | E2E tests |
| Partial | `FR-UI-023` | Data Manager provides separate Instruments and Sessions tabs. Instruments displays Add Instrument, Clone Instrument, Mass Edit Instrument, Mass Delete, Save, and Load in that order above the instrument table. Sessions displays Add Session, Clone Session, Mass Delete, Save, and Load in that order above a selectable table of session names and broker profiles. Use distinct add, copy, edit, delete, save, and load icons with full text labels. Add Instrument retains its simulated configuration dialog; remaining toolbar operations are presently visual entry points without execution handlers. | E2E tests |
| Partial | `FR-UI-024` | Instruments provides Filter items, All data types, and All broker profiles controls above a selectable table. Columns follow this order: Instrument, Description, Broker profile, Point value, Pip/Tick size, Pip/Tick step, Default spread, Default slippage, Commissions, Swap, Data type, Order size mult., Order size step, followed by row actions. Instrument names support ascending and descending sorting. Search matches names and descriptions; data-type filtering combines with search, and select-all affects visible rows. Unavailable metadata displays an em dash. Broker-profile filtering and row deletion remain disabled until their capabilities exist. | E2E tests |
| Partial | `FR-UI-025` | Sessions provides Filter items and All broker profiles controls above a full-width table. Rows contain a selection checkbox, Session Name, Broker profile, unused flexible space, and a far-right delete action. Search filters session names and select-all affects only visible rows; no matches produces an empty-result message. Missing broker profiles display an em dash. Broker-profile filtering and deletion remain disabled until their capabilities exist. | E2E tests |
| Partial | `FR-UI-026` | External indicators displays Add new, Import indicator data, Recognize from file, Mass delete, Save, and Load in that order with distinct add, file-import, file-search, delete, save, and folder icons. Above the table, provide Filter items, All data types, and a record count. Columns follow row selection in this order: Name, Values, Data type, Timeframe, Date from, Date to, Total Days, Total Records. With no indicators, show Records: 0 and No External indicators defined. The current table is empty, the type filter and select-all are disabled, and toolbar execution remains unimplemented. | E2E tests |
| Partial | `FR-UI-027` | Stock groups displays Add new, Edit stocks, Update data in group (automatic), Mass delete, Save, and Load in that order with distinct add, list-edit, refresh, delete, save, and folder icons. The full-width table contains row selection followed by Name, Count, Description, Number of symbols, Downloaded, Ready to use?, Data from, and Data to. Description takes the remaining width. When no groups exist, display No stock groups defined and disable select-all. The current workspace has no stock-group records; toolbar execution remains unimplemented. | E2E tests |
| Partial | `FR-UI-028` | Broker profiles displays Add new, Update data for broker (automatic), Import broker instruments from XML, Import broker sessions from XML, Edit stocks, Mass delete, Save, and Load in that order with distinct action icons. The full-width table contains selection followed by Name, Description, Postfix, Timezone, Customized stocks, Customized instruments, and Customized sessions. Description takes the remaining width. With no configured profiles, show No broker profiles defined and disable select-all. Toolbar execution remains unimplemented. | E2E tests |
| Partial | `FR-UI-029` | Data Manager provides a Log tab after Broker profiles. Hide the action ribbon and progress strip on this tab and fill the remaining workspace with a bordered, scrollable log area. Display Log at the upper left and Clear log at the upper right. Show timestamped simulated operation transitions, retaining at most 500 entries during the mounted Data Manager session. Clear log removes displayed entries without stopping work; subsequent transitions can add entries. An unused or cleared log stays blank. | E2E tests |
| Partial | `FR-UI-030` | All nine Data sources provider icons and five contextual action icons use distinct or purpose-consistent accent colors while retaining their shapes and text labels. All toolbar buttons remain enabled and keyboard reachable. Clicking Update selected, Mass delete, or Save without selected datasets displays Select at least one dataset first and does not start an operation or open its dialog. | E2E tests |

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

### Frontend documentation

- [Reference audit](docs/reference.md)
- [Coverage inventory](docs/coverage.json)
- [Interaction map](docs/interactions.md)
- [Navigation map](docs/navigation.md)
- [Mock contracts](docs/mock-contracts.md)
- [Parity ledger](docs/parity.md)

### Verification boundaries

```text
app/ui/src/**/*.test.ts
app/ui/src/**/*.test.tsx
app/ui/e2e/
app/ui/docs/coverage.json
app/ui/docs/parity.md
app/ui/docs/mock-contracts.md
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

Baseline E-R01 confirms a broad deterministic mock frontend: shell/theme/settings/notifications; Builder/Improver controls and progress; Optimizer; virtualized databanks; linked results with Lightweight Charts; Data Manager; AlgoWizard; portfolio screens; custom projects; extensions; localStorage schema sqx-recreation-v1. It must be described as a research simulator, not engine parity. Partial gaps are authoritative backend/engine integration, dedicated retester controls, specialized robustness/3D/correlation renderers, arbitrary CSV mapping, proprietary formats, Dockview geometry persistence, complete undo/redo, comprehensive Playwright/visual baselines, and all native/provider/compiler/remote/MCP/SMTP/license/live operations. Interrupted mock jobs remain in last persisted state, not silently completed. Server-owned records replace localStorage as truth; client caches/view state remain bounded. Virtual rows and charts must preserve identity and dispose listeners/resources.
