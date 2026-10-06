# Implementation plan: Yahoo frontend alignment to DataSourceYahoo

Version: 1. Status: APPROVED.
Date: 2026-10-06, Africa/Cairo. Source HEAD: 69c24c148be9693a2c300f88c179b3ef2e832ddc.
Working-tree baseline: clean after owner-authorized TickDownloader commit.
Owner approval reference: explicit APPROVED: EXECUTE user reply on 2026-10-06 for version 1. Commit/start-next authorizes previous commit and this audit/plan only.

## Objective and acceptance boundary

Align HARUQUANTAI_ROOT/ui/app/plugins/data_source/Yahoo with explicitly confirmed SQX_REFERENCE_ROOT/internal/plugins/DataSourceYahoo. Outer names differ intentionally. Complete this final remaining DataSource donor cohort using Dukascopy pilot standards. Frontend only: preserve independent offline catalogue, mock add/download/store/progress, validation, errors, date presets, selected-row eligibility, overwrite policy, focus/Escape and persistence. No Yahoo Finance integration, backend, new datasets, network requests, database work or SQX parity assertion.

## Research and authority

Read root AGENTS.md, canonical plan/walkthrough templates and prior cohorts. Audited all donor UI artifacts: root module, YahooService.js, singular style.css, add/addPopup.html/addPopupCtrl.js/module.js, download/downloadPopup.html/downloadPopupCtrl.js/module.js; binary inventory only. Read five current target files, unit/browser tests, Data Manager imports/render/target eligibility, Common ribbon registration, shared dependencies and sibling rules/store consumers. Commands: git status/rev-parse, Get-ChildItem/Get-Content, rg imports/consumers and hidden/ignored ledger/instruction search. Root AGENTS.md is the sole discovered contributor instruction file; canonical reimplementation.json and reimplementation.schema.json remain absent. No ledger edits or validation claim authorized.

Current target inventory: YahooAddDialog.tsx, YahooDownloadDialog.tsx, yahoo.css, yahoo.ts, yahooStore.ts (5 files). Add dialog owns shared modal keyboard trap and cross-provider context in addition to add form. Download imports those helpers and owns initial date range, preset selection, overwrite/error state and start. Shared rules own ticker parsing/catalogue, target eligibility and bounded date ranges; store owns mock jobs, reservations, corruption/quota handling, paused restoration, incremental add and coverage merge. Preserve both rules/store paths and bytes; sibling providers/Common/FileImport consume reservedYahoo/useYahoo/yahooActive. Only DataManager.tsx externally imports the dialogs; no separate route files. CSS imported by add dialog and reused by download through shared modal.

Donor inventory: 10 artifacts = 2 HTML, 6 JS, 1 CSS, 1 JAR. Exact stylesheet is style.css, not styles.css. Controller filenames are add/addPopupCtrl.js and download/downloadPopupCtrl.js; internal Angular controller names do not change filename mapping. Donor service delegates add/cancel/import/action to backend; target adapter attaches to current mock capabilities. Algorithmic and remote behavior remain unverified; do not copy donor controller logic or silently adopt donor defaults.

## Decisions and public contracts

Propose domain plugins/data_source/Yahoo with FEAT-UI-YAHOO-TRACEABILITY, DEC-UI-YAHOO-TRACEABILITY, FR-UI-YAHOO-source-mapping, FR-UI-YAHOO-workflow-preservation and FR-UI-YAHOO-clean-room registered in new README. IDs become repository truth only through approved registration; README owns implementation status.

| Donor-relative artifact | Target counterpart/exclusion |
| --- | --- |
| YahooService.js | YahooService.ts |
| module.js | module.ts |
| style.css | style.css |
| add/addPopup.html | add/addPopup.tsx |
| add/addPopupCtrl.js | add/addPopupCtrl.ts |
| add/module.js | add/module.ts |
| download/downloadPopup.html | download/downloadPopup.tsx |
| download/downloadPopupCtrl.js | download/downloadPopupCtrl.ts |
| download/module.js | download/module.ts |
| DataSourceYahoo.jar | excluded backend binary; fingerprint only |

Counts: 9 meaningful counterparts, 1 exclusion; final 13 target files = 9 counterparts + 4 exceptions (yahoo.ts, yahooStore.ts, README.md, source-map.json). Preserve nested names/casing and extension mappings. No helper folders or placeholders. Keep small presentation helpers/shared YahooModal in mapped add/addPopup.tsx, reused by download counterpart. Move cross-provider context into YahooService.ts, controller state/actions into exact mapped controller files; service builds definitions and invokes existing startAdd/startDownload/action capability. Root/child modules own existing provider/commands/exports. Existing callbacks, errors, storage keys and host lifecycle remain unchanged.

## Ordered implementation

1. Capture before/donor inventories and SHA-256 fingerprints, approved scope and clean baseline.
2. Move YahooAddDialog.tsx to add/addPopup.tsx; extract symbols/postfix/error/store/form actions into add/addPopupCtrl.ts. Move context/reservation/active/storage checks into typed YahooService.ts. Preserve check order and add callback sequence.
3. Move YahooDownloadDialog.tsx to download/downloadPopup.tsx; extract initial range, preset/date/overwrite/error state and start into download/downloadPopupCtrl.ts. Reuse mapped YahooModal; retain small preset button helper in view. Preserve existing target date functions and selected-row host checks.
4. Move yahoo.css to singular style.css, update references. Add add/download module.ts and root module.ts; wire Common ribbon contribution and Data Manager imports only. Preserve IDs/labels/order, icon, target selection and progress behavior.
5. Register ownership README and complete source-map.json with exact logical roots/relative locators, dates, SHA-256, catalog references, narrow source locations, source commit/review/version and clean-room flags. Exclude JAR explicitly; structural manifest does not replace behavioral ledger.
6. Add scoped mapping/boundary tests, qualify browser workflows and prepare walkthrough. Perform final read-only completion inventory of all DataSource family manifests; report any remaining gap without editing prior cohorts.

## ALLOWED_WRITE_PATHS

All paths are HARUQUANTAI_ROOT-relative and exact.

Moves/removals:
- ui/app/plugins/data_source/Yahoo/YahooAddDialog.tsx -> ui/app/plugins/data_source/Yahoo/add/addPopup.tsx
- ui/app/plugins/data_source/Yahoo/YahooDownloadDialog.tsx -> ui/app/plugins/data_source/Yahoo/download/downloadPopup.tsx
- ui/app/plugins/data_source/Yahoo/yahoo.css -> ui/app/plugins/data_source/Yahoo/style.css

New files:
- ui/app/plugins/data_source/Yahoo/YahooService.ts
- ui/app/plugins/data_source/Yahoo/module.ts
- ui/app/plugins/data_source/Yahoo/add/addPopupCtrl.ts
- ui/app/plugins/data_source/Yahoo/add/module.ts
- ui/app/plugins/data_source/Yahoo/download/downloadPopupCtrl.ts
- ui/app/plugins/data_source/Yahoo/download/module.ts
- ui/app/plugins/data_source/Yahoo/README.md
- ui/app/plugins/data_source/Yahoo/source-map.json

Integration/tests:
- ui/app/plugins/data_source/Common/dataSourceRibbon.ts (Yahoo contribution only)
- ui/app/workspace/DataManager/DataManager.tsx (Yahoo dialog imports only)
- ui/tests/unit/plugins/data_source/Yahoo/sourceMapping.test.ts
- ui/tests/unit/plugins/data_source/Yahoo/sourceMappingValidation.ts
- ui/tests/e2e/data-manager-yahoo.spec.ts (bounded qualification adjustments including launcher disambiguation/keyboard cases if required)

Evidence: bounded .agents/logs/20261006_135832_data-source-yahoo-alignment/ subtree for plan/inventories/hashes, archived script text, actual verification results, read-only final donor-family inventory and walkthrough. No absolute local machine paths, sensitive material or donor source text.

Protected: yahoo.ts, yahooStore.ts and existing yahoo.test.ts; sibling features/Common store/host/backend except named integration paths; dependencies/configuration, donor installation, data/, .vscode/, live databases/schema. Only three obsolete named frontend files may be removed after relocation. No junction detach, database action or Git mutation authorized by execution approval.

## Verification and release conditions

Run and record exact commands/results/exit codes/timestamps:
- npm --prefix ui run test -- tests/unit/plugins/data_source/Yahoo
- npm --prefix ui run typecheck
- npm --prefix ui run test
- npm --prefix ui run build
- npm --prefix ui run test:ui -- tests/e2e/data-manager-yahoo.spec.ts --workers=1
- git diff --check
- rg -n 'Yahoo/YahooAddDialog|Yahoo/YahooDownloadDialog|yahoo.css' ui/app ui/tests (obsolete imports absent)

Check actual 10-artifact donor inventory/fingerprints, 9 exact counterparts/1 exclusion, 13 classified target files, extension/case/collision correctness, catalog/owner/review/source references and clean-room flags. Negative tests cover missing/mis-cased/unclassified/duplicate targets, wrong extension, unsafe paths, invalid hash/catalog and unresolved ownership. Check callable controllers/views and preserved provider commands. Compare protected rules/store/sibling hashes, unchanged relocated stylesheet, and approved-write compliance.

Browser workflows cover add separators/postfix/catalogue validation and errors, provider label/icon, simulated add/reload status, selected-row download eligibility, presets/custom invalid ranges, overwrite coverage metadata, paused restoration/resume, quota failure, focus/Tab/Escape/return focus and responsive presentation. Add bounded checks if needed for preserved cancel/guard behavior. Review actual screenshots and report skin appearance separately from successful skin selection; do not fix unrelated theme behavior. Tests use isolated browser storage and mock data. No ledger-schema validation while canonical files are absent; no SQX runtime parity claim.

Final read-only inventory compares each installed DataSource* donor to its declared target mapping/manifests, with explicit SQData dual roots. This is a structural completion report, not independent behavioral verification or authority to change prior features.

## Risks and deviations

Avoid cycles by moving shared context to service and keeping modal presentation owned by mapped add view. Shared rules/store retain stable sibling contracts. Preserve existing date preset semantics even if donor controller defaults differ. No real Yahoo calls or new subscriptions. Record pre-existing harness/theme gaps separately; material new paths/contracts/behavior/dependencies/destructive targets require iteration and renewed approval. Preserve shared junctions/live database throughout.

## Walkthrough and owner gates

Create walkthrough.md using canonical template with before/after inventories and counts, actual commands/results, deviations/unresolved gaps, final read-only donor-family coverage, Git status and proposed subject: refactor(ui): align Yahoo UI with DataSourceYahoo structure.

Await APPROVED: EXECUTE on version 1 before source edits or registry registration. Separate owner authorization after walkthrough review required for commit/merge/push/history mutation. Structural completion of all donor folders does not establish SQX behavioral parity.
