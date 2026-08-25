# V2 → V3 UI Migration Plan

Status: ACTIVE coordination plan · Created: 2026-08-25 · Owner inputs: V2→V3 migration dry run (2026-08-25), reviewer adjustments, phased donor-port recommendation.

## 0. Authority and session continuity

This document is a **coordination artifact for donor reuse only**. It is not a feature registry and not a delivery schedule:

- `app/ui/README.md` remains the sole feature/FR registry and feature-to-widget map.
- `docs/dev/IMPLEMENTATION_ORDER.md` remains the delivery sequencing authority; Phase 2 below maps to its Stage 1 entries and never overrides them.
- Every migration step executes through the normal three-role workflow (Planner → Executor → Reviewer) as its own task with evidence gates. **This plan never authorizes direct implementation.**

**Resume protocol for a fresh agent session:**

1. Read this document top to bottom; note every checked/unchecked item.
2. Read `docs/dev/IMPLEMENTATION_ORDER.md` Stage 1 to find the next feature entry.
3. Read the owning `app/ui/README.md` section for that feature.
4. Read the donor paths listed in the matrix row (§6) under `.migration/v2-ui/`.
5. Run the normal task workflow for that entry, citing this plan's row in the task spec.

**Checkbox update rule:** a checkbox in this document is updated only by the Executor of the completing task, and only when that task's approved dry run explicitly includes the line item. Checkboxes are never updated speculatively.

## 1. Central rule

> **Preserve V2's product work; preserve V3's architecture. When the two conflict, V3 always wins.**

V2 (`HaruquantAI-V2/app/ui`: Next.js 15 + zustand + zod, ~313 files, ~59k LOC, 82 unit-test files) is a visual/UX donor. V3 (`HaruquantAI/app/ui`: Vite 6, generated contracts, typed widget registry, mock provider) owns the architecture. The migration is a port, not an import: V2's shell, clients, stores, contexts, and workspace machinery are replaced, not carried over.

## 2. Classification rules

| Classification | Meaning |
|---|---|
| **KEEP** | V2 visual/product implementation is preserved substantially as-is; V3 contract/runtime wiring replaces V2 backend wiring. |
| **ADAPT** | UX/design/component logic is preserved but restructured into V3 feature/widget ownership and generated contracts. |
| **REPLACE** | V3 already solves this differently; harvest ideas/visuals only, use the V3 implementation. |
| **DROP** | Do not migrate into production V3; archive/reference only. |

Example: `price-ladder` is **KEEP** even though its `useDepthStream.ts` must disappear — we keep the ladder UI, not the V2 transport.

## 3. Non-goals (parked in §11)

No backend migration, no SSE/streaming layer, no governed preflight, no auth/session UI, no Playwright e2e setup, no training/education content — until their owning V3 stages exist.

## 4. Phase 0 — Donor baseline

Rationale for placement: `.migration/v2-ui/` lives at the **repository root, outside `app/ui/`**, so `tsc`, `vitest`, and IDE indexing never see donor code; no exclude churn in protected config files. The donor tree is **untracked**.

- [x] Copy `C:\Users\rharu\AppDev\HaruquantAI-V2\app\ui\` → `HaruQuantAI\.migration\v2-ui\` (owner, local) — done 2026-08-25: 387 files / 16.11 MB, 0 failed; excluded non-source artifacts (`node_modules`, `.next`, `dist`, `coverage`, `test-results`, `htmlcov`, `__pycache__`, `*.log`)
- [x] Add `.migration/` to `.gitignore` (own mini-task or first feature task) — done 2026-08-25 (TASK-UI-MIG-PHASE0)
- [x] Record donor provenance here: V2 commit SHA `ba06b61e5b2af1e911f70181528c6f4a492f03bf`, copy date `2026-08-25`
- [x] Re-verify donor inventory against §6 matrix (20 widget families); record any deltas here: `none — donor src/widgets contains exactly the 20 matrix families (verified 2026-08-25)`
- [x] Baseline verification before importing any donor component — all green:
  - [x] `uv run python scripts/generate_contracts.py --check` (from `app/ui`: `npm run contracts:check`) — 33 artifacts, 0 problems (2026-08-25)
  - [x] `app/ui`: `npx tsc --noEmit` — clean (2026-08-25)
  - [x] `app/ui`: `npx vitest run` — 10 files / 35 tests passed (2026-08-25)
  - [x] `app/ui`: `npm run build` — built in 2.44s, chunk-size warning only (2026-08-25)
  - [x] `uv run pytest --no-cov tests/ui` — 13 passed (2026-08-25)
  - [x] pre-commit gates (`uv run pre-commit run --all-files` or equivalent) — changed-file run passed (2026-08-25)

## 5. Phase 1 — Conventions adopted (rules land with this document)

- [x] Per-widget transaction (§7) adopted for every migration — adopted 2026-08-25 (TASK-UI-MIG-PHASE1; rules landed with a43eef2)
- [x] Generated-contracts-only rule adopted (§8.1) — adopted 2026-08-25 (TASK-UI-MIG-PHASE1; rules landed with a43eef2)
- [x] Mock-growth rule adopted (§8.2) — adopted 2026-08-25 (TASK-UI-MIG-PHASE1; rules landed with a43eef2)
- [x] Scoped state rule adopted (§8.3) — adopted 2026-08-25 (TASK-UI-MIG-PHASE1; rules landed with a43eef2)
- [x] Mock-stage streaming rule adopted (§8.4) — adopted 2026-08-25 (TASK-UI-MIG-PHASE1; rules landed with a43eef2)
- [x] Red zones (§8.5) acknowledged — adopted 2026-08-25 (TASK-UI-MIG-PHASE1; rules landed with a43eef2)

## 6. Widget migration matrix

Progress legend: `M` mock done · `U` UI migrated · `T` tests ported/passing · `D` donor folder deleted. Tracker entries refer to `docs/dev/IMPLEMENTATION_ORDER.md`.

| V2 widget | Class | Tracker / FEAT | V3 widget slugs | Generated contracts | M U T D |
|---|---|---|---|---|---|
| `workspaces` (+`public/templates`) | REPLACE | 1.3 MANAGE_LAYOUTS | (V3 engine exists) presets → `workspace_templates` | `ui.ts`, `workspace.ts` | ☑ ☑ ☑ ☐ | (2026-08-25) donor consumed for templates/persistence algorithms; donor folder retained — family also feeds later rows; deletion at Phase 3 sweep |
| `components/workflow` (form-heavy pieces) | ADAPT | 1.4 EDIT_INPUTS | `schema_form`, `selection_table`, `confirmation` | `ui.ts` | ☐ ☐ ☑ ☐ | (2026-08-26) completable slice FR-UI-PRESERVE_DRAFTS done (draft store; contract-level tests); donor workflow pieces remain for the 6.15 de-mock |
| `components/common`, alarm/status patterns | ADAPT | 1.5 MONITOR_WORK | `job_progress`, `activity_log`, `notifications` | `ui.ts`, `orchestration.ts` | ☑ ☑ ☑ ☐ | (2026-08-26) completable slice FR-UI-TRACK_PROGRESS, FR-UI-STREAM_ACTIVITY, FR-UI-PRESENT_FAILURES done (job_progress, activity_log; snapshot log); notifications widget completes at 14.10 |
| `system-settings` | ADAPT | 1.6 ADMINISTER_SYSTEM | `settings`, `capability_admin`, `updates` | `ui.ts`, `plugins.ts`, `interfaces.ts`, `orchestration.ts` | ☑ ☑ ☑ ☑ | (2026-08-26) completable slice FR-UI-SET_APPEARANCE, FR-UI-CONFIGURE_CLIENT, FR-UI-MANAGE_LICENSE done (settings widget); donor deleted; mock builds language/updates/capabilities complete at 3.10/14.11/15.8 |
| `human-factors` (a11y/alert semantics) | ADAPT | 1.7 ENSURE_ACCESS | strengthen shell/accessibility surfaces | `ui.ts`, `trading.ts`, `risk.ts` | ☐ ☐ ☐ ☐ |
| `markets`, `watchlists`, `instrument-panels`, `market-hours`, `session-registry` | ADAPT | 1.8 MANAGE_DATA | `datasets`, `instruments`, `sessions`, `data_quality` | `ui.ts`, `catalogue.ts`, `data.ts` | ☐ ☐ ☐ ☐ |
| (mostly V3-native; harvest where useful) | ADAPT | 1.9 AUTHOR_STRATEGIES | `strategy_tree`, `block_catalogue`, `strategy_inspector` | `ui.ts`, `strategy.ts` | ☐ ☐ ☐ ☐ |
| `analytics` (library/table/query) | ADAPT | 1.10 OPERATE_DATABANKS | `databank_browser`, `databank_bulk_actions` | `ui.ts`, `analytics.ts` | ☐ ☐ ☐ ☐ |
| `analytics`+`simulator`+`chart` | ADAPT | 1.11 EXPLORE_RESULTS | `result_overview`, `result_charts`, `result_trades`, `result_robustness`, `result_provenance` | `ui.ts`, `simulator.ts`, `analytics.ts` | ☐ ☐ ☐ ☐ |
| (V3-native unless a donor equivalent exists) | — | 1.12 EDIT_CODE | code editor widgets | `ui.ts` | ☐ ☐ ☐ ☐ |
| `research` (builders/comparisons/run status) | KEEP/ADAPT | 1.13 RUN_RESEARCH | `research_builder`, `research_monitor`, `research_comparison` | `ui.ts`, `research.ts`, `strategy.ts`, `simulator.ts` | ☐ ☐ ☐ ☐ |
| `planning` + workflow-page UX | ADAPT | 1.14 EDIT_PROJECTS | `project_editor`, `task_graph`, `project_run` | `ui.ts`, `orchestration.ts` | ☐ ☐ ☐ ☐ |
| `analytics` (charts/tables, reuse) | ADAPT | 1.15 COMPOSE_PORTFOLIOS | `portfolio_builder`, `portfolio_comparison`, `portfolio_results` | `ui.ts`, `portfolio.ts` | ☐ ☐ ☐ ☐ |
| `trading`, `price-ladder`, `market-ticks`, watchlist interactions, `emergency-ux` behavior | KEEP/ADAPT | 1.16 OPERATE_TRADING | `order_ticket`, `positions_orders`, `price_ladder`, `trading_session` | `ui.ts`, `trading.ts`, `broker.ts`, `risk.ts`, `data.ts` | ☐ ☐ ☐ ☐ |
| (last — conventions established) | — | 1.17 EXTEND_VIEWS | declarative/external widget contribution | `ui.ts`, `plugins.ts` | ☐ ☐ ☐ ☐ |
| `news` | ADAPT | later Data/Research stages | market-news views (NOT V3 `product_news`) | `ui.ts`, `data.ts`, `research.ts` | ☐ ☐ ☐ ☐ |
| `chart` (standalone) | REPLACE | absorbed by 1.11 | chart primitives inside owning widgets | owner-dependent | ☐ ☐ ☐ ☐ |
| `simulator` (run surfaces) | ADAPT | 1.11 + 1.13 monitors | result/run-state surfaces | `ui.ts`, `simulator.ts` | ☐ ☐ ☐ ☐ |
| `training-ux` (+content, `docs/education`) | DROP | — | none (no V3 feature; see §11) | — | ☐ ☐ ☐ ☐ |
| `workflow-pages`, `App.tsx`, `app/`, `clients/`, `context/`, `store/`, `types/` | REPLACE | — | harvest visuals only; V3 engine/contracts win | — | n/a |

Special classifications:

- **`training-ux` → DROP.** Useful idea ≠ valid V3 feature. If HaruQuantAI later needs a Learning/Training capability, it enters through the normal V3 design process, not by migration.
- **`human-factors` / `emergency-ux` → ADAPT into existing homes**, not standalone widgets: human factors → `system_status`, `notifications`, `activity_log`; emergency handling → `trading_session`, `notifications`, `activity_log`. Preserve behavior, not the V2 directory taxonomy.

## 7. Per-widget migration transaction

Every migrated widget follows the same mini-process, executed inside the owning feature's task:

```text
V2 donor widget
 1. Identify owning FEAT-UI-* (tracker entry)
 2. Identify canonical V3 widget slug
 3. Copy visual React implementation only
 4. Remove V2 clients, stores, contracts/types, Next deps, direct fetch/streams
 5. Bind generated V3 contracts (adapt widget, or change contract via its process)
 6. Build/grow typed mock fixture + provider support
 7. Register widget with WidgetRegistry (single FEAT-UI-* owner)
 8. Test states: loading, empty, ready, stale, degraded, failure, recovery
 9. Accessibility + removal/leak tests
10. typecheck / vitest / build / contracts:check
11. Delete that donor folder (monotonic donor reduction)
```

## 8. Migration rules

1. **Contracts.** Widgets consume only generated contracts from `app/ui/src/contracts/generated/`. Never hand-mirror a V2 type (e.g., no new handwritten `TradingPosition` interface). If a V2 component cannot be satisfied by a ratified contract, either adapt the component or change the contract through the documented contract process.
2. **Mocks.** `src/mocks/` stays dev-only, gated, visibly non-authoritative, whole-folder deletable. Fixtures/scenarios **grow per feature** — each task adds exactly what its tests need (loading/empty/failure at minimum). No pre-built 12-domain fixture tree. Flow is always: widget → V3 client capability → generated contract → mock provider now, real provider at de-mock stage. Never widget → fake store → hardcoded object.
3. **State.** Feature-local state (including zustand) is allowed as an explicit per-task decision recorded in the owning feature README. Cross-feature shared stores and anything resembling domain state (positions, balances, quotes) are banned. No simulated intervals (V2's 1.2 s fake-quote `setInterval` dies permanently).
4. **Streaming at mock stage.** Streaming-fed widgets (market ticks, depth ladder) present bounded snapshots or an explicit "awaiting live feed — de-mock stage" state. Only ratified subscription ports (`monitor_work`, `operate_trading`) may carry events. Never simulate streams against the mock.
5. **Red zones (V2 must never overwrite):** `app/ui/package.json`, lockfile, `index.html`, `vite.config.ts`, `tsconfig.json`, `src/main.tsx`, `src/accessibility/`, `src/clients/`, `src/context/`, `src/contracts/`, `src/features/`, `src/mocks/`, `src/runtime/`, `src/workspaces/`, and existing `src/widgets/{home,product_news,system_status,widget_catalogue}/`.
6. **CSS.** Harvest V2 `index.css` into an explicitly temporary `legacy-v2.css`; extract design tokens/base classes incrementally. Never permanently import the entire V2 global stylesheet.
7. **Dependencies.** Add a V2 dependency only when a migrated component demonstrably needs it (e.g., `lucide-react`), one at a time, inside the owning task. No blanket installs of zustand/zod/playwright.
8. **Primitives.** `components/common` harvesting rides inside the first feature task that needs a primitive — no standalone speculative harvest pass.

## 9. Phase 2 — Feature-by-feature execution (tracker order)

Each line is one normal workflow task; donors come from the matrix row. A task's dry run includes "update this plan's §9/§6 row" when it completes.

- [x] 1.3 `FEAT-UI-MANAGE_LAYOUTS` — donors: `widgets/workspaces` presets, `public/templates` (done 2026-08-25; donor folder retained for later rows)
- [x] 1.4 `FEAT-UI-EDIT_INPUTS` — completable slice done 2026-08-26 (FR-UI-PRESERVE_DRAFTS); donor workflow pieces remain for the 6.15 de-mock
- [x] 1.5 `FEAT-UI-MONITOR_WORK` — completable slice done 2026-08-26 (FR-UI-TRACK_PROGRESS, FR-UI-STREAM_ACTIVITY, FR-UI-PRESENT_FAILURES; job_progress, activity_log; snapshot log); notifications widget completes at 14.10
- [x] 1.6 `FEAT-UI-ADMINISTER_SYSTEM` — completable slice done 2026-08-26 (FR-UI-SET_APPEARANCE, FR-UI-CONFIGURE_CLIENT, FR-UI-MANAGE_LICENSE; settings widget); donor deleted; language/updates/capabilities complete at 3.10/14.11/15.8
- [ ] 1.7 `FEAT-UI-ENSURE_ACCESS` — donors: `human-factors` a11y/alert semantics
- [ ] 1.8 `FEAT-UI-MANAGE_DATA` — donors: `markets`, `watchlists`, `instrument-panels`, `market-hours`, `session-registry`
- [ ] 1.9 `FEAT-UI-AUTHOR_STRATEGIES` — donors: minimal; build V3-native
- [ ] 1.10 `FEAT-UI-OPERATE_DATABANKS` — donors: `analytics` library/table/query
- [ ] 1.11 `FEAT-UI-EXPLORE_RESULTS` — donors: `analytics`, `simulator`, `chart`
- [ ] 1.12 `FEAT-UI-EDIT_CODE` — donors: only if a real equivalent exists; else V3-native
- [ ] 1.13 `FEAT-UI-RUN_RESEARCH` — donors: `research` family (highest-reuse task)
- [ ] 1.14 `FEAT-UI-EDIT_PROJECTS` — donors: `planning`, workflow-page UX
- [ ] 1.15 `FEAT-UI-COMPOSE_PORTFOLIOS` — donors: `analytics` charts/tables (reuse)
- [ ] 1.16 `FEAT-UI-OPERATE_TRADING` — donors: `trading`, `price-ladder`, `market-ticks`, `emergency-ux` behavior
- [ ] 1.17 `FEAT-UI-EXTEND_VIEWS` — last; all built-in conventions established

## 10. Phase 3 — Sweeps and closure

- [ ] **Legacy-import sweep:** zero production references to `next/*`, V2 clients, `useTradingStore`, V2 handwritten types, V2 workspace machinery, fake quote intervals, V2 backend URLs
- [ ] **Mock-boundary sweep:** no production widget imports `src/mocks` directly; mock selection happens only at the client/bootstrap boundary
- [ ] **Ownership sweep:** every widget's `owning_feature` is exactly one `FEAT-UI-*` and appears in the README feature-to-widget map
- [ ] **Donor deletion:** `.migration/v2-ui/` deleted entirely; `.gitignore` entry removed; deleting the donor tree changes nothing
- [ ] **Stage 1 UI checkpoint:** launch, workspaces, dockview manipulation, capability/readiness states, temporal state, layouts/drafts, and every mock-backed feature visibly non-authoritative
- [ ] **Final zeros:** donor remaining = 0 · unmapped V2 widget = 0 · handwritten V2 contract = 0 · V2 backend client = 0 · V2 authoritative store = 0 · Next runtime dependency = 0

## 11. Deferred-items registry (revisit at owning stages)

| Item | Reason | Revisit |
|---|---|---|
| SSE/streaming layer (`clients/stream.ts`, `context/streams.ts`) | No V3 event surface yet beyond two ratified subscriptions | Interfaces/events domain stage |
| Governed-action preflight (`context/governed.ts`) | No V3 governed-request surface yet | Trading/risk stages |
| Auth/session + login UI | No V3 identity surface yet | Access/identity stage |
| Playwright e2e | Valuable journeys; rewrite after Stage 1 checkpoint | Post-checkpoint |
| `training-ux`/education | No owning V3 feature | Product decision only |
| V2 `docs/`, `resources/` | Design reference only | n/a |

## 12. Expected reuse tiers

| Reuse value | Donor areas |
|---|---|
| Very high | `price-ladder`, `trading`, `research`, `analytics`, major CSS/design work |
| High | `markets`, `watchlists`, `market-hours`, `session-registry`, `system-settings`, `planning` |
| Moderate/conceptual | `simulator`, `instrument-panels`, `emergency-ux`, `human-factors` |
| Architecture replacement | `App.tsx`, `app/`, `workspaces`, `workflow-pages`, `clients`, `context`, `store`, `types` |
| Drop | `training-ux` runtime, `scratch/`, Next infrastructure, duplicate SSOT docs |

This is a port of V2's product work into V3's feature model — generated contracts, truthful mocks, V3 workstation — fully compatible with the Stage 1 mock-first strategy and per-domain de-mocking.
