# UI preservation migration verification

Date: 2026-10-30. Status: application migrated; UI verification passed with the pre-existing limitations below. Starting commit: `d16f65ff0c3c2116acf26dee7ed13bc456aeee1c`.

## Result

`app/web` is the sole active frontend. It mounts the existing React application, preserving StrictMode, BrowserRouter, routes, CSS import order, theme variables, stores, fixtures, education content and current behavior. No screens were rebuilt or replaced with stubs. Continue frontend development here.

The original 953 UI files and 14 target files are accounted for in the [manifest](ui-preservation-migration-manifest.csv). The migration also adds one browser suite and 38 pre-migration screenshot assets, giving 1,006 source disposition rows. The [implemented file tree](ui-preservation-target-tree.txt) contains 996 frontend source/configuration/content/test files, excluding generated output. Four obsolete/generated configuration files were retired or consolidated; every other destination exists. The additional shared provenance-test inventory is `app/web/tests/common/project/projectFiles.ts`.

The old `ui` directory is absent from the active checkout. Its remaining root configuration and generated caches were archived under ignored `.agents/logs/ui-preservation-migration/retired-ui/` rather than deleting a mixed directory. Pre-migration source bytes are separately preserved under `source-backup/` for recovery. Neither archive is an application dependency.

## Preserved implementation and styling

- Compared the TypeScript ASTs of all 556 migrated production `.ts`/`.tsx` files, normalizing file locators and the approved CustomProjectsWorkspace → TaskManagerWorkspace identifier rename. No other implementation changes were found. Mounting/configuration were reviewed separately.
- The old and migrated builds emit **byte-identical** `assets/index-B4b1Mkww.css`, SHA-256 `383c813beee4b8972ee9b9ec6fe21cc9cb46e184a6733881c1d7bf886027697d`. Global and workspace styles retain their content/order.
- Dependency resolution is unchanged. Package-lock differs only in root package identity (`haruquantai-web`); no package versions were upgraded.
- Donor roots, source commits, review records, owners, clean-room declarations, source catalogues and source/fingerprint arrays are unchanged in all 78 source-map records. Haru target/dependency locators were updated to new paths.
- Existing target helper implementations `themeProjection.ts`, `notesPreview.ts` and `databankDefaults.ts` remain byte-identical to their captured source hashes.
- Every screenshot asset moved without changing its SHA-256. No expected screenshot was regenerated from the migrated UI.

## Measured checks

Environment: Windows, Node v24.21.0, npm 12.0.2, configured Chrome channel. Detailed command outputs and comparison data are in `.agents/logs/ui-preservation-migration/`.

| Check | Old UI baseline | Migrated result |
|---|---|---|
| Typecheck | Pass | Pass |
| Unit tests | 650 passed | 658 passed in 121 files; original coverage plus retained target helpers and expanded bootstrap guard tests |
| Production build | Pass | Pass; same CSS bytes, unchanged dependencies |
| Chart lint | Pass | Pass |
| Chart formatting | Fails on 96 files | Same 96-file pre-existing formatting debt; no broad formatting rewrite |
| Browser discovery | 235 tests / 60 files | 276 tests / 61 files; original tests plus 41 migration tests |
| Dedicated migration browser checks | Pre-migration screenshot capture and baseline replay; persistence/viewport checks pass | **41 passed** against unchanged old-UI images |
| Broad browser diagnostic | 30 failed, 3 interrupted, 202 not run after 30-failure cap | 30 failed, 3 interrupted, 243 not run at same cap; the same 33 failed/interrupted test identities |
| Repository-wide check | Existing script lint defect inspected | Stops at pre-existing `scripts/examples/brokers.py:51` import-order failure; no claim of full repository qualification |

Final frontend checks also run with `ui/` absent, establishing independence from the old root. See `final-checks.json`, `final-unit.log`, `final-typecheck.log`, `final-build.log` and `final-chart-lint.log`. Git diff whitespace validation is recorded separately.

The broad browser diagnostic uses `--workers=4 --timeout=15000 --max-failures=30`; it is deliberately bounded and **does not qualify all legacy E2E tests**. The failed/interrupted cohort is identical before/after; parallel scheduling changes which one of those tests is interrupted at the cap. Those failures involve existing host/fixture/interaction expectations. They have not been hidden, skipped in source, or rewritten to pass. The independent migration suite runs all 41 tests with isolated API fixtures and a 60-second timeout.

## Browser preservation coverage and limits

The migration suite compares all 19 existing routes in dark and light skins at 1440×900. It also verifies seeded version-1 Builder population data, reload persistence, the `/home` alias, deep-link query preservation, back navigation and shell/settings/results access at 1280×720 and 1920×1080. No real user profile storage or live broker actions were used.

Expected images were captured from `ui/` before source movement. An initial cold-server capture of Home timed out and was recaptured from the unchanged old source. Old-root replay showed 2,349 differing Chart pixels and 2,715 differing MT Analyzer pixels (about 0.18–0.21% of the 1440×900 image), attributable to live canvas/timing variation. Those two routes use a documented 0.3% pixel-difference limit; other route comparisons use 0.1%. The expected files themselves remain unchanged. This is measured screenshot equivalence within those tolerances, not a mathematical pixel-perfect guarantee for dynamic charts.

For isolated parallel baseline diagnostics, capture used test frontend port 4175; final migration checks used 4173. Each run used clean isolated browser contexts and the same persisted-data fixture schema. The normal developer origin remains port 3000, with unchanged storage keys/versions and routes. Tests establish old-schema hydration and reload/back behavior; they do not inspect or reset the user's personal browser profile.

All existing test assertions were retained, except the obsolete literal `<main>HaruQuantAI</main>` bootstrap assertion. It is replaced by Node import safety, existing-root mounting and missing-root behavior tests; browser snapshots verify that the real shell mounts. E2E TypeScript continues to be transpiled by Playwright, as before. The ordinary typecheck excludes E2E files just as the old application's typecheck did; no new E2E static type-coverage claim is made.

Dedicated screenshots do not exhaust every dialog, profile or workflow permutation. The full original unit suite, unchanged production ASTs, identical CSS and retained legacy E2E suites provide additional coverage; unresolved legacy E2E failures remain explicit.

## Structural decisions applied

- `shell`: existing App, router, Zustand store, host transport/types/menus/dialogs and global styles.
- `common/components`, `common/assets`, `common/project`: shared controls/assets and the single existing ProjectWorkbench implementation. The old project registry is `common/project/registry.md`, distinct from its Workbench README.
- `workspaces`: lower-case owner names, including preserved `chart` and `mt_analyzer` implementations absent from the earlier plan inventory.
- `algo_wizard` is the canonical Wizard namespace, with `/algowizard` preserved; `ai` is canonical for assistant/MCP code.
- CustomProjects component/file is renamed TaskManagerWorkspace under `task_manager`, preserving `/projects`, module ID, visible labels and existing task behavior.
- Business presentation is preserved. Node/MCP modal source ownership moved to Grid Control/AI while Business retains access.
- Data Manager provider/catalog/tool hierarchy, results/databank modules and project settings/results modules retain their implementations. Shared provenance inventories now resolve each actual owner without copying production modules.
- Existing runtime fixtures, defaults, preview algorithms and mock behavior remain available to current consumers. No production imports from `tests/` were introduced.

Vite carries forward React + Tailwind, port 3000 and loopback-validated HARU_TEST_API_TARGET `/api` proxy. TypeScript settings are consolidated; generated JS/d.ts Vite configs and obsolete tsconfig.app/node configs are retired. Vitest retains the old application's explicit mock lifecycle instead of globally imposing the bootstrap-only reset behavior. Chart scripts, CI frontend/cache/browser paths, ignore rules and current README commands use app/web.

The workflow's missing `scripts/release_check.py` entrypoint was corrected to the existing `scripts/ci_check.py`, and upload paths now describe actual logs/test output. The migration persistence/viewport checks are included in CI. CI execution itself remains limited by the recorded pre-existing Python lint failure; no remote CI result is asserted.

## Unrelated work and deferred scope

Pre-existing and concurrent broker/trading Python edits, connection/simulation packages and tests were preserved. Full initial status is in `starting-status.txt`. No broad reset, staging or commit of unrelated work was performed.

Backend service integration, donor qualification, runtime-fixture/type splitting, task store extraction, numerical preview retirement, optional component deduplication and unimplemented future panels remain separate work. Python-hosted SPA serving remains with the existing AppCore hosting order; this refactor does not introduce a new server feature. The documents' original migration tables retain historical source paths where appropriate, but their migration notes/manifest now govern current locations.

## Reproduce

```powershell
npm --prefix app/web ci
npm --prefix app/web run dev
npm --prefix app/web run typecheck
npm --prefix app/web test
npm --prefix app/web run build
npm --prefix app/web run lint:chart
npm --prefix app/web run test:ui -- ui-migration-parity.spec.ts --workers=1 --timeout=60000
```

Run screenshot comparisons on the recorded Windows/Chrome environment. Existing formatting and repository-check limitations above remain visible rather than being folded into a claim that every repository check passes.
