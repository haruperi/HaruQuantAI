# UI

> **Package:** `app/services/ui/`
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
[Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md) owns the
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
tests/services/ui/<feature>/
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
| `FEAT-UI-DATA` | Data source, import, instrument and quality screens | `app/ui/src/data_manager.tsx` | `ui.data_manager@1` | `data.datasets@1` | Partial |
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
| Partial | `data_manager.tsx` | Data source, import, instrument and quality screens; configuration, service, lifecycle, immutable specification, factory/contribution | `DataManagerView` |
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
