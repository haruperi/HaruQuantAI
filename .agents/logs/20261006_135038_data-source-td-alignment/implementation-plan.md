# Implementation plan: TickDownloader frontend alignment to DataSourceTD

Version: 1. Status: APPROVED.
Date: 2026-10-06, Africa/Cairo. Source HEAD: 30128b58bbc7ac495f33a860ba7d31d603eecec5.
Working-tree baseline: clean after owner-authorized SQData commit. Owner approval reference: explicit APPROVED: EXECUTE user reply on 2026-10-06 for version 1; commit/start-next authorizes previous commit and this audit/plan only.

## Objective and acceptance boundary

Align one bounded folder, HARUQUANTAI_ROOT/ui/app/plugins/data_source/TickDownloader, with explicitly confirmed SQX_REFERENCE_ROOT/internal/plugins/DataSourceTD. Outer names differ intentionally. Apply completed Dukascopy pilot conventions. Preserve existing browser metadata discovery, mock import, selection, errors, postfix, focus/Escape, persistence and simulated progress. Frontend only: no filesystem content parsing, real TickDownloader process, remote connection, backend or parity claim.

## Research and authority

Read root AGENTS.md, canonical plan/walkthrough templates and previous qualified cohorts. Audited all six donor UI files: root service/module/styles and import controller/template/module, plus binary inventory. Read all three current target files (TickDownloaderImportDialog.tsx, tickDownloader.ts, tickDownloader.css), scoped unit/browser tests, Common store ownership, ribbon registration and Data Manager import/render/advance/controls. Used git status/rev-parse, Get-ChildItem/Get-Content, rg consumer searches and hidden/ignored ledger/instruction search. Only root AGENTS.md found; reimplementation.json and reimplementation.schema.json remain absent. No new behavioral evidence records or ledger validation assertion.

Current inventory: three target files. Dialog owns browser picker metadata, manifest/postfix/selection/error state, indeterminate selection, initial focus/return focus and keyboard trap. Rules own bounded folder metadata discovery and validation. Shared Common/dataManagerStore.ts owns useTickDownloader persistence, corruption/quota handling, cross-provider guards/reservations, progress, pause/resume/stop and restored-running-to-paused behavior. Its state is consumed by sibling providers and Data Manager; preserve shared store unchanged. tickDownloader.ts is imported by that store; preserve its path/API unchanged. One external dialog import in DataManager.tsx; no separate route files. Styles consumed only by dialog. Ribbon currently contributes one provider and command inline.

Donor has seven artifacts: one HTML, four JS, one CSS and one JAR. Service UI methods reference backend discovery/import/action requests; target adapter attaches solely to existing metadata rules/store. Runtime directory semantics and import algorithms remain unverified. Existing target rule comment attributes nested tickdata discovery to SQX without a ledger citation; preserve protected utility unchanged and record this pre-existing unsupported attribution as a research gap, not confirmed donor behavior.

## Decisions and public contracts

Propose README ownership registration for plugins/data_source/TickDownloader: FEAT-UI-TD-TRACEABILITY, DEC-UI-TD-TRACEABILITY, FR-UI-TD-source-mapping, FR-UI-TD-workflow-preservation and FR-UI-TD-clean-room. IDs become repository truth only after approved registration; README owns status.

| Donor-relative artifact | Target counterpart/exclusion |
| --- | --- |
| DataSourceTDService.js | DataSourceTDService.ts |
| module.js | module.ts |
| styles.css | styles.css |
| import/DataSourceTDImportCtrl.js | import/DataSourceTDImportCtrl.ts |
| import/importPopup.html | import/importPopup.tsx |
| import/module.js | import/module.ts |
| DataSourceTD.jar | excluded backend binary, inventory/hash only |

Counts: six counterparts, one exclusion; final nine target files = six counterparts plus three exceptions (tickDownloader.ts, README.md, source-map.json). Shared Common store is outside scoped target inventory and retained as an explicit external dependency. Exact names/casing/subfolders and html->tsx/js->ts/css->css mappings; no helper folders/placeholders. Controller owns existing state/picker/lifecycle, service adapts existing discoverTD and useTickDownloader.start/action, view owns JSX/keyboard presentation, modules own original typed contribution/export. No duplicate store or new persistence contract.

## Ordered implementation

1. Record logical-root before inventories and donor hashes; confirm clean baseline/approved writes.
2. Move TickDownloaderImportDialog.tsx to import/importPopup.tsx. Extract state, focus effects, picker-selection handling, indeterminate checkbox and submit into import/DataSourceTDImportCtrl.ts; retain view keyboard trap and presentation in mapped component. Preserve exact errors and callback order.
3. Add DataSourceTDService.ts attaching discovery/start and existing action capability without network/file-content reads. Preserve store authority and validation, no new progress owner.
4. Move tickDownloader.css to styles.css; update import. Add import/module.ts and root module.ts for current provider/command. Update Common ribbon and Data Manager imports without changing identity/ordering/labels.
5. Register README and source-map.json with complete logical locators, inspection dates, SHA-256, catalog references, narrow inspected locations, source HEAD/review/version and clean-room flags. Exclude JAR explicitly. Do not create behavioral ledger substitutes.
6. Add scoped mapping negative/boundary tests and browser qualification adjustments; verify then prepare walkthrough.

## ALLOWED_WRITE_PATHS

HARUQUANTAI_ROOT-relative exact paths.

Moves/removals:
- ui/app/plugins/data_source/TickDownloader/TickDownloaderImportDialog.tsx -> ui/app/plugins/data_source/TickDownloader/import/importPopup.tsx
- ui/app/plugins/data_source/TickDownloader/tickDownloader.css -> ui/app/plugins/data_source/TickDownloader/styles.css

New files:
- ui/app/plugins/data_source/TickDownloader/DataSourceTDService.ts
- ui/app/plugins/data_source/TickDownloader/module.ts
- ui/app/plugins/data_source/TickDownloader/import/DataSourceTDImportCtrl.ts
- ui/app/plugins/data_source/TickDownloader/import/module.ts
- ui/app/plugins/data_source/TickDownloader/README.md
- ui/app/plugins/data_source/TickDownloader/source-map.json

Integration/tests:
- ui/app/plugins/data_source/Common/dataSourceRibbon.ts (TickDownloader contribution only)
- ui/app/workspace/DataManager/DataManager.tsx (TickDownloader dialog import only)
- ui/tests/unit/plugins/data_source/TickDownloader/sourceMapping.test.ts
- ui/tests/unit/plugins/data_source/TickDownloader/sourceMappingValidation.ts
- ui/tests/e2e/data-manager-tickdownloader.spec.ts (scoped qualification; launcher disambiguation if required)

Evidence: bounded .agents/logs/20261006_135038_data-source-td-alignment/ subtree for plan, inventories/fingerprints, archived audit script text, actual results and walkthrough. Store no machine-specific absolute paths or donor source text. Archive one-off scripts as text evidence to avoid treating them as retained application Python modules.

Protected: tickDownloader.ts, Common/dataManagerStore.ts, existing rule tests; all sibling/host/backend files except named integration paths; dependencies/config, donor installation, data/, .vscode/ and live databases. Only two obsolete named frontend source files may be removed following relocation. No branch/junction changes, schema/restore action or Git mutation under execution approval.

## Verification and release conditions

Record actual commands/results, exit codes and timestamps:
- npm --prefix ui run test -- tests/unit/plugins/data_source/TickDownloader
- npm --prefix ui run typecheck
- npm --prefix ui run test
- npm --prefix ui run build
- npm --prefix ui run test:ui -- tests/e2e/data-manager-tickdownloader.spec.ts --workers=1
- git diff --check
- rg -n 'TickDownloader/TickDownloaderImportDialog|tickDownloader.css' ui/app ui/tests (obsolete imports absent)

Check seven-artifact donor inventory and fingerprints, six exact mappings/one exclusion, nine classified targets, casing/extensions/collisions, provenance/catalog/owner/review resolution and clean-room flags. Negative tests cover missing/mis-cased/unclassified/duplicate targets, wrong extension, unsafe paths, invalid hash/catalog and unresolved ownership. Compare preserved rules/shared store/all sibling application baseline hashes, relocated stylesheet and write scope.

Browser tests exercise metadata selection, empty folder, select-all/individual selection, postfix/duplicate/required validation, import pause/reload/resume/completed status, stop/cancel, quota errors, unchanged mock file contents, offline operation and retained-folder reselection. Add focused checks for Escape/focus trap/return focus if existing coverage is insufficient. Review normal/narrow presentation and record actual skin appearance; selection of Light skin alone is not visual proof. Use isolated temporary fixtures/storage. No donor execution parity or ledger validation claimed.

## Risks and deviations

Shared store dependency must remain stable; adapter cannot duplicate persistence or change guards. Preserve metadata-only discovery even though donor service delegates backend operations. Do not fix unsupported target donor attribution or add real TickDownloader parsing within structural refactor. Record visual-theme or pre-existing harness issues separately. Any material added paths/contracts/behavior/dependencies/destructive targets require plan iteration and renewed approval. Shared junctions/live database remain untouched.

## Walkthrough and owner gates

Create walkthrough.md from docs/templates/walkthrough.md with before/after inventories, separate counts, actual commands/results, deviations/gaps, Git status and proposed subject: refactor(ui): align TickDownloader UI with DataSourceTD structure.

Stop for APPROVED: EXECUTE on version 1 before source edits or README registration. Separate owner authorization after walkthrough review is required for commit/merge/push/history changes. Yahoo remains the next donor cohort after this one.
