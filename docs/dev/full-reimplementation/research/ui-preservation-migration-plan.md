# Preserve the current UI while consolidating it into app/web

Date: 2026-10-30. Status: executed; see [verification and limitations](ui-preservation-migration-verification.md).

The user requires the existing browser UI to retain its appearance, interactions and existing work while its implementation moves from `ui/` into the canonical `app/web/` structure. Continue feature implementation on that migrated application. The current UI is the presentation baseline; the new bootstrap is infrastructure to integrate with it.

## Execution package and precedence

- [Exact migration manifest](ui-preservation-migration-manifest.csv): one row for every tracked file in `ui/` and `app/web/`, including source hashes, proposed destinations, actions and execution phase.
- [Complete target file tree](ui-preservation-target-tree.txt): preserved existing files and existing target helpers after consolidation. This is separate from the future feature inventory in the workspace plans.
- Existing architecture: [Core architecture](../../../ARCHITECTURE.md), [Home](../02-AppHome.md), and workspace documents 03–20 supply ownership and later feature contracts.

This plan defines the structural migration scope requested by the user. It does not release blocked backend work orders or claim donor functionality. Before moving application code, UI-M00 records the decisions below in the affected dispatch/workspace documents, so later executors do not follow conflicting instructions. The Core C00 restriction against importing the old UI applied to that isolated bootstrap order; do not retroactively describe C00 as a completed application migration.

Execution is complete for the structural migration. The work-order checklists below record execution, with the dedicated alternate-profile screenshot coverage limit left explicit. The verification report is authoritative for measured evidence, diagnostic caps, baseline failures and coverage limits; checked migration tasks do not assert that every legacy E2E test or every dialog permutation passes.

## Verified starting point

The inventory was taken from Git on 2026-10-30 with a clean working tree before these planning artifacts were written.

| Area | Observed state | Migration consequence |
|---|---|---|
| Existing UI | 953 tracked files under `ui/`; all present on disk | Every file must have an accounted-for disposition |
| Existing target | 14 tracked files under `app/web/` | Merge and retain work; never overwrite the target directory wholesale |
| Current entrypoint | `ui/app/main.tsx`: StrictMode → BrowserRouter → App; global CSS then Dockview CSS | Preserve provider tree, mount behavior and style ordering |
| Target entrypoint | `app/web/shell/bootstrap.tsx` renders only `<main>HaruQuantAI</main>` | Replace placeholder application mounting with the real existing application |
| Existing target behavior | theme projection plus Home notes preview/databank defaults and their tests | Preserve implementations and assertions |
| Target tests | Two Home tests currently live under `tests/workspaces/home/` | Normalize to singular `tests/workspace/home/` without dropping tests |
| Styles/build | Existing Vite uses React + Tailwind; target uses React alone | Preserve Tailwind compilation, stylesheet imports and generated utility coverage |
| Development API | Existing Vite uses loopback-validated `HARU_TEST_API_TARGET`, `/api` proxy, port 3000 | Carry forward the working development contract |
| Persistence | Host store uses `sqx-recreation-v1`, version 1 | Preserve key, version, defaults, hydration and origin during parity checks |
| CI scripts | `scripts/ci_check.py` runs `npm --prefix ui` | Change the active frontend commands at cutover |
| GitHub workflow | `.github/workflows/qualification.yml` references `app/ui` and absent `scripts/release_check.py` | Explicit pre-existing CI defect; resolve the frontend path and choose a valid qualification entrypoint |
| Generated tracked files | `ui/vite.config.js` and `ui/vite.config.d.ts` | Verify they are generated, then retire them so TS config is authoritative |
| Other generated files | node_modules, dist, tsbuildinfo and possible test artifacts | Rebuild locally; do not migrate generated directories as source |

No UI build, unit suite, browser suite or screenshot comparison has been run for this planning task. Baseline health remains to be measured in UI-M01.

## Preservation contract

1. Preserve all current workspaces and their content, including Chart and MT Analyzer, even when absent from the donor allocation.
2. Preserve navigation labels/order/icons, routes/aliases, query parameters, tabs, keyboard behavior, modal flows, table layouts, docking, resizing and splitters.
3. Preserve light/dark skins, feature-profile behavior, zoom, responsive behavior, CSS specificity/order, global variables, assets, chart rendering and existing education content.
4. Preserve existing transport behavior, endpoints, authentication handling and streaming behavior during the move. Do not change Python contracts in a structural migration.
5. Preserve browser persistence schemas and keys. Moving the source directory must not reset preferences, projects, drafts or chart layouts. Validate using the same origin; changing a port creates a different storage origin.
6. Keep current fixtures/default data/preview behavior where production imports depend on them. Do not invent service success or reclassify previews as real executions. Record existing service limitations rather than silently changing them.
7. Rename source files and exports only when required by an explicit destination. Do not rename visible labels, route IDs or persisted identifiers to match directory names.
8. Retain useful existing `app/web` helpers/tests. Configuration and entrypoint collisions require reviewed merges.
9. Keep current test assertions meaningful. Update paths, not expected business behavior, merely to make migration checks pass.
10. Do not create all future panel files from the previously extracted plan tree. Future feature names are requirements for later work, not replacement stubs for existing components.

## Target ownership and decisions

### Existing application files

| Current source | Target | Decision |
|---|---|---|
| `ui/app/main.tsx` | `app/web/shell/bootstrap.tsx` | Merge real mounting into target entrypoint |
| `ui/app/host/*` | `app/web/shell/*` | Retain App, router, store, transport, types, menus, modals and styles |
| `ui/app/components/*` | `app/web/common/components/*` | Keep reusable controls and documentation |
| `ui/app/assets/*` | `app/web/common/assets/*` | Keep images; rewrite URLs/imports |
| `ui/docs/*` | `app/web/docs/*` | Retain education content and links |
| `ui/app/plugins/data_source/*` | `app/web/workspaces/data_manager/plugins/*` | Preserve complete provider/catalog/tool hierarchy |
| `ui/app/plugins/databank/*` | `app/web/workspaces/results/databank/*` | Results owns databank implementation; other workspaces import it |
| `ui/app/plugins/optimization/*` | `app/web/workspaces/optimizer/plugins/*` | Preserve current hierarchy without duplicate wrappers |
| `ui/app/plugins/project/ProjectWorkbench/*` | `app/web/common/project/*` | Keep shared project frame/contracts/settings/results single-owned |
| `ui/app/plugins/project/README.md` | `app/web/common/project/registry.md` | Preserve module registry separately from the Workbench README |
| `ui/app/plugins/project/Results*/*` | `app/web/workspaces/results/Results*/*` | Keep named result modules, CSS and provenance |
| `ui/app/plugins/project/SettingsRankings/*` | `app/web/workspaces/builder/SettingsRankings/*` | Builder owner |
| `ui/app/plugins/project/SettingsCrossChecks/*` | `app/web/workspaces/retester/SettingsCrossChecks/*` | Retester owner |
| `ui/app/plugins/project/SettingsAdvancedTM/*` | `app/web/workspaces/task_manager/SettingsAdvancedTM/*` | Task Manager owner |
| Remaining project modules: EnginePanel, ProjectResults, ProjectSettings, SettingsData, SettingsMoneyManagement, SettingsNotes, SettingsOptions, SettingsPanel | Same module names beneath `app/web/workspaces/home/` | Home/project configuration owner; existing consumers remain functional |

Keep the shared Workbench implementation under `common/project`; do not copy it into Builder, Retester and Optimizer. Workspace-specific implementations already present alongside it also survive. Do not deduplicate similar implementations until a separate behavior-backed change establishes equivalence.

### Workspace names

| Current folder | Target folder under `app/web/workspaces/` |
|---|---|
| Home | `home` |
| DataManager | `data_manager` |
| CodeEditor | `code_editor` |
| AlgoWizard | `algo_wizard` |
| Results | `results` |
| Retester | `retester` |
| Builder | `builder` |
| Optimizer | `optimizer` |
| PortfolioComposer | `portfolio_composer` |
| PortfolioMaster | `portfolio_master` |
| CustomProjects | `task_manager` |
| NeuralNetwork | `neural_network` |
| GridControl | `grid_control` |
| GridTest | `grid_test` |
| DebugConsole | `debug_console` |
| Business | `business` |
| AIAssistant | `ai` |
| Trading | `trading` |
| Chart | `chart` |
| MTAnalyzer | `mt_analyzer` |
| Catalog | `marketplace` when implementation exists; currently an empty folder |

The manifest covers files; empty Catalog is not a missing file. Do not fabricate a marketplace screen as part of migration.

### Conflicts resolved for migration

| Conflict | Migration decision | Follow-up |
|---|---|---|
| `wizard` vs `algo_wizard` | Preserve current AlgoWizard under `algo_wizard`; `/algowizard` remains unchanged | Update AppWizard future UI targets to this namespace in UI-M00; do not create a second application |
| `sqai` vs `ai` | Use `ai`, including ConfigureMcpModal and future MCP tests | Correct Business/AI references in UI-M00 |
| `tests/workspaces`, `tests/workspace`, direct workspace test roots | Use `tests/workspace/<owner>` for migrated workspace tests; retain `tests/shell`, `tests/common`, `tests/e2e` | Align future acceptance commands; do not create both layouts |
| Missing `navigation.ts` and `navigationState.ts` sources | Actual current files are `router.tsx` and `store.ts`, with navigation embedded in App | Preserve those files and behavior; amend stale mapping rows instead of inventing replacement state machines |
| CustomProjects component name | Move and rename `CustomProjectsWorkspace.tsx` and exported component to `TaskManagerWorkspace.tsx` / `TaskManagerWorkspace` | Preserve visible Custom Projects label, `/projects`, module ID `projects`, current task catalogue and execution behavior |
| Business screen differs from future donor business scope | Preserve current screen under `business/` | Future product-build changes require a separate plan; never replace the screen merely to satisfy donor naming |
| Business-owned node/MCP modals | Move AddNodeModal to `grid_control`, ConfigureMcpModal to `ai`; preserve Business imports and user access | No store extraction/service replacement in migration |
| Runtime fixtures targeted for test-only relocation | Keep runtime-dependent fixtures under migrated production owners for now | Later service work separates types/defaults/catalogues from genuine test fixtures; production must never import `tests/` |
| `portfolioOptimization.ts` retirement instruction | Preserve the file and current behavior during migration | Any retirement belongs to a separately qualified numerical/service change |
| Source-map/registry paths | Preserve original evidence hashes and donor logical paths; update only Haru source locators and resolvers | A path move does not establish donor parity or authorize regenerating evidence |

These are explicit preservation-driven amendments to older migration rows, not claims that those later feature adaptations are completed.

### Manifest semantics

`MOVE`: keep implementation, update references. `MOVE_ADAPT`: path-bearing configuration/tests/content need editing. `MERGE`: two inputs contribute to one retained target. `RETAIN`: keep an existing target helper. `ADAPT`: replace obsolete bootstrap-only assertions. `CONSOLIDATE_RETIRE`: transfer required TypeScript options into one target config, then retire obsolete config files. `RETIRE_GENERATED`: remove only verified generated Vite outputs.

The manifest has 967 source rows: 953 existing UI files and 14 target files. Hashes are pre-migration byte baselines, not required post-migration hashes for files whose imports change. A completed implementation must explain content changes beyond paths/configuration. Re-inventory before execution if the checkout changes, including untracked source files; never overwrite work absent from the captured Git inventory.

## Work orders and checkpoints

### UI-M00 — reconcile instructions and lock the file map

Prerequisites: this plan and manifest. Scope: documentation/inventory only.

- [x] Read repository instructions and inspect working-tree changes before editing. Reuse the current checkout unless isolation is necessary; preserve unrelated work.
- [x] Re-run `git ls-files ui app/web`, inspect untracked source/config/assets with `git status --short --untracked-files=all`, and refresh the manifest if necessary.
- [x] Check each source exists, each source appears exactly once, destinations are case-insensitively unique except intentional merges, and retirements are limited to the four named config files.
- [x] Reconcile namespace, shared ownership, runtime-fixture deferrals, Business preservation and future test paths in 00-README and affected workspace documents. Keep evidence records and blocked-domain gates intact.
- [x] Record the starting commit and any pre-existing changes in `research/ui-preservation-migration-verification.md`.

Acceptance: full coverage, no unexplained collision, dispatch links point to this plan, and migration work is clearly separate from future service behavior. No application files moved.

Suggested commit: `docs: define preservation-first UI migration contracts`.

### UI-M01 — establish the old UI baseline

Prerequisite: UI-M00. Scope: evidence and migration-focused browser checks.

- [x] Use the existing lockfile/dependencies; record Node/npm/browser versions. Install with `npm --prefix ui ci` only if needed. Do not upgrade dependencies.
- [x] Run old-root typecheck, unit tests, build, chart lint/format checks, and Playwright discovery. Record exit codes, collected test totals, duration and existing failures.
- [x] Run existing browser coverage with the existing API fixtures/backend setup. Inspect each suite's setup: port 4180 is the configured test API target; do not assume all suites launch the same backend.
- [x] Record all 19 module routes from `host/router.tsx`, aliases, query parameters, visible navigation and header launch actions.
- [x] Capture stable screenshots for the parity matrix below, using current application data and identical browser/environment settings. Add migration-specific screenshot assertions only for missing visual coverage.
- [ ] Dedicated alternate-feature-profile screenshots were not added. Clean-profile, seeded persistence and dark/light route checks passed; existing profile logic is covered by the retained unit suite and unchanged implementation. See the verification report for this coverage limit.
- [x] Record representative build assets, loaded styles and console/network errors to distinguish existing defects from migration regressions.

Acceptance: reproducible old-root baseline with test counts, screenshot references and an explicit existing-failure ledger. A pre-existing failing check is documented and reproduced; it is not silently waived or presented as passing. New screenshot expectations come from the old application, never from the migrated implementation.

Suggested commit: `test: capture current UI migration baseline`.

### UI-M02 — prepare compatible app/web infrastructure

Prerequisite: UI-M01. Scope: build/configuration merge, target helper retention; old UI remains runnable.

- [x] Merge package scripts while retaining existing `haruquantai-web` package identity and locked dependency versions. Reconcile package-lock root metadata if needed; verify there is no dependency resolution churn.
- [x] Preserve React + Tailwind Vite plugins, loopback proxy validation, current default development port and HARU_TEST_API_TARGET behavior. Specify the TS Vite config explicitly where required.
- [x] Consolidate compiler requirements into `app/web/tsconfig.json`: strict/noEmit, DOM/ES2022, React JSX, JSON imports, interop and casing semantics. Include shell, common, workspaces, tests and tool configs. Preserve E2E typing coverage or give it an explicit checking command; do not accidentally weaken the old checks.
- [x] Merge Vitest configuration to collect all existing helpers and migrated tests. Use node environment and explicit imports unless a suite already requires a different environment. Do not globally change mock/reset semantics without checking the old suites.
- [x] Move/carry Playwright, chart ESLint and Prettier configuration with corrected end-state paths. Preserve Chrome channel, 1440×900 viewport and 4173 frontend/4180 API test setup.
- [x] Normalize the two existing Home helper test paths to singular `tests/workspace/home`; preserve theme/notes/defaults behavior.
- [x] Keep the placeholder entrypoint until the coordinated source cutover. Its replacement and test rewrite happen together in UI-M03.

Acceptance: target helpers/typecheck/build pass, dependency versions unchanged, old UI still starts. Future-path scripts need not pass before the source cutover and must be identified as pending rather than reported green.

Suggested commit: `build: prepare app/web for the preserved React application`.

### UI-M03 — coordinated source migration and application cutover

Prerequisite: UI-M02. Scope: all manifest MOVE rows, entrypoint, migrated tests and active tooling references. This is one coordinated runnable checkpoint: App and the store eagerly import many workspaces, so moving only Home and breaking the rest is not an acceptable checkpoint.

Review/edit in the following order; intermediate edits may be incomplete locally, but the committed cutover must build and run:

1. Move shared components/assets, shell files and common/project. Preserve CSS content/order and shared state behavior.
2. Move result modules/databanks, Builder/Retester/Optimizer settings modules and Home-owned project modules. Rewrite every cross-owner consumer using the manifest.
3. Move Data Manager and its complete provider/catalog/tool hierarchy, including CSS, dialogs and provenance.
4. Move remaining workspaces, including Chart's complete nested `src/`, MT Analyzer and current Business UI. Apply the specified TaskManager rename and modal ownership moves.
5. Move education content, tests, helpers, source maps and module registries. Preserve runtime fixture paths and data.
6. Mount the migrated existing App from `shell/bootstrap.tsx` with StrictMode, BrowserRouter and the original CSS import sequence. Retain a document/root guard if module imports need Node safety. Do not directly SSR browser-only workspace modules merely to satisfy the former placeholder test.
7. Merge index.html: preserve current title/theme-color/viewport metadata while pointing to `/shell/bootstrap.tsx`. Replace the exact `<main>HaruQuantAI</main>` assertion with meaningful entrypoint/import-safety coverage as applicable and a browser check that the real shell mounts.
8. Update static/dynamic imports, `vi.mock` module strings, CSS `@import`/`url()`, asset paths, `?raw` imports, glob expressions, module registries, source-map Haru paths and documentation links. Do not use a blanket text replacement that changes donor paths or user-visible content.
9. Adapt browser tests that import Vite source URLs (`/app/plugins/...`) to the real new source URLs. Preserve test purpose and assertions; source-structure checks are not visual coverage.
10. Fix evidence/screenshot paths based on repository root or config location. Existing `../../.agents/...` expressions must be reviewed after moving from `ui` to `app/web`; prevent output outside the intended evidence directory.
11. Update `scripts/ci_check.py` and chart npm scripts to `app/web` / new Chart paths. Correct the GitHub workflow's frontend install/cache/browser paths. Since `scripts/release_check.py` is absent, use the real `scripts/ci_check.py` entrypoint and adjust artifact upload to evidence actually produced; do not invent a successful release report. Validate the resulting job's requirements before claiming CI works.
12. Update `.gitignore` for the actual `app/web` generated directories and TS artifacts. Review active editor/task/launch settings and operational docs found by the repository-wide reference search.

Do not use a raw folder move onto a nonempty target. Use explicit tracked moves plus reviewed merges; no `ui` symlink, cross-root source import or second copy as the finished application. On Windows, perform case-only renames through a temporary name and check Git's recorded casing.

Acceptance: all source destinations accounted for; real shell and all old routes accessible; typecheck, unit tests and build pass without lost tests; current helpers still tested; chart checks pass; browser parity results are ready for UI-M04. No production imports from tests, and no app/web source imports from ui.

Suggested commit: `refactor: migrate the existing UI into app/web without redesign`.

### UI-M04 — verify browser parity and repair migration regressions

Prerequisite: runnable UI-M03. Scope: repairs caused by migration, verification evidence.

- [x] Run the complete final command set below. Compare collected suite/test counts and assertion coverage with UI-M01; investigate every reduction.
- [x] Replay baseline screenshots without regenerating their expected images. Any unexpected visual difference requires a fix or an explicitly documented environmental cause supported by evidence.
- [x] Check route deep-link reload, back/forward, `/home`, trailing/nested paths and preserved tab/strategy/bank query strings.
- [x] Restore the seeded pre-migration persistence fixture on the same origin; verify keys/schema, navigation, theme, zoom, drafts and chart state survive.
- [x] Verify source URL tests, raw-content/provenance tests, CSS/asset loads, API mocks/proxy and connection/error states.
- [x] Investigate changed CSS module hashes/Tailwind scanning paths: generated class names may differ while rendering must remain equivalent.
- [x] Check console exceptions, failed requests, duplicate store instances, missing providers and duplicate stylesheet loading.
- [x] Log results, environment, screenshot comparison artifacts and remaining baseline defects in the verification document. Do not mark skipped or blocked browser suites as passing.

Acceptance: no unexplained appearance/behavior regression, no test loss, all migration-specific checks green; every environmental/pre-existing limitation explicitly reported.

Suggested commit if fixes are needed: `fix: preserve UI parity after app/web migration`.

### UI-M05 — retire old paths and hand off future development

Prerequisite: UI-M04 gates satisfied. Scope: cleanup and authoritative developer instructions.

- [x] Confirm required TypeScript semantics are consolidated; retire old tsconfig.app/node files instead of copying unused configs.
- [x] Verify tracked vite.config.js/d.ts contain no unique source, then retire them. Confirm Vite loads vite.config.ts.
- [x] Confirm no remaining source/config/assets need `ui/`. Remove only empty old source directories after verifying resolved paths are inside the workspace. Do not recursively delete a mixed directory with unrelated/untracked files.
- [x] Audit all active references to `ui`, `app/ui`, `/app/host`, `/app/plugins`, `/app/workspace` and old test roots. Distinguish historical source evidence from active executable paths; retain historical evidence unchanged.
- [x] Ensure the final frontend can install, typecheck, test and build without an old-root node_modules or dist. Use only app/web commands. Do not copy node_modules between roots.
- [x] Publish final startup/test instructions in `app/web/README.md`, mark manifest rows completed with evidence in the verification document, and update dispatch/workspace current paths.
- [x] Record deferred feature adaptations: real services, fixture/type splitting, store extraction, future panel additions, donor qualification and optional deduplication. No deferred item is mislabeled complete.

Acceptance: one authoritative frontend root, complete accounted-for source migration, verified current presentation and future work orders targeting the migrated implementation.

Suggested commit: `docs: finalize app/web development and migration evidence`.

## Browser parity matrix

Baseline at 1440×900 in the configured Chrome channel. Also check one 1280×720 and one 1920×1080 viewport for the shell and the most crowded layouts. Check actual baseline support at smaller widths rather than introducing responsive redesign. Keep OS/browser/font/DPR/zoom/data fixed. Freeze clocks/animations or mask dynamic regions narrowly; never mask controls/layout under evaluation.

| Surface | Required baseline and migrated checks |
|---|---|
| Shell/Home | Sidebar collapsed/expanded, header launch actions, settings/connection dialogs, notifications, status bar, dark/light themes, profile selection and zoom |
| Data Manager | Home/dock/chart, provider ribbon, connection/catalog panels, import/export/tools, progress/log and error states; retain existing provider E2E suites |
| Builder | Progress, all existing settings tabs, result selection, equity/trades/source tabs, fitness dialog and databank splitter |
| Retester/Optimizer | Current settings/progress/results, cross-check popup, optimization parameters/dialogs and walk-forward matrix |
| Shared project/results | Project frame/header, settings sections, result tabs/conditional states, custom analysis, source generation and provenance checks |
| Databank | Load/save, selection/notes, rename/delete, view columns, comparison, correlation, portfolio actions and split resizing |
| AlgoWizard | Current home/editor, rule/block dialogs, templates, toolbar/settings/resources, AI prompt and code export |
| Code Editor | File tree/editor, current language support and keyboard behavior, dialogs and existing regression suite |
| Chart | Main layout, chart rendering, indicators/tools, panels, saved layout/drawings, replay and existing performance thresholds |
| Portfolio Master/Composer | Existing settings/progress/results, composition/member operations, candidate/modal flows |
| Custom Projects | `/projects`, task list/order/selection/configuration and New Task modal; preserve current preview behavior |
| Business/AI | Current Business tabs/node/MCP dialogs; AI tiles, drafts, pin/project selections and availability states |
| Other workspaces | MT Analyzer, Neural Network, Live Trading, Debug Console, Grid Control, Grid Test: rendered screen and primary existing interaction |
| Persistence/deep links | Clean storage and old seeded storage; reload/back/forward, tab/strategy/bank selection, saved preferences and chart state |

All 19 current route paths: `/`, `/aiassistant`, `/datamanager`, `/chart`, `/business`, `/builder`, `/algowizard`, `/codeeditor`, `/neuralnet`, `/retester`, `/optimizer`, `/mtanalyzer`, `/projects`, `/portfolio`, `/composer`, `/trading`, `/debugconsole`, `/gridcontrol`, `/gridtest`. `/home` remains a supported alias. Folder naming must not alter this list.

## Commands and evidence

Run commands from the repository root. Baseline commands use `ui`; final commands use `app/web`. Record outputs in `.agents/logs/ui-preservation-migration/` and summarize in `research/ui-preservation-migration-verification.md`. That verification document is created during execution, not a fabricated completed report in this planning task.

```powershell
# UI-M01: measure baseline before touching the application
npm --prefix ui run typecheck
npm --prefix ui test
npm --prefix ui run build
npm --prefix ui run lint:chart
npm --prefix ui run format:chart:check
npm --prefix ui run test:ui -- --list
npm --prefix ui run test:ui

# UI-M02 onward: install only if dependencies are absent/out of sync
npm --prefix app/web ci

# UI-M03/UI-M04: final checks, after all source paths exist
npm --prefix app/web run typecheck
npm --prefix app/web test
npm --prefix app/web run build
npm --prefix app/web run lint:chart
npm --prefix app/web run format:chart:check
npm --prefix app/web run test:ui -- --list
npm --prefix app/web run test:ui

# Final browser development entrypoint
npm --prefix app/web run dev

# Repository integration after scripts/CI frontend references are corrected
uv run python scripts/ci_check.py
git diff --check
```

Use Playwright's supported config/browser setup from the installed lockfile. Install the configured Chrome browser only if missing. Baseline and migrated screenshots must run against the same controlled backend/data. Avoid triggering live broker orders or other external mutations; existing deterministic browser fixtures qualify layout and interactions without external effects.

The broad repository check may reproduce unrelated Python/architecture failures. Preserve and report them distinctly from frontend migration results; investigate changes only when the migration caused them. Browser tests passing against Vite do not prove Python-hosted SPA serving: if actual startup already serves a UI build, update/test that existing binding. Otherwise the AppCore web-build hosting order remains separate; do not implement a new hosting feature just to perform this refactor.

## Reference audit, recovery and completion

Search active scripts, workflow/config files, tests and developer instructions for old paths, not just imports. Pay special attention to Playwright source imports, `import.meta.glob`, Markdown raw imports, provenance validators, E2E evidence directories and shell CSS imports. Keep historical donor records immutable. New paths must be inside the checkout and case-correct on Windows and case-sensitive systems.

Use the pre-migration Git commit plus baseline artifacts as the recovery point. Keep commits reviewable and runnable at their stated checkpoints. If a checkpoint fails, repair its migration changes or revert only the migration commit after checking for unrelated work; never use hard reset or broad cleanup as the default recovery. Do not delete old source before all its manifest rows have destinations and the coordinated cutover is complete.

Completion requires:

- [x] Every current source file accounted for, all target merge collisions resolved, and no unexplained deletion or duplicate implementation.
- [x] The browser opens the existing real application from app/web with preserved routes, appearance, interactions and persistence.
- [x] Existing target helpers remain present and tested; the placeholder screen is retired.
- [x] Typecheck/build/unit and applicable browser/visual checks verified against the old baseline, with no hidden exclusions or baseline regeneration.
- [x] Chart tooling, active CI/startup paths, assets, content and provenance resolvers use the new structure.
- [x] Frontend install/build/test does not depend on ui/; there is one authoritative application root.
- [x] Documentation records actual completed work and remaining service adaptations separately.

The structural migration has been executed. Continue feature work on the existing application in app/web, using the verification report and current file tree; do not create a replacement shell or regenerate the future feature inventory.
